#!/usr/bin/env python3
"""Compile a Beamer deck or article script and triage what went wrong.

Usage:
    python3 <skill-dir>/scripts/compile_deck.py talk.tex
        [--engine xelatex|pdflatex|lualatex] [--build-dir build]
        [--themes-dir PATH] [--passes 2] [--timeout 600] [--json]

--engine defaults to the deck's ``% !TEX program = ...`` line (pdflatex,
xelatex or lualatex, within its first 20 lines), else xelatex. An explicit
--engine always wins.

Runs the engine non-interactively, parses the log, and prints a compact
human/machine-readable verdict: OK with page count, or the first real error
with its line number and a triage hint. Exit code 0 on success, 1 on failure,
3 if the helper itself crashes.

When the source (including local \\input files) uses \\bibliography{...} or
\\addbibresource{...}, BibTeX or Biber runs between the first and the final
passes. It runs from the source directory, as an in-place build would, so
relative paths such as \\bibliography{../refs} resolve; its .bbl goes to the
build directory. If the tool cannot find a database or style file, a prebuilt
<stem>.bbl beside the source (an arXiv or Overleaf export, or an earlier
in-place build) is used instead of the empty one the tool wrote. Undefined
citations and cross-references left in the final log are counted as
``undefined_refs``; check_deck.py treats them as a hard blocker.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Sibling helpers are imported by path so the script runs from any directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_script import tex_tree  # noqa: E402  (no PyMuPDF dependency)

# scripts/ and themes/ ship side by side in the skill folder
# (skills/econ-slides/ in the repository). resolve() follows a symlinked or
# junctioned install back to the real folder.
SKILL_DIR = Path(__file__).resolve().parent.parent
BUNDLED_THEMES = SKILL_DIR / "themes"

PACKAGE_FILE_SUFFIXES = {".sty", ".cls", ".clo", ".def", ".fd", ".cfg",
                         ".ldf", ".bst", ".tfm"}


def missing_file_hint(name: str) -> str:
    """Tell a missing TeX package apart from a missing figure or input file."""
    if Path(name).suffix.lower() in PACKAGE_FILE_SUFFIXES:
        return (f"Missing TeX package file {name}. Find the package that ships "
                f"it with `tlmgr search --global --file /{name}`, then run "
                "`tlmgr install <package>` (with sudo when the TeX tree is "
                "system-owned, as in MacTeX). MiKTeX can install it on demand.")
    return (f"Missing file {name}: check the path and extension relative to "
            "the .tex file (figures and \\input files are not TeX packages).")


TRIAGE = [
    (r"! LaTeX Error: File `([^']+)' not found", missing_file_hint),
    # A figure named with its extension: XeTeX, then the pdfTeX/LuaTeX drivers.
    (r"! Unable to load picture or PDF file '([^']+)'", missing_file_hint),
    (r"! Package (?:pdftex|luatex|xetex|dvipdfmx)\.def Error: File `([^']+)' "
     r"not found", missing_file_hint),
    (r"! Undefined control sequence",
     "Undefined command — usually a macro used without its package, or a typo."),
    (r"! Missing \$ inserted",
     "Math outside math mode — check underscores/carets in text, e.g. in titles."),
    (r"! LaTeX Error: Environment ([\w*-]+) undefined",
     "Environment {0} undefined — a package is missing or the theme is not loaded."),
    (r"! Package tikz Error",
     "TikZ error — check node syntax and library loading."),
    (r"! Extra \}, or forgotten \$",
     "Unbalanced braces — often an unescaped % or & inside a table cell."),
    (r"! LaTeX Error: Command \\(\w+) already defined",
     "Macro clash: \\{0} defined twice — likely a package conflict."),
    (r"! Dimension too large",
     "A length overflowed — usually a resizebox/includegraphics with a bad value."),
]


ENGINES = ("xelatex", "lualatex", "pdflatex")
# TeXShop/TeXstudio/VS Code style magic comment: % !TEX program = pdflatex
# (also % !TEX TS-program = ...). Read only near the top of the file.
TEX_PROGRAM_RE = re.compile(
    r"^\s*%\s*!\s*TEX\s+(?:TS-)?program\s*=\s*(\S+)", re.I)
DIRECTIVE_LINES = 20


def engine_from_directive(text: str) -> tuple[str | None, str | None]:
    """Read a ``% !TEX program = ...`` line from the first 20 lines.

    Returns ``(engine, None)`` for pdflatex, xelatex or lualatex,
    ``(None, value)`` for any other program (latexmk, pdflatexmk ...), and
    ``(None, None)`` when there is no such line.
    """
    for line in text.splitlines()[:DIRECTIVE_LINES]:
        match = TEX_PROGRAM_RE.match(line)
        if match:
            value = match.group(1)
            engine = value.lower()
            return (engine, None) if engine in ENGINES else (None, value)
    return None, None


# The context line TeX prints under an error (``l.12 \pdfgentounicode``)
# ends with the offending control sequence.
CONTEXT_LINE_RE = re.compile(r"^l\.\d+ (.*)$", re.M)


def pdftex_only_primitive(log_text: str) -> str | None:
    """Name the ``\\pdf...`` command behind an undefined-control-sequence error.

    XeTeX and LuaTeX lack most pdfTeX primitives (\\pdfgentounicode,
    \\pdfglyphtounicode, \\pdfminorversion ...), so such a deck needs pdfLaTeX.
    """
    log_text = unwrap_log(log_text)
    error = re.search(r"^! Undefined control sequence\.", log_text, re.M)
    if not error:
        return None
    context = CONTEXT_LINE_RE.search(log_text, error.end())
    command = re.search(r"(\\[A-Za-z@]+)\s*$", context.group(1)) if context else None
    if command and command.group(1).startswith("\\pdf"):
        return command.group(1)
    return None


def installed_engine(engine: str) -> Path | None:
    """Find a TeX engine in the usual install folders when PATH misses it."""
    home = Path.home()
    newest_first = lambda root, pattern: sorted(  # noqa: E731
        Path(root).glob(pattern), key=str, reverse=True)
    folders = [Path("/Library/TeX/texbin"),          # MacTeX
               *newest_first("/usr/local/texlive", "*/bin/*"),
               *newest_first("/opt/texlive", "*/bin/*"),
               *newest_first(home / "Library" / "TinyTeX" / "bin", "*"),
               *newest_first(home / ".TinyTeX" / "bin", "*"),
               *newest_first("C:/texlive", "*/bin/*"),
               home / "AppData" / "Local" / "Programs" / "MiKTeX" / "miktex"
               / "bin" / "x64"]
    for folder in folders:
        for name in (engine, engine + ".exe"):
            candidate = folder / name
            if candidate.is_file():
                return candidate
    return None


def find_error(log_text: str) -> tuple[str, str] | None:
    """Return (error_line, hint) for the first hard error in the log.

    The log is unwrapped first, so an error line is reported whole.
    """
    log_text = unwrap_log(log_text)
    for pattern, hint in TRIAGE:
        m = re.search(pattern, log_text)
        if m:
            line_m = re.search(re.escape(m.group(0)) + r".*?\nl\.(\d+)", log_text, re.S)
            loc = f" (source line {line_m.group(1)})" if line_m else ""
            text = hint(*m.groups()) if callable(hint) else hint.format(*m.groups())
            return m.group(0) + loc, text
    m = re.search(r"^! (.+)$", log_text, re.M)
    if m:
        return m.group(0), "Unrecognized error — read the log around this line."
    return None


def page_count(log_text: str) -> int | None:
    """Read TeX's output page count even when the log wraps mid-number.

    TeX hard-wraps long ``Output written on ...`` lines at about 79 columns.
    With a long output path, even ``13 pages`` can become ``1\n3 pages``.
    """
    match = re.search(
        r"Output written on .*?\(([\d\s]+?)p\s*a\s*g\s*e\s*s?\b",
        log_text,
        re.S,
    )
    if not match:
        return None
    digits = re.sub(r"\s+", "", match.group(1))
    return int(digits) if digits else None


# TeX hard-wraps log lines at max_print_line (79 columns by default).
MAX_PRINT_LINE = 79


def unwrap_log(log_text: str, width: int = MAX_PRINT_LINE) -> str:
    """Rejoin log lines that TeX hard-wrapped at ``width`` columns.

    A line of exactly ``width`` characters continues on the next one, so a
    warning such as ``Citation `key' on p`` / ``age 1 undefined`` is read
    whole wherever the break fell.
    """
    lines: list[str] = []
    pending = ""
    for line in log_text.split("\n"):
        pending += line
        if len(line) != width:
            lines.append(pending)
            pending = ""
    if pending:
        lines.append(pending)
    return "\n".join(lines)


# ``Citation `key' on page 3 undefined`` from LaTeX and natbib; biblatex uses
# straight quotes. The log is unwrapped first; the optional newline inside the
# key still covers a log written with a different line width.
UNDEFINED_RE = re.compile(
    r"(?:LaTeX|Package natbib) Warning: (Citation|Reference) [`']"
    r"([^'\s]+(?:\n[^'\s]+)?)'\s+on\s+page\s+(\d+)\s+undefined")
