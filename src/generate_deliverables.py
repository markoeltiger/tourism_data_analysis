"""Render the evidence-backed report and 12-slide presentation PDFs."""

from __future__ import annotations

import textwrap
from collections.abc import Callable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.backends.backend_pdf import PdfPages

from src.tourism_figures import (
    plot_annual_correlation,
    plot_monthly_seasonality,
    plot_monthly_trend,
    prepare_latest_ksh_regions,
    prepare_residence_series,
)

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
PROCESSED = ROOT / "data" / "processed"


def _plain_lines(markdown: str, width: int) -> list[str]:
    lines: list[str] = []
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line:
            lines.append("")
        elif line.startswith("#"):
            lines.extend(textwrap.wrap(line.lstrip("# ").upper(), width=width) or [""])
        else:
            lines.extend(textwrap.wrap(line, width=width) or [""])
    return lines


def render_report(source: Path, destination: Path) -> None:
    lines = _plain_lines(source.read_text(encoding="utf-8"), 92)
    with PdfPages(destination) as pdf:
        for start in range(0, len(lines), 48):
            page = lines[start : start + 48]
            fig = plt.figure(figsize=(8.27, 11.69), facecolor="white")
            fig.text(0.08, 0.96, "\n".join(page), va="top", ha="left",
                     family="DejaVu Sans", fontsize=9.5, linespacing=1.35)
            fig.text(0.08, 0.035, "Hungary Tourism Analytics | Official-source evidence; see coverage notes",
                     color="#52616b", fontsize=8)
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)


def _presentation_charts(
    processed_dir: Path,
) -> tuple[dict[int, Callable[[Axes], object]], dict[int, str], dict[int, str]]:
    charts: dict[int, Callable[[Axes], object]] = {}
    notes: dict[int, str] = {}
    unavailable: dict[int, str] = {}

    tourism_path = processed_dir / "tour_occ_nim.csv"
    if not tourism_path.exists():
        unavailable[6] = (
            "data/processed/tour_occ_nim.csv is missing. Run "
            "`python -m src.run_pipeline` to download and process it."
        )
        unavailable[8] = unavailable[6]
    else:
        tourism, reason = prepare_residence_series(pd.read_csv(tourism_path))
        if tourism is None:
            unavailable[6] = reason or "Compatible Eurostat residence observations are unavailable."
            unavailable[8] = unavailable[6]
        else:
            charts[6] = lambda ax: plot_monthly_trend(
                tourism,
                title="Hungary monthly tourism nights by visitor residence",
                ylabel="Nights spent (number)",
                hue_column="residence_category",
                ax=ax,
            )
            notes[6] = (
                "Source: Eurostat tour_occ_nim; geo=HU, freq=M, unit=NR, NACE I551. "
                "Domestic and foreign categories are shown as published."
            )
            charts[8] = lambda ax: plot_monthly_seasonality(
                tourism,
                title="Observed monthly tourism-night distributions by residence",
                ylabel="Nights spent (number)",
                hue_column="residence_category",
                ax=ax,
            )
            notes[8] = (
                "Source: Eurostat tour_occ_nim with the same filters; monthly "
                "distributions use observed values only, with no imputation."
            )

    ksh_path = processed_dir / "ksh_tourism_monthly.csv"
    if not ksh_path.exists():
        unavailable[7] = (
            "data/processed/ksh_tourism_monthly.csv is missing. Run "
            "`python -m src.run_pipeline` to download and process it."
        )
    else:
        regions, reason = prepare_latest_ksh_regions(pd.read_csv(ksh_path))
        if regions is None:
            unavailable[7] = reason or "Compatible KSH regional observations are unavailable."
        else:
            unavailable[7] = (
                "Compatible KSH regional data are available for the dashboard, but "
                "the source table does not state reuse terms. Its figure is omitted "
                "from this distributed presentation until redistribution is confirmed."
            )

    economy_path = processed_dir / "annual_tourism_economy.csv"
    if not economy_path.exists():
        unavailable[9] = (
            "data/processed/annual_tourism_economy.csv is missing. Run "
            "`python -m src.run_pipeline` to download and process it."
        )
    else:
        economy = pd.read_csv(economy_path)
        availability_figure = plot_annual_correlation(economy)
        if availability_figure is None:
            unavailable[9] = "Compatible matched annual tourism-economic data are unavailable."
        else:
            plt.close(availability_figure)
            charts[9] = lambda ax: plot_annual_correlation(economy, ax=ax)
            if "year" in economy and not economy.empty:
                years = f"{int(economy['year'].min())}–{int(economy['year'].max())}"
                notes[9] = (
                    f"Source: aligned annual Eurostat and World Bank observations, "
                    f"{years} (n={len(economy)}); descriptive association, not causation."
                )
            else:
                notes[9] = (
                    "Source: aligned annual Eurostat and World Bank observations; "
                    "descriptive association, not causation."
                )

    return charts, notes, unavailable


def render_slides(
    source: Path,
    destination: Path,
    processed_dir: Path = PROCESSED,
) -> None:
    markdown = source.read_text(encoding="utf-8")
    sections = [section.strip() for section in markdown.split("### Slide ")[1:] if section.strip()]
    charts, chart_notes, unavailable = _presentation_charts(processed_dir)
    with PdfPages(destination) as pdf:
        for index, section in enumerate(sections, start=1):
            title, _, body = section.partition("\n")
            fig = plt.figure(figsize=(13.33, 7.5), facecolor="#f5f8fa")
            fig.text(0.08, 0.88, f"{index:02d}", color="#d62828", fontsize=18, weight="bold")
            fig.text(0.08, 0.78, title.strip(), color="#102a43", fontsize=25, weight="bold")
            wrapped = "\n".join(textwrap.wrap(body.strip().replace("\n", " "), width=92))
            if index in charts:
                fig.text(0.08, 0.67, wrapped, color="#243b53", fontsize=14, va="top", linespacing=1.35)
                ax = fig.add_axes([0.11, 0.16, 0.78, 0.40])
                charts[index](ax)
                fig.text(0.10, 0.09, chart_notes[index], color="#52616b", fontsize=8.5)
            else:
                fig.text(0.08, 0.60, wrapped, color="#243b53", fontsize=17, va="top", linespacing=1.45)
                if index in unavailable:
                    fig.text(
                        0.08,
                        0.28,
                        "Figure unavailable: "
                        + unavailable[index]
                        + " No substitute values are shown.",
                        color="#9b2226",
                        fontsize=12,
                        va="top",
                        wrap=True,
                    )
            fig.text(0.08, 0.035, "DISCOVER HUNGARY  •  OFFICIAL-SOURCE EMPIRICAL RESULTS",
                     color="#627d98", fontsize=10, weight="bold")
            pdf.savefig(fig)
            plt.close(fig)


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    render_report(REPORTS / "project_report.md", REPORTS / "project_report.pdf")
    render_slides(REPORTS / "presentation.md", REPORTS / "presentation.pdf")
    print("Rendered report and presentation PDFs; slide figures use only current processed source data.")


if __name__ == "__main__":
    main()
