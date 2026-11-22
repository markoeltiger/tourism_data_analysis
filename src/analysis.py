"""Exploratory analysis and publication-quality figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
FIGURES_DIR = ROOT / "figures"
SUMMARY_PATH = PROCESSED_DIR / "descriptive_statistics.csv"


def load_processed() -> dict[str, pd.DataFrame]:
    return {path.stem: pd.read_csv(path) for path in PROCESSED_DIR.glob("*.csv")}


def run_eda(frames: dict[str, pd.DataFrame], figures_dir: Path = FIGURES_DIR) -> dict[str, pd.DataFrame]:
    """Create summaries and figures only from downloaded, processed observations."""
    import seaborn as sns

    figures_dir.mkdir(parents=True, exist_ok=True)
    summaries: dict[str, pd.DataFrame] = {}
    sns.set_theme(style="whitegrid")

    for dataset_name, frame in frames.items():
        if "value" not in frame or frame.empty:
            continue
        if "indicator" in frame:
            for indicator, group in frame.groupby("indicator", dropna=True):
                stats = group["value"].describe().rename(f"{dataset_name}:{indicator}").to_frame()
                summaries[f"{dataset_name}:{indicator}"] = stats
        elif "period" not in frame or not frame["period"].duplicated().any():
            stats = frame["value"].describe().rename(dataset_name).to_frame()
            summaries[dataset_name] = stats
        if "period" not in frame:
            continue

        data = frame.copy()
        data["period"] = pd.to_datetime(data["period"], errors="coerce")
        data = data.dropna(subset=["period", "value"])
        if data.empty or data["period"].duplicated().any():
            continue

        fig, ax = plt.subplots(figsize=(11, 5))
        sns.lineplot(data=data, x="period", y="value", ax=ax)
        ax.set(title=f"{dataset_name}: monthly tourism observations", xlabel="Month", ylabel="Nights (provider unit)")
        fig.tight_layout()
        fig.savefig(figures_dir / f"{dataset_name}_trend.png", dpi=160)
        plt.close(fig)

        data["month"] = data["period"].dt.month
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.boxplot(data=data, x="month", y="value", ax=ax)
        ax.set(title=f"{dataset_name}: monthly distribution", xlabel="Month", ylabel="Nights (provider unit)")
        fig.tight_layout()
        fig.savefig(figures_dir / f"{dataset_name}_seasonality.png", dpi=160)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(10, 5))
        sns.violinplot(data=data, x="month", y="value", inner=None, cut=0, ax=ax)
        sns.stripplot(data=data, x="month", y="value", color="#243b53", alpha=0.25, size=2, ax=ax)
        ax.set(title=f"{dataset_name}: monthly raincloud-style distribution",
               xlabel="Month", ylabel="Nights (provider unit)")
        fig.tight_layout()
        fig.savefig(figures_dir / f"{dataset_name}_raincloud.png", dpi=160)
        plt.close(fig)

    if summaries:
        pd.concat(summaries, names=["dataset", "statistic"]).to_csv(SUMMARY_PATH)
    return summaries


if __name__ == "__main__":
    output = run_eda(load_processed())
    print(f"EDA summaries created for {len(output)} datasets.")
