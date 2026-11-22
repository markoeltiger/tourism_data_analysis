# Hungary Tourism Analytics
## Trends, regional differences, seasonality and predictive modelling

**University Data Analysis project**  
**Status:** Source acquisition and empirical analysis unavailable in this run  
**Prepared:** 23 November 2026

## Abstract

This project establishes a reproducible workflow for analysing Hungarian
tourism using official statistical sources. The intended scope includes monthly
overnight stays, regional comparisons, seasonal patterns, economic indicators
and chronological demand prediction. External source access was denied during
this run, so no observations were downloaded. Consequently, this report
contains no empirical estimates, charts or model results; it documents the
research design and the exact boundary between implemented code and
unavailable evidence.

## 1. Introduction

Tourism is a geographically and seasonally concentrated activity. Official
monthly accommodation statistics can support analysis of temporal and regional
patterns, while annual macroeconomic indicators provide a limited contextual
comparison. This study is designed to describe those patterns without
interpreting correlation as causation.

## 2. Objectives and research questions

The objectives are to describe changes in tourism nights, compare regions and
visitor categories when source definitions permit, measure seasonality,
examine associations with annual economic indicators and evaluate an
out-of-sample monthly forecast. Research questions are listed in the project
README.

## 3. Literature and source background

The dataset inventory identifies Eurostat monthly tourism tables, Hungarian
Central Statistical Office (KSH) county tables, World Bank Development
Indicators and the European Central Bank exchange-rate dataset. The provider
references and intended variables appear in `data/source_inventory.csv`.
Source access, current series codes, date coverage and licenses remain
unverified in this environment and must be checked against the providers
before interpreting results.

## 4. Data and methodology

The collection module stores provider responses unchanged in `data/raw/`.
Cleaning expands Eurostat JSON-stat dimensions and normalizes World Bank
indicator observations into separate processed tables. Missing provider values
are excluded from numerical summaries rather than imputed. Duplicate rows are
removed only in normalized tables; raw observations remain untouched.

Monthly tourism is not joined to annual economic variables as if both had the
same frequency. Regional, accommodation-type and residence dimensions must
match before comparison. Any model requires one explicitly selected monthly
series; ambiguous categories are rejected. The predictive holdout is
chronological. A seasonal-naive forecast is compared with a random forest;
high-demand logistic regression and a shallow decision tree are conditional on
sufficient observations. Annual regressions and statistical assumption checks
remain pending data availability and review of compatible variables.

## 5. Exploratory and statistical results

**Unavailable — no source observations were acquired.** No tourism totals,
growth rates, rankings, seasonal averages, correlations or regression
coefficients are reported. This omission is deliberate; values cannot be
calculated without authentic downloaded data.

## 6. Models

**Unavailable — no training or test series exists in the workspace.** Model
scores, feature importance and predicted values are not claimed. On successful
acquisition, the pipeline writes the holdout predictions and metrics; the
results must then be reviewed for data coverage, series breaks and baseline
comparability.

## 7. Visualizations and dashboard

The analysis code creates trend and monthly-distribution figures from
processed observations. The Streamlit dashboard reads only these processed
files and shows an explicit unavailable message when they are absent. No
data-backed chart is included in this edition.

## 8. Discussion

The current result is an implementation scaffold, not an empirical study. The
principal limitation is source-access failure, followed by unverified API
filters and KSH download details. Further limitations include mismatched
frequencies, evolving regional classifications, data revisions and the
inability of observational correlations to establish causal economic impact.
The current Python environment also lacks Seaborn, Scikit-learn and Jupyter,
which are declared in `requirements.txt` but could not be exercised here.

## 9. Conclusion

The repository now provides a modular collection and analysis workflow,
dashboard, source inventory, report and presentation templates. The substantive
research questions remain unanswered until provider data can be downloaded,
validated and analysed. No fabricated data or results have been substituted.

## References

- Eurostat, Tourism database and dissemination API: links recorded in
  `data/source_inventory.csv`.
- Hungarian Central Statistical Office, STADAT tourism tables 0079 and 0080:
  links recorded in `data/source_inventory.csv`.
- World Bank, World Development Indicators API: links recorded in
  `data/source_inventory.csv`.
- European Central Bank, Exchange Rates data: links recorded in
  `data/source_inventory.csv`.

**Retrieval date/status:** 23 November 2026; source access denied in the
execution environment. The references identify intended providers and do not
imply successful retrieval.
