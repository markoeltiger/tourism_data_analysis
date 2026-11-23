"""Shared Seaborn figures for Hungarian tourism dashboard and presentation."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.figure import Figure


EUROSTAT_SERIES_FILTERS = {
    "freq": "M",
    "unit": "NR",
    "nace_r2": "I551",
    "geo": "HU",
}
RESIDENCE_CODES = ("DOM", "FOR")
MONTHS = tuple(pd.date_range("2024-01-01", periods=12, freq="MS").strftime("%b"))
CORRELATION_LABELS = {
    "tourism_nights": "Tourism nights",
    "FP.CPI.TOTL.ZG": "Inflation (annual %)",
    "NY.GDP.MKTP.KD.ZG": "GDP growth (annual %)",
    "NY.GDP.PCAP.CD": "GDP per capita (current US$)",
    "SP.POP.TOTL": "Population (persons)",
}


def prepare_residence_series(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame | None, str | None]:
    """Select the compatible Eurostat Hungary domestic/foreign monthly series."""
    if frame.empty:
        return None, "The Eurostat monthly tourism dataset is empty."

    data = frame.copy()
    for column, expected in EUROSTAT_SERIES_FILTERS.items():
        if column not in data:
            return None, f"The Eurostat {column} dimension is missing."
        data[column] = data[column].astype(str)
        if expected not in set(data[column].dropna()):
            return None, f"The Eurostat {column}={expected} series is unavailable."
        data = data.loc[data[column] == expected]

    if not {"period", "value", "c_resid"}.issubset(data.columns):
        return None, "Eurostat residence, period, or value fields are missing."
    data["c_resid"] = data["c_resid"].astype(str)
    data = data.loc[data["c_resid"].isin(RESIDENCE_CODES)].copy()
    data["period"] = pd.to_datetime(data["period"], errors="coerce")
    data["value"] = pd.to_numeric(data["value"], errors="coerce")
    data = data.dropna(subset=["period", "value"])
    if set(data["c_resid"].unique()) != set(RESIDENCE_CODES):
        return None, "Both domestic and foreign Eurostat observations are required."
    if data.duplicated(["period", "c_resid"]).any():
        return None, "Eurostat residence categories do not define unique monthly observations."
    if (data.groupby("c_resid", observed=True).size() < 2).any():
        return None, "There are too few monthly observations for both residence categories."

    if "c_resid_label" in data:
        data["residence_category"] = data["c_resid_label"].fillna(data["c_resid"])
    else:
        data["residence_category"] = data["c_resid"].map(
            {"DOM": "Domestic country", "FOR": "Foreign country"}
        )
    return data.sort_values(["period", "c_resid"]).reset_index(drop=True), None


def prepare_latest_ksh_regions(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame | None, str | None]:
    """Select one compatible KSH large-region observation per region and month."""
    required = {
        "dataset",
        "period",
        "geo",
        "geo_level",
        "accommodation_type",
        "value",
    }
    if not required.issubset(frame.columns):
        return None, "The KSH dataset is missing required geography or value fields."

    data = frame.loc[
        (frame["dataset"].astype(str) == "tur0079")
        & (frame["geo_level"].astype(str) == "large region")
        & (
            frame["accommodation_type"].astype(str)
            == "Tourist accommodation establishments"
        )
    ].copy()
    data["period"] = pd.to_datetime(data["period"], errors="coerce")
    data["value"] = pd.to_numeric(data["value"], errors="coerce")
    data = data.dropna(subset=["period", "geo", "value"])
    if data.empty:
        return None, "KSH total tourism nights by large region are unavailable."

    latest = data["period"].max()
    data = data.loc[data["period"] == latest]
    if data["geo"].duplicated().any():
        return None, "KSH large-region observations are not unique for the latest month."
    if len(data) < 2:
        return None, "At least two KSH large regions are required for comparison."
    return data.sort_values("geo").reset_index(drop=True), None


def _get_axes(ax: Axes | None, figsize: tuple[float, float]) -> tuple[Figure, Axes, bool]:
    if ax is not None:
        return ax.figure, ax, False
    fig, created_ax = plt.subplots(figsize=figsize)
    return fig, created_ax, True


def _finish(fig: Figure, created_axes: bool) -> Figure:
    if created_axes:
        fig.tight_layout()
    return fig


def plot_monthly_trend(
    data: pd.DataFrame,
    *,
    title: str,
    ylabel: str = "Nights spent (number)",
    hue_column: str | None = None,
    ax: Axes | None = None,
) -> Figure:
    """Plot source observations without aggregating duplicate monthly values."""
    required = {"period", "value"}
    if not required.issubset(data.columns):
        raise ValueError("Monthly tourism figures require period and value columns.")
    if hue_column is not None:
        if hue_column not in data or data.duplicated(["period", hue_column]).any():
            raise ValueError("Each plotted category must have one observation per month.")
    elif data["period"].duplicated().any():
        raise ValueError("Monthly tourism figures require one observation per month.")

    sns.set_theme(style="whitegrid")
    fig, ax, created_axes = _get_axes(ax, (11, 5))
    sns.lineplot(
        data=data,
        x="period",
        y="value",
        hue=hue_column,
        estimator=None,
        errorbar=None,
        ax=ax,
    )
    legend = ax.get_legend()
    if legend is not None:
        legend.set_title(
            "Visitor residence"
            if hue_column == "residence_category"
            else hue_column.replace("_", " ").title()
        )
    ax.set(title=title, xlabel="Month", ylabel=ylabel)
    ax.tick_params(axis="x", rotation=30)
    return _finish(fig, created_axes)


def plot_monthly_seasonality(
    data: pd.DataFrame,
    *,
    title: str,
    ylabel: str = "Nights spent (number)",
    hue_column: str | None = None,
    ax: Axes | None = None,
) -> Figure:
    """Compare observed monthly distributions without imputing missing months."""
    if not {"period", "value"}.issubset(data.columns):
        raise ValueError("Seasonality figures require period and value columns.")
    if hue_column is not None and hue_column not in data:
        raise ValueError(f"Seasonality category is absent: {hue_column}")

    plot_data = data.copy()
    plot_data["period"] = pd.to_datetime(plot_data["period"], errors="coerce")
    plot_data["value"] = pd.to_numeric(plot_data["value"], errors="coerce")
    plot_data = plot_data.dropna(subset=["period", "value"])
    plot_data["month_name"] = plot_data["period"].dt.month.map(
        {month: name for month, name in enumerate(MONTHS, start=1)}
    )
    sns.set_theme(style="whitegrid")
    fig, ax, created_axes = _get_axes(ax, (11, 5))
    sns.boxplot(
        data=plot_data,
        x="month_name",
        y="value",
        hue=hue_column,
        order=MONTHS,
        ax=ax,
    )
    legend = ax.get_legend()
    if legend is not None:
        legend.set_title(
            "Visitor residence"
            if hue_column == "residence_category"
            else hue_column.replace("_", " ").title()
        )
    ax.set(title=title, xlabel="Month", ylabel=ylabel)
    return _finish(fig, created_axes)


def plot_regional_values(
    data: pd.DataFrame,
    *,
    title: str,
    ylabel: str = "Nights spent (number)",
    ax: Axes | None = None,
) -> Figure:
    """Plot one source period and geographic level in source-name order."""
    if not {"geo", "value"}.issubset(data.columns):
        raise ValueError("Regional figures require geo and value columns.")
    if data["geo"].duplicated().any():
        raise ValueError("Regional figures require one observation per geography.")

    sns.set_theme(style="whitegrid")
    fig, ax, created_axes = _get_axes(ax, (10, 5))
    sns.barplot(
        data=data.sort_values("geo"),
        x="value",
        y="geo",
        order=sorted(data["geo"].astype(str).unique()),
        errorbar=None,
        ax=ax,
    )
    ax.set(title=title, xlabel=ylabel, ylabel="Geography (as reported)")
    return _finish(fig, created_axes)


def plot_annual_correlation(
    data: pd.DataFrame,
    *,
    title: str = "Pearson correlations across matched annual observations",
    ax: Axes | None = None,
) -> Figure | None:
    """Draw a correlation heatmap only when aligned numeric variables exist."""
    if "tourism_nights" not in data:
        return None
    numeric = data.drop(columns=["year"], errors="ignore").select_dtypes(
        include="number"
    ).rename(columns=CORRELATION_LABELS)
    if "Tourism nights" not in numeric or numeric.shape[1] < 2:
        return None
    correlation = numeric.corr(min_periods=3)
    if not correlation.drop(columns="Tourism nights").loc[
        "Tourism nights"
    ].notna().any():
        return None

    sns.set_theme(style="white")
    fig, ax, created_axes = _get_axes(ax, (10, 7))
    sns.heatmap(
        correlation,
        annot=True,
        fmt=".2f",
        cmap="vlag",
        center=0,
        vmin=-1,
        vmax=1,
        mask=correlation.isna(),
        cbar_kws={"label": "Pearson correlation"},
        ax=ax,
    )
    ax.set(title=title)
    ax.tick_params(axis="x", labelrotation=35, labelsize=8)
    ax.tick_params(axis="y", labelsize=8)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")
    return _finish(fig, created_axes)
