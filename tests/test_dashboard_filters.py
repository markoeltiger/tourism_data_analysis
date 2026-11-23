import unittest
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

from src.dashboard_filters import filter_month_year, prepare_month_year


class DashboardFilterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = pd.DataFrame({
            "period": ["2024-01-01", "2024-06-01", "2025-01-01", "2025-06-01"],
            "value": [10, 20, 30, 40],
        })

    def test_year_and_month_are_combined(self) -> None:
        result = filter_month_year(self.data, [2024], [6])
        self.assertEqual(result["value"].tolist(), [20])

    def test_empty_year_or_month_selection_returns_no_rows(self) -> None:
        self.assertTrue(filter_month_year(self.data, [], [1]).empty)
        self.assertTrue(filter_month_year(self.data, [2025], []).empty)

    def test_prepare_adds_numeric_year_and_month(self) -> None:
        result = prepare_month_year(self.data)
        self.assertEqual(result["year"].tolist(), [2024, 2024, 2025, 2025])
        self.assertEqual(result["month"].tolist(), [1, 6, 1, 6])

    def test_dashboard_imports_src_when_launched_outside_repository(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        script = repository / "dashboard" / "app.py"
        with tempfile.TemporaryDirectory() as working_directory:
            completed = subprocess.run(
                [sys.executable, "-c", f"import runpy; runpy.run_path({str(script)!r})"],
                cwd=working_directory,
                capture_output=True,
                text=True,
                timeout=30,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
