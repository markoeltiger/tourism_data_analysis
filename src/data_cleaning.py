"""Normalize provider payloads without modifying the original raw files."""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"


def eurostat_to_frame(payload: dict[str, Any]) -> pd.DataFrame:
    """Expand Eurostat JSON-stat dimensions into one row per observation."""
    dimension_ids = payload["id"]
    sizes = payload["size"]
    dimensions = payload["dimension"]
    categories: list[list[str]] = []
    labels: dict[str, dict[str, str]] = {}
    for name in dimension_ids:
        category = dimensions[name]["category"]
        index = category["index"]
        ordered_codes = (
            [code for code, _ in sorted(index.items(), key=lambda item: item[1])]
            if isinstance(index, dict)
            else list(range(len(index)))
        )
        categories.append([str(code) for code in ordered_codes])
        labels[name] = {
            str(code): str(category.get("label", {}).get(str(code), code))
            for code in ordered_codes
        }

    values = payload.get("value", {})
    if isinstance(values, list):
        indexed_values = {i: value for i, value in enumerate(values) if value is not None}
    else:
        indexed_values = {int(i): value for i, value in values.items()}

    rows = []
    for flat_index, codes in enumerate(itertools.product(*categories)):
        if flat_index not in indexed_values:
            continue
        row = {dimension_ids[i]: code for i, code in enumerate(codes)}
        row["value"] = indexed_values[flat_index]
        for name, code in zip(dimension_ids, codes):
            row[f"{name}_label"] = labels[name].get(code, code)
        rows.append(row)

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    time_column = next((name for name in dimension_ids if name in {"time", "month"}), None)
    if time_column:
        frame["period"] = pd.to_datetime(frame[time_column], format="mixed", errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame.dropna(subset=["value"]).drop_duplicates().reset_index(drop=True)


def world_bank_to_frame(payload: list[Any], indicator: str) -> pd.DataFrame:
    """Normalize a World Bank API response into annual observations."""
    if len(payload) < 2 or not isinstance(payload[1], list):
        raise ValueError(f"Unexpected World Bank response for {indicator}")
    frame = pd.DataFrame(payload[1])
    if frame.empty:
        return pd.DataFrame(columns=["year", "indicator", "value", "country_code"])
    return pd.DataFrame(
        {
            "year": pd.to_numeric(frame["date"], errors="coerce").astype("Int64"),
            "indicator": indicator,
            "value": pd.to_numeric(frame["value"], errors="coerce"),
            "country_code": frame["countryiso3code"],
            "country_name": frame["country"].map(lambda item: item.get("value") if isinstance(item, dict) else None),
        }
    ).dropna(subset=["value"]).drop_duplicates().reset_index(drop=True)


def clean_downloads(raw_dir: Path = RAW_DIR, processed_dir: Path = PROCESSED_DIR) -> dict[str, pd.DataFrame]:
    """Read cached raw files, normalize them and persist processed CSVs."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, pd.DataFrame] = {}
    for path in sorted((raw_dir / "eurostat").glob("*.json")):
        with path.open(encoding="utf-8") as source:
            frame = eurostat_to_frame(json.load(source))
        frame.to_csv(processed_dir / f"{path.stem}.csv", index=False)
        outputs[path.stem] = frame

    wb_frames = []
    for path in sorted((raw_dir / "world_bank").glob("*.json")):
        with path.open(encoding="utf-8") as source:
            wb_frames.append(world_bank_to_frame(json.load(source), path.stem))
    if wb_frames:
        economic = pd.concat(wb_frames, ignore_index=True).drop_duplicates()
        economic.to_csv(processed_dir / "world_bank_indicators.csv", index=False)
        outputs["world_bank_indicators"] = economic
    return outputs


if __name__ == "__main__":
    frames = clean_downloads()
    print(f"Processed {len(frames)} datasets.")
