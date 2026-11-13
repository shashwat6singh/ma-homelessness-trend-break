# Reproduces every statistic quoted in the memo.
#
# The memo's claim is structural: Massachusetts homelessness did not drift
# upward over two decades, it sat flat for fifteen years and then jumped. That
# claim rests on four pieces of evidence, computed here in order:
#
#   1. headline change, level and per capita, 2007-2025
#   2. where the 2022-2024 increase actually went (families? shelter? chronic?)
#   3. a trend fitted to 2007-2022 only, and how far 2024 sits outside it
#   4. a Chow test of one trend against two
#
# Run:  Rscript src/analysis.R
# Every number printed here appears in docs/Memo - Massachusetts Homelessness.docx.

suppressPackageStartupMessages({
  library(readr); library(dplyr)
})

d <- read_csv("data/ma_homelessness_analysis.csv", show_col_types = FALSE)

# Guards on the inputs. Every statistic below assumes a complete 19-year series
# with no missing rates, so the script fails here rather than reporting a
# number computed from a short or broken file.
stopifnot(
  nrow(d) == 19,
  all(d$year == 2007:2025),
  !any(is.na(d$rate)),
  !any(is.na(d$total)),
  all(d$total > 0)
)

# The break year is set BEFORE looking at the series, on institutional grounds:
# large asylum-seeker arrivals began reaching Massachusetts shelters in 2023.
# This matters for the Chow test below, whose conventional critical values
# assume the break date was not chosen by searching the data for the biggest
# jump. (The series in fact breaks in 2024, not 2023 - see section 3.)
BREAK <- 2023          # first year treated as post-break
say <- function(...) cat(sprintf(...), "\n", sep = "")

# ---- 1. headline ------------------------------------------------------------
a <- d[d$year == 2007, ]; z <- d[d$year == 2025, ]
say("1. HEADLINE 2007-2025")
say("   count      %d -> %d  (%+.0f%%)", a$total, z$total, 100 * (z$total / a$total - 1))
say("   per 10,000 %.1f -> %.1f  (%+.0f%%)", a$rate, z$rate, 100 * (z$rate / a$rate - 1))

pre <- d %>% filter(year <= 2022)
say("   2007-2022 rate: mean %.1f, SD %.1f, range %.1f-%.1f",
    mean(pre$rate), sd(pre$rate), min(pre$rate), max(pre$rate))

# ---- 2. decomposition of the 2022-2024 increase -----------------------------
# The memo's substantive point: the rise is families entering shelter, not a
# broad deterioration. Chronic and veteran homelessness barely move.
y22 <- d[d$year == 2022, ]; y24 <- d[d$year == 2024, ]
total_rise <- y24$total - y22$total

say("\n2. WHERE THE 2022-2024 INCREASE WENT  (total %+d, %+.0f%%)",
    total_rise, 100 * (y24$total / y22$total - 1))
for (comp in c("in_families", "sheltered", "chronic_indiv", "veterans")) {
  delta <- y24[[comp]] - y22[[comp]]
  say("   %-14s %+6d   %5.1f%% of the increase", comp, delta, 100 * delta / total_rise)
}

# ---- 3. the pre-break trend, extended out of sample -------------------------
# Fitting only 2007-2022 and testing later years against it is the whole design:
# it asks whether the later years are a continuation or a departure.
m <- lm(rate ~ year, data = pre)
co <- summary(m)$coefficients
sigma <- summary(m)$sigma

say("\n3. TREND FITTED TO 2007-2022 ONLY  (n = %d)", nrow(pre))
say("   slope    %+.2f per 10,000 per year (SE %.2f, p = %.2f)", co[2, 1], co[2, 2], co[2, 4])
say("   R-squared %.3f   residual SD %.2f", summary(m)$r.squared, sigma)

pred <- predict(m, data.frame(year = c(2023, 2024, 2025)), interval = "prediction", level = 0.95)
for (i in seq_len(3)) {
  yr <- c(2023, 2024, 2025)[i]
  actual <- d$rate[d$year == yr]
  inside <- actual >= pred[i, "lwr"] && actual <= pred[i, "upr"]
  say("   %d: predicted %.1f [%.1f, %.1f], actual %.1f -> %s (%.1f residual SD)",
      yr, pred[i, "fit"], pred[i, "lwr"], pred[i, "upr"], actual,
      if (inside) "inside the band" else "OUTSIDE the band",
      (actual - pred[i, "fit"]) / sigma)
}
excess <- d$rate[d$year == 2024] - pred[2, "fit"]
say("   2024 excess = %.1f per 10,000 = about %s people",
    excess, format(round(excess * d$population[d$year == 2024] / 10000, -2), big.mark = ","))

# ---- 4. Chow test: one trend or two? ---------------------------------------
# Restricted = a single line through all 19 years. Unrestricted = separate
# intercept and slope either side of the break. F tests the two restrictions.
d$post <- as.integer(d$year >= BREAK)
restricted   <- lm(rate ~ year, data = d)
unrestricted <- lm(rate ~ year * post, data = d)

rss_r <- sum(resid(restricted)^2); rss_u <- sum(resid(unrestricted)^2)
k <- 2; df2 <- nrow(d) - 2 * k
F <- ((rss_r - rss_u) / k) / (rss_u / df2)
p <- pf(F, k, df2, lower.tail = FALSE)

say("\n4. CHOW TEST FOR A BREAK AT %d", BREAK)
say("   F(%d, %d) = %.2f, p = %.3f -> %s", k, df2, F, p,
    if (p < 0.05) "reject a single trend across the period" else "cannot reject a single trend")

# ---- 5. the counterpoint series --------------------------------------------
# Individuals not in families moved the other way over the full period. This is
# what rules out a general deterioration in housing hardship.
mi <- lm(ind_rate ~ year, data = d)
ci <- summary(mi)$coefficients
say("\n5. INDIVIDUALS NOT IN FAMILIES, 2007-2025")
say("   rate %.1f -> %.1f", a$ind_rate, z$ind_rate)
say("   slope %+.2f per 10,000 per year (p = %.3f)", ci[2, 1], ci[2, 4])

say("\n6. SHELTER STATUS, 2025")
say("   unsheltered share %.1f%% (national comparison in the memo: 35.7%%)",
    100 * z$unsheltered / z$total)

# ---- 7. provenance ----------------------------------------------------------
# Printed so a reader can tell which versions produced the numbers above.
say("\n7. ENVIRONMENT")
say("   %s", R.version.string)
for (pkg in c("readr", "dplyr")) {
  say("   %-6s %s", pkg, as.character(utils::packageVersion(pkg)))
}
say("   run at %s", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z"))
