# Structure plan — "Broadband Expansion and Small-Firm Productivity"

15-minute conference talk, house theme. Review this before the deck; it is the
cheapest moment to change course.

## Phase 0 intake (what I assumed, since running non-interactively)

- **Genre:** conference talk (short). **Clock:** 15 min. **Theme:** `econ-slides-house` (as requested).
- **Audience:** assumed field-adjacent generalists (default for a conference). Pitched to
  "JEP not Econometrica": model stays intuitive, one equation, results carry.
- **Materials:** the paper PDF only. No source data, so figures are *cropped* from the
  paper (exhibit-surgery §Figures "no source to rebuild from"), not rebuilt. Tables are
  rebuilt for slides from the printed numbers.

## Slide budget

15 min ⇒ 7 content frames + rich appendix (talk-structures.md short-talk arc:
motivation+question, this-paper, data, design, main result, mechanism, conclusion).
Model vs results: results carry; the model gets **one** fused mechanism slide because
Proposition 1's heterogeneity prediction *is* the second contribution.

## Concept → color map (held for the whole talk)

- `cTreat = cAccentC` (teal) — broadband / treatment. Chosen to match the paper figures'
  teal, so the cropped figures agree with the text color.
- `cMech = cAccentA` (blue) — communication intensity / the complementarity channel.
- `cHighlight` — the one punchline phrase per slide.

## Content frames (assertion titles + exhibit)

1. **"Small firms adopt technology late — can broadband close the gap?"**
   (motivation+question, text). Striking fact: small firms are most of employment but
   adopt tech later/less completely (`\graycite` Syverson '11; Bloom et al. '12). Question
   as economics: causal effect of universal broadband on small-firm productivity, and
   whether the gain concentrates where a task-outsourcing model predicts. Antecedents
   (`\graycite` Czernich '13; Akerman '15; Hjort–Poulsen '19) are aggregate / worker-level.
2. **"This paper"** (punchline, enumerate). Framing line + 3 numbered contributions,
   mirroring the paper's stated threefold contribution:
   1. First causal small-firm estimates: broadband raises labor productivity by
      `\KeyIdea{3.4%}` (0.034, s.e. 0.002).  *[Table 2 col (1), p.7]*
   2. Gains concentrate in communication-intensive firms, as a task-outsourcing model
      predicts (interaction 0.032, s.e. 0.005).  *[Table 4 col (1), p.9]*
   3. Large policy return: repays its €2.3bn cost within six years via small firms alone.
      *[§7, p.8–9]*
   Implication: universal broadband is among the most cost-effective productivity policies
   for small open economies.
3. **"Data"** (structural, text, RunIn). Sample 9,400 firms, 3–49 employees, 2008–2019
   (112,800 firm-years) *[§4.2, p.5]*; treatment = year the municipality's backbone entered
   service *[§4.1, App B]*; outcome = log real value added per worker *[App B]*; het measure
   = 2008 wage-bill share of communication-intensive occupations, mean 0.42 *[Table 1, p.5]*.
   Nav → summary stats (A1).
4. **"Staggered rollout timing identifies the effect"** (figure = Fig 1 rollout, cropped).
   Subtitle carries the identifying assumption; `\Takeaway` = timing set by the 2010 Act
   and terrain, not firm prospects. Nav → placebo (A4).
5. **"Effects appear only after arrival and build for five years"** (MAIN exhibit = Fig 2
   event study, cropped). Subtitle: coefficients vs. year before arrival; 95% CIs,
   firm-clustered. `\Takeaway` gives the average DiD gain 3.4% (0.034, s.e. 0.002).
   Nav → full table (A2) + robustness (A3).
6. **"Gains concentrate where the model predicts"** (mechanism; annotated estimating
   equation, γ term highlighted). Proposition 1: gain strictly increasing in communication
   intensity. Confirmed γ̂ = 0.032 (s.e. 0.005) *[Table 4]*; one SD above mean ⇒ gain
   ~one-fifth larger than the average firm *[§6.3, p.8]*. Nav → model (A7) + het table (A6).
7. **"Conclusion"** — mirrors "This paper": same 3 numbered contributions, same Implication.

## Appendix (linked, each with a Back button)

- A1 Summary statistics (Table 1 → mean/SD/N; min/max dropped, see note) ← Data
- A2 Baseline estimates, full (Table 2 cols 1–4, col 1 highlighted) ← Main result
- A3 Robustness perturbations (Table 5) ← Main result
- A4 Placebo test (Table 3: −0.004) ← Design
- A5 Cohort estimates (Fig 3, cropped: positive & similar ⇒ no negative weighting) ← Main result
- A6 Heterogeneity table (Table 4 cols 1–2) ← Mechanism
- A7 The model (production fn, sourcing rule, Prop 1) ← Mechanism
- A8 Policy arithmetic (€410M/yr, €2.3bn, six-year payback) ← Conclusion
- A9 Related literature (deploy only if asked)

## Number-provenance notes (paper is a demo with intentional inconsistencies)

- Headline **3.4%** = Table 2 col (1) 0.034 and the intro/conclusion. The **abstract's
  "34 percent" is a typo**; not used.
- Text §6.1 calls the region-trends coefficient **0.024**, but **Table 2 col (3) shows
  0.030**; Table 5 col (1) also 0.030. I use the table value 0.030 and present robustness
  as a range 0.030–0.037.
- Table 1 lists Employees **max 19.0 < mean 23.4** (impossible). On the summary-stats slide
  I keep mean/SD/N and drop min/max (legitimate slide-table surgery), which avoids
  displaying the bad cell.
- §7 phrases the level gain "3.4%" as "3.4 percentage points per year" of growth (a
  level-vs-growth slip). I present only the euro figures and the six-year payback, not the
  growth-rate phrasing.

## What I deliberately leave out

Literature-review slide (antecedents are `\graycite` inline + one appendix slide only);
the full model derivation (App A of the paper → one appendix slide, statement not proof);
ICT-investment control detail; sectoral figure (Fig 4) — not load-bearing for 15 min.
