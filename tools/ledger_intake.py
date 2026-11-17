"""Nhận một dự báo từ GitHub Issue 'Forecast' và ghi vào ledger/predictions.jsonl (ARCHITECTURE v3.0 §4.1, ADR-0003).
Chạy trong workflow ledger_intake.yml. Đầu vào qua biến môi trường:
  ISSUE_NUMBER, ISSUE_CREATED_AT (ISO, giờ máy chủ GitHub), ISSUE_BODY (thân Issue dạng form),
  ISSUE_AUTHOR và REPO_OWNER (tùy chọn; có đủ cả hai mà khác nhau → từ chối).
Đầu ra: in JSON {"ok": bool, "message": str}; thoát 0 khi ghi được, 2 khi từ chối (không ghi), 3 khi Issue đã có trong
Ledger (bỏ qua), 1 khi lỗi hệ thống.

Luật kiểm lúc nhận (mọi "ngày" tính theo giờ Việt Nam, UTC+7):
- Thân Issue: mỗi trường đúng một tiêu đề "### <trường>"; trùng tiêu đề hoặc trường lạ → từ chối.
- Khớp contracts/forecast_issue.schema.json; resolve_at dạng YYYY-MM-DD; p trong [0,05; 0,95].
- L-05: resolve_at sau ngày tạo Issue; model_cutoff dạng YYYY-MM hoặc YYYY-MM-DD và không ở tương lai. Hai điều này
  cùng bảo đảm câu hỏi giải SAU ngày cắt dữ liệu của mô hình (cutoff ≤ ngày tạo < resolve_at).
- L-09: author_seat bắt đầu bằng tên ghế (mô hình/nhà cung cấp hoặc Owner) — để về sau xác định người phân định độc lập.
- L-02: không chứa từ khóa khuyến nghị mua bán (Ledger chỉ ghi thêm; một dòng sai sẽ làm validate đỏ mãi).
- Nhóm đối chứng: seat B bắt buộc prompt_hash = sha256 khối prompt hiện hành trong governance/CONTROL_B_PROMPT.md;
  seat A không được có prompt_hash.
- Một câu hỏi (question + resolve_at) mỗi ghế chỉ một dự báo; ghế kia nếu đã ghi thì resolution_rule và resolution_source
  phải giống hệt; cùng câu chữ mà khác resolve_at → từ chối. Khác ngày với ghế kia vẫn ghi nhưng không vào cặp A–B (§4.2).
Mỗi dòng có id "F-<số Issue>", issue_created_at, issue_author, prev_hash, hash.
"""
import hashlib, json, os, pathlib, re, sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tools.laws_checks import line_hash, nfc, recommendation_hit, recognised_seat  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledger" / "predictions.jsonl"
SCHEMA = ROOT / "contracts" / "forecast_issue.schema.json"
CONTROL_B = ROOT / "governance" / "CONTROL_B_PROMPT.md"
NUMERIC = {"p", "base_rate"}
VN = timezone(timedelta(hours=7))
EMPTY = ("_No response_", "None", "")


def vn_day(iso: str) -> date:
    """Ngày theo giờ Việt Nam của một mốc thời gian ISO do GitHub cấp (UTC)."""
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(VN).date()


def norm_question(q) -> str:
    """Chuẩn hóa để so câu hỏi: Unicode NFC, gộp khoảng trắng, chữ thường."""
    return re.sub(r"\s+", " ", nfc(str(q or ""))).strip().lower()


def qkey(p):
    """Khóa câu hỏi: câu chữ chuẩn hóa + resolve_at. Dùng chung cho nhận dự báo, phân định và chấm A–B."""
    return (norm_question(p.get("question")), str(p.get("resolve_at", "")))


def parse_issue_form(body: str) -> dict:
    """Thân Issue do GitHub sinh từ mẫu: '### <field>\\n\\n<value>' lặp lại. Trùng tiêu đề → ValueError
    (một dòng '### p' chèn trong ô văn bản không được đè giá trị thật)."""
    out, cur = {}, None
    for line in nfc(body).splitlines():                    # lưu vào sổ ở dạng NFC để A và B dán từ nguồn khác nhau vẫn khớp
        m = re.match(r"^###\s+(.+?)\s*$", line)
        if m:
            cur = m.group(1).strip().lower().replace(" ", "_")
            if cur in out:
                raise ValueError(f"thân Issue có hai tiêu đề '### {cur}'")
            out[cur] = ""
            continue
        if cur is not None:
            out[cur] = (out[cur] + "\n" + line).strip() if out[cur] else line.strip()
    for k in list(out):
        v = out[k]
        if v in EMPTY:
            out.pop(k)
        elif k in NUMERIC:
            try:
                out[k] = float(v.replace(",", "."))          # nhận cả dấu phẩy thập phân kiểu Việt Nam
            except ValueError:
                pass
    return out


def parse_cutoff(s: str):
    """'YYYY-MM' → ngày cuối tháng; 'YYYY-MM-DD' → ngày đó; khác → None."""
    m = re.fullmatch(r"(\d{4})-(\d{2})(?:-(\d{2}))?", str(s or "").strip())
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), m.group(3)
    if not 1 <= mo <= 12:
        return None
    try:
        if d:
            return date(y, mo, int(d))
        return (date(y + (mo == 12), mo % 12 + 1, 1) - timedelta(days=1))
    except ValueError:
        return None


def control_b_hash(path=None):
    """sha256 của khối ```text trong governance/CONTROL_B_PROMPT.md (không kể xuống dòng cuối); None nếu không đọc được."""
    path = path or CONTROL_B
    try:
        m = re.search(r"```text\n(.*?)```", path.read_text(encoding="utf-8"), re.S)
    except OSError:
        return None
    return hashlib.sha256(m.group(1).rstrip("\n").encode("utf-8")).hexdigest() if m else None


