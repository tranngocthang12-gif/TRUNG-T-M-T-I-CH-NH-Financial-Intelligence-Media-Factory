"""Kiểm tra cấu trúc bộ não theo kiến trúc hiện hành (v2.0 + v2.1 + v2.2) và các contract.
LỖI  → thoát mã 1 (chặn workflow). CẢNH BÁO → in ra, không chặn (hạng mục kiến trúc yêu cầu nhưng chưa tới lượt làm).
Chạy: python tools/validate.py"""
import json, sys, pathlib
import yaml
ROOT = pathlib.Path(__file__).resolve().parents[1]
errors, warnings = [], []

# ---------- 1) File/thư mục bắt buộc (đã có — mất là LỖI) ----------
REQUIRED = ["BOOT.md", "CHANGELOG.md", "config.yaml", ".github/workflows/daily_cycle.yml",
            "governance/OWNER_MISSION.md", "governance/OWNER_PROFILE.md", "governance/GOVERNOR_POLICY.yaml",
            "governance/SAFETY_STATE.yaml", "governance/GATES.md", "governance/DATA_SOURCES.yaml", "governance/MEDIA_LEGAL_POLICY.md",
            "orchestrator/ORCHESTRATOR.md", "state/PROJECT_STATE.yaml", "state/CAPABILITY_STATE.yaml",
            "academy/competency_map.yaml", "library/INFORMATION_MAP.md",
            "architecture/ARCHITECTURE_v2.0.md", "architecture/ARCHITECTURE_v2.1.md", "architecture/ARCHITECTURE_v2.2.md",
            "engine/run_cycle.py", "engine/ledger.py", "engine/experts.py", "engine/budget.py", "engine/adjust.py",
            "data/corporate_actions.csv"]
REQUIRED_DIRS = ["library", "academy", "governance", "contracts", "engine", "tests"]
for f in REQUIRED:
    if not (ROOT / f).is_file(): errors.append(f"Thiếu file: {f}")
for d in REQUIRED_DIRS:
    if not (ROOT / d).is_dir(): errors.append(f"Thiếu thư mục: {d}/")

# ---------- 2) Kiến trúc v2.x yêu cầu nhưng chưa có (CẢNH BÁO) ----------
PLANNED = {  # đường dẫn → nguồn yêu cầu
    "library/INDEX.md": "v2.0 IX", "library/foundations/playbooks": "v2.0 IX (Tầng 1)",
    "library/vietnam/law": "v2.0 IX (Tầng 2)", "library/vietnam/accounting": "v2.0 IX (Tầng 2)",
    "library/vietnam/market": "v2.0 IX (Tầng 2)", "library/vietnam/sectors": "v2.0 IX (Tầng 2)",
    "library/vietnam/policy": "v2.1 §6", "library/casebook/manipulation": "v2.0 IX (Tầng 2)",
    "library/dossiers": "v2.0 IX (Tầng 3)", "library/lessons": "v2.0 IX (Tầng 4)",
    "library/influence": "v2.1 §5", "library/value_chain": "v2.2 §2", "library/owner_observations": "v2.2 §3",
    "academy/curriculum.md": "v2.0 IX", "academy/exams": "v2.0 IX", "academy/results": "v2.0 IX",
    "engine/financials.py": "v2.0 IX", "engine/red_flags.py": "v2.0 IX", "engine/retrieval.py": "v2.0 IX",
    "engine/exams.py": "v2.0 IX", "fact/calendar.jsonl": "v2.1 §2", "reports/BLIND_SPOTS.md": "v2.1 §4",
}
missing_planned = [f"{p} ({src})" for p, src in PLANNED.items() if not (ROOT / p).exists()]
if missing_planned:
    warnings.append(f"Kiến trúc v2.x yêu cầu, chưa có ({len(missing_planned)}): " + ", ".join(missing_planned))

# ---------- 3) Mọi YAML trong repo phải đọc được ----------
yamls = sorted(p for ext in ("*.yaml", "*.yml") for p in ROOT.rglob(ext) if ".git" not in p.parts)
parsed = {}
for p in yamls:
    try:
        parsed[p.relative_to(ROOT).as_posix()] = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"YAML lỗi: {p.relative_to(ROOT)} ({str(e).splitlines()[0]})")

