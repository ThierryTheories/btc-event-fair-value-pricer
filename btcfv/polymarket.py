"""Polymarket side: find open 'Bitcoin above ___' events and read their YES order books."""

import json
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import requests

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
S = requests.Session()  # reuses the connection across calls

MONTHS = ["january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"]


def slug_for(d: date) -> str:
    """date(2026, 11, 22) -> 'bitcoin-above-on-november-22-2026'"""
    return f"bitcoin-above-on-{MONTHS[d.month - 1]}-{d.day}-{d.year}"


def event_slugs(today: date, days_ahead: int = 7) -> list[str]:
    """Today plus the next 7 days: each event opens about a week before it resolves."""
    return [slug_for(today + timedelta(days=i)) for i in range(days_ahead + 1)]


def discover(slugs: list[str]) -> list[dict]:
    """Gamma: one row per open strike, with its YES token."""
    rows = []
    for slug in slugs:
        r = S.get(f"{GAMMA}/events", params={"slug": slug}, timeout=20)
        r.raise_for_status()
        for event in r.json():  # empty list if the event doesn't exist yet
            for m in event["markets"]:
                if not m.get("active") or m.get("closed"):
                    continue
                outcomes = json.loads(m["outcomes"])     # '["Yes", "No"]' -> list
                tokens = json.loads(m["clobTokenIds"])
                rows.append({
                    "event_slug": slug,
                    "end_date": m["endDate"],
                    "strike": int(m["groupItemTitle"].replace(",", "")),  # "64,000" -> 64000
                    "yes_token": tokens[outcomes.index("Yes")],
                    "condition_id": m["conditionId"],
                })
    return rows


def books(tokens: list[str]) -> dict[str, dict]:
    """CLOB: every order book in one request, keyed by token id."""
    r = S.post(f"{CLOB}/books", json=[{"token_id": t} for t in tokens], timeout=20)
    r.raise_for_status()
    out = {}
    for b in r.json():
        bids = [(float(x["price"]), float(x["size"])) for x in b.get("bids", [])]
        asks = [(float(x["price"]), float(x["size"])) for x in b.get("asks", [])]
        best_bid = max(bids) if bids else (None, None)  # highest price someone pays
        best_ask = min(asks) if asks else (None, None)  # lowest price someone sells
        out[b["asset_id"]] = {
            "bid": best_bid[0], "bid_size": best_bid[1],
            "ask": best_ask[0], "ask_size": best_ask[1],
            "book_ts": b.get("timestamp"),
        }
    return out


def snapshot() -> pd.DataFrame:
    """One Polymarket snapshot of every open BTC 'above' strike."""
    ts = datetime.now(timezone.utc)
    markets = discover(event_slugs(ts.date()))
    if not markets:
        return pd.DataFrame()
    quotes = books([m["yes_token"] for m in markets])
    df = pd.DataFrame([{**m, **quotes.get(m["yes_token"], {})} for m in markets])
    df["ts"] = ts
    return df.sort_values(["end_date", "strike"]).reset_index(drop=True)


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    df = snapshot()
    print(df[["event_slug", "strike", "bid", "ask", "bid_size", "ask_size"]].to_string())
    print(f"\n{len(df)} strikes across {df['event_slug'].nunique()} events at {df['ts'].iloc[0]:%Y-%m-%d %H:%M} UTC")
