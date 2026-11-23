# Hungary Tourism Analytics
## Trends, regional differences, seasonality and predictive modelling

**University Data Analysis project**  
**Status:** Processed empirical results available locally
**Prepared:** 23 November 2026

## Abstract

This project implements a reproducible workflow for analysing Hungarian
tourism using official statistical sources. The processed evidence includes
141 monthly domestic Eurostat observations, KSH county/regional observations,
annual World Bank indicators and a chronological tourism-demand holdout.
The exact Eurostat domestic series is used for trend and model results.

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
The source inventory records exact series codes, provider payload coverage,
retrieval URLs and licenses. Provider revisions should be checked before
future analyses are updated.

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

The selected exact Eurostat series contains 141 monthly domestic-country
observations from 2015-01 through 2026-09, with 132,738,487 nights in total.
The period includes 2026 observations that may be incomplete; it is not treated
as a complete annual year. Annual aggregation rises from 9,974,972 nights in
2015 to 12,669,186 in 2025, with a 2020 low of 7,876,805. Average monthly
demand peaks in August and July. KSH processed observations cover 2021-01
through 2026-09 at county and regional geographic levels; these figures are
provider observations and are not ranked or mapped.

Eleven annual tourism observations align with the World Bank indicators.
Simple Pearson correlations are 0.050 for CPI inflation, 0.212 for real GDP
growth, 0.240 for GDP per capita and -0.122 for population. A multiple linear
model has R-squared 0.338, but 11 observations and a predictor condition number
of 3.195 million show why coefficients are unsuitable for causal or stable
out-of-sample interpretation.

## 6. Models

The chronological holdout is 26 months. The seasonal-naive baseline has
MAE 108,174, RMSE 123,191 and R-squared 0.947. The random forest has
MAE 111,227, RMSE 149,037 and R-squared 0.923. The linear regression has
MAE 240,465, RMSE 318,313 and R-squared 0.647. At the training-median threshold
of 1,801,215 nights, logistic regression achieves accuracy 0.923 and F1 0.955;
the shallow decision tree achieves accuracy 0.846 and F1 0.909. Metrics describe
the computed holdout only and are not forecasts of future accuracy.

## 7. Visualizations and dashboard

The analysis pipeline creates monthly trend, seasonality, raincloud, correlation,
regression and prediction figures from processed observations. The Streamlit
dashboard applies year and month filters independently, keeps source dimensions
explicit and reports unavailable sections separately. Its geography view
displays processed KSH records; it does not rank counties or create a regional
map without a documented geographic join.

## 8. Discussion

The principal empirical limitations are the short annual economic sample,
changing or partial source coverage, structural breaks including 2020 and the
incomplete 2026 observations. Eurostat national and KSH geographic observations
use different definitions and must not be summed or directly compared. Monthly
forecast error may depend on the chosen series, changing category codes and
structural tourism shocks. Associations do not establish economic causality.

## 9. Conclusion

The repository provides a reproducible collection and cleaning pipeline,
empirical processed datasets, a chronological model comparison, a dashboard,
and evidence-backed report templates. Summer demand is visibly higher in the
selected series. Annual economic associations are weak, and stable causal
inference is unsupported. No county ranking or regional map is inferred.

## References

- Eurostat, Tourism database and dissemination API: links recorded in
  `data/source_inventory.csv`.
- Hungarian Central Statistical Office, STADAT tourism tables 0079 and 0080:
  links recorded in `data/source_inventory.csv`.
- World Bank, World Development Indicators API: links recorded in
  `data/source_inventory.csv`.
- European Central Bank, Exchange Rates data: links recorded in
  `data/source_inventory.csv`.

**Retrieval date/status:** 23 November 2026; provider observations are
available in the local processed data. Re-run the collection pipeline for
provider revisions or newly released observations.
