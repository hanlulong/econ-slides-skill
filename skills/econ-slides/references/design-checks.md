# Design checks: what each research design owes the audience

Use this file beside `source-integrity.md` when a talk presents a causal
design. Each card lists what the design or result slide must show, the usual
overclaim, and one or two canonical references. The cards check the paper; they
never license computing an estimate or diagnostic the paper does not report.
When a required object is missing from the source, say so in the delivery note
rather than filling the gap.

## Contents

- Difference-in-differences and event studies
- Regression discontinuity
- Instrumental variables
- Shift-share (Bartik) designs
- Synthetic control
- Randomized experiments and pre-registration
- Multiple testing and chosen supports
- References

## Difference-in-differences and event studies

- **Show:** the comparison (which units, which dates), the base period, the
  event-study path with intervals, and the estimator.
- **Staggered timing:** follow `source-integrity.md` §Staggered adoption. A
  static two-way fixed-effects coefficient below every post-period or cohort
  estimate is a regression-weighted summary, not the average effect.
- **Pre-trends:** flat leads are a low-powered partial check (Roth 2022). A
  sensitivity analysis for violations of parallel trends (Rambachan and Roth
  2023) belongs in backup when the paper has one. Read event-study plots from
  the newer estimators on their own terms (Roth 2024).
- **Overclaim:** "pre-period coefficients test (or validate) parallel trends".

## Regression discontinuity

- **Show:** the running variable, the cutoff, a binned scatter with local fits
  on each side, the bandwidth and polynomial order, and any manipulation or
  covariate-balance checks the paper reports.
- **Fits:** local linear or quadratic fits, not global high-order polynomials
  (Gelman and Imbens 2019).
- **Overclaim:** stating a local effect at the cutoff as an effect for the
  whole population.

## Instrumental variables

- **Show:** the first stage on screen (coefficient and strength), the reduced
  form when the paper has it, and the exclusion restriction in one plain
  sentence.
- **Inference:** with one instrument, conventional t-ratio inference can be
  badly distorted; report weak-instrument-robust inference such as the tF
  adjustment (Lee, McCrary, Moreira and Porter 2022) or Anderson-Rubin
  intervals when the paper does.
- **Overclaim:** presenting a local average treatment effect for compliers
  (Imbens and Angrist 1994) as the effect for everyone.

## Shift-share (Bartik) designs

- **Show:** the shares, the shocks, and which of the two the identification
  rests on.
- **Two readings:** exogenous shares (Goldsmith-Pinkham, Sorkin and Swift
  2020) or quasi-random shocks with possibly endogenous shares (Borusyak, Hull
  and Jaravel 2022). Each comes with its own diagnostics; show the ones the
  paper reports for its reading.
- **Overclaim:** treating a Bartik instrument as exogenous by construction.

## Synthetic control

- **Show:** the treated and synthetic paths with the pre-treatment fit, the
  donor units and their weights, and the placebo comparisons the paper uses
  for inference.
- **Feasibility:** a good pre-period fit, a suitable donor pool and no
  spillovers to donors are preconditions (Abadie 2021).
- **Overclaim:** conventional standard errors or precise confidence intervals
  from one treated unit.

## Randomized experiments and pre-registration

- **Show:** the randomization unit, balance and attrition, and whether the
  estimate is intent-to-treat or treatment-on-the-treated.
- **Registration:** the AEA journals require field experiments to be
  "registered prior to submission" (AEA RCT Registry policy), but
  "Researchers may register during any phase of the trial—forthcoming,
  ongoing, or completed", and no pre-analysis plan is required. So a
  registration alone does not show that an outcome was pre-specified: check
  the registration date and whether a pre-analysis plan exists. In the talk,
  separate pre-specified outcomes and analyses from exploratory ones.
- **Overclaim:** presenting an exploratory subgroup as a pre-specified test.

## Multiple testing and chosen supports

- The emphasis ledger allows up to two supporting claims. When a support is a
  heterogeneity cut or a secondary outcome, record whether it was
  pre-specified and how many alternatives the paper reports.
- With many outcomes, subgroups or treatments, show the multiple-testing
  adjustment when the paper reports one (List, Shaikh and Xu 2019); otherwise
  label the support exploratory.
- **Overclaim:** promoting the one significant cut out of many into a
  headline.

## References

- Abadie, A. (2021). Using Synthetic Controls: Feasibility, Data Requirements,
  and Methodological Aspects. *Journal of Economic Literature* 59(2), 391–425.
- AEA. RCT Registry policy, https://www.aeaweb.org/journals/policies/rct-registry.
- Borusyak, K., P. Hull and X. Jaravel (2022). Quasi-Experimental Shift-Share
  Research Designs. *Review of Economic Studies* 89(1), 181–213.
- Borusyak, K., X. Jaravel and J. Spiess (2024). Revisiting Event-Study
  Designs: Robust and Efficient Estimation. *Review of Economic Studies*
  91(6), 3253–3285.
- Callaway, B. and P. H. C. Sant'Anna (2021). Difference-in-Differences with
  Multiple Time Periods. *Journal of Econometrics* 225(2), 200–230.
- de Chaisemartin, C. and X. D'Haultfœuille (2020). Two-Way Fixed Effects
  Estimators with Heterogeneous Treatment Effects. *American Economic Review*
  110(9), 2964–2996.
- Gelman, A. and G. Imbens (2019). Why High-Order Polynomials Should Not Be
  Used in Regression Discontinuity Designs. *Journal of Business & Economic
  Statistics* 37(3), 447–456.
- Goldsmith-Pinkham, P., I. Sorkin and H. Swift (2020). Bartik Instruments:
  What, When, Why, and How. *American Economic Review* 110(8), 2586–2624.
- Goodman-Bacon, A. (2021). Difference-in-Differences with Variation in
  Treatment Timing. *Journal of Econometrics* 225(2), 254–277.
- Halvorsen, R. and R. Palmquist (1980). The Interpretation of Dummy Variables
  in Semilogarithmic Equations. *American Economic Review* 70(3), 474–475.
- Imbens, G. and J. Angrist (1994). Identification and Estimation of Local
  Average Treatment Effects. *Econometrica* 62(2), 467–475.
- Lee, D. S., J. McCrary, M. Moreira and J. Porter (2022). Valid t-Ratio
  Inference for IV. *American Economic Review* 112(10), 3260–3290.
- List, J., A. Shaikh and Y. Xu (2019). Multiple Hypothesis Testing in
  Experimental Economics. *Experimental Economics* 22(4), 773–793.
- Rambachan, A. and J. Roth (2023). A More Credible Approach to Parallel
  Trends. *Review of Economic Studies* 90(5), 2555–2591.
- Roth, J. (2022). Pretest with Caution: Event-Study Estimates after Testing
  for Parallel Trends. *American Economic Review: Insights* 4(3), 305–322.
- Roth, J. (2024). Interpreting Event-Studies from Recent
  Difference-in-Differences Methods. arXiv:2401.12309.
- Sun, L. and S. Abraham (2021). Estimating Dynamic Treatment Effects in Event
  Studies with Heterogeneous Treatment Effects. *Journal of Econometrics*
  225(2), 175–199.