# ---------- 4) Bản đồ năng lực ----------
LEVELS = ["NOT_STARTED", "STUDYING", "SYNTHESIZED", "PRACTICED", "VALIDATED", "READY", "PRODUCTION_PROVEN"]
cm = parsed.get("academy/competency_map.yaml") or {}
comps = (cm.get("competencies") or {}) if isinstance(cm, dict) else {}
if not comps: errors.append("academy/competency_map.yaml: không có mục competencies")
lib_missing = []
for name, c in comps.items():
    c = c or {}
    if c.get("level") not in LEVELS:
        errors.append(f"competency_map: '{name}' có level không hợp lệ: {c.get('level')}")
    for rel in c.get("library") or []:
        if not (ROOT / "library" / rel).exists(): lib_missing.append(f"{name} → library/{rel}")
if lib_missing:
    warnings.append(f"competency_map trỏ tới thư viện chưa tồn tại ({len(lib_missing)}): " + ", ".join(lib_missing))

# ---------- 5) Contract theo kiến trúc hiện hành ----------
V1_CONTRACTS = ["attribution_report", "backtest_run", "conflict_disclosure", "editorial_review", "evidence_item",
                "hypothesis", "investment_decision", "knowledge_item", "learning_lesson", "market_data_contract",
                "market_regime", "media_story", "model_card", "portfolio_snapshot", "prediction", "procedure",
                "research_report", "resolution", "risk_assessment", "trade_record", "valuation_case"]
V2_CONTRACTS = ["knowledge_note", "exam_item", "dossier"]          # v2.0 IX: "+ KNOWLEDGE_NOTE, EXAM_ITEM, DOSSIER (tổng 24)"
schemas = sorted((ROOT / "contracts").glob("*.schema.json"))
have = {s.name.removesuffix(".schema.json") for s in schemas}
for s in schemas:
    try:
        d = json.loads(s.read_text(encoding="utf-8"))
        for k in d["required"]:
            if k not in d["properties"]: errors.append(f"{s.name}: required '{k}' không có trong properties")
    except Exception as e: errors.append(f"{s.name}: JSON lỗi ({e})")
lost = [c for c in V1_CONTRACTS if c not in have]
if lost: errors.append(f"Mất contract đã có từ v1.0: {lost}")
todo = [c for c in V2_CONTRACTS if c not in have]
expected = len(V1_CONTRACTS) + len(V2_CONTRACTS)
n_ok = len([c for c in V1_CONTRACTS + V2_CONTRACTS if c in have])
if todo: warnings.append(f"Contract theo kiến trúc v2.0: có {n_ok}/{expected}; còn thiếu {todo}")

# ---------- 6) Công tắc an toàn ----------
SAFE = {"live_trading_enabled": False, "autonomous_order_execution": False, "autonomous_spending_enabled": False,
        "auto_publish_enabled": False}
safety = parsed.get("governance/SAFETY_STATE.yaml") or {}
for k, v in SAFE.items():
    if safety.get(k) is not v: print(f"CẢNH BÁO AN TOÀN: {k} không còn = {str(v).lower()} — phải có Owner duyệt")

# ---------- 7) Mẫu hypothesis khớp schema ----------
try:
    import jsonschema
    ex = json.loads((ROOT / "templates/hypothesis.example.json").read_text(encoding="utf-8"))
    sch = json.loads((ROOT / "contracts/hypothesis.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(ex, sch)
except ImportError:
    print("(bỏ qua kiểm tra mẫu — chưa cài jsonschema)")
except Exception as e: errors.append(f"Mẫu hypothesis không khớp schema: {e}")

for w in warnings: print("CẢNH BÁO: " + w)
if errors:
    print("\n".join("LỖI: " + e for e in errors)); sys.exit(1)
print(f"OK — {len(yamls)} YAML hợp lệ, {len(comps)} năng lực, contract {n_ok}/{expected} theo kiến trúc hiện hành, "
      f"cấu trúc bắt buộc đầy đủ ({len(warnings)} cảnh báo).")
