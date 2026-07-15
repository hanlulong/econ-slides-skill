# Structure plan — 15-minute conference talk

**Paper:** Lindqvist & Berg, "Broadband Expansion and Small-Firm Productivity:
Evidence from a Staggered Municipal Rollout" (July 2026).

**Intake (Phase 0)**
- Genre: short **conference talk**
- Clock: **15 minutes** -> budget 8-10 content slides + linked appendix (talk-structures.md)
- Audience: assumed **smart generalists** (default for a conference; not field-expert-only). Pitch to "JEP not Econometrica."
- Theme: **econ-slides-house** (user asked for "house")
- Materials: paper PDF only; **no figure source** -> paper figures cropped from the PDF per exhibit-surgery no-source rule; regression exhibits rebuilt as slide tables.

**Short-talk emphasis choice (talk-structures.md):** chose **results over model**.
The model gets exactly one main-line slide (its testable prediction + the
heterogeneity result); the full derivation and Proposition 1 go to the appendix.

## Main line (9 content slides; assertion titles)

1. **Digital infrastructure could close the small-firm productivity gap** — motivation, text. Small firms = most employment, adopt tech last (Syverson '11; Bloom et al. '12). Exhibit: none (policy-question motivation).
2. **Existing work has bypassed the small-firm segment** — question as economics + 2-4 gray antecedents (Czernich '13; Akerman '15; Hjort-Poulsen '19). Exhibit: none.
3. **This paper** — punchline slide. Numbered: (1) first causal small-firm estimate, broadband raises labor productivity by KeyIdea 3.4%; (2) gains concentrate in communication-intensive firms, as a task-outsourcing model predicts; (3) program repaid its cost in six years. Implication line. Exhibit: none.
4. **Setting and data** — RunIn bullets: NBP, 284 municipalities, 9,400 firms 2008-2019 (112,800 firm-years). Nav -> summary stats. Exhibit: none.
5. **Fiber reached towns one at a time, on a fixed schedule** — **Figure 1** (rollout, cropped). Key assumption in subtitle; one bullet on threat + answer. Nav -> placebo, cohorts.
6. **Productivity is flat before arrival, then climbs steadily** — **Figure 2** (event study, cropped). Takeaway: no pre-trends; average gain 3.4% (Table 2). Nav -> baseline table, robustness.
7. **Gains concentrate in communication-intensive firms** — surgical **slide table from Table 4** (interaction 0.032, teal). Model prediction (Prop 1) stated. Nav -> model appendix.
8. **The program paid for itself within six years** — **ResultBox** with euro magnitudes (410M/yr vs 2.3B cost). Exhibit: ResultBox.
9. **Conclusion** — mirrors slide 3 (same numbering, same Implication).

## Appendix (linked, `\AppendixStart`)
- A1 Summary statistics (Table 1; mean/SD/N only — Min/Max dropped, see notes) <- from Data
- A2 Model and estimating equation (eq 5, Proposition 1 in ResultBox) <- from Mechanism
- A3 Baseline difference-in-differences table (Table 2, 4 cols) <- from Main result
- A4 Robustness (Table 5, 3 cols) <- from Main result
- A5 Placebo with permuted rollout years (Table 3) <- from Design
- A6 Effects by rollout cohort (Figure 3) <- from Design
- A7 Related literature (deploy only if asked; no inbound link)

## Semantic color code (held for the whole talk)
- `cAccentA` blue = **broadband / treatment effect** (beta term, Table 2 col 1)
- `cAccentC` teal = **communication intensity / mechanism** (gamma term, Table 4 interaction)
- `cHighlight` magenta = the one punchline phrase (3.4%) via `\KeyIdea`
- Included paper figures keep their original teal ink (cannot recolor without source) — flagged.

## Number-provenance ledger (every slide number tagged in-source)
- 3.4% main effect = 0.034 (0.002)  [Table 2 col 1, p.7]
- Table 4 interaction 0.032 (0.005); level 0.020 (0.003) / 0.034 (0.002)  [Table 4, p.9]
- Placebo -0.004 (0.002)  [Table 3, p.8]
- Robustness 0.030 / 0.034 / 0.037  [Table 5, p.9]
- 410M euro/yr, 2.3B cost, six-year payback  [Section 7, p.8-9]
- 284 munis, 9,400 firms, 112,800 firm-years, 2008-2019  [Section 4, p.4-5]

## Deliberate-error handling (paper has intentional errors)
- Abstract "34 percent" contradicts body "3.4 percent" and Table 2 coeff 0.034 -> use **3.4%** everywhere; never show 34%.
- Table 1 Employees Max 19.00 < Mean 23.40 (impossible) -> summary-stats slide shows Mean/SD/N only; no number altered.
- Section 7 conflates a 3.4% level gain with "3.4 pp per year growth" -> state the level effect + euro magnitude only.

*Recorded and proceeding as approved (dogfood: no live user to sign off).*
