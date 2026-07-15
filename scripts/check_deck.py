#!/usr/bin/env python3
"""Audit a compiled Beamer deck against the econ-slides layout rules.

Usage:
    python3 scripts/check_deck.py build/talk.pdf [--tex talk.tex] [--log build/talk.log]
                                                 [--render-dir pages] [--json]

Checks (geometry measured from the PDF itself, not guessed from source):
  edge-overflow   any text placed outside the safe page margins
  wrapped-title   a frame title that runs to a second line
  wrapped-bullet  a bullet whose text wraps to further lines
  density         more than MAX_BULLETS top-level bullets on one slide
  overfull        Overfull \\hbox/\\vbox warnings parsed from the .log
  pause-chain     3+ \\pause in one frame (overlay used as decoration)

Score starts at 100 and deducts per finding. Gates: >=90 ship,
80-89 fix recommended, <80 must fix. --render-dir writes one PNG per page
at 200 DPI for the visual pass (box-interior overflow and title-bar/toprule
merges are invisible to every static check — always eyeball the renders).

Requires PyMuPDF: pip install pymupdf
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    print("error: PyMuPDF missing — pip install pymupdf", file=sys.stderr)
    sys.exit(1)

# NOTE: en/em dashes are deliberately NOT markers — they appear as empty
# table cells ("---") and would false-positive the bullet checks.
BULLET_GLYPHS = "•▪■◦‣⋆★✓✔"
ARROW_GLYPHS = "⇒→↳"
EDGE_MARGIN_PT = 6        # text closer than this to the paper edge = overflow
TITLE_ZONE = 0.18         # top fraction of the page that can hold the title
MAX_BULLETS = 5           # house norm is 1-4 top-level bullets
MAX_TEXT_LINES = 15       # more = a wall of text

DEDUCT = {"edge-overflow": 15, "wrapped-title": 10, "wrapped-bullet": 4,
          "density": 3, "overfull": 5, "pause-chain": 2}


MATH_FONT_RE = re.compile(r"CMMI|CMSY|CMEX|MSBM|MSAM|Math|rsfs", re.I)
ENUM_MARKER_RE = re.compile(r"^\d{1,2}\.$")


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


def check_page(page: fitz.Page, pno: int, footer_zone: float = 0.93) -> list[dict]:
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

    # --- wrapped title: >1 line in title-size font inside the title zone ---
    # \large bold at an 11pt base renders ~12pt; body text ~10.9pt
    title_lines = [l for l in body if l["bbox"].y0 < H * TITLE_ZONE
                   and l["size"] >= 11.5 and not is_marker_line(l)]
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
    top_level = [l for l in marker_lines if l["bbox"].x0 < W * 0.12]
    if len(top_level) > MAX_BULLETS:
        findings.append({"check": "density", "page": pno,
                         "detail": f"{len(top_level)} top-level bullets (max {MAX_BULLETS})"})

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
                         "detail": f"{len(body)} text lines (max {MAX_TEXT_LINES})"})
    return findings


def check_log(log_path: Path) -> list[dict]:
    findings = []
    text = log_path.read_text(errors="replace")
    for m in re.finditer(r"^Overfull \\([hv])box \(([\d.]+)pt too \w+\)", text, re.M):
        if float(m.group(2)) > 2.0:
            findings.append({"check": "overfull", "page": None,
                             "detail": f"\\{m.group(1)}box {m.group(2)}pt too wide/tall"})
    return findings


def check_tex(tex_path: Path) -> list[dict]:
    findings = []
    src = tex_path.read_text(errors="replace")
    for fm in re.finditer(r"\\begin\{frame\}(.*?)\\end\{frame\}", src, re.S):
        n_pause = fm.group(1).count(r"\pause")
        if n_pause >= 3:
            title = re.search(r"\{([^}]*)\}", fm.group(1))
            findings.append({"check": "pause-chain", "page": None,
                             "detail": f"{n_pause} \\pause in one frame "
                                       f"({title.group(1)[:40] if title else '?'}) — "
                                       "overlay as decoration; build reasoning instead"})
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--tex", type=Path, default=None)
    ap.add_argument("--log", type=Path, default=None)
    ap.add_argument("--render-dir", type=Path, default=None,
                    help="write page-NN.png at 200 DPI for the visual pass")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    doc = fitz.open(args.pdf)
    findings: list[dict] = []
    for pno in range(doc.page_count):
        findings += check_page(doc.load_page(pno), pno + 1)
    if args.log and args.log.exists():
        findings += check_log(args.log)
    if args.tex and args.tex.exists():
        findings += check_tex(args.tex)

    if args.render_dir:
        args.render_dir.mkdir(parents=True, exist_ok=True)
        mat = fitz.Matrix(200 / 72, 200 / 72)
        for pno in range(doc.page_count):
            out = args.render_dir / f"page-{pno + 1:02d}.png"
            doc.load_page(pno).get_pixmap(matrix=mat).save(out)

    score = 100
    for f in findings:
        score -= DEDUCT.get(f["check"], 2)
    score = max(0, score)
    verdict = ("ship" if score >= 90 else
               "fix recommended" if score >= 80 else "must fix")

    result = {"pages": doc.page_count, "score": score, "verdict": verdict,
              "findings": findings,
              "rendered": str(args.render_dir) if args.render_dir else None}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{args.pdf.name}: {doc.page_count} pages, score {score} — {verdict}")
        for f in findings:
            loc = f"p{f['page']}" if f["page"] else "log/tex"
            print(f"  [{f['check']}] {loc}: {f['detail']}")
        if not findings:
            print("  no findings from static checks")
        print("  reminder: static checks cannot see box-interior overflow or a"
              " \\toprule merged into a title bar — always view the renders.")
    return 0 if score >= 80 else 1


if __name__ == "__main__":
    sys.exit(main())
