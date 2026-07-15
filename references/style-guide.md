# Style guide: themes, files, and deck engineering

## Themes

Three bundled themes, one semantic interface — full reference in
`themes/README.md`:

- `econ-slides-house` (default): no chrome, centered titles, Palatino math,
  Okabe–Ito accents. Research talks.
- `econ-slides-clean`: near-monochrome, left titles, thin rule. Zero
  visual signature.
- `econ-slides-boxed`: navy title bar, structured blocks. Discussions and
  policy rooms.

Every deck begins:

```latex
\documentclass[11pt, aspectratio=169]{beamer}
\usepackage{econ-slides-house}   % the only line a theme swap changes
```

Write frames against the interface (`\KeyIdea`, `\Takeaway`, `\graycite`,
`\RunIn`, `\PlaceNav`, `\BackButton`, `ResultBox`, `\AppendixStart`,
`cAccentA…D`) — never against theme internals or raw colors. Test a theme
swap before delivery if the user is undecided: the deck must compile
cleanly under all three.

**User's own template**: copy the closest bundled `.sty`, replace its
"Theme" block with the institution's look, keep the "Semantic interface"
block intact. The deck never changes.

## File engineering

- **One clean file per venue.** Never maintain a master with 40% of its
  frames commented out — that graveyard pattern (common in real Overleaf
  projects) makes every venue cut a manual diff. Shared content that
  several venue decks reuse belongs in `frames/*.tex` modules pulled in
  with `\input`.
- Layout for a paper's talk directory:

  ```
  talk/
  ├── sed-2026.tex          % one file per venue
  ├── seminar-90min.tex
  ├── frames/               % shared frame modules (optional, when ≥2 venues)
  ├── figures-slides/       % slide-rebuilt figures, never the paper's
  └── build/                % compile output (never committed)
  ```

- Title slide pattern: `[plain]` frame + `\addtocounter{framenumber}{-1}`
  so numbering starts at the first content slide. Disclaimer footnote on
  the title frame when the employer requires one.
- Appendix: `\AppendixStart` (divider, numbering switches to A1, A2, …,
  main total freezes). Navigation is a **pair of targets** — the Back
  button must point at the *main* slide, not at the appendix frame it sits
  on (a `\BackButton{app:X}` next to `\hypertarget{app:X}` is a dead
  self-link):

  ```latex
  % main slide
  \hypertarget{main:robust}{}%
  \PlaceNav{\hyperlink{app:robust}{\beamergotobutton{Robustness}}}
  % appendix slide
  \hypertarget{app:robust}{}%
  ...
  \BackButton{main:robust}
  ```

  Two buttons on one frame share a single `\PlaceNav` node:
  `\PlaceNav{\hyperlink{app:a}{\beamergotobutton{Placebo}}\;\hyperlink{app:b}{\beamergotobutton{By cohort}}}`
  (stacked `\PlaceNav` calls overprint). Every button's target must exist —
  cutting frames orphans links; the compile log lists undefined references.

## Build and check

```bash
python3 scripts/compile_deck.py talk/sed-2026.tex
python3 scripts/check_deck.py talk/build/sed-2026.pdf \
    --tex talk/sed-2026.tex --log talk/build/sed-2026.log \
    --render-dir talk/build/pages
```

- `compile_deck.py`: XeLaTeX, two passes, themes dir on `TEXINPUTS`,
  triaged first error on failure.
- `check_deck.py`: geometry-measured layout audit + numeric score.
  Ship at ≥ 90 **and** a page-by-page visual pass of `build/pages/`.
- Engines: XeLaTeX default; pdfLaTeX and LuaLaTeX also work with the
  bundled themes (`--engine`).

## Delivery conventions

- Deliver `.tex` + compiled PDF + a three-line map: main deck contents,
  appendix contents, anything marked `\TODO`.
- State where each headline number came from (table/page), so the user can
  spot-check in one minute.
- Offer the standard follow-ups: theme swap, venue retarget, handout mode
  (`\documentclass[handout]` collapses overlays for sharing).
