# Hungary Tourism Analytics

**Discover Hungary – Tourism Intelligence Dashboard**

This university project is designed to study tourism trends, seasonality,
regional differences and the relationship between tourism and economic
indicators using official Hungarian and European statistics.

> **Data and results status (2026-11-23):** This run could not access the
> external data providers because outbound network requests were denied by the
> execution environment. No raw datasets were acquired, and therefore no
> descriptive findings, charts, regression results or forecasts are reported.
> The source inventory, acquisition code, analysis, dashboard and deliverable
> templates are in place for a reproducible run when source access is available.
> Seaborn, Scikit-learn and Jupyter are also absent from the current runtime;
> install `requirements.txt` before running the full sourced analysis and
> notebooks.

## Research questions

1. How have overnight stays in Hungary changed over time?
2. How do tourism volumes differ by Hungarian region and, where definitions
   permit, domestic versus international visitor residence?
3. What monthly seasonal patterns are present?
4. How are tourism measures associated with annual economic indicators?
5. Can a chronological holdout model improve on a seasonal-naive baseline?

## Data sources

The official source candidates, API patterns, geography, frequency, variables
and retrieval status are recorded in [`data/source_inventory.csv`](data/source_inventory.csv).
The planned inputs are Eurostat monthly accommodation nights at national and
NUTS 2 levels, World Bank Hungary GDP/inflation/population indicators, KSH
county tables and ECB HUF/EUR reference exchange rates. KSH and ECB are not
currently downloaded by the automated pipeline; their exact file/query
semantics must be verified before analysis. All source URLs and license notes
must remain alongside any derived outputs.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Run the pipeline

With network access:

```bash
python -m src.run_pipeline
```

This saves original provider responses under `data/raw/`, parses them into
`data/processed/`, computes descriptive summaries, creates figures, and runs a
chronological demand-model comparison when the downloaded observations support
one. Raw files are never edited in place. The pipeline surfaces HTTP, parsing,
and data ambiguity errors rather than silently filling missing values.

For already downloaded raw responses:

```bash
python -m src.run_pipeline --skip-download
```

The Eurostat source has dimensions that may create multiple series. Before
modelling, select one exact code for every non-time dimension using
`make_monthly_series(..., category_filters={...})`. The code intentionally
refuses to merge incompatible categories or aggregate duplicate months
implicitly. Annual World Bank indicators are kept separate from monthly
tourism; do not infer monthly economic data from annual values.

## Dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard uses processed files only. It displays an explicit unavailable
state until a usable tourism dataset exists. Totals are shown only for one
selected monthly series and not as an unsafe sum across categories.

## Notebooks and deliverables

Run notebooks `01` through `06` in order after installing the requirements.
`reports/project_report.md` and `reports/presentation.md` are the editable
source text; the corresponding PDFs are generated with:

```bash
python -m src.generate_deliverables
```

Figures are created in `figures/`. They and raw/processed data are excluded from
version control by default. Keep approved public datasets local unless their
license and size justify redistribution.

## Methods and limitations

The intended analysis includes descriptive statistics, year-over-year
changes, seasonality and regional comparisons; correlation and regression are
only performed on aligned series with documented definitions. Prediction uses
a chronological split, a seasonal-naive baseline and a random forest;
logistic regression and a shallow decision tree classify high-demand months
using the training-period median. Predictive performance is not causal
evidence. The small annual economic series, structural breaks, changing
statistical definitions, coverage and missing observations limit inference.

At present, no empirical conclusion or model score is available. The project
does not claim that a source was verified or fetched until the pipeline
successfully retrieves and parses its original provider payload.
