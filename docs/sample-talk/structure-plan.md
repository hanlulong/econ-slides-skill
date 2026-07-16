# Structure plan: 30-minute author presentation

## Intake

- **Stance:** authors presenting their paper, not a referee or discussant.
- **Genre and clock:** 30-minute total conference session; 22.5--24 minutes of prepared speech leaves 6--7.5 minutes reserved for questions.
- **Audience:** applied micro, productivity, and policy economists without paper-specific prior knowledge.
- **Theme:** `econ-slides-house`, 16:9.
- **Source:** the fictional demonstration manuscript linked in `README.md`. The source identifies the setting, program, authors, and data as fictional and simulated, with intentional errors (author footnote, paper p. 1).
- **Layout:** one column throughout. No `columns` or `minipage` layouts.
- **Visual policy:** no new figures. Reuse three previously inspected source crops; use native TeX text, equations, and surgically shortened tables for everything else.

## Emphasis ledger

- **Primary takeaway:** small-firm labor productivity is 0.034 log points higher after municipal backbone arrival in the paper's baseline specification.
- **Support 1:** the reported post-arrival coefficient stays between 0.030 and 0.034 across the four Table 2 specifications.
- **Support 2:** one standard deviation more pre-program communication intensity adds 0.0064 log points, about one-fifth of the main 0.034 difference (`0.032 x 0.20`).
- **Boundary:** projected growth helped determine rollout order, and the paper's event-study figure rises before arrival; the talk therefore describes associations rather than causal effects or fiscal returns.
- **Implication:** digital infrastructure may matter most where communication frictions bind.

## Claim--evidence ledger

| Planned claim | Best evidence | Source | Status |
|---|---|---|---|
| Every municipality joined the backbone in eight rollout waves from 2011 to 2018. | Program description and cumulative rollout figure. | pp. 1, 4--5; Figure 1 | supported |
| The estimation panel contains 9,400 firms and 112,800 firm-years from 2008 to 2019. | Sample construction and Table 1. | pp. 1, 4--5; Table 1 | supported |
| Treatment is municipal backbone availability, not observed firm take-up. | Baseline treatment definition and Appendix B. | pp. 4--6, 11 | supported |
| The baseline post-arrival association is 0.034 log points with reported SE 0.002. | Exact load-bearing table cell. | Table 2, col. (1), p. 7 | descriptive only |
| Table 2 coefficients span 0.030--0.034 across the four reported specifications. | Exact Table 2 cells. | Table 2, cols. (1)--(4), p. 7 | descriptive only |
| One SD more communication intensity adds 0.0064 log points, about one-fifth of 0.034. | `0.032 x 0.20`, with both inputs displayed. | Tables 1 and 4, pp. 5 and 9 | descriptive only |
| The model predicts a positive communication-intensity gradient in the switching case. | `G'(theta)>0` under `kappa_1 p <= phi w < kappa_0 p`. | Proposition 1 and proof, pp. 2--3 | supported, conditional |
| Projected growth helped determine rollout order. | Published score prioritized below-median levels and above-median projected growth. | Section 4.1, p. 4 | supported |
| The plotted pre-arrival coefficients rise toward treatment. | Visible shape of the source figure; no exact pixel values used. | Figure 2, p. 7 | supported |
| The paper's “no differential pre-trends” reading is inconsistent with Figure 2. | Prose versus source figure. | pp. 2, 6--7; Figure 2 | conflicted |
| The placebo is a precisely estimated zero. | Table reports -0.004 with SE 0.002, while prose calls it indistinguishable from zero. | Table 3 and Section 6.2, pp. 7--8 | conflicted |
| The abstract's 34 percent is the headline magnitude. | Abstract conflicts with 3.4 percent in the text and 0.034 in Table 2. | pp. 1--2; Table 2, p. 7 | conflicted; excluded |
| Region trends produce 0.024. | Prose conflicts with Table 2's 0.030. | Section 6.1, p. 6; Table 2, p. 7 | conflicted; table cell used |
| The program paid for itself within six years. | The source does not provide a unit-preserving chain from the regression estimand to fiscal return. | Section 7, pp. 8--9 | excluded |
| Figure 4 shows broadband effects within sectors. | Figure 4 shows sector levels, not effects. | Section 6.4, p. 8; Figure 4, p. 10 | excluded |

