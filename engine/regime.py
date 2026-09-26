"""Market Regime Engine: nhãn regime theo xu hướng và biến động của chỉ số đại diện (bình quân universe)."""
import pandas as pd

def market_returns(close, bad=None):
    r = close.pct_change(fill_method=None)
    if bad is not None:
        r = r.mask(bad.reindex(index=r.index, columns=r.columns).fillna(False).astype(bool))   # bỏ ô lỗi dữ liệu
    return r.mean(axis=1).fillna(0)

def regimes(close, bad=None):
    r = market_returns(close, bad)
    idx = (1 + r).cumprod()
    trend = (idx > idx.rolling(120).mean()).map({True: "UP", False: "DOWN"})
    vol = r.rolling(20).std()
    high = vol > vol.expanding(250).median()
    lab = trend + "_" + high.map({True: "HIGHVOL", False: "LOWVOL"})
    lab[idx.rolling(120).mean().isna()] = "UNKNOWN"
    return lab
