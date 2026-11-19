"""Một vòng học: DATA → FEATURES → REGIME → RESEARCH (meta-learning chọn phương pháp) → PROMOTION
→ LIVE PREDICTION → DECAY → PAPER TRADE → ATTRIBUTION → REPORT.
Chạy: python -m engine.run_cycle [--source live|store|synthetic] [--as-of YYYY-MM-DD] [--trials N]
  live = tải dữ liệu mới theo config data.sources (hiện: yahoo) rồi chạy; "vnstock" là tên cũ của "live"."""
import argparse, json
import numpy as np, pandas as pd
from .config import CFG, ROOT, path, load_json, save_json
from . import data, features, regime, research, meta, knowledge, paper, attribution, report, llm_review
from . import ledger, experts, facts, knowledge_notes

def load_ledger():
    p = ROOT / "research/trials.csv"
    return pd.read_csv(p) if p.exists() else None

def cycle(as_of=None, trials=None, write_report=True, use_llm=True, seed=None, live=False, ingest=None):
    mk = data.load_market(as_of)                    # GIÁ ĐIỀU CHỈNH point-in-time + cờ lỗi dữ liệu
    close, volume, bad, quality = mk["close"], mk["volume"], mk["bad"], mk["quality"]
    as_of = str((pd.Timestamp(as_of) if as_of else close.index[-1]).date())
    close, volume, bad = close.loc[:as_of], volume.loc[:as_of], bad.loc[:as_of]
    skip = quality["skip"]                          # lỗi dữ liệu vượt ngưỡng → không nghiên cứu, không dự báo
    udates = close.index
    h = CFG["horizon_days"]
    ds = features.dataset(close, volume, h, bad)
    reg_lab = regime.regimes(close, bad)
    regime_now = str(reg_lab.iloc[-1])

    # RESEARCH — meta-learning phân bổ ngân sách thử nghiệm
    rng = np.random.default_rng(seed if seed is not None else int(pd.Timestamp(as_of).strftime("%Y%m%d")))
    bandit, ledger_df = meta.load(), load_ledger()
    registry = knowledge.load_registry()
    done = []
    n_trials = 0 if skip else (CFG["research"]["trials_per_cycle"] if trials is None else trials)
    for _ in range(n_trials):
        method, spec = meta.next_spec(bandit, rng, ledger_df)
        if spec is None:
            break
        n_total = research.next_trial_number(ledger_df)
        thr = research.threshold(n_total)
        reg_hash = research.register_trial(f"T{n_total:05d}", as_of, method, spec, thr)   # L-06: đăng ký trước
        oos, folds = research.walk_forward(ds, spec)
        m = research.metrics(oos, folds, reg_lab)
        status = research.classify(m, thr)
        mid = research.spec_id(spec)
        prev_sr = (pd.to_numeric(ledger_df["sharpe"], errors="coerce").dropna().tolist()
                   if ledger_df is not None and "sharpe" in ledger_df else [])
        var_sr = research.sharpe_variance(prev_sr, m["sharpe"], m["sr_T"])   # N = mọi lần thử từ đầu (kể cả chưa ghi Sharpe)
        dsr = research.deflated_sharpe(m["sharpe"], m["sr_T"], m["sr_skew"], m["sr_kurt"], n_total, var_sr)
        row = {"trial_id": f"T{n_total:05d}", "cycle_date": as_of, "method": method, "spec_id": mid,
               "features": ";".join(spec["features"]), "model": spec["model"], "ic_mean": m["ic_mean"],
               "ic_t": m["ic_t"], "net_ann": m["net_ann"], "fold_pos": m["fold_pos"], "threshold": thr,
               "status": status, "regimes": json.dumps(m["regimes"]),
               "sharpe": m["sharpe"], "sharpe_ann": m["sharpe_ann"], "dsr": dsr, "registry_hash": reg_hash,
               "max_dd": m["max_dd"]}        # max_dd chỉ vào báo cáo; research/trials.csv giữ đúng 17 cột (L-06)
        ledger_df = pd.concat([ledger_df, pd.DataFrame([row])], ignore_index=True) if ledger_df is not None else pd.DataFrame([row])
        meta.update(bandit, method, status)
        if status != "REJECTED":
            knowledge.write_candidate(mid, spec, m, status, row["trial_id"], as_of)
        was_new = mid not in registry
        knowledge.promote(registry, mid, spec, m, status, as_of)
        if was_new and mid in registry and use_llm:
            llm_review.review(mid, load_json(f"knowledge/candidates/{mid}.json", {}), m, as_of)
        done.append(row)
    research.append_trial_results(done)                   # chỉ ghi thêm; dòng cũ giữ nguyên từng ký tự (L-06)
    meta.save(bandit)

    # LIVE PREDICTION + DECAY
    if skip:
        preds_today, alerts = pd.DataFrame(columns=["date", "model_id", "ticker", "score"]), []
    else:
        preds_today, allp = knowledge.live_predict(ds, registry, as_of, udates)
        alerts = knowledge.decay(registry, allp, ds, as_of)
    knowledge.save_registry(registry)

    # PAPER + ATTRIBUTION
    nav, decision = paper.run(as_of, close, preds_today, registry, udates, events=mk["events"], frozen=skip)
    attr = attribution.run(close, bad)
    n_total = research.total_trials(ledger_df)            # kể cả lần thử đăng ký rồi bỏ dở (L-06)

    # ---- v1.0 GĐ1: PREDICTION LEDGER ----
    resolved = ledger.resolve(close, as_of, bad)
    news = facts.ingest_news(as_of) if live else {"new_items": 0, "errors": []}
    if skip:
        ex = {"ran": False, "reasons": [f"tạm dừng: tỷ lệ lỗi dữ liệu {quality['error_rate_window']:.2%} "
                                        f"> ngưỡng {quality['max_error_rate']:.2%}"]}
    else:
        ex = experts.run(as_of, close) if use_llm else {"ran": False, "reasons": ["tắt bởi --no-llm"]}
    sc = ledger.scorecard(as_of)
    outdated = knowledge_notes.mark_outdated(ROOT)        # L-08: ghi chú dựa trên văn bản hết hiệu lực → OUTDATED

    if write_report:
        report.write(as_of, regime_now, done, bandit, registry, nav, decision, attr, alerts,
                     research.threshold(max(1, n_total)), n_total, quality=quality, ingest=ingest,
                     news_errors=news["errors"])
        L = ["", "## Prediction Ledger (v1.0)", f"- Tin mới vào Fact Layer: {news['new_items']}"
             + (f" | lỗi nguồn: {len(news['errors'])}" if news["errors"] else ""),
             f"- Chuyên gia: " + (f"ghi {ex.get('recorded', 0)} dự báo, loại {ex.get('rejected', 0)}, "
                                   f"Devil's Advocate {ex.get('devils_advocate', 0)}" if ex.get("ran")
                                   else "KHÔNG CHẠY — " + "; ".join(ex.get("reasons", []))),
             f"- Dự báo đã chấm hôm nay: {len(resolved)} | Tổng: {sc['total_predictions']} dự báo, {sc['resolved']} đã chấm",
             "- Dự báo từ Issue: " + (", ".join(f"ghế {k}: {v['n']} (đã phân định {v['resolved']}, VOID {v['void']}, chờ {v['pending']})"
                                                 for k, v in sorted(sc["issue_forecasts"]["by_seat"].items()))
                                       or "chưa có")
             + (f" | dòng hỏng bị bỏ qua: {sc['issue_forecasts']['malformed']}" if sc["issue_forecasts"].get("malformed") else ""),
             "- Thời điểm (L-05, ADR-0011): ghi {recorded}, có bằng chứng hợp lệ {timing_valid}, đã phân định {resolved}, đã phân định "
             "và hợp lệ {resolved_timing_valid}".format(**sc["issue_forecasts"]["counts"])
             + f" — nguồn xác nhận: {sc['issue_forecasts']['timing_verification_source']}. Số năng lực dưới đây chỉ tính dự báo hợp lệ; "
             "số toàn sổ nằm ở raw_audit trong reports/scorecard.json (không phải bằng chứng năng lực).",
             "- Cặp A–B: {pairs} cặp (lẻ {unpaired}, khác ngày {not_same_day}), bất đồng trong phạm vi phép thử {disagreements} "
             "(ngoài phạm vi — event_before_date, ADR-0002: {disagreements_out_of_scope}), đã phân định "
             "{disagreements_resolved}, VOID {disagreements_void}, A đúng {a_correct}, mâu thuẫn {inconsistent_outcomes} — {verdict}".format(**sc["issue_forecasts"]["ab"])
             + ("  ⚠ " + sc["issue_forecasts"]["ab"]["warning_inconsistent"] if "warning_inconsistent" in sc["issue_forecasts"]["ab"] else ""),
             "- VOID (câu hỏi bị hủy; trong kiểm định A–B tính theo hướng bất lợi cho kết luận đang xét): "
             + (", ".join(f"ghế {k}: {v['void']}/{v['closed']} đã đóng, Brier nếu VOID tính là sai "
                          f"{'chưa có' if v['brier_void_worst'] is None else v['brier_void_worst']}"
                          for k, v in sc["issue_forecasts"]["void"]["by_seat"].items()) or "chưa có")
             + " | cặp: {void}/{closed}".format(**sc["issue_forecasts"]["void"]["pairs"])
             + " | cặp bất đồng: {void}/{closed}".format(**sc["issue_forecasts"]["void"]["disagreements"]),
             f"- Ghi chú chuyển OUTDATED (L-08): {', '.join(outdated) if outdated else 'không có'}",
             "- Lần thử đã đăng ký nhưng không có kết quả (L-06; vẫn tính vào số lần thử): "
             + (", ".join(research.abandoned_trials(ledger_df)) or "không có"), ""]
        if sc["procedures"]:
            L += ["| Chuyên gia | n | Brier | Brier baseline TỰ KHAI/đồng xu (lấy cái mạnh hơn) | Skill | Độ chính xác chiều | Tỷ lệ YES quan sát | Kết luận |",
                  "|---|---|---|---|---|---|---|---|"]
            L += [f"| {k} | {v['n']} | {v['brier']} | {v['brier_base_rate']} | {v['brier_skill']} | "
                  f"{'—' if v['directional_accuracy'] is None else v['directional_accuracy']} | {v['observed_yes_rate']} | {v['verdict']} |"
                  for k, v in sc["procedures"].items()]
            L += ["", "Độ chính xác chiều: p>0,5 gọi YES, p<0,5 gọi NO; p=0,5 không vào mẫu số. "
                  "Tỷ lệ YES quan sát không phải tỷ lệ đúng. Brier và skill giữ nguyên công thức. "
                  "'HƠN BASELINE' chỉ thắng base_rate do dòng tự khai hoặc đồng xu 0,5 — chưa có baseline độc lập đã ghim."]
        with open(path(f"reports/cycle_{as_of}.md"), "a", encoding="utf-8") as f:
            f.write("\n".join(L) + "\n")
    return {"as_of": as_of, "trials": done, "alerts": alerts, "nav": nav, "decision": decision,
            "experts": ex, "resolved": len(resolved), "quality": quality}

