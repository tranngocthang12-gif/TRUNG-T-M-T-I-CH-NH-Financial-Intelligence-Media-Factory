"""Kiểm tra cấu trúc bộ não theo kiến trúc hiện hành (ARCHITECTURE.md v3.0; các bản v2.x là SUPERSEDED) và các contract.
LỖI  → thoát mã 1 (chặn workflow). CẢNH BÁO → in ra, không chặn. THÔNG TIN → tiến độ lộ trình v3.0 §8.
Chạy: python tools/validate.py"""
import json, sys, pathlib
import yaml
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tools import laws_checks
ROOT = pathlib.Path(__file__).resolve().parents[1]
errors, warnings = [], []

# ---------- 1) File/thư mục bắt buộc (đã có — mất là LỖI) ----------
REQUIRED = ["BOOT.md", "CHANGELOG.md", "config.yaml", ".github/workflows/daily_cycle.yml",
            "architecture/ARCHITECTURE.md", "architecture/ARCHIVE.md", "governance/LAWS.md",
            "governance/OWNER_MISSION.md", "governance/OWNER_PROFILE.md", "governance/GOVERNOR_POLICY.yaml",
            "governance/SAFETY_STATE.yaml", "governance/GATES.md", "governance/DATA_SOURCES.yaml",
            "orchestrator/ORCHESTRATOR.md", "state/PROJECT_STATE.yaml", "state/CAPABILITY_STATE.yaml",
            "academy/competency_map.yaml", "library/INFORMATION_MAP.md",
            "architecture/ARCHITECTURE_v2.0.md", "architecture/ARCHITECTURE_v2.1.md", "architecture/ARCHITECTURE_v2.2.md",
            "engine/run_cycle.py", "engine/ledger.py", "engine/experts.py", "engine/budget.py", "engine/adjust.py",
            "data/corporate_actions.csv",
            # v3.0 (G0 + v3.0.1/v3.0.2): đường ghi và phân định dự báo, luật, thư viện/học viện khởi động
            "architecture/adr/ADR-0001-hop-nhat-v3.md", "governance/CONTROL_B_PROMPT.md",
            ".github/ISSUE_TEMPLATE/forecast.yml", ".github/ISSUE_TEMPLATE/resolution.yml",
            ".github/workflows/ledger_intake.yml", ".github/workflows/resolution_intake.yml", ".github/workflows/tests.yml",
            "tools/ledger_intake.py", "tools/resolution_intake.py", "tools/laws_checks.py",
            "tools/review_gate.py", "tools/ledger_audit.py", "tools/registry_push.py", ".github/workflows/review_gate.yml",
            ".github/workflows/ledger_audit.yml",
            ".github/pull_request_template.md", "architecture/adr/ADR-0003-phan-dinh-va-van-hanh.md",
            "docs/HUONG_DAN_VAN_HANH.md", "engine/knowledge_notes.py",
            "library/INDEX.md", "library/SOURCE_MANIFEST.json", "library/reading_queue.yaml", "academy/curriculum.md"]
REQUIRED_DIRS = ["library", "academy", "governance", "contracts", "engine", "tests"]
for f in REQUIRED:
    if not (ROOT / f).is_file(): errors.append(f"Thiếu file: {f}")
for d in REQUIRED_DIRS:
    if not (ROOT / d).is_dir(): errors.append(f"Thiếu thư mục: {d}/")

# ---------- 2) Tiến độ theo lộ trình v3.0 §8 (THÔNG TIN, không phải cảnh báo) ----------
# Danh sách "v2.x yêu cầu nhưng chưa có" đã bỏ: v2.0–v2.2 là SUPERSEDED (L-07), không còn là yêu cầu.
def _count_lines(rel):
    p = ROOT / rel
    return sum(1 for l in p.read_text(encoding="utf-8").splitlines() if l.strip()) if p.is_file() else 0
try:
    n_sources = len(json.loads((ROOT / "library/SOURCE_MANIFEST.json").read_text(encoding="utf-8")).get("files") or {})
except Exception as e:
    n_sources = 0; errors.append(f"library/SOURCE_MANIFEST.json đọc lỗi ({e})")