def load_rows(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.is_file() else []


def reject(msg) -> int:
    print(json.dumps({"ok": False, "message": f"Từ chối{msg}"}, ensure_ascii=False))
    return 2


def main() -> int:
    number = int(os.environ["ISSUE_NUMBER"])
    created = os.environ["ISSUE_CREATED_AT"]
    author, owner = os.environ.get("ISSUE_AUTHOR", "").strip(), os.environ.get("REPO_OWNER", "").strip()
    if author and owner and author.lower() != owner.lower():
        return reject(f": chỉ Issue do chủ kho ({owner}) mở mới được ghi vào Ledger")
    try:
        data = parse_issue_form(os.environ.get("ISSUE_BODY", ""))
    except ValueError as e:
        return reject(f": {e}")
    try:
        import jsonschema
    except ImportError:
        print(json.dumps({"ok": False, "message": "Lỗi hệ thống: thiếu thư viện jsonschema"}, ensure_ascii=False))
        return 1
    try:
        jsonschema.validate(data, json.loads(SCHEMA.read_text(encoding="utf-8")))
    except Exception as e:  # noqa: BLE001
        return reject(f": không khớp forecast_issue.schema.json — {str(e).splitlines()[0]}")
    created_day = vn_day(created)
    try:
        resolve_at = date.fromisoformat(data["resolve_at"])
    except ValueError:
        return reject(f" (L-05): resolve_at '{data['resolve_at']}' phải có dạng YYYY-MM-DD")
    if resolve_at <= created_day:
        return reject(" (L-05): resolve_at phải sau ngày tạo Issue (giờ Việt Nam)")
    cutoff = parse_cutoff(data["model_cutoff"])
    if cutoff is None:
        return reject(f" (L-05): model_cutoff '{data['model_cutoff']}' phải có dạng YYYY-MM hoặc YYYY-MM-DD (ví dụ 2026-06)")
    if cutoff > created_day:      # cutoff ≤ ngày tạo < resolve_at ⇒ câu hỏi luôn giải SAU ngày cắt dữ liệu (L-05)
        return reject(f" (L-05): model_cutoff {data['model_cutoff']} ở tương lai so với ngày tạo Issue — mô hình không thể "
                      "có dữ liệu sau hôm nay; ghi tháng cắt dữ liệu thật (YYYY-MM)")
    if not recognised_seat(data["author_seat"]):
        return reject(f" (L-09): author_seat '{data['author_seat']}' phải BẮT ĐẦU bằng tên ghế viết — tên mô hình/nhà cung cấp "
                      "(ví dụ 'Claude Project TTC', 'Claude trần', 'ChatGPT trần') hoặc 'Owner'; không nhận ra ghế viết thì "
                      "về sau không xác định được người phân định độc lập")
    hit = recommendation_hit(json.dumps(data, ensure_ascii=False))
    if hit:
        return reject(f" (L-02): nội dung chứa từ khóa khuyến nghị '{hit}'")
    if data["seat"] == "B":
        want = control_b_hash()
        if want is None:
            return reject(": không đọc được khối prompt trong governance/CONTROL_B_PROMPT.md để đối chiếu prompt_hash")
        if str(data.get("prompt_hash", "")).strip().lower() != want:
            return reject(f": seat B phải có prompt_hash = {want} (sha256 khối prompt chuẩn hiện hành; đổi prompt phải qua ADR)")
    elif "prompt_hash" in data:
        return reject(": seat A không dùng prompt chuẩn của nhóm B — để trống prompt_hash")

    rows = load_rows(LEDGER)
    if any(r.get("issue_number") == number for r in rows):
        print(json.dumps({"ok": True, "duplicate": True, "message": f"Dự báo #{number} đã có trong Ledger, bỏ qua (không ghi trùng)"}, ensure_ascii=False))
        return 3
    key, note = qkey(data), ""
    issue_rows = [r for r in rows if "issue_number" in r]
    for r in issue_rows:
        if norm_question(r.get("question")) == key[0] and str(r.get("resolve_at")) != key[1]:
            return reject(f": câu hỏi này đã có trong Ledger với resolve_at {r.get('resolve_at')} ({r.get('id')}); "
                          "cùng câu chữ thì phải cùng resolve_at, hoặc viết câu hỏi mới")
    same_q = [r for r in issue_rows if qkey(r) == key]
    for r in same_q:
        if str(r.get("seat")) == data["seat"]:
            return reject(f": ghế {data['seat']} đã có dự báo cho câu hỏi này ({r.get('id')}); mỗi ghế một dự báo cho một câu hỏi")
        if r.get("resolution_rule") != data["resolution_rule"] or norm_question(r.get("resolution_source")) != norm_question(data["resolution_source"]):
            return reject(f": ghế kia ({r.get('id')}) đã ghi câu hỏi này với resolution_rule/resolution_source khác — "
                          "A và B phải cùng câu hỏi, cùng luật, cùng nguồn phân định")
        if vn_day(r["issue_created_at"]) != created_day:
            note = f" ⚠ Khác ngày với {r.get('id')} — vẫn ghi, nhưng không tính vào cặp A–B (§4.2 đòi cùng ngày)."

    prev = rows[-1]["hash"] if rows else "GENESIS"
    row = {**data, "id": f"F-{number}", "issue_number": number, "issue_created_at": created, "prev_hash": prev}
    if author:
        row["issue_author"] = author
    row["hash"] = line_hash(row)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps({"ok": True, "message": f"Đã ghi dự báo #{number} (seat {data['seat']}, p={data['p']}, resolve_at {data['resolve_at']}), "
                      f"hash {row['hash'][:12]}.{note}"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
