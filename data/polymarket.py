from zoneinfo import ZoneInfo

import requests
import json
import datetime as dt

et_day = dt.datetime.now(ZoneInfo("America/New_York")).day


GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"

# 1. Gamma: find the event and get each strike's YES token

resp = requests.get(
    f"{GAMMA}/events",
    params={f"slug": f"bitcoin-above-on-november-{et_day}-2026"},
    timeout=20,
)
resp.raise_for_status()
events = resp.json()

btc_data = []
for event in events:
    for market in event["markets"]:
        if not market.get("active") or market.get("closed"):
            continue

        outcomes = json.loads(market["outcomes"])
        token_ids = json.loads(market["clobTokenIds"])
        yes_token = token_ids[outcomes.index("Yes")]
        strike_str = market["question"].split("$")[1].split(" ")[0]
        strike = int(strike_str.replace(",", ""))  # "94,000" -> 94000

        btc_data.append({"strike": strike, "yes_token": yes_token})

btc_data.sort(key=lambda d: d["strike"])

# 2. CLOB: get the order book for each YES token
for row in btc_data:
    r = requests.get(f"{CLOB}/book", params={"token_id": row["yes_token"]}, timeout=20)
    r.raise_for_status()
    book = r.json()

    bids = [float(b["price"]) for b in book.get("bids", [])]
    asks = [float(a["price"]) for a in book.get("asks", [])]

    row["bid"] = max(bids) if bids else None  # best bid = highest
    row["ask"] = min(asks) if asks else None  # best ask = lowest

for row in btc_data:
    print(row["strike"], row["bid"], row["ask"])
