#!/usr/bin/env python3
"""Audit a compiled Beamer deck against econ-slides geometry gates and review prompts.

Usage:
    python3 scripts/check_deck.py build/talk.pdf [--tex talk.tex] [--log build/talk.log]
                                                 [--render-dir pages]
                                                 [--baseline-json baseline.json]
                                                 [--json]

Checks (geometry measured from the PDF itself, not guessed from source):
  edge-overflow   any text placed outside the safe page margins
  wrapped-title   a frame title that runs to a second line
  wrapped-bullet  a bullet whose text wraps to further lines
  density         more than MAX_BULLETS top-level bullets on one slide
  overfull        Overfull \\hbox/\\vbox warnings parsed from the .log
  compile-error   a TeX error (a ``! ...`` line) in the .log: a halted or
                  ``nonstopmode`` build, a missing figure, an undefined macro
  missing-glyph   a character the font lacks (``Missing character`` in the
                  .log), such as a β or ≥ typed in text: it does not render
  lost-char       a dropped character that is usually harmless: a stray
                  character inside a TikZ picture (nullfont) or an invisible
                  one (U+200B); a note, no deduction
  undefined-ref   an undefined citation or cross-reference: LaTeX/natbib/biblatex
                  warnings in the .log, or a [?], (?) or ?? marker in the PDF
                  text (biblatex prints a missing key itself and natbib's
                  \\citet a bare ?, so only --log catches those). A deck
                  that shows such a marker as literal text declares it with
                  a source comment ``% econ-slides: allow-literal-marker ??``
                  (or --allow-literal-marker '??'); the marker is then waived
                  only when --log is given and reports no undefined key
  pause-chain     3+ \\pause in one frame (overlay used as decoration)
  dead-link       a navigation target is absent from the TeX source, or a
                  \\hyperref[key] target the .log reports as undefined
  arrow-bullet    a right arrow is used as a list marker
  question-label  an opening object is called "economic question"
  question-subtitle a concise question is hidden in a generic frame subtitle
  roadmap-emphasis a Roadmap uses boldface instead of regular-weight orientation
  exhibit-reading a static table or figure has no bottom interpretation line
  conclusion-link a conclusion frame contains Beamer navigation
  conclusion-density a conclusion carries more than three bullet items

Score starts at 100 and deducts only for objective or strongly actionable
findings. TeX errors in the log, characters missing from the font, edge
overflow, serious overfull boxes, navigation collisions, dead links,
undefined citations or references, prohibited arrow markers, the disallowed
question label, and conclusion links are hard blockers. Wrapped
text, density, sparse layout, prose columns, emphasis, exhibit readings, and
conclusion density are review prompts: judge
them against the paper and target deck, and never trigger filler or a forced
structure.
--render-dir writes one PNG per page
at 200 DPI for the visual pass (box-interior overflow and title-bar/toprule
merges are invisible to every static check — always eyeball the renders).

For a scoped edit to an existing deck, first save the untouched checker's JSON
output and pass it back with --baseline-json. Objective blockers are compared
as a multiset of semantic signatures: page numbers and volatile measurements
are ignored, but text/link/title context and occurrence counts are retained.
Inherited blockers remain visible but do not fail the edited deck; new
blockers still fail. Undefined citations and references are never waived:
a [?] or ?? on screen fails every deck, inherited or not. Review prompts and
visual inspection remain necessary.

--log must be the log of the build that made the PDF: its first line is a TeX
engine banner, and its ``Output written on`` line names a file with the PDF's
stem and the PDF's page count. Any other file (an empty log, another deck's
log, the .tex itself) stops the check with exit 2 instead of passing as clean.

Without --tex the source checks (dead links, arrow bullets, the question
label, conclusion links, pause chains, exhibit readings, and the other source
prompts) do not run; without --log the compile-error, missing-glyph,
overfull-box and log-based undefined-reference checks do not run. Such a run
is partial: it lists the skipped checks, and its verdict is "incomplete"
instead of "ship".

Exit status: 0 = ship (full check, no blocker); 1 = the deck is not ready
(must fix, fix recommended, or incomplete); 2 = the check could not run (bad
arguments, a missing or unreadable input, or no PyMuPDF); 3 = the checker
itself crashed. Only 0 and 1 carry a verdict.

Requires PyMuPDF (requirements.txt). If this Python lacks it, use a venv
or ``uv run --with pymupdf python ...`` rather than ``pip install --user``.
"""

from __future__ import annotations

import argparse
from collections import defaultdict, deque
import json
import os
import re
import sys
from pathlib import Path

# Sibling helpers imported by path so the script runs from any directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from compile_deck import (  # noqa: E402  (no PyMuPDF)
        missing_characters, undefined_references, unwrap_log)
except ImportError as exc:  # pragma: no cover
    print(f"error: check_deck.py cannot import its sibling scripts ({exc}). "
          "Keep check_deck.py, compile_deck.py and check_script.py together "
          "in the skill's scripts/ folder.", file=sys.stderr)
    sys.exit(2)

try:
    import pymupdf as fitz  # PyMuPDF >= 1.24 (``fitz`` is deprecated in 2.x)
except ImportError:  # pragma: no cover
    try:
        import fitz  # older PyMuPDF releases
    except ImportError:
        print("error: PyMuPDF is not importable by this Python "
              f"({sys.executable}).\n"
              "  Run the script with an interpreter that has it, e.g. a venv:\n"
              "    python3 -m venv ~/.venvs/econ-slides\n"
              "    ~/.venvs/econ-slides/bin/python -m pip install pymupdf\n"
              "    ~/.venvs/econ-slides/bin/python <this script> ...\n"
              "  or: uv run --with pymupdf python <this script> ...",
              file=sys.stderr)
        sys.exit(2)

# NOTE: en/em dashes are deliberately NOT markers — they appear as empty
# table cells ("---") and would false-positive the bullet checks.
BULLET_GLYPHS = "•▪■◦‣⋆★✓✔"
ARROW_GLYPHS = "⇒→↳"
EDGE_MARGIN_PT = 6        # text closer than this to the paper edge = overflow
TITLE_ZONE = 0.18         # top fraction of the page that can hold the title
MAX_BULLETS = 5           # more than this prompts a hierarchy review
MAX_TEXT_LINES = 20       # review threshold; the user's dense decks often reach this
MIN_CONTENT_BOTTOM = 0.68  # review an accidental empty lower third; never add filler
MIN_LAYOUT_LINES = 2       # title + one short content line is enough to judge

