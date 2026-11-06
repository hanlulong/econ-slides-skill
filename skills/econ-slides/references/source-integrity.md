# Source integrity: claims must survive the paper

Use this pass whenever a paper, report, or draft becomes a talk. A slide deck
is an argument, but it is not permission to make the source cleaner or more
causal than it is. Paper prose is a claim; assignment rules, exhibits, table
notes, units, and algebra are the evidence. For an author talk, this pass
protects the authors' story; it does not turn the deck into a referee report.

## Contents

- Build a claim--evidence ledger before the outline
- Keep disclosure proportionate in an author talk
- Identification and estimands
- Models, mechanisms, and policy arithmetic
- Numbers, figures, and contradictions
- Delivery audit

## Build a claim--evidence ledger before the outline

For every candidate headline, record four fields in `structure-plan.md`:

| Planned claim | Best evidence | Source location | Status |
|---|---|---|---|
| [one-sentence assertion] | [exhibit/design/model condition] | [page/table/figure] | supported / descriptive only / conflicted / excluded |

- **Supported**: the evidence directly warrants the wording.
- **Descriptive only**: the pattern is real, but the design does not support a
  causal or structural interpretation.
- **Conflicted**: prose, exhibit, units, assignment, or algebra disagree.
  Document the conflict and weaken the claim; do not vote among mentions. Put
  it in the main line only when it changes the headline result. Otherwise use
  a linked backup and report it in the handoff.
- **Excluded**: the claim depends on an untraceable number, invalid step, or
  evidence the materials do not contain. Leave it out and tell the user why.

The status governs both title and script. The spoken layer may simplify a
claim, but never strengthen it: *associated with* cannot become *raises*;
*consistent with* cannot become *validates*; illustrative arithmetic cannot
become *pays for itself*.

## Keep disclosure proportionate in an author talk

The ledger governs wording and disclosure, not rhetorical weight. Before the
outline, reduce it to the author-story hierarchy:

- **Primary takeaway:** the strongest economically interesting claim that
  survives the evidence pass.
- **Up to two supports:** the design, mechanism, or heterogeneity findings that
  make the takeaway credible or useful.
- **Boundary audit:** identify the single qualification that most changes how
  the takeaway should be interpreted. Keep it in the working ledger even when
  it does not belong on screen.

Show that boundary only when omitting it would materially misstate a headline.
When visible, state it once beside the relevant design or result. Do not add it
by default to ``This paper'' or the conclusion, put it on the title page,
elevate it to a numbered contribution, turn every result slide into a threat
audit, or give it a larger box or stronger color than the finding. Secondary
inconsistencies, alternative specifications, and source repairs belong in the
appendix and delivery note.

If a contradiction invalidates the headline rather than bounding it, the main
claim must change and the invalidating fact belongs in the main line. If that
change would produce a fundamentally different genre from the requested author
talk, pause and ask whether to deliver the weaker author story or a critical
presentation.

## Identification and estimands

Before using a causal verb, check all of the following against the source:

1. **Assignment**: what determined treatment timing or intensity? A schedule
   fixed in advance is not exogenous if the schedule used projected outcomes.
2. **Estimand**: treatment, outcome, unit, sample restriction, and comparison
   group are named correctly. Availability is not take-up; a balanced survivor
   panel is not the original population.
3. **Diagnostics**: read the plotted coefficients and intervals, not only the
   paper's caption. Visible pre-trends override prose that says "no pre-trend."
   The converse does not hold: flat pre-period coefficients are a partial and
   often low-powered check, and they cannot confirm that post-period trends
   would have stayed parallel (Roth 2022). Never write that pre-period
   coefficients "test" or "validate" parallel trends; they "check for
   diverging trends before treatment".
4. **Estimator**: the method is valid for the assignment structure and effect
   heterogeneity claimed. A robustness table does not repair a mismatched
   estimand. For staggered adoption, run the check below.
5. **Inference**: uncertainty respects the assignment level and dependence.

**Staggered adoption.** When treatment timing varies across units and the
paper's headline is a static two-way fixed-effects (TWFE) coefficient:

