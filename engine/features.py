"""Feature Library. Mọi feature tại ngày t chỉ dùng dữ liệu đến hết ngày t (kiểm tra bởi tests/test_no_lookahead.py).
Đầu vào là GIÁ ĐIỀU CHỈNH. `bad` = cờ lỗi dữ liệu (adjust.quality): feature/nhãn chạm vào ô lỗi bị loại (NaN)."""
import numpy as np, pandas as pd
from .adjust import contamination
from .config import CFG

def _ret(c, n): return c / c.shift(n) - 1
def _lr(c): return np.log(c).diff()

FEATURES = {
    "mom_20":        ("momentum",   lambda c, v: _ret(c, 20)),
    "mom_60":        ("momentum",   lambda c, v: _ret(c, 60)),
    "mom_120_skip20":("momentum",   lambda c, v: c.shift(20) / c.shift(120) - 1),
    "rel_mom_20":    ("momentum",   lambda c, v: _ret(c, 20).sub(_ret(c, 20).mean(axis=1), axis=0)),
    "rev_1":         ("reversal",   lambda c, v: -_ret(c, 1)),
    "rev_5":         ("reversal",   lambda c, v: -_ret(c, 5)),
    "lowvol_20":     ("volatility", lambda c, v: -_lr(c).rolling(20).std()),
    "lowvol_60":     ("volatility", lambda c, v: -_lr(c).rolling(60).std()),
    "maxret_20":     ("volatility", lambda c, v: -_lr(c).rolling(20).max()),
    "volu_ratio":    ("volume",     lambda c, v: v.rolling(5).mean() / v.rolling(60).mean()),
    "volu_trend":    ("volume",     lambda c, v: np.log((v.rolling(20).mean() + 1) / (v.rolling(120).mean() + 1))),
    "dist_ma20":     ("trend",      lambda c, v: c / c.rolling(20).mean() - 1),
    "dist_ma120":    ("trend",      lambda c, v: c / c.rolling(120).mean() - 1),
}
FAMILIES = sorted({f for f, _ in FEATURES.values()})

def _bad(bad, close):
    if bad is None: return None
    b = bad.reindex(index=close.index, columns=close.columns).fillna(False).astype(bool)
    return b if b.values.any() else None

def build_wide(close, volume, bad=None):
    out = {}
    b = _bad(bad, close)
    contam = contamination(b, CFG["quality"]["feature_lookback"]) if b is not None else None
    for name, (_, f) in FEATURES.items():
        x = f(close, volume).replace([np.inf, -np.inf], np.nan)
        if contam is not None:
            x = x.mask(contam)                           # cửa sổ nhìn lại chứa ô lỗi dữ liệu → loại
        out[name] = x.rank(axis=1, pct=True) - 0.5      # chuẩn hóa xếp hạng chéo theo ngày
    return out

def labels_wide(close, h, bad=None):
    """Nhãn: lợi nhuận vượt trội trung bình universe, VÀO LỆNH ở close t+1 (không dùng giá t).
    Nếu cửa sổ nắm giữ (t+1, t+1+h] của một mã có ô lỗi dữ liệu → nhãn mã đó bị loại."""
    fwd = close.shift(-(1 + h)) / close.shift(-1) - 1
    b = _bad(bad, close)
    if b is not None:
        fwd = fwd.mask(contamination(b, h).shift(-(1 + h)).fillna(False).astype(bool))
    return fwd.sub(fwd.mean(axis=1), axis=0)

def dataset(close, volume, h, bad=None):
    wide = build_wide(close, volume, bad)
    idx = pd.MultiIndex.from_product([close.index, close.columns], names=["date", "ticker"])
    ds = pd.DataFrame({n: w.values.ravel() for n, w in wide.items()}, index=idx)
    ds["y"] = labels_wide(close, h, bad).values.ravel()
    ds["yr"] = ds["y"].groupby(level=0).rank(pct=True) - 0.5
    return ds
