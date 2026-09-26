"""Data Engine: kho du lieu append-only, giu ban quan sat dau tien (point-in-time).
Kho giu GIA GOC lam bang chung. Moi tinh toan (feature, nhan, paper, Ledger) dung GIA DIEU CHINH tu load_market()."""
import datetime as dt
import numpy as np, pandas as pd
from .config import CFG, path
from . import adjust

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

FETCHERS = {"vnstock": lambda t, s, e: _fetch_vnstock(t, s, e, CFG["data"]["vnstock_source"]),
            "yahoo": _fetch_yahoo}

def ingest(end=None):
    """Tai gia theo thu tu nguon trong config (data.sources); nguon sau chi dung khi nguon truoc loi.
    Ghi ro nguon cua tung dong. Tra ve nhat ky DAY DU: loi tung ma, tung nguon (khong chi in ra log)."""
    store = load_store()
    now = pd.Timestamp.now(tz="UTC").tz_localize(None)
    end = (end or dt.date.today()).isoformat()
    sources = list(CFG["data"]["sources"])
    frames, errors, no_new = [], [], []
    for t in CFG["universe"]:
        last = store.loc[store.ticker == t, "date"].max() if len(store) else pd.NaT
        start = (last + pd.Timedelta(days=1)).date().isoformat() if pd.notna(last) else CFG["data"]["start"]
        if start > end:
            continue
        q, used = None, None
        for name in sources:
            try:
                q = _norm(FETCHERS[name](t, start, end), t)
                if q is not None and len(q):
                    used = name
                    break
            except Exception as e:
                errors.append({"ticker": t, "source": name, "error": str(e)[:300]})
        if q is None or not len(q):
            no_new.append(t)
            continue
        q["observed_at"], q["source"] = now, used
        frames.append(q)
    new = pd.concat(frames, ignore_index=True) if frames else None
    store = append_rows(store, new)
    errors += fetch_yahoo_actions()
    if store.empty:
        raise RuntimeError("Khong lay duoc du lieu tu nguon nao.\n" + "\n".join(map(str, errors[:20])))
    save_store(store)
    return {"at": now.isoformat(), "end": end, "sources": sources,
            "new_rows": 0 if new is None else len(new),
            "rows_by_source": {} if new is None else new.source.value_counts().to_dict(),
            "tickers_no_new_data": no_new, "errors": errors,
            "last_date_by_ticker": {t: str(d.date()) for t, d in store.groupby("ticker").date.max().items()}}

ingest_vnstock = ingest          # ten cu, giu de tuong thich

def fetch_yahoo_actions():
    """Tai lai TOAN BO lich su co tuc tien / chia tach tu Yahoo (du lieu dan xuat, ghi de moi lan, ghi ngay tai)."""
    try:
        import yfinance as yf
    except Exception as e:
        return [{"ticker": "*", "source": "yahoo_actions", "error": f"khong co yfinance ({e})"}]
    now = pd.Timestamp.now(tz="UTC").tz_localize(None).isoformat()
    rows, errors = [], []
    for t in CFG["universe"]:
        try:
            a = yf.Ticker(f"{t}.VN").actions
        except Exception as e:
            errors.append({"ticker": t, "source": "yahoo_actions", "error": str(e)[:300]}); continue
        if a is None or a.empty:
            continue
        for d, r in a.iterrows():
            ex = pd.Timestamp(d).tz_localize(None).normalize() if pd.Timestamp(d).tzinfo else pd.Timestamp(d).normalize()
            if r.get("Dividends", 0) > 0:
                rows.append({"ticker": t, "ex_date": ex.date(), "type": adjust.CASH, "ratio": None,
                             "cash_per_share": float(r["Dividends"]), "source": "yahoo", "source_status": "TU_DONG",
                             "note": "", "fetched_at": now})
            if r.get("Stock Splits", 0) > 0:
                rows.append({"ticker": t, "ex_date": ex.date(), "type": "stock_split", "ratio": float(r["Stock Splits"]),
                             "cash_per_share": None, "source": "yahoo", "source_status": "TU_DONG",
                             "note": "", "fetched_at": now})
    if rows or not errors:
        pd.DataFrame(rows, columns=adjust.EV_COLS + ["fetched_at"]).to_csv(
            path(CFG["corporate_actions"]["yahoo_cache"]), index=False)
    return errors

def load_market(as_of=None):
    """Bang gia DIEU CHINH point-in-time + co loi du lieu + bao cao chat luong.
    Tra ve dict: close, volume (dieu chinh), raw_close, bad (co loi), events, quality, flags."""
    s = load_store()
    if s.empty:
        raise RuntimeError("Kho du lieu trong. Chay ingest hoac tao du lieu synthetic.")
    if as_of is not None:
        s = s[s.date <= pd.Timestamp(as_of)]
    raw = s.pivot(index="date", columns="ticker", values="close").sort_index()
    vol = s.pivot(index="date", columns="ticker", values="volume").sort_index()
    obs = s.pivot(index="date", columns="ticker", values="observed_at").sort_index()
    keep = raw.columns[raw.notna().sum() > 250]
    raw, vol, obs = raw[keep], vol[keep], obs[keep]
    events = adjust.build_events(raw, obs, adjust.load_manual(), adjust.load_yahoo())
    F, S = adjust.factors(raw.index, raw.columns, events)
    adj = raw * F
    bad, rep, flags = adjust.quality(adj)
    rep["events"] = events.status.value_counts().to_dict() if len(events) else {}
    rep["events_not_applied"] = [f"{e.ticker} {e.ex_date.date()} {e.type} ({e.source}): {e.status}"
                                 for e in events.itertuples() if e.status not in ("APPLIED", "CHUA_DEN_HAN",
                                                                                  "DA_NAM_TRONG_GIA_NGUON")]
    rep["events_applied"] = [f"{e.ticker} {e.trade_date.date()} {e.type} ({e.source}, {e.source_status}): "
                             f"gốc {e.raw_return:+.2%} → điều chỉnh {e.adj_return:+.2%}"
                             for e in events.itertuples() if e.status == "APPLIED"]
    return {"close": adj.ffill(limit=5), "volume": (vol / S).fillna(0), "raw_close": raw, "bad": bad,
            "events": events, "quality": rep, "flags": flags}

def write_derived(mk=None):
    """Ghi du lieu DAN XUAT (tinh lai toan bo, ghi de, co ngay tinh): he so dieu chinh + co loi du lieu."""
    mk = mk or load_market()
    now = pd.Timestamp.now(tz="UTC").tz_localize(None).isoformat()
    ev = mk["events"].copy()
    ev["computed_at"] = now
    ev.to_csv(path(CFG["corporate_actions"]["derived"]), index=False)
    fl = pd.DataFrame(mk["flags"], columns=["date", "ticker", "return", "allowed"])
    fl["computed_at"] = now
    fl.to_csv(path(CFG["quality"]["flags_file"]), index=False)
    return now

def load_panel(as_of=None):
    """Tuong thich nguoc: (close, volume) DA DIEU CHINH."""
    mk = load_market(as_of)
    return mk["close"], mk["volume"]
