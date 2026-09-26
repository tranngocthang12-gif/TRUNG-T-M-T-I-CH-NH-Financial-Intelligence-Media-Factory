"""Điều chỉnh giá theo sự kiện quyền + kiểm tra chất lượng dữ liệu.

- Kho `data/store` giữ GIÁ GỐC append-only làm bằng chứng — module này KHÔNG sửa kho.
- Sự kiện quyền lấy từ: `data/corporate_actions.csv` (nhập tay, có nguồn, ưu tiên) và
  `data/derived/yahoo_actions.csv` (tải lại toàn bộ mỗi lần ingest).
- Hệ số điều chỉnh là DỮ LIỆU DẪN XUẤT, tính lại toàn bộ mỗi lần, POINT-IN-TIME: tại as_of chỉ dùng sự kiện có
  ngày giao dịch không hưởng quyền <= as_of, neo tại as_of (giá điều chỉnh ngày as_of = giá gốc ngày as_of).
- Kiểm tra chất lượng: biến động giữa hai lần quan sát liên tiếp (trên chuỗi ĐÃ điều chỉnh) vượt biên độ sàn
  → cờ lỗi dữ liệu. Ô bị cờ được loại khỏi feature/nhãn và ghi vào báo cáo chu kỳ."""
import numpy as np, pandas as pd
from .config import CFG, ROOT

STOCK = ("stock_split", "stock_dividend")
CASH = "cash_dividend"
EV_COLS = ["ticker", "ex_date", "type", "ratio", "cash_per_share", "source", "source_status", "note"]

def _read_events(rel):
    p = ROOT / rel
    if not p.exists():
        return pd.DataFrame(columns=EV_COLS)
    df = pd.read_csv(p, parse_dates=["ex_date"])
    for c in EV_COLS:
        if c not in df.columns: df[c] = np.nan
    return df[EV_COLS]

def load_manual(): return _read_events(CFG["corporate_actions"]["manual"])
def load_yahoo(): return _read_events(CFG["corporate_actions"]["yahoo_cache"])

def limits(index, columns):
    """Biên độ giá theo ngày và mã: mặc định HOSE, ghi đè theo cấu hình (mã từng niêm yết sàn khác)."""
    q = CFG["quality"]
    L = pd.DataFrame(float(q["price_limit"]), index=index, columns=columns)
    for o in q.get("limit_overrides") or []:
        if o["ticker"] in L.columns:
            m = (L.index >= pd.Timestamp(o.get("from", "1900-01-01"))) & (L.index <= pd.Timestamp(o["until"]))
            L.loc[m, o["ticker"]] = float(o["limit"])
    return L

def bands(L, k):
    """Biên trên/dưới cho biến động qua k phiên (k>1 khi mã thiếu phiên), cộng dung sai làm tròn bước giá."""
    tol = float(CFG["quality"]["tolerance"])
    return (1 + L) ** k - 1 + tol, 1 - (1 - L) ** k + tol

def obs_returns(close):
    """Lợi nhuận giữa hai lần quan sát liên tiếp của từng mã và số phiên giữa chúng (không ffill giá)."""
    pos = pd.DataFrame(np.tile(np.arange(len(close), dtype=float)[:, None], (1, close.shape[1])),
                       index=close.index, columns=close.columns).where(close.notna())
    ret = (close / close.ffill().shift(1) - 1).where(close.notna())
    return ret, pos - pos.ffill().shift(1)

