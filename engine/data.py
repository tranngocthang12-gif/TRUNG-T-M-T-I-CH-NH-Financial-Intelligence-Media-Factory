"""Data Engine: kho dữ liệu append-only, giữ bản quan sát đầu tiên (point-in-time)."""
import datetime as dt
import numpy as np, pandas as pd
from .config import CFG, path

COLS = ["date", "ticker", "open", "high", "low", "close", "volume", "observed_at", "source"]

def load_store():
    p = path(CFG["data"]["store"])
    if not p.exists():
        return pd.DataFrame(columns=COLS)
    return pd.read_csv(p, parse_dates=["date", "observed_at"])

def save_store(df):
    df.sort_values(["date", "ticker"]).to_csv(path(CFG["data"]["store"]), index=False, compression="gzip")

def append_rows(store, new):
    """Append-only: nếu một (date, ticker) đã có, giữ bản quan sát ĐẦU TIÊN, không ghi đè quá khứ."""
    if new is None or new.empty:
        return store
    allr = pd.concat([store, new[COLS]], ignore_index=True) if len(store) else new[COLS].copy()
    return allr.sort_values("observed_at").drop_duplicates(["date", "ticker"], keep="first")

def ingest_vnstock(end=None):
    try:
        from vnstock import Vnstock
    except ImportError as e:
        raise RuntimeError("Chưa cài vnstock: pip install vnstock") from e
    store = load_store()
    now = pd.Timestamp.now(tz="UTC").tz_localize(None)
    end = (end or dt.date.today()).isoformat()
    src = CFG["data"]["vnstock_source"]
    frames, errors = [], []
    for t in CFG["universe"]:
        last = store.loc[store.ticker == t, "date"].max() if len(store) else pd.NaT
        start = (last + pd.Timedelta(days=1)).date().isoformat() if pd.notna(last) else CFG["data"]["start"]
        if start > end:
            continue
        try:
            q = Vnstock().stock(symbol=t, source=src).quote.history(start=start, end=end, interval="1D")
        except Exception as e:
            errors.append(f"{t}: {e}")
            continue
        if q is None or q.empty:
            continue
        q = q.rename(columns={"time": "date"})
        q["date"] = pd.to_datetime(q["date"]).dt.normalize()
        q["ticker"], q["observed_at"], q["source"] = t, now, f"vnstock:{src}"
        frames.append(q)
    new = pd.concat(frames, ignore_index=True) if frames else None
    store = append_rows(store, new)
    save_store(store)
    return {"new_rows": 0 if new is None else len(new), "errors": errors}

def load_panel(as_of=None):
    s = load_store()
    if s.empty:
        raise RuntimeError("Kho dữ liệu trống. Chạy ingest hoặc tạo dữ liệu synthetic.")
    if as_of is not None:
        s = s[s.date <= pd.Timestamp(as_of)]
    close = s.pivot(index="date", columns="ticker", values="close").sort_index().ffill(limit=5)
    volume = s.pivot(index="date", columns="ticker", values="volume").sort_index().fillna(0)
    keep = close.columns[close.notna().sum() > 250]
    return close[keep], volume[keep]
