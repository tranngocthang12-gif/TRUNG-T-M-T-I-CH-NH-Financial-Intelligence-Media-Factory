"""PREDICTION LEDGER — trái tim của v1.0.
Dự báo ghi TRƯỚC khi biết kết quả (append-only, commit vào git). Kết quả ghi ở file riêng.
Auditor, Resolution, Scorecard đều là code tất định — không LLM nào tự chấm mình."""
import hashlib, json, math, sys
import numpy as np, pandas as pd
from .config import CFG, ROOT, REPO, path, save_json

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from tools.laws_checks import line_hash  # noqa: E402  một thuật toán hash chuỗi cho mọi bên ghi Ledger
from tools.ledger_intake import qkey as _qkey, vn_day  # noqa: E402  một định nghĩa "câu hỏi" và "ngày" cho nhận/phân định/chấm

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
        r = {**_finite(r), "prev_hash": prev}
        r["hash"] = line_hash(r)
        prev = r["hash"]
        out.append(r)
    with open(path(rel), "a", encoding="utf-8") as f:
        for r in out: f.write(json.dumps(r, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")

def _finite(x):
    """NaN/±vô cực không phải JSON chuẩn (laws_checks.check_ledger_chain từ chối): đổi thành null trước khi ghi sổ."""
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    if isinstance(x, dict):
        return {k: _finite(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_finite(v) for v in x]
    return x

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
    _append_chained(RES, new)
    return new

# ---------------- SCORECARD (code) ----------------
TARGET_DISAGREEMENTS = 194        # ARCHITECTURE v3.0 §4.2: phát hiện A đúng 60% so với 50%, độ mạnh 80%, α 0,05

MIN_PAIRS_FOR_RATE_WARNING = 60   # governance/CONTROL_B_PROMPT.md: "dưới 10% sau 60 câu" thì mở ADR đổi nhóm B

def _calibration(ps, os_):
    out = {}
    for k in range(10):
        lo, hi = k / 10, (k + 1) / 10
        idx = [i for i, p in enumerate(ps) if lo <= p < hi or (k == 9 and p == 1.0)]
        if idx:
            out[f"{lo:.1f}-{hi:.1f}"] = {"n": len(idx), "mean_p": round(float(np.mean([ps[i] for i in idx])), 3),
                                              "hit_rate": round(float(np.mean([os_[i] for i in idx])), 3)}
    return out

def _binom_two_sided(k, n):
    """p hai phía của kiểm định nhị thức với p0 = 0,5 (khớp cỡ mẫu 194 ở §4.2, vốn tính cho kiểm định hai phía):
    p = 2·P(X ≥ max(k, n−k)), chặn ≤ 1."""
    if not n:
        return 1.0
    m = max(k, n - k)
    return float(min(1.0, 2 * sum(math.comb(n, j) for j in range(m, n + 1)) / 2 ** n))

def _valid_issue_row(p):
    """Dòng Issue đủ để chấm: có id, seat A/B, p là số trong (0, 1). Dòng hỏng không được làm vỡ vòng học."""
    try:
        return bool(p.get("id")) and str(p.get("seat")) in ("A", "B") and 0.0 < float(p["p"]) < 1.0
    except (KeyError, TypeError, ValueError):
        return False

def _same_day(a, b):
    try:
        return vn_day(a["issue_created_at"]) == vn_day(b["issue_created_at"])
    except (KeyError, TypeError, ValueError):
        return False

def issue_summary(all_rows, R):
    """Chấm dự báo từ Issue theo ARCHITECTURE v3.0 §4.1 bước 5 và ADR-0003.
    Theo ghế: n, đã phân định, VOID, chờ; Brier, Brier của xác suất nền, hiệu chuẩn.
    Cặp A–B: cùng câu hỏi (question + resolve_at), ghi cùng ngày (giờ VN, §4.2). Bất đồng = hai ghế ở hai phía 0,5.
    Chỉ chấm cặp mà cả A và B đã phân định cùng một sự thật.
    Kiểm định CHỐT MẪU: phán quyết chỉ tính trên đúng 194 bất đồng được phân định ĐẦU TIÊN (theo thứ tự ghi trong sổ),
    kiểm định nhị thức hai phía với p0 = 0,5 — không xem lại mỗi vòng trên mẫu lớn dần (tránh dừng tùy ý)."""
    res_order = {r.get("prediction_id"): i for i, r in enumerate(R)}
    done = set(res_order)
    outcome = {r.get("prediction_id"): int(r["outcome"]) for r in R if r.get("outcome") in (0, 1)}
    void_ids = {r.get("prediction_id") for r in R if r.get("outcome") is None}
    raw = [p for p in all_rows if is_issue_row(p)]
    issue = [p for p in raw if _valid_issue_row(p)]
    by_seat, scores = {}, {}
    for p in issue:
        d = by_seat.setdefault(str(p["seat"]), {"n": 0, "resolved": 0, "void": 0, "pending": 0})
        d["n"] += 1
        if p["id"] in outcome: d["resolved"] += 1
        elif p["id"] in void_ids: d["void"] += 1
        elif p["id"] not in done: d["pending"] += 1
    for s in sorted(by_seat):
        rows = [p for p in issue if str(p["seat"]) == s and p["id"] in outcome]
        if not rows:
            continue
        ps = [float(p["p"]) for p in rows]; os_ = [outcome[p["id"]] for p in rows]
        bs = []
        for p in rows:
            try: bs.append(min(1.0, max(0.0, float(p.get("base_rate", 0.5)))))
            except (TypeError, ValueError): bs.append(0.5)
        scores[s] = {"n": len(rows), "brier": round(float(np.mean([(a - b) ** 2 for a, b in zip(ps, os_)])), 4),
                     "brier_base_rate": round(float(np.mean([(a - b) ** 2 for a, b in zip(bs, os_)])), 4),
                     "brier_coin": round(float(np.mean([(0.5 - b) ** 2 for b in os_])), 4),
                     "mean_p": round(float(np.mean(ps)), 3), "hit_rate": round(float(np.mean(os_)), 3),
                     "calibration": _calibration(ps, os_)}
    by_q = {}
    for p in sorted(issue, key=lambda r: r.get("issue_number", 0)):
        by_q.setdefault(_qkey(p), {"A": [], "B": []})[str(p["seat"])].append(p)
    pairs, unpaired, not_same_day = [], 0, 0
    for g in by_q.values():
        for a, b in zip(g["A"], g["B"]):
            if _same_day(a, b): pairs.append((a, b))
            else: not_same_day += 1
        unpaired += abs(len(g["A"]) - len(g["B"]))
    dis = [(a, b) for a, b in pairs if (float(a["p"]) - 0.5) * (float(b["p"]) - 0.5) < 0]
    both = [(a, b) for a, b in dis if a["id"] in outcome and b["id"] in outcome]
    inconsistent = sum(1 for a, b in both if outcome[a["id"]] != outcome[b["id"]])
    dis_res = sorted(((a, b) for a, b in both if outcome[a["id"]] == outcome[b["id"]]),
                     key=lambda ab: (res_order.get(ab[0]["id"], 0), ab[0].get("issue_number", 0)))
    def right(a): return (float(a["p"]) > 0.5) == (outcome[a["id"]] == 1)
    n_all, a_all = len(dis_res), sum(1 for a, _ in dis_res if right(a))
    fixed = dis_res[:TARGET_DISAGREEMENTS]
    n, a_right = len(fixed), sum(1 for a, _ in fixed if right(a))
    pval = _binom_two_sided(a_right, n) if n == TARGET_DISAGREEMENTS else None
    ab = {"pairs": len(pairs), "unpaired": unpaired, "not_same_day": not_same_day, "disagreements": len(dis),
          "disagreement_rate": round(len(dis) / len(pairs), 3) if pairs else None,
          "disagreements_resolved": n_all, "inconsistent_outcomes": inconsistent, "a_correct": a_all,
          "a_accuracy": round(a_all / n_all, 3) if n_all else None,
          "target_disagreements": TARGET_DISAGREEMENTS,
          "fixed_sample": {"n": n, "a_correct": a_right, "p_value_two_sided_vs_coin": round(pval, 4) if pval is not None else None},
          "verdict": (f"CHƯA ĐỦ MẪU ({n}/{TARGET_DISAGREEMENTS} bất đồng đã phân định)" if n < TARGET_DISAGREEMENTS else
                      "A HƠN B CÓ Ý NGHĨA" if pval < 0.05 and a_right > n / 2 else
                      "B HƠN A CÓ Ý NGHĨA" if pval < 0.05 else "CHƯA THẤY KHÁC BIỆT A–B")}
    if inconsistent:
        ab["warning_inconsistent"] = f"{inconsistent} cặp có hai outcome khác nhau cho cùng câu hỏi — kiểm ledger/resolutions.jsonl"
    if len(pairs) >= MIN_PAIRS_FOR_RATE_WARNING and len(dis) / len(pairs) < 0.10:
        ab["warning"] = "tỷ lệ bất đồng < 10% sau 60 cặp: mở ADR đổi nhóm B sang nhà cung cấp khác (CONTROL_B_PROMPT, ARCHITECTURE §9)"
    out = {"total": len(raw), "by_seat": by_seat, "scores": scores, "ab": ab}
    if len(raw) != len(issue):
        out["malformed"] = len(raw) - len(issue)
    return out

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
