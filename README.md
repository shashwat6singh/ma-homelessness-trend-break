# Massachusetts homelessness, 2007–2025: a level break, not a rising trend

A one-page policy memo to the Governor of Massachusetts, and the R that produces
every number in it.

The usual framing — homelessness has been rising for a decade — does not fit this
state. Massachusetts had **no detectable upward trend from 2007 to 2022**, and then
the count jumped 89% in two years. Those are different problems with different
instruments: a drifting series points at housing supply and subsidy, a level break in
a right-to-shelter state points at intake capacity, eligibility rules and surge
financing.

![Massachusetts homelessness rate, 2007–2025](output/ma-homelessness-rate-2007-2025.png)

**Read the memo:** [`docs/memo.md`](docs/memo.md) · [original .docx](docs/Memo%20-%20Massachusetts%20Homelessness.docx)

## What the analysis establishes

| Finding | Evidence |
|---|---|
| The pre-2023 period is flat, not slow-rising | Slope +0.04 per 10,000 per year (SE 0.17, p = 0.82, R² = 0.004) over 2007–2022 |
| 2024 is a genuine departure, not noise | Predicted 26.4 per 10,000, actual 41.1 — 4.7 residual SD above trend, ≈10,500 people |
| The break is 2024, not 2023 | 2023 (27.1) falls inside the 95% prediction band; 2024 and 2025 fall outside |
| One trend does not fit the period | Chow test, F(2,15) = 8.53, p = 0.003 |
| The rise is families entering shelter | Families are 89.6% of the 2022–2024 increase; sheltered 96.4%; chronic individuals 3.1%; veterans 0.1% |
| It is not a general deterioration | Homelessness among individuals *fell*: −0.12 per 10,000 per year, p = 0.006 |

The memo is explicit about what this design cannot do. A 19-point single-state series
describes structure; it does not identify a cause. The 2024 break coincides with large
asylum-seeker arrivals meeting the state's shelter obligation, and the 2025 decline
follows tightened Emergency Assistance eligibility — but attributing the break to
either would need a comparison group and covariates this data does not have. A
right-to-shelter system also converts hidden homelessness into *counted* homelessness,
and PIT data cannot separate enrolment from new hardship.

## Running it

```bash
Rscript src/build_data.R   # raw PIT counts + Census population -> analysis file
Rscript src/analysis.R     # every statistic quoted in the memo
Rscript src/figure.R       # the figure
```

Requires `readr`, `dplyr` and `ggplot2`. Run from the repository root.

`src/analysis.R` prints the headline change, the decomposition of the 2022–2024
increase, the pre-break trend with its out-of-sample predictions, the Chow test and
the counterpoint series — in that order, each labelled. Running it is how you check
the memo rather than trust it.

```
data/   ma_pit_2007_2025.csv   HUD PIT counts, Massachusetts, 19 state-years
        ma_pop.csv             Census population estimates (rate denominators)
        ma_homelessness_analysis.csv   the joined, rate-adjusted file
src/    build_data.R, analysis.R, figure.R
docs/   the memo
output/ the figure
```

## Data

HUD Point-in-Time counts from the 2025 Annual Homelessness Assessment Report, Part 1
([huduser.gov](https://www.huduser.gov/portal/datasets/ahar.html)). The unit of
observation is a state-year: one count on one January night, broken down by shelter
status, household type, chronicity and veteran status.

Denominators are U.S. Census Bureau state population totals, which splice three
vintages (2000–2010 intercensal, Vintage 2020, Vintage 2025). That introduces small
discontinuities at the 2010 and 2020 boundaries — noted in the memo rather than
smoothed away.

## Context

Written for **API-232: Computational Policy Analysis**, Harvard Kennedy School,
Fall 2026.
