import pandas as pd


def compute_peer_metrics(df: pd.DataFrame, metrics: list) -> pd.DataFrame:
    df = df.copy()

    # Ensure date is datetime
    df["REPDTE"] = pd.to_datetime(df["REPDTE"], errors="coerce")

    # --- Percentile ranks ---
    for metric in metrics:
        df[f"{metric}_pct"] = (
            df.groupby("REPDTE")[metric]
            .rank(pct=True)
        )

    # --- Z-scores ---
    for metric in metrics:
        df[f"{metric}_z"] = (
            df.groupby("REPDTE")[metric]
            .transform(lambda x: (x - x.mean()) / x.std())
        )

    return df