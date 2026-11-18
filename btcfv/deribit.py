import json
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import requests

DERIBIT = "https://www.deribit.com/api/v2/public"

S = requests.Session()


def index_price() -> float:
    """Current BTC/USD index price from Deribit."""
    r = S.get(
        f"{DERIBIT}/get_index_price", params={"index_name": "btc_usd"}, timeout=20
    )
    r.raise_for_status()
    data = r.json()
    return data["result"]["index_price"]


if __name__ == "__main__":
    print(index_price())
