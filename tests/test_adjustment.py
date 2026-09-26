"""Chứng minh giá ĐIỀU CHỈNH đúng và kiểm tra chất lượng hoạt động. Chỉ đọc dữ liệu, không ghi gì vào repo.
Chạy: python -m tests.test_adjustment"""
import numpy as np, pandas as pd
from engine import adjust, data, features, ledger

# ---------- 1) Dữ liệu THẬT: TCB 11/06/2024 và VCB 03/03/2025 không còn là cú rơi giả ----------
mk = data.load_market()
raw, adj, bad = mk["raw_close"], mk["close"], mk["bad"]
for t, d, lo in [("TCB", "2024-06-11", -0.45), ("VCB", "2025-03-03", -0.30)]:
    i = raw.index.get_loc(pd.Timestamp(d))
    r_raw = raw[t].iloc[i] / raw[t].iloc[i - 1] - 1
    r_adj = adj[t].iloc[i] / adj[t].iloc[i - 1] - 1
    assert r_raw < lo, (t, r_raw)                               # kho vẫn giữ giá gốc (bằng chứng)
    assert abs(r_adj) <= 0.07 + 0.003, (t, r_adj)               # chuỗi điều chỉnh nằm trong biên độ HOSE
    assert not bad.at[raw.index[i], t]                          # không bị cờ lỗi (đã có sự kiện quyền giải thích)
    assert adj[t].iloc[-1] == raw[t].iloc[-1]                   # neo tại ngày cuối: giá điều chỉnh = giá gốc
    print(f"OK 1: {t} {d}: giá gốc {r_raw:+.2%} → điều chỉnh {r_adj:+.2%}, không bị cờ lỗi")
st = mk["events"].set_index("ticker").status
assert st["TCB"] == "APPLIED" and st["VCB"] == "APPLIED"

# Point-in-time: tính tại 10/06/2024 thì sự kiện TCB CHƯA tồn tại → không điều chỉnh quá khứ bằng thông tin tương lai
mk0 = data.load_market("2024-06-10")
assert ((mk0["close"]["TCB"] - mk0["raw_close"]["TCB"]).abs().max()) < 1e-9
assert mk0["events"].set_index("ticker").status["TCB"] == "CHUA_DEN_HAN"
d9 = pd.Timestamp("2024-06-10")
assert abs(mk["close"].at[d9, "TCB"] - mk["raw_close"].at[d9, "TCB"] / 2) < 1e-6
print("OK 2: point-in-time — tại 10/06/2024 chưa điều chỉnh; tính tại hôm nay thì giá 10/06/2024 = gốc / 2")

# Nhãn 20 phiên của TCB quanh ngày GDKHQ không còn chứa cú rơi -50%
y = features.labels_wide(adj, 20, bad)
yr = features.labels_wide(raw.ffill(limit=5), 20)
dd = pd.Timestamp("2024-05-31")
assert yr.at[dd, "TCB"] < -0.3 and abs(y.at[dd, "TCB"]) < 0.3, (yr.at[dd, "TCB"], y.at[dd, "TCB"])
print(f"OK 3: nhãn TCB ngày 31/05/2024: giá gốc {yr.at[dd, 'TCB']:+.1%} → điều chỉnh {y.at[dd, 'TCB']:+.1%}")

# ---------- 2) Hàm thuần trên dữ liệu dựng tay ----------
idx = pd.bdate_range("2024-01-01", periods=300)
close = pd.DataFrame(10000.0, index=idx, columns=["A", "B", "C", "D"])
close.loc[idx[100]:, "A"] = 5000.0          # A: chia tách 2:1 (có sự kiện)
close.loc[idx[150]:, "B"] = 7000.0          # B: rơi 30% KHÔNG có sự kiện → lỗi dữ liệu
close.loc[idx[200]:, "C"] = 9500.0          # C: cổ tức tiền 500đ
close.loc[idx[250]:, "D"] = 5000.0          # D: Yahoo báo chia tách nhưng giá gốc KHÔNG nhảy (đã nằm sẵn trong giá nguồn)
close.loc[idx[250]:, "D"] = 10000.0
obs = pd.DataFrame(idx[0], index=idx, columns=close.columns)
obs["D"] = idx[-1]                           # toàn bộ D được quan sát sau ngày chia tách
manual = pd.DataFrame([
    {"ticker": "A", "ex_date": idx[100], "type": "stock_split", "ratio": 2.0, "cash_per_share": np.nan},
    {"ticker": "C", "ex_date": idx[200], "type": "cash_dividend", "ratio": np.nan, "cash_per_share": 500.0}])
