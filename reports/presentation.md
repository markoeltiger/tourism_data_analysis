# Discover Hungary – Tourism Intelligence
## Presentation source (12 slides)

### Slide 1 — Hungary Tourism Analytics
Trends, regional differences, seasonality and predictive modelling.  
**Evidence status:** figures are generated from locally processed provider observations; unavailable or incompatible data are called out instead of replaced.

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
Compare published domestic and foreign monthly nights for Hungary. The
Eurostat series, units and accommodation category are identified with the
figure; partial years are not presented as complete-year totals.

### Slide 7 — Regional differences
KSH tables provide county and regional tourism-night dimensions when
processed inputs are available. The source does not state reuse terms, so its
regional figure is omitted from this distributed presentation until
redistribution is confirmed.

### Slide 8 — Seasonality
Monthly distributions show the observed seasonality in domestic and foreign
tourism nights. Missing observations are not imputed.

### Slide 9 — Statistical analysis
The heatmap uses only matched annual Hungary tourism and World Bank
observations. Correlations are descriptive associations and do not establish
causation; the chart note reports the matched years and sample size.

### Slide 10 — Predictive modelling
Prediction results use a chronological holdout and compare learned models
against a seasonal-naive baseline. Holdout metrics are not evidence of future
accuracy.

### Slide 11 — Dashboard
The Streamlit dashboard uses the same Seaborn trend, seasonality, regional and
correlation plotting functions as the presentation. It reads processed data
and labels unavailable evidence explicitly.

### Slide 12 — Findings and next step
Refresh the official-source pipeline to update figures and matched annual
results. Regional comparisons remain at one compatible geographic level, and
economic associations are not causal claims.
