"""Một vòng học: DATA → FEATURES → REGIME → RESEARCH (meta-learning chọn phương pháp) → PROMOTION
→ LIVE PREDICTION → DECAY → PAPER TRADE → ATTRIBUTION → REPORT.
Chạy: python -m engine.run_cycle [--source vnstock|store|synthetic] [--as-of YYYY-MM-DD] [--trials N]"""
import argparse, json
import numpy as np, pandas as pd
from .config import CFG, ROOT, path, load_json
from . import data, features, regime, research, meta, knowledge, paper, attribution, report, llm_review
from . import ledger, experts, facts

def load_ledger():
    p = ROOT / "research/trials.csv"
    return pd.read_csv(p) if p.exists() else None

def cycle(as_of=None, trials=None, write_report=True, use_llm=True, seed=None, live=False):
    close, volume = data.load_panel(as_of)
    as_of = str((pd.Timestamp(as_of) if as_of else close.index[-1]).date())
    close, volume = close.loc[:as_of], volume.loc[:as_of]
    udates = close.index
    h = CFG["horizon_days"]
    ds = features.dataset(close, volume, h)
    reg_lab = regime.regimes(close)
    regime_now = str(reg_lab.iloc[-1])

    # RESEARCH — meta-learning phân bổ ngân sách thử nghiệm
    rng = np.random.default_rng(seed if seed is not None else int(pd.Timestamp(as_of).strftime("%Y%m%d")))
    bandit, ledger_df = meta.load(), load_ledger()
    registry = knowledge.load_registry()
    done = []
    n_trials = CFG["research"]["trials_per_cycle"] if trials is None else trials
    for _ in range(n_trials):
        method, spec = meta.next_spec(bandit, rng, ledger_df)
        if spec is None:
            break
        n_total = (0 if ledger_df is None else len(ledger_df)) + 1
        thr = research.threshold(n_total)
        oos, folds = research.walk_forward(ds, spec)
        m = research.metrics(oos, folds, reg_lab)
        status = research.classify(m, thr)
        mid = research.spec_id(spec)
        row = {"trial_id": f"T{n_total:05d}", "cycle_date": as_of, "method": method, "spec_id": mid,
               "features": ";".join(spec["features"]), "model": spec["model"], "ic_mean": m["ic_mean"],
               "ic_t": m["ic_t"], "net_ann": m["net_ann"], "fold_pos": m["fold_pos"], "threshold": thr,
               "status": status, "regimes": json.dumps(m["regimes"])}
        ledger_df = pd.concat([ledger_df, pd.DataFrame([row])], ignore_index=True) if ledger_df is not None else pd.DataFrame([row])
        meta.update(bandit, method, status)
        if status != "REJECTED":
            knowledge.write_candidate(mid, spec, m, status, row["trial_id"], as_of)
        was_new = mid not in registry
        knowledge.promote(registry, mid, spec, m, status, as_of)
        if was_new and mid in registry and use_llm:
            llm_review.review(mid, load_json(f"knowledge/candidates/{mid}.json", {}), m)
        done.append(row)
    if ledger_df is not None:
        ledger_df.to_csv(path("research/trials.csv"), index=False)
    meta.save(bandit)

    # LIVE PREDICTION + DECAY
    preds_today, allp = knowledge.live_predict(ds, registry, as_of, udates)
    alerts = knowledge.decay(registry, allp, ds, as_of)
    knowledge.save_registry(registry)

    # PAPER + ATTRIBUTION
    nav, decision = paper.run(as_of, close, preds_today, registry, udates)
    attr = attribution.run(close)
    n_total = 0 if ledger_df is None else len(ledger_df)

    # ---- v1.0 GĐ1: PREDICTION LEDGER ----
    resolved = ledger.resolve(close, as_of)
    news = facts.ingest_news(as_of) if live else {"new_items": 0, "errors": []}
    ex = experts.run(as_of, close) if use_llm else {"ran": False, "reasons": ["tắt bởi --no-llm"]}
    sc = ledger.scorecard(as_of)

    if write_report:
        report.write(as_of, regime_now, done, bandit, registry, nav, decision, attr, alerts,
                     research.threshold(max(1, n_total)), n_total)
        L = ["", "## Prediction Ledger (v1.0)", f"- Tin mới vào Fact Layer: {news['new_items']}"
             + (f" | lỗi nguồn: {len(news['errors'])}" if news["errors"] else ""),
             f"- Chuyên gia: " + (f"ghi {ex.get('recorded', 0)} dự báo, loại {ex.get('rejected', 0)}, "
                                   f"Devil's Advocate {ex.get('devils_advocate', 0)}" if ex.get("ran")
                                   else "KHÔNG CHẠY — " + "; ".join(ex.get("reasons", []))),
             f"- Dự báo đã chấm hôm nay: {len(resolved)} | Tổng: {sc['total_predictions']} dự báo, {sc['resolved']} đã chấm", ""]
        if sc["procedures"]:
            L += ["| Chuyên gia | n | Brier | Brier baseline mạnh nhất | Skill | Tỷ lệ đúng | Kết luận |", "|---|---|---|---|---|---|---|"]
            L += [f"| {k} | {v['n']} | {v['brier']} | {v['brier_base_rate']} | {v['brier_skill']} | {v['hit_rate']} | {v['verdict']} |"
                  for k, v in sc["procedures"].items()]
        with open(path(f"reports/cycle_{as_of}.md"), "a", encoding="utf-8") as f:
            f.write("\n".join(L) + "\n")
    return {"as_of": as_of, "trials": done, "alerts": alerts, "nav": nav, "decision": decision,
            "experts": ex, "resolved": len(resolved)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=CFG["data"]["source"])
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--trials", type=int, default=None)
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--force", action="store_true", help="chạy lại dù ngày này đã xử lý")
    a = ap.parse_args()
    if a.source == "vnstock":
        print("[ingest]", data.ingest_vnstock())
    elif a.source == "synthetic" and not (ROOT / CFG["data"]["store"]).exists():
        from .synthetic import make_store
        make_store()
    last = load_json("state/ENGINE_STATE.json", {}).get("as_of")
    newest = str(data.load_panel(a.as_of)[0].index[-1].date())
    if last == newest and not a.force:
        print(f"[cycle] Ngày {newest} đã xử lý (có thể hôm nay nghỉ giao dịch). Bỏ qua.")
        return
    r = cycle(a.as_of, a.trials, use_llm=not a.no_llm, live=(a.source == "vnstock"))
    print(f"[cycle] {r['as_of']} | thử nghiệm: {len(r['trials'])} | cảnh báo: {r['alerts']} | NAV: {r['nav']:,.0f}")

if __name__ == "__main__":
    main()
