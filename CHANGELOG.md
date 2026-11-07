# Changelog

All notable changes to econ-slides. Versions follow semantic versioning.
From 0.2.0, release tags use the OpenEcon.ai catalog form
`econ-slides--vX.Y.Z`; the earlier `v0.1.0` and `v0.1.1` tags stay as they are.

## 0.2.0 — 2026-11-07

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
  two copies. That includes the `~/.codex/skills/econ-slides` link that the
  v0.1.x README told Codex users to make; Codex still loads it.
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
  "ship". A deck that shows `??`, `(?)` or `[?]` as literal text declares it
  with a source comment, `% econ-slides: allow-literal-marker (?) ??`, or with
  `--allow-literal-marker`; the marker is then waived only when `--log` is
  given and reports no undefined citation or reference.
- Bibliography-aware compile. `compile_deck.py` runs BibTeX or Biber between
  passes when the source tree uses `\bibliography` or `\addbibresource`, and
  reports `undefined_refs` in its JSON and OK line. The tool runs from the
  source folder, so `\bibliography{../refs}` resolves as it does in an
  in-place build, and a prebuilt `.bbl` beside the source (an arXiv or
  Overleaf export) is kept when the database is missing. With biblatex's
  `backend=bibtex`, the build folder is on BibTeX's search path too, so the
  `-blx.bib` file biblatex writes there is found.
- `check_deck.py` exit codes: 0 ship, 1 not ready (must fix, fix
  recommended, or incomplete), 2 the check could not run (bad arguments, a
  missing input, or no PyMuPDF; this was 1 before), 3 the checker crashed. A
  crash used to exit 1 like "must fix", so the documented baseline command
  accepted it and saved an empty baseline; it now stops, and the command also
  runs `test -s` on the saved JSON. `check_script.py` exits 3 on a crash too.
- A `check_deck.py` run without `--tex` or `--log` now lists the checks it
  skipped (`skipped_checks`, `complete: false` in the JSON) and reports
  "incomplete" instead of "ship".
- `compile-error` hard blocker in `check_deck.py`: a TeX error (a `! ...`
  line) in the log blocks delivery. A halted build, a `nonstopmode` build that
  wrote every page despite an undefined macro, and a missing figure used to
  score 100 and ship. A `--baseline-json` comparison can treat an inherited
  error as inherited, so an Overleaf deck that compiles despite errors can
  still take a scoped edit.
- `check_deck.py --log` must be the log of the build that made the PDF: a TeX
  engine banner, and an `Output written on` line with the PDF's stem and page
  count. An empty file, `/dev/null`, the `.tex` itself or another deck's log
  now stops the check (exit 2) instead of counting as a clean log that could
  waive a literal `??`. A log much older than the PDF gets a note.
- `check_script.py --genre conference|seminar|job-talk|discussant` sets the
  speech window for a `--slot-minutes` clock. Only an overrun fails; a script
  under the window gets a warning, as the docs already said. The warning gives
  the shortfall in minutes and, past 10 minutes, cites Piazzesi's limit
  instead of calling it fine; declared minute labels below the window no
  longer get a fill target. The summary line
  and JSON now show the assumed speaking pace (`--wpm`, default 135), which
  SKILL.md and speaker-script.md now tell the agent to ask for.
- `discussant.md` lists typical discussant allocations (ASHEcon: usually 5–7
  minutes for a 15-minute paper; the Dallas Fed's undergraduate Economic
  Scholars Program: 10 minutes), and the README's
  discussant example uses a 7-minute slot instead of a 15-minute total
  session.
- `compile_deck.py --timeout` (default 600 s). A timed-out run now returns the
  usual JSON with `ok: false` instead of a traceback.
- `requirements.txt` (PyMuPDF) and a `tlmgr install` line for BasicTeX, TinyTeX
  and other minimal TeX installs.
- A Contents list in each reference file over 100 lines.
- Light CI: TeX-free unit tests (`tests/test_static.py`) on Python 3.10 with
  PyMuPDF 1.x and 3.12 with the latest PyMuPDF, the skills-ref and
  `claude plugin validate --strict` validators, a weekly Markdown link check,
  and Dependabot for GitHub Actions. Decks are not compiled in CI.
- `references/design-checks.md`: one card each for difference-in-differences
  and event studies, regression discontinuity, instrumental variables,
  shift-share, synthetic control, randomized experiments and multiple testing
  (what the slide must show, the usual overclaim, canonical references).
- Trigger evals for `claude plugin eval` (`evals/`): three requests the skill
  should take and four it should leave alone (a paper's discussion section, a
  PowerPoint deck, editing an introduction, a referee report).
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

- The skill description is scoped to LaTeX/Beamer talks. It drops the bare
  "slides" and "discussion" triggers and keeps "talk", "presentation" and
  "deck" only for Beamer or LaTeX slides on an economics paper; says it is
  not for PowerPoint, Keynote or Google Slides; and routes paper writing to
  econ-write and referee reports to econ-review. The plugin manifests say the
  same in short.