DEDUCT = {"edge-overflow": 15, "wrapped-title": 0, "wrapped-bullet": 0,
          "density": 0, "overfull": 5, "pause-chain": 0,
          "nav-footer-overlap": 5, "layout-balance": 0, "dead-link": 10,
          "emphasis-overuse": 0, "prose-columns": 0, "arrow-bullet": 5,
          "question-label": 5, "question-subtitle": 0,
          "roadmap-emphasis": 0,
          "exhibit-reading": 0, "conclusion-link": 10,
          "conclusion-density": 0, "undefined-ref": 10,
          "compile-error": 15, "missing-glyph": 10, "lost-char": 0}
HARD_BLOCKERS = {"edge-overflow", "overfull", "nav-footer-overlap",
                 "dead-link", "arrow-bullet", "question-label",
                 "conclusion-link", "undefined-ref", "compile-error",
                 "missing-glyph"}
# Blockers that a --baseline-json comparison never treats as inherited: an
# unresolved [?] or ?? is visible to the audience whoever introduced it.
NON_WAIVABLE_BLOCKERS = {"undefined-ref"}
# Checks that need an input the PDF alone cannot supply.
TEX_ONLY_CHECKS = ("dead-link", "arrow-bullet", "question-label",
                   "question-subtitle", "roadmap-emphasis", "exhibit-reading",
                   "conclusion-link", "conclusion-density", "pause-chain",
                   "emphasis-overuse", "prose-columns")
LOG_ONLY_CHECKS = ("compile-error", "missing-glyph", "overfull",
                   "undefined-ref (log warnings)")
EXIT_SHIP, EXIT_NOT_READY, EXIT_CANNOT_RUN, EXIT_CRASH = 0, 1, 2, 3
# What LaTeX, natbib, and the standard styles print for an unresolved key:
# [?] or [?, ?] (\cite), (?) (natbib), and a bold ?? (\ref). ``What??`` in
# prose is not matched because the marker must stand alone.
UNRESOLVED_MARKER_RE = re.compile(
    r"\[\?(?:\s*,\s*\?)*\]|\(\?(?:\s*[,;]\s*\?)*\)|(?<![\w?])\?\?(?![\w?])")
# A deck that shows one of those markers as literal text (a quiz slide, a
# "(?)" in a reproduced questionnaire) declares it in its source:
#   % econ-slides: allow-literal-marker (?) ??
ALLOW_MARKER_RE = re.compile(r"%\s*econ-slides:\s*allow-literal-marker\b([^\n]*)")
# A log is trusted only if it is a TeX log for this PDF: an engine banner
# ("This is pdfTeX", "This is XeTeX", "This is LuaHBTeX", MiKTeX's pdfTeX ...)
# and an "Output written on <stem>.pdf|.xdv|.dvi (N pages" line.
TEX_BANNER_RE = re.compile(r"This is [\w.\u03b5-]*TeX\b")
OUTPUT_WRITTEN_RE = re.compile(
    r"Output written on\s+(.+?)\s+\(\s*([\d\s]+?)\s*pages?\b", re.S)
# TeX errors start a line with "!" ("! Undefined control sequence.",
# "!pdfTeX error: ..."). The fatal-error and emergency-stop lines only
# restate an earlier error, so they are reported only when nothing else is.
TEX_ERROR_RE = re.compile(r"^!\s?(\S.*)$", re.M)
TEX_ERROR_ECHO_RE = re.compile(r"^(?:\s*==> Fatal error occurred|Emergency stop)")
MAX_COMPILE_ERRORS = 10


def normalize_marker(marker: str) -> str:
    """Collapse whitespace so ``[?,?]`` and ``[?, ?]`` compare equal."""
    return re.sub(r"\s*([,;])\s*", r"\1 ", re.sub(r"\s+", " ", marker.strip()))


def parse_allowed_markers(values: list[str]) -> set[str]:
    """Validate literal-marker allowances; raise ValueError on anything else."""
    allowed = set()
    for value in values:
        leftover = UNRESOLVED_MARKER_RE.sub(" ", value).strip()
        markers = UNRESOLVED_MARKER_RE.findall(value)
        if leftover or not markers:
            raise ValueError(
                f"allow-literal-marker {value.strip()!r} is not a list of "
                "unresolved-key markers; use ??, (?), [?] or [?, ?]")
        allowed.update(normalize_marker(marker) for marker in markers)
    return allowed


MATH_FONT_RE = re.compile(r"CMMI|CMSY|CMEX|MSBM|MSAM|Math|rsfs", re.I)
ENUM_MARKER_RE = re.compile(r"^\d{1,2}\.$")


def _is_gray(srgb: int) -> bool:
    """Mid-gray text (roadmap/transition slides gray out completed items)."""
    r, g, b = (srgb >> 16) & 255, (srgb >> 8) & 255, srgb & 255
    return abs(r - g) < 12 and abs(g - b) < 12 and 90 <= (r + g + b) / 3 <= 200


def _is_marker_token(token: str) -> bool:
    """A span/line head that is a list marker: bullet glyph, arrow, or '1.'."""
    return (bool(token) and token[0] in BULLET_GLYPHS + ARROW_GLYPHS) \
        or bool(ENUM_MARKER_RE.match(token))


def page_lines(page: fitz.Page) -> list[dict]:
    """Flatten a page into text lines with bbox, font size, and text."""
    lines = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            spans = line["spans"]
            if not spans:
                continue
            text = "".join(s["text"] for s in spans)
            if not text.strip():
                continue
            lines.append({
                "text": text, "bbox": fitz.Rect(line["bbox"]),
                "size": max(s["size"] for s in spans),
                "math": any(MATH_FONT_RE.search(s["font"]) for s in spans),
                "gray": all(_is_gray(s.get("color", 0)) for s in spans),
                "x_text": next((fitz.Rect(s["bbox"]).x0 for s in spans
                                if s["text"].strip()
                                and not _is_marker_token(s["text"].strip())),
                               fitz.Rect(spans[0]["bbox"]).x0),
            })
    lines.sort(key=lambda l: (l["bbox"].y0, l["bbox"].x0))
    return lines


def is_marker_line(line: dict) -> bool:
    """A line that starts a list item: bullet/arrow glyph or a '1.' label.

    The glyph may extract with or without a following space, so no separator
    is required. Dashes are not in the glyph set (see note above), which is
    what keeps '---' table cells out of the bullet checks.
    """
    head = line["text"].lstrip()
    if not head:
        return False
    if head[0] in BULLET_GLYPHS + ARROW_GLYPHS:
        return True
    return bool(re.match(r"^\d{1,2}\.(\s|$)", head))