def refresh_scorecard_report(as_of, attempts=3, while_writing=None):
    """Viết lại reports/scorecard.json từ Ledger hiện tại. Không đăng ký trial, không backtest, không đụng NAV giấy hay model.
    Nếu sổ đổi trong lúc ghi, thử lại tối đa `attempts` lần. Hết lần mà chưa FRESH thì trả 1 — kể cả khi lần ghi cuối
    tình cờ khớp sổ vừa bị sửa — và không coi bản đó là được phát hành. Đã FRESH đúng `as_of` thì không ghi lại
    (`generated_at` không đổi). Không bật TTC_PROVENANCE_ONLINE: điểm năng lực chỉ do scorecard() phát khi xuất xứ GitHub
    đã được xác nhận.
    `while_writing(i)` nếu có: gọi sau khi chụp sổ và trước scorecard(), để thử nghiệm mô phỏng robot ghi xen giữa."""
    from tools.laws_checks import scorecard_freshness, scorecard_sources
    root = ROOT
    attempts = max(1, int(attempts))
    if while_writing is None:
        status, _why = scorecard_freshness(root)
        if status == "FRESH":
            try:
                current = json.loads((root / "reports" / "scorecard.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                current = {}
            if current.get("as_of") == as_of:
                print(f"[scorecard] đã FRESH as_of={as_of} — không ghi lại")
                return 0
    last = None
    for i in range(attempts):
        before = scorecard_sources(root)
        if while_writing is not None:
            while_writing(i)
        sc = ledger.scorecard(as_of)
        after = scorecard_sources(root)
        recorded = (sc.get("freshness") or {}).get("sources")
        if before != after or recorded != after:
            last = ("drift",)
            print("[scorecard] sổ đổi trong lúc ghi — thử lại")
            continue
        status, why = scorecard_freshness(root)
        if status == "FRESH":
            print(f"[scorecard] FRESH as_of={as_of} predictions={sc.get('total_predictions')}")
            return 0
        last = (status, why)
        if status == "INVALID":
            print(f"[scorecard] INVALID — không phát hành: {why}")
            return 1
    print(f"[scorecard] không ổn định sau {attempts} lần: {last}")
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=CFG["data"]["source"])
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--trials", type=int, default=None)
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--force", action="store_true", help="chạy lại dù ngày này đã xử lý")
    ap.add_argument("--scorecard-only", action="store_true",
                    help="chỉ sinh lại scorecard từ Ledger; không nghiên cứu, không trial, không paper, không model")
    a = ap.parse_args()
    if a.scorecard_only:
        as_of = a.as_of or str(data.load_panel(None)[0].index[-1].date())
        raise SystemExit(refresh_scorecard_report(as_of))
    live = a.source in ("live", "vnstock")
    ing = None
    if live:
        ing = data.ingest()
        print(f"[ingest] nguồn {ing['sources']} | dòng mới {ing['new_rows']} {ing['rows_by_source']} | "
              f"lỗi {len(ing['errors'])}")
        for e in ing["errors"]:
            print(f"   lỗi {e['ticker']} [{e['source']}]: {e['error']}")
        print("[derived] tính lại hệ số điều chỉnh + cờ lỗi dữ liệu lúc", data.write_derived())
    elif a.source == "synthetic" and not (ROOT / CFG["data"]["store"]).exists():
        from .synthetic import make_store
        make_store()
    last = load_json("state/ENGINE_STATE.json", {}).get("as_of")
    newest = str(data.load_panel(a.as_of)[0].index[-1].date())
    if last == newest and not a.force:
        if ing is not None:                          # vẫn lưu nhật ký tải (kể cả lỗi) dù không chạy vòng học
            st = load_json("state/ENGINE_STATE.json", {})
            st["data_ingest"] = ing
            save_json("state/ENGINE_STATE.json", st)
        # Giá không đổi không có nghĩa Ledger không đổi. Chỉ viết lại scorecard; không mở trial.
        if refresh_scorecard_report(newest) != 0:
            raise SystemExit(1)
        print(f"[cycle] Ngày {newest} đã xử lý (có thể hôm nay nghỉ giao dịch). Bỏ qua nghiên cứu.")
        return
    r = cycle(a.as_of, a.trials, use_llm=not a.no_llm, live=live, ingest=ing)
    print(f"[cycle] {r['as_of']} | thử nghiệm: {len(r['trials'])} | cảnh báo: {r['alerts']} | NAV: {r['nav']:,.0f}")

if __name__ == "__main__":
    main()