- Rules that changed since the v0.1.1 notes:
  - Arrows are no longer bullet markers. v0.1.1 suggested "arrow intuition
    lines"; `\item[$\Rightarrow$]` and `\item[$\rightarrow$]` are now the
    `arrow-bullet` hard blocker. Use an ordinary nested bullet, a neutral run-in
    label, or a direct sentence.
  - The opening object is called "Key question", never "economic question"
    (`question-label` hard blocker).
  - The conclusion carries no navigation buttons or appendix links
    (`conclusion-link` hard blocker).
  - Clocks are total sessions unless stated as speaking time. The prepared-
    speech share now depends on the genre: 75–80% for a conference talk,
    60–70% for a department seminar or job talk (following Piazzesi's 60 of 90
    minutes and Startz's advice to leave time for interruptions), and at most
    80% for a discussion.
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
- Both READMEs say how to update and uninstall a plugin, manual or paste-in
  install. The uninstall `rm -f` also removes a v0.1.x `~/.codex/skills` link
  and does not fail when only one client was linked.
- The paste-in install prompt says what to do when xelatex is missing (install
  a TeX distribution) apart from a failed Python check (a venv), and its `uv`
  example installs the requirements with `uv pip install -p`, since a
  `uv venv` has no pip.
- `requirements.txt` asks for PyMuPDF 1.24.3 or newer, the first release
  that installs the `pymupdf` module name the test runners and SKILL.md use.
- `compile_deck.py` hints: a missing figure or `\input` file gets a path hint
  instead of "tlmgr install", whether the figure is named with its extension
  (XeTeX's "Unable to load picture", the pdfTeX and LuaTeX driver errors) or
  without; a missing `.sty` or `.cls` gets `tlmgr search --global --file` and
  the sudo note for MacTeX. Error lines are read from the unwrapped log, so
  they are no longer cut at 79 columns. When the engine is installed (for
  example in `/Library/TeX/texbin`) but not on PATH, the error says so
  instead of telling the user to install TeX. With `--json`, these early
  failures are JSON too. A crash exits 3.
- A `\hyperref[key]{...}` to a missing label is reported as a dead link with
  its key (`dead-link`, which a baseline can treat as inherited), not as an
  unexplained undefined reference; nothing renders as `??` for it.
- `tests/run-tests.sh` is executable and removes generated sources on exit,
  even after an interrupt.

- Econometric guidance:
  - `source-integrity.md` adds a staggered-adoption check. A static two-way
    fixed-effects coefficient is compared with the event-study path and any
    cohort or heterogeneity-robust estimates; robust evidence is headlined, and
    a static coefficient below all of them is `conflicted (estimator)`.
  - Pre-period coefficients are described as a partial, often low-powered
    check that never "tests" or "validates" parallel trends (Roth 2022), with
    Rambachan–Roth sensitivity in backup when the paper has it, and a warning
    not to read newer estimators' event-study plots as TWFE plots.
  - The default table recipe no longer adds significance stars. It reproduces
    the source's convention, following the AER Style Guide ("Do not use
    asterisks to denote significance").
  - Numbers are rounded, never truncated. Log points convert to percent as
    100 × (exp(b) − 1) once |b| exceeds about 0.1, and a ratio of rounded
    entries carries its rounding range.
  - A supporting heterogeneity cut records whether it was pre-specified, and
    an Implication line under a descriptive result avoids causal verbs.

### Fixed

- The Acknowledgments link for Marc Bellemare pointed to another author's
  presentation guide. It now points to Bellemare's own conference and seminar
  presentation tips.
- Guide attributions checked against the sources. The "slide lets a listener
  catch back up" rule is Shapiro's, not Meager's; "people don't remember
  equations from one slide to the next" is Cochrane's, beside Piazzesi's
  "Explain every symbol"; Cochrane rejects any results preview, so the
  one-sentence bottom line is credited to Shapiro and Startz; "JEP, not
  Econometrica" is Tabarrok's, as quoted by Startz with his caveat; Shapiro's
  "30 minute talk" line credits Matthew Rabin. The README no longer calls the
  guides "unanimous" about literature reviews, and the Acknowledgments now
  link the Startz, Piazzesi, Meager, Tabarrok, Davis, Dallas Fed and ASHEcon
  guides.
- `compile_deck.py` reports a missing themes folder clearly instead of
  failing inside TeX.
- A nested `\input` is resolved from the main file's folder, as TeX does, so
  an `allow-literal-marker` comment or a `\bibliography` two levels down in a
  modular deck is no longer missed.
- An unreadable `--tex`, `--log` or PDF, a folder passed as a file, an
  unwritable `--render-dir`, and a `scripts/` folder missing a sibling script
  exit 2 ("could not run") instead of 3 or 1. All three scripts write
  characters the console code page lacks as escapes instead of crashing
  (Windows ANSI code pages).
- `check_deck.py` crashed with `AttributeError: 'Rect' object has no attribute
  'get_area'` on PyMuPDF 1.26.5, the release that `pip` picks for Python 3.9
  (such as Apple's bundled `python3`). It now computes areas with `abs(rect)`,
  which works on 1.24 through 2.x. The paste-in install prompt also checks for
  Python 3.10+, and `requirements.txt` and both READMEs note the size of a
  PyMuPDF 2.x install (about 265 MB with onnxruntime and numpy) and the
  smaller `pymupdf>=1.26,<2` alternative.

### Documentation

- The 30-minute sample talk now headlines the paper's cohort-by-cohort
  comparisons for its staggered rollout: each 2011–2015 cohort against
  municipalities connected at least three years later (Figure 3). They are
  clean-control comparisons only if the paper's unstated event window ends
  before the controls connect, and the slide says so. Its takeaway is an
  economic reading, the design slide says what the pooled equation does, and
  the script and ledger keep to the five waves shown, log the Figure 3
  caption/axis unit conflict, and mark the low-end comparison as a visual
  reading. The static
  two-way coefficient (0.034 log points), which sits below every post-arrival
  event-study point, moves to a backup as a pooled summary, and the script no
  longer describes it as a comparison with waiting firms only. The design
  slide says pre-arrival coefficients "check for diverging trends" rather than
  "test" parallel trends; the Implication avoids a causal verb; the placebo
  backup reports the rounding range of its t ratio; and the README images are
  regenerated. The Implication now says the differences track communication
  intensity, as the model predicts, instead of naming unmeasured frictions.

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
