# Exhibit surgery: tables, figures, and numbers

The most economics-specific work this skill does. A paper exhibit is built
for a referee with unlimited time; a slide exhibit is built for a listener
with eight seconds. Never paste one as the other.

## Number provenance (governs everything below)

- Every number shown comes from the user's materials, tagged at draft time:
  `0.034 (0.008)  % Table 2, col (3), p.24`.
- Never re-round beyond dropping digits (0.0342 → 0.034 is fine; 0.034 →
  "about 0.05" is fabrication). Never average, rescale, or convert units
  without showing the conversion on the slide or in the note.
- Derived magnitudes ("one SD ⇒ 0.7%") show their arithmetic in the slide
  note or takeaway, with inputs traceable to the paper.
- Missing number → `\TODO{<what is needed>}` in red, surfaced to the user.
  A `\TODO` in a delivered deck must be called out in the summary.

## Regression table → slide table

Procedure, in order:

1. **Choose the story.** One estimate is the point; 1–3 comparison columns
   defend it. Everything else goes to a full appendix table.
2. **Keep rows**: the coefficient(s) of interest with SEs. **Collapse
   rows**: controls, fixed effects, and diagnostics become `Controls — No /
   Yes / Yes` indicator lines. **Drop rows**: constants, nuisance
   covariates nobody will ask about.
3. **Column headers say what changes**: `(1) OLS`, `(2) +Controls`,
   `(3) +Region trends` — the identification story reads left to right.
4. **Highlight the load-bearing column** in `cAccentA` (header, estimate,
   SE), not bold-everything.
5. **Embed the interpretation**: a colored full-width `\multicolumn` row
   inside the table stating what the pattern means ("stable across (2)–(3)
   ⇒ selection on observables is not driving it"). The table states its own
   conclusion.
6. **Translate the magnitude** under the table via `\Takeaway{}`: convert
   the coefficient with a paper-relevant change (one SD, interquartile
   range, the policy's actual dose) — "significant" is not a magnitude.
7. Typeset: `booktabs` (never vertical rules), right-aligned numbers,
   2–3 significant digits, `threeparttable` with the clustering and stars
   convention in `tablenotes`, wrapped in
   `\resizebox{0.7–0.8\textwidth}{!}{...}`. Font floor: if the resize drops
   below `\scriptsize` legibility, the table is too wide — cut columns.

Pattern — **every value below is illustrative fiction. Copying any number
from this snippet into a real deck is fabrication**; replace all of them
from the user's paper and keep the provenance comments:

```latex
\resizebox{0.72\textwidth}{!}{%
\begin{threeparttable}
  \begin{tabular}{lccc}
    \toprule
    & (1) OLS & (2) +Controls & \textcolor{cAccentA}{(3) +Trends} \\ \midrule
    Broadband $\times$ Post & 0.041*** & 0.036*** & \textcolor{cAccentA}{\textbf{0.034***}} \\
     & (0.009) & (0.008) & \textcolor{cAccentA}{(0.008)} \\ \midrule
    Controls & No & Yes & Yes \\
    Observations & 148,220 & 148,220 & 148,220 \\
    \multicolumn{4}{l}{\textcolor{cAccentA}{\footnotesize Stable once trends enter ⇒ …}} \\
    \bottomrule
  \end{tabular}
  \begin{tablenotes}\footnotesize
    \item SEs clustered by municipality. *** $p<0.01$.
  \end{tablenotes}
\end{threeparttable}}
\Takeaway{One SD of exposure moves productivity by 0.7 percent.}
```

- **"Data | Model" tables** (structural/theory-empirics): two value columns
  compared moment by moment; reveal the model column on a second overlay
  step after the data column is absorbed.
- Never place `\toprule` directly under a colored frame title bar (boxed
  theme) — insert `\vspace{4pt}` first; the compiler will not warn you.

## Figures

- **Rebuild figures for the slide** whenever sources are available: figure
  fonts at slide scale (legible from the back row), legends inside the plot
  area or dropped in favor of direct line labels, and **line colors =
  slide concept colors** (same Okabe–Ito hex values — this is the single
  strongest professional signal the skill produces). Keep a
  `figures-slides/` directory separate from the paper's figures.
- No source to rebuild from → crop tightly with
  `scripts/crop_figure.py` (`--list` finds candidate regions, `--bbox`
  crops at 300 DPI) and include at `width=0.9\textwidth, keepaspectratio`;
  if its internal text is illegible at that size, it does not go on the
  slide.
- An included paper figure keeps its own colors, so the slide↔figure color
  contract cannot hold for it. Do not fight it: if the figure's palette is
  close to a theme accent, adopt that accent for the concept in the text;
  otherwise drop concept-coloring for that concept rather than color the
  word one hue and the line another.
- One figure per frame, centered; panels labeled `A.`/`B.` only if both
  panels are discussed. Wide figures: `\makebox[\textwidth][c]{...}`.
- Every figure slide: assertion title, `\framesubtitle` with the precise
  reading (sample, units, CI level), `\Takeaway` beneath.
- Prefer figures to tables for the main result (event-study plot,
  coefficient plot, binscatter); the regression table then defends the
  figure from the appendix.

## Event-study / coefficient plots (the workhorse)

- Reference line at zero, treatment date marked, CIs shaded or as bars,
  pre-period visually distinguishable. Normalized coefficient (t = −1)
  shown, not silently dropped.
- Axis label carries the unit ("log points × 100" ≠ "percent" — say which).
  Caption/axis unit mismatches are a classic referee catch; check both
  against the paper's numbers.
- Overlay build (optional, if it aids reasoning): pre-period first, then
  post — the audience judges parallel trends before seeing the effect.

## TikZ and diagrams

- Design diagrams (timelines, DAGs, model schematics) beat prose. Rules:
  - Any point that must sit on a plotted curve is **computed**
    (`\pgfmathsetmacro` from the same function), never eyeballed — an
    eyeballed point drifts on every edit and renders without warning.
  - Explicit `minimum width/height` or `text width` on boxed nodes; bare
    `scale=` is banned (it scales coordinates but not labels) — use
    `transform shape` or scale node styles too.
  - Labels keep ≥ 0.3–0.4 cm clearance from curves, shapes, and each
    other; when a curved arrow and a label compete, compute the arc's
    depth before placing (adapted from Scott Cunningham's MixtapeTools
    measurement rules, with thanks).
- After any TikZ edit, re-render and *look*: label collisions produce zero
  compiler warnings.

## The visual pass (why the renders exist)

`check_deck.py --render-dir` writes every page as PNG. Inspect each for the
failures no static check sees: content overflowing a `ResultBox` or block
(Beamer suppresses those warnings), `\toprule`-under-title-bar merges, TikZ
label overlap, figure text too small, a slide that is simply ugly. One
sweep, page by page, before delivery — non-negotiable.
