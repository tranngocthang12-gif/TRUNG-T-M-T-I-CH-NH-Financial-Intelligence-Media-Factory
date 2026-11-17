"""Nhận một dự báo từ GitHub Issue 'Forecast' và ghi vào ledger/predictions.jsonl (ARCHITECTURE v3.0 §4.1, ADR-0003).
Chạy trong workflow ledger_intake.yml. Đầu vào qua biến môi trường:
  ISSUE_NUMBER, ISSUE_CREATED_AT (ISO, giờ máy chủ GitHub), ISSUE_BODY (thân Issue dạng form),
  ISSUE_AUTHOR và REPO_OWNER (tùy chọn; có đủ cả hai mà khác nhau → từ chối).
Đầu ra: in JSON {"ok": bool, "message": str, "attest": [...]}; thoát 0 khi ghi được, 2 khi từ chối (không ghi), 3 khi Issue
đã có trong Ledger (bỏ qua), 1 khi lỗi hệ thống. "attest" là dấu nhận "predictions F-<n> <hash>": workflow đăng nó thành
bình luận của github-actions[bot] trên Issue; tools/ledger_audit.py đối chiếu từng dòng sổ với dấu nhận đó.

Luật kiểm lúc nhận — forecast_error() — (mọi "ngày" tính theo giờ Việt Nam, UTC+7). CI chạy LẠI đúng các luật này trên mọi
dòng đã có trong sổ (replay(), gọi từ tools/validate.py), nên một dòng ghi vòng qua intake vẫn bị bắt:
- Thân Issue: mỗi trường đúng một tiêu đề "### <trường>"; trùng tiêu đề hoặc trường lạ → từ chối; chứa chuỗi
  "ledger-attest" → từ chối (bình luận của robot có thể nhắc lại chữ người dùng nhập; không để ai tự viết dấu nhận).
- Khớp contracts/forecast_issue.schema.json; p và base_rate là số thập phân viết bằng chữ số 0-9 (không NaN, không vô
  cực, không ký hiệu mũ); resolve_at đúng dạng YYYY-MM-DD; p trong [0,05; 0,95].
- L-05: resolve_at sau ngày tạo Issue; model_cutoff dạng YYYY-MM hoặc YYYY-MM-DD và không ở tương lai. Hai điều này
  cùng bảo đảm câu hỏi giải SAU ngày cắt dữ liệu của mô hình (cutoff ≤ ngày tạo < resolve_at).
- L-09: author_seat bắt đầu bằng tên ghế (mô hình/nhà cung cấp hoặc Owner) — để về sau xác định người phân định độc lập.
- L-02: không chứa từ khóa khuyến nghị mua bán (Ledger chỉ ghi thêm; một dòng sai sẽ làm validate đỏ mãi).
- resolution_source phải nêu ít nhất một tên miền (vd nso.gov.vn): lời hứa về nguồn phải máy kiểm được lúc phân định.
- Nhóm đối chứng: seat B bắt buộc prompt_hash = sha256 khối prompt hiện hành trong governance/CONTROL_B_PROMPT.md;
  seat A không được có prompt_hash.
- Một câu hỏi (question + resolve_at) mỗi ghế chỉ một dự báo; ghế kia nếu đã ghi thì resolution_rule và resolution_source
  phải giống hệt; cùng câu chữ mà khác resolve_at → từ chối. Khác ngày với ghế kia vẫn ghi nhưng không vào cặp A–B (§4.2).
- Câu hỏi đã được phân định thì không nhận thêm dự báo.
Mỗi dòng có id "F-<số Issue>", issue_created_at, issue_author, prev_hash, hash.
"""
import hashlib, json, math, os, pathlib, re, sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tools.laws_checks import line_hash, nfc, recommendation_hit, recognised_seat  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledger" / "predictions.jsonl"
SCHEMA = ROOT / "contracts" / "forecast_issue.schema.json"
CONTROL_B = ROOT / "governance" / "CONTROL_B_PROMPT.md"
RES = ROOT / "ledger" / "resolutions.jsonl"
NUMERIC = {"p", "base_rate"}
VN = timezone(timedelta(hours=7))
EMPTY = ("_No response_", "None", "")
ATTEST_MARK = "ledger-attest"             # tiền tố dấu nhận trong bình luận của robot; thân Issue không được chứa
SYSTEM_FIELDS = {"id", "issue_number", "issue_created_at", "issue_author", "prev_hash", "hash"}   # do intake thêm, không từ form
_NUMBER_RE = re.compile(r"[0-9]+(?:[.,][0-9]+)?")          # chỉ chữ số ASCII: float() của Python nhận cả 'nan', '1_0', '١٢', '1e309'
_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")       # date.fromisoformat nhận cả '20261210', '2026-W50-4'
_HEX64_RE = re.compile(r"[0-9a-f]{64}")
# Tên miền trong một chuỗi nguồn. 'tp.hcm', 'q.iv', 'x.pdf' không phải tên miền (đuôi phải thuộc danh sách).
_TLDS = "vn|com|org|net|gov|edu|int|io|co|uk|us|eu|info|asia"
_DOMAIN_RE = re.compile(r"(?<![a-z0-9@.-])((?:[a-z0-9-]+\.)+(?:" + _TLDS + r"))(?![a-z0-9.-])")
_URL_RE = re.compile(r"https?://[^\s<>\"'`]+", re.I)


