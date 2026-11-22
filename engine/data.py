"""Data Engine: kho du lieu append-only, giu ban quan sat dau tien (point-in-time).
Kho giu GIA GOC lam bang chung. Moi tinh toan (feature, nhan, paper, Ledger) dung GIA DIEU CHINH tu load_market().

Ghi TANG DAN (ADR-0006, C2): kho cu `data.store` (prices.csv.gz) DONG BANG — khong ghi lai nua. Dong moi vao
`data.store_dir`, moi thang giao dich mot tep CSV `YYYY-MM.csv`; chi NOI THEM vao cuoi tep (thu tu = thu tu quan sat),
khong bao gio viet lai dong cu. tools/ledger_audit.py kiem: kho cu khong doi, moi tep thang cu la tien to cua ban moi."""
import datetime as dt
import hashlib
import json
import pathlib
import numpy as np, pandas as pd
from . import config
from .config import CFG, path
from . import adjust
from . import verified_adjust as va

COLS = ["date", "ticker", "open", "high", "low", "close", "volume", "observed_at", "source"]

def _root(root):
    return pathlib.Path(root) if root is not None else config.ROOT

def load_store(root=None):
    """Kho cu (dong bang) + moi tep thang; trung (date, ticker) thi giu ban quan sat DAU TIEN."""
    r, parts = _root(root), []
    legacy = r / CFG["data"]["store"]
    if legacy.exists():
        parts.append(pd.read_csv(legacy))
    d = r / CFG["data"]["store_dir"]
    if d.is_dir():
        parts += [pd.read_csv(f) for f in sorted(d.glob("*.csv"))]
    parts = [x for x in parts if len(x)]
    if not parts:
        return pd.DataFrame(columns=COLS)
    s = pd.concat(parts, ignore_index=True)[COLS]
    for c in ("date", "observed_at"):     # mot tep co the co ca "YYYY-MM-DD" lan "YYYY-MM-DD HH:MM:SS.ffffff"
        s[c] = pd.to_datetime(s[c], format="ISO8601")
    s = s.sort_values("observed_at", kind="stable").drop_duplicates(["date", "ticker"], keep="first")
    return s.sort_values(["date", "ticker"], kind="stable").reset_index(drop=True)

def save_store(df, root=None):
    """Ghi TANG DAN (ADR-0006): chi them dong (date, ticker) chua co trong kho, noi vao cuoi tep thang cua ngay giao dich.
    Dong da co thi GIU NGUYEN ban cu (diem-thoi-gian: ban quan sat dau tien) — truyen vao gia da sua cung khong ghi de.
    Tra ve so dong da them."""
    if df is None or len(df) == 0:
        return 0
    r = _root(root)
    have = load_store(r)
    keys = set(zip(have["date"], have["ticker"])) if len(have) else set()
    df = df[COLS].copy()
    df["date"], df["observed_at"] = pd.to_datetime(df["date"]), pd.to_datetime(df["observed_at"])
    new = df[[(d, t) not in keys for d, t in zip(df["date"], df["ticker"])]]
    new = new.sort_values("observed_at", kind="stable").drop_duplicates(["date", "ticker"], keep="first")
    if new.empty:
        return 0
    d = r / CFG["data"]["store_dir"]
    d.mkdir(parents=True, exist_ok=True)
    new = new.sort_values(["observed_at", "date", "ticker"], kind="stable")
    for month, g in new.groupby(new["date"].dt.strftime("%Y-%m"), sort=True):
        f = d / f"{month}.csv"
        g.to_csv(f, mode="a", header=not f.exists(), index=False)
    return len(new)

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

RESEARCH_INPUTS = ("legacy", "verified")
EVIDENCE_DIR = ("data", "evidence", "corporate_actions")
NOT_IN_CHAIN = "KHONG_VAO_CHUOI_KIEM_CHUNG"


def evidence_docs(root=None):
    """Mọi bản gốc trong các tệp EVIDENCE_MANIFEST*.json dưới data/evidence/corporate_actions/, đọc theo thứ tự tên tệp.
    Đây là nơi DUY NHẤT đầu vào nghiên cứu đọc bản gốc (không dùng DEFAULT_EVIDENCE của tools/build_verified_derivation.py,
    vốn chỉ có manifest đầu)."""
    d = _root(root).joinpath(*EVIDENCE_DIR)
    return va.load_evidence(sorted(d.glob("EVIDENCE_MANIFEST*.json"), key=lambda p: p.name)) if d.is_dir() else []


def window_bounds():
    """(trước, sau) của cửa sổ loại mã QĐ-3 (ADR-0016): trước = horizon_days + 1 (nhãn tại t nhìn tới t + 1 + h, nên mọi
    nhãn chạm phiên sự kiện bị loại); sau = quality.feature_lookback − 1 (đặc trưng nhìn lại ngần ấy phiên kể cả t)."""
    return int(CFG["horizon_days"]) + 1, int(CFG["quality"]["feature_lookback"]) - 1


