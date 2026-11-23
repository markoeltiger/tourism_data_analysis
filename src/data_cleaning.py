"""Normalize provider payloads without modifying the original raw files."""

from __future__ import annotations

import csv
import itertools
import json
import re
from calendar import month_name
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
MONTHS = {name.lower(): number for number, name in enumerate(month_name) if name}


def _normalize_strings(
    frame: pd.DataFrame,
    columns: list[str],
    uppercase: tuple[str, ...] = (),
) -> pd.DataFrame:
    """Trim provider strings and normalize only identifier codes to uppercase."""
    for column in columns:
        if column in frame:
            frame[column] = frame[column].map(
                lambda value: value.strip() if isinstance(value, str) else value
            )
            if column in uppercase:
                frame[column] = frame[column].map(
                    lambda value: value.upper() if isinstance(value, str) else value
                )
    return frame


def _deduplicate(frame: pd.DataFrame, keys: list[str], dataset: str) -> pd.DataFrame:
    """Drop exact duplicate rows and reject conflicting observations for one key."""
    duplicate_rows = frame.loc[frame.duplicated(keys, keep=False)]
    if not duplicate_rows.empty:
        for _, group in duplicate_rows.groupby(keys, dropna=False, sort=False):
            if len(group.drop_duplicates()) > 1:
                raise ValueError(f"Conflicting duplicate observation in {dataset}")
    return frame.drop_duplicates().reset_index(drop=True)


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
        categories.append([str(code).strip() for code in ordered_codes])
        labels[name] = {
            str(code).strip(): str(category.get("label", {}).get(str(code), code)).strip()
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
    _normalize_strings(
        frame,
        dimension_ids,
        uppercase=tuple(name for name in dimension_ids if name != "time"),
    )
    time_column = next((name for name in dimension_ids if name in {"time", "month"}), None)
    if time_column:
        frame["period"] = pd.to_datetime(frame[time_column], format="mixed", errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    required = ["value", *(["period"] if time_column else [])]
    frame = frame.dropna(subset=required)
    if time_column:
        frame["year"] = frame["period"].dt.year.astype("Int64")
        is_monthly = (
            frame["freq"].eq("M").all()
            if "freq" in frame
            else time_column == "month"
            or frame[time_column].astype(str).str.fullmatch(r"\d{4}-\d{2}").all()
        )
        if is_monthly:
            frame["month"] = frame["period"].dt.month.astype("Int64")
    return _deduplicate(frame, dimension_ids, "Eurostat").sort_values(
        dimension_ids, kind="stable"
    ).reset_index(drop=True)


def world_bank_to_frame(payload: list[Any], indicator: str) -> pd.DataFrame:
    """Normalize a World Bank API response into annual observations."""
    if len(payload) < 2 or not isinstance(payload[1], list):
        raise ValueError(f"Unexpected World Bank response for {indicator}")
    frame = pd.DataFrame(payload[1])
    if frame.empty:
        return pd.DataFrame(columns=["year", "indicator", "value", "country_code"])
    frame = pd.DataFrame(
        {
            "year": pd.to_numeric(frame["date"], errors="coerce").astype("Int64"),
            "indicator": indicator,
            "value": pd.to_numeric(frame["value"], errors="coerce"),
            "country_code": frame["countryiso3code"],
            "country_name": frame["country"].map(lambda item: item.get("value") if isinstance(item, dict) else None),
        }
    )
    _normalize_strings(frame, ["indicator", "country_code"], uppercase=("country_code",))
    _normalize_strings(frame, ["country_name"])
    frame = frame.dropna(subset=["year", "value", "country_code"])
    return _deduplicate(frame, ["year", "country_code", "indicator"], "World Bank").sort_values(
        ["country_code", "year", "indicator"], kind="stable"
    ).reset_index(drop=True)


def ksh_to_frame(path: Path) -> pd.DataFrame:
    """Expand an unmodified KSH STADAT semicolon-separated table into monthly rows."""
    with path.open(encoding="iso-8859-2", newline="") as source:
        rows = list(csv.reader(source, delimiter=";"))

    header_index = next(
        (
            index
            for index, row in enumerate(rows)
            if len(row) >= 3
            and row[0].strip() == "Name of territorial units"
            and row[1].strip() == "Level of territorial units"
        ),
        None,
    )
    if header_index is None:
        raise ValueError(f"Unexpected KSH table in {path.name}: monthly header not found")

    columns = rows[header_index]
    month_columns: list[tuple[int, int, int]] = []
    for index, label in enumerate(columns[2:], start=2):
        match = re.fullmatch(r"(\d{4}) ([A-Za-z]+)", label.strip())
        if match and match.group(2).lower() in MONTHS:
            month_columns.append((index, int(match.group(1)), MONTHS[match.group(2).lower()]))
    if not month_columns:
        raise ValueError(f"Unexpected KSH table in {path.name}: no monthly columns found")

    records: list[dict[str, Any]] = []
    accommodation_type = ""
    for row in rows[header_index + 1 :]:
        if not row or not row[0].strip():
            continue
        geography = row[0].strip()
        level = row[1].strip() if len(row) > 1 else ""
        if not level:
            accommodation_type = geography
            continue
        for index, year, month in month_columns:
            if index >= len(row) or not row[index].strip():
                continue
            number = row[index].replace(" ", "").replace("\u00a0", "").strip()
            if not number.isdigit():
                raise ValueError(
                    f"Unexpected KSH value {row[index]!r} for {geography} in {year}-{month:02d}"
                )
            records.append(
                {
                    "period": pd.Timestamp(year=year, month=month, day=1),
                    "geo": geography,
                    "geo_level": level,
                    "accommodation_type": accommodation_type,
                    "value": int(number),
                }
            )
    frame = pd.DataFrame(
        records,
        columns=["period", "geo", "geo_level", "accommodation_type", "value"],
    )
    _normalize_strings(frame, ["geo", "geo_level", "accommodation_type"])
    if not frame.empty:
        frame["year"] = frame["period"].dt.year.astype("Int64")
        frame["month"] = frame["period"].dt.month.astype("Int64")
    return _deduplicate(
        frame,
        ["period", "geo", "geo_level", "accommodation_type"],
        path.name,
    ).sort_values(
        ["period", "geo", "geo_level", "accommodation_type"], kind="stable"
    ).reset_index(drop=True)


def ecb_to_frame(path: Path) -> pd.DataFrame:
    """Read the ECB CSV export without modifying it; retain daily HUF/EUR observations."""
    frame = pd.read_csv(path, usecols=["TIME_PERIOD", "OBS_VALUE"])
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(frame["TIME_PERIOD"], errors="coerce"),
            "value": pd.to_numeric(frame["OBS_VALUE"], errors="coerce"),
        }
    ).dropna(subset=["date", "value"])
    if not frame.empty:
        frame["year"] = frame["date"].dt.year.astype("Int64")
        frame["month"] = frame["date"].dt.month.astype("Int64")
    return _deduplicate(frame, ["date"], path.name).sort_values(
        "date", kind="stable"
    ).reset_index(drop=True)


