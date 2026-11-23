"""Render the evidence-backed report and 12-slide presentation PDFs."""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


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
            fig.text(0.08, 0.035, "Hungary Tourism Analytics | Evidence status: no data acquired",
                     color="#52616b", fontsize=8)
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)


def render_slides(source: Path, destination: Path) -> None:
    markdown = source.read_text(encoding="utf-8")
    sections = [section.strip() for section in markdown.split("### Slide ")[1:] if section.strip()]
    with PdfPages(destination) as pdf:
        for index, section in enumerate(sections, start=1):
            title, _, body = section.partition("\n")
            fig = plt.figure(figsize=(13.33, 7.5), facecolor="#f5f8fa")
            fig.text(0.08, 0.88, f"{index:02d}", color="#d62828", fontsize=18, weight="bold")
            fig.text(0.08, 0.72, title.strip(), color="#102a43", fontsize=28, weight="bold")
            wrapped = "\n".join(textwrap.wrap(body.strip().replace("\n", " "), width=78))
            fig.text(0.08, 0.57, wrapped, color="#243b53", fontsize=19, va="top", linespacing=1.5)
            fig.text(0.08, 0.08, "DISCOVER HUNGARY  •  OFFICIAL-SOURCE EMPIRICAL RESULTS",
                     color="#627d98", fontsize=10, weight="bold")
            pdf.savefig(fig)
            plt.close(fig)


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    render_report(REPORTS / "project_report.md", REPORTS / "project_report.pdf")
    render_slides(REPORTS / "presentation.md", REPORTS / "presentation.pdf")
    print("Rendered report and 12-slide presentation PDFs with evidence-backed results.")


if __name__ == "__main__":
    main()
