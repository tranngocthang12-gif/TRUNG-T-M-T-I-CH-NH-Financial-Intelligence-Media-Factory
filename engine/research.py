"""Research & Backtest Engine: walk-forward có embargo, chi phí thật, ngưỡng thống kê tăng theo số lần thử.
L-06: mọi lần thử được ĐĂNG KÝ vào research/trial_registry.jsonl (hash chuỗi) TRƯỚC khi chạy, và trong vòng học trên
GitHub dòng đăng ký được đẩy lên main trước khi backtest bắt đầu (persist_registration) — lần thử hỏng giữa chừng vẫn
được đếm; báo Sharpe kèm Deflated Sharpe (Bailey & López de Prado 2014) tính theo tổng số lần thử."""
import csv, hashlib, io, json, math, os, subprocess, sys
from datetime import datetime, timezone
from statistics import NormalDist
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from .config import CFG, ROOT, REPO, ROUNDTRIP, path

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from tools.laws_checks import LEGACY_ANCHOR, TRIAL_LEGACY_COLS, line_hash, read_trials, trials_digest  # noqa: E402

REGISTRY = "research/trial_registry.jsonl"
TRIALS = "research/trials.csv"
TRIAL_NEW_COLS = ("sharpe", "sharpe_ann", "dsr", "registry_hash")     # thêm từ v3.0.2, đứng sau 13 cột gốc
EULER_GAMMA = 0.5772156649015329

MODELS = ["ridge", "gbm", "signed_sum"]

def spec_id(spec):
    s = json.dumps({"f": sorted(spec["features"]), "m": spec["model"]})
    return "M-" + hashlib.sha1(s.encode()).hexdigest()[:10]

def fit(model, X, y):
    if model == "ridge":
        return ("sk", Ridge(alpha=1.0).fit(X, y))
    if model == "gbm":
        return ("sk", HistGradientBoostingRegressor(max_iter=80, max_depth=3, learning_rate=0.05,
                                                    min_samples_leaf=200, random_state=0).fit(X, y))
    signs = np.array([np.nan_to_num(np.corrcoef(X[:, j], y)[0, 1]) for j in range(X.shape[1])])
    return ("sum", np.sign(signs))

def predict(f, X):
    kind, m = f
    return m.predict(X) if kind == "sk" else X @ m

def threshold(n_trials):
    """Ngưỡng t kiểu Bonferroni: càng thử nhiều, càng phải mạnh mới được tin."""
    a = CFG["research"]["family_wise_alpha"] / max(1, n_trials)
    return max(CFG["research"]["min_t"], NormalDist().inv_cdf(1 - a / 2))

def walk_forward(ds, spec):
    r, h = CFG["research"], CFG["horizon_days"]
    f = spec["features"]
    d = ds[f + ["y", "yr"]]
    dates = d.index.get_level_values(0)
    valid = d[f].notna().all(axis=1).values
    labeled = d["y"].notna().values
    udates = pd.Index(sorted(dates[valid].unique()))
    emb = h + 1
    preds, fold_ics = [], []
    i = r["min_train_days"]
    while i < len(udates):
        test_dates = udates[i:i + r["test_days"]]
        cutoff = udates[i - emb]                      # nhãn tập train kết thúc trước ngày test đầu tiên
        trm = valid & labeled & (dates < cutoff)
        tem = valid & dates.isin(test_dates)
        if trm.sum() >= 1000 and tem.sum() > 0:
            m = fit(spec["model"], d.loc[trm, f].values, d.loc[trm, "yr"].values)
            out = pd.DataFrame({"pred": predict(m, d.loc[tem, f].values), "y": d.loc[tem, "y"].values},
                               index=d.index[tem])
            preds.append(out)
            ic = daily_ic(out)
            if len(ic):
                fold_ics.append(ic.mean())
        i += r["test_days"]
    oos = pd.concat(preds) if preds else pd.DataFrame(columns=["pred", "y"])
    return oos, fold_ics

def daily_ic(o):
    """Rank IC theo ngày (Spearman), tính vector hóa."""
    o = o.dropna(subset=["pred", "y"])
    if o.empty:
        return pd.Series(dtype=float)
    lv = o.index.get_level_values(0)
    rp = o["pred"].groupby(lv).rank(); ry = o["y"].groupby(lv).rank()
    dp = rp - rp.groupby(lv).transform("mean"); dy = ry - ry.groupby(lv).transform("mean")
    cov = (dp * dy).groupby(lv).sum()
    den = np.sqrt((dp ** 2).groupby(lv).sum() * (dy ** 2).groupby(lv).sum())
    return (cov / den).replace([np.inf, -np.inf], np.nan).dropna()

