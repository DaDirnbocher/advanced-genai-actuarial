import os
import warnings
from typing import Tuple

import numpy as np
import pandas as pd


TAIL_FACTOR = 1.00
INPUT_FILE = "triangle.csv"


def get_data_path(filename: str = INPUT_FILE) -> str:
    return os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "examples",
        "simple",
        filename,
    )


def row_is_contiguous(x: np.ndarray) -> bool:
    obs = np.where(~pd.isna(x))[0]
    if len(obs) == 0:
        return False
    return np.array_equal(obs, np.arange(obs.max() + 1))


def read_triangle(input_file: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    triangle_data = pd.read_csv(input_file, index_col=0)
    triangle_inc = triangle_data.to_numpy(dtype=float)
    origin_years = triangle_data.index.astype(str).to_numpy()
    dev_periods = triangle_data.columns.astype(str).to_numpy()
    return triangle_inc, origin_years, dev_periods


def validate_triangle(triangle_inc: np.ndarray, origin_years: np.ndarray, dev_periods: np.ndarray) -> None:
    n_origin, n_dev = triangle_inc.shape

    if n_origin == 0 or n_dev < 2:
        raise ValueError("Triangle must have at least 1 origin period and 2 development periods.")

    if np.any(origin_years == ""):
        raise ValueError("Origin period names are missing.")

    if np.any(np.sum(~pd.isna(triangle_inc), axis=1) == 0):
        raise ValueError("At least one origin period has no observed data.")

    bad_rows = [i for i in range(n_origin) if not row_is_contiguous(triangle_inc[i, :])]
    if bad_rows:
        rows_text = ", ".join(origin_years[bad_rows])
        raise ValueError(
            "Triangle has internal missing values or does not start at development period 1 for row(s): "
            f"{rows_text}. Clean the input triangle before reserving."
        )

    if np.any(triangle_inc[~pd.isna(triangle_inc)] < 0):
        warnings.warn(
            "Negative incremental values detected. "
            "Simple chain-ladder on cumulative data may be unstable; review recoveries/re-openings.",
            UserWarning,
        )


def compute_cumulative_triangle(
    triangle_inc: np.ndarray, origin_years: np.ndarray, dev_periods: np.ndarray
) -> pd.DataFrame:
    n_origin, n_dev = triangle_inc.shape
    triangle_cum = np.full((n_origin, n_dev), np.nan, dtype=float)

    for i in range(n_origin):
        obs = np.where(~pd.isna(triangle_inc[i, :]))[0]
        triangle_cum[i, obs] = np.cumsum(triangle_inc[i, obs])

    for i in range(n_origin):
        obs = np.where(~pd.isna(triangle_cum[i, :]))[0]
        if len(obs) > 1 and np.any(np.diff(triangle_cum[i, obs]) < 0):
            warnings.warn(
                f"Cumulative claims decrease for origin period {origin_years[i]}. Review input data.",
                UserWarning,
            )

    return pd.DataFrame(triangle_cum, index=origin_years, columns=dev_periods)


def calculate_development_factors(
    triangle_cum: pd.DataFrame, dev_periods: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    triangle_cum_np = triangle_cum.to_numpy(dtype=float)
    n_dev = triangle_cum_np.shape[1]
    dev_factors = np.full(n_dev - 1, np.nan, dtype=float)
    n_pairs = np.zeros(n_dev - 1, dtype=int)

    for j in range(n_dev - 1):
        valid_rows = (~pd.isna(triangle_cum_np[:, j])) & (~pd.isna(triangle_cum_np[:, j + 1]))
        n_pairs[j] = int(np.sum(valid_rows))

        if n_pairs[j] == 0:
            raise ValueError(
                f"No observed pairs available to calculate development factor for {dev_periods[j]} -> {dev_periods[j + 1]}."
            )

        denom = float(np.sum(triangle_cum_np[valid_rows, j]))
        if denom <= 0:
            raise ValueError(
                f"Non-positive denominator when calculating development factor for {dev_periods[j]} -> {dev_periods[j + 1]}."
            )

        dev_factors[j] = float(np.sum(triangle_cum_np[valid_rows, j + 1]) / denom)

        if dev_factors[j] < 1:
            warnings.warn(
                f"Selected development factor for {dev_periods[j]} -> {dev_periods[j + 1]} is {dev_factors[j]:.4f} (< 1). "
                "Review whether simple chain-ladder is appropriate.",
                UserWarning,
            )

    dev_factor_table = pd.DataFrame(
        {
            "from_dev": dev_periods[:-1],
            "to_dev": dev_periods[1:],
            "n_pairs": n_pairs,
            "factor": np.round(dev_factors, 6),
        }
    )

    return dev_factors, n_pairs, dev_factor_table


def calculate_cdf_to_ultimate(dev_factors: np.ndarray, dev_periods: np.ndarray, tail_factor: float) -> pd.DataFrame:
    n_dev = len(dev_periods)
    cdf_to_ultimate = np.full(n_dev, np.nan, dtype=float)
    cdf_to_ultimate[-1] = tail_factor

    if n_dev > 1:
        for j in range(n_dev - 2, -1, -1):
            cdf_to_ultimate[j] = dev_factors[j] * cdf_to_ultimate[j + 1]

    cdf_table = pd.DataFrame(
        {
            "dev_period": dev_periods,
            "cdf_to_ultimate": np.round(cdf_to_ultimate, 6),
        }
    )
    return cdf_table


def project_ultimates(
    triangle_cum: pd.DataFrame, origin_years: np.ndarray, dev_periods: np.ndarray, cdf_values: np.ndarray
) -> pd.DataFrame:
    triangle_cum_np = triangle_cum.to_numpy(dtype=float)
    n_origin = triangle_cum_np.shape[0]

    latest_observed = np.full(n_origin, np.nan, dtype=float)
    latest_dev_idx = np.zeros(n_origin, dtype=int)
    ultimate_claims = np.full(n_origin, np.nan, dtype=float)
    reserve_amount = np.full(n_origin, np.nan, dtype=float)

    for i in range(n_origin):
        obs = np.where(~pd.isna(triangle_cum_np[i, :]))[0]
        latest_dev_idx[i] = int(obs.max())
        latest_observed[i] = triangle_cum_np[i, latest_dev_idx[i]]
        ultimate_claims[i] = latest_observed[i] * cdf_values[latest_dev_idx[i]]
        reserve_amount[i] = ultimate_claims[i] - latest_observed[i]

    results = pd.DataFrame(
        {
            "origin_year": origin_years,
            "latest_dev_period": dev_periods[latest_dev_idx],
            "latest_observed": np.round(latest_observed, 2),
            "cdf_to_ultimate": np.round(cdf_values[latest_dev_idx], 6),
            "ultimate": np.round(ultimate_claims, 2),
            "unpaid_claims_reserve": np.round(reserve_amount, 2),
        }
    )
    return results


def run_chain_ladder(input_file: str = None, tail_factor: float = TAIL_FACTOR):
    if input_file is None:
        input_file = get_data_path(INPUT_FILE)

    triangle_inc, origin_years, dev_periods = read_triangle(input_file)
    validate_triangle(triangle_inc, origin_years, dev_periods)

    triangle_cum = compute_cumulative_triangle(triangle_inc, origin_years, dev_periods)
    dev_factors, n_pairs, dev_factor_table = calculate_development_factors(triangle_cum, dev_periods)
    cdf_table = calculate_cdf_to_ultimate(dev_factors, dev_periods, tail_factor)
    cdf_values = cdf_table["cdf_to_ultimate"].to_numpy(dtype=float)
    results = project_ultimates(triangle_cum, origin_years, dev_periods, cdf_values)

    total_reserve = round(float(results["unpaid_claims_reserve"].sum(skipna=True)), 2)

    return {
        "triangle_cum": triangle_cum,
        "dev_factors": dev_factors,
        "n_pairs": n_pairs,
        "dev_factor_table": dev_factor_table,
        "cdf_table": cdf_table,
        "results": results,
        "total_reserve": total_reserve,
    }


def main() -> None:
    output = run_chain_ladder()

    print("Cumulative Triangle:")
    print(output["triangle_cum"])

    print("\nDevelopment Factors (volume-weighted):")
    print(output["dev_factor_table"])

    print("\nCDF to Ultimate:")
    print(output["cdf_table"])

    print("\nUltimate Claims by Origin Year:")
    print(output["results"])

    print(f"\nTotal Unpaid Claims Reserve: {output['total_reserve']}")


if __name__ == "__main__":
    main()