def _count_issue_forecasts(rel):
    p = ROOT / rel
    if not p.is_file(): return 0
    n = 0
    for i, l in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not l.strip(): continue
        try:
            n += "issue_number" in json.loads(l)
        except ValueError:
            errors.append(f"{rel}: dòng {i} không phải JSON")      # báo lỗi, không đổ
    return n
n_forecasts = _count_issue_forecasts("ledger/predictions.jsonl")          # chỉ dự báo A+B qua Issue (§8 G1), không đếm dòng engine
progress = f"tiến độ G1: tài liệu gốc ghim {n_sources}/40, dự báo A+B trong Ledger {n_forecasts}/60"

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
# Con trỏ thư viện của competency_map là chủ đề sẽ lấp dần (thư viện v3.0 đang rỗng — đúng hiện trạng),
# nên báo ở dòng tiến độ, không phải cảnh báo lỗi.
if lib_missing:
    progress += f"; năng lực chưa có tài liệu thư viện {len(lib_missing)}/{len(comps)}"

# ---------- 5) Contract theo kiến trúc hiện hành ----------
V1_CONTRACTS = ["attribution_report", "backtest_run", "conflict_disclosure", "editorial_review", "evidence_item",
                "hypothesis", "investment_decision", "knowledge_item", "learning_lesson", "market_data_contract",
                "market_regime", "media_story", "model_card", "portfolio_snapshot", "prediction", "procedure",
                "research_report", "resolution", "risk_assessment", "trade_record", "valuation_case"]
V2_CONTRACTS = ["knowledge_note", "exam_item", "dossier", "forecast_issue"]   # v2.0 IX + v3.0 §4.1 (tổng 25)
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
if todo: errors.append(f"Contract theo kiến trúc v3.0: có {n_ok}/{expected}; thiếu {todo}")

# ---------- 5b) Luật vận hành máy kiểm (governance/LAWS.md: L-02, L-03, L-05 hash chuỗi + chạy lại luật nhận trên từng dòng sổ,
#              L-06, L-07, L-10 đề thi) ----------
errors.extend(laws_checks.run_all(ROOT))

# ---------- 5c) Thư viện: L-01 nguồn ghim + trích nguyên văn, L-04 giấy phép, L-08 hiệu lực, L-09 trạng thái ----------
from engine import knowledge_notes  # noqa: E402
lib_err, lib_warn = knowledge_notes.check_library(ROOT)
errors.extend(lib_err); warnings.extend(lib_warn)

# ---------- 6) Công tắc an toàn ----------
SAFE = {"live_trading_enabled": False, "autonomous_order_execution": False, "autonomous_spending_enabled": False,
        "auto_publish_enabled": False}
safety = parsed.get("governance/SAFETY_STATE.yaml") or {}
# ARCHITECTURE v3.0 §6: "mọi công tắc tiền/API vẫn false". Lệch là LỖI (chặn CI và vòng học), không chỉ cảnh báo:
# muốn bật một công tắc thì Owner phải sửa cả bảng SAFE này trong cùng PR — thay đổi hiện rõ trong diff.
for k, v in SAFE.items():
    if safety.get(k) is not v: errors.append(f"AN TOÀN: governance/SAFETY_STATE.yaml {k} phải = {str(v).lower()} (đổi cần Owner duyệt và sửa tools/validate.py)")

# ---------- 7) Mẫu hypothesis khớp schema ----------
try:
    import jsonschema
    ex = json.loads((ROOT / "templates/hypothesis.example.json").read_text(encoding="utf-8"))
    sch = json.loads((ROOT / "contracts/hypothesis.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(ex, sch)
except ImportError:
    errors.append("Thiếu thư viện jsonschema: không kiểm được hợp đồng nào (pip install -r requirements.txt). "
                  "Bỏ qua lặng lẽ là để lọt lỗi, nên đây là lỗi.")
except Exception as e: errors.append(f"Mẫu hypothesis không khớp schema: {e}")

for w in warnings: print("CẢNH BÁO: " + w)
print("THÔNG TIN: " + progress)
if errors:
    print("\n".join("LỖI: " + e for e in errors)); sys.exit(1)
print(f"OK — {len(yamls)} YAML hợp lệ, {len(comps)} năng lực, contract {n_ok}/{expected} theo kiến trúc hiện hành, "
      f"cấu trúc bắt buộc đầy đủ ({len(warnings)} cảnh báo).")