yahoo = pd.DataFrame([{"ticker": "D", "ex_date": idx[250], "type": "stock_split", "ratio": 2.0,
                       "cash_per_share": np.nan, "source": "yahoo"}])
for df in (manual, yahoo):
    for c in adjust.EV_COLS:
        if c not in df: df[c] = np.nan
ev = adjust.build_events(close, obs, manual[adjust.EV_COLS], yahoo[adjust.EV_COLS])
s = ev.set_index("ticker").status
assert s["A"] == "APPLIED" and s["C"] == "APPLIED" and s["D"] == "DA_NAM_TRONG_GIA_NGUON", s
F, S = adjust.factors(close.index, close.columns, ev)
a = close * F
assert np.allclose(a["A"], 5000.0) and np.allclose(a["C"].iloc[:200], 9500.0) and np.allclose(a["D"], 10000.0)
bad2, rep, flags = adjust.quality(a)
assert [(f["ticker"], f["date"]) for f in flags] == [("B", str(idx[150].date()))], flags
print("OK 4: chia tách áp đúng, cổ tức tiền áp đúng, chia tách đã nằm sẵn trong giá không bị áp lại; "
      "rơi 30% không có sự kiện bị cờ lỗi")

# Ô lỗi bị loại khỏi feature (cửa sổ nhìn lại) và nhãn (cửa sổ nắm giữ), mã sạch không bị ảnh hưởng
vol = pd.DataFrame(1e5, index=idx, columns=close.columns)
w = features.build_wide(a, vol, bad2)["mom_20"]
L = features.CFG["quality"]["feature_lookback"]
assert w["B"].iloc[150:150 + L].isna().all() and w["B"].iloc[150 + L:].notna().all() and w["B"].iloc[21:150].notna().all()
yl = features.labels_wide(a, 20, bad2)
assert yl["B"].iloc[129:149].isna().all() and yl["B"].iloc[149:278].notna().all() and yl["B"].iloc[:129].notna().all()
assert w["A"].iloc[21:].notna().all()
print("OK 5: feature/nhãn chạm ô lỗi bị loại; phần sạch giữ nguyên")

# Ledger: dự báo có ô lỗi trong cửa sổ chấm → VOID, không chấm điểm
import engine.ledger as LG
LG._load = lambda rel: [{"id": "P-x", "created_at": str(idx[140].date()), "procedure": "t",
                         "resolution_rule": {"ticker": "B", "horizon": 20}}] if rel == LG.PRED else []
LG._append = lambda rel, rows: None
r = ledger.resolve(a.ffill(), str(idx[-1].date()), bad2)
assert r[0]["outcome"] is None and "lỗi dữ liệu" in r[0]["void"], r
print("OK 6: Ledger đặt VOID cho dự báo có ô lỗi dữ liệu trong cửa sổ chấm")

# Paper trading: sự kiện quyền khi đang nắm giữ được áp vào vị thế (không ghi file ra repo)
from engine import paper
logs = []
paper._append = lambda rel, row: logs.append(row)
st = {"cash": 0.0, "positions": {"A": 1000, "C": 300}, "last_date": str(idx[99].date())}
paper.apply_corporate_actions(st, ev, str(idx[100].date()), str(idx[100].date()))
assert st["positions"]["A"] == 2000 and st["cash"] == 0.0
st["last_date"] = str(idx[199].date())
paper.apply_corporate_actions(st, ev, str(idx[200].date()), str(idx[200].date()))
tax = paper.CFG["costs"]["dividend_tax"]
assert abs(st["cash"] - 300 * 500 * (1 - tax)) < 1e-6 and st["positions"]["A"] == 2000
print(f"OK 7: paper — chia tách 2:1 nhân đôi số cổ phiếu; cổ tức tiền cộng {st['cash']:,.0f}đ (sau thuế {tax:.0%})")
