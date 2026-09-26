"""Meta-learning: học xem PHƯƠNG PHÁP nghiên cứu nào tạo ra phát hiện đứng vững, rồi phân bổ ngân sách thử nghiệm
bằng Thompson sampling. Đây là 'học cách học' ở dạng đo được."""
import numpy as np
from .config import load_json, save_json
from .features import FEATURES, FAMILIES
from .research import MODELS, spec_id

METHODS = ["single_family", "cross_family", "random_subset", "mutate_best"]
REWARD = {"STRONG": 1.0, "SUPPORTED": 1.0, "REGIME_SPECIFIC": 0.6, "WEAK": 0.3, "REJECTED": 0.0}
BANDIT = "state/bandit.json"

def load():
    b = load_json(BANDIT, {})
    for m in METHODS:
        b.setdefault(m, {"a": 1.0, "b": 1.0, "trials": 0, "survivors": 0})
    return b

def save(b): save_json(BANDIT, b)

def choose(b, rng):
    return max(METHODS, key=lambda m: rng.beta(b[m]["a"], b[m]["b"]))

def update(b, method, status):
    r = REWARD[status]
    b[method]["a"] += r; b[method]["b"] += 1 - r; b[method]["trials"] += 1
    b[method]["survivors"] += int(r >= 0.6)

def _fam(f): return [n for n, (fam, _) in FEATURES.items() if fam == f]

def propose(method, rng, ledger):
    names = list(FEATURES)
    if method == "single_family":
        pool = _fam(rng.choice(FAMILIES))
        feats = list(rng.choice(pool, size=rng.integers(1, len(pool) + 1), replace=False))
    elif method == "cross_family":
        fams = rng.choice(FAMILIES, size=rng.integers(2, 4), replace=False)
        feats = [str(rng.choice(_fam(f))) for f in fams]
    elif method == "mutate_best" and ledger is not None and len(ledger):
        best = ledger.sort_values("ic_t", ascending=False).iloc[int(rng.integers(0, min(3, len(ledger))))]
        feats = best["features"].split(";")
        op = rng.choice(["add", "drop", "swap", "model"])
        rest = [n for n in names if n not in feats]
        if op == "add" and rest: feats = feats + [str(rng.choice(rest))]
        elif op == "drop" and len(feats) > 1: feats.remove(str(rng.choice(feats)))
        elif op == "swap" and rest: feats[int(rng.integers(0, len(feats)))] = str(rng.choice(rest))
        else: return {"features": sorted(feats), "model": str(rng.choice([m for m in MODELS if m != best["model"]]))}
    else:
        feats = list(rng.choice(names, size=rng.integers(2, 6), replace=False))
    return {"features": sorted(set(map(str, feats))), "model": str(rng.choice(MODELS))}

def next_spec(b, rng, ledger):
    tested = set(ledger["spec_id"]) if ledger is not None and len(ledger) else set()
    for _ in range(40):
        m = choose(b, rng)
        s = propose(m, rng, ledger)
        if spec_id(s) not in tested:
            return m, s
    return None, None
