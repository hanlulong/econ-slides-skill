# econ-slides themes

Every theme implements the same semantic interface, so a finished deck
switches looks by swapping one line:

```latex
\usepackage{econ-slides-house}   % → econ-slides-clean, econ-slides-boxed
```

## Choosing a theme

| Theme | Look | Reach for it when |
|---|---|---|
| `econ-slides-house` *(default)* | No chrome, centered titles, Palatino math, Okabe–Ito accents | Research talks: seminars, conferences, job talks |
| `econ-slides-clean` | Near-monochrome, left titles over a thin rule, one blue accent | You want zero visual signature — referee workshops, teaching |
| `econ-slides-boxed` | Navy title bar, circle bullets, structured blocks | Discussant decks, policy and central-bank audiences |

All themes assume:

```latex
\documentclass[11pt, aspectratio=169]{beamer}
```

## The semantic interface

Decks are written against these names, never against raw colors or theme
internals — that is what makes themes swappable.

| Element | Meaning |
|---|---|
| `cAccentA` … `cAccentD` | Concept colors (Okabe–Ito). Assign one color per recurring concept and keep it for the whole talk — in text, equations, and figures. |
| `cHighlight` | The punchline spotlight color |
| `cGood` / `cBad` | Semantic aliases (teal / vermillion) |
| `\KeyIdea{...}` | Bold + spotlight color for the one key phrase on a slide |
| `\Takeaway{...}` | Centered one-line takeaway under an exhibit |
| `\graycite{...}` | Gray inline citations: `\graycite{(Autor '13; Hjort--Poulsen '19)}` |
| `\RunIn{Label:}` | Bold run-in label for structured summaries (discussant decks) |
| `\Et` | `\mathbb{E}_t` |
| `\PlaceNav{...}` | Pin a button bottom-right without reflowing the body |
| `\BackButton{label}` | Appendix return button paired with `\hypertarget{label}{}` |
| `\begin{ResultBox}[title]` | Framed, tinted box for the headline result |
| `\AppendixStart` | Appendix divider frame; footer switches to `A1, A2, …` and the main total freezes |

## Bring your own template

To use an institutional theme, keep the deck's content untouched and write a
thin adapter package that (1) loads your institution's style, then (2) defines
the interface above on top of it. Copy any bundled `.sty` and replace the
"Theme" block; the "Semantic interface" block is the contract to preserve.

## Verification

`tests/interface-test.tex` exercises every interface element and must compile
warning-free under all bundled themes (see `tests/`).
