"""Testable helpers for the Streamlit monthly time filters."""

from __future__ import annotations

import pandas as pd


def prepare_month_year(data: pd.DataFrame) -> pd.DataFrame:
    """Normalize monthly data before applying independent year/month filters."""
    if "period" not in data:
        raise ValueError("Processed tourism data must contain a period column.")
    result = data.copy()
    result["period"] = pd.to_datetime(result["period"], errors="coerce")
    result["value"] = pd.to_numeric(result["value"], errors="coerce")
    result = result.dropna(subset=["period", "value"]).copy()
    result["year"] = result["period"].dt.year
    result["month"] = result["period"].dt.month
    return result


def filter_month_year(
    data: pd.DataFrame,
    selected_years: list[int],
    selected_months: list[int],
) -> pd.DataFrame:
    """Apply both time filters; an empty selection produces no observations."""
    prepared = prepare_month_year(data)
    if not selected_years or not selected_months:
        return prepared.iloc[0:0].copy()
    return prepared.loc[
        prepared["year"].isin(selected_years)
        & prepared["month"].isin(selected_months)
    ].copy()
