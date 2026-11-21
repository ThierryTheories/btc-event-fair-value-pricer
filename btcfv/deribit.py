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


# POLYMARKET Expires 17.00 UTC ,Deribit Options 08:00 UTC

# def discover(slugs: list[str]) -> list[dict]:
#     """Gamma: one row per open strike, with its YES token."""
#     rows = []
#     for slug in slugs:
#         r = S.get(f"{GAMMA}/events", params={"slug": slug}, timeout=20)
#         r.raise_for_status()
#         for event in r.json():  # empty list if the event doesn't exist yet
#             for m in event["markets"]:
#                 if not m.get("active") or m.get("closed"):
#                     continue
#                 outcomes = json.loads(m["outcomes"])  # '["Yes", "No"]' -> list
#                 tokens = json.loads(m["clobTokenIds"])
#                 rows.append(
#                     {
#                         "event_slug": slug,
#                         "end_date": m["endDate"],
#                         "strike": int(
#                             m["groupItemTitle"].replace(",", "")
#                         ),  # "64,000" -> 64000
#                         "yes_token": tokens[outcomes.index("Yes")],
#                         "condition_id": m["conditionId"],
#                     }
#                 )
#     return rows
def option_chain():
    r = S.get(
            f"{DERIBIT}/get_book_summary_by_currency", params={"currency": "BTC", "kind" : "option"}, timeout=20
        )
    r.raise_for_status()
    data = r.json()
    rows = []
    for opt in data["result"]:
        parse_instrument = opt["instrument_name"].split("-")
        rows.append(
            {
                "instrument" : opt["instrument_name"],
                "expiry_date" : parse_instrument[1],
                "strike_price" : int(parse_instrument[2]),
                "mark_price" : opt['mark_price'],
                "underlying_price" : opt["underlying_price"],
                "option" : parse_instrument[3],
                "ask" : opt['ask_price'],
                "bid" : opt['bid_price'],
                "mark_iv" : opt['mark_iv']


            }
        )
    return rows











if __name__ == "__main__":
    print(index_price())
    print(option_chain())
