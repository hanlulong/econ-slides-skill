# Contributing

Bug reports and improvements are welcome.

- **Bad slides are bugs.** If the skill produced an ugly, dishonest, or broken
  slide, open a ["Report a bad slide"](https://github.com/hanlulong/econ-slides-skill/issues/new?template=bad-slide.yml)
  issue with the `.tex` snippet or a screenshot — redact anything confidential.
- **Small fixes** (typos, docs, checker false positives): open a pull request
  directly.
- **Behavior changes** (workflow steps, references, themes, checkers): open an
  issue first so the design can be agreed — the reference files encode
  deliberate craft rules, and a well-meaning change can break them silently.
- Run `bash tests/run-tests.sh` before a pull request that touches
  `skills/econ-slides/scripts/` or `skills/econ-slides/themes/`. It needs a
  TeX Live install and a `python3` that can import PyMuPDF. If PyMuPDF lives
  in a venv, put that venv first on `PATH`:
  `PATH="$HOME/.venvs/econ-slides/bin:$PATH" bash tests/run-tests.sh`.
- CI (`.github/workflows/ci.yml`) runs only the TeX-free checks:
  `python -m unittest discover -s tests -p "test_*.py"` on Python 3.10 with
  PyMuPDF 1.x and on 3.12 with the latest PyMuPDF, plus `agentskills validate`
  and `claude plugin validate --strict`. It does not compile decks, so the full
  suite above still has to pass locally. A weekly job checks the Markdown
  links.

By contributing you agree that your contribution is licensed under the
[MIT License](LICENSE).
