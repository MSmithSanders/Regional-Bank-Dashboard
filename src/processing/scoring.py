import pandas as pd


def compute_composite_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # --- Cap extreme L/D ratios and adjust metrics direction ---
    df["loan_to_deposit_capped"] = df["loan_to_deposit"].clip(lower=0.4, upper=1.2)
    df["loan_to_deposit_adj"] = -df["loan_to_deposit_capped"]

    # --- Use percentile ranks (already computed) ---
    metrics = {
        "roa_calc_pct": 0.4,
        "roe_calc_pct": 0.3,
        "equity_to_assets_pct": 0.2,
        "loan_to_deposit_pct": 0.1,
    }

    # Note: for L/D we use adjusted version
    df["loan_to_deposit_pct"] = (
        df.groupby("REPDTE")["loan_to_deposit_adj"]
        .rank(pct=True)
    )

    # --- Weighted score ---
    df["composite_score"] = sum(
        df[metric] * weight for metric, weight in metrics.items()
    )

    # --- Rank within each quarter ---
    df["composite_rank"] = (
        df.groupby("REPDTE")["composite_score"]
        .rank(method="first", ascending=False)
    )

    # --- Rolling 4 quarter score ---
    df["score_rolling_4q"] = (
        df.sort_values("REPDTE")
            .groupby("Ticker")["composite_score"]
            .rolling(4)
            .mean()
            .reset_index(level=0, drop=True)
    )

    # --- Rolling 4 quarter score rank ---
    df["rolling_4q_rank"] = (
        df.groupby("REPDTE")["score_rolling_4q"]
        .rank(method="first", ascending=False)
    )

    return df