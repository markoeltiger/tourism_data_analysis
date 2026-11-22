"""Streamlit interface for downloaded and processed Hungary tourism data."""

from pathlib import Path
import json

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

st.set_page_config(page_title="Discover Hungary", page_icon="🇭🇺", layout="wide")
st.title("Discover Hungary – Tourism Intelligence Dashboard")
st.caption("Evidence-based analysis from official statistical sources; no estimated values are substituted for missing data.")

datasets = sorted(PROCESSED.glob("*.csv"))
tourism_path = PROCESSED / "tour_occ_nim.csv"
if not tourism_path.exists():
    st.warning(
        "Tourism data has not been downloaded and processed in this workspace. "
        "Run `python -m src.run_pipeline` after network access is available."
    )
    st.info("All charts and KPIs remain unavailable until official source observations are present.")
    st.stop()

data = pd.read_csv(tourism_path)
if data.empty or not {"period", "value"}.issubset(data.columns):
    st.error("The processed tourism file has no usable monthly observations.")
    st.stop()
data["period"] = pd.to_datetime(data["period"], errors="coerce")
data["value"] = pd.to_numeric(data["value"], errors="coerce")
data = data.dropna(subset=["period", "value"])

st.sidebar.header("Filters")
dimensions = [
    column for column in data.columns
    if column not in {"period", "value", "geo"} and not column.endswith("_label")
]
for column in dimensions:
    choices = sorted(data[column].dropna().astype(str).unique())
    if len(choices) > 1:
        selected = st.sidebar.selectbox(column, choices)
        data = data.loc[data[column].astype(str) == selected]
years = sorted(data["period"].dt.year.unique().tolist())
selected_years = st.sidebar.multiselect("Year", years, default=years)
months = sorted(data["period"].dt.month.unique().tolist())
selected_months = st.sidebar.multiselect("Month", months, default=months)
data = data.loc[
    data["period"].dt.year.isin(selected_years)
    & data["period"].dt.month.isin(selected_months)
]

tab_overview, tab_trends, tab_regions, tab_economy, tab_prediction = st.tabs(
    ["Overview", "Tourism Trends", "Regional Analysis", "Economic Impact", "Prediction"]
)
with tab_overview:
    if data["period"].duplicated().any():
        st.warning("Choose dimensions in the sidebar until exactly one monthly series remains; totals are not summed across categories.")
    else:
        first, second = st.columns(2)
        first.metric("Observed tourism nights", f"{data['value'].sum():,.0f}", help="Sum of the selected monthly series only.")
        second.metric("Months observed", f"{data['period'].nunique():,}")
    st.dataframe(data.head(20), use_container_width=True)
with tab_trends:
    if "geo" in data and not data.duplicated(["period", "geo"]).any():
        trend = data.pivot(index="period", columns="geo", values="value")
        st.line_chart(trend, y_label="Nights (provider unit)")
    elif not data["period"].duplicated().any():
        st.line_chart(data.set_index("period")["value"], y_label="Nights (provider unit)")
    else:
        st.warning("Choose one value for each non-time category before charting this source.")
with tab_regions:
    region_column = next((name for name in ("geo", "nuts2", "region") if name in data), None)
    if region_column and not data.duplicated(["period", region_column]).any():
        ranking = data.groupby(region_column, as_index=False)["value"].sum()
        st.dataframe(ranking.sort_values("value", ascending=False), use_container_width=True)
    else:
        st.info("Regional comparison is unavailable in the selected single-series view or source data.")
with tab_economy:
    economy_path = PROCESSED / "world_bank_indicators.csv"
    if economy_path.exists():
        st.dataframe(pd.read_csv(economy_path), use_container_width=True)
        st.caption("Annual World Bank indicators are shown separately; association does not establish causality.")
    else:
        st.info("Economic indicators are unavailable until the World Bank source is downloaded.")
with tab_prediction:
    prediction_path = PROCESSED / "model_predictions.csv"
    metrics_path = PROCESSED / "model_metrics.json"
    if prediction_path.exists() and metrics_path.exists():
        predictions = pd.read_csv(prediction_path, parse_dates=["period"]).set_index("period")
        st.line_chart(predictions[["actual", "random_forest", "seasonal_naive"]])
        st.json(json.loads(metrics_path.read_text(encoding="utf-8")))
    else:
        st.info("Prediction results are unavailable until sufficient monthly observations are acquired and the chronological models run.")
