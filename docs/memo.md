# MEMORANDUM

**To:** Governor of Massachusetts
**From:** Shashwat Singh
**Date:** September 16, 2026
**Re:** Homelessness in Massachusetts, 2007–2025 — a level break, not a rising trend

---

## Question and why it matters

Has homelessness in Massachusetts risen steadily over the past two decades, or did
something discrete happen recently? The distinction carries different policy
responses. A gradual rise tracking housing costs points to supply and subsidy
instruments. A sudden level shift in a state with a statutory right to shelter for
families points instead to intake capacity, eligibility rules and surge financing.
Massachusetts is one of only three U.S. jurisdictions guaranteeing shelter, so the
question is live rather than academic.

## Data and unit of observation

US Department of Housing & Urban Development (HUD) Point-in-Time (PIT) counts,
published in the 2025 Annual Homelessness Assessment Report, Part 1 (huduser.gov).
The unit of observation is a state-year: a single count of people experiencing
homelessness on one night each January. That yields 19 annual observations for
Massachusetts, 2007–2025, each broken down by shelter status (sheltered /
unsheltered), household type (in families / individuals), chronicity and veteran
status. Rates use Census Bureau state population estimates as denominators.

## Analysis

The count rose from 15,127 in 2007 to 28,311 in 2025 — up 87%, or 68% per capita
(23.5 to 39.6 per 10,000 residents). That headline conceals the structure. Across
2007–2022 the rate averaged 26.1 per 10,000 (standard deviation 3.0, range
21.6–31.4) with no direction at all. Almost the entire increase arrives in two
years: the count rose 89% from 2022 to 2024 (15,507 to 29,360), then eased to
28,311 in 2025. The increase of 13,853 people decomposes as:

| Component | Change, 2022–2024 | Share of the increase |
|---|---:|---:|
| People in families | +12,418 | 89.6% |
| Sheltered | +13,353 | 96.4% |
| Chronically homeless individuals | +426 | 3.1% |
| Veterans | +16 | 0.1% |

Two further facts sharpen this. Homelessness among individuals not in families fell
over the full period, from 12.9 to 10.6 per 10,000, a statistically significant
decline (−0.12 per 10,000 per year, p = 0.006). Massachusetts remains almost
entirely sheltered: 6.2% of its 2025 count was unsheltered against 35.7%
nationally, the second-lowest share among 54 states and territories, behind only
New York. Both states are large right-to-shelter jurisdictions.

## Testing trend against break

Because the question is precisely whether the series follows a trend or shifts
level, I fit a linear trend to 2007–2022 only (n = 16) and tested the later years
against it. This is a description of the series' structure, not a causal model, and
it is reported as such.

The pre-2023 slope is +0.04 per 10,000 per year (SE 0.17; p = 0.82; R² = 0.004):
year explains essentially none of the variation, so the earlier period is flat
rather than merely slow-rising. Extrapolating that trend predicts 26.4 per 10,000
for 2024. The actual value is 41.1 — outside the interval, 4.7 residual standard
deviations above the prediction, about 10,500 more people than the trend implies. A
Chow test rejects a single trend across the period (F(2,15) = 8.53, p = 0.003).
Note that 2023 itself (27.1) falls inside the band: the break is 2024, not 2023.

![Massachusetts homelessness rate, 2007–2025](../output/ma-homelessness-rate-2007-2025.png)

## Interpretation

**Supported by these data.** Massachusetts had no detectable upward trend in
homelessness from 2007 to 2022, so the common framing that homelessness has been
rising for a decade does not fit this state. The increase is a discrete level shift
in 2024, distinguishable from trend at conventional significance. Families are
overwhelmingly entering shelter, while chronic and individual homelessness were
close to unaffected.

**Not established by the data.** The cause of the increase is unexplained. The
timing coincides with large asylum-seeker arrivals meeting the state's
right-to-shelter obligation, and the 2025 decline follows tightened Emergency
Assistance eligibility. However, a single-state series of 19 points cannot
attribute the break to either. Doing so would require a comparison group (other
states, or the other right-to-shelter jurisdictions) and covariates for housing
costs, mortgage rates and labour markets. Separately, a right-to-shelter system
converts hidden homelessness into counted and sheltered homelessness, so part of
the measured rise may reflect enrolment in a system rather than new hardship. The
HUD PIT data cannot separate the two.

**Measurement limits.** PIT data captures one January night and so misses episodic
homelessness across the year (AHAR Part 2 annual counts would be needed).
Unsheltered figures rest on street canvasses with a known undercount, so
year-to-year movements in that series are the least reliable component. Population
denominators splice three Census vintages (2000–2010 intercensal, Vintage 2020,
Vintage 2025), introducing small discontinuities at the 2010 and 2020 boundaries.

---

**Sources.** HUD, 2025 AHAR Part 1, PIT Counts by State 2007–2025
(huduser.gov/portal/datasets/ahar). U.S. Census Bureau, State Population Totals
(NST-EST2025, nst-est2020, st-est00int). Analysis in R; scripts and the extracted
Massachusetts series accompany this memo.