def parse_number(v):
    """Chuỗi số thập phân viết bằng chữ số 0-9 (dấu chấm hoặc dấu phẩy) → float hữu hạn; khác → None."""
    v = str(v).strip()
    if not _NUMBER_RE.fullmatch(v):
        return None
    x = float(v.replace(",", "."))
    return x if math.isfinite(x) else None


def dumps(row) -> str:
    """Một dòng sổ: JSON chuẩn (allow_nan=False — NaN/Infinity không phải JSON), khóa sắp xếp."""
    return json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False)


def _strict_const(name):
    raise ValueError(f"giá trị {name} không phải JSON chuẩn")


def strict_loads(line):
    """json.loads từ chối NaN/Infinity (mặc định Python đọc được, công cụ khác thì không)."""
    return json.loads(line, parse_constant=_strict_const)


def promised_domains(text) -> set:
    """Tên miền một dự báo hứa dùng để phân định (bỏ 'www.'). URL chỉ tính phần máy chủ, không tính đường dẫn/tham số."""
    t = str(text or "").lower()
    def host(m):
        try:
            from urllib.parse import urlsplit
            return " " + (urlsplit(m.group(0)).hostname or "") + " "
        except ValueError:
            return " "
    t = _URL_RE.sub(host, t)
    return {d[4:] if d.startswith("www.") else d for d in _DOMAIN_RE.findall(t)}


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
    if ATTEST_MARK in nfc(body).lower():
        raise ValueError(f"thân Issue chứa chuỗi dành riêng '{ATTEST_MARK}' (chỉ robot được viết dấu nhận)")
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
            x = parse_number(v)                             # nhận dấu phẩy thập phân kiểu Việt Nam; 'NaN', '1e309', '35%' giữ
            if x is not None:                               # nguyên là chuỗi → schema từ chối vì không phải số
                out[k] = x
    return out


