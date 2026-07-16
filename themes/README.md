# econ-slides themes

Every theme implements the same semantic interface, so a finished deck
switches looks by swapping one line:

```latex
\usepackage{econ-slides-house}   % → econ-slides-clean, econ-slides-boxed
```

## Choosing a theme

| Theme | Look | Reach for it when |
|---|---|---|
| `econ-slides-house` *(default)* | No chrome, centered structure-blue titles, Palatino math, Okabe–Ito accents | Research talks: seminars, conferences, job talks |
| `econ-slides-clean` | Near-monochrome, left titles over a thin rule, one blue accent | You want zero visual signature — referee workshops, teaching |
| `econ-slides-boxed` | Navy title bar, circle bullets, structured blocks | Discussant decks, policy and central-bank audiences |
| `econ-slides-compat` | **Your choice of stock Beamer theme** | You prefer Madrid, metropolis, CambridgeUS, Boadilla, an institutional theme, … |

New decks using the bundled themes assume:

```latex
\documentclass[11pt, aspectratio=169]{beamer}
```

## Prefer a stock Beamer theme?

Load your theme first, then the adapter — it adds the semantic interface
without touching the theme's look (it only removes navigation symbols):

```latex
\documentclass[11pt, aspectratio=169]{beamer}
\usetheme{Madrid}                 % any stock or institutional theme
\usepackage{econ-slides-compat}
```

The `ResultBox` tints itself with the host theme's structure color, and
`\RunIn` uses it too, so the interface blends in. Verified in the test suite
with Madrid and CambridgeUS.

## The semantic interface

Decks are written against these names, never against raw colors or theme
internals — that is what makes themes swappable.

| Element | Meaning |
|---|---|
| `\AuthorAffil{Name}{Institution}` | Title-page author block with the institution directly beneath the author; arrange 1--3 in a row or four in a 2-by-2 grid |
| `cAccentA` … `cAccentD` | Concept colors (Okabe–Ito). Assign one color per recurring concept and keep it for the whole talk — in text, equations, and figures. |
| `cHighlight` | Transient spotlight for one term during a build; not a generic punchline color |
| `cGood` / `cBad` | Diagnostic aliases (teal / vermillion), mainly for discussions; avoid good/bad cards in author talks |
| `\KeyIdea{...}` | Bold structure-colored hierarchy for at most one key phrase on a slide |
| `\Takeaway[gap]{...}` | One normal-body-size bullet directly under a load-bearing exhibit: insight, intuition, economic scale, interpretation, or the decisive limit; omit the optional local gap on ordinary frames |
| `\TakeawayWithNav[gap]{...}` | The same full-width reading plus bounded clearance for a separate bottom-right navigation lane |
| `\ExhibitReadingGap` / `\ExhibitReadingGapRoomy` | Default and roomy bounded gaps before a takeaway. Keep technical notes tight to the exhibit; use the roomy gap locally only after the final render shows surplus space |
| `\graycite{...}` | Gray inline citations: `\graycite{(Autor '13; Hjort--Poulsen '19)}` |
| `\RunIn{Label:}` | Bold run-in label for structured summaries (discussant decks) |
| `\Et` | `\mathbb{E}_t` |
| `\PlaceNav{...}` | Pin a button bottom-right without reflowing the body |
| `\BackButton{label}` | Appendix return button paired with `\hypertarget{label}{}` |
| `\begin{ResultBox}[title]` | Rare framed treatment for one singular headline result or proposition; not for questions, caveats, or routine summaries |
| `\AppendixStart` | Appendix divider frame; footer switches to `A1, A2, …` and the main total freezes |

## Make a reusable adapter for a new template

When the user asks to make an institutional style reusable for future decks,
write a thin adapter package that (1) loads the institution's style, then (2)
defines the interface above on top of it. Copying a bundled `.sty` and replacing
its Theme block is one implementation route. This is not the workflow for
editing an existing deck: preserve that deck's current preamble and macros
unless the user explicitly requests a restyle or reusable adapter.

## Verification

`tests/interface-test.tex` exercises every interface element and must compile
without overfull boxes and pass the rendered checker under every bundled theme
(see `tests/`).