def has_table_rules(page: fitz.Page) -> bool:
    """A booktabs table draws >=2 horizontal rules spanning real width."""
    W = page.rect.width
    rules = 0
    for d in page.get_drawings():
        r = d["rect"]
        if r.width > 0.30 * W and r.height < 2.5:
            rules += 1
    return rules >= 2


def footer_key(page: fitz.Page, footer_zone: float = 0.93) -> str:
    """The footer text (frame number) — overlay builds of one frame share it."""
    H = page.rect.height
    return " ".join(l["text"].strip() for l in page_lines(page)
                    if l["bbox"].y0 >= H * footer_zone)


def has_frame_counter(footer: str) -> bool:
    """A footer can group overlays only when it exposes a frame counter.

    Adjacent distinct frames may share a static institutional footer. Treating
    those as builds would skip checks on every page but the last.
    """
    return bool(re.search(r"\bA\s*\d+\b|\b\d+\s*/\s*\d+\b", footer))


def frame_title_key(page: fitz.Page) -> str:
    """Return the largest top-zone text, used to distinguish real frames.

    Overlay pages share both a frame counter and title. A following
    ``noframenumbering`` frame can share the counter but has a different title;
    footer-only grouping would otherwise skip the previous frame's audit.
    """
    H = page.rect.height
    top = [line for line in page_lines(page)
           if line["bbox"].y0 < H * TITLE_ZONE and not is_marker_line(line)]
    if not top:
        return ""
    largest = max(line["size"] for line in top)
    title = [line["text"].strip() for line in top
             if line["size"] >= largest - 0.35]
    return re.sub(r"\s+", " ", " ".join(title)).strip().lower()


