"""Báo cáo chu kỳ dạng markdown + ENGINE_STATE cho AI/Owner đọc."""
import pandas as pd
from .config import CFG, save_json, path

def write(as_of, regime_now, trials, bandit, reg, nav, decision, attr, alerts, thr, n_total):
    act = {s: sum(1 for v in reg.values() if v["state"] == s) for s in
           ["ACTIVE", "WATCH", "DEGRADING", "PAUSED", "INVALIDATED", "RETIRED"]}
    state = {"as_of": as_of, "regime": regime_now, "total_trials": n_total, "current_t_threshold": round(thr, 2),
             "models": act, "paper_nav": nav, "alerts": alerts,
             "bandit": {m: {"trials": v["trials"], "survivors": v["survivors"],
                            "posterior_mean": round(v["a"] / (v["a"] + v["b"]), 3)} for m, v in bandit.items()}}
    save_json("state/ENGINE_STATE.json", state)
    L = [f"# Báo cáo chu kỳ {as_of}", "", f"- Regime hiện tại: **{regime_now}**",
         f"- Tổng số thử nghiệm từ trước tới nay: {n_total} → ngưỡng t hiện hành: **{thr:.2f}**",
         f"- Mô hình: " + ", ".join(f"{k} {v}" for k, v in act.items()),
         f"- NAV giao dịch giấy: {nav:,.0f} VND" if nav else "- Chưa có giao dịch giấy", ""]
    if decision:
        L += [f"**Quyết định giao dịch giấy:** {decision['action']} {decision['targets']}", ""]
    if alerts:
        L += ["## Cảnh báo suy thoái", *[f"- {a}" for a in alerts], ""]
    if trials:
        L += ["## Thử nghiệm trong chu kỳ", "", "| Phương pháp | Feature | Mô hình | IC | t | Ròng/năm | Kết luận |",
              "|---|---|---|---|---|---|---|"]
        L += [f"| {t['method']} | {t['features']} | {t['model']} | {t['ic_mean']:.3f} | {t['ic_t']:.2f} | "
              f"{t['net_ann']:.1%} | {t['status']} |" for t in trials]
        L.append("")
    L += ["## Meta-learning: hiệu quả phương pháp nghiên cứu", "", "| Phương pháp | Số thử | Sống sót | Kỳ vọng hậu nghiệm |",
          "|---|---|---|---|"]
    L += [f"| {m} | {v['trials']} | {v['survivors']} | {v['a']/(v['a']+v['b']):.2f} |" for m, v in bandit.items()]
    if attr and "skill_assessment" in attr:
        L += ["", "## Attribution", f"- Lợi nhuận thực: {attr['actual_return']:.2%} | Chỉ số: "
              f"{attr['counterfactuals']['index']:.2%} | Không làm gì: 0%",
              f"- Beta: {attr['components']['market_beta']:.2f} | Alpha năm hóa: "
              f"{attr['components']['residual_alpha_ann']:.2%} (t={attr['components']['alpha_t']:.2f})",
              f"- Chi phí đã trả: {attr['costs_paid']:,.0f} VND", f"- Đánh giá: **{attr['skill_assessment']}**"]
    path(f"reports/cycle_{as_of}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
