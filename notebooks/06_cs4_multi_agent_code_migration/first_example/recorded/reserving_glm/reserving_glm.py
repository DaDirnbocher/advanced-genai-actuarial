import os
import sqlite3
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf


BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'examples', 'difficult')
TRIANGLE_CSV = os.path.join(BASE_DIR, 'claims_triangle.csv')
POLICIES_DB = os.path.join(BASE_DIR, 'policies.db')
OUTPUT_SUMMARY_CSV = os.path.join(os.path.dirname(__file__), 'reserve_summary.csv')


def load_claims_triangle(csv_path: str) -> pd.DataFrame:
    triangle_raw = pd.read_csv(csv_path, index_col=0)
    print(f"Claims triangle loaded: {triangle_raw.shape[0]} x {triangle_raw.shape[1]}")
    return triangle_raw


def load_policy_data(db_path: str) -> Dict[str, pd.DataFrame]:
    con = sqlite3.connect(db_path)
    try:
        policies = pd.read_sql_query("SELECT * FROM policies", con)
        premiums = pd.read_sql_query("SELECT * FROM premiums", con)
        claims = pd.read_sql_query("SELECT * FROM claims_detail", con)

        policy_premiums = pd.merge(policies, premiums, on="policy_id")
        premium_by_year = (
            policy_premiums.groupby("origin_year", as_index=False)
            .agg(
                total_earned_premium=("earned_premium", "sum"),
                total_written_premium=("written_premium", "sum"),
                n_policies=("policy_id", "size"),
            )
        )

        print(f"Policy data loaded: {len(policies)} policies, {len(claims)} claims")
        return {
            "premium_by_year": premium_by_year,
            "policies": policies,
            "claims": claims,
        }
    finally:
        con.close()


def prepare_glm_data(triangle: pd.DataFrame | np.ndarray) -> pd.DataFrame:
    triangle_arr = triangle.to_numpy(dtype=float) if isinstance(triangle, pd.DataFrame) else np.asarray(triangle, dtype=float)
    records = []
    n_rows, n_cols = triangle_arr.shape

    for i in range(n_rows):
        for j in range(n_cols):
            value = triangle_arr[i, j]
            if not np.isnan(value):
                records.append({"origin": i + 1, "dev": j + 1, "incremental": float(value)})

    df = pd.DataFrame(records)
    df["origin_f"] = pd.Categorical(df["origin"])
    df["dev_f"] = pd.Categorical(df["dev"])
    return df


def fit_odp_glm(data: pd.DataFrame) -> Dict[str, Any]:
    model = smf.glm(
        formula="incremental ~ C(origin_f) + C(dev_f)",
        data=data,
        family=sm.families.Poisson(link=sm.families.links.Log()),
    ).fit(scale="X2")

    phi = float(model.scale)

    print("GLM fitted successfully")
    print(f"  Dispersion parameter (phi): {phi:.4f}")
    print(f"  Residual deviance: {model.deviance:.2f}")
    print(f"  Degrees of freedom: {int(model.df_resid)}")

    return {"model": model, "phi": phi}


def predict_reserves(model, n_rows: int, n_cols: int) -> pd.DataFrame:
    pred_records = []

    for i in range(2, n_rows + 1):
        start_dev = n_cols - i + 2
        if start_dev <= n_cols:
            for j in range(start_dev, n_cols + 1):
                pred_records.append({"origin": i, "dev": j})

    pred_data = pd.DataFrame(pred_records)
    if pred_data.empty:
        pred_data["origin_f"] = pd.Categorical([])
        pred_data["dev_f"] = pd.Categorical([])
        pred_data["predicted"] = pd.Series(dtype=float)
        return pred_data

    pred_data["origin_f"] = pd.Categorical(
        pred_data["origin"],
        categories=model.model.data.frame["origin_f"].cat.categories,
    )
    pred_data["dev_f"] = pd.Categorical(
        pred_data["dev"],
        categories=model.model.data.frame["dev_f"].cat.categories,
    )
    pred_data["predicted"] = model.predict(pred_data)
    return pred_data


def bootstrap_reserves(
    model,
    glm_data: pd.DataFrame,
    triangle: pd.DataFrame | np.ndarray,
    n_boot: int = 100,
    phi: Optional[float] = None,
    seed: int = 42,
) -> np.ndarray:
    triangle_arr = triangle.to_numpy(dtype=float) if isinstance(triangle, pd.DataFrame) else np.asarray(triangle, dtype=float)
    n_rows, n_cols = triangle_arr.shape

    if phi is None:
        phi = float(model.scale)

    fitted_vals = np.asarray(model.fittedvalues, dtype=float)
    raw_residuals = (glm_data["incremental"].to_numpy(dtype=float) - fitted_vals) / np.sqrt(fitted_vals)

    n_params = int(len(model.params))
    n_obs = int(len(glm_data))
    adj_factor = np.sqrt(n_obs / (n_obs - n_params))
    adj_residuals = raw_residuals * adj_factor
    valid_residuals = adj_residuals[np.isfinite(adj_residuals)]

    rng = np.random.default_rng(seed)
    boot_reserves = np.full(n_boot, np.nan, dtype=float)

    for b in range(n_boot):
        try:
            resampled_residuals = rng.choice(valid_residuals, size=len(fitted_vals), replace=True)
            pseudo_incremental = fitted_vals + resampled_residuals * np.sqrt(fitted_vals)
            pseudo_incremental = np.maximum(pseudo_incremental, 1.0)

            pseudo_data = glm_data.copy()
            pseudo_data["incremental"] = pseudo_incremental

            pseudo_model = smf.glm(
                formula="incremental ~ C(origin_f) + C(dev_f)",
                data=pseudo_data,
                family=sm.families.Poisson(link=sm.families.links.Log()),
            ).fit(scale="X2")

            pred = predict_reserves(pseudo_model, n_rows, n_cols)
            simulated = rng.gamma(shape=np.asarray(pred["predicted"], dtype=float) / phi, scale=phi)
            boot_reserves[b] = float(np.sum(simulated))
        except Exception:
            boot_reserves[b] = np.nan

    return boot_reserves[np.isfinite(boot_reserves)]


