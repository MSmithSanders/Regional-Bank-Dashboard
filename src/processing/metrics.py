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

def compute_credit_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Remove FDIC JSON-normalize prefix
    df.columns = [col.replace("data.", "") for col in df.columns]

    numeric_cols = [
        "LNLSNET",    # loans and leases, net
        "NCLNLS",     # noncurrent loans and leases
        "NTLNLSQR",   # net charge-offs to loans and leases, quarterly %
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    required_cols = ["LNLSNET", "NCLNLS", "NTLNLSQR"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required FDIC credit columns: {missing}")

    # Avoid divide-by-zero
    df["LNLSNET"] = df["LNLSNET"].replace(0, np.nan)

    # Stock credit risk: noncurrent loans / loans
    df["npl_ratio"] = df["NCLNLS"] / df["LNLSNET"]

    # Flow credit risk: FDIC reports this as a percent, so convert to decimal
    df["chargeoff_ratio"] = df["NTLNLSQR"] / 100.0

    #  Robustness caps
    npl_cap = df["npl_ratio"].quantile(0.99)
    chargeoff_cap = df["chargeoff_ratio"].quantile(0.99)

    df["npl_ratio"] = df["npl_ratio"].clip(upper=npl_cap)
    df["chargeoff_ratio"] = df["chargeoff_ratio"].clip(upper=chargeoff_cap)

    return df