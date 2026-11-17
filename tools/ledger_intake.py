"""Nhận một dự báo từ GitHub Issue 'Forecast' và ghi vào ledger/predictions.jsonl (ARCHITECTURE v3.0 §4.1, ADR-0003).
Chạy trong workflow ledger_intake.yml. Đầu vào qua biến môi trường:
  ISSUE_NUMBER, ISSUE_CREATED_AT (ISO, giờ máy chủ GitHub), ISSUE_BODY (thân Issue dạng form),
  ISSUE_AUTHOR và REPO_OWNER (tùy chọn; có đủ cả hai mà khác nhau → từ chối).
Đầu ra: in JSON {"ok": bool, "message": str, "attest": [...]}; thoát 0 khi ghi được, 2 khi từ chối (không ghi), 3 khi Issue
đã có trong Ledger (bỏ qua), 1 khi lỗi hệ thống. "attest" là dấu nhận "predictions F-<n> <hash>": workflow đăng nó thành
bình luận của github-actions[bot] trên Issue; tools/ledger_audit.py đối chiếu từng dòng sổ với dấu nhận đó.

THỨ TỰ (ADR-0003 quyết định 10). Robot nhận dự báo và robot phân định chạy độc lập; thứ tự chúng GHI có thể khác thứ tự
MỞ Issue. Sổ chỉ ghi thêm nên không được phép ghi một trạng thái mà kiểm lại sẽ đánh đỏ. Ba lớp:
1. Luật lúc ghi dựa vào TRẠNG THÁI SỔ ngay lúc ghi (mỗi lần ghi là "lấy main mới nhất → quyết định → đẩy; main đã đổi thì
   làm lại từ đầu", nên quyết định luôn ứng với đúng trạng thái được ghi tiếp lên): câu hỏi đã có kết quả trong sổ thì
   không nhận thêm dự báo — kể cả khi Issue dự báo mở trước Issue phân định; và một Issue phân định chỉ ghi được khi mọi
   dự báo của câu hỏi đang có trong sổ đều mở TRƯỚC nó (tools/resolution_intake.decide).
2. Tự kiểm trước khi ghi: main() dựng trạng thái sổ SAU KHI GHI trong bộ nhớ và chạy lại toàn bộ luật kiểm (ledger_errors —
   đúng hàm mà tools/validate.py chạy). Có lỗi MỚI thì không ghi, báo lỗi hệ thống. Luật lúc ghi và luật kiểm lại có lệch
   nhau ở đâu đó thì hậu quả là một Issue bị từ chối, không phải một sổ hỏng vĩnh viễn.
3. Hạn ghi: dấu nhận của một dự báo phải được đăng trong 6 giờ sau khi Issue mở và trước ngày resolve_at. Robot không ghi
   khi đã sát các hạn đó (chạy lại một job cũ sau nhiều giờ sẽ tạo dòng không bao giờ có dấu nhận hợp lệ).
PHỤC HỒI, không sửa sổ: (a) Issue bị từ chối → mở Issue mới. (b) Job hỏng giữa chừng → chạy lại job: đã ghi thì không ghi
trùng mà chỉ đăng bổ sung dấu nhận — và CHỈ khi dòng trong sổ khớp thân Issue lúc mở VÀ việc có dòng đó trong sổ qua được
đúng phép tự kiểm của đường ghi (một Issue đã bị robot từ chối thì chạy lại bao nhiêu lần cũng không xin được dấu nhận cho
một dòng ghi tay). (c) Một dự báo đã nằm trong sổ mà dấu nhận không kịp hạn (GitHub không cho đăng bình luận suốt 6 giờ,
hoặc bình luận ✅ bị xóa) → chạy lại job để robot đăng dấu nhận muộn; kiểm toán vẫn đỏ ở dòng đó cho tới khi câu hỏi
được hủy bằng VOID lúc tới resolve_at (VOID không ghi được trước hạn — xem tools/resolution_intake.py). Dấu nhận của dòng
phân định không có hạn 6 giờ, nên (b) luôn đủ cho phân định.

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
- Nhóm đối chứng: seat B bắt buộc prompt_hash = sha256 của PHIÊN BẢN prompt chuẩn có hiệu lực vào ngày Issue mở, theo
  governance/control_b_prompts.jsonl (mỗi dòng một phiên bản: sha256 + ngày bắt đầu hiệu lực; chỉ ghi thêm). Luật này
  giống hệt nhau lúc nhận và lúc kiểm lại, nên một dòng B mang prompt_hash sai không qua được validate dù có dấu nhận
  hay không. Lúc nhận còn đòi khối prompt trong governance/CONTROL_B_PROMPT.md trùng phiên bản mới nhất (đổi prompt mà
  quên thêm dòng phiên bản thì robot ngừng nhận ghế B). Seat A không được có prompt_hash.
- Một câu hỏi (question + resolve_at) mỗi ghế chỉ một dự báo; ghế kia nếu đã ghi thì resolution_rule và resolution_source
  phải giống hệt; cùng câu chữ mà khác resolve_at → từ chối. Khác ngày với ghế kia vẫn ghi nhưng không vào cặp A–B (§4.2).
- Câu hỏi đã được phân định thì không nhận thêm dự báo.
- Mọi dòng của sổ phải đến từ Issue: đường ghi dự báo của engine đang đóng (config.yaml ledger.engine_forecasts), dòng
  không có issue_number là lỗi dù mang mã gì.
Mỗi dòng có id "F-<số Issue>", issue_created_at, issue_author, prev_hash, hash.
"""
import hashlib, json, math, os, pathlib, re, sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tools.laws_checks import ATTEST_WINDOW, line_hash, nfc, recommendation_hit, recognised_seat  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledger" / "predictions.jsonl"
SCHEMA = ROOT / "contracts" / "forecast_issue.schema.json"
CONTROL_B = ROOT / "governance" / "CONTROL_B_PROMPT.md"
CONTROL_B_VERSIONS = ROOT / "governance" / "control_b_prompts.jsonl"
RES = ROOT / "ledger" / "resolutions.jsonl"
NUMERIC = {"p", "base_rate"}
VN = timezone(timedelta(hours=7))
EMPTY = ("_No response_", "None", "")
ATTEST_MARK = "ledger-attest"             # tiền tố dấu nhận trong bình luận của robot; thân Issue không được chứa
SYSTEM_FIELDS = {"id", "issue_number", "issue_created_at", "issue_author", "prev_hash", "hash"}   # do intake thêm, không từ form
_NUMBER_RE = re.compile(r"[0-9]+(?:[.,][0-9]+)?")          # chỉ chữ số ASCII: float() của Python nhận cả 'nan', '1_0', '١٢', '1e309'
_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")       # date.fromisoformat nhận cả '20261210', '2026-W50-4'
_HEX64_RE = re.compile(r"[0-9a-f]{64}")
WRITE_MARGIN = timedelta(minutes=30)      # job nhận chạy tối đa 15 phút: còn dưới 30 phút tới hạn dấu nhận thì không ghi nữa
NOW_ENV = "TTC_INTAKE_NOW"                # chỉ để test đặt giờ; workflow không đặt biến này → dùng đồng hồ máy chạy
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


