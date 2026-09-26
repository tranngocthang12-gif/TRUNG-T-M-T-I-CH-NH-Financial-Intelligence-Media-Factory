"""Data Engine: kho du lieu append-only, giu ban quan sat dau tien (point-in-time)."""
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
    """Append-only: neu mot (date, ticker) da co, giu ban quan sat DAU TIEN, khong ghi de qua khu."""
    if new is None or new.empty:
        return store
    allr = pd.concat([store, new[COLS]], ignore_index=True) if len(store) else new[COLS].copy()
    return allr.sort_values("observed_at").drop_duplicates(["date", "ticker"], keep="first")

def _norm(q, t):
    """Chuan hoa bang gia tu moi nguon ve cot date/open/high/low/close/volume."""
    if q is None or len(q) == 0:
        return None
    q = q.copy()
    if isinstance(q.columns, pd.MultiIndex):
        q.columns = q.columns.get_level_values(0)
    q = q.reset_index() if not any(str(c).lower() in ("time", "date", "tradingdate") for c in q.columns) else q
    q.columns = [str(c).lower() for c in q.columns]
    for k in ("time", "tradingdate", "index"):
        if k in q.columns and "date" not in q.columns:
            q = q.rename(columns={k: "date"})
    need = ["date", "open", "high", "low", "close", "volume"]
    if not all(c in q.columns for c in need):
        raise RuntimeError(f"thieu cot, nhan duoc {list(q.columns)}")
    q = q[need].dropna(subset=["close"])
    q["date"] = pd.to_datetime(q["date"]).dt.tz_localize(None).dt.normalize()
    q["ticker"] = t
    return q

def _fetch_vnstock(t, start, end, src):
    import vnstock
    if hasattr(vnstock, "Vnstock"):
        return vnstock.Vnstock().stock(symbol=t, source=src).quote.history(start=start, end=end, interval="1D")
    if hasattr(vnstock, "Quote"):
        return vnstock.Quote(symbol=t, source=src).history(start=start, end=end, interval="1D")
    if hasattr(vnstock, "stock_historical_data"):
        return vnstock.stock_historical_data(symbol=t, start_date=start, end_date=end, resolution="1D", type="stock")
    raise RuntimeError("khong nhan ra API cua phien ban vnstock nay")

def _fetch_yahoo(t, start, end):
    import yfinance as yf
    e = (pd.Timestamp(end) + pd.Timedelta(days=1)).date().isoformat()
    return yf.download(f"{t}.VN", start=start, end=e, auto_adjust=False, progress=False)

def ingest_vnstock(end=None):
    """Thu vnstock truoc, khong duoc thi dung Yahoo Finance (ma .VN). Ghi ro nguon cua tung dong."""
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
        q, used = None, None
        for name, fn in (("vnstock:" + src, lambda: _fetch_vnstock(t, start, end, src)),
                         ("yahoo", lambda: _fetch_yahoo(t, start, end))):
            try:
                q = _norm(fn(), t)
                if q is not None and len(q):
                    used = name
                    break
            except Exception as e:
                errors.append(f"{t} [{name}]: {str(e)[:160]}")
        if q is None or not len(q):
            continue
        q["observed_at"], q["source"] = now, used
        frames.append(q)
    new = pd.concat(frames, ignore_index=True) if frames else None
    store = append_rows(store, new)
    if store.empty:
        raise RuntimeError("Khong lay duoc du lieu tu nguon nao.\n" + "\n".join(errors[:20]))
    save_store(store)
    return {"new_rows": 0 if new is None else len(new), "errors": errors[:20]}

def load_panel(as_of=None):
    s = load_store()
    if s.empty:
        raise RuntimeError("Kho du lieu trong. Chay ingest hoac tao du lieu synthetic.")
    if as_of is not None:
        s = s[s.date <= pd.Timestamp(as_of)]
    close = s.pivot(index="date", columns="ticker", values="close").sort_index().ffill(limit=5)
    volume = s.pivot(index="date", columns="ticker", values="volume").sort_index().fillna(0)
    keep = close.columns[close.notna().sum() > 250]
    return close[keep], volume[keep]
