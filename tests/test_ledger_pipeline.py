"""Kiểm thử đường ống Prediction Ledger bằng chuyên gia GIẢ LẬP (TTC_MOCK_LLM=1), không tốn API.
Kiểm: Budget Governor chặn đúng, Auditor loại nguồn bịa, dự báo được chấm khi đến hạn, Scorecard tính đúng.
Chạy: python -m tests.test_ledger_pipeline"""
import os, json, shutil, pathlib, yaml
home = pathlib.Path("/tmp/ttc_ledger_test")
if home.exists(): shutil.rmtree(home)
(home / "governance").mkdir(parents=True)
repo = pathlib.Path(__file__).resolve().parents[1]
cfg = yaml.safe_load((repo / "config.yaml").read_text(encoding="utf-8"))
(home / "config.yaml").write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
safety = {"autonomous_spending_enabled": False}
(home / "governance/SAFETY_STATE.yaml").write_text(yaml.safe_dump(safety))
os.environ["TTC_HOME"] = str(home)
os.environ["TTC_MOCK_LLM"] = "1"
import pandas as pd
from engine.synthetic import make_store
from engine import run_cycle, ledger, facts, budget
from engine.config import path

dates = make_store(n_days=900)
d0 = str(dates[700].date())

# 1) Governor phải CHẶN khi chưa được Owner cho phép
r = run_cycle.cycle(d0, trials=0, write_report=False, use_llm=True)
assert r["experts"]["ran"] is False and any("autonomous_spending" in x for x in r["experts"]["reasons"]), r["experts"]
print("OK 1: Budget Governor chặn khi Owner chưa cho phép chi tiêu")

# Owner cho phép (chỉ trong môi trường kiểm thử)
(home / "governance/SAFETY_STATE.yaml").write_text(yaml.safe_dump({"autonomous_spending_enabled": True}))
(home / "governance/GOVERNOR_POLICY.yaml").write_text(yaml.safe_dump({"api_budget": {"daily_cap_usd": 1, "monthly_cap_usd": 10}}))
cfg["experts"]["price_input_per_mtok"] = 1; cfg["experts"]["price_output_per_mtok"] = 1
(home / "config.yaml").write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
import importlib, engine.config as C; importlib.reload(C)
for m in ["engine.budget", "engine.facts", "engine.ledger", "engine.experts", "engine.run_cycle"]:
    importlib.reload(importlib.import_module(m))
from engine import run_cycle, ledger, facts

# 2) Auditor phải loại dự báo có nguồn bịa / xác suất sai / mã lạ
close = pd.read_csv(home / cfg["data"]["store"], parse_dates=["date"]).pivot(index="date", columns="ticker", values="close")
_, rej = ledger.record([{"procedure": "test", "ticker": "S01", "horizon": 20, "probability": 0.6, "claim": "x", "evidence_refs": ["N-bia"]},
                        {"procedure": "test", "ticker": "XXX", "horizon": 20, "probability": 0.6, "claim": "x", "evidence_refs": []},
                        {"procedure": "test", "ticker": "S01", "horizon": 7, "probability": 1.0, "claim": "x", "evidence_refs": []}],
                       d0, list(close.columns), set(), close.loc[:d0])
assert len(rej) == 3, rej
print("OK 2: Auditor loại 3/3 dự báo sai luật:", [r["audit_errors"][0] for r in rej])

# 3) Chạy 60 phiên, mỗi phiên có tin giả nhắc S01, S05
for i in range(701, 761):
    d = dates[i]
    with open(path(facts.NEWS), "a", encoding="utf-8") as f:
        for t in ["S01", "S05"]:
            f.write(json.dumps({"id": f"N-{t}-{i}", "source": "test", "link": f"x/{t}/{i}", "title": f"Tin về {t}",
                                "summary": "", "published_at": None, "retrieved_at": d.isoformat(), "status": "RAW"}) + "\n")
    r = run_cycle.cycle(str(d.date()), trials=0, write_report=(i == 760), use_llm=True)
sc = json.loads((home / "reports/scorecard.json").read_text(encoding="utf-8"))
print("OK 3:", sc["total_predictions"], "dự báo,", sc["resolved"], "đã chấm")
for k, v in sc["procedures"].items():
    print(f"   {k}: n={v['n']} Brier={v['brier']} nền={v['brier_base_rate']} skill={v['brier_skill']} → {v['verdict']}")
assert sc["resolved"] > 0 and "news@v1" in sc["procedures"] and "devils_advocate@v1" in sc["procedures"]
spend = pd.read_csv(home / "memory/economic/api_spend.csv") if (home / "memory/economic/api_spend.csv").exists() else None
print("OK 4: nhật ký chi phí có", 0 if spend is None else len(spend), "dòng")
print(open(home / f"reports/cycle_{dates[760].date()}.md", encoding="utf-8").read().split("## Prediction Ledger")[1])