# hyperref's \\hyperref[key]{text} with no such label: the text still
# prints, but the link goes nowhere (a dead link, not a [?] or ??).
HYPER_UNDEFINED_RE = re.compile(
    r"LaTeX Warning: Hyper reference [`']([^'\s]+(?:\n[^'\s]+)?)'\s+on\s+"
    r"page\s+(\d+)\s+undefined")
UNDEFINED_SUMMARY_RE = re.compile(
    r"LaTeX Warning: There were undefined references"
    r"|Package natbib Warning: There were undefined citations")
BIBER_RERUN_RE = re.compile(r"Package biblatex Warning: Please \(re\)run Biber")
BIBTEX_RE = re.compile(r"\\bibliography\s*\{")
BIBLATEX_RE = re.compile(r"\\addbibresource\s*(?:\[[^]]*\])?\s*\{")


def undefined_references(log_text: str) -> dict:
    """Summarize unresolved citations and cross-references in a final log.

    Returns ``{"items": [{"kind", "key", "page"}...], "hyper": [...],
    "summary": bool, "biber_rerun": bool}``. Items are unique by kind and key
    (first page kept). ``hyper`` lists ``\\hyperref[key]`` targets that do
    not exist (dead links; nothing renders as ??). ``summary`` records
    LaTeX's or natbib's end-of-run notice, which can appear without per-key
    lines; ``biber_rerun`` records biblatex's request for a Biber run, whose
    citations are then unresolved.
    """
    log_text = unwrap_log(log_text)
    items: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for match in UNDEFINED_RE.finditer(log_text):
        kind = match.group(1).lower()
        key = match.group(2).replace("\n", "").strip()
        if (kind, key) in seen:
            continue
        seen.add((kind, key))
        items.append({"kind": kind, "key": key, "page": int(match.group(3))})
    hyper: list[dict] = []
    for match in HYPER_UNDEFINED_RE.finditer(log_text):
        key = match.group(1).replace("\n", "").strip()
        if key not in {item["key"] for item in hyper}:
            hyper.append({"kind": "hyper reference", "key": key,
                          "page": int(match.group(2))})
    return {"items": items, "hyper": hyper,
            "summary": bool(UNDEFINED_SUMMARY_RE.search(log_text)),
            "biber_rerun": bool(BIBER_RERUN_RE.search(log_text))}


