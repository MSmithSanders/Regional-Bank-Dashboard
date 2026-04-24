from __future__ import annotations

from pathlib import Path
import pandas as pd


def load_ffiec_tab_file(path: Path, sep: str = "\t") -> pd.DataFrame:
    """
    Load a tab-delimited FFIEC bulk file.
    """
    return pd.read_csv(path, sep=sep, dtype="string", low_memory=False)


def normalize_ffiec_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize FFIEC column names for easier downstream handling.
    """
    out = df.copy()
    out.columns = [c.strip() for c in out.columns]
    return out


def parse_reporting_date(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col], errors="coerce")
    return out


def coerce_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def merge_ffiec_to_control(
    ffiec_df: pd.DataFrame,
    control_df: pd.DataFrame,
    ffiec_cert_col: str | None = None,
    ffiec_rssd_col: str | None = None,
) -> pd.DataFrame:
    """
    Merge FFIEC data to your control table using FDIC cert or RSSD.
    """
    control = control_df.copy()

    if ffiec_cert_col and ffiec_cert_col in ffiec_df.columns:
        merged = ffiec_df.merge(
            control,
            left_on=ffiec_cert_col,
            right_on="FDIC_cert",
            how="inner",
        )
        return merged

    if ffiec_rssd_col and ffiec_rssd_col in ffiec_df.columns:
        merged = ffiec_df.merge(
            control,
            left_on=ffiec_rssd_col,
            right_on="RSSD_ID",
            how="inner",
        )
        return merged

    raise ValueError("No valid merge key found. Check FFIEC cert/RSSD column names.")