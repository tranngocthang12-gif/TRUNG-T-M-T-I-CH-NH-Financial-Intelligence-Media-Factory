"""Chứng minh llm_review đi qua Budget Governor: KHÔNG gọi API khi Governor chặn, và ghi chi phí khi được phép.
Mạng bị thay bằng hàm giả — không tốn API. Chạy: python -m tests.test_llm_review_budget"""
import os, io, json, shutil, pathlib, importlib, urllib.request, yaml
home = pathlib.Path("/tmp/ttc_llm_review_test")
if home.exists(): shutil.rmtree(home)
(home / "governance").mkdir(parents=True)
repo = pathlib.Path(__file__).resolve().parents[1]
cfg = yaml.safe_load((repo / "config.yaml").read_text(encoding="utf-8"))
cfg["llm_review"]["enabled"] = True
(home / "config.yaml").write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
(home / "governance/SAFETY_STATE.yaml").write_text(yaml.safe_dump({"autonomous_spending_enabled": False}))
os.environ["TTC_HOME"] = str(home)
os.environ["ANTHROPIC_API_KEY"] = "sk-gia-lap"          # có key nhưng Governor vẫn phải chặn
os.environ.pop("TTC_MOCK_LLM", None)

calls = []
class _Resp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False
def fake_urlopen(req, timeout=None):
    calls.append(req.full_url)
    return _Resp(json.dumps({"content": [{"type": "text", "text": "phản biện"}],
                             "usage": {"input_tokens": 1000, "output_tokens": 500}}).encode())
urllib.request.urlopen = fake_urlopen

def reload():
    import engine.config
    importlib.reload(engine.config)
    for m in ["engine.budget", "engine.llm_review"]:
        importlib.reload(importlib.import_module(m))
    from engine import llm_review
    return llm_review

AS_OF = "2026-09-25"
SPEND = home / "memory/economic/api_spend.csv"

# 1) Owner chưa cho chi tiêu → không gọi API, không ghi file, không ghi chi phí
lr = reload()
assert lr.review("M-test", {}, {}, AS_OF) is None
assert calls == [], calls
assert not (home / "research/reviews/M-test.md").exists() and not SPEND.exists()
print("OK 1: SAFETY_STATE chặn → llm_review không gọi API (0 lần gọi)")

# 2) Cho chi tiêu nhưng chưa đặt trần/đơn giá → vẫn chặn
(home / "governance/SAFETY_STATE.yaml").write_text(yaml.safe_dump({"autonomous_spending_enabled": True}))
lr = reload()
assert lr.review("M-test", {}, {}, AS_OF) is None and calls == []
print("OK 2: chưa đặt trần ngân sách / đơn giá → vẫn không gọi API")

# 3) Đủ điều kiện → gọi đúng 1 lần và ghi chi phí qua budget.record()
(home / "governance/GOVERNOR_POLICY.yaml").write_text(yaml.safe_dump({"api_budget": {"daily_cap_usd": 1, "monthly_cap_usd": 10}}))
cfg["experts"]["price_input_per_mtok"] = 3; cfg["experts"]["price_output_per_mtok"] = 15
(home / "config.yaml").write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
lr = reload()
assert lr.review("M-test", {}, {}, AS_OF) == "phản biện" and len(calls) == 1
import pandas as pd
sp = pd.read_csv(SPEND)
assert len(sp) == 1 and sp.procedure[0] == "llm_review@v1" and abs(sp.usd[0] - 0.0105) < 1e-9, sp
print(f"OK 3: Governor cho phép → gọi 1 lần, ghi chi phí {sp.usd[0]} USD vào api_spend.csv")

# 4) Chạm trần ngày → chặn lại
pd.DataFrame([{"date": AS_OF, "procedure": "x", "input_tokens": 0, "output_tokens": 0, "usd": 5}]).to_csv(
    SPEND, mode="a", header=False, index=False)
lr = reload()
assert lr.review("M-test2", {}, {}, AS_OF) is None and len(calls) == 1
print("OK 4: chạm trần ngày → không gọi thêm")