- A static TWFE coefficient is a weighted average of all two-by-two
  comparisons, including comparisons that use already-treated units as
  controls (Goodman-Bacon 2021); with heterogeneous or growing effects some
  weights can be negative (de Chaisemartin and D'Haultfœuille 2020).
- Compare it with the event-study path and with any cohort-specific or
  heterogeneity-robust estimates the paper reports (Callaway and Sant'Anna
  2021; Sun and Abraham 2021; Borusyak, Jaravel and Spiess 2024; de
  Chaisemartin and D'Haultfœuille 2020).
- If the paper reports robust estimates, headline those. If it reports only
  cohort-specific comparisons with not-yet-treated units, headline that
  evidence and show the static coefficient as a regression-weighted summary.
  If the static coefficient sits below every post-treatment or cohort
  estimate, record it as `conflicted (estimator)` in the ledger and never call
  it "the average effect".
- In a TWFE event study with staggered timing, the lead and lag coefficients
  can be contaminated by effects from other periods, so even the pre-trend
  reading is not clean (Sun and Abraham 2021).
- Never compute a robust estimate the paper does not report; ask, or name
  the gap in the delivery note.

`design-checks.md` gives the same kind of check for regression
discontinuity, instrumental variables, shift-share, synthetic control,
randomized experiments and multiple testing, and lists full references for the
papers cited here.

Classify a failed link by consequence. If it invalidates the headline, use
descriptive language and state the boundary once beside the design or result.
If it narrows scope without changing the headline pattern, use one short
qualification. If it is a secondary diagnostic or source inconsistency, move
it to a linked backup and the handoff rather than repeating it in the main
story.

## Models, mechanisms, and policy arithmetic

- A theoretical result is headline-ready only under the conditions actually
  shown. Check algebra, symbol definitions, domains, and whether a local or
  switching-regime result is being stated globally.
- Heterogeneity is **consistent with** a channel unless the evidence
  discriminates that mechanism from alternatives. An interaction coefficient
  does not by itself identify an unobserved behavior.
- When a heterogeneity cut or a secondary outcome becomes a supporting claim,
  record whether it was pre-specified and how many alternatives the paper
  reports. A support picked from many cuts is labeled exploratory
  (`design-checks.md` §Multiple testing).
- An Implication line inherits the ledger status of the evidence beneath it.
  When the primary result is `descriptive only`, the Implication avoids causal
  verbs ("matters", "raises", "drives"): write "gains are concentrated where
  ...", not "infrastructure matters most where ...".
- Trace policy calculations as a unit-preserving chain on the slide or in its
  note. Do not silently turn a labor-productivity level effect into TFP growth,
  annual output, fiscal revenue, welfare, or comparative cost-effectiveness.
- Label conditional arithmetic as conditional. State the load-bearing
  assumptions in the main reading and keep the fuller list — causality,
  permanence, discounting, maintenance cost, incidence, and the distinction
  between gross output and fiscal return — in a linked backup when space is
  limited.

## Numbers, figures, and contradictions

- Never read an exact magnitude from a raster plot unless the underlying data
  or a source table supplies it. Describe the visible shape instead.
- When a conflicted number is displayed, give it a visible dagger and both
  source locations. A substantive conflict changes the headline; it is not
  resolved by choosing the coefficient or the majority of mentions. A
  secondary numeric conflict need not be promoted into the main deck merely
  because it was found.
- Keep displayed and spoken magnitudes in shared macros when the deck and
  script are generated together. Every magnitude also carries an adjacent
  source comment.
- Treat bibliographic metadata as evidence, not decoration. Verify author,
  year, title, and venue against the cited work before placing them on a slide;
  a manuscript's reference list can itself be wrong. If verification is
  outside scope, omit unverified years and venues rather than repeating them.
- Verify the literature before making priority claims ("first," "only,"
  "largest," "cheapest"). If that verification is outside scope, use a narrow
  descriptive contribution instead.

## Delivery audit

Before shipping, read only the frame titles and then only the script's first
sentences. Each must match the ledger's status, and together they must still
tell the requested author story: one takeaway and up to two supports, with a
boundary appearing only where accuracy requires it. Report unresolved
conflicts, excluded claims, and consequential sample or estimand limits in the
handoff even when they appropriately stay out of the main deck.
