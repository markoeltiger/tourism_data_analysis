"""Chronological tourism-demand models; never shuffle time-series observations."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def _figures_dir(output_dir: Path) -> Path:
    """Resolve repository figures from processed output; otherwise use local output."""
    if output_dir.name == "processed" and output_dir.parent.name == "data":
        return output_dir.parent.parent / "figures"
    return output_dir / "figures"


def make_monthly_series(
    frame: pd.DataFrame,
    category_filters: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Select one explicit Eurostat category and return a unique monthly series."""
    data = frame.copy()
    for column, category in (category_filters or {}).items():
        if column not in data:
            raise ValueError(f"Requested filter column is absent: {column}")
        data = data.loc[data[column].astype(str) == str(category)]
    if "period" not in data or "value" not in data:
        raise ValueError("Tourism data must include period and value columns.")
    data["period"] = pd.to_datetime(data["period"], errors="coerce")
    data["value"] = pd.to_numeric(data["value"], errors="coerce")
    data = data.dropna(subset=["period", "value"]).sort_values("period")
    if data["period"].duplicated().any():
        raise ValueError(
            "More than one observation remains per month. Supply category_filters "
            "for every non-time dimension; do not aggregate incompatible series."
        )
    return data[["period", "value"]].reset_index(drop=True)


