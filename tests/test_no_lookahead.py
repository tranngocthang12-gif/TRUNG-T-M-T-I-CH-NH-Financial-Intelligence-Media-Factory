"""Chứng minh không nhìn trước tương lai: feature tại ngày t không đổi khi thêm dữ liệu sau t
(kể cả khi có cờ lỗi dữ liệu nằm SAU t)."""
import numpy as np, pandas as pd
from engine.features import build_wide

def test_features_point_in_time():
    rng = np.random.default_rng(0)
    d = pd.bdate_range("2021-01-01", periods=400)
    c = pd.DataFrame(np.exp(np.cumsum(rng.normal(0, 0.02, (400, 8)), axis=0)) * 1e4, index=d)
    v = pd.DataFrame(rng.lognormal(12, 0.5, (400, 8)), index=d)
    bad = pd.DataFrame(False, index=d, columns=c.columns)
    bad.iloc[150, 2] = True                     # lỗi trước ngày cắt
    bad.iloc[320, 3] = True                     # lỗi SAU ngày cắt — không được ảnh hưởng feature ngày 299
    for b in (None, bad):
        full = build_wide(c, v, b)
        cut = build_wide(c.iloc[:300], v.iloc[:300], None if b is None else b.iloc[:300])
        for n in full:
            pd.testing.assert_series_equal(full[n].iloc[299], cut[n].iloc[299], check_names=False)

if __name__ == "__main__":
    test_features_point_in_time(); print("OK: không có look-ahead trong feature (kể cả khi có cờ lỗi dữ liệu)")
