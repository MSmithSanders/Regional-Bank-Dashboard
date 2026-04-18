from pathlib import Path
import pandas as pd


def validate_control_table(path: Path) -> None:
    df = pd.read_csv(path, dtype={"CIK": "string"})

    print(f"Row count: {len(df)}")
    print(f"Columns: {list(df.columns)}")

    missing_cik = df[df["CIK"].isna() | (df["CIK"].astype(str).str.strip() == "")]
    if missing_cik.empty:
        print("No missing CIK values.")
    else:
        print("Missing CIK values:")
        print(missing_cik[["Ticker", "Holding_Company_Name"]].to_string(index=False))

    cik_str = df["CIK"].astype(str).str.strip()
    bad_format = df[~cik_str.str.fullmatch(r"\d{10}", na=False)]
    if bad_format.empty:
        print("All CIK values are 10 digits.")
    else:
        print("CIKs with bad format:")
        print(bad_format[["Ticker", "CIK"]].to_string(index=False))

    duplicates = df[df["Ticker"].duplicated(keep=False)]
    if duplicates.empty:
        print("No duplicate tickers.")
    else:
        print("Duplicate tickers found:")
        print(duplicates[["Ticker", "Holding_Company_Name"]].to_string(index=False))

    print("\nPreview:")
    print(
        df[
            [
                "Ticker",
                "Holding_Company_Name",
                "SEC_Company_Name",
                "Primary_Bank_Sub_Name",
                "FDIC_cert",
                "RSSD_ID",
                "CIK",
            ]
        ].head(10).to_string(index=False)
    )


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    path = project_root / "data" / "control" / "RegionalBankControlTable_with_CIK.csv"
    validate_control_table(path)


if __name__ == "__main__":
    main()