#!/usr/bin/env python3
"""Crop a figure out of a paper PDF for slide use (when it can't be rebuilt).

Usage:
    # 1. Find candidate figure regions on a page:
    python3 scripts/crop_figure.py paper.pdf --page 6 --list

    # 2. Crop one (coordinates in PDF points, from --list or a PDF viewer):
    python3 scripts/crop_figure.py paper.pdf --page 6 \
        --bbox 72,150,540,420 --out figures-slides/fig2_eventstudy.png

Renders at 300 DPI so the crop stays legible when scaled to slide width.
Requires PyMuPDF: pip install pymupdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    print("error: PyMuPDF missing — pip install pymupdf", file=sys.stderr)
    sys.exit(1)


def candidate_regions(page: fitz.Page) -> list[fitz.Rect]:
    """Merge image blocks and vector-drawing clusters into figure candidates."""
    rects: list[fitz.Rect] = []
    for info in page.get_image_info():
        rects.append(fitz.Rect(info["bbox"]))
    # vector figures (pgfplots/tikz): cluster drawings that overlap or abut
    drawings = [fitz.Rect(d["rect"]) for d in page.get_drawings()
                if d["rect"].width > 5 and d["rect"].height > 5]
    for r in drawings:
        for existing in rects:
            grown = fitz.Rect(existing) + (-10, -10, 10, 10)
            if grown.intersects(r):
                existing.include_rect(r)
                break
        else:
            rects.append(fitz.Rect(r))
    # keep plausibly figure-sized regions
    W, H = page.rect.width, page.rect.height
    return [r for r in rects if r.width > 0.25 * W and r.height > 0.08 * H]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--page", type=int, required=True, help="1-indexed page")
    ap.add_argument("--list", action="store_true",
                    help="print candidate figure bboxes and exit")
    ap.add_argument("--bbox", type=str, default=None,
                    help="x0,y0,x1,y1 in PDF points")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--pad", type=float, default=4.0,
                    help="padding in points around the bbox")
    args = ap.parse_args()

    if not args.pdf.exists():
        print(f"error: {args.pdf} not found", file=sys.stderr)
        return 2
    try:
        doc = fitz.open(args.pdf)
    except Exception as exc:
        print(f"error: cannot open {args.pdf}: {exc}", file=sys.stderr)
        return 2
    if doc.needs_pass:
        print(f"error: {args.pdf} is password-protected", file=sys.stderr)
        return 2
    if not 1 <= args.page <= doc.page_count:
        print(f"error: page {args.page} out of range 1..{doc.page_count}",
              file=sys.stderr)
        return 1
    page = doc.load_page(args.page - 1)

    if args.list:
        regions = candidate_regions(page)
        if not regions:
            print("no figure-sized regions detected; use a PDF viewer to "
                  "read coordinates and pass --bbox")
        for i, r in enumerate(regions, 1):
            print(f"  candidate {i}: --bbox "
                  f"{r.x0:.0f},{r.y0:.0f},{r.x1:.0f},{r.y1:.0f}"
                  f"   ({r.width:.0f}x{r.height:.0f} pt)")
        return 0

    if not args.bbox or not args.out:
        print("error: --bbox and --out required (or use --list first)",
              file=sys.stderr)
        return 1
    x0, y0, x1, y1 = (float(v) for v in args.bbox.split(","))
    clip = fitz.Rect(x0 - args.pad, y0 - args.pad,
                     x1 + args.pad, y1 + args.pad) & page.rect
    args.out.parent.mkdir(parents=True, exist_ok=True)
    mat = fitz.Matrix(args.dpi / 72, args.dpi / 72)
    page.get_pixmap(matrix=mat, clip=clip).save(args.out)
    print(f"wrote {args.out} ({clip.width:.0f}x{clip.height:.0f} pt "
          f"@ {args.dpi} DPI)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