def _world_bank_wide(frame: pd.DataFrame) -> pd.DataFrame:
    """Pivot compatible annual country indicators without filling missing values."""
    if frame.empty:
        return pd.DataFrame(columns=["year", "country_code", "country_name"])
    country_names = frame.loc[
        frame["country_name"].notna(), ["country_code", "country_name"]
    ].drop_duplicates()
    if country_names.duplicated("country_code").any():
        raise ValueError("Conflicting country names in World Bank indicators")
    wide = frame.pivot(
        index=["year", "country_code"],
        columns="indicator",
        values="value",
    ).reset_index().merge(
        country_names,
        on="country_code",
        how="left",
        validate="many_to_one",
    )
    wide.columns.name = None
    indicators = sorted(frame["indicator"].dropna().unique())
    return wide[["year", "country_code", "country_name", *indicators]]


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
        economic = _deduplicate(
            pd.concat(wb_frames, ignore_index=True),
            ["year", "country_code", "indicator"],
            "World Bank",
        ).sort_values(["country_code", "year", "indicator"]).reset_index(drop=True)
        economic.to_csv(processed_dir / "world_bank_indicators.csv", index=False)
        outputs["world_bank_indicators"] = economic
        economic_wide = _world_bank_wide(economic)
        economic_wide.to_csv(processed_dir / "world_bank_indicators_wide.csv", index=False)
        outputs["world_bank_indicators_wide"] = economic_wide

    ksh_frames = []
    for path in sorted((raw_dir / "ksh").glob("*.csv")):
        frame = ksh_to_frame(path)
        frame.to_csv(processed_dir / f"{path.stem}.csv", index=False)
        outputs[path.stem] = frame
        if not frame.empty:
            frame = frame.copy()
            frame.insert(0, "dataset", path.stem)
            ksh_frames.append(frame)
    if ksh_frames:
        ksh_monthly = _deduplicate(
            pd.concat(ksh_frames, ignore_index=True),
            ["dataset", "period", "geo", "geo_level", "accommodation_type"],
            "KSH",
        ).sort_values(
            ["dataset", "period", "geo", "geo_level", "accommodation_type"]
        ).reset_index(drop=True)
        ksh_monthly.to_csv(processed_dir / "ksh_tourism_monthly.csv", index=False)
        outputs["ksh_tourism_monthly"] = ksh_monthly

    ecb_path = raw_dir / "ecb" / "EXR_D_HUF_EUR_SP00_A.csv"
    if ecb_path.exists():
        exchange_rates = ecb_to_frame(ecb_path)
        exchange_rates.to_csv(processed_dir / "ecb_huf_eur_daily.csv", index=False)
        outputs["ecb_huf_eur_daily"] = exchange_rates
    return outputs


if __name__ == "__main__":
    frames = clean_downloads()
    print(f"Processed {len(frames)} datasets.")
