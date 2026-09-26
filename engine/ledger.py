"""PREDICTION LEDGER — trái tim của v1.0.
Dự báo ghi TRƯỚC khi biết kết quả (append-only, commit vào git). Kết quả ghi ở file riêng.
Auditor, Resolution, Scorecard đều là code tất định — không LLM nào tự chấm mình."""
import hashlib, json
import numpy as np, pandas as pd
from .config import CFG, ROOT, path, save_json

PRED, RES = "ledger/predictions.jsonl", "ledger/resolutions.jsonl"

def _load(rel):
    p = ROOT / rel
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []

def _append(rel, rows):
    with open(path(rel), "a", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")

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
    _append(PRED, ok)
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
def scorecard(as_of):
    P = {p["id"]: p for p in _load(PRED)}
    R = _load(RES)
    rows = [{**P[r["prediction_id"]], **r} for r in R if r["prediction_id"] in P and r.get("outcome") is not None]
    void = sum(1 for r in R if r.get("outcome") is None)
    out = {"as_of": as_of, "total_predictions": len(P), "resolved": len(rows), "void_data_error": void, "procedures": {}}
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
