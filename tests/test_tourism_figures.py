import tempfile
import unittest
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.generate_deliverables import _presentation_charts
from src.tourism_figures import (
    plot_annual_correlation,
    plot_monthly_seasonality,
    plot_monthly_trend,
    plot_regional_values,
    prepare_latest_ksh_regions,
    prepare_residence_series,
)


class TourismFigureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.monthly = pd.DataFrame(
            [
                {
                    "freq": "M",
                    "unit": "NR",
                    "nace_r2": "I551",
                    "geo": "HU",
                    "c_resid": residence,
                    "c_resid_label": label,
                    "period": period,
                    "value": value,
                }
                for period, domestic, foreign in (
                    ("2024-01-01", 100, 50),
                    ("2024-02-01", 110, 60),
                    ("2024-03-01", 120, 70),
                )
                for residence, label, value in (
                    ("DOM", "Domestic country", domestic),
                    ("FOR", "Foreign country", foreign),
                )
            ]
        )

    def test_selects_domestic_and_foreign_for_one_exact_eurostat_series(self) -> None:
        extra = self.monthly.iloc[[0]].copy()
        extra["nace_r2"] = "I552"
        total = self.monthly.iloc[[0]].copy()
        total["c_resid"] = "TOTAL"
        frame = pd.concat([self.monthly, extra, total], ignore_index=True)

        selected, reason = prepare_residence_series(frame)

        self.assertIsNone(reason)
        self.assertEqual(len(selected), 6)
        self.assertEqual(set(selected["c_resid"]), {"DOM", "FOR"})
        self.assertEqual(set(selected["nace_r2"]), {"I551"})

    def test_missing_residence_category_is_reported_without_substitution(self) -> None:
        selected, reason = prepare_residence_series(
            self.monthly.loc[self.monthly["c_resid"] == "DOM"]
        )

        self.assertIsNone(selected)
        self.assertIn("Both domestic and foreign", reason)

    def test_seasonality_and_trend_use_seaborn_figures(self) -> None:
        selected, _ = prepare_residence_series(self.monthly)
        trend = plot_monthly_trend(
            selected,
            title="Hungary tourism nights",
            hue_column="residence_category",
        )
        seasonality = plot_monthly_seasonality(
            selected,
            title="Hungary tourism seasonality",
            hue_column="residence_category",
        )

        legend = trend.axes[0].get_legend()
        self.assertEqual(
            {text.get_text() for text in legend.get_texts()},
            {"Domestic country", "Foreign country"},
        )
        self.assertEqual(seasonality.axes[0].get_xlabel(), "Month")
        plt.close(trend)
        plt.close(seasonality)

    def test_regional_comparison_uses_latest_compatible_source_rows(self) -> None:
        regions = pd.DataFrame(
            [
                {
                    "dataset": "tur0079",
                    "period": "2024-01-01",
                    "geo": "Region A",
                    "geo_level": "large region",
                    "accommodation_type": "Tourist accommodation establishments",
                    "value": 20,
                },
                {
                    "dataset": "tur0079",
                    "period": "2024-02-01",
                    "geo": "Region A",
                    "geo_level": "large region",
                    "accommodation_type": "Tourist accommodation establishments",
                    "value": 30,
                },
                {
                    "dataset": "tur0079",
                    "period": "2024-02-01",
                    "geo": "Region B",
                    "geo_level": "large region",
                    "accommodation_type": "Tourist accommodation establishments",
                    "value": 40,
                },
                {
                    "dataset": "tur0080",
                    "period": "2024-02-01",
                    "geo": "Region A",
                    "geo_level": "large region",
                    "accommodation_type": "Tourist accommodation establishments",
                    "value": 10,
                },
            ]
        )

        selected, reason = prepare_latest_ksh_regions(regions)

        self.assertIsNone(reason)
        self.assertEqual(set(selected["geo"]), {"Region A", "Region B"})
        self.assertTrue((selected["period"] == "2024-02-01").all())
        figure = plot_regional_values(selected, title="KSH large-region nights")
        self.assertEqual(figure.axes[0].get_ylabel(), "Geography (as reported)")
        plt.close(figure)

    def test_correlation_heatmap_requires_compatible_matched_values(self) -> None:
        self.assertIsNone(plot_annual_correlation(pd.DataFrame({"year": [2022]})))
        figure = plot_annual_correlation(
            pd.DataFrame(
                {
                    "year": [2022, 2023, 2024],
                    "tourism_nights": [100, 120, 130],
                    "indicator": [1.2, 1.5, 1.8],
                }
            )
        )
        self.assertIsNotNone(figure)
        plt.close(figure)

    def test_presentation_reports_absent_processed_datasets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            charts, _, unavailable = _presentation_charts(Path(temporary_directory))

        self.assertEqual(charts, {})
        self.assertEqual(set(unavailable), {6, 7, 8, 9})
        self.assertIn("missing", unavailable[6])
        self.assertIn("missing", unavailable[7])

    def test_presentation_does_not_redistribute_ksh_without_reuse_terms(self) -> None:
        rows = pd.DataFrame(
            [
                {
                    "dataset": "tur0079",
                    "period": "2024-02-01",
                    "geo": region,
                    "geo_level": "large region",
                    "accommodation_type": "Tourist accommodation establishments",
                    "value": value,
                }
                for region, value in (("Region A", 20), ("Region B", 30))
            ]
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            processed = Path(temporary_directory)
            rows.to_csv(processed / "ksh_tourism_monthly.csv", index=False)
            charts, _, unavailable = _presentation_charts(processed)

        self.assertNotIn(7, charts)
        self.assertIn("reuse terms", unavailable[7])


if __name__ == "__main__":
    unittest.main()
