"""Diễn tập toàn bộ vòng học trên dữ liệu giả lập có CÀI SẴN quy luật (động lượng 60 phiên), quy luật ĐẢO CHIỀU
ở phiên 1250. Kỳ vọng: hệ thống tự tìm ra quy luật, tự giao dịch giấy, rồi tự phát hiện khi quy luật chết.
Chạy theo đợt (mỗi đợt dưới 5 phút):
  TTC_HOME=/tmp/ttc_demo python -m tests.demo_synthetic init
  TTC_HOME=/tmp/ttc_demo python -m tests.demo_synthetic run 1051 1200
  ...
  TTC_HOME=/tmp/ttc_demo python -m tests.demo_synthetic run 1400 1540"""
import os, sys, shutil, pathlib
home = pathlib.Path(os.environ.setdefault("TTC_HOME", "/tmp/ttc_demo"))
if sys.argv[1] == "init":
    if home.exists(): shutil.rmtree(home)
    home.mkdir(parents=True)
    shutil.copy(pathlib.Path(__file__).resolve().parents[1] / "config.yaml", home / "config.yaml")
from engine.synthetic import make_store
from engine.run_cycle import cycle
import pandas as pd
dates = pd.bdate_range("2020-01-01", periods=1560)
if sys.argv[1] == "init":
    make_store()
    r = cycle(str(dates[1050].date()), trials=16, write_report=True, use_llm=False, seed=1)
    print(f"[khởi động {r['as_of']}] 16 thử nghiệm, sống sót: " +
          ", ".join(f"{t['features']}/{t['model']}:{t['status']}" for t in r["trials"] if t["status"] != "REJECTED"))
else:
    a, b = int(sys.argv[2]), int(sys.argv[3])
    for i in range(a, b):
        r = cycle(str(dates[i].date()), trials=3 if i % 40 == 0 else 0, write_report=(i == b - 1),
                  use_llm=False, seed=i)
        for al in r["alerts"]:
            print(f"[{r['as_of']}] {al}")
    print(f"Đợt {a}-{b} xong. Ngày quy luật đảo chiều: {dates[1250].date()}")