def fit_demand_models(series: pd.DataFrame, output_dir: Path) -> dict[str, object]:
    """Compare baseline and learned forecasts on a chronological holdout."""
    if len(series) < 30:
        raise ValueError("At least 30 monthly observations are required for the holdout model.")
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    data = series.copy().sort_values("period").reset_index(drop=True)
    data["lag_1"] = data["value"].shift(1)
    data["lag_12"] = data["value"].shift(12)
    data["month"] = data["period"].dt.month
    data = data.dropna().reset_index(drop=True)
    split = int(len(data) * 0.8)
    if split < 12 or len(data) - split < 3:
        raise ValueError("Insufficient observations for a stable chronological test split.")

    features = ["lag_1", "lag_12", "month"]
    train, test = data.iloc[:split], data.iloc[split:]
    from sklearn.linear_model import LinearRegression

    linear = LinearRegression()
    linear.fit(train[features], train["value"])
    linear_predictions = linear.predict(test[features])
    forest = RandomForestRegressor(n_estimators=300, min_samples_leaf=2, random_state=42)
    forest.fit(train[features], train["value"])
    predictions = forest.predict(test[features])
    baseline = test["lag_12"].to_numpy()
    metrics = {
        "linear_regression": {
            "mae": float(mean_absolute_error(test["value"], linear_predictions)),
            "rmse": float(np.sqrt(mean_squared_error(test["value"], linear_predictions))),
            "r2": float(r2_score(test["value"], linear_predictions)),
        },
        "random_forest": {
            "mae": float(mean_absolute_error(test["value"], predictions)),
            "rmse": float(np.sqrt(mean_squared_error(test["value"], predictions))),
            "r2": float(r2_score(test["value"], predictions)),
        },
        "seasonal_naive": {
            "mae": float(mean_absolute_error(test["value"], baseline)),
            "rmse": float(np.sqrt(mean_squared_error(test["value"], baseline))),
            "r2": float(r2_score(test["value"], baseline)),
        },
    }

    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, f1_score
    from sklearn.tree import DecisionTreeClassifier

    threshold = float(train["value"].median())
    train_class = (train["value"] >= threshold).astype(int)
    test_class = (test["value"] >= threshold).astype(int)
    classifier = LogisticRegression(max_iter=1000)
    classifier.fit(train[features], train_class)
    tree = DecisionTreeClassifier(max_depth=3, min_samples_leaf=3, random_state=42)
    tree.fit(train[features], train_class)
    metrics["high_demand_threshold"] = threshold
    for name, model in (("logistic_regression", classifier), ("decision_tree", tree)):
        predicted = model.predict(test[features])
        metrics[name] = {
            "accuracy": float(accuracy_score(test_class, predicted)),
            "f1": float(f1_score(test_class, predicted, zero_division=0)),
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "period": test["period"].to_numpy(),
            "actual": test["value"].to_numpy(),
            "linear_regression": linear_predictions,
            "random_forest": predictions,
            "seasonal_naive": baseline,
        }
    ).to_csv(output_dir / "model_predictions.csv", index=False)
    import matplotlib.pyplot as plt
    from sklearn.tree import plot_tree

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.plot(test["period"], test["value"], label="Actual")
    ax.plot(test["period"], linear_predictions, label="Linear regression")
    ax.plot(test["period"], predictions, label="Random forest")
    ax.plot(test["period"], baseline, label="Seasonal naive")
    ax.set(title="Tourism demand: chronological holdout", xlabel="Month", ylabel="Nights (provider unit)")
    ax.legend()
    fig.tight_layout()
    figures_dir = _figures_dir(output_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(figures_dir / "actual_vs_predicted.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 8))
    plot_tree(tree, feature_names=features, class_names=["Low demand", "High demand"], filled=True, ax=ax)
    fig.tight_layout()
    fig.savefig(figures_dir / "decision_tree.png", dpi=160)
    plt.close(fig)

    with (output_dir / "model_metrics.json").open("w", encoding="utf-8") as target:
        json.dump(metrics, target, indent=2)
    return {
        "metrics": metrics,
        "linear_regression": linear,
        "forest": forest,
        "tree": tree,
    }


def analyze_annual_economy(
    monthly_series: pd.DataFrame,
    economy: pd.DataFrame,
    output_dir: Path,
) -> dict[str, object]:
    """Compare annual tourism totals with observed annual indicators, without causal claims."""
    from sklearn.linear_model import LinearRegression

    required = {"year", "indicator", "value"}
    if not required.issubset(economy.columns):
        raise ValueError(f"Economic indicators must include {sorted(required)}")
    tourism = monthly_series.copy()
    tourism["year"] = pd.to_datetime(tourism["period"]).dt.year
    annual_tourism = tourism.groupby("year", as_index=False)["value"].sum()
    annual_tourism = annual_tourism.rename(columns={"value": "tourism_nights"})
    indicators = economy.pivot_table(
        index="year", columns="indicator", values="value", aggfunc="first"
    ).reset_index()
    paired = annual_tourism.merge(indicators, on="year", how="inner").sort_values("year")
    predictors = [column for column in indicators.columns if column != "year"]
    correlations: dict[str, float | None] = {}
    simple_models: dict[str, dict[str, float | int | None]] = {}
    for column in predictors:
        pair = paired[["tourism_nights", column]].dropna()
        correlations[column] = (
            float(pair.corr().iloc[0, 1]) if len(pair) >= 3 and pair[column].nunique() > 1 else None
        )
        if len(pair) >= 3 and pair[column].nunique() > 1:
            model = LinearRegression().fit(pair[[column]], pair["tourism_nights"])
            simple_models[column] = {
                "observations": int(len(pair)),
                "intercept": float(model.intercept_),
                "coefficient": float(model.coef_[0]),
                "r_squared": float(model.score(pair[[column]], pair["tourism_nights"])),
            }

    complete = paired[["tourism_nights", *predictors]].dropna()
    multiple: dict[str, object] = {"status": "NOT RUN: insufficient complete annual observations"}
    if predictors and len(complete) > len(predictors) + 1:
        x = complete[predictors].to_numpy(dtype=float)
        design = np.column_stack([np.ones(len(x)), x])
        if np.linalg.matrix_rank(design) == design.shape[1]:
            model = LinearRegression().fit(complete[predictors], complete["tourism_nights"])
            multiple = {
                "status": "fit",
                "observations": int(len(complete)),
                "predictors": predictors,
                "intercept": float(model.intercept_),
                "coefficients": {
                    name: float(coefficient)
                    for name, coefficient in zip(predictors, model.coef_)
                },
                "r_squared": float(model.score(complete[predictors], complete["tourism_nights"])),
                "predictor_condition_number": float(np.linalg.cond(x)),
            }
        else:
            multiple = {"status": "NOT RUN: predictor design is rank deficient"}

    output_dir.mkdir(parents=True, exist_ok=True)
    if not paired.empty:
        paired.to_csv(output_dir / "annual_tourism_economy.csv", index=False)
        import matplotlib.pyplot as plt
        import seaborn as sns

        matrix = paired.drop(columns="year").corr()
        fig, ax = plt.subplots(figsize=(9, 7))
        sns.heatmap(matrix, annot=True, cmap="vlag", center=0, ax=ax)
        ax.set_title("Annual tourism and economic indicator correlations")
        fig.tight_layout()
        figures_dir = _figures_dir(output_dir)
        figures_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(figures_dir / "economic_correlation_heatmap.png", dpi=160)
        plt.close(fig)
        for column, model_result in simple_models.items():
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.regplot(data=paired, x=column, y="tourism_nights", ax=ax)
            ax.set(title=f"Annual tourism and {column}", ylabel="Annual tourism nights")
            fig.tight_layout()
            fig.savefig(figures_dir / f"regression_{column}.png", dpi=160)
            plt.close(fig)
    pd.Series(correlations, name="pearson_correlation").to_csv(
        output_dir / "economic_correlations.csv", header=True
    )
    results = {
        "simple_linear_regressions": simple_models,
        "multiple_linear_regression": multiple,
        "interpretation_note": "Associations are descriptive and do not establish causality.",
        "matched_years": paired["year"].astype(int).tolist(),
    }
    with (output_dir / "economic_regression_results.json").open("w", encoding="utf-8") as target:
        json.dump(results, target, indent=2)
    return results