def check_page(page: fitz.Page, pno: int, footer_zone: float = 0.93,
               final: bool = True) -> list[dict]:
    findings = []
    W, H = page.rect.width, page.rect.height
    lines = page_lines(page)
    body = [l for l in lines if l["bbox"].y1 < H * footer_zone]

    # --- edge overflow ---
    for l in body:
        if l["bbox"].x1 > W - EDGE_MARGIN_PT or l["bbox"].x0 < 2:
            findings.append({"check": "edge-overflow", "page": pno,
                             "detail": f"text reaches x={l['bbox'].x1:.0f} of {W:.0f}: "
                                       f"{l['text'][:60]!r}"})

    # intermediate overlay builds are partial by design: only edge overflow
    # is meaningful on them ("unfold points one by one" must not be punished)
    if not final:
        return findings

    # --- wrapped title: >1 line in title-size font inside the title zone ---
    # threshold is RELATIVE to this page's body size so 10pt decks and
    # stock themes are covered too (title fonts run >=1.04x the body)
    below = [l["size"] for l in body if l["bbox"].y0 >= H * TITLE_ZONE]
    body_size = sorted(below)[len(below) // 2] if below else 11.0
    title_thresh = max(body_size * 1.04, 11.0)
    title_lines = [l for l in body if l["bbox"].y0 < H * TITLE_ZONE
                   and l["size"] >= title_thresh and not is_marker_line(l)]
    if len(title_lines) > 1:
        # tolerate title+subtitle: subtitle is smaller; equal-size pairs = a wrap
        sizes = sorted({round(l["size"], 1) for l in title_lines}, reverse=True)
        top = [l for l in title_lines if round(l["size"], 1) == sizes[0]]
        if len(top) > 1:
            findings.append({"check": "wrapped-title", "page": pno,
                             "detail": f"frame title spans {len(top)} lines: "
                                       f"{top[0]['text'][:50]!r} …"})

    # --- bullets: count and wrap detection ---
    marker_lines = [l for l in body if is_marker_line(l)]
    # top level = the shallowest marker indent on this page (absolute
    # thresholds misclassify nested items in enumerate+itemize stacks)
    top_level = []
    if marker_lines:
        # Split marker indents at column-sized gaps; within each column, the
        # shallowest indent is top-level. This also covers deliberately
        # indented blocks whose bullets begin far right of the page margin.
        ordered = sorted(marker_lines, key=lambda line: line["bbox"].x0)
        groups: list[list[dict]] = [[ordered[0]]]
        for line in ordered[1:]:
            if line["bbox"].x0 - groups[-1][-1]["bbox"].x0 > W * 0.20:
                groups.append([line])
            else:
                groups[-1].append(line)
        for group in groups:
            min_x = min(line["bbox"].x0 for line in group)
            top_level.extend(line for line in group
                             if line["bbox"].x0 < min_x + 5)
    if len(top_level) > MAX_BULLETS:
        findings.append({"check": "density", "page": pno,
                         "detail": f"{len(top_level)} top-level bullets "
                                   f"(review threshold {MAX_BULLETS})"})

    for i, l in enumerate(body):
        if not is_marker_line(l):
            continue
        # continuation: a following non-marker line left-aligned with this
        # bullet's text start, within two text lines vertically
        for m in body[i + 1:]:
            if m["bbox"].y0 - l["bbox"].y1 > 2.2 * l["size"]:
                break
            if is_marker_line(m):
                break
            # beamer indents wrapped lines up to ~6pt right of the text start
            if -2.5 < m["x_text"] - l["x_text"] < 8.5 and m["bbox"].y0 > l["bbox"].y0 + 2:
                findings.append({"check": "wrapped-bullet", "page": pno,
                                 "detail": f"bullet wraps: {l['text'][:60]!r}"})
                break

    # exhibit slides get a larger line budget: booktabs tables (drawn rules)
    # and math-heavy slides (display equations fragment into many "lines" —
    # every \underbrace label and shifted baseline counts separately)
    math_share = sum(1 for l in body if l["math"]) / max(1, len(body))
    if len(body) > MAX_TEXT_LINES and not has_table_rules(page) \
            and math_share < 0.25:
        findings.append({"check": "density", "page": pno,
                         "detail": f"{len(body)} extracted text lines "
                                   f"(review threshold {MAX_TEXT_LINES})"})

    # --- severe visual imbalance: a review prompt, never a padding target ---
    # Dividers/title pages are exempt. Whitespace can be deliberate emphasis;
    # this check only asks for a visual decision when content ends very early.
    gray_share = sum(1 for l in body if l.get("gray")) / max(1, len(body))
    content = [l for l in body if l["bbox"].y1 <= H * 0.85]  # exclude nav pills
    # exemptions: title page; roadmap/outline frames (sparse by design);
    # gray-heavy transitions. Appendix backups are audience-facing slides and
    # receive the same vertical-rhythm review as the main deck.
    title_text = " ".join(l["text"] for l in body
                          if l["bbox"].y0 < H * TITLE_ZONE).lower()
    is_roadmap = bool(re.search(r"roadmap|outline|agenda|plan of the talk",
                                title_text))
    is_title_page = pno == 1 and not footer_key(page, footer_zone) \
        and not marker_lines
    if (not is_title_page and not is_roadmap
            and len(content) >= MIN_LAYOUT_LINES and gray_share < 0.4):
        bottom = max(l["bbox"].y1 for l in content)
        for info in page.get_image_info():
            rect = fitz.Rect(info["bbox"])
            area_share = abs(rect) / max(1, W * H)
            is_picture_slide = area_share >= 0.65 and not marker_lines \
                and len(content) <= 3
            if 0.005 < area_share < 0.65 or is_picture_slide:
                bottom = max(bottom, min(rect.y1, H * 0.85))
        # TikZ and other vector figures are drawings rather than images.
        # Count substantial diagrams, but ignore tiny rules and backgrounds.
        for drawing in page.get_drawings():
            rect = fitz.Rect(drawing["rect"])
            area_share = abs(rect) / max(1, W * H)
            if (rect.width > 20 and rect.height > 20
                    and 0.003 < area_share < 0.65
                    and rect.y0 > H * TITLE_ZONE and rect.y1 < H * 0.88):
                bottom = max(bottom, rect.y1)
            # PDF rectangles and TikZ axes often extract as separate
            # zero-thickness strokes rather than one drawing bbox.
            elif (rect.width > W * 0.20 and rect.height < 2
                  and H * TITLE_ZONE < rect.y1 < H * 0.88):
                bottom = max(bottom, rect.y1)
            elif (rect.height > H * 0.10 and rect.width < 2
                  and rect.y0 > H * TITLE_ZONE and rect.y1 < H * 0.88):
                bottom = max(bottom, rect.y1)
        if bottom / H < MIN_CONTENT_BOTTOM:
            findings.append({"check": "layout-balance", "page": pno,
                             "detail": f"content stops at {bottom / H:.0%} of page "
                                       f"height — review vertical rhythm; merge if "
                                       "redundant, deepen only with source-supported "
                                       "content, and never invent an exhibit"})
    return findings


def check_nav_overlap(page: fitz.Page, pno: int) -> list[dict]:
    """Nav buttons (link annotations) must not overlap footer text."""
    findings = []
    H = page.rect.height
    # bottom zone includes takeaway lines, not just the page number — a
    # centered \Takeaway running under the nav pills is a real collision
    footer_lines = [l for l in page_lines(page) if l["bbox"].y0 > H * 0.78]
    if not footer_lines:
        return findings
    for link in page.get_links():
        # the drawn button pill extends ~3pt beyond the clickable rect
        r = fitz.Rect(link["from"]) + (-3, -3, 3, 3)
        for fl in footer_lines:
            inter = r & fl["bbox"]
            if inter.is_empty:
                continue
            # a button's own label sits fully inside the link rect — skip it
            if abs(inter) > 0.8 * abs(fl["bbox"]):
                continue
            if inter.width > 1 and inter.height > 0.5:
                findings.append({"check": "nav-footer-overlap", "page": pno,
                                 "detail": f"button overlaps footer text "
                                           f"{fl['text'][:20]!r} by "
                                           f"{inter.width:.1f}x{inter.height:.1f}pt"})
                break
    return findings


def check_unresolved_markers(page: fitz.Page, pno: int,
                             allowed: set[str] | frozenset[str] = frozenset(),
                             ) -> list[dict]:
    """Flag the rendered placeholders of undefined citations and references.

    Markers the deck declares as literal text come back flagged
    ``allowed_literal``; main() waives them only when the log is clean.
    """
    markers = [normalize_marker(m)
               for m in UNRESOLVED_MARKER_RE.findall(page.get_text())]
    findings = []
    blocked = [m for m in markers if m not in allowed]
    permitted = [m for m in markers if m in allowed]
    if blocked:
        shown = ", ".join(sorted(set(blocked)))
        findings.append({
            "check": "undefined-ref", "page": pno,
            "detail": f"unresolved citation/reference marker {shown} "
                      f"x{len(blocked)} in the PDF text — define the key, "
                      "run BibTeX/Biber (compile_deck.py does), or remove it"})
    if permitted:
        shown = ", ".join(sorted(set(permitted)))
        findings.append({
            "check": "undefined-ref", "page": pno, "allowed_literal": True,
            "detail": f"marker {shown} x{len(permitted)} is declared literal "
                      "text (allow-literal-marker); pass --log so a clean log "
                      "can waive it"})
    return findings


def read_log(log_path: Path, pdf_path: Path, pdf_pages: int) -> tuple[str, list[str]]:
    """Return the text of a log that belongs to this PDF, plus notes.

    Raises ValueError when the file is not a TeX log, records no output, or
    names a different file or page count than the PDF, so that an empty or
    foreign log can never stand in for a clean one.
    """
    text = log_path.read_text(encoding="utf-8", errors="replace")
    head = [line.strip() for line in text.lstrip("\ufeff").splitlines()[:3]]
    if not any(TEX_BANNER_RE.match(line) for line in head):
        raise ValueError(
            f"{log_path} is not a TeX log (its first line has no "
            "'This is ...TeX' banner); pass the .log written by the build "
            f"that made {pdf_path.name}")
    flat = unwrap_log(text)
    outputs = OUTPUT_WRITTEN_RE.findall(flat)
    if not outputs:
        error = TEX_ERROR_RE.search(flat)
        reason = f" (it stops at {error.group(0).strip()!r})" if error else ""
        raise ValueError(
            f"{log_path} records no output{reason}, so {pdf_path.name} comes "
            "from an earlier build; fix the error, recompile, and pass the "
            "new log")
    name, pages = outputs[-1]
    written = re.split(r"[\\/]", name.strip().strip('"'))[-1]
    written_stem = written.rsplit(".", 1)[0] if "." in written else written
    pages = int(re.sub(r"\s+", "", pages))
    if written_stem != pdf_path.stem:
        raise ValueError(
            f"{log_path} was written for {written}, not {pdf_path.name}; pass "
            "the log from the build that made this PDF")
    if pages != pdf_pages:
        raise ValueError(
            f"{log_path} records {pages} page(s) but {pdf_path.name} has "
            f"{pdf_pages}; the log is from another build, so recompile and "
            "pass its log")
    notes = []
    age = pdf_path.stat().st_mtime - log_path.stat().st_mtime
    if age > 120:
        notes.append(
            f"{log_path.name} is {age / 60:.0f} min older than {pdf_path.name}; "
            "make sure it comes from the build that made this PDF")
    return text, notes


def compile_errors(text: str) -> list[dict]:
    """Report the TeX errors (``! ...`` lines) recorded in a log."""
    flat = unwrap_log(text)
    matches = list(TEX_ERROR_RE.finditer(flat))
    errors = []
    for index, m in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(flat)
        line_m = re.search(r"^l\.(\d+)", flat[m.end():min(end, m.end() + 2000)],
                           re.M)
        errors.append((m.group(0).strip(), line_m.group(1) if line_m else None))
    real = [e for e in errors if not TEX_ERROR_ECHO_RE.match(e[0].lstrip("! "))]
    findings = []
    for message, line in (real or errors)[:MAX_COMPILE_ERRORS]:
        where = f" (source line {line})" if line else ""
        findings.append({
            "check": "compile-error", "page": None,
            "detail": f"TeX error {message!r}{where} — the build did not "
                      "finish cleanly; fix it and recompile "
                      "(compile_deck.py prints a hint)"})
    return findings


def missing_character_findings(text: str) -> list[dict]:
    """Report characters the font lacks; no page numbers, so a baseline matches."""
    findings = []
    for item in missing_characters(text):
        shown = repr(item["char"])
        code = f" ({item['code']})" if item["code"] else ""
        if item["kind"] == "glyph":
            findings.append({
                "check": "missing-glyph", "page": None,
                "detail": f"{shown}{code} is missing from font {item['font']} "
                          "and does not render — use math mode or a font "
                          "that has it"})
        elif item["kind"] == "nullfont":
            findings.append({
                "check": "lost-char", "page": None,
                "detail": f"a character ({shown}) typed inside a TikZ/PGF "
                          "picture outside a node was dropped — check that "
                          "picture for a stray character"})
        else:
            findings.append({
                "check": "lost-char", "page": None,
                "detail": f"invisible character {item['code']} is not in font "
                          f"{item['font']} — usually harmless; remove it from "
                          "the source"})
    return findings


def check_log(text: str) -> list[dict]:
    findings = compile_errors(text)
    findings += missing_character_findings(text)
    for m in re.finditer(r"^Overfull \\([hv])box \(([\d.]+)pt too \w+\)", text, re.M):
        if float(m.group(2)) > 2.0:
            findings.append({"check": "overfull", "page": None,
                             "detail": f"\\{m.group(1)}box {m.group(2)}pt too wide/tall"})
    undefined = undefined_references(text)
    for item in undefined["items"]:
        findings.append({"check": "undefined-ref", "page": None,
                         "detail": f"undefined {item['kind']} {item['key']!r} "
                                   f"(log, TeX page {item['page']}) — renders as "
                                   "[?] or ??"})
    for item in undefined["hyper"]:
        findings.append({"check": "dead-link", "page": None,
                         "detail": f"navigation target {item['key']!r} is not "
                                   "defined"})
    if not undefined["items"] and undefined["biber_rerun"]:
        findings.append({"check": "undefined-ref", "page": None,
                         "detail": "biblatex asks for a Biber run — citations are "
                                   "unresolved; compile with compile_deck.py"})
    elif not undefined["items"] and not undefined["hyper"] \
            and undefined["summary"]:
        findings.append({"check": "undefined-ref", "page": None,
                         "detail": "the log reports undefined references — rerun "
                                   "LaTeX or fix the missing keys"})
    return findings


def tex_tree(tex_path: Path, seen: set[Path] | None = None,
             strip_comments: bool = True, root: Path | None = None) -> str:
    """Read a TeX source plus local \\input/\\include files for static checks.

    TeX resolves a nested \\input relative to the main file's folder (where
    the build runs), not the including file's, so the root folder is tried
    first and the including file's folder second.
    """
    seen = seen or set()
    path = tex_path.resolve()
    if path in seen or not path.is_file():
        return ""
    seen.add(path)
    root = root or path.parent
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if strip_comments:
        src = re.sub(r"(?<!\\)%[^\n]*", "", src)

    def expand(match: re.Match) -> str:
        child = Path(match.group(1).strip())
        if child.suffix == "":
            child = child.with_suffix(".tex")
        if not child.is_absolute():
            child = next((folder / child for folder in (root, path.parent)
                          if (folder / child).is_file()), root / child)
        return tex_tree(child, seen, strip_comments, root)

    return re.sub(r"\\(?:input|include)\s*\{([^{}]+)\}", expand, src)


def command_argument(src: str, command: str) -> str | None:
    """Return a command's first mandatory argument, preserving nested braces.

    A regex such as ``[^{}]*`` stops at the first semantic-color command. That
    made ``\\framesubtitle{Can \\textcolor{...}{...}?}`` invisible to the
    question-placement review even though colored concepts are normal in this
    skill. Overlay and short-title specifications are skipped before scanning
    the balanced mandatory argument.
    """
    match = re.search(rf"\\{re.escape(command)}\b", src)
    if not match:
        return None
    pos = match.end()
    prefix = re.match(r"\s*(?:<[^>]*>\s*)?(?:\[[^]]*\]\s*)?", src[pos:])
    pos += prefix.end() if prefix else 0
    if pos >= len(src) or src[pos] != "{":
        return None

    depth = 0
    start = pos + 1
    for index in range(pos, len(src)):
        char = src[index]
        escaped = index > 0 and src[index - 1] == "\\"
        if escaped:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return src[start:index]
    return None


def check_tex(tex_path: Path) -> list[dict]:
    findings = []
    src = tex_tree(tex_path)
    appendix_match = re.search(r"\\AppendixStart|\\appendix\b", src)
    appendix_at = appendix_match.start() if appendix_match else len(src) + 1
    frames = []
    for fm in re.finditer(
            r"\\begin\s*\{frame\}(?:<[^>]*>)?(?:\[[^]]*\])?"
            r"(.*?)\\end\s*\{frame\}", src, re.S):
        frame_src = fm.group(1)
        title_match = re.match(r"\s*\{([^{}]*)\}", frame_src)
        if not title_match:
            title_match = re.search(r"\\frametitle\s*\{([^{}]*)\}", frame_src)
        title = title_match.group(1).strip() if title_match else ""
        title_plain = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^]]*\])?", "", title)
        title_plain = re.sub(r"[{}~]", "", title_plain)
        title_plain = re.sub(r"\s+", " ", title_plain).strip().lower()
        frames.append({"src": frame_src, "title": title,
                       "plain": title_plain, "appendix": fm.start() > appendix_at})
        n_pause = frame_src.count(r"\pause")
        if n_pause >= 3:
            findings.append({"check": "pause-chain", "page": None,
                             "detail": f"{n_pause} \\pause in one frame "
                                       f"({title[:40] if title else '?'}) — "
                                       "overlay as decoration; build reasoning instead"})
        n_keyidea = frame_src.count(r"\KeyIdea")
        n_resultbox = len(re.findall(r"\\begin\s*\{ResultBox\}", frame_src))
        n_primary = n_keyidea + n_resultbox
        if n_primary > 1:
            findings.append({"check": "emphasis-overuse", "page": None,
                             "detail": f"{n_primary} primary emphasis treatments "
                                       f"({title[:40] if title else '?'}) — "
                                       "keep one primary emphasis treatment"})
        has_columns = r"\begin{columns}" in frame_src
        has_split_minipages = len(re.findall(
            r"\\begin\s*\{minipage\}", frame_src)) >= 2
        has_visual_comparison = bool(re.search(
            r"\\(?:includegraphics|input)\b|\\begin\s*\{(?:tabular|tikzpicture|axis|pgfpicture)\}",
            frame_src))
        if (has_columns or has_split_minipages) and not has_visual_comparison:
            findings.append({"check": "prose-columns", "page": None,
                             "detail": "text-only split layout in "
                                       f"{title[:40] if title else '?'} — "
                                       "use one reading order unless the comparison "
                                       "is genuinely irreducible"})

        arrow_items = re.findall(
            r"\\item\s*\[\s*(?:\$?\s*\\(?:Rightarrow|rightarrow|Longrightarrow)\b|[⇒→])[^]]*\]",
            frame_src)
        if arrow_items:
            findings.append({"check": "arrow-bullet", "page": None,
                             "detail": f"right-arrow list marker in "
                                       f"{title[:40] if title else '?'} — use a normal "
                                       "bullet or a plain-language run-in label"})

        opening_label = bool(
            re.search(r"\beconomic\s+question\b", title, re.I)
            or re.search(
                r"\\(?:RunIn|textbf)\s*\{\s*(?:the\s+)?economic\s+question\b",
                frame_src,
                re.I,
            )
        )
        if opening_label:
            findings.append({"check": "question-label", "page": None,
                             "detail": f"'economic question' used as a label in "
                                       f"{title[:40] if title else '?'} — call the "
                                       "opening object 'Key question'"})

        if title_plain == "key question":
            subtitle = command_argument(frame_src, "framesubtitle")
            if subtitle and "?" in subtitle:
                findings.append({"check": "question-subtitle", "page": None,
                                 "detail": "a concise question is hidden in the "
                                           "subtitle of 'Key question' — make the "
                                           "question the frame title when it fits"})

        if title_plain == "roadmap" and re.search(
                r"\\textbf\s*\{|\\bfseries\b", frame_src):
            findings.append({"check": "roadmap-emphasis", "page": None,
                             "detail": "Roadmap uses boldface — keep orientation "
                                       "labels regular weight; use muted color only "
                                       "to mark inactive modules when needed"})

        static_match = re.search(
            r"\\includegraphics\b|\\begin\s*\{(?:tabular|tabularx|longtable|axis|tikzpicture)\}",
            frame_src)
        reading_match = re.search(
            r"\\Takeaway(?:WithNav)?(?:\s*\[[^\]]+\])?\s*\{", frame_src)
        semantic_build = bool(re.search(
            r"\\(?:only|uncover|visible|onslide)\s*<|\\begin\s*\{overlayarea\}",
            frame_src))
        if static_match and not semantic_build \
                and (not reading_match or reading_match.start() < static_match.start()):
            findings.append({"check": "exhibit-reading", "page": None,
                             "detail": f"static exhibit in "
                                       f"{title[:40] if title else '?'} needs a bottom "
                                       "interpretation or economic-significance line "
                                       "after the exhibit"})

        if title_plain == "conclusion" and re.search(
                r"\\(?:PlaceNav|hyperlink|beamergotobutton|beamerbutton|BackButton)\b",
                frame_src):
            findings.append({"check": "conclusion-link", "page": None,
                             "detail": "Conclusion contains Beamer navigation — "
                                       "end on the takeaway, not a link hub"})
        if title_plain == "conclusion":
            n_items = len(re.findall(
                r"\\item(?![A-Za-z@])(?:\s*<[^>]*>)?(?:\s*\[[^]]*\])?",
                frame_src))
            if n_items > 3:
                findings.append({"check": "conclusion-density", "page": None,
                                 "detail": f"Conclusion has {n_items} bullet items; "
                                           "keep the answer, one support, and the "
                                           "implication; recall a boundary only in "
                                           "the rare case that omitting it would "
                                           "materially misstate the result"})

    targets = set(re.findall(r"\\hypertarget(?:<[^>]+>)?\s*\{([^{}]+)\}", src))
    targets.update(re.findall(r"\\label\{([^{}]+)\}", src))
    targets.update(value.strip() for value in re.findall(
        r"\\begin\{frame\}(?:<[^>]+>)?\[[^]]*label\s*=\s*([^,\]]+)", src))
    links = set(re.findall(r"\\hyperlink(?:<[^>]+>)?\s*\{([^{}]+)\}", src))
    links.update(re.findall(r"\\BackButton\{([^{}]+)\}", src))
    for target in sorted(links - targets):
        findings.append({"check": "dead-link", "page": None,
                         "detail": f"navigation target {target!r} is not defined"})
    return findings


