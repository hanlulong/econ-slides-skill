# Changelog

All notable changes to econ-slides. Versions follow semantic versioning.
From 0.2.0, release tags use the OpenEcon.ai catalog form
`econ-slides--vX.Y.Z`; the earlier `v0.1.0` and `v0.1.1` tags stay as they are.

## 0.2.0 — 2026-11-06

The first release packaged as a plugin, and the first since v0.1.1. It also
collects the unreleased work on `main` since then, which changes several rules
that the v0.1.1 notes described.

### Migration: the skill moved to `skills/econ-slides/`

- `SKILL.md`, `references/`, `scripts/`, `templates/` and `themes/` now live in
  `skills/econ-slides/`. They moved together, so the scripts still find the
  bundled themes.
- New installs link `<clone>/skills/econ-slides`, or install the plugin (below).
- An existing link to the clone root keeps working after `git pull`. Claude
  Code now loads it as a plugin-style folder (`econ-slides@skills-dir`,
  invoked as `/econ-slides:econ-slides`). To keep the bare `/econ-slides`,
  re-link `~/.claude/skills/econ-slides` to `<clone>/skills/econ-slides`.
- Codex lists a manual link to the clone as `econ-slides:econ-slides`,
  whichever folder it points at, because the clone now carries plugin
  manifests.
- Remove any manual link before installing the plugin, so a client never loads
  two copies.
- Scripts are now called as `<skill-dir>/scripts/...`, where `<skill-dir>` is
  the folder that holds `SKILL.md`. Paths inside the skill are unchanged.

### Added

- Claude Code and Codex plugin manifests (`.claude-plugin/plugin.json`,
  `.codex-plugin/plugin.json`): name `econ-slides`, MIT, version 0.2.0. Install
  from the OpenEcon.ai marketplace with `/plugin install econ-slides@openeconai`
  (Claude Code) or `codex plugin add econ-slides@openeconai` (Codex) once the
  catalog lists it (resolves #1).
- `undefined-ref` hard blocker in `check_deck.py`. It reads LaTeX, natbib and
  biblatex warnings in the log, and the standard `[?]`, `(?)` and `??`
  placeholders in the PDF text. The PDF scan alone misses biblatex, which
  prints a missing key as the key itself, and natbib's `\citet`, which prints
  a bare `?`, so always pass `--log`. A `--baseline-json` comparison never
  waives it, so a deck that shows an unresolved key can no longer score
  "ship".
- Bibliography-aware compile. `compile_deck.py` runs BibTeX or Biber between
  passes when the source tree uses `\bibliography` or `\addbibresource`, and
  reports `undefined_refs` in its JSON and OK line. The tool runs from the
  source folder, so `\bibliography{../refs}` resolves as it does in an
  in-place build, and a prebuilt `.bbl` beside the source (an arXiv or
  Overleaf export) is kept when the database is missing.
- `compile_deck.py --timeout` (default 600 s). A timed-out run now returns the
  usual JSON with `ok: false` instead of a traceback.
- `requirements.txt` (PyMuPDF) and a `tlmgr install` line for BasicTeX, TinyTeX
  and other minimal TeX installs.
- A Contents list in each reference file over 100 lines.
- Trigger evals for `claude plugin eval` (`evals/`): three requests the skill
  should take and three it should leave alone.
- Unreleased work from `main` since v0.1.1:
  - speaker scripts (`check_script.py`, `references/speaker-script.md`, and
    the empirical and theory script templates);
  - the existing-deck workflow (`references/existing-deck-workflow.md`,
    `references/beamer-layout-mechanics.md`, and `check_deck.py
    --baseline-json` for scoped edits);
  - the claim–evidence ledger (`references/source-integrity.md`) and a
    pure-theory talk template;
  - a 30-minute sample talk with its rehearsal script, replacing the 15-minute
    sample;
  - a Chinese README, CONTRIBUTING, and a "Report a bad slide" issue template.

### Changed

- Rules that changed since the v0.1.1 notes:
  - Arrows are no longer bullet markers. v0.1.1 suggested "arrow intuition
    lines"; `\item[$\Rightarrow$]` and `\item[$\rightarrow$]` are now the
    `arrow-bullet` hard blocker. Use an ordinary nested bullet, a neutral run-in
    label, or a direct sentence.
  - The opening object is called "Key question", never "economic question"
    (`question-label` hard blocker).
  - The conclusion carries no navigation buttons or appendix links
    (`conclusion-link` hard blocker).
  - Clocks are total sessions unless stated as speaking time: plan 75–80% for
    prepared speech and reserve 20–25% for questions.
- The checker now separates hard blockers (edge overflow, serious overfull
  boxes, navigation collisions, dead links, undefined references, and the house
  rules above) from review prompts. Wrapped titles and bullets, density, sparse
  layout, prose columns, emphasis and exhibit readings no longer deduct points;
  in v0.1.1, wrapped titles cost 10 points, wrapped bullets 4 and density 3.
- Install guidance:
  - the manual Claude Code install creates `~/.claude/skills` first
    (`New-Item -Force` on Windows);
  - PyMuPDF goes into a dedicated venv or `uv run --with pymupdf`, because
    PEP 668 also blocks `pip install --user`;
  - the scripts import PyMuPDF as `pymupdf`, since the `fitz` name is
    deprecated in PyMuPDF 2.x;
  - a missing PyMuPDF now gets a message that names the interpreter and the
    venv route.
- Codex manual installs use `~/.agents/skills` (changed on `main` after v0.1.1).
- `tests/run-tests.sh` is executable and removes generated sources on exit,
  even after an interrupt.

### Fixed

- The Acknowledgments link for Marc Bellemare pointed to another author's
  presentation guide. It now points to Bellemare's own conference and seminar
  presentation tips.
- `compile_deck.py` reports a missing themes folder clearly instead of
  failing inside TeX.
- `check_deck.py` crashed with `AttributeError: 'Rect' object has no attribute
  'get_area'` on PyMuPDF 1.26.5, the release that `pip` picks for Python 3.9
  (such as Apple's bundled `python3`). It now computes areas with `abs(rect)`,
  which works on 1.24 through 2.x. The paste-in install prompt also checks for
  Python 3.10+.

### Documentation

- The sample-talk README notes that its figure crops, metadata and results
  derive from the econ-paper-review-skill demonstration manuscript, which is
  distributed under the PolyForm Noncommercial License 1.0.0.

## 0.1.1 — 2026-07-15

A polish release from a deep review: the house theme matches its reference
style, the stock-theme `econ-slides-compat` adapter, notation discipline for
equations, a navigation and footer overlap detector, handout-safe overlays,
Windows portability, and verified discovery on Claude Code and Codex. See the
[v0.1.1 release](https://github.com/hanlulong/econ-slides-skill/releases/tag/v0.1.1).
Some of its enrichment advice ("arrow intuition lines") was later reversed;
see 0.2.0.

## 0.1.0 — 2026-07-15

First public release: paper-to-talk, discussant decks, deck polishing and venue
retargeting; three Beamer themes behind one semantic interface;
`compile_deck.py`, `check_deck.py` and `crop_figure.py`; and a sample deck built
from a demonstration manuscript. See the
[v0.1.0 release](https://github.com/hanlulong/econ-slides-skill/releases/tag/v0.1.0).
