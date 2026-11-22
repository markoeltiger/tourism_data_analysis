"""Download unchanged source responses from Eurostat and the World Bank."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
EUROSTAT_ENDPOINT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
WORLD_BANK_ENDPOINT = "https://api.worldbank.org/v2/country/HUN/indicator"

EUROSTAT_DATASETS = {
    "tour_occ_nim": {
        "dataset": "Monthly nights spent at tourist accommodation establishments",
        "params": {"geo": "HU", "unit": "NR", "sinceTimePeriod": "2015-01"},
    },
    "tour_occ_nin2": {
        "dataset": "Monthly nights spent at tourist accommodation establishments by NUTS 2 region",
        "params": {"geo": "HU", "unit": "NR", "sinceTimePeriod": "2015-01"},
    },
}
WORLD_BANK_INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "GDP growth (annual %)",
    "NY.GDP.PCAP.CD": "GDP per capita (current US$)",
    "FP.CPI.TOTL.ZG": "Inflation, consumer prices (annual %)",
    "SP.POP.TOTL": "Population, total",
}


def _save_response(url: str, params: dict[str, str], destination: Path) -> None:
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response.content)


def download_sources(raw_dir: Path = RAW_DIR) -> list[Path]:
    """Fetch original provider payloads; a failed request is surfaced to the caller."""
    outputs: list[Path] = []
    for code, spec in EUROSTAT_DATASETS.items():
        target = raw_dir / "eurostat" / f"{code}.json"
        _save_response(
            f"{EUROSTAT_ENDPOINT}/{code}",
            {**spec["params"], "format": "JSON"},
            target,
        )
        outputs.append(target)
    for indicator in WORLD_BANK_INDICATORS:
        target = raw_dir / "world_bank" / f"{indicator}.json"
        _save_response(
            f"{WORLD_BANK_ENDPOINT}/{indicator}",
            {"format": "json", "per_page": "100", "date": "2015:2025"},
            target,
        )
        outputs.append(target)
    return outputs


def read_eurostat_json(path: Path) -> Any:
    """Parse an untouched Eurostat JSON-stat response."""
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def download_with_message(raw_dir: Path = RAW_DIR) -> list[Path]:
    """Entry point used by the CLI; preserve provider/network errors."""
    return download_sources(raw_dir)


if __name__ == "__main__":
    for downloaded in download_with_message():
        print(downloaded.relative_to(ROOT))
