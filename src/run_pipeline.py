"""Command-line entry point for source collection and analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.analysis import run_eda
from src.data_cleaning import PROCESSED_DIR, RAW_DIR, clean_downloads
from src.data_collection import download_sources
from src.modelling import analyze_annual_economy, fit_demand_models, make_monthly_series
from src.prediction import run_chronological_prediction


def run(
    download: bool = True,
    category_filters: dict[str, str] | None = None,
) -> dict[str, str]:
    statuses: dict[str, str] = {}
    if download:
        downloaded = download_sources()
        statuses["collection"] = f"Downloaded {len(downloaded)} original source payloads"
    else:
        statuses["collection"] = "Skipped by request; reading existing raw files"

    raw_files = (
        [
            path
            for path in RAW_DIR.rglob("*")
            if path.is_file() and path.suffix.lower() in {".json", ".csv"}
        ]
        if RAW_DIR.exists()
        else []
    )
    if not raw_files:
        statuses["data"] = "UNAVAILABLE: no raw source responses found; no results computed"
        _write_status(statuses)
        return statuses

    frames = clean_downloads()
    statuses["cleaning"] = f"Cleaned and exported {len(frames)} datasets"
    if not frames:
        statuses["data"] = "No observations were returned by the configured source responses"
        _write_status(statuses)
        return statuses

    summaries = run_eda(frames)
    statuses["eda"] = f"Created descriptive summaries for {len(summaries)} datasets"
    tourism = frames.get("tour_occ_nim")
    if tourism is None or tourism.empty or "period" not in tourism:
        statuses["models"] = "UNAVAILABLE: monthly national tourism series is not present"
    else:
        if not category_filters:
            available_filters = {
                column: set(tourism[column].dropna().astype(str).unique())
                for column in ("freq", "c_resid", "unit", "nace_r2", "geo")
                if column in tourism
            }
            category_filters = {}
            if "freq" in available_filters and "M" in available_filters["freq"]:
                category_filters["freq"] = "M"
            if "c_resid" in available_filters and "TOTAL" in available_filters["c_resid"]:
                category_filters["c_resid"] = "TOTAL"
            if "unit" in available_filters and "NR" in available_filters["unit"]:
                category_filters["unit"] = "NR"
            if "nace_r2" in available_filters and "I551" in available_filters["nace_r2"]:
                category_filters["nace_r2"] = "I551"
            if "geo" in available_filters and "HU" in available_filters["geo"]:
                category_filters["geo"] = "HU"
        try:
            series = make_monthly_series(tourism, category_filters=category_filters)
        except ValueError as error:
            statuses["models"] = f"NOT RUN: {error}"
        else:
            try:
                run_chronological_prediction(tourism, PROCESSED_DIR, category_filters)
                statuses["models"] = "Completed chronological model comparison"
            except ValueError as error:
                statuses["models"] = f"NOT RUN: {error}"
            economy = frames.get("world_bank_indicators")
            if economy is not None and not economy.empty:
                analyze_annual_economy(series, economy, PROCESSED_DIR)
                statuses["economic_analysis"] = "Completed aligned annual correlation and regression analysis"
            else:
                statuses["economic_analysis"] = "UNAVAILABLE: annual economic indicators are absent"
    _write_status(statuses)
    return statuses


def _write_status(statuses: dict[str, str]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [{"stage": stage, "status": status} for stage, status in statuses.items()]
    ).to_csv(PROCESSED_DIR / "pipeline_status.csv", index=False)
    for stage, status in statuses.items():
        print(f"{stage}: {status}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Use existing files under data/raw rather than accessing provider APIs.",
    )
    parser.add_argument(
        "--filter",
        action="append",
        default=[],
        metavar="DIMENSION=CODE",
        help="Select one exact provider category; repeat for each non-time dimension.",
    )
    args = parser.parse_args()
    filters: dict[str, str] = {}
    for item in args.filter:
        if "=" not in item:
            parser.error(f"Invalid filter {item!r}; expected DIMENSION=CODE")
        dimension, code = item.split("=", 1)
        if not dimension or not code:
            parser.error(f"Invalid filter {item!r}; expected DIMENSION=CODE")
        filters[dimension] = code
    run(download=not args.skip_download, category_filters=filters)
