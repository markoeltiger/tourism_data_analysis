"""Streamlit dashboard for processed Hungary tourism data."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from src.dashboard_filters import filter_month_year, prepare_month_year
from src.tourism_figures import (
    plot_annual_correlation,
    plot_monthly_seasonality,
    plot_monthly_trend,
    plot_regional_values,
)

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


st.set_page_config(page_title="Discover Hungary", page_icon="🇭🇺", layout="wide")
st.title("Discover Hungary – Tourism Intelligence Dashboard")
st.caption(
    "Official-source observations from data/processed. "
    "No unavailable values, county rankings, or regional maps are invented."
)

tourism_path = PROCESSED / "tour_occ_nim.csv"
if not tourism_path.exists():
    st.warning("Processed Eurostat tourism data is unavailable.")
    st.info("Run `python3 -m src.run_pipeline --skip-download` after provider files exist.")
    st.stop()

tourism = prepare_month_year(pd.read_csv(tourism_path))
if tourism.empty:
    st.error("The processed tourism file contains no usable observations.")
    st.stop()

st.sidebar.header("Eurostat monthly series")
dimension_choices: dict[str, list[str]] = {}
for column in ("freq", "c_resid", "unit", "nace_r2", "geo"):
    if column in tourism:
        choices = sorted(tourism[column].dropna().astype(str).unique())
        preferred = {
            "freq": "M",
            "c_resid": "TOTAL",
            "unit": "NR",
            "nace_r2": "I551",
            "geo": "HU",
        }.get(column)
        default = preferred if preferred in choices else choices[0]
        dimension_choices[column] = st.sidebar.selectbox(
            column,
            choices,
            index=choices.index(default),
        )

filtered = tourism.copy()
for column, selected in dimension_choices.items():
    filtered = filtered.loc[filtered[column].astype(str) == selected]

st.sidebar.header("Time filters")
available_years = sorted(filtered["year"].dropna().unique().tolist())
available_months = sorted(filtered["month"].dropna().unique().tolist())
selected_years = st.sidebar.multiselect(
    "Year",
    available_years,
    default=available_years,
)
selected_months = st.sidebar.multiselect(
    "Month",
    available_months,
    default=available_months,
    format_func=lambda month: pd.Timestamp(2024, month, 1).strftime("%B"),
)
filtered = filter_month_year(filtered, selected_years, selected_months)

tab_overview, tab_seasonality, tab_geography, tab_economy, tab_prediction = st.tabs(
    ["Overview", "Seasonality", "Geography", "Economy", "Prediction"]
)

with tab_overview:
    source_codes = ", ".join(
        f"{column}={value}" for column, value in dimension_choices.items()
    )
    st.caption(
        f"Source: Eurostat tour_occ_nim ({source_codes}); unit NR is a count of nights."
    )
    first, second, third = st.columns(3)
    first.metric("Observed nights", f"{filtered['value'].sum():,.0f}")
    second.metric("Months in view", f"{filtered['period'].nunique():,}")
    third.metric(
        "Coverage",
        (
            f"{filtered['year'].min():.0f}–{filtered['year'].max():.0f}"
            if not filtered.empty
            else "No selection"
        ),
    )
    if filtered.empty:
        st.warning("No observations match both the dimension choices and time filters.")
    elif filtered.duplicated(["period"]).any():
        st.warning("The remaining dimensions do not define one unique observation per month.")
    else:
        fig = plot_monthly_trend(
            filtered,
            title="Monthly tourism nights in Hungary — selected Eurostat series",
            ylabel="Nights spent (number)",
        )
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    st.dataframe(filtered, use_container_width=True)

with tab_seasonality:
    st.caption(
        "Source: Eurostat tour_occ_nim using the selected categories and observed "
        "monthly nights; missing values are not imputed."
    )
    if filtered.empty:
        st.info("Choose at least one year and month.")
    elif filtered.duplicated(["period"]).any():
        st.info("Select one exact provider category before comparing monthly seasonality.")
    else:
        fig = plot_monthly_seasonality(
            filtered,
            title="Seasonality in observed Hungarian tourism nights",
            ylabel="Nights spent (number)",
        )
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

with tab_geography:
    ksh_path = PROCESSED / "ksh_tourism_monthly.csv"
    if not ksh_path.exists():
        st.info("KSH county and regional observations are unavailable.")
    else:
        ksh = pd.read_csv(ksh_path)
        ksh["period"] = pd.to_datetime(ksh["period"], errors="coerce")
        ksh = ksh.dropna(subset=["period", "value"])
        dataset_options = sorted(ksh["dataset"].dropna().astype(str).unique())
        dataset = st.selectbox("KSH source table", dataset_options)
        geo_level = st.selectbox(
            "Geographic level",
            sorted(ksh.loc[ksh["dataset"] == dataset, "geo_level"].dropna().unique()),
        )
        accommodation = st.selectbox(
            "Accommodation type",
            sorted(
                ksh.loc[
                    (ksh["dataset"] == dataset) & (ksh["geo_level"] == geo_level),
                    "accommodation_type",
                ].dropna().unique()
            ),
        )
        periods = sorted(
            ksh.loc[
                (ksh["dataset"] == dataset)
                & (ksh["geo_level"] == geo_level)
                & (ksh["accommodation_type"] == accommodation),
                "period",
            ].dropna().unique()
        )
        period = st.selectbox(
            "Observation month",
            periods,
            index=len(periods) - 1,
            format_func=lambda value: pd.Timestamp(value).strftime("%B %Y"),
        )
        ksh = ksh.loc[
            (ksh["dataset"] == dataset)
            & (ksh["geo_level"] == geo_level)
            & (ksh["accommodation_type"] == accommodation)
            & (ksh["period"] == period)
        ]
        st.caption(
            f"KSH {dataset}; source observations for {pd.Timestamp(period):%B %Y}. "
            "Geographies are shown in source-name order, not ranked. "
            "Eurostat national and KSH geographic observations must not be summed "
            "or directly compared."
        )
        if not ksh.empty:
            fig = plot_regional_values(
                ksh,
                title=f"KSH tourism nights by {geo_level} — {pd.Timestamp(period):%B %Y}",
            )
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        st.dataframe(ksh.sort_values(["period", "geo"]), use_container_width=True)

with tab_economy:
    annual_path = PROCESSED / "annual_tourism_economy.csv"
    correlations_path = PROCESSED / "economic_correlations.csv"
    regression_path = PROCESSED / "economic_regression_results.json"
    if not annual_path.exists():
        st.info("Annual tourism-economic results are unavailable.")
    else:
        annual = pd.read_csv(annual_path)
        st.line_chart(
            annual.set_index("year")[["tourism_nights"]],
            use_container_width=True,
            y_label="Annual tourism nights",
        )
        st.dataframe(annual, use_container_width=True)
    if correlations_path.exists():
        st.subheader("Pearson correlations")
        correlations = pd.read_csv(correlations_path, index_col=0)
        correlation_figure = plot_annual_correlation(
            annual if annual_path.exists() else pd.DataFrame()
        )
        if correlation_figure is None:
            st.info("No compatible annual tourism-economic correlations are available.")
        else:
            st.pyplot(correlation_figure, use_container_width=True)
            plt.close(correlation_figure)
            st.caption(
                "Source: matched annual Eurostat tourism nights and World Bank "
                f"Hungary indicators, {int(annual['year'].min())}–"
                f"{int(annual['year'].max())} (n={len(annual)}). Descriptive "
                "correlations are not causal evidence."
            )
        st.dataframe(correlations, use_container_width=True)
    if regression_path.exists():
        st.subheader("Regression diagnostics")
        st.json(json.loads(regression_path.read_text(encoding="utf-8")))
    st.caption("Correlations and regressions are descriptive associations, not causal effects.")

with tab_prediction:
    predictions_path = PROCESSED / "model_predictions.csv"
    metrics_path = PROCESSED / "model_metrics.json"
    if not predictions_path.exists() or not metrics_path.exists():
        st.info("Chronological prediction results are unavailable.")
    else:
        predictions = pd.read_csv(predictions_path, parse_dates=["period"])
        st.line_chart(
            predictions.set_index("period")[["actual", "seasonal_naive", "random_forest"]],
            use_container_width=True,
            y_label="Nights (provider unit)",
        )
        st.dataframe(predictions, use_container_width=True)
        st.subheader("Holdout metrics")
        st.json(json.loads(metrics_path.read_text(encoding="utf-8")))