def parse_cutoff(s: str):
    """'YYYY-MM' → ngày cuối tháng; 'YYYY-MM-DD' → ngày đó; khác → None."""
    m = re.fullmatch(r"([0-9]{4})-([0-9]{2})(?:-([0-9]{2}))?", str(s or "").strip())
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
    return [strict_loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.is_file() else []


def _schema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def forecast_error(data, created, issue_rows, res_rows=(), schema=None, prompt_hash="current"):
    """Luật nhận một dự báo. data: các trường của form; created: giờ tạo Issue (ISO); issue_rows: các dòng dự báo Issue đã
    có TRƯỚC nó; res_rows: các dòng phân định. Trả về (lỗi hoặc None, ghi chú). Hàm thuần — intake và replay() dùng chung.
    prompt_hash="current": seat B phải khớp prompt hiện hành (lúc nhận); None: chỉ kiểm dạng (lúc kiểm lại dòng cũ, vì
    prompt có thể đã đổi qua ADR sau khi dòng được ghi)."""
    import jsonschema
    try:
        jsonschema.validate(data, schema or _schema())
    except Exception as e:  # noqa: BLE001
        return f": không khớp forecast_issue.schema.json — {str(e).splitlines()[0]}", ""
    for k in NUMERIC:
        if isinstance(data[k], bool) or not isinstance(data[k], (int, float)) or not math.isfinite(data[k]):
            return f": {k} phải là số hữu hạn", ""
    created_day = vn_day(created)
    if not _DATE_RE.fullmatch(data["resolve_at"]):
        return f" (L-05): resolve_at '{data['resolve_at']}' phải có dạng YYYY-MM-DD", ""
    try:
        resolve_at = date.fromisoformat(data["resolve_at"])
    except ValueError:
        return f" (L-05): resolve_at '{data['resolve_at']}' phải có dạng YYYY-MM-DD", ""
    if resolve_at <= created_day:
        return " (L-05): resolve_at phải sau ngày tạo Issue (giờ Việt Nam)", ""
    cutoff = parse_cutoff(data["model_cutoff"])
    if cutoff is None:
        return f" (L-05): model_cutoff '{data['model_cutoff']}' phải có dạng YYYY-MM hoặc YYYY-MM-DD (ví dụ 2026-06)", ""
    if cutoff > created_day:      # cutoff ≤ ngày tạo < resolve_at ⇒ câu hỏi luôn giải SAU ngày cắt dữ liệu (L-05)
        return (f" (L-05): model_cutoff {data['model_cutoff']} ở tương lai so với ngày tạo Issue — mô hình không thể "
                "có dữ liệu sau hôm nay; ghi tháng cắt dữ liệu thật (YYYY-MM)"), ""
    if not recognised_seat(data["author_seat"]):
        return (f" (L-09): author_seat '{data['author_seat']}' phải BẮT ĐẦU bằng tên ghế viết — tên mô hình/nhà cung cấp "
                "(ví dụ 'Claude Project TTC', 'Claude trần', 'ChatGPT trần') hoặc 'Owner'; không nhận ra ghế viết thì "
                "về sau không xác định được người phân định độc lập"), ""
    hit = recommendation_hit(json.dumps(data, ensure_ascii=False))
    if hit:
        return f" (L-02): nội dung chứa từ khóa khuyến nghị '{hit}'", ""
    if not promised_domains(data["resolution_source"]):
        return (": resolution_source phải nêu ít nhất một tên miền của nguồn (ví dụ nso.gov.vn, sbv.gov.vn) — lúc phân "
                "định máy chỉ nhận đường dẫn thuộc tên miền đã hứa"), ""
    if data["seat"] == "B":
        got = str(data.get("prompt_hash", "")).strip().lower()
        if prompt_hash == "current":
            want = control_b_hash()
            if want is None:
                return ": không đọc được khối prompt trong governance/CONTROL_B_PROMPT.md để đối chiếu prompt_hash", ""
            if got != want:
                return f": seat B phải có prompt_hash = {want} (sha256 khối prompt chuẩn hiện hành; đổi prompt phải qua ADR)", ""
        elif not _HEX64_RE.fullmatch(got):
            return ": seat B phải có prompt_hash là sha256 (64 ký tự hex) của prompt chuẩn", ""
    elif "prompt_hash" in data:
        return ": seat A không dùng prompt chuẩn của nhóm B — để trống prompt_hash", ""

    key, note = qkey(data), ""
    for r in issue_rows:
        if norm_question(r.get("question")) == key[0] and str(r.get("resolve_at")) != key[1]:
            return (f": câu hỏi này đã có trong Ledger với resolve_at {r.get('resolve_at')} ({r.get('id')}); "
                    "cùng câu chữ thì phải cùng resolve_at, hoặc viết câu hỏi mới"), ""
    same_q = [r for r in issue_rows if qkey(r) == key]
    same_ids = {r.get("id") for r in same_q}
    done = sorted({str(r.get("prediction_id")) for r in res_rows if r.get("prediction_id") in same_ids
                   and str(r.get("resolution_issue_created_at") or "") <= created})
    if done:
        return f": câu hỏi này đã được phân định ({', '.join(done)}); không nhận thêm dự báo sau khi đã có kết quả", ""
    for r in same_q:
        if str(r.get("seat")) == data["seat"]:
            return f": ghế {data['seat']} đã có dự báo cho câu hỏi này ({r.get('id')}); mỗi ghế một dự báo cho một câu hỏi", ""
        if r.get("resolution_rule") != data["resolution_rule"] or norm_question(r.get("resolution_source")) != norm_question(data["resolution_source"]):
            return (f": ghế kia ({r.get('id')}) đã ghi câu hỏi này với resolution_rule/resolution_source khác — "
                    "A và B phải cùng câu hỏi, cùng luật, cùng nguồn phân định"), ""
        if vn_day(r["issue_created_at"]) != created_day:
            note = f" ⚠ Khác ngày với {r.get('id')} — vẫn ghi, nhưng không tính vào cặp A–B (§4.2 đòi cùng ngày)."
    return None, note


def build_row(data, number, created, author, prev):
    row = {**data, "id": f"F-{number}", "issue_number": number, "issue_created_at": created, "prev_hash": prev}
    if author:
        row["issue_author"] = author
    row["hash"] = line_hash(row)
    return row


def attest(row) -> str:
    """Dấu nhận của một dòng dự báo: workflow đăng thành bình luận, kiểm toán đối chiếu (tools/ledger_audit.py)."""
    return f"predictions {row.get('id')} {row.get('hash')}"


def replay(pred_rows, res_rows=()) -> list[str]:
    """Chạy lại luật nhận trên mọi dòng dự báo Issue đã có trong sổ, theo thứ tự. Trả về danh sách lỗi."""
    errs, prior, seen = [], [], set()
    schema = _schema()
    for row in pred_rows:
        if "issue_number" not in row:
            continue                                        # dòng của engine: hợp đồng khác, engine/ledger.py lo
        n, label = row.get("issue_number"), row.get("id")
        if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
            errs.append(f"L-05: dòng dự báo {label}: issue_number {n!r} không phải số Issue"); continue
        if label != f"F-{n}":
            errs.append(f"L-05: dòng dự báo có id {label!r} không khớp issue_number {n} (phải là F-{n})")
        if n in seen:
            errs.append(f"L-05: Issue #{n} có hai dòng dự báo trong sổ")
        seen.add(n)
        data = {k: v for k, v in row.items() if k not in SYSTEM_FIELDS}
        try:
            msg, _ = forecast_error(data, row.get("issue_created_at"), prior, res_rows, schema, prompt_hash=None)
        except Exception as e:  # noqa: BLE001
            msg = f": không đọc được ({str(e).splitlines()[0]})"
        if msg:
            errs.append(f"L-05: dòng dự báo {label} trong sổ không qua luật nhận{msg}")
        prior.append(row)
    return errs


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
        import jsonschema  # noqa: F401
    except ImportError:
        print(json.dumps({"ok": False, "message": "Lỗi hệ thống: thiếu thư viện jsonschema"}, ensure_ascii=False))
        return 1
    rows = load_rows(LEDGER)
    old = next((r for r in rows if r.get("issue_number") == number), None)
    if old is not None:        # chạy lại job: không ghi trùng, nhưng trả lại dấu nhận để workflow đăng nếu lần trước chưa đăng được
        print(json.dumps({"ok": True, "duplicate": True, "attest": [attest(old)],
                          "message": f"Dự báo #{number} đã có trong Ledger, bỏ qua (không ghi trùng)"}, ensure_ascii=False))
        return 3
    msg, note = forecast_error(data, created, [r for r in rows if "issue_number" in r], load_rows(RES))
    if msg:
        return reject(msg)
    row = build_row(data, number, created, author, rows[-1]["hash"] if rows else "GENESIS")
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(dumps(row) + "\n")
    print(json.dumps({"ok": True, "attest": [attest(row)],
                      "message": f"Đã ghi dự báo #{number} (seat {data['seat']}, p={data['p']}, resolve_at {data['resolve_at']}).{note}"},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