def tstat(ic, h):
    n = len(ic)
    if n < 2 or ic.std() == 0:
        return 0.0
    return float(ic.mean() / ic.std() * np.sqrt(n / h))    # hiệu chỉnh nhãn chồng lấn

def metrics(oos, fold_ics, regime):
    h, k = CFG["horizon_days"], CFG["research"]["top_k"]
    ic = daily_ic(oos)
    out = {"n_days": int(len(ic)), "ic_mean": float(ic.mean()) if len(ic) else 0.0, "ic_t": tstat(ic, h),
           "fold_pos": float(np.mean([x > 0 for x in fold_ics])) if fold_ics else 0.0, "n_folds": len(fold_ics)}
    o = oos.dropna(subset=["y"])
    prev, net = set(), []
    for d in ic.index[::h]:
        g = o.loc[d]
        top = set(g["pred"].nlargest(k).index)
        turnover = 1 - len(top & prev) / k if prev else 1.0
        net.append(g.loc[list(top), "y"].mean() - turnover * ROUNDTRIP)
        prev = top
    out["net_ann"] = float(np.mean(net) * 252 / h) if net else 0.0
    out.update(sharpe_stats(net, h))
    reg = {}
    lab = regime.reindex(ic.index)
    for rname, s in ic.groupby(lab):
        reg[rname] = {"n": int(len(s)), "ic_mean": float(s.mean()), "t": tstat(s, h)}
    out["regimes"] = reg
    recent = ic[ic.index >= ic.index.max() - pd.Timedelta(days=365)] if len(ic) else ic
    out["recent_ic"] = float(recent.mean()) if len(recent) else 0.0     # cổng gần đây: quy luật còn sống không?
    return out

def classify(m, thr):
    r = CFG["research"]
    if (m["ic_t"] >= thr and m["net_ann"] > 0 and m["fold_pos"] >= r["min_fold_positive"]
            and m.get("recent_ic", 0) > 0):
        good = [k for k, v in m["regimes"].items() if k != "UNKNOWN" and v["n"] >= 60 and v["ic_mean"] > 0]
        if len(good) <= 1:
            return "REGIME_SPECIFIC"
        return "STRONG" if m["ic_t"] >= thr + 1 else "SUPPORTED"
    if m["ic_t"] >= 2:
        return "WEAK"
    return "REJECTED"


# ---------------- L-06: Sharpe, Deflated Sharpe, sổ đăng ký thử ----------------
def sharpe_stats(net, h):
    """Sharpe theo kỳ tái cân bằng (không năm hóa) + năm hóa, số kỳ T, độ lệch, độ nhọn (không trừ 3)."""
    x = np.asarray([v for v in net if v is not None and np.isfinite(v)], dtype=float)
    T = int(len(x))
    if T < 3 or x.std(ddof=1) == 0:
        return {"sharpe": 0.0, "sharpe_ann": 0.0, "sr_T": T, "sr_skew": 0.0, "sr_kurt": 3.0}
    sd = x.std(ddof=1)
    sr = float(x.mean() / sd)
    z = (x - x.mean()) / x.std(ddof=0)
    return {"sharpe": sr, "sharpe_ann": float(sr * math.sqrt(252 / h)), "sr_T": T,
            "sr_skew": float(np.mean(z ** 3)), "sr_kurt": float(np.mean(z ** 4))}

MIN_SR_SAMPLE = 10     # dưới ngưỡng này, phương sai Sharpe giữa các lần thử chưa ước lượng được → dùng phương sai lý thuyết

def sharpe_variance(prev_sharpes, sr, T):
    """V[SR] để tính SR0. Đủ ≥ MIN_SR_SAMPLE Sharpe đã ghi → phương sai mẫu (Bailey & López de Prado 2014).
    Chưa đủ (sổ cũ không ghi Sharpe) → phương sai lý thuyết của ước lượng Sharpe dưới giả thuyết SR thật = 0: 1/(T−1).
    Không bao giờ trả về None để SR0 không bị đặt = 0 khi đã thử nhiều lần."""
    xs = [x for x in prev_sharpes if x is not None and math.isfinite(x)] + ([sr] if sr is not None and math.isfinite(sr) else [])
    theory = 1.0 / max(T - 1, 1)
    if len(xs) >= MIN_SR_SAMPLE:
        return max(float(np.var(xs, ddof=1)), 1e-12)
    return theory

