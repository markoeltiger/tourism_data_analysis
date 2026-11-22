import unittest

from src.data_cleaning import eurostat_to_frame, world_bank_to_frame
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


if __name__ == "__main__":
    unittest.main()
