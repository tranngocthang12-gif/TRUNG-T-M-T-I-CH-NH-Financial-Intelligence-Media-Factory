"""Báo cáo chu kỳ dạng markdown + ENGINE_STATE cho AI/Owner đọc."""
import pandas as pd
from .config import CFG, save_json, path

def _quality_lines(q):
    if not q:
        return []
    L = ["## Chất lượng dữ liệu giá", "",
         f"- Tỷ lệ lỗi {q['window_sessions']} phiên gần nhất: **{q['error_rate_window']:.2%}** "
         f"({q['flagged_window']} ô) — ngưỡng {q['max_error_rate']:.2%}",
         f"- Toàn lịch sử: {q['flagged_total']} ô bị cờ / {q['checked']} ô kiểm ({q['error_rate_total']:.2%}); "
         "ô lỗi và cửa sổ chứa nó bị LOẠI khỏi feature, nhãn, chấm Ledger"]
    if q["skip"]:
        L.append("- **TẠM DỪNG hôm nay: KHÔNG nghiên cứu, KHÔNG dự báo, KHÔNG khớp lệnh giấy** (lỗi dữ liệu vượt ngưỡng)")
    if q.get("events_applied"):
        L += ["- Sự kiện quyền đã điều chỉnh:", *[f"  - {e}" for e in q["events_applied"]]]
    if q.get("events_not_applied"):
        L += ["- Sự kiện quyền KHÔNG áp dụng được:", *[f"  - {e}" for e in q["events_not_applied"]]]
    if q["flags_window"]:
        L += ["", "| Ngày | Mã | Biến động | Cho phép |", "|---|---|---|---|"]
        L += [f"| {f['date']} | {f['ticker']} | {f['return']:+.2%} | {f['allowed'][0]:+.1%} … {f['allowed'][1]:+.1%} |"
              for f in q["flags_window"][:40]]
    return L + [""]

def _ingest_lines(ing, news_errors):
    if not ing and not news_errors:
        return []
    L = ["## Nguồn dữ liệu", ""]
    if ing:
        L += [f"- Tải lúc {ing['at']} (UTC) | thứ tự nguồn: {', '.join(ing['sources'])} | dòng mới: {ing['new_rows']} "
              f"{ing['rows_by_source'] or ''}",
              f"- Mã không có dữ liệu mới: {', '.join(ing['tickers_no_new_data']) or 'không'}"]
        if ing["errors"]:
            L += ["", f"**Lỗi nguồn dữ liệu ({len(ing['errors'])}):**", "", "| Mã | Nguồn | Lỗi |", "|---|---|---|"]
            L += [f"| {e['ticker']} | {e['source']} | {str(e['error']).replace('|', '/')[:200]} |" for e in ing["errors"]]
        else:
            L.append("- Không có lỗi nguồn giá")
    if news_errors:
        L += ["", f"**Lỗi nguồn tin tức ({len(news_errors)}):**", *[f"- {e}" for e in news_errors]]
    return L + [""]

def write(as_of, regime_now, trials, bandit, reg, nav, decision, attr, alerts, thr, n_total, quality=None,
          ingest=None, news_errors=None):
    act = {s: sum(1 for v in reg.values() if v["state"] == s) for s in
           ["ACTIVE", "WATCH", "DEGRADING", "PAUSED", "INVALIDATED", "RETIRED"]}
    state = {"as_of": as_of, "regime": regime_now, "total_trials": n_total, "current_t_threshold": round(thr, 2),
             "models": act, "paper_nav": nav, "alerts": alerts,
             "data_quality": {k: v for k, v in (quality or {}).items() if k != "flags_window"} | (
                 {"flags_window": (quality or {}).get("flags_window", [])[:50]} if quality else {}),
             "data_ingest": ingest, "news_errors": news_errors or [],
             "bandit": {m: {"trials": v["trials"], "survivors": v["survivors"],
                            "posterior_mean": round(v["a"] / (v["a"] + v["b"]), 3)} for m, v in bandit.items()}}
    save_json("state/ENGINE_STATE.json", state)
    L = [f"# Báo cáo chu kỳ {as_of}", "", f"- Regime hiện tại: **{regime_now}**",
         f"- Tổng số thử nghiệm từ trước tới nay: {n_total} → ngưỡng t hiện hành: **{thr:.2f}**",
         f"- Mô hình: " + ", ".join(f"{k} {v}" for k, v in act.items()),
         f"- NAV giao dịch giấy: {nav:,.0f} VND" if nav else "- Chưa có giao dịch giấy", ""]
    L += _ingest_lines(ingest, news_errors)
    L += _quality_lines(quality)
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