def deflated_sharpe(sr, T, skew, kurt, n_trials, var_sr):
    """Xác suất Sharpe thật > 0 sau khi trừ kỳ vọng Sharpe lớn nhất của n_trials lần thử ngẫu nhiên.
    SR0 = sqrt(V[SR]) * ((1-γ)·Φ⁻¹(1-1/N) + γ·Φ⁻¹(1-1/(N·e))); DSR = Φ((SR-SR0)·sqrt(T-1) / sqrt(1-γ3·SR+(γ4-1)/4·SR²)).
    var_sr None → dùng sharpe_variance([], sr, T) (phương sai lý thuyết), không đặt SR0 = 0."""
    nd = NormalDist()
    if T is None or T < 3:
        return float("nan")
    if var_sr is None:
        var_sr = sharpe_variance([], sr, T)
    sr0 = 0.0
    if n_trials >= 2 and var_sr is not None and var_sr > 0:
        sr0 = math.sqrt(var_sr) * ((1 - EULER_GAMMA) * nd.inv_cdf(1 - 1 / n_trials)
                                   + EULER_GAMMA * nd.inv_cdf(1 - 1 / (n_trials * math.e)))
    den = 1 - skew * sr + (kurt - 1) / 4 * sr ** 2
    if den <= 0:
        return float("nan")
    return float(nd.cdf((sr - sr0) * math.sqrt(T - 1) / math.sqrt(den)))

def _registry_rows():
    p = ROOT / REGISTRY
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []

def _registry_trials():
    """Các dòng đăng ký lần thử (bỏ dòng neo lịch sử đứng đầu sổ)."""
    return [r for r in _registry_rows() if r.get("kind") != "legacy_anchor"]

def total_trials(ledger_df):
    """Tổng số lần đã thử = số đã có kết quả + số đã đăng ký mà chưa có kết quả (thử bị dừng giữa chừng). Mọi con số
    phụ thuộc số lần thử — ngưỡng Bonferroni, N của Deflated Sharpe, báo cáo, trạng thái — đều lấy từ đây (L-06)."""
    done = set(ledger_df["trial_id"]) if ledger_df is not None and "trial_id" in ledger_df else set()
    return len(done) + sum(1 for r in _registry_trials() if r.get("trial_id") not in done)

def next_trial_number(ledger_df):
    """Số thứ tự lần thử kế tiếp."""
    return total_trials(ledger_df) + 1

