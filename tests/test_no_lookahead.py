"""Chứng minh không nhìn trước tương lai: feature tại ngày t không đổi khi thêm dữ liệu sau t."""
import numpy as np, pandas as pd
from engine.features import build_wide

def test_features_point_in_time():
    rng = np.random.default_rng(0)
    d = pd.bdate_range("2021-01-01", periods=400)
    c = pd.DataFrame(np.exp(np.cumsum(rng.normal(0, 0.02, (400, 8)), axis=0)) * 1e4, index=d)
    v = pd.DataFrame(rng.lognormal(12, 0.5, (400, 8)), index=d)
    full, cut = build_wide(c, v), build_wide(c.iloc[:300], v.iloc[:300])
    for n in full:
        pd.testing.assert_series_equal(full[n].iloc[299], cut[n].iloc[299], check_names=False)

if __name__ == "__main__":
    test_features_point_in_time(); print("OK: không có look-ahead trong feature")
