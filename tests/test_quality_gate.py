"""Cổng chất lượng: tỷ lệ lỗi dữ liệu vượt ngưỡng → vòng học KHÔNG nghiên cứu, KHÔNG dự báo, KHÔNG khớp lệnh giấy,
và ghi lý do vào báo cáo chu kỳ + ENGINE_STATE. Chạy trong thư mục tạm. Chạy: python -m tests.test_quality_gate"""
import os, json, shutil, pathlib, yaml
home = pathlib.Path("/tmp/ttc_quality_gate_test")
if home.exists(): shutil.rmtree(home)
home.mkdir(parents=True)
repo = pathlib.Path(__file__).resolve().parents[1]
shutil.copy(repo / "config.yaml", home / "config.yaml")
os.environ["TTC_HOME"] = str(home)
import pandas as pd
from engine.synthetic import make_store
from engine import run_cycle, data

dates = make_store(n_days=800)

# 1) Dữ liệu sạch → vòng học chạy bình thường
q = data.load_market(str(dates[700].date()))["quality"]
assert q["flagged_total"] == 0, q
r = run_cycle.cycle(str(dates[700].date()), trials=2, write_report=True, use_llm=False, seed=1)
assert len(r["trials"]) == 2 and not r["quality"]["skip"]
print("OK 1: dữ liệu giả lập tôn trọng biên độ → 0 cờ lỗi, vòng học chạy 2 thử nghiệm")

# 2) Cấy lỗi: 12 mã rơi 25% rồi hồi lại trong 20 phiên gần nhất (không có sự kiện quyền)
s = data.load_store()
tick = sorted(s.ticker.unique())[:12]
for j, t in enumerate(tick):
    d = dates[705 + j]
    s.loc[(s.ticker == t) & (s.date == d), "close"] *= 0.75
data.save_store(s)
d_bad = str(dates[720].date())
r = run_cycle.cycle(d_bad, trials=2, write_report=True, use_llm=True, seed=2)
q = r["quality"]
assert q["skip"] and q["flagged_window"] >= 12 and q["error_rate_window"] > q["max_error_rate"], q
assert r["trials"] == [], "không được nghiên cứu khi dữ liệu lỗi"
assert r["experts"]["ran"] is False and "tỷ lệ lỗi dữ liệu" in r["experts"]["reasons"][0]
assert r["decision"]["action"] == "NO_DECISION_DATA_QUALITY"
rep = (home / f"reports/cycle_{d_bad}.md").read_text(encoding="utf-8")
assert "TẠM DỪNG hôm nay" in rep and "## Chất lượng dữ liệu giá" in rep
st = json.loads((home / "state/ENGINE_STATE.json").read_text(encoding="utf-8"))
assert st["data_quality"]["skip"] is True and len(st["data_quality"]["flags_window"]) >= 12
print(f"OK 2: lỗi {q['error_rate_window']:.2%} > ngưỡng {q['max_error_rate']:.2%} → 0 thử nghiệm, chuyên gia không chạy, "
      "paper không ra quyết định; báo cáo + ENGINE_STATE ghi lý do")
