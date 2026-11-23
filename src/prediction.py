"""Public prediction entry point for chronological tourism-demand models."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.modelling import fit_demand_models, make_monthly_series


def run_chronological_prediction(
    tourism: pd.DataFrame,
    output_dir: Path,
    category_filters: dict[str, str] | None = None,
) -> dict[str, object]:
    """Fit chronological demand models for one explicitly identified series."""
    series = make_monthly_series(tourism, category_filters=category_filters)
    return fit_demand_models(series, output_dir)
