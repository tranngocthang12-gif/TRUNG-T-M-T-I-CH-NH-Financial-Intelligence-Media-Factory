"""Knowledge & Model Registry: thăng hạng tri thức, sổ đăng ký mô hình, dự báo trực tiếp và phát hiện suy thoái."""
import numpy as np, pandas as pd, joblib
from .config import CFG, ROOT, path, load_json, save_json
from .research import fit, predict, daily_ic, tstat

REG = "state/model_registry.json"
PRED = "research/predictions.csv.gz"
LIVE = {"ACTIVE", "WATCH", "DEGRADING"}

def load_registry(): return load_json(REG, {})
def save_registry(r): save_json(REG, r)

def write_candidate(mid, spec, m, status, trial_id, as_of):
    h, k = CFG["horizon_days"], CFG["research"]["top_k"]
    valid = [r for r, v in m["regimes"].items() if r != "UNKNOWN" and v["n"] >= 60 and v["t"] >= 2]
    unver = [r for r, v in m["regimes"].items() if r != "UNKNOWN" and r not in valid]
    save_json(f"knowledge/candidates/{mid}.json", {
        "id": mid, "schema_version": "0.1", "created_at": f"{as_of}T00:00:00Z", "created_by": "engine.walk_forward",
        "statement": (f"Tổ hợp [{', '.join(spec['features'])}] với mô hình {spec['model']} dự báo lợi nhuận vượt trội "
                      f"{h} phiên: IC={m['ic_mean']:.3f}, t={m['ic_t']:.2f}, lợi nhuận ròng năm hóa top{k}={m['net_ann']:.1%}, "
                      f"{m['n_folds']} fold walk-forward."),
        "status": status, "evidence_refs": [f"research/trials.csv#{trial_id}"], "valid_regimes": valid,
        "unverified_regimes": unver, "validated_by": "engine.walk_forward", "validated_at": f"{as_of}T00:00:00Z",
        "review_by": (pd.Timestamp(as_of) + pd.Timedelta(days=90)).date().isoformat()})

def promote(reg, mid, spec, m, status, as_of):
    if status in ("SUPPORTED", "STRONG", "REGIME_SPECIFIC") and mid not in reg:
        reg[mid] = {"spec": spec, "status": status, "state": "WATCH", "backtest": m, "created": as_of,
                    "fitted_at": None, "realized": None, "history": [[as_of, "WATCH", "vượt ngưỡng walk-forward"]]}
    rank_active(reg, as_of)

def rank_active(reg, as_of):
    ok = [k for k, v in reg.items() if v["state"] in ("ACTIVE", "WATCH")]
    ok.sort(key=lambda k: reg[k]["backtest"]["ic_t"], reverse=True)
    for i, k in enumerate(ok):
        new = "ACTIVE" if i < CFG["registry"]["max_active"] else "WATCH"
        if reg[k]["state"] != new:
            reg[k]["state"] = new
            reg[k]["history"].append([as_of, new, "xếp hạng theo độ mạnh backtest"])

def live_predict(ds, reg, as_of, udates):
    h, emb = CFG["horizon_days"], CFG["horizon_days"] + 1
    dates = ds.index.get_level_values(0)
    rows = []
    pos = udates.get_loc(pd.Timestamp(as_of))
    for mid, r in reg.items():
        if r["state"] not in LIVE:
            continue
        f = r["spec"]["features"]
        mp = path(f"state/models/{mid}.pkl")
        stale = r["fitted_at"] is None or pos - udates.get_loc(pd.Timestamp(r["fitted_at"])) >= CFG["registry"]["refit_days"]
        if stale or not mp.exists():
            cutoff = udates[max(0, pos - emb)]
            trm = ds[f].notna().all(axis=1).values & ds["y"].notna().values & (dates < cutoff)
            joblib.dump(fit(r["spec"]["model"], ds.loc[trm, f].values, ds.loc[trm, "yr"].values), mp)
            r["fitted_at"] = str(pd.Timestamp(as_of).date())
        m = joblib.load(mp)
        today = ds.xs(pd.Timestamp(as_of), level=0)[f].dropna()
        if len(today):
            for t, s in zip(today.index, predict(m, today.values)):
                rows.append((pd.Timestamp(as_of), mid, t, float(s)))
    new = pd.DataFrame(rows, columns=["date", "model_id", "ticker", "score"])
    p = ROOT / PRED
    old = pd.read_csv(p, parse_dates=["date"]) if p.exists() else new.iloc[0:0]
    allp = pd.concat([old[old.date != pd.Timestamp(as_of)], new], ignore_index=True)
    allp.to_csv(path(PRED), index=False, compression="gzip")
    return new, allp

def decay(reg, allp, ds, as_of):
    """So dự báo đã đưa ra TRƯỚC với kết quả thực tế SAU — đây là kiểm định thật, không phải backtest."""
    h, dc = CFG["horizon_days"], CFG["decay"]
    alerts = []
    y = ds["y"]
    for mid, r in reg.items():
        if r["state"] in ("RETIRED", "INVALIDATED"):
            continue
        p = allp[allp.model_id == mid].set_index(["date", "ticker"])["score"]
        o = pd.DataFrame({"pred": p}).join(y).dropna()
        if o.empty:
            continue
        ic = daily_ic(o)
        ic = ic[ic.index >= ic.index.max() - pd.Timedelta(days=int(dc["window_days"] * 1.45))]
        if len(ic) < dc["min_realized_days"]:
            continue
        m, t = float(ic.mean()), tstat(ic, h)
        r["realized"] = {"n_days": int(len(ic)), "ic_mean": m, "ic_t": t, "as_of": as_of}
        old = r["state"]
        if t <= -3: new = "INVALIDATED"
        elif t <= -2: new = "PAUSED"
        elif old == "PAUSED" and t < 1: new = "PAUSED"          # trễ (hysteresis): không dao động qua lại
        elif m < 0 and t <= -1: new = "DEGRADING"
        elif old in ("DEGRADING", "PAUSED") and t >= 1: new = "WATCH"
        else: new = old
        if new != old:
            r["state"] = new
            r["history"].append([as_of, new, f"IC thực tế={m:.3f}, t={t:.2f}"])
            alerts.append(f"{mid}: {old} → {new} (IC thực tế {m:.3f}, t={t:.2f})")
            if new == "INVALIDATED":
                c = load_json(f"knowledge/candidates/{mid}.json", None)
                if c:
                    c["status"] = "INVALIDATED"
                    c["invalidation_reason"] = f"{as_of}: kiểm định thực tế IC={m:.3f}, t={t:.2f}"
                    save_json(f"knowledge/candidates/{mid}.json", c)
    rank_active(reg, as_of)
    return alerts
