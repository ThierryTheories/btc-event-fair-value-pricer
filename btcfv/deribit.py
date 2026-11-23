import json
from datetime import UTC, date, datetime, timedelta, timezone

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


def option_chain(curr_price):
    r = S.get(
        f"{DERIBIT}/get_book_summary_by_currency",
        params={"currency": "BTC", "kind": "option"},
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()
    rows = []
    today = datetime.now(timezone.utc)
    for opt in data["result"]:
        parse_instrument = opt["instrument_name"].split("-")
        exp_date_parsed = datetime.strptime(parse_instrument[1], "%d%b%y").replace(
            hour=8, tzinfo=timezone.utc
        )
        strike_price = int(parse_instrument[2])

        # we take 14 days because theres a missalignment, theres no daily expiration
        if (
            today <= exp_date_parsed <= today + timedelta(days=14)
            and curr_price * 0.75 <= strike_price <= curr_price * 1.25
        ):
            rows.append(
                {
                    "instrument": opt["instrument_name"],
                    "expiry_date": exp_date_parsed,
                    "strike_price": strike_price,
                    "mark_price": opt["mark_price"],
                    "underlying_price": opt["underlying_price"],
                    "option": parse_instrument[3],
                    "ask": opt["ask_price"],
                    "bid": opt["bid_price"],
                    "mark_iv": opt["mark_iv"],
                }
            )
    return rows


if __name__ == "__main__":
    print(option_chain(index_price()))
