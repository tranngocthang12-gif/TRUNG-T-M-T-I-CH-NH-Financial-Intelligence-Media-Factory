"""Lỗi nguồn dữ liệu (từng mã, từng nguồn) phải vào báo cáo chu kỳ và state/ENGINE_STATE.json, không chỉ in ra log.
Nguồn mạng được thay bằng hàm giả. Chạy trong thư mục tạm. Chạy: python -m tests.test_ingest_errors"""
import os, sys, json, shutil, pathlib, yaml
home = pathlib.Path("/tmp/ttc_ingest_test")
if home.exists(): shutil.rmtree(home)
home.mkdir(parents=True)
repo = pathlib.Path(__file__).resolve().parents[1]
cfg = yaml.safe_load((repo / "config.yaml").read_text(encoding="utf-8"))
cfg["universe"] = [f"S{i:02d}" for i in range(30)]
cfg["data"]["sources"] = ["vnstock", "yahoo"]          # thử cả chuỗi dự phòng
(home / "config.yaml").write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
os.environ["TTC_HOME"] = str(home)
import pandas as pd
from engine.synthetic import make_store
from engine import data, run_cycle, facts
facts.ingest_news = lambda as_of: {"new_items": 0, "errors": ["https://rss.gia-lap: HTTP 403"]}   # không gọi mạng thật

dates = make_store(n_days=700)
store = data.load_store()
nxt = dates[-1] + pd.offsets.BDay(1)

def fake_vnstock(t, s, e): raise ModuleNotFoundError("No module named 'vnstock'")
def fake_yahoo(t, s, e):
    if t in ("S03", "S07"): raise RuntimeError(f"HTTP 404 {t}.VN not found")
    last = store[store.ticker == t].close.iloc[-1]
    return pd.DataFrame({"date": [nxt], "open": last, "high": last, "low": last, "close": last, "volume": 1e5})
data.FETCHERS.update(vnstock=fake_vnstock, yahoo=fake_yahoo)
data.fetch_yahoo_actions = lambda: [{"ticker": "S05", "source": "yahoo_actions", "error": "timeout"}]

ing = data.ingest(end=nxt.date())
errs = {(e["ticker"], e["source"]) for e in ing["errors"]}
assert len([e for e in ing["errors"] if e["source"] == "vnstock"]) == 30          # KHÔNG bị cắt còn 20 như trước
assert ("S03", "yahoo") in errs and ("S07", "yahoo") in errs and ("S05", "yahoo_actions") in errs
assert ing["rows_by_source"] == {"yahoo": 28} and set(ing["tickers_no_new_data"]) == {"S03", "S07"}
print(f"OK 1: ingest ghi đủ {len(ing['errors'])} lỗi theo từng mã/nguồn; 28 mã lấy từ yahoo, 2 mã không có dữ liệu mới")

# Chạy vòng học qua main() đúng như GitHub Actions
data.ingest = lambda end=None: ing
sys.argv = ["run_cycle", "--source", "live", "--trials", "0", "--no-llm"]
run_cycle.main()
st = json.loads((home / "state/ENGINE_STATE.json").read_text(encoding="utf-8"))
assert len(st["data_ingest"]["errors"]) == len(ing["errors"])
rep = (home / f"reports/cycle_{nxt.date()}.md").read_text(encoding="utf-8")
assert "## Nguồn dữ liệu" in rep and "| S03 | yahoo | HTTP 404 S03.VN not found |" in rep and "| S05 | yahoo_actions | timeout |" in rep
assert "https://rss.gia-lap: HTTP 403" in rep and st["news_errors"] == ["https://rss.gia-lap: HTTP 403"]
print("OK 2: lỗi nguồn có trong báo cáo chu kỳ và state/ENGINE_STATE.json")

# Ngày đã xử lý → không chạy vòng học nhưng VẪN lưu nhật ký tải
ing2 = {**ing, "errors": [{"ticker": "S09", "source": "yahoo", "error": "rate limited"}]}
data.ingest = lambda end=None: ing2
run_cycle.main()
st = json.loads((home / "state/ENGINE_STATE.json").read_text(encoding="utf-8"))
assert st["data_ingest"]["errors"][0]["error"] == "rate limited" and st["as_of"] == str(nxt.date())
print("OK 3: ngày đã xử lý (bỏ qua vòng học) vẫn lưu lỗi nguồn vào ENGINE_STATE")