def score_findings(findings: list[dict]) -> int:
    """Return the ordinary whole-deck score for a collection of findings."""
    score = 100
    for finding in findings:
        score -= DEDUCT.get(finding["check"], 2)
    return max(0, score)


def finding_signature(finding: dict) -> str:
    """Build a page-stable identity for one objective blocker.

    A page number is presentation order, not defect identity, so it is never
    part of the signature. Geometry measurements are similarly volatile after
    a nearby edit. Context that identifies the affected object is retained:
    the overflowing text, footer label, navigation target, or frame title.
    Matching is performed as a multiset, so a second identical defect is new.
    """
    check = str(finding.get("check", "")).strip()
    detail = re.sub(r"\s+", " ", str(finding.get("detail", ""))).strip()

    if check == "edge-overflow":
        # ``text reaches x=... of ...: 'semantic text'``
        context = detail.split(":", 1)[1] if ":" in detail else detail
    elif check == "nav-footer-overlap":
        # Retain the footer object, not the overlap dimensions.
        match = re.search(r"footer text (.+?) by [\d.]+x[\d.]+pt$", detail)
        context = match.group(1) if match else detail
    elif check == "overfull":
        # TeX does not reliably expose box contents in the log. Preserve box
        # orientation and use occurrence counts to detect additional warnings.
        match = re.search(r"\\([hv])box\b", detail)
        context = f"\\{match.group(1)}box" if match else "box"
    elif check == "dead-link":
        match = re.search(r"navigation target (.+?) is not defined$", detail)
        context = match.group(1) if match else detail
    elif check in {"arrow-bullet", "question-label"}:
        # The text before the explanatory dash contains the local frame title.
        context = detail.split(" — ", 1)[0]
    elif check == "conclusion-link":
        context = "conclusion navigation"
    elif check == "compile-error":
        # Keep the error message; the source line moves with nearby edits.
        context = re.sub(r" \(source line \d+\)", "", detail.split(" — ", 1)[0])
    elif check == "undefined-ref":
        # Key the log findings by kind and key; PDF markers by marker text.
        context = re.sub(r" \(log, TeX page \d+\)", "", detail.split(" — ", 1)[0])
        context = re.sub(r" x\d+ in the PDF text$", "", context)
    else:
        context = detail

    # Fallback normalization for future blockers: ignore explicit geometry
    # measurements without erasing meaningful numbers in titles or labels.
    context = re.sub(r"\b[\d.]+(?:pt|%)\b", "<measure>", context)
    context = re.sub(r"\s+", " ", context).strip().casefold()
    return f"{check}|{context}"