def run_analysis(claims_csv: str, db_path: str, n_boot: int = 1000, seed: int = 42) -> Dict[str, Any]:
    triangle_raw = load_claims_triangle(claims_csv)
    triangle_inc = triangle_raw.to_numpy(dtype=float)

    policy_data = load_policy_data(db_path)
    premium_by_year = policy_data["premium_by_year"]

    print("\nPremium summary by year:")
    print(premium_by_year.head(5))

    glm_data = prepare_glm_data(triangle_raw)
    print(f"\nGLM data prepared: {len(glm_data)} observations")

    glm_result = fit_odp_glm(glm_data)
    model = glm_result["model"]
    phi = glm_result["phi"]

    n_rows, n_cols = triangle_inc.shape
    predictions = predict_reserves(model, n_rows, n_cols)

    reserves_by_year = (
        predictions.groupby("origin", as_index=False)["predicted"]
        .sum()
        .rename(columns={"predicted": "reserve"})
    )
    total_reserve = float(reserves_by_year["reserve"].sum())

    print("\nReserves by origin year:")
    print(reserves_by_year)
    print(f"\nTotal reserve (point estimate): {total_reserve:.2f}")

    print("\n==== DETERMINISTIC OUTPUTS ====")
    print(f"Dispersion parameter (phi): {phi:.10f}")
    print(f"Total reserve (point estimate): {total_reserve:.6f}")
    print("\nReserves by origin year:")
    for _, row in reserves_by_year.iterrows():
        print(f"  Origin {int(row['origin'])}: {row['reserve']:.6f}")
    print("==== END DETERMINISTIC OUTPUTS ====")

    print(f"\nRunning bootstrap ({n_boot} simulations)...")
    boot_results = bootstrap_reserves(model, glm_data, triangle_raw, n_boot=n_boot, phi=phi, seed=seed)
    print(f"Bootstrap complete: {len(boot_results)} successful simulations")

    print("\n==== STOCHASTIC OUTPUTS ====")

    reserve_summary = pd.DataFrame({
        "statistic": ["Mean", "Std Dev", "CV", "P25", "P50 (Median)", "P75", "P95", "P99"],
        "value": np.round([
            float(np.mean(boot_results)),
            float(np.std(boot_results, ddof=1)),
            float(np.std(boot_results, ddof=1) / np.mean(boot_results)),
            float(np.quantile(boot_results, 0.25)),
            float(np.quantile(boot_results, 0.50)),
            float(np.quantile(boot_results, 0.75)),
            float(np.quantile(boot_results, 0.95)),
            float(np.quantile(boot_results, 0.99)),
        ], 2),
    })

    print("\nReserve Distribution Summary:")
    print(reserve_summary)

    origin_years = triangle_raw.index.to_numpy(dtype=int)
    reserves_with_premium = pd.merge(
        pd.DataFrame({
            "origin_year": origin_years[reserves_by_year["origin"].to_numpy(dtype=int) - 1],
            "reserve": reserves_by_year["reserve"].to_numpy(dtype=float),
        }),
        premium_by_year,
        on="origin_year",
        how="left",
    )

    reserves_with_premium["reserve_to_premium"] = np.round(
        reserves_with_premium["reserve"] / reserves_with_premium["total_earned_premium"], 4
    )

    print("\nReserves with Premium Ratios:")
    print(reserves_with_premium[["origin_year", "reserve", "total_earned_premium", "reserve_to_premium"]])

    return {
        "triangle_raw": triangle_raw,
        "triangle_inc": triangle_inc,
        "policy_data": policy_data,
        "premium_by_year": premium_by_year,
        "glm_data": glm_data,
        "model": model,
        "phi": phi,
        "predictions": predictions,
        "reserves_by_year": reserves_by_year,
        "total_reserve": total_reserve,
        "boot_results": boot_results,
        "reserve_summary": reserve_summary,
        "reserves_with_premium": reserves_with_premium,
    }


def main() -> None:
    results = run_analysis(TRIANGLE_CSV, POLICIES_DB, n_boot=1000, seed=42)
    results["reserve_summary"].to_csv(OUTPUT_SUMMARY_CSV, index=False)
    print("\nResults saved to reserve_summary.csv")


if __name__ == "__main__":
    main()