def _legacy_anchor():
    """Dòng neo lịch sử: ghi một lần lúc tạo sổ đăng ký. Chốt số kết quả đã có trước khi có sổ và sha256 của chúng, để
    về sau không ai sửa được kết quả cũ hay chèn kết quả không đăng ký mà kiểm máy không thấy (laws_checks.check_trial_registry)."""
    p = ROOT / TRIALS
    _, rows = read_trials(p.read_text(encoding="utf-8")) if p.exists() else ([], [])
    row = {"trial_id": LEGACY_ANCHOR, "kind": "legacy_anchor", "results": len(rows),
           "last_trial_id": rows[-1].get("trial_id", "") if rows else "", "legacy_sha256": trials_digest(rows),
           "registered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "prev_hash": "GENESIS"}
    row["hash"] = line_hash(row)
    return row

def append_trial_results(new_rows):
    """GHI THÊM kết quả vào research/trials.csv ở mức văn bản: dòng cũ giữ nguyên từng ký tự (không đọc–ghi lại qua
    pandas, vì việc đó có thể đổi cách viết số và làm lệch sha256 lịch sử). Lần đầu có cột mới thì nối tên cột vào tiêu
    đề và thêm ô rỗng vào cuối mỗi dòng cũ; 13 cột gốc không bị đụng."""
    if not new_rows:
        return
    p = ROOT / TRIALS
    cols = list(TRIAL_LEGACY_COLS) + list(TRIAL_NEW_COLS)
    lines = p.read_text(encoding="utf-8").split("\n") if p.exists() else []
    while lines and lines[-1] == "":
        lines.pop()
    if lines:
        head = next(csv.reader([lines[0]]))
        if head[:len(TRIAL_LEGACY_COLS)] != list(TRIAL_LEGACY_COLS):
            raise RuntimeError("L-06: tiêu đề research/trials.csv không đúng 13 cột gốc — không ghi thêm")
        missing = [c for c in cols if c not in head]
        if missing:
            if head != cols[:len(head)]:
                raise RuntimeError("L-06: thứ tự cột research/trials.csv lạ — không ghi thêm")
            pad = "," * len(missing)
            lines = [lines[0] + "," + ",".join(missing)] + [ln + pad for ln in lines[1:]]
    else:
        lines = [",".join(cols)]
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    for r in new_rows:
        w.writerow(["" if r.get(c) is None else (repr(float(r[c])) if isinstance(r[c], (float, np.floating)) else r[c]) for c in cols])
    with open(path(TRIALS), "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(lines) + "\n" + buf.getvalue())

def register_trial(trial_id, cycle_date, method, spec, thr):
    """Đăng ký một lần thử TRƯỚC khi chạy walk-forward (L-06). Trả về hash dòng đăng ký."""
    old = _registry_rows()
    if any(r.get("trial_id") == trial_id for r in old):
        raise RuntimeError(f"L-06: {trial_id} đã có trong sổ đăng ký — không chạy lại cùng mã thử")
    anchor = None
    if not old:                                           # tạo sổ: dòng đầu là neo lịch sử, đi cùng lần đẩy đầu tiên lên main
        anchor = _legacy_anchor()
        old = [anchor]
    fs = CFG["research"].get("frozen_space")
    if fs:
        extra = [f for f in spec["features"] if f not in fs["features"]]
        if extra or spec["model"] not in fs["models"]:
            raise RuntimeError(f"L-06: lần thử nằm ngoài không gian giả thuyết đóng băng (feature lạ {extra}, mô hình "
                               f"{spec['model']}) — giả thuyết mới phải qua ADR và sửa config.yaml research.frozen_space")
    row = {"trial_id": trial_id, "cycle_date": cycle_date,
           "registered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "method": method, "spec_id": spec_id(spec), "features": ";".join(spec["features"]),
           "model": spec["model"], "threshold": float(thr), "horizon_days": CFG["horizon_days"],
           "hypothesis": "rank IC > 0 ngoài mẫu (walk-forward có embargo), lãi ròng sau phí > 0",
           "prev_hash": old[-1]["hash"] if old else "GENESIS"}
    row["hash"] = line_hash(row)
    with open(path(REGISTRY), "a", encoding="utf-8") as f:
        for r in ([anchor] if anchor else []) + [row]:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")
    persist_registration(trial_id)                        # không ghi bền được → báo lỗi, backtest không chạy
    return row["hash"]

def persist_registration(trial_id):
    """L-06: đăng ký phải nằm trên main TRƯỚC khi backtest chạy, để vòng học hỏng giữa chừng không làm mất lần thử.
    Bật bằng TTC_REGISTRY_PUSH=1 (workflow daily_cycle.yml). Không bật (test, chạy thử trong thư mục tạm) → chỉ ghi tệp."""
    if os.environ.get("TTC_REGISTRY_PUSH") != "1":
        return False
    script = REPO / "tools" / "registry_push.py"
    args = [sys.executable, str(script), "--root", str(ROOT), trial_id]
    for k in ("TTC_REGISTRY_PUSH_TRIES", "TTC_REGISTRY_PUSH_WAIT"):
        if os.environ.get(k):
            args += ["--" + k.rsplit("_", 1)[-1].lower(), os.environ[k]]
    r = subprocess.run(args, capture_output=True, text=True)
    print(f"[L-06] {(r.stdout or r.stderr).strip()}")
    if r.returncode != 0:
        raise RuntimeError(f"L-06: không ghi bền được đăng ký {trial_id} lên main nên không chạy backtest — "
                           f"{(r.stdout + r.stderr).strip()}")
    return True

def abandoned_trials(ledger_df):
    """Mã thử đã đăng ký mà không có kết quả (vòng học dừng giữa chừng). Vẫn tính vào số lần thử."""
    done = set(ledger_df["trial_id"]) if ledger_df is not None and "trial_id" in ledger_df else set()
    return [r.get("trial_id") for r in _registry_trials() if r.get("trial_id") not in done]
