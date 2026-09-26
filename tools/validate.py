"""Kiểm tra cấu trúc bộ não và các contract. Chạy: python tools/validate.py"""
import json, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIRED = ["BOOT.md","governance/OWNER_MISSION.md","governance/GOVERNOR_POLICY.yaml","governance/SAFETY_STATE.yaml",
            "governance/GATES.md","orchestrator/ORCHESTRATOR.md","state/PROJECT_STATE.yaml","state/CAPABILITY_STATE.yaml",
            "config.yaml","engine/run_cycle.py",".github/workflows/daily_cycle.yml"]
SAFE = {"live_trading_enabled":"false","autonomous_order_execution":"false","autonomous_spending_enabled":"false","auto_publish_enabled":"false"}
errors = []
for f in REQUIRED:
    if not (ROOT/f).exists(): errors.append(f"Thiếu file: {f}")
schemas = sorted((ROOT/"contracts").glob("*.schema.json"))
for s in schemas:
    try:
        d = json.loads(s.read_text(encoding="utf-8"))
        for k in d["required"]:
            if k not in d["properties"]: errors.append(f"{s.name}: required '{k}' không có trong properties")
    except Exception as e: errors.append(f"{s.name}: JSON lỗi ({e})")
if len(schemas) != 18: errors.append(f"Cần 18 contract, đang có {len(schemas)}")
safety = (ROOT/"governance/SAFETY_STATE.yaml").read_text(encoding="utf-8")
for k,v in SAFE.items():
    if f"{k}: {v}" not in safety: print(f"CẢNH BÁO: {k} không còn = {v} — phải có Owner duyệt")
try:
    import jsonschema
    ex = json.loads((ROOT/"templates/hypothesis.example.json").read_text(encoding="utf-8"))
    sch = json.loads((ROOT/"contracts/hypothesis.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(ex, sch)
except ImportError:
    print("(bỏ qua kiểm tra mẫu — chưa cài jsonschema)")
except Exception as e: errors.append(f"Mẫu hypothesis không khớp schema: {e}")
if errors:
    print("\n".join("LỖI: "+e for e in errors)); sys.exit(1)
print(f"OK — {len(schemas)} contract hợp lệ, cấu trúc đầy đủ.")