def classify_blocker_regressions(
        findings: list[dict], baseline_findings: list[dict],
) -> tuple[list[dict], list[dict], list[dict]]:
    """Split current blockers into inherited/new and baseline blockers resolved.

    Matching uses queues keyed by semantic signature. This preserves
    multiplicity: if the baseline has one occurrence and the edited deck has
    two, exactly one is inherited and one is new. A non-waivable blocker
    (``NON_WAIVABLE_BLOCKERS``) is always returned with the failing ``new``
    list, flagged ``"non_waivable": True`` and ``"in_baseline"`` when the
    baseline already had it, so an inherited ``[?]`` still fails the edit.
    """
    baseline_pool: dict[str, deque[dict]] = defaultdict(deque)
    for finding in baseline_findings:
        if finding.get("check") in HARD_BLOCKERS:
            signature = finding_signature(finding)
            baseline_pool[signature].append(
                {**finding, "signature": signature}
            )

    inherited: list[dict] = []
    new: list[dict] = []
    for finding in findings:
        if finding.get("check") not in HARD_BLOCKERS:
            continue
        signature = finding_signature(finding)
        classified = {**finding, "signature": signature}
        matched = bool(baseline_pool[signature])
        if matched:
            baseline_pool[signature].popleft()
        if finding.get("check") in NON_WAIVABLE_BLOCKERS:
            new.append({**classified, "non_waivable": True,
                        "in_baseline": matched})
        elif matched:
            inherited.append(classified)
        else:
            new.append(classified)

    resolved = [finding for queue in baseline_pool.values() for finding in queue]
    return inherited, new, resolved