def window_exclude(index, columns, checks, before, after):
    """Mặt nạ QĐ-3: ô (t, mã) là True khi vị trí của t trên trục ngày `index` thuộc [k − before, k + after], với k là vị trí
    phiên áp dụng của một sự kiện có `taints` của mã đó. Sự kiện lệch ngày: hợp của cửa sổ quanh ngày engine (`trade_date`)
    và quanh ngày chính thức (`official_trade_date`, không có thì `official_ex_date`). Vị trí của một ngày là phiên đầu tiên
    trên trục không sớm hơn ngày đó; ngày sau phiên cuối có vị trí len(index)."""
    index = pd.DatetimeIndex(index)
    m = np.zeros((len(index), len(columns)), dtype=bool)
    col = {t: j for j, t in enumerate(columns)}
    for r in checks[checks["taints"].astype(bool)].itertuples(index=False):
        j = col.get(r.ticker)
        if j is None:
            continue
        days = [r.trade_date, r.official_trade_date if pd.notna(r.official_trade_date) else r.official_ex_date]
        for k in {pd.Timestamp(x) for x in days if pd.notna(x)}:
            pos = int(index.searchsorted(k))
            lo, hi = max(0, pos - before), min(len(index) - 1, pos + after)
            if lo <= hi:
                m[lo:hi + 1, j] = True
    return pd.DataFrame(m, index=index, columns=columns)


def _derivation_id(research_input, cut, docs, ev):
    """Định danh dẫn xuất chỉ phụ thuộc đầu vào: chế độ, ngày cắt, hash kho giá, hash CSV sự kiện, metadata mọi bản gốc,
    config (tệp và giá trị đang dùng). Dùng lại verified_adjust.derivation_manifest; code_commit để trống."""
    m = va.derivation_manifest(root=config.ROOT, cfg=CFG, as_of=cut, docs=docs, ev=ev, code_commit=None)
    cfg_now = hashlib.sha256(json.dumps(CFG, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()
    key = {"research_input": research_input, "verified_derivation_id": m["derivation_id"], "config_values": cfg_now}
    return "RI-" + hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:16]


def load_market(as_of=None, research_input="legacy"):
    """Bang gia DIEU CHINH point-in-time + co loi du lieu + bao cao chat luong.
    Tra ve dict: close, volume (dieu chinh), raw_close, bad (co loi), events, quality, flags.

    research_input (E2a, QĐ-1 và QĐ-3 của ADR-0016):
      - "legacy" (mặc định): chuỗi điều chỉnh hiện hành của engine.adjust; mọi khóa cũ không đổi từng byte;
      - "verified": chỉ sự kiện cổ phiếu vào chuỗi kiểm chứng (engine.verified_adjust, bản gốc từ evidence_docs, ngày cắt là
        as_of hoặc phiên cuối) được áp hệ số; sự kiện không vào chuỗi không mang trạng thái APPLIED trong `events`. Thêm
        `exclude` (mặt nạ cửa sổ QĐ-3), `eligible` (có giá và không bị loại) và `event_checks` (bảng kiểm sự kiện).
    Cả hai chế độ thêm: research_input, derivation_id, pit_label (luôn "RETROSPECTIVE" ở bản này), pit_gaps."""
    if research_input not in RESEARCH_INPUTS:
        raise ValueError(f"research_input phải là một trong {RESEARCH_INPUTS}, không phải {research_input!r}")
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
    cut = pd.Timestamp(as_of) if as_of is not None else raw.index[-1]
    docs, checks = evidence_docs(), None
    if research_input == "verified":
        checks = va.verify_events(events, raw, docs, evidence_root=config.ROOT, as_of=cut)
        F, S = va.verified_factors(raw.index, raw.columns, checks)
        events = checks[list(events.columns)].copy()
        events.loc[(events["status"] == "APPLIED") & ~checks["in_verified_chain"].astype(bool), "status"] = NOT_IN_CHAIN
    else:
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
    out = {"close": adj.ffill(limit=5), "volume": (vol / S).fillna(0), "raw_close": raw, "bad": bad,
           "events": events, "quality": rep, "flags": flags}
    gaps = ["rổ theo cấu hình hiện tại (universe), chưa theo thành viên VN30 từng ngày",
            "trục ngày chưa lọc ngày nghỉ theo lịch phiên HOSE"]
    if research_input == "legacy":
        gaps.append("sự kiện quyền chưa kiểm: hệ số theo chuỗi điều chỉnh hiện hành, gồm sự kiện chưa đối chiếu bản gốc")
    out.update(research_input=research_input, derivation_id=_derivation_id(research_input, cut, docs,
                                                                             events if checks is None else checks),
               pit_label="RETROSPECTIVE", pit_gaps=gaps)
    if checks is not None:
        exclude = window_exclude(raw.index, raw.columns, checks, *window_bounds())
        out.update(exclude=exclude, eligible=raw.notna() & ~exclude, event_checks=checks)
    return out

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
