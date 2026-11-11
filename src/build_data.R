# Builds data/ma_homelessness_analysis.csv from the two raw extracts.
#
#   data/ma_pit_2007_2025.csv  HUD Point-in-Time counts for Massachusetts,
#                              one row per year, from AHAR Part 1.
#   data/ma_pop.csv            Census state population estimates, the rate
#                              denominators.
#
# Rates are per 10,000 residents. Run this before analysis.R or figure.R if you
# want to rebuild the analysis file rather than use the committed one.
#
# Run:  Rscript src/build_data.R

suppressPackageStartupMessages({ library(readr); library(dplyr) })

pit <- read_csv("data/ma_pit_2007_2025.csv", show_col_types = FALSE)
pop <- read_csv("data/ma_pop.csv", show_col_types = FALSE)

out <- pit %>%
  inner_join(pop, by = "year") %>%
  mutate(
    rate     = 10000 * total       / population,
    fam_rate = 10000 * in_families / population,
    ind_rate = 10000 * individuals / population,
  ) %>%
  arrange(year)

stopifnot(nrow(out) == 19, !any(is.na(out$rate)))
write_csv(out, "data/ma_homelessness_analysis.csv")
cat("wrote data/ma_homelessness_analysis.csv:", nrow(out), "state-years\n")