def load_baseline(path: Path) -> dict:
    """Load and validate prior ``check_deck.py --json`` output."""
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read baseline JSON {path}: {exc}") from exc
    if not isinstance(result, dict) or not isinstance(result.get("findings"), list):
        raise ValueError(
            f"baseline JSON {path} is not check_deck.py output: "
            "expected an object with a findings list"
        )
    for index, finding in enumerate(result["findings"], start=1):
        if not isinstance(finding, dict) or not isinstance(finding.get("check"), str):
            raise ValueError(
                f"baseline JSON {path} has an invalid finding at position {index}"
            )
    return result


def input_problem(path: Path) -> str | None:
    """Say why an input file cannot be read, or return None."""
    if not path.exists():
        return "does not exist"
    if not path.is_file():
        return "is not a regular file"
    if not os.access(path, os.R_OK):
        return "is not readable"
    return None


def verdict_for(score: int, blockers: list[str], complete: bool = True) -> str:
    """Apply the normal ship/fix thresholds to a score and blocker set.

    A run without --tex or --log never ships: it is "incomplete" unless it
    already found something to fix.
    """
    verdict = ("must fix" if blockers else
               "ship" if score >= 90 else
               "fix recommended" if score >= 80 else "must fix")
    return "incomplete" if verdict == "ship" and not complete else verdict


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--tex", type=Path, default=None)
    ap.add_argument("--log", type=Path, default=None)
    ap.add_argument("--render-dir", type=Path, default=None,
                    help="write page-NN.png at 200 DPI for the visual pass")
    ap.add_argument(
        "--baseline-json", type=Path, default=None,
        help=("prior check_deck.py --json output for a scoped existing-deck "
              "regression check; inherited objective blockers remain visible "
              "but only new blockers fail"),
    )
    ap.add_argument(
        "--allow-literal-marker", action="append", default=[], metavar="MARKER",
        help=("a ??, (?), [?] or [?, ?] that the deck shows as literal text; "
              "repeatable. Same as a source comment "
              "'%% econ-slides: allow-literal-marker MARKER'. Waived only "
              "when --log reports no undefined citation or reference"))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    for label, path in (("TeX source", args.tex), ("log", args.log),
                        ("baseline JSON", args.baseline_json)):
        problem = input_problem(path) if path is not None else None
        if problem:
            print(f"error: supplied {label} {path} {problem}", file=sys.stderr)
            return EXIT_CANNOT_RUN
    baseline_result = None
    if args.baseline_json is not None:
        try:
            baseline_result = load_baseline(args.baseline_json)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    if not args.pdf.exists():
        print(f"error: {args.pdf} not found — compile the deck first",
              file=sys.stderr)
        return 2
    if input_problem(args.pdf):
        print(f"error: {args.pdf} {input_problem(args.pdf)}", file=sys.stderr)
        return 2
    try:
        doc = fitz.open(args.pdf)
    except Exception as exc:
        print(f"error: cannot open {args.pdf}: {exc}", file=sys.stderr)
        return 2
    if doc.needs_pass:
        print(f"error: {args.pdf} is password-protected", file=sys.stderr)
        return 2
    if doc.page_count == 0:
        print(f"error: {args.pdf} has no pages", file=sys.stderr)
        return 2
    log_text, notes = None, []
    if args.log:
        try:
            log_text, notes = read_log(args.log, args.pdf, doc.page_count)
        except (ValueError, OSError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return EXIT_CANNOT_RUN
    try:
        declared = list(args.allow_literal_marker)
        if args.tex:
            declared += [m.group(1) for m in ALLOW_MARKER_RE.finditer(
                tex_tree(args.tex, strip_comments=False))]
        allowed_markers = parse_allowed_markers(declared)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_CANNOT_RUN
    findings: list[dict] = []
    keys = [footer_key(doc.load_page(p)) for p in range(doc.page_count)]
    titles = [frame_title_key(doc.load_page(p)) for p in range(doc.page_count)]
    for pno in range(doc.page_count):
        same_overlay = (pno < doc.page_count - 1 and keys[pno]
                        and keys[pno] == keys[pno + 1]
                        and has_frame_counter(keys[pno])
                        and titles[pno]
                        and titles[pno] == titles[pno + 1])
        final = not same_overlay
        findings += check_page(doc.load_page(pno), pno + 1, final=final)
        if final:
            findings += check_nav_overlap(doc.load_page(pno), pno + 1)
            findings += check_unresolved_markers(doc.load_page(pno), pno + 1,
                                                 allowed_markers)
    if log_text is not None:
        findings += check_log(log_text)
    # A declared literal marker is waived only when the log shows that no
    # citation or reference is actually undefined.
    log_clean = args.log is not None and not any(
        f["check"] == "undefined-ref" and f["page"] is None for f in findings)
    waived_markers = [f for f in findings if f.get("allowed_literal")] \
        if log_clean else []
    if waived_markers:
        findings = [f for f in findings if not f.get("allowed_literal")]
    elif args.log is not None:
        for f in findings:
            if f.get("allowed_literal"):
                f["detail"] = f["detail"].split(";", 1)[0] + (
                    "; it still blocks because the log reports an undefined "
                    "citation or reference")
    if args.tex:
        findings += check_tex(args.tex)

    if args.render_dir:
        try:
            args.render_dir.mkdir(parents=True, exist_ok=True)
            for stale in args.render_dir.glob("page-*.png"):
                stale.unlink()
            mat = fitz.Matrix(200 / 72, 200 / 72)
            for pno in range(doc.page_count):
                out = args.render_dir / f"page-{pno + 1:02d}.png"
                doc.load_page(pno).get_pixmap(matrix=mat).save(out)
        except (OSError, RuntimeError) as exc:
            print(f"error: cannot write renders to {args.render_dir}: {exc}",
                  file=sys.stderr)
            return EXIT_CANNOT_RUN

    skipped_checks = ([] if args.tex else list(TEX_ONLY_CHECKS)) \
        + ([] if args.log else list(LOG_ONLY_CHECKS))
    complete = not skipped_checks
    score = score_findings(findings)
    all_blockers = sorted({f["check"] for f in findings
                           if f["check"] in HARD_BLOCKERS})
    inherited_blockers = None
    new_blockers = None
    resolved_blockers = None
    regression_score = None
    if baseline_result is not None:
        inherited_blockers, new_blockers, resolved_blockers = (
            classify_blocker_regressions(findings, baseline_result["findings"])
        )
        # Keep the ordinary whole-deck score visible, but judge the scoped edit
        # after removing only matched inherited objective blockers. Review
        # prompts remain in the regression score and in the visual workflow.
        regression_findings = [
            finding for finding in findings
            if finding.get("check") not in HARD_BLOCKERS
        ] + new_blockers
        regression_score = score_findings(regression_findings)
        blockers = sorted({f["check"] for f in new_blockers})
        verdict = verdict_for(regression_score, blockers, complete)
    else:
        blockers = all_blockers
        verdict = verdict_for(score, blockers, complete)

    baseline_meta = None
    if baseline_result is not None:
        baseline_meta = {
            "path": str(args.baseline_json),
            "pages": baseline_result.get("pages"),
            "objective_blocker_occurrences": sum(
                finding.get("check") in HARD_BLOCKERS
                for finding in baseline_result["findings"]
            ),
        }
    result = {"schema_version": 2,
              "pages": doc.page_count, "score": score,
              "regression_score": regression_score,
              "verdict": verdict,
              "complete": complete,
              "skipped_checks": skipped_checks,
              "blockers": blockers,
              "all_blockers": all_blockers,
              "baseline": baseline_meta,
              "inherited_blockers": inherited_blockers,
              "new_blockers": new_blockers,
              "resolved_blockers": resolved_blockers,
              "undefined_refs": sum(f["check"] == "undefined-ref"
                                    for f in findings),
              "allowed_literal_markers": [
                  {"page": f["page"], "detail": f["detail"]}
                  for f in waived_markers],
              "findings": findings,
              "notes": notes,
              "rendered": str(args.render_dir) if args.render_dir else None}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        score_label = f"score {score}"
        if regression_score is not None:
            score_label += f", regression score {regression_score}"
        print(f"{args.pdf.name}: {doc.page_count} pages, "
              f"{score_label} — {verdict}")
        if skipped_checks:
            missing = " and ".join(flag for flag, given in
                                   (("--tex", args.tex), ("--log", args.log))
                                   if not given)
            print(f"  partial check: pass {missing} to run "
                  f"{', '.join(skipped_checks)}; a partial run never ships")
        if baseline_result is not None:
            print("  baseline comparison: "
                  f"{len(inherited_blockers)} inherited, "
                  f"{len(new_blockers)} new, "
                  f"{len(resolved_blockers)} resolved objective blockers")
        for f in findings:
            loc = f"p{f['page']}" if f["page"] else "log/tex"
            print(f"  [{f['check']}] {loc}: {f['detail']}")
        for f in waived_markers:
            print(f"  note p{f['page']}: literal marker waived — the deck "
                  "declares it and the log has no undefined key")
        for note in notes:
            print(f"  note: {note}")
        if not findings:
            print("  no findings from static checks")
        print("  reminder: static checks cannot see box-interior overflow or a"
              " \\toprule merged into a title bar — always view the renders.")
    return EXIT_SHIP if verdict == "ship" else EXIT_NOT_READY


def safe_output() -> None:
    """Never crash on a console code page that lacks a character (Windows).

    Python before 3.15 writes redirected output in the ANSI code page there;
    a bullet or CJK slide text would otherwise raise UnicodeEncodeError.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError):
            pass


def run() -> int:
    """Run main(), keeping a crash (exit 3) apart from a failing deck (exit 1)."""
    safe_output()
    try:
        return main()
    except Exception as exc:  # noqa: BLE001  (report, never pass as a verdict)
        import traceback
        traceback.print_exc()
        print(f"error: check_deck.py crashed ({type(exc).__name__}: {exc}). "
              "No verdict was produced; exit 3 means the checker failed, not "
              "the deck.", file=sys.stderr)
        return EXIT_CRASH


if __name__ == "__main__":
    sys.exit(run())
