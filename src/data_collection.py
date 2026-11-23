"""Download unchanged source responses from official statistical providers."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
EUROSTAT_ENDPOINT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
WORLD_BANK_ENDPOINT = "https://api.worldbank.org/v2/country/HUN/indicator"
ECB_ENDPOINT = "https://data-api.ecb.europa.eu/service/data/EXR/D.HUF.EUR.SP00.A"

EUROSTAT_DATASETS = {
    "tour_occ_nim": {
        "dataset": "Monthly nights spent at tourist accommodation establishments",
        "params": {"geo": "HU", "unit": "NR", "sinceTimePeriod": "2015-01"},
    },
    "tour_occ_nin2": {
        "dataset": "Nights spent at tourist accommodation establishments by NUTS 3 region",
        "params": {"geo": "HU", "unit": "NR", "sinceTimePeriod": "2015-01"},
    },
}
WORLD_BANK_INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "GDP growth (annual %)",
    "NY.GDP.PCAP.CD": "GDP per capita (current US$)",
    "FP.CPI.TOTL.ZG": "Inflation, consumer prices (annual %)",
    "SP.POP.TOTL": "Population, total",
}
KSH_DATASETS = {
    "tur0079": {
        "dataset": "Number of tourism nights at tourist accommodation establishments by county and region",
        "url": "https://www.ksh.hu/stadat_files/tur/en/tur0079.csv",
    },
    "tur0080": {
        "dataset": "Number of international tourist nights at tourist accommodation establishments by county and region",
        "url": "https://www.ksh.hu/stadat_files/tur/en/tur0080.csv",
    },
}
ECB_DATASET = "EXR_D_HUF_EUR_SP00_A"


def _validate_payload(content: bytes, source_format: str) -> None:
    """Reject provider error pages or malformed responses before saving them."""
    if source_format == "json":
        payload = json.loads(content)
        if isinstance(payload, dict):
            valid = {"id", "size", "dimension", "value"}.issubset(payload)
        else:
            valid = (
                isinstance(payload, list)
                and len(payload) >= 2
                and isinstance(payload[1], list)
            )
        if not valid:
            raise ValueError("Provider returned an unexpected JSON payload")
        return

    text = content.decode("iso-8859-2" if source_format == "ksh_csv" else "utf-8-sig")
    reader = csv.reader(io.StringIO(text), delimiter=";" if source_format == "ksh_csv" else ",")
    rows = list(reader)
    if source_format == "ksh_csv":
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
        if header_index is None or not any(
            re.fullmatch(r"\d{4} [A-Za-z]+", cell.strip())
            for cell in rows[header_index][2:]
        ):
            raise ValueError("KSH response did not contain the expected monthly table")
    elif source_format == "ecb_csv":
        header = rows[0] if rows else []
        if not {"TIME_PERIOD", "OBS_VALUE"}.issubset(header) or len(rows) < 2:
            raise ValueError("ECB response did not contain exchange-rate observations")
    else:
        raise ValueError(f"Unknown provider response format: {source_format}")


def _save_response(
    url: str,
    params: dict[str, str],
    destination: Path,
    source_format: str,
) -> None:
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    _validate_payload(response.content, source_format)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.read_bytes() == response.content:
        return
    destination.write_bytes(response.content)


def _write_checksum_manifest(paths: list[Path], raw_dir: Path) -> None:
    lines = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(raw_dir).as_posix()}"
        for path in sorted(paths)
    ]
    (raw_dir / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def download_sources(raw_dir: Path = RAW_DIR) -> list[Path]:
    """Fetch and validate original provider payloads; surface all request failures."""
    outputs: list[Path] = []
    for code, spec in EUROSTAT_DATASETS.items():
        target = raw_dir / "eurostat" / f"{code}.json"
        _save_response(
            f"{EUROSTAT_ENDPOINT}/{code}",
            {**spec["params"], "format": "JSON"},
            target,
            "json",
        )
        outputs.append(target)

    for indicator in WORLD_BANK_INDICATORS:
        target = raw_dir / "world_bank" / f"{indicator}.json"
        _save_response(
            f"{WORLD_BANK_ENDPOINT}/{indicator}",
            {"format": "json", "per_page": "100", "date": "2015:2025"},
            target,
            "json",
        )
        outputs.append(target)

    for code, spec in KSH_DATASETS.items():
        target = raw_dir / "ksh" / f"{code}.csv"
        _save_response(spec["url"], {}, target, "ksh_csv")
        outputs.append(target)

    ecb_target = raw_dir / "ecb" / f"{ECB_DATASET}.csv"
    _save_response(
        ECB_ENDPOINT,
        {"format": "csvdata", "startPeriod": "2015-01-01"},
        ecb_target,
        "ecb_csv",
    )
    outputs.append(ecb_target)

    _write_checksum_manifest(outputs, raw_dir)
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