def undefined_count(info: dict) -> int:
    """Count unresolved items; a bare summary or Biber request counts once.

    LaTeX's summary also follows a dead \\hyperref target alone; that is
    reported separately and does not count here.
    """
    unexplained = info["summary"] and not info.get("hyper")
    return len(info["items"]) or int(unexplained or info["biber_rerun"])


# A missing input leaves the tool's .bbl empty or useless: BibTeX's
# "I couldn't open database/style file", "I found no database files" (or
# \\bibdata/\\bibstyle), and Biber's "ERROR - Cannot find 'refs.bib'!".
MISSING_BIB_INPUT_RE = re.compile(
    r"I couldn't open (?:database|style) file"
    r"|I found no (?:database files|style file|\\bibdata command|\\bibstyle command)"
    r"|ERROR - Cannot find")


def run_bibliography(tool: str, tex: Path, build: Path, env: dict,
                     timeout: float) -> dict:
    """Run BibTeX or Biber for ``tex`` after the first engine pass.

    Both run from the source directory, the directory an in-place build uses,
    so a relative ``\\bibliography{../refs}`` or ``\\addbibresource{../refs.bib}``
    resolves; the .bbl and .blg go to ``build``. When the tool reports a
    missing database or style file and a prebuilt ``<stem>.bbl`` sits beside
    the source, the .bbl the tool wrote is discarded (or, for a build in the
    source directory, the previous one restored), so the prebuilt one still
    reaches the final passes.
    """
    bib: dict = {"tool": tool, "ran": False, "returncode": None}
    if shutil.which(tool) is None:
        bib["warning"] = f"{tool} not on PATH; citations stay undefined"
        return bib
    bbl = build / (tex.stem + ".bbl")
    in_place = build == tex.parent
    prior = bbl.read_bytes() if in_place and bbl.exists() else None
    run_env = dict(env)
    if tool == "biber":
        cmd = [tool, "--output-directory", str(build), tex.stem]
    else:
        # BibTeX writes <aux>.bbl and <aux>.blg beside the .aux it is given.
        # TeX Live's default openout_any=p refuses that for most absolute
        # paths and for any hidden folder. BibTeX opens no other output
        # file, so lifting the check for this one call is safe.
        cmd = [tool, str(build / tex.stem)]
        run_env["openout_any"] = "a"
        # biblatex's backend=bibtex writes <stem>-blx.bib next to the .aux,
        # so a separate build folder must be on BibTeX's search path too.
        if not in_place:
            run_env["BIBINPUTS"] = f"{build}{os.pathsep}" + run_env.get("BIBINPUTS", "")
    try:
        proc = subprocess.run(cmd, cwd=tex.parent, env=run_env,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        bib["warning"] = f"{tool} timed out after {timeout:g}s"
        return bib
    bib["ran"] = True
    bib["returncode"] = proc.returncode
    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        # BibTeX exits 1 on warnings (for example a missing entry) and 2 on
        # errors; either way the final log reports what is left.
        tail = output.strip().splitlines()[-3:]
        bib["warning"] = f"{tool} exited {proc.returncode}: " + " | ".join(tail)
    source_bbl = tex.parent / bbl.name
    fallback = prior is not None or (not in_place and source_bbl.exists())
    if fallback and MISSING_BIB_INPUT_RE.search(output):
        if prior is not None:
            bbl.write_bytes(prior)  # in-place build: put the user's .bbl back
        else:
            bbl.unlink(missing_ok=True)  # TeX then reads the source .bbl
        bib["kept_bbl"] = str(source_bbl)
        bib["warning"] = (bib.get("warning", f"{tool} reported a missing input")
                          + f"; kept the existing {source_bbl.name} beside the source")
    return bib


def bibliography_tool(tex: Path) -> str | None:
    """Return ``bibtex``, ``biber``, or None for the deck's bibliography."""
    src = tex_tree(tex)
    if BIBLATEX_RE.search(src):
        backend = re.search(r"backend\s*=\s*(\w+)", src)
        return "bibtex" if backend and backend.group(1).startswith("bibtex") \
            else "biber"
    if BIBTEX_RE.search(src):
        return "bibtex"
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("texfile", type=Path)
    ap.add_argument("--engine", default=None, choices=list(ENGINES),
                    help="default: the deck's %% !TEX program line, else xelatex")
    ap.add_argument("--build-dir", type=Path, default=None,
                    help="output directory (default: <texdir>/build)")
    ap.add_argument("--themes-dir", type=Path, default=None,
                    help="added to TEXINPUTS so \\usepackage{econ-slides-*} resolves")
    ap.add_argument("--passes", type=int, default=2)
    ap.add_argument("--timeout", type=float, default=600,
                    help="seconds allowed per engine or bibliography run (default 600)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()
    if args.passes <= 0:
        ap.error("--passes must be positive")
    if args.timeout <= 0:
        ap.error("--timeout must be positive")

    def fail_early(error: str, hint: str) -> int:
        """Report a failure before any engine run, as JSON with --json."""
        if args.json:
            print(json.dumps({"ok": False, "error": error, "hint": hint},
                             indent=2))
        else:
            print(f"error: {error} — {hint}", file=sys.stderr)
        return 1

    tex = args.texfile.resolve()
    if not tex.is_file():
        return fail_early(f"{tex} not found",
                          "pass the path of the deck's .tex file")
    # An explicit --engine wins; then the deck's own % !TEX program line.
    engine_note = None
    if args.engine:
        engine_source = "flag"
    else:
        directive, unsupported = engine_from_directive(
            tex.read_text(encoding="utf-8", errors="replace"))
        if directive:
            args.engine, engine_source = directive, "directive"
        else:
            args.engine, engine_source = "xelatex", "default"
            if unsupported:
                engine_note = (f"% !TEX program = {unsupported} is not "
                               "supported; using xelatex (pass --engine to "
                               "choose)")
    if not args.json:
        if engine_source == "directive":
            print(f"engine: {args.engine} (from % !TEX program)")
        if engine_note:
            print(f"note: {engine_note}")
    if shutil.which(args.engine) is None:
        found = installed_engine(args.engine)
        if found:
            return fail_early(
                f"{args.engine} is installed at {found.parent} but that "
                "folder is not on PATH",
                "add it to PATH, or open a new terminal or agent session "
                "after installing TeX")
        return fail_early(f"{args.engine} not found on PATH or in the usual "
                          "TeX folders",
                          "install TeX Live, MacTeX, TinyTeX or MiKTeX")

    build = (args.build_dir or tex.parent / "build").resolve()
    build.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    # Resolve before changing cwd to the deck directory. A caller may pass a
    # relative --themes-dir from the repository root.
    themes = (args.themes_dir or BUNDLED_THEMES).resolve()
    if not themes.is_dir():
        reason = ("--themes-dir does not exist" if args.themes_dir else
                  "the skill's scripts/ and themes/ must stay together in one "
                  "skill folder, or pass --themes-dir")
        return fail_early(f"themes directory {themes} not found", reason)
    # os.pathsep: ':' on Unix, ';' on Windows (TeX Live/MiKTeX expect it)
    sep = os.pathsep
    env["TEXINPUTS"] = f".{sep}{themes}{sep}" + env.get("TEXINPUTS", "")

    # BibTeX/Biber run from the source directory, which also stays on the
    # search path when the caller's BIBINPUTS/BSTINPUTS omit ".".
    for var in ("BIBINPUTS", "BSTINPUTS"):
        env[var] = f"{tex.parent}{sep}" + env.get(var, "")

    cmd = [args.engine, "-interaction=nonstopmode", "-halt-on-error",
           f"-output-directory={build}", tex.name]
    bib_tool = bibliography_tool(tex)
    # A bibliography needs one pass to write citations, the tool, and two more
    # passes so labels and citations settle.
    passes = max(args.passes, 3) if bib_tool else args.passes
    ok = True
    stdout = ""
    timed_out: str | None = None
    bib: dict | None = None
    for index in range(passes):
        try:
            proc = subprocess.run(cmd, cwd=tex.parent, env=env, capture_output=True,
                                  text=True, encoding="utf-8", errors="replace",
                                  timeout=args.timeout)
        except subprocess.TimeoutExpired:
            ok = False
            timed_out = f"{args.engine} timed out after {args.timeout:g}s"
            break
        stdout = proc.stdout
        if proc.returncode != 0:
            ok = False
            break
        if index == 0 and bib_tool:
            bib = run_bibliography(bib_tool, tex, build, env, args.timeout)

    log_path = build / (tex.stem + ".log")
    log_text = (log_path.read_text(encoding="utf-8", errors="replace")
                if log_path.exists() else stdout)
    pdf_path = build / (tex.stem + ".pdf")

    result: dict = {"ok": ok and pdf_path.exists(), "pdf": str(pdf_path),
                    "log": str(log_path), "engine": args.engine,
                    "engine_source": engine_source}
    if engine_note:
        result["engine_note"] = engine_note
    if bib is not None:
        result["bibliography"] = bib
    if result["ok"]:
        result["overfull"] = len(re.findall(r"^Overfull \\[hv]box", log_text, re.M))
        result["pages"] = page_count(log_text)
        undefined = undefined_references(log_text)
        result["undefined_refs"] = undefined_count(undefined)
        result["undefined"] = undefined["items"]
        result["dead_hyperrefs"] = [item["key"] for item in undefined["hyper"]]
    elif timed_out:
        result["error"] = timed_out
        result["hint"] = ("The engine did not finish. Look for an infinite loop "
                          "(a runaway \\loop, TikZ/pgfplots recursion, or a "
                          "prompt despite nonstopmode), or raise --timeout.")
    else:
        err = find_error(log_text)
        result["error"], result["hint"] = err if err else ("unknown", "inspect the log")
        primitive = (pdftex_only_primitive(log_text)
                     if args.engine in ("xelatex", "lualatex") and err
                     and err[0].startswith("! Undefined control sequence")
                     else None)
        if primitive:
            result["hint"] += (f" This looks like a pdfTeX-only primitive "
                               f"({primitive}): try --engine pdflatex, or "
                               "remove it for XeLaTeX/LuaLaTeX.")

    if args.json:
        print(json.dumps(result, indent=2))
    elif result["ok"]:
        print(f"OK: {result['pages']} pages, {result['overfull']} overfull box warnings, "
              f"{result['undefined_refs']} undefined citations/references")
        print(f"pdf: {pdf_path}")
        if result["undefined_refs"]:
            keys = ", ".join(f"{u['kind']} {u['key']}" for u in undefined["items"][:8])
            print("warning: unresolved citations or references render as [?] or ??"
                  + (f": {keys}" if keys else "")
                  + " — check_deck.py blocks delivery until they are fixed")
        if result["dead_hyperrefs"]:
            print("warning: \\hyperref targets with no \\label (dead links): "
                  + ", ".join(result["dead_hyperrefs"][:8])
                  + " — check_deck.py blocks delivery until they are fixed")
        if bib is not None and bib.get("warning"):
            print(f"warning: {bib['warning']}")
    else:
        print(f"FAILED: {result['error']}")
        print(f"hint: {result['hint']}")
        print(f"log: {log_path}")
    return 0 if result["ok"] else 1


def run() -> int:
    """Run main(), keeping a crash (exit 3) apart from a failed compile (1)."""
    for stream in (sys.stdout, sys.stderr):  # Windows ANSI code pages
        try:
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError):
            pass
    try:
        return main()
    except Exception as exc:  # noqa: BLE001  (report, never pass as a result)
        import traceback
        traceback.print_exc()
        print(f"error: compile_deck.py crashed ({type(exc).__name__}: {exc}); "
              "exit 3 means the helper failed, not the deck.", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(run())
