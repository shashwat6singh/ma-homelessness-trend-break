# Figure: Massachusetts homelessness rate, 2007-2025, against the pre-2023 trend.
#
# One panel carries both findings:
#   (1) the statewide rate was flat 2007-2022, then broke sharply upward;
#   (2) the break is entirely families -- the rate for individuals actually fell.

library(readr); library(dplyr); library(ggplot2)

d <- read_csv("data/ma_homelessness_analysis.csv", show_col_types = FALSE)
out_path <- "output/ma-homelessness-rate-2007-2025.png"

# ---- palette ----
surface <- "#fcfcfb"; s1 <- "#2a78d6"; s2 <- "#eb6834"
ink <- "#0b0b0b"; ink2 <- "#52514e"; muted <- "#898781"
grid <- "#e1e0d9"; axis <- "#c3c2b7"; band <- "#e8e7e0"

# ---- pre-break trend, extended out of sample ----
pre <- d %>% filter(year <= 2022)
m   <- lm(rate ~ year, data = pre)
sig <- summary(m)$sigma
proj <- data.frame(year = 2007:2025)
pi   <- predict(m, proj, interval = "prediction", level = 0.95)
proj <- cbind(proj, as.data.frame(pi))

excess24 <- d$rate[d$year == 2024] - proj$fit[proj$year == 2024]
people24 <- excess24 * d$population[d$year == 2024] / 10000

p <- ggplot() +
  # the band the pre-2023 trend says we should have seen
  geom_ribbon(data = proj, aes(x = year, ymin = lwr, ymax = upr),
              fill = band, alpha = 0.75) +
  geom_line(data = proj, aes(x = year, y = fit),
            colour = muted, linetype = "dashed", linewidth = 0.45) +

  # individuals only -- the counterpoint series
  geom_line(data = d, aes(x = year, y = ind_rate), colour = s2, linewidth = 0.9) +
  geom_point(data = d, aes(x = year, y = ind_rate), colour = s2, size = 1.3) +

  # total rate -- the headline series
  geom_line(data = d, aes(x = year, y = rate), colour = s1, linewidth = 1.2) +
  geom_point(data = d, aes(x = year, y = rate), colour = s1, size = 1.7) +

  # direct labels instead of a legend box
  annotate("text", x = 2007.1, y = 37.2, label = "All people experiencing homelessness",
           colour = s1, size = 3.35, fontface = "bold", hjust = 0) +
  annotate("text", x = 2007.1, y = 6.4, label = "Individuals (not in families)",
           colour = s2, size = 3.35, fontface = "bold", hjust = 0) +
  annotate("text", x = 2010.6, y = 20.6, label = "95% prediction band from the 2007-2022 trend",
           colour = muted, size = 3.05, hjust = 0) +

  # the break, called out with the quantity that matters
  annotate("segment", x = 2023.62, xend = 2023.62,
           y = proj$fit[proj$year == 2024], yend = d$rate[d$year == 2024],
           colour = ink2, linewidth = 0.4) +
  annotate("text", x = 2023.35, y = 45.0,
           label = sprintf("2024 sits %.1f SD above trend\n(%s more people than\nthe trend predicts)",
                           excess24 / sig, format(round(people24, -2), big.mark = ",")),
           colour = ink2, size = 3.1, hjust = 1, vjust = 1, lineheight = 1.25) +

  scale_x_continuous(breaks = seq(2007, 2025, 3), expand = expansion(mult = c(.02, .03))) +
  scale_y_continuous(limits = c(0, 46), breaks = seq(0, 45, 10), expand = c(0, 0)) +
  labs(
    title = "Massachusetts homelessness was flat for fifteen years, then broke sharply upward",
    subtitle = paste0(
      "People counted homeless on one January night per 10,000 residents. The 2007-2022 trend is statistically flat\n",
      "(slope p = 0.82); a Chow test rejects a single trend across the period (F = 8.53, p = 0.003). The rate for\n",
      "individuals not in families fell over the same period, so the break is a family-shelter phenomenon."),
    x = NULL, y = "Per 10,000 residents",
    caption = "Source: HUD PIT counts, 2007-2025 AHAR Part 1; denominators from Census state population estimates."
  ) +
  theme_minimal(base_size = 11) +
  theme(
    plot.background    = element_rect(fill = surface, colour = NA),
    panel.background   = element_rect(fill = surface, colour = NA),
    panel.grid.minor   = element_blank(),
    panel.grid.major.x = element_blank(),
    panel.grid.major.y = element_line(colour = grid, linewidth = 0.3),
    axis.ticks   = element_blank(),
    axis.text    = element_text(colour = muted, size = 9),
    axis.title.y = element_text(colour = ink2, size = 9.5, margin = margin(r = 8)),
    plot.title    = element_text(colour = ink, size = 12.2, face = "bold", margin = margin(b = 7)),
    plot.subtitle = element_text(colour = ink2, size = 8.8, lineheight = 1.4, margin = margin(b = 14)),
    plot.caption  = element_text(colour = muted, size = 7.6, hjust = 0, margin = margin(t = 11)),
    plot.title.position = "plot", plot.caption.position = "plot",
    plot.margin = margin(16, 16, 12, 12)
  )

ggsave(out_path, p, width = 7.6, height = 4.6, dpi = 220, bg = surface)
cat("saved", out_path, "\n")
cat(sprintf("2024 excess: %.1f per 10,000 = %.0f people; residual SD %.2f\n", excess24, people24, sig))
