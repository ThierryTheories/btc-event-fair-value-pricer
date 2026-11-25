from btcfv import deribit, polymarket
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import time


def save(df, venue, ts):
    path = Path(f"data/raw/{venue}/{ts:%Y-%m-%d}.parquet")

    if path.exists():
        old = pd.read_parquet(path)
        df = pd.concat([old, df], ignore_index=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def snapshot_all():
    ts = datetime.now(timezone.utc)
    n_poly = 0
    n_dbit = 0
    # test polymarket
    try:
        poly = polymarket.snapshot()
        if not poly.empty:
            poly["ts"] = ts
            save(poly, "poly", ts)
            n_poly = len(poly)
    except Exception as e:
        print(f"Polymarket error~! at {ts} : {e}")
    # test deribit
    try:
        dbit = deribit.snapshot()
        if not dbit.empty:
            dbit["ts"] = ts
            save(dbit, "dbit", ts)
            n_dbit = len(dbit)
    except Exception as e:
        print(f"Deribit Error~! at {ts} : {e}")

    return n_poly, n_dbit


if __name__ == "__main__":

    while True:
        current = datetime.now()
        n_poly, n_dbit = snapshot_all()
        print(
            f"Saved {n_poly} polymarket rows, {n_dbit} deribit rows at {current.strftime("%H:%M")}"
        )
        time.sleep(300 - time.time() % 300)
