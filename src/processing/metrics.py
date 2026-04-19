import pandas as pd
import numpy as np


def clean_fdic_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Remove FDIC prefix
    df.columns = [col.replace("data.", "") for col in df.columns]

    # Drop redundant ID and score column
    df = df.drop(columns=["ID"], errors="ignore")
    df = df.drop(columns=["score"], errors="ignore") 

    return df


def enforce_numeric_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    numeric_cols = [
        "ASSET",
        "DEP",
        "LNLSNET",
        "EQ",
        "NETINC",
        "ROA",
        "ROE",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def compute_bank_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_fdic_columns(df)
    df = enforce_numeric_types(df)
    df["ROA"] = df["ROA"] / 100
    df["ROE"] = df["ROE"] / 100

    df = df.copy()

    # --- Balance Sheet Structure ---
    df["loan_to_deposit"] = df["LNLSNET"] / df["DEP"]
    df["equity_to_assets"] = df["EQ"] / df["ASSET"]

    # --- Profitability ---
    df["roa_calc"] = df["NETINC"] / df["ASSET"]
    df["roe_calc"] = df["NETINC"] / df["EQ"]

    # Compare to FDIC reported values
    df["roa_diff"] = df["roa_calc"] - df["ROA"]
    df["roe_diff"] = df["roe_calc"] - df["ROE"]

    # --- Scale ---
    df["log_assets"] = np.log(df["ASSET"])

    return df