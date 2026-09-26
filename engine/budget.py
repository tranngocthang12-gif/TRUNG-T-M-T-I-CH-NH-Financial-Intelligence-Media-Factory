"""Budget Governor: chuyên gia Claude chỉ chạy khi Owner đã cho phép chi tiêu, đã đặt trần và đơn giá, và còn ngân sách."""
import os
import pandas as pd, yaml
from .config import CFG, ROOT, path

SPEND = "memory/economic/api_spend.csv"

def _yaml(rel):
    p = ROOT / rel
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}

def _num(x):
    try: return float(x)
    except (TypeError, ValueError): return 0.0

def status(as_of):
    safety = _yaml("governance/SAFETY_STATE.yaml")
    gov = _yaml("governance/GOVERNOR_POLICY.yaml").get("api_budget", {}) or {}
    e = CFG.get("experts", {})
    reasons = []
    if not safety.get("autonomous_spending_enabled", False): reasons.append("SAFETY_STATE: autonomous_spending_enabled = false")
    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("TTC_MOCK_LLM"): reasons.append("thiếu secret ANTHROPIC_API_KEY")
    daily, monthly = _num(gov.get("daily_cap_usd")), _num(gov.get("monthly_cap_usd"))
    if daily <= 0 or monthly <= 0: reasons.append("GOVERNOR_POLICY: chưa đặt daily_cap_usd / monthly_cap_usd")
    if _num(e.get("price_input_per_mtok")) <= 0 or _num(e.get("price_output_per_mtok")) <= 0:
        reasons.append("config.yaml: chưa đặt đơn giá API")
    spent_day = spent_month = 0.0
    p = ROOT / SPEND
    if p.exists():
        s = pd.read_csv(p, parse_dates=["date"])
        d = pd.Timestamp(as_of)
        spent_day = s.loc[s.date == d, "usd"].sum()
        spent_month = s.loc[(s.date.dt.year == d.year) & (s.date.dt.month == d.month), "usd"].sum()
    if daily > 0 and spent_day >= daily: reasons.append(f"đã chạm trần ngày {daily} USD")
    if monthly > 0 and spent_month >= monthly: reasons.append(f"đã chạm trần tháng {monthly} USD")
    return {"allowed": not reasons, "reasons": reasons, "spent_day": float(spent_day),
            "spent_month": float(spent_month), "daily_cap": daily, "monthly_cap": monthly}

def record(as_of, procedure, usage):
    e = CFG["experts"]
    usd = (usage.get("input_tokens", 0) * _num(e["price_input_per_mtok"]) +
           usage.get("output_tokens", 0) * _num(e["price_output_per_mtok"])) / 1e6
    p = ROOT / SPEND
    pd.DataFrame([{"date": as_of, "procedure": procedure, "input_tokens": usage.get("input_tokens", 0),
                   "output_tokens": usage.get("output_tokens", 0), "usd": round(usd, 6)}]).to_csv(
        path(SPEND), mode="a", header=not p.exists(), index=False)
    return usd
