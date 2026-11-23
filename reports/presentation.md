# Discover Hungary – Tourism Intelligence
## Presentation source (12 slides)

### Slide 1 — Hungary Tourism Analytics
Trends, regional differences, seasonality and predictive modelling.  
**Evidence status:** provider observations and computed model outputs are available locally.

### Slide 2 — Why study tourism?
Official monthly accommodation statistics can describe demand and its
distribution. Economic association is not the same as causal impact.

### Slide 3 — Research questions
How did tourism nights change? How do regions and visitor categories compare?
What seasonal patterns exist? Can chronological forecasts beat a baseline?

### Slide 4 — Official sources
Eurostat monthly national tourism; KSH county and regional tables; World Bank
annual indicators; ECB daily HUF/EUR rates. The exact inventory is in
`data/source_inventory.csv`.

### Slide 5 — Reproducible data pipeline
Official API response → unchanged raw file → normalized processed table →
quality checks → analysis, models, figures and dashboard.

### Slide 6 — Tourism trends
Eurostat has 141 monthly domestic-country observations for 2015-01 through
2026-09. Total selected-series demand reached 132.7 million nights. Partial
2026 observations and category changes are not comparable to a complete-year
estimate.

### Slide 7 — Regional differences
The KSH data provide county, region and large-region observations from 2021
through 2026-09. They are reported as source observations, not ranked or mapped;
KSH geographic units must not be summed with Eurostat national observations.

### Slide 8 — Seasonality
Across the domestic monthly series, average demand peaks in August
(approximately 1.72 million nights) and July (1.62 million), using the full
selected observation window rather than complete-calendar-year totals only.

### Slide 9 — Statistical analysis
Eleven annual observations align tourism totals with World Bank indicators.
Pearson correlations range from -0.12 to 0.24; the 11-observation multiple
model has R-squared 0.338 but a 3.195-million predictor condition number.
These are descriptive associations, not causal evidence.

### Slide 10 — Predictive modelling
The 26-month chronological holdout is 2024-08 through 2026-09. Seasonal naive
was best on MAE (108,174), RMSE (123,191) and R-squared (0.947); random forest
was close on MAE (111,227). This is holdout evidence, not future accuracy.

### Slide 11 — Dashboard
The Streamlit dashboard reads processed data, supports independent year/month
filters and labels unavailable evidence explicitly. It does not rank counties
or draw unsupported regional maps.

### Slide 12 — Findings and next step
Seasonal demand is most visible in summer. Economic associations are weak and
unstable across a small sample. No regional ranking or causal claim is supported.
