from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import requests

from src.config import SEC_USER_AGENT

SEC_TICKER_URL = "https://www.sec.gov/files/company_tickers.json"


def get_sec_ticker_map() -> pd.DataFrame:
    """Download the SEC ticker-to-CIK mapping."""
    if not SEC_USER_AGENT:
        raise ValueError(
            "SEC_USER_AGENT is not set in .env. "
            "Add something like: SEC_USER_AGENT=your_email@example.com"
        )

    headers = {"User-Agent": SEC_USER_AGENT}
    response = requests.get(SEC_TICKER_URL, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    sec_df = pd.DataFrame.from_dict(data, orient="index")

    sec_df["Ticker"] = sec_df["ticker"].astype(str).str.upper().str.strip()
    sec_df["CIK_from_SEC"] = sec_df["cik_str"].astype(int).astype(str).str.zfill(10)
    sec_df["SEC_Company_Name"] = sec_df["title"].astype(str).str.strip()

    return sec_df[["Ticker", "CIK_from_SEC", "SEC_Company_Name"]]


def update_control_table(input_path: Path, output_path: Path) -> None:
    """Read control table, merge SEC CIKs, and write updated CSV."""
    df = pd.read_csv(
        input_path,
        dtype={
            "CIK": "string",
            "RSSD_ID": "string",
            "FDIC_cert": "string"
        }
    )   

    required_columns = [
        "Ticker",
        "Holding_Company_Name",
        "Primary_Bank_Sub_Name",
        "FDIC_cert",
        "RSSD_ID",
        "CIK",
    ]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in control table: {missing}")

    df["Ticker"] = df["Ticker"].astype(str).str.upper().str.strip()

    # Clean existing CIK column
    df["CIK"] = df["CIK"].astype("string").str.strip()
    df["CIK"] = df["CIK"].replace({"": pd.NA, "nan": pd.NA, "<NA>": pd.NA})

    sec_df = get_sec_ticker_map()

    merged = df.merge(sec_df, on="Ticker", how="left")

    # Fill only missing CIK values from SEC
    merged["CIK"] = merged["CIK"].fillna(merged["CIK_from_SEC"])

    # Final formatting
    merged["CIK"] = merged["CIK"].astype("string")
    merged["CIK"] = merged["CIK"].where(
        merged["CIK"].isna(),
        merged["CIK"].str.replace(r"\.0$", "", regex=True).str.zfill(10),
    )

    # Reorder columns
    ordered_cols = [
        "Ticker",
        "Holding_Company_Name",
        "SEC_Company_Name",
        "Primary_Bank_Sub_Name",
        "FDIC_cert",
        "RSSD_ID",
        "CIK",
    ]
    other_cols = [col for col in merged.columns if col not in ordered_cols + ["CIK_from_SEC"]]
    merged = merged[ordered_cols + other_cols]

    # Report any unmatched tickers
    unmatched = merged.loc[merged["CIK"].isna(), "Ticker"].tolist()
    if unmatched:
        print("Tickers still missing CIK values:")
        for ticker in unmatched:
            print(f"  - {ticker}")
    else:
        print("All tickers matched successfully.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)
    print(f"Updated file written to: {output_path}")


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]

    input_path = project_root / "data" / "control" / "RegionalBankControlTable.csv"
    output_path = project_root / "data" / "control" / "RegionalBankControlTable_with_CIK.csv"

    try:
        update_control_table(input_path, output_path)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()