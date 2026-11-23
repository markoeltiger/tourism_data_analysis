import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from src.data_cleaning import (
    ecb_to_frame,
    eurostat_to_frame,
    ksh_to_frame,
    world_bank_to_frame,
)
from src.data_collection import _save_response, download_sources
from src.modelling import make_monthly_series


class ProviderParsingTests(unittest.TestCase):
    def test_expands_json_stat_cells_without_changing_values(self):
        payload = {
            "id": ["geo", "time"],
            "size": [1, 2],
            "dimension": {
                "geo": {"category": {"index": {"HU": 0}, "label": {"HU": "Hungary"}}},
                "time": {"category": {"index": {"2024-01": 0, "2024-02": 1}}},
            },
            "value": {"0": 100, "1": 125},
        }
        frame = eurostat_to_frame(payload)
        self.assertEqual(frame["value"].tolist(), [100, 125])
        self.assertEqual(frame["geo_label"].tolist(), ["Hungary", "Hungary"])
        self.assertEqual(frame["period"].dt.month.tolist(), [1, 2])

    def test_world_bank_normalizes_annual_indicator(self):
        payload = [
            {"page": 1},
            [{
                "date": "2024",
                "value": 2.5,
                "countryiso3code": "HUN",
                "country": {"value": "Hungary"},
            }],
        ]
        frame = world_bank_to_frame(payload, "TEST")
        self.assertEqual(int(frame.loc[0, "year"]), 2024)
        self.assertEqual(frame.loc[0, "value"], 2.5)

    def test_model_series_rejects_ambiguous_categories(self):
        import pandas as pd

        frame = pd.DataFrame({
            "period": ["2024-01-01", "2024-01-01"],
            "value": [10, 20],
            "geo": ["HU", "HU"],
            "residence": ["DOM", "FOR"],
        })
        with self.assertRaisesRegex(ValueError, "category_filters"):
            make_monthly_series(frame)


class RawProviderReaderTests(unittest.TestCase):
    def test_reads_ksh_monthly_csv_and_keeps_raw_bytes_unchanged(self):
        content = (
            "27.2.2.1;;;;\n"
            "Name of territorial units;Level of territorial units;2024 January;2024 February\n"
            "Commercial accommodation establishments;;;\n"
            "Budapest;capital, region;1 234;0\n"
            "Total;country;2 345;\n"
        ).encode("iso-8859-2")
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "tur0079.csv"
            path.write_bytes(content)

            frame = ksh_to_frame(path)

            self.assertEqual(len(frame), 3)
            self.assertEqual(frame["geo"].tolist(), ["Budapest", "Budapest", "Total"])
            self.assertEqual(frame["value"].tolist(), [1234, 0, 2345])
            self.assertEqual(frame["period"].dt.strftime("%Y-%m").tolist(), [
                "2024-01",
                "2024-02",
                "2024-01",
            ])
            self.assertEqual(frame["accommodation_type"].tolist(), [
                "Commercial accommodation establishments",
            ] * 3)
            self.assertEqual(path.read_bytes(), content)

    def test_reads_ecb_csv_without_modifying_raw_bytes(self):
        content = (
            "KEY,FREQ,TIME_PERIOD,OBS_VALUE\n"
            "D.HUF.EUR.SP00.A,D,2024-01-02,378.12\n"
            "D.HUF.EUR.SP00.A,D,2024-01-03,377.91\n"
        ).encode()
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "ecb.csv"
            path.write_bytes(content)

            frame = ecb_to_frame(path)

            self.assertEqual(frame["value"].tolist(), [378.12, 377.91])
            self.assertEqual(frame["date"].dt.strftime("%Y-%m-%d").tolist(), [
                "2024-01-02",
                "2024-01-03",
            ])
            self.assertEqual(path.read_bytes(), content)

    def test_ksh_reader_rejects_unexpected_layout(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "invalid.csv"
            path.write_text("not a KSH table\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "monthly header"):
                ksh_to_frame(path)


class DownloaderTests(unittest.TestCase):
    def test_downloads_all_sources_and_writes_sha256_manifest_offline(self):
        eurostat_payload = json.dumps(
            {
                "id": ["geo", "time"],
                "size": [1, 1],
                "dimension": {},
                "value": {"0": 1},
            }
        ).encode()
        world_bank_payload = json.dumps(
            [{"page": 1}, [{
                "date": "2024",
                "value": 2.5,
                "countryiso3code": "HUN",
                "country": {"value": "Hungary"},
            }]]
        ).encode()
        ksh_payload = (
            "27.2.2.1;;;;\n"
            "Name of territorial units;Level of territorial units;2024 January\n"
            "Budapest;capital, region;1 234\n"
        ).encode("iso-8859-2")
        ecb_payload = (
            "KEY,FREQ,TIME_PERIOD,OBS_VALUE\n"
            "D.HUF.EUR.SP00.A,D,2024-01-02,378.12\n"
        ).encode()

        def fake_get(url, params, timeout):
            if "eurostat" in url:
                content = eurostat_payload
            elif "worldbank" in url:
                content = world_bank_payload
            elif "ksh.hu" in url:
                content = ksh_payload
            else:
                content = ecb_payload
            response = Mock()
            response.content = content
            return response

        with tempfile.TemporaryDirectory() as temporary_directory:
            raw_dir = Path(temporary_directory)
            with patch("src.data_collection.requests.get", side_effect=fake_get) as get:
                outputs = download_sources(raw_dir)

            self.assertEqual(len(outputs), 9)
            self.assertEqual(get.call_count, 9)
            self.assertEqual(
                (raw_dir / "ecb" / "EXR_D_HUF_EUR_SP00_A.csv").read_bytes(),
                ecb_payload,
            )
            checksum_lines = (raw_dir / "SHA256SUMS.txt").read_text().splitlines()
            self.assertEqual(len(checksum_lines), 9)
            expected_digest = hashlib.sha256(ksh_payload).hexdigest()
            self.assertTrue(any(expected_digest in line and "tur0079.csv" in line for line in checksum_lines))

    def test_http_failure_is_raised_without_creating_raw_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "source.json"
            response = Mock()
            response.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
            with patch("src.data_collection.requests.get", return_value=response):
                with self.assertRaisesRegex(requests.HTTPError, "403"):
                    _save_response("https://provider.test/data", {}, path, "json")
            self.assertFalse(path.exists())

    def test_invalid_provider_payload_is_not_saved(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "source.json"
            response = Mock()
            response.content = b'{"error":"unavailable"}'
            with patch("src.data_collection.requests.get", return_value=response):
                with self.assertRaisesRegex(ValueError, "unexpected JSON"):
                    _save_response("https://provider.test/data", {}, path, "json")
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