def build_events(close, observed, manual, yahoo):
    """Xét từng sự kiện: áp dụng được không, hệ số bao nhiêu. `close` là giá gốc (không ffill), đã cắt tới as_of."""
    ev = pd.concat([manual.assign(prio=0), yahoo.assign(prio=1)], ignore_index=True)
    cols = EV_COLS + ["trade_date", "raw_return", "adj_return", "price_factor", "split_factor", "status"]
    if ev.empty:
        return pd.DataFrame(columns=cols)
    ev["group"] = np.where(ev["type"] == CASH, "cash", "stock")
    ev = ev.sort_values("prio").drop_duplicates(["ticker", "ex_date", "group"], keep="first")
    L = limits(close.index, close.columns)
    _, K = obs_returns(close)
    out = []
    for e in ev.itertuples(index=False):
        row = {c: getattr(e, c) for c in EV_COLS}
        row.update(trade_date=pd.NaT, raw_return=np.nan, adj_return=np.nan, price_factor=1.0, split_factor=1.0)
        s = close[e.ticker].dropna() if e.ticker in close.columns else pd.Series(dtype=float)
        before, after = s[s.index < e.ex_date], s[s.index >= e.ex_date]
        if e.ticker not in close.columns:
            row["status"] = "KHONG_CO_MA"
        elif after.empty:
            row["status"] = "CHUA_DEN_HAN"
        elif before.empty:
            row["status"] = "NGOAI_DU_LIEU"
        else:
            d, p0, p1 = after.index[0], before.iloc[-1], after.iloc[0]
            raw = p1 / p0 - 1
            up, dn = bands(L.at[d, e.ticker], K.at[d, e.ticker])
            within = lambda r: -dn <= r <= up
            row.update(trade_date=d, raw_return=raw)
            if e.type in STOCK:
                r = float(e.ratio) if pd.notna(e.ratio) else 0.0
                adj = (1 + raw) * r - 1 if r > 0 else np.nan
                row["adj_return"] = adj
                # Yahoo đã tự điều chỉnh chia tách vào giá nó trả về tại thời điểm tải: nếu các dòng trước ngày
                # GDKHQ được quan sát SAU ngày đó thì chia tách đã nằm sẵn trong giá gốc → không áp lại.
                seen = observed[e.ticker].loc[before.index].max() if observed is not None else pd.NaT
                if r <= 0:
                    row["status"] = "LOI_TY_LE"
                elif str(e.source).startswith("yahoo") and pd.notna(seen) and seen >= e.ex_date:
                    row["status"] = "DA_NAM_TRONG_GIA_NGUON"
                elif within(adj):
                    row.update(status="APPLIED", price_factor=1 / r, split_factor=1 / r)
                else:
                    row["status"] = "KHONG_KHOP"            # tỷ lệ không giải thích được bước nhảy giá
            elif e.type == CASH:
                c = float(e.cash_per_share) if pd.notna(e.cash_per_share) else 0.0
                if 0 < c < 0.3 * p0:
                    f = (p0 - c) / p0
                    row.update(status="APPLIED", price_factor=f, adj_return=p1 / (p0 * f) - 1)
                else:
                    row["status"] = "LOAI_BAT_THUONG"       # cổ tức tiền âm/0 hoặc quá lớn so với giá: nghi sai đơn vị
            else:
                row["status"] = "LOAI_KHONG_HO_TRO"
        out.append(row)
    return pd.DataFrame(out, columns=cols).sort_values(["ticker", "ex_date"]).reset_index(drop=True)

def factors(index, columns, events):
    """Hệ số giá (gồm cổ tức tiền) và hệ số chia tách (cho khối lượng) theo ngày: nhân dồn các sự kiện xảy ra SAU ngày đó."""
    F = pd.DataFrame(1.0, index=index, columns=columns)
    S = F.copy()
    for e in events[events.status == "APPLIED"].itertuples(index=False):
        m = F.index < e.trade_date
        F.loc[m, e.ticker] *= e.price_factor
        S.loc[m, e.ticker] *= e.split_factor
    return F, S

def quality(adj_close, as_of=None):
    """Cờ lỗi dữ liệu + tỷ lệ lỗi trong cửa sổ gần nhất. Trả về (bad, báo cáo)."""
    q = CFG["quality"]
    ret, K = obs_returns(adj_close)
    up, dn = bands(limits(adj_close.index, adj_close.columns), K)
    bad = ((ret > up) | (ret < -dn)).fillna(False).astype(bool)
    checked = ret.notna()
    W = int(q["window_sessions"])
    nw, cw = int(bad.iloc[-W:].values.sum()), int(checked.iloc[-W:].values.sum())
    rate_w = nw / cw if cw else 0.0
    st = bad.stack()
    flags = [{"date": str(d.date()), "ticker": t, "return": round(float(ret.at[d, t]), 4),
              "allowed": [round(-float(dn.at[d, t]), 4), round(float(up.at[d, t]), 4)]}
             for d, t in st[st].index]
    wstart = adj_close.index[-W:][0] if len(adj_close) else None
    rep = {"as_of": str((as_of or adj_close.index[-1]).date()) if len(adj_close) else None,
           "checked": int(checked.values.sum()), "flagged_total": len(flags),
           "error_rate_total": round(len(flags) / max(1, int(checked.values.sum())), 5),
           "window_sessions": W, "flagged_window": nw, "error_rate_window": round(rate_w, 5),
           "max_error_rate": float(q["max_error_rate"]), "skip": bool(rate_w > float(q["max_error_rate"])),
           "flags_window": [f for f in flags if wstart is not None and pd.Timestamp(f["date"]) >= wstart],
           "flags_total_by_year": pd.Series([f["date"][:4] for f in flags]).value_counts().sort_index().to_dict() if flags else {}}
    return bad, rep, flags

def contamination(bad, window):
    """Ô (ngày, mã) có ít nhất một cờ lỗi trong `window` phiên gần nhất tính tới ngày đó (chỉ nhìn quá khứ)."""
    return bad.astype(float).rolling(window, min_periods=1).max().fillna(0).astype(bool)
