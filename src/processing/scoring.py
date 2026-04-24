import pandas as pd


def compute_composite_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # --- Cap extreme L/D ratios and adjust direction ---
    df["loan_to_deposit_capped"] = df["loan_to_deposit"].clip(lower=0.4, upper=1.2)
    df["loan_to_deposit_adj"] = -df["loan_to_deposit_capped"]

    # --- Adjust credit-risk metric directions ---
    # Lower NPL and charge-off ratios are better.
    df["npl_ratio_adj"] = -df["npl_ratio"]
    df["chargeoff_ratio_adj"] = -df["chargeoff_ratio"]

    # Recompute direction-adjusted percentiles
    df["loan_to_deposit_pct"] = (
        df.groupby("REPDTE")["loan_to_deposit_adj"].rank(pct=True)
    )

    df["npl_ratio_pct"] = (
        df.groupby("REPDTE")["npl_ratio_adj"].rank(pct=True)
    )

    df["chargeoff_ratio_pct"] = (
        df.groupby("REPDTE")["chargeoff_ratio_adj"].rank(pct=True)
    )

    # --- Weighted score ---
    # Profitability remains dominant, but credit risk now has a real role.
    metrics = {
        "roa_calc_pct": 0.30,
        "roe_calc_pct": 0.25,
        "equity_to_assets_pct": 0.15,
        "loan_to_deposit_pct": 0.10,
        "npl_ratio_pct": 0.10,
        "chargeoff_ratio_pct": 0.10,
    }

    df["composite_score"] = sum(
        df[metric] * weight for metric, weight in metrics.items()
    )

    # --- Rank within each quarter ---
    df["composite_rank"] = (
        df.groupby("REPDTE")["composite_score"]
        .rank(method="first", ascending=False)
    )

    # --- Rolling 4-quarter score ---
    df = df.sort_values(["Ticker", "REPDTE"]).copy()

    df["score_rolling_4q"] = (
        df.groupby("Ticker")["composite_score"]
        .rolling(4, min_periods=4)
        .mean()
        .reset_index(level=0, drop=True)
    )

    # --- Rolling 4-quarter score rank ---
    df["rolling_4q_rank"] = (
        df.groupby("REPDTE")["score_rolling_4q"]
        .rank(method="first", ascending=False)
    )

    return df