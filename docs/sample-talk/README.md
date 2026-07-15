# Sample talk

A complete 15-minute conference deck — [`conference-15min.pdf`](conference-15min.pdf)
with its [LaTeX source](conference-15min.tex) and the
[structure plan](structure-plan.md) the skill produced before drafting.

**Provenance.** This deck was built *cold* by an agent following `SKILL.md`
literally, from a single input: the fictional demonstration manuscript
"Broadband Expansion and Small-Firm Productivity" used as the public sample
of [econ-paper-review-skill](https://github.com/hanlulong/econ-paper-review-skill)
(see its `docs/sample-review/demo-paper.pdf`). The run took four
compile/check iterations and finished at a verification score of 100.

Two honesty notes:

- The manuscript is fictional and **contains deliberately planted errors**
  (it exists to test reviewing tools). The deck presents the paper's claims
  as a presenter would — including, e.g., its "first causal evidence" claim
  — because a slides skill presents your paper; refereeing it is the sibling
  skill's job. Where the manuscript contradicts itself on a number (its
  abstract's "34 percent" vs. the body's 3.4%), the deck follows the
  coefficient in the results table.
- Every number on the slides is tagged with its source table/page in the
  `.tex` comments — that is the skill's number-provenance rule at work.

The figures under `figures-slides/` were cropped from the manuscript PDF
with `scripts/crop_figure.py` (the paper's underlying data are simulated,
so the figures could not be rebuilt from source).
