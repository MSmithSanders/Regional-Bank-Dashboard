import pandas as pd

from src.data.ffiec_loader import load_ffiec_data
from src.processing.metrics import compute_credit_metrics  # adjust import if needed


def main():
    df = load_ffiec_data(
        "data/raw/ffiec/FFIEC CDR Call Subset of Schedules 2025(1 of 2).txt",
        "data/raw/ffiec/FFIEC CDR Call Subset of Schedules 2025(2 of 2).txt",
    )

    control = pd.read_csv(
        "data/control/RegionalBankControlTable_with_CIK.csv",
        dtype={"RSSD_ID": "string", "FDIC_cert": "string", "Ticker": "string"}
    )

    # Normalize merge keys on both sides
    df["IDRSSD"] = (
        df["IDRSSD"]
        .astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )

    control["RSSD_ID"] = (
        control["RSSD_ID"]
        .astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )

    # Optional debug checks before merge
    print("Sample FFIEC IDRSSD values:")
    print(df["IDRSSD"].dropna().head(10).tolist())

    print("Sample control RSSD_ID values:")
    print(control["RSSD_ID"].dropna().head(10).tolist())

    print("FFIEC unique IDRSSD:", df["IDRSSD"].nunique())
    print("Control unique RSSD_ID:", control["RSSD_ID"].nunique())

    matches = set(df["IDRSSD"].dropna()) & set(control["RSSD_ID"].dropna())
    print("Number of overlapping RSSD IDs:", len(matches))
    print("Example overlaps:", list(sorted(matches))[:10])

    df = df.merge(
        control[["RSSD_ID", "Ticker"]],
        left_on="IDRSSD",
        right_on="RSSD_ID",
        how="inner"
    )

    print("Loaded FFIEC data:", df.shape)

    df = compute_credit_metrics(df)

    print("After credit metrics:", df.shape)

    output_path = "data/processed/ffiec_merged.csv"
    df.to_csv(output_path, index=False)

    print(f"Saved processed FFIEC data to {output_path}")


if __name__ == "__main__":
    main()