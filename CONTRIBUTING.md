# Contributing

Bug reports and improvements are welcome.

- **Bad slides are bugs.** If the skill produced an ugly, dishonest, or broken
  slide, open a ["Report a bad slide"](../../issues/new?template=bad-slide.yml)
  issue with the `.tex` snippet or a screenshot — redact anything confidential.
- **Small fixes** (typos, docs, checker false positives): open a pull request
  directly.
- **Behavior changes** (workflow steps, references, themes, checkers): open an
  issue first so the design can be agreed — the reference files encode
  deliberate craft rules, and a well-meaning change can break them silently.
- Run `tests/run-tests.sh` before a pull request that touches `scripts/` or
  `themes/`.

By contributing you agree that your contribution is licensed under the
[MIT License](LICENSE).
