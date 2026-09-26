import os, json, pathlib, yaml
REPO = pathlib.Path(__file__).resolve().parents[1]
ROOT = pathlib.Path(os.environ.get("TTC_HOME", REPO))
CFG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8")) if (ROOT / "config.yaml").exists() \
    else yaml.safe_load((REPO / "config.yaml").read_text(encoding="utf-8"))

def path(rel):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def load_json(rel, default):
    p = ROOT / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default

def save_json(rel, obj):
    path(rel).write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

ROUNDTRIP = (CFG["costs"]["buy_fee"] + CFG["costs"]["sell_fee"] + CFG["costs"]["sell_tax"]
             + 2 * CFG["costs"]["slippage"])
