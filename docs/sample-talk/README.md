# Sample talk

A complete 30-minute author presentation:

- [`conference-30min.pdf`](conference-30min.pdf) and its [LaTeX source](conference-30min.tex)
- [`script.pdf`](script.pdf) and its synchronized [rehearsal-script source](script.tex)
- the shared [result and metadata macros](results.tex)
- the [claim, emphasis, and asset plan](structure-plan.md) written before drafting

The main deck has eleven content frames and ten backup frames. Eight backups are
linked from the main deck; the robustness and policy backups remain available
while browsing the appendix. It uses one
column throughout, native slide tables and equations, and three tight crops of
the manuscript's own figures. No demonstration figure was generated or
redrawn.

## Provenance and stance

The only substantive input was the fictional demonstration manuscript
*Broadband Expansion and Small-Firm Productivity*, published as the sample for
[econ-paper-review-skill](https://github.com/hanlulong/econ-paper-review-skill/tree/main/docs/sample-review).
Its country, program, authors, and data are fictional, and the manuscript
contains deliberate inconsistencies.

The three figure crops in `figures-slides/` and the paper metadata and
source-traced results in `results.tex` derive from that manuscript, which
econ-paper-review-skill distributes under the
[PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0);
both repositories have the same author.

This is still an **author talk**, not a disguised referee report. The positive
result appears on `This paper` and is supported by the cohort comparisons and
the heterogeneity evidence.

The rollout is staggered, so the main evidence is the paper's cohort-by-cohort
comparison (Figure 3): each 2011–2015 cohort against municipalities connected
at least three years later, which never uses an already-connected place as a
control. The pooled two-way coefficient (0.034 log points, Table 2) sits at
the low end of those comparisons and below every post-arrival event-study
coefficient, the pattern a pooled estimate shows when effects grow over time
(Goodman-Bacon 2021). It is reported as a summary and kept in backup, not
headlined; the plan's ledger marks it `conflicted (estimator)`. A short `Roadmap` follows the introduction, and a
dedicated `Data` slide defines the sample, outcome, exposure, and
communication-intensity measure before the design. The visible pretrend sets
the interpretation once, beside the event-study evidence that reveals it. It
is not repeated on the punchline or conclusion, so those frames retain the
author-talk hierarchy. The concise conclusion has no navigation links and ends
on the economic implication. Secondary source conflicts are documented in the
plan and linked appendix rather than promoted into equal-weight contributions.

Every displayed magnitude is traced in `results.tex` or a nearby source
comment. Where prose and tables disagree, the deck uses the exact table cell,
states the conflict in backup, and avoids causal or fiscal language the source
cannot support.

## Verification

- Deck: 23 physical PDF pages; 11 numbered main frames; checker score **100**;
  no blockers and no overfull boxes. Its one whitespace prompt is reviewed and
  intentional on the concise conclusion.
- Script: 9 letter-size pages; 3,093 prepared words; 9 selected Q&A blocks;
  synchronized title order, no checker findings or warnings, and no overfull
  boxes.
- Visual QA: every deck page, every script page, and all three source crops
  were inspected at rendered size.

The prepared script is about 22.9 minutes at the 135-word-per-minute audit
pace, leaving about 7 minutes for questions. A slower rehearsal should lead
to trimming—not borrowing from the question period.