def ts(iso) -> datetime:
    """Mốc thời gian ISO do GitHub cấp → datetime có múi giờ. ValueError nếu không đọc được hoặc thiếu múi giờ
    (so hai mốc bằng chuỗi sẽ sai khi một bên viết '+00:00', bên kia viết 'Z')."""
    d = datetime.fromisoformat(str(iso).strip().replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError(f"mốc thời gian '{iso}' thiếu múi giờ")
    return d


def vn_day(iso: str) -> date:
    """Ngày theo giờ Việt Nam của một mốc thời gian ISO do GitHub cấp (UTC)."""
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(VN).date()


def now_utc() -> datetime:
    """Giờ hiện tại. Test đặt TTC_INTAKE_NOW; khi chạy thật là đồng hồ của máy chạy workflow. Đây chỉ là lưới an toàn của
    bên ghi — bên kiểm (tools/ledger_audit.py) dùng giờ đăng bình luận do máy chủ GitHub ghi, không tin đồng hồ này."""
    v = os.environ.get(NOW_ENV, "").strip()
    return ts(v) if v else datetime.now(timezone.utc)


def write_deadline_error(created, now, resolve_at=None):
    """Hạn ghi. Dấu nhận (bình luận của robot, đăng ngay sau khi ghi) chỉ hợp lệ khi đăng trong ATTEST_WINDOW sau giờ tạo
    Issue và — với dự báo — trước 00:00 ngày resolve_at (giờ Việt Nam). Một job nhận bị chạy lại muộn, hay một Issue mở
    sát nửa đêm trước ngày resolve_at, nếu vẫn ghi sẽ để lại trong sổ một dòng vĩnh viễn không có dấu nhận hợp lệ. Vì vậy
    còn dưới WRITE_MARGIN tới một trong hai hạn thì KHÔNG ghi. Trả về lời từ chối hoặc None."""
    opened = ts(created)
    if now - opened > ATTEST_WINDOW - WRITE_MARGIN:
        h, m = divmod(int((ATTEST_WINDOW - WRITE_MARGIN).total_seconds() // 60), 60)
        return (f"Issue này mở lúc {created}, tới giờ robot chạy ({now.isoformat(timespec='seconds')}) đã quá {h} giờ {m} phút. "
                f"Dấu nhận của sổ phải được đăng trong {int(ATTEST_WINDOW.total_seconds() // 3600)} giờ sau khi Issue mở, nên robot "
                "không ghi nữa. Mở Issue mới với cùng nội dung (giờ tính từ Issue mới)")
    if resolve_at is not None and (now + WRITE_MARGIN).astimezone(VN).date().isoformat() >= str(resolve_at):
        return (f"(L-05) đã quá sát ngày resolve_at {resolve_at}: dấu nhận của sổ phải được đăng trước 00:00 ngày đó (giờ Việt "
                f"Nam), robot cần ít nhất {int(WRITE_MARGIN.total_seconds() // 60)} phút. Không ghi")
    return None


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


def control_b_versions(path=None) -> list:
    """Các phiên bản prompt chuẩn của ghế B: [(ngày bắt đầu hiệu lực, sha256)] theo thứ tự trong tệp
    governance/control_b_prompts.jsonl. Tệp không có → []. ValueError nếu tệp hỏng: mỗi dòng phải là
    {"sha256": <64 hex>, "valid_from": "YYYY-MM-DD"}, ngày tăng dần, không trùng hash."""
    path = path or CONTROL_B_VERSIONS
    if not path.is_file():
        return []
    out = []
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = strict_loads(raw)
            sha, start = row["sha256"], row["valid_from"]
            if set(row) != {"sha256", "valid_from"} or not isinstance(sha, str) or not _HEX64_RE.fullmatch(sha) \
                    or not isinstance(start, str) or not _DATE_RE.fullmatch(start):
                raise ValueError("sai dạng")
            day = date.fromisoformat(start)
        except (ValueError, KeyError, TypeError):
            raise ValueError(f"dòng {n} không đúng dạng {{\"sha256\": <64 hex>, \"valid_from\": \"YYYY-MM-DD\"}}") from None
        if out and day <= out[-1][0]:
            raise ValueError(f"dòng {n}: valid_from phải sau phiên bản trước")
        if any(sha == h for _, h in out):
            raise ValueError(f"dòng {n}: sha256 trùng một phiên bản trước")
        out.append((day, sha))
    return out


def control_b_hash_on(day, versions):
    """sha256 của phiên bản prompt chuẩn có hiệu lực vào ngày `day` (giờ Việt Nam): phiên bản mới nhất có valid_from ≤ day.
    None nếu chưa phiên bản nào có hiệu lực vào ngày đó."""
    hit = None
    for start, sha in versions:
        if start <= day:
            hit = sha
    return hit


def load_rows(path):
    return [strict_loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.is_file() else []


def _schema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def forecast_error(data, created, issue_rows, res_rows=(), schema=None, live=True, versions=None):
    """Luật nhận một dự báo. data: các trường của form; created: giờ tạo Issue (ISO); issue_rows: các dòng dự báo Issue đã
    có TRƯỚC nó; res_rows: các dòng phân định. Trả về (lỗi hoặc None, ghi chú). Hàm thuần — intake và replay() dùng chung.
    live=True (lúc nhận): res_rows là sổ phân định NGAY LÚC GHI; live=False (kiểm lại dòng đã có): res_rows là cả sổ. Hai
    chỗ khác nhau, và chỉ hai chỗ:
    - seat B: luật prompt_hash giống nhau ở cả hai chế độ (phiên bản có hiệu lực ngày Issue mở); lúc nhận thêm một điều
      kiện về trạng thái kho: khối prompt hiện hành phải trùng phiên bản mới nhất.
    - câu hỏi đã có kết quả: lúc nhận, CÓ BẤT KỲ dòng phân định nào của câu hỏi trong sổ là từ chối — kể cả khi Issue dự
      báo này mở trước Issue phân định (robot ghi theo thứ tự chạy xong, không theo thứ tự mở). Lúc kiểm lại, sổ đầy đủ
      luôn chứa cả các phân định ghi SAU dòng đang xét, nên chỉ phân định mở KHÔNG SAU dự báo mới là lỗi ở đây; trường hợp
      còn lại (dự báo mở trước nhưng ghi sau phân định) do resolution_intake.replay bắt: phân định khi ấy không phủ nó."""
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
        # Cùng một luật lúc nhận và lúc kiểm lại: prompt_hash phải là phiên bản có hiệu lực vào NGÀY ISSUE MỞ. (Trước vòng
        # chấm 9, kiểm lại chỉ đòi 64 ký tự hex: một dòng B ghi tay với prompt_hash sai qua được validate.)
        got = str(data.get("prompt_hash", "")).strip().lower()
        try:
            versions = control_b_versions() if versions is None else versions
        except (OSError, ValueError) as e:
            return f": không đọc được governance/control_b_prompts.jsonl ({str(e).splitlines()[0]})", ""
        want = control_b_hash_on(created_day, versions)
        if want is None:
            return (f": chưa có phiên bản prompt chuẩn nào của ghế B có hiệu lực vào ngày {created_day.isoformat()} "
                    "(governance/control_b_prompts.jsonl)"), ""
        if live and control_b_hash() != versions[-1][1]:
            return (": khối prompt trong governance/CONTROL_B_PROMPT.md không trùng phiên bản mới nhất ghi trong "
                    "governance/control_b_prompts.jsonl — đổi prompt phải qua ADR và thêm một dòng phiên bản; robot ngừng nhận "
                    "dự báo ghế B cho tới khi hai tệp khớp nhau"), ""
        if got != want:
            return (f": seat B phải có prompt_hash = {want} (sha256 của prompt chuẩn có hiệu lực ngày {created_day.isoformat()}, "
                    "theo governance/control_b_prompts.jsonl; đổi prompt phải qua ADR)"), ""
    elif "prompt_hash" in data:
        return ": seat A không dùng prompt chuẩn của nhóm B — để trống prompt_hash", ""

    key, note = qkey(data), ""
    for r in issue_rows:
        if norm_question(r.get("question")) == key[0] and str(r.get("resolve_at")) != key[1]:
            return (f": câu hỏi này đã có trong Ledger với resolve_at {r.get('resolve_at')} ({r.get('id')}); "
                    "cùng câu chữ thì phải cùng resolve_at, hoặc viết câu hỏi mới"), ""
    same_q = [r for r in issue_rows if qkey(r) == key]
    same_ids = {r.get("id") for r in same_q}
    opened = ts(created)
    def not_after(iso):                                    # Issue phân định mở không sau Issue dự báo này (không đọc được → coi là có)
        try:
            return ts(iso) <= opened
        except (TypeError, ValueError):
            return True
    res_q = [r for r in res_rows if r.get("prediction_id") in same_ids and r.get("resolution_issue") is not None]
    done = sorted({str(r.get("prediction_id")) for r in res_q if live or not_after(r.get("resolution_issue_created_at"))})
    if done:
        if all(not not_after(r.get("resolution_issue_created_at")) for r in res_q):
            return (f": câu hỏi này đã được phân định ({', '.join(done)}) trước khi robot ghi được dự báo này. Sổ không nhận "
                    "thêm dự báo cho câu hỏi đã có kết quả, kể cả khi Issue dự báo mở trước Issue phân định (robot ghi theo "
                    "thứ tự chạy xong). Chỉ mở Issue phân định sau khi mọi dự báo của câu hỏi đã có ✅"), ""
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


def replay(pred_rows, res_rows=(), versions=None) -> list[str]:
    """Chạy lại luật nhận trên MỌI dòng dự báo đã có trong sổ, theo thứ tự. Trả về danh sách lỗi.
    versions: các phiên bản prompt ghế B (control_b_versions) của kho đang kiểm; None = kho chứa mô-đun này."""
    errs, prior, seen = [], [], set()
    schema = _schema()
    for row in pred_rows:
        if "issue_number" not in row:
            # Không loại dòng nào được miễn. Trước vòng chấm 8, dòng "trông như của engine" (mã P-…, luật chấm có ticker)
            # được bỏ qua: bốn dấu hiệu ấy ai cũng viết ra được, không chứng minh xuất xứ, và một dòng P- thiếu trường làm
            # vòng học vỡ. Đường ghi dự báo của engine nay ĐÓNG (laws_checks.check_engine_gate), nên mọi dòng phải từ Issue.
            errs.append(f"L-05: dòng dự báo {row.get('id')!r} không có issue_number — mọi dòng của sổ phải đến từ Issue "
                        "'Forecast' (đường ghi dự báo của engine đang đóng: config.yaml ledger.engine_forecasts, ADR-0003 "
                        "quyết định 11); dòng mang mã P-… hay bất kỳ mã nào khác đều không được nằm trong sổ")
            continue
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
            msg, _ = forecast_error(data, row.get("issue_created_at"), prior, res_rows, schema, live=False, versions=versions)
        except Exception as e:  # noqa: BLE001
            msg = f": không đọc được ({str(e).splitlines()[0]})"
        if msg:
            errs.append(f"L-05: dòng dự báo {label} trong sổ không qua luật nhận{msg}")
        prior.append(row)
    return errs


def ledger_errors(pred_rows, res_rows, versions=None) -> list[str]:
    """TOÀN BỘ luật kiểm lại trên một trạng thái của hai sổ (dự báo + phân định). tools/validate.py gọi hàm này trên sổ
    trong kho; hai robot nhận gọi nó trên trạng thái sau khi ghi, trước khi đẩy."""
    from tools import resolution_intake                    # nạp muộn: resolution_intake nhập lại mô-đun này
    return replay(pred_rows, res_rows, versions) + resolution_intake.replay(pred_rows, res_rows)


def post_write_errors(pred_before, res_before, pred_after, res_after) -> list[str]:
    """Tự kiểm trước khi ghi: lỗi kiểm lại có ở trạng thái SAU KHI GHI mà trạng thái trước chưa có. Rỗng = ghi được.
    So với trạng thái trước (chứ không đòi sổ sạch tuyệt đối) để một lỗi cũ đang chờ xử lý không khóa mọi Issue mới."""
    before = ledger_errors(pred_before, res_before)
    return [e for e in ledger_errors(pred_after, res_after) if e not in before]


def system_error(msg) -> int:
    print(json.dumps({"ok": False, "message": f"Lỗi hệ thống: {msg}"}, ensure_ascii=False))
    return 1


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
    if old is not None:
        # Chạy lại job: không ghi trùng, và trả lại dấu nhận để workflow đăng nếu lần trước chưa đăng được — nhưng CHỈ khi dòng
        # đang có trong sổ đúng là dòng robot dựng từ thân Issue lúc mở (job chạy lại nhận đúng thân Issue của sự kiện gốc).
        # Một dòng mang số Issue này mà nội dung khác — ai đó ghi tay rồi chạy lại job để xin dấu nhận — không được cấp.
        if strict_loads(dumps(build_row(data, number, created, author, old.get("prev_hash")))) != old:
            return reject(f": sổ đã có một dòng mang số Issue #{number} nhưng nội dung dòng đó KHÔNG khớp thân Issue lúc mở. Robot "
                          "chỉ cấp dấu nhận cho dòng do chính nó ghi từ thân Issue; dòng kia không có bằng chứng thời điểm")
        # Khớp nội dung chưa đủ: thân Issue có thể chính là thứ robot đã TỪ CHỐI (ví dụ ghế B sai prompt_hash), rồi ai đó ghi
        # tay đúng nội dung ấy vào sổ. Dấu nhận chỉ được cấp khi việc có dòng này trong sổ qua được đúng phép tự kiểm của
        # đường ghi: so sổ không có dòng này với sổ đang có, không được sinh lỗi kiểm lại nào.
        res_rows = load_rows(RES)
        try:
            broken = post_write_errors([r for r in rows if r is not old], res_rows, rows, res_rows)
        except Exception as e:  # noqa: BLE001
            broken = [f"không chạy được kiểm lại ({str(e).splitlines()[0]})"]
        if broken:
            return reject(f": sổ đã có một dòng mang số Issue #{number}, nhưng dòng đó không qua luật nhận — {broken[0]} — nên "
                          "robot không cấp dấu nhận cho nó")
        print(json.dumps({"ok": True, "duplicate": True, "attest": [attest(old)],
                          "message": f"Dự báo #{number} đã có trong Ledger, bỏ qua (không ghi trùng)"}, ensure_ascii=False))
        return 3
    res_rows = load_rows(RES)
    try:
        msg, note = forecast_error(data, created, [r for r in rows if "issue_number" in r], res_rows)
        late = None if msg else write_deadline_error(created, now_utc(), data["resolve_at"])
    except (TypeError, ValueError) as e:
        return reject(f": không đọc được mốc thời gian ({str(e).splitlines()[0]})")
    if msg:
        return reject(msg)
    if late:
        return reject(f": {late}")
    row = build_row(data, number, created, author, rows[-1]["hash"] if rows else "GENESIS")
    try:                                # tự kiểm: trạng thái sổ sau khi ghi dòng này phải qua đúng luật mà validate.py chạy
        broken = post_write_errors(rows, res_rows, rows + [strict_loads(dumps(row))], res_rows)
    except Exception as e:  # noqa: BLE001
        broken = [f"không chạy được kiểm lại ({str(e).splitlines()[0]})"]
    if broken:
        return system_error(f"ghi dự báo #{number} sẽ làm sổ không qua kiểm lại luật — {broken[0]} — nên KHÔNG ghi. Đây là "
                            "lỗi của máy (luật lúc ghi lệch luật kiểm lại), báo cho người giữ mã; sổ không bị đụng tới")
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(dumps(row) + "\n")
    print(json.dumps({"ok": True, "attest": [attest(row)],
                      "message": f"Đã ghi dự báo #{number} (seat {data['seat']}, p={data['p']}, resolve_at {data['resolve_at']}).{note}"},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
