#!/usr/bin/env python3
"""Compile a Beamer deck or article script and triage what went wrong.

Usage:
    python3 scripts/compile_deck.py talk.tex [--engine xelatex] [--build-dir build]
                                             [--themes-dir PATH] [--passes 2]

Runs the engine non-interactively, parses the log, and prints a compact
human/machine-readable verdict: OK with page count, or the first real error
with its line number and a triage hint. Exit code 0 on success, 1 on failure.
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

TRIAGE = [
    (r"! LaTeX Error: File `([^']+)' not found",
     "Missing package or file: {0}. Install it (tlmgr install <pkg>) or fix the path."),
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


def find_error(log_text: str) -> tuple[str, str] | None:
    """Return (error_line, hint) for the first hard error in the log."""
    for pattern, hint in TRIAGE:
        m = re.search(pattern, log_text)
        if m:
            line_m = re.search(re.escape(m.group(0)) + r".*?\nl\.(\d+)", log_text, re.S)
            loc = f" (source line {line_m.group(1)})" if line_m else ""
            return m.group(0) + loc, hint.format(*m.groups())
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("texfile", type=Path)
    ap.add_argument("--engine", default="xelatex",
                    choices=["xelatex", "lualatex", "pdflatex"])
    ap.add_argument("--build-dir", type=Path, default=None,
                    help="output directory (default: <texdir>/build)")
    ap.add_argument("--themes-dir", type=Path, default=None,
                    help="added to TEXINPUTS so \\usepackage{econ-slides-*} resolves")
    ap.add_argument("--passes", type=int, default=2)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()
    if args.passes <= 0:
        ap.error("--passes must be positive")

    tex = args.texfile.resolve()
    if not tex.exists():
        print(f"error: {tex} not found", file=sys.stderr)
        return 1
    if shutil.which(args.engine) is None:
        print(f"error: {args.engine} not on PATH — install TeX Live / MacTeX / MiKTeX", file=sys.stderr)
        return 1

    build = (args.build_dir or tex.parent / "build").resolve()
    build.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    # Resolve before changing cwd to the deck directory. A caller may pass a
    # relative --themes-dir from the repository root.
    themes = (args.themes_dir or Path(__file__).resolve().parent.parent / "themes").resolve()
    # os.pathsep: ':' on Unix, ';' on Windows (TeX Live/MiKTeX expect it)
    sep = os.pathsep
    env["TEXINPUTS"] = f".{sep}{themes}{sep}" + env.get("TEXINPUTS", "")

    cmd = [args.engine, "-interaction=nonstopmode", "-halt-on-error",
           f"-output-directory={build}", tex.name]
    ok = True
    for _ in range(args.passes):
        proc = subprocess.run(cmd, cwd=tex.parent, env=env,
                              capture_output=True, text=True, timeout=600)
        if proc.returncode != 0:
            ok = False
            break

    log_path = build / (tex.stem + ".log")
    log_text = (log_path.read_text(encoding="utf-8", errors="replace")
                if log_path.exists() else proc.stdout)
    pdf_path = build / (tex.stem + ".pdf")

    result: dict = {"ok": ok and pdf_path.exists(), "pdf": str(pdf_path),
                    "log": str(log_path)}
    if result["ok"]:
        result["overfull"] = len(re.findall(r"^Overfull \\[hv]box", log_text, re.M))
        result["pages"] = page_count(log_text)
    else:
        err = find_error(log_text)
        result["error"], result["hint"] = err if err else ("unknown", "inspect the log")

    if args.json:
        print(json.dumps(result, indent=2))
    elif result["ok"]:
        print(f"OK: {result['pages']} pages, {result['overfull']} overfull box warnings")
        print(f"pdf: {pdf_path}")
    else:
        print(f"FAILED: {result['error']}")
        print(f"hint: {result['hint']}")
        print(f"log: {log_path}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