## Main-deck arc

1. **Key question**
   Single-column motivation, empirical test, and policy relevance. No exhibit. Status: supported question.
2. **This paper**
   Primary result, larger difference for communication-intensive firms, and
   the positive implication. No inference details or repeated caveat; the
   interpretation-changing boundary belongs with the event-study evidence.
   Status: descriptive only.
3. **Roadmap**
   Three quick stops: setting and data; design and main evidence; model and
   interpretation.
4. **Broadband reached every municipality in eight waves**
   Source crop of Figure 1. Status: supported.
5. **Data**
   Business Register, audited accounts, worker records, sample restrictions, outcome construction, municipal availability, and the pre-program communication-intensity measure.
6. **The design follows firms as local backbone service arrives**
   Native TWFE equation plus the comparison, fixed effects, counterfactual path, and diagnostic in one column. Status: supported design description.
7. **Labor productivity is about 3.4% higher after arrival**
   Native, surgically shortened Table 2 plus a transparent log-point interpretation. Status: descriptive only.
8. **Productivity rises before and after broadband arrives**
   Source crop of Figure 2. This is the single main-line caveat. Status: conflicted with paper prose.
9. **The model predicts larger gains for communication-intensive firms**
   Native model condition, derivative, and symbol definitions. Status: supported under the switching case.
10. **The broadband association is larger for communication-intensive firms**
   Native Table 4 plus exact one-SD arithmetic inside the table. Status: descriptive only.
11. **Conclusion**
   Two results and the final implication; no repeated boundary, backup links,
   or specification bookkeeping.

## Appendix and selective Q&A

1. Sample restrictions and the Table 1 employment conflict.
2. Rollout assignment and the projected-growth score.
3. Cohort-specific estimates using the source Figure 3 crop.
4. Placebo coefficient and its prose conflict.
5. Table 2 source conflicts: 34 versus 3.4 percent and 0.024 versus 0.030.
6. Table 5 robustness cells and its header--note conflict.
7. Municipal assignment and the reported municipal-cluster column.
8. Full model switching condition and derivative.
9. Interpretation of the larger difference for communication-intensive firms.
10. Missing steps in the six-year policy-payback claim.

The script includes conditional answers only for the high-probability sample, assignment, placebo, inference, model, mechanism, and policy questions. Every scripted backup title exactly matches its slide title.

## Asset inventory and provenance

| Asset | Treatment | Source and provenance | Necessity | SHA-256 |
|---|---|---|---|---|
| `figures-slides/fig1_rollout.png` | reused unchanged | Tight crop of paper Figure 1; cropped from the manuscript PDF without redrawing | The paper's own rollout exhibit is the clearest account of staggered coverage | `91f6b8dbdc0dfa2f90ec7abb0552e23bb894b99f6d34fd170d6717768a0dfae6` |
| `figures-slides/fig2_event_study.png` | reused unchanged | Tight crop of paper Figure 2; cropped from the manuscript PDF without redrawing | The source figure is load-bearing for dynamics and the causal boundary | `8beec2977db1d03d1c3ca9b0846eeb67d92a7df5b8190402b4fc3d9fcdbc7ae1` |
| `figures-slides/fig3_cohorts.png` | reused unchanged | Tight crop of paper Figure 3; cropped from the manuscript PDF without redrawing | Useful only as a linked backup on cohort stability | `64e5aeaebf82c8a003fc13525410fd28f3b5507a2e8148edd40a8b39b14933d9` |
| Table 2 | native TeX table | Exact cells from paper Table 2, p. 7 | The paper table is too wide at presentation scale; a native shortened table preserves exact inputs | not a raster asset |
| Table 4 | native TeX table | Exact cells from paper Table 4, p. 9; SD from Table 1, p. 5 | The native table makes the load-bearing interaction and one-SD arithmetic readable | not a raster asset |
| TWFE and model equations | native TeX equations | Paper equations (6), (3), and Proposition 1 | Equations are clearer and more faithful than a generated design or mechanism diagram | not a raster asset |

No other figure is included, rebuilt, or generated.
