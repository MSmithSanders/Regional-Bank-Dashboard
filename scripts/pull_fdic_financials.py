from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.fdic_data import fetch_financial_history_for_control_table


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]

    control_path = (
        project_root / "data" / "control" / "RegionalBankControlTable_with_CIK.csv"
    )
    output_dir = project_root / "data" / "raw" / "fdic"
    output_dir.mkdir(parents=True, exist_ok=True)

    control_df = pd.read_csv(
        control_path,
        dtype={
            "Ticker": "string",
            "FDIC_cert": "string",
            "RSSD_ID": "string",
            "CIK": "string",
        },
    )

    # Keep this narrow for v1.
    fields = [
        "CERT",
        "NAME",
        "REPDTE",
        "ASSET",
        "DEP",
        "LNLSNET",
        "EQ",
        "NETINC",
        "ROA",
        "ROE",
        "NCLNLS",
        "NTLNLSQR"
    ]

    fdic_df = fetch_financial_history_for_control_table(
        control_df=control_df,
        fields=fields,
    )

    output_path = output_dir / "fdic_financials_raw.csv"
    fdic_df.to_csv(output_path, index=False)

    print(f"Saved {len(fdic_df)} rows to {output_path}")
    print("Columns returned:")
    print(sorted(fdic_df.columns.tolist()))


if __name__ == "__main__":
    main()