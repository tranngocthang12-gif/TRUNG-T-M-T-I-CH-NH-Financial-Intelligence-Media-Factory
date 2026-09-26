"""Dữ liệu giả lập có CÀI SẴN một quy luật, dùng để kiểm tra hệ thống có tự tìm ra — và tự phát hiện khi quy luật biến mất.
Quy luật: cổ phiếu có động lượng 60 phiên mạnh sẽ tăng thêm; sau ngày `break_day` quy luật đảo chiều."""
import numpy as np, pandas as pd
from .data import COLS, append_rows, save_store

def make_store(n_days=1560, n=30, seed=7, break_day=1250, strength=0.002):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2020-01-01", periods=n_days)
    tick = [f"S{i:02d}" for i in range(n)]
    logp = np.zeros((n_days, n)); logp[0] = np.log(rng.uniform(15000, 90000, n))
    for d in range(1, n_days):
        mkt = rng.normal(0.0002, 0.011)
        drift = np.zeros(n)
        if d > 60:
            mom = logp[d - 1] - logp[d - 61]
            r = (pd.Series(mom).rank(pct=True).values - 0.5)
            drift = (strength if d < break_day else -0.5 * strength) * r
        logp[d] = logp[d - 1] + mkt + drift + rng.normal(0, 0.02, n)
    close = np.round(np.exp(logp), -1)
    rows = []
    vol = rng.lognormal(13, 0.5, (n_days, n))
    for j, t in enumerate(tick):
        rows.append(pd.DataFrame({"date": dates, "ticker": t, "open": close[:, j], "high": close[:, j],
                                  "low": close[:, j], "close": close[:, j], "volume": vol[:, j].round(),
                                  "observed_at": dates, "source": "synthetic"}))
    df = pd.concat(rows, ignore_index=True)[COLS]
    save_store(df)
    return dates
