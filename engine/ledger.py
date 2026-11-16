"""PREDICTION LEDGER — trái tim của v1.0.
Dự báo ghi TRƯỚC khi biết kết quả (append-only, commit vào git). Kết quả ghi ở file riêng.
Auditor, Resolution, Scorecard đều là code tất định — không LLM nào tự chấm mình."""
import hashlib, json, math, re, sys
import numpy as np, pandas as pd
from .config import CFG, ROOT, REPO, path, save_json

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from tools.laws_checks import line_hash  # noqa: E402  một thuật toán hash chuỗi cho mọi bên ghi Ledger

PRED, RES = "ledger/predictions.jsonl", "ledger/resolutions.jsonl"

def _load(rel):
    p = ROOT / rel
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []

def _append(rel, rows):
    with open(path(rel), "a", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")

def _append_chained(rel, rows):
    """Ghi nối tiếp vào Ledger có hash chuỗi prev_hash/hash, cùng luật với tools/ledger_intake.py
    (tools/laws_checks.check_ledger_chain kiểm mọi dòng)."""
    old = _load(rel)
    prev = old[-1].get("hash", "GENESIS") if old else "GENESIS"
    out = []
    for r in rows:
        r = {**r, "prev_hash": prev}
        r["hash"] = line_hash(r)
        prev = r["hash"]
        out.append(r)
    with open(path(rel), "a", encoding="utf-8") as f:
        for r in out: f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

def is_issue_row(p):
    """Dòng ghi từ GitHub Issue 'Forecast' (tools/ledger_intake.py). Không chấm bằng giá ở đây."""
    return "issue_number" in p

def is_engine_row(p):
    """Dòng do engine/experts ghi: có id và luật chấm dạng dict có ticker → chấm tự động bằng giá."""
    rr = p.get("resolution_rule")
    return not is_issue_row(p) and "id" in p and isinstance(rr, dict) and "ticker" in rr

def base_rate(close, ticker, h):
    """Tỷ lệ lịch sử mã này vượt bình quân universe trong h phiên (do code tính)."""
    fwd = close.shift(-h) / close - 1
    ex = fwd.sub(fwd.mean(axis=1), axis=0)[ticker].dropna()
    return float(np.clip((ex > 0).mean(), 0.05, 0.95)) if len(ex) > 50 else 0.5

# ---------------- AUDITOR (code) ----------------
def audit(p, universe, fact_ids, as_of):
    L = CFG["ledger"]; errs = []
    if p.get("ticker") not in universe: errs.append("mã không thuộc universe")
    if p.get("horizon") not in L["horizons"]: errs.append(f"horizon phải thuộc {L['horizons']}")
    try:
        pr = float(p.get("probability"))
        if not (L["min_p"] <= pr <= L["max_p"]): errs.append(f"xác suất ngoài [{L['min_p']}, {L['max_p']}]")
    except (TypeError, ValueError): errs.append("xác suất không phải số")
    refs = p.get("evidence_refs") or []
    if p.get("requires_evidence", True):
        if not refs: errs.append("không có evidence_refs")
        missing = [r for r in refs if r not in fact_ids]
        if missing: errs.append(f"nguồn không tồn tại trong Fact Layer: {missing}")
    if not str(p.get("claim", "")).strip(): errs.append("thiếu claim")
    return errs

def record(preds, as_of, universe, fact_ids, close):
    """Kiểm toán rồi ghi. Trả về (đã ghi, bị loại)."""
    ok, rejected = [], []
    for p in preds:
        errs = audit(p, universe, fact_ids, as_of)
        if errs:
            rejected.append({**p, "audit_errors": errs}); continue
        h = int(p["horizon"])
        row = {"id": None, "created_at": as_of, "procedure": p["procedure"], "claim": p["claim"],
               "question": f"{p['ticker']} vượt bình quân universe trong {h} phiên, vào lệnh tại close phiên kế tiếp sau {as_of}",
               "resolution_rule": {"type": "excess_return_positive", "ticker": p["ticker"], "horizon": h,
                                   "benchmark": "universe_equal_weight", "entry": "close_t+1"},
               "probability": round(float(p["probability"]), 3), "base_rate": round(base_rate(close, p["ticker"], h), 3),
               "evidence_refs": p.get("evidence_refs", []), "links": p.get("links", {}), "note": p.get("note", "")}
        row["id"] = "P-" + hashlib.sha1(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
        ok.append(row)
    _append_chained(PRED, ok)
    if rejected:
        _append("ledger/rejected.jsonl", [{**r, "rejected_at": as_of} for r in rejected])
    return ok, rejected

# ---------------- RESOLUTION (code) ----------------
def resolve(close, as_of, bad=None):
    """Chấm bằng GIÁ ĐIỀU CHỈNH. Mã có ô lỗi dữ liệu trong cửa sổ chấm → VOID (không tính điểm);
    mã khác có lỗi trong cửa sổ bị loại khỏi bình quân universe."""
    done = {r["prediction_id"] for r in _load(RES)}
    idx = close.index
    new = []
    for p in _load(PRED):
        if not is_engine_row(p): continue                # dự báo từ Issue: phân định theo resolution_source, không bằng giá
        if p["id"] in done: continue
        rr = p["resolution_rule"]; h = rr["horizon"]
        c = pd.Timestamp(p["created_at"])
        pos = idx.searchsorted(c, side="right")          # phiên kế tiếp = điểm vào lệnh
        if pos + h >= len(idx): continue                 # chưa đến hạn
        t0, t1 = idx[pos], idx[pos + h]
        ret = close.loc[t1] / close.loc[t0] - 1
        if bad is not None:
            dirty = bad.loc[(bad.index > t0) & (bad.index <= t1)].any()
            if bool(dirty.get(rr["ticker"], False)):
                new.append({"prediction_id": p["id"], "resolved_at": as_of, "entry_date": str(t0.date()),
                            "exit_date": str(t1.date()), "excess_return": None, "outcome": None,
                            "void": "lỗi dữ liệu giá trong cửa sổ chấm"})
                continue
            ret = ret[~dirty.reindex(ret.index).fillna(False).astype(bool)]
        if pd.isna(ret.get(rr["ticker"])): continue
        excess = float(ret[rr["ticker"]] - ret.mean())
        new.append({"prediction_id": p["id"], "resolved_at": as_of, "entry_date": str(t0.date()),
                    "exit_date": str(t1.date()), "excess_return": round(excess, 5), "outcome": int(excess > 0)})
    _append(RES, new)
    return new

# ---------------- SCORECARD (code) ----------------
TARGET_DISAGREEMENTS = 194        # ARCHITECTURE v3.0 §4.2: phát hiện A đúng 60% so với 50%, độ mạnh 80%, α 0,05

def _qkey(p):
    return (re.sub(r"\s+", " ", str(p.get("question", ""))).strip().lower(), str(p.get("resolve_at", "")))

def _calibration(ps, os_):
    out = {}
    for k in range(10):
        lo, hi = k / 10, (k + 1) / 10
        idx = [i for i, p in enumerate(ps) if lo <= p < hi or (k == 9 and p == 1.0)]
        if idx:
            out[f"{lo:.1f}-{hi:.1f}"] = {"n": len(idx), "mean_p": round(float(np.mean([ps[i] for i in idx])), 3),
                                              "hit_rate": round(float(np.mean([os_[i] for i in idx])), 3)}
    return out

def _binom_sf(k, n):
    """P(X ≥ k) với X ~ Binomial(n, 0,5): A đúng trên tập bất đồng có hơn tung đồng xu không."""
    return float(sum(math.comb(n, j) for j in range(k, n + 1)) / 2 ** n) if n else 1.0

def issue_summary(all_rows, R):
    """Chấm dự báo từ Issue theo ARCHITECTURE v3.0 §4.1 bước 5: theo ghế (n, Brier, Brier xác suất nền, hiệu chuẩn);
    cặp A–B cùng câu hỏi: tỷ lệ bất đồng (hai ghế ở hai phía 0,5) và độ đúng của A trên tập bất đồng đã phân định."""
    done = {r.get("prediction_id") for r in R}
    outcome = {r.get("prediction_id"): r.get("outcome") for r in R if r.get("outcome") is not None}
    issue = [p for p in all_rows if is_issue_row(p)]
    by_seat, scores = {}, {}
    for p in issue:
        s = str(p.get("seat", "?"))
        d = by_seat.setdefault(s, {"n": 0, "resolved": 0, "pending": 0})
        d["n"] += 1
        if p.get("id") in done: d["resolved"] += 1
        else: d["pending"] += 1
    for s in sorted(by_seat):
        rows = [p for p in issue if str(p.get("seat")) == s and p.get("id") in outcome]
        if not rows:
            continue
        ps = [float(p["p"]) for p in rows]; os_ = [int(outcome[p["id"]]) for p in rows]
        bs = [float(p.get("base_rate", 0.5)) for p in rows]
        scores[s] = {"n": len(rows), "brier": round(float(np.mean([(a - b) ** 2 for a, b in zip(ps, os_)])), 4),
                     "brier_base_rate": round(float(np.mean([(a - b) ** 2 for a, b in zip(bs, os_)])), 4),
                     "mean_p": round(float(np.mean(ps)), 3), "hit_rate": round(float(np.mean(os_)), 3),
                     "calibration": _calibration(ps, os_)}
    first = {}
    for p in sorted(issue, key=lambda r: r.get("issue_number", 0)):
        first.setdefault((_qkey(p), str(p.get("seat"))), p)
    pairs = [(a, first[(k, "B")]) for (k, seat), a in first.items() if seat == "A" and (k, "B") in first]
    dis = [(a, b) for a, b in pairs if (float(a["p"]) - 0.5) * (float(b["p"]) - 0.5) < 0]
    dis_res = [(a, b) for a, b in dis if a.get("id") in outcome]
    a_right = sum(1 for a, _ in dis_res if (float(a["p"]) > 0.5) == (int(outcome[a["id"]]) == 1))
    n = len(dis_res)
    ab = {"pairs": len(pairs), "disagreements": len(dis),
          "disagreement_rate": round(len(dis) / len(pairs), 3) if pairs else None,
          "disagreements_resolved": n, "a_correct": a_right,
          "a_accuracy": round(a_right / n, 3) if n else None,
          "p_value_a_better_than_coin": round(_binom_sf(a_right, n), 4) if n else None,
          "target_disagreements": TARGET_DISAGREEMENTS,
          "verdict": (f"CHƯA ĐỦ MẪU ({n}/{TARGET_DISAGREEMENTS} bất đồng đã phân định)" if n < TARGET_DISAGREEMENTS else
                      "A HƠN B CÓ Ý NGHĨA" if _binom_sf(a_right, n) < 0.05 else "CHƯA THẤY A HƠN B")}
    if pairs and len(dis) / len(pairs) < 0.10 and len(pairs) >= 20:
        ab["warning"] = "tỷ lệ bất đồng < 10%: thư viện chưa làm A khác B (ARCHITECTURE v3.0 §9)"
    return {"total": len(issue), "by_seat": by_seat, "scores": scores, "ab": ab}

def scorecard(as_of):
    all_rows = _load(PRED)
    P = {p["id"]: p for p in all_rows if is_engine_row(p)}
    R = _load(RES)
    rows = [{**P[r["prediction_id"]], **r} for r in R if r.get("prediction_id") in P and r.get("outcome") is not None]
    void = sum(1 for r in R if r.get("prediction_id") in P and r.get("outcome") is None)
    out = {"as_of": as_of, "total_predictions": len(all_rows), "resolved": len(rows), "void_data_error": void,
           "issue_forecasts": issue_summary(all_rows, R), "procedures": {}}
    if rows:
        df = pd.DataFrame(rows)
        for proc, g in df.groupby("procedure"):
            p, o, b = g.probability.astype(float), g.outcome.astype(float), g.base_rate.astype(float)
            brier = float(((p - o) ** 2).mean())
            baselines = {"base_rate": float(((b - o) ** 2).mean()), "coin_0.5": float(((0.5 - o) ** 2).mean())}
            best = min(baselines, key=baselines.get)          # phải thắng baseline MẠNH NHẤT
            brier_base = baselines[best]
            bss = 1 - brier / brier_base if brier_base > 0 else 0.0
            buckets = {}
            for lo in np.arange(0.0, 1.0, 0.1):
                m = (p >= lo) & (p < lo + 0.1)
                if m.sum(): buckets[f"{lo:.1f}-{lo+0.1:.1f}"] = {"n": int(m.sum()), "mean_p": round(float(p[m].mean()), 3),
                                                                "hit_rate": round(float(o[m].mean()), 3)}
            n = len(g)
            verdict = ("CHƯA ĐỦ MẪU" if n < CFG["ledger"]["min_n_for_verdict"] else
                       "HƠN BASELINE" if bss > 0 else "KHÔNG HƠN BASELINE")
            out["procedures"][proc] = {"n": n, "brier": round(brier, 4), "brier_base_rate": round(brier_base, 4),
                                       "brier_skill": round(bss, 4), "best_baseline": best, "hit_rate": round(float(o.mean()), 3),
                                       "mean_p": round(float(p.mean()), 3), "calibration": buckets, "verdict": verdict}
    save_json("reports/scorecard.json", out)
    return out
