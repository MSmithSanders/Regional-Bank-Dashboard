from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

from src.config import FDIC_API_KEY

FDIC_BASE_URL = "https://api.fdic.gov/banks"


class FDICClient:
    def __init__(self, api_key: str | None = None, timeout: int = 30) -> None:
        self.api_key = api_key or FDIC_API_KEY
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json"
        })

    def _get(self, endpoint: str, params: dict) -> dict:
        url = f"{FDIC_BASE_URL}/{endpoint}"
        if self.api_key:
            params["api_key"] = self.api_key

        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_financials_by_cert(
        self,
        cert: str,
        fields: list[str],
        limit: int = 10000,
        offset: int = 0,
        sort_by: str = "REPDTE",
        sort_order: str = "DESC",
    ) -> dict:
        params = {
            "filters": f'CERT:{cert}',
            "fields": ",".join(fields),
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
        return self._get("financials", params)

    def get_institutions_by_cert(
        self,
        cert: str,
        fields: list[str],
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        params = {
            "filters": f'CERT:{cert}',
            "fields": ",".join(fields),
            "limit": limit,
            "offset": offset,
        }
        return self._get("institutions", params)


def extract_rows(response_json: dict) -> list[dict]:
    """
    FDIC responses usually store returned records in `data`.
    """
    return response_json.get("data", [])


def fetch_financial_history_for_control_table(
    control_df: pd.DataFrame,
    fields: list[str],
) -> pd.DataFrame:
    """
    Pull financial history for each FDIC certificate in the control table.
    """
    client = FDICClient()
    all_rows: list[dict] = []

    for _, row in control_df.iterrows():
        ticker = row["Ticker"]
        cert = str(row["FDIC_cert"]).strip()

        response = client.get_financials_by_cert(cert=cert, fields=fields)
        records = extract_rows(response)

        for record in records:
            record["Ticker"] = ticker
            record["Control_FDIC_cert"] = cert
            record["Holding_Company_Name"] = row["Holding_Company_Name"]
            record["Primary_Bank_Sub_Name"] = row["Primary_Bank_Sub_Name"]
            all_rows.append(record)

    return pd.json_normalize(all_rows)