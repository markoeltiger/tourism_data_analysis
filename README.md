# Hungary Tourism Analytics

**Discover Hungary – Tourism Intelligence Dashboard**

This university project is designed to study tourism trends, seasonality,
regional differences and the relationship between tourism and economic
indicators using official Hungarian and European statistics.

> **Data status (2026-11-23):** The configured Eurostat, World Bank, KSH and
> ECB endpoints returned valid provider payloads. Retrieved originals and their
> SHA-256 manifest are stored locally under `data/raw/` and are excluded from
> version control. The source inventory records the exact queries, observed
> coverage and licensing notes.

## Research questions

1. How have overnight stays in Hungary changed over time?
2. How do tourism volumes differ by Hungarian region and, where definitions
   permit, domestic versus international visitor residence?
3. What monthly seasonal patterns are present?
4. How are tourism measures associated with annual economic indicators?
5. Can a chronological holdout model improve on a seasonal-naive baseline?

## Data sources

The exact source and download URLs, geographic scope, frequency, variables,
observed coverage and licensing notes are recorded in
[`data/source_inventory.csv`](data/source_inventory.csv). The inputs include
Eurostat monthly national nights and an annual dataset labelled by Eurostat as
NUTS 3, World Bank Hungary indicators, KSH county/region monthly tables, and
daily ECB HUF/EUR reference rates. KSH CSV exports and ECB SDMX CSV are
downloaded automatically alongside the Eurostat and World Bank API responses.

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

This saves byte-for-byte provider responses under `data/raw/`, writes a local
`SHA256SUMS.txt` manifest, parses them into `data/processed/`, computes
descriptive summaries, creates figures, and runs a chronological demand-model
comparison when the downloaded observations support one. The pipeline
surfaces HTTP, parsing, and data ambiguity errors rather than silently filling
missing values.

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

The dashboard uses processed files only. It provides independent year and month
filters, exact Eurostat category selectors, a KSH source-observation table,
annual economic association views and chronological prediction outputs.
Dashboard totals are never unsafe sums across Eurostat categories. KSH county
and regional observations are displayed without invented rankings or maps.

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

## Observed model results

For the exact Eurostat series `freq=M`, `c_resid=TOTAL`, `unit=NR`,
`nace_r2=I551`, and `geo=HU`, the chronological holdout contains 26 months.
The seasonal-naive model had MAE 108,174, RMSE 123,191 and R-squared 0.947;
the random forest had MAE 111,227, RMSE 149,037 and R-squared 0.923. These
values are in-provider-unit nights and are not evidence of future accuracy.
The logistic regression classified the training-median threshold with accuracy
0.923 and F1 0.955; the shallow decision tree achieved accuracy 0.846 and F1
0.909.

The 11 matched annual observations yield positive simple correlations for the
tested economic indicators, but simple R-squared values range from 0.0025 to
0.058 and the fitted four-predictor model has a high condition number
(3.195 million). It is therefore descriptive only and not suitable for causal
or stable out-of-sample inference.

Eurostat national observations and KSH county/region observations are not
equivalent geographic series and must not be summed or directly compared.
The pipeline reports unavailable or not-run states when dimensions remain
ambiguous or the sample is too small.
