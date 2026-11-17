"""Nhận một phân định từ GitHub Issue 'Resolution' và ghi vào ledger/resolutions.jsonl (ARCHITECTURE v3.0 §4.1 bước 4, ADR-0003).
Chạy trong workflow resolution_intake.yml. Đầu vào qua biến môi trường:
  ISSUE_NUMBER, ISSUE_CREATED_AT (ISO, giờ máy chủ GitHub), ISSUE_BODY (thân Issue dạng form),
  ISSUE_AUTHOR và REPO_OWNER (tùy chọn; có đủ cả hai mà khác nhau → từ chối).
Đầu ra: in JSON {"ok": bool, "message": str}; thoát 0 khi ghi được, 2 khi từ chối (không ghi), 3 khi Issue này đã được ghi,
1 khi lỗi hệ thống.

Luật (mọi "ngày" tính theo giờ Việt Nam, UTC+7):
- Một Issue phân định MỘT CÂU HỎI, và ghi cùng một outcome cho MỌI dự báo Issue của câu hỏi đó (cùng question + resolve_at),
  dù forecast_ids chỉ liệt kê một phần: một câu hỏi chỉ có một sự thật, A và B nhận cùng outcome.
- Câu hỏi đã có bất kỳ dự báo nào được phân định thì không phân định lại (kể cả VOID).
- L-05: không phân định trước resolve_at; ngoại lệ duy nhất: YES khi MỌI dự báo của câu hỏi có luật event_before_date.
- L-09: resolver bắt đầu bằng tên ghế (Owner hoặc mô hình/nhà cung cấp) và không chung GHẾ với bất kỳ người viết dự báo nào
  của câu hỏi (đọc author_seat từng dòng: nhà cung cấp mô hình hoặc Owner; Anthropic luôn bị chặn). author_seat không nhận
  ra được ghế → không ghi. resolver là người ĐỌC NGUỒN và quyết định, không phải người bấm nút.
- Nguồn: YES/NO phải có resolution_source và trích nguyên văn (quote). Nếu resolution_source của dự báo có nêu tên miền
  (vd nso.gov.vn) thì nguồn phân định phải thuộc đúng tên miền đó (hoặc tên miền con) — không đổi nguồn sau khi biết kết quả.
  Nguồn đã hứa không công bố → VOID kèm void_reason.
- L-02: không chứa từ khóa khuyến nghị mua bán.
- Mỗi dòng khớp contracts/resolution.schema.json và nối hash chuỗi (prev_hash/hash) như predictions.jsonl.
Giới hạn: máy không mở được nguồn để kiểm quote; quote và resolver là lời khai có ghi tên, kiểm được bởi người đọc sổ.
"""
import json, os, pathlib, re, sys
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tools.laws_checks import line_hash, recommendation_hit, recognised_seat, _seats  # noqa: E402
from tools.ledger_intake import parse_issue_form, qkey, vn_day, load_rows  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRED = ROOT / "ledger" / "predictions.jsonl"
RES = ROOT / "ledger" / "resolutions.jsonl"
SCHEMA = ROOT / "contracts" / "resolution.schema.json"
OUTCOMES = {"YES": 1, "NO": 0, "VOID": None}
AUTHOR_PROVIDER = "anthropic"            # prompt chuẩn của A và B đều chạy trên Claude → luôn chặn
_TLDS = "vn|com|org|net|gov|edu|int|io|co|uk|us|eu|info|asia"
_DOMAIN_RE = re.compile(r"(?<![a-z0-9@.-])((?:[a-z0-9-]+\.)+(?:" + _TLDS + r"))(?![a-z0-9.-])")   # 'tp.hcm', 'q.iv', 'x.pdf' không phải tên miền


def domains(text) -> set:
    """Tên miền nêu trong một chuỗi nguồn (bỏ 'www.'), vd 'https://www.nso.gov.vn — thông cáo…' → {'nso.gov.vn'}."""
    return {d[4:] if d.startswith("www.") else d for d in _DOMAIN_RE.findall(str(text or "").lower())}


def source_allowed(promised: set, used: set) -> bool:
    """Nguồn phân định hợp lệ khi có ít nhất một tên miền trùng hoặc là tên miền con của một tên miền đã hứa."""
    return any(u == p or u.endswith("." + p) for u in used for p in promised)


def reject(msg) -> int:
    print(json.dumps({"ok": False, "message": f"Từ chối: {msg}"}, ensure_ascii=False))
    return 2


def main() -> int:
    number = int(os.environ["ISSUE_NUMBER"])
    created = os.environ["ISSUE_CREATED_AT"]
    author, owner = os.environ.get("ISSUE_AUTHOR", "").strip(), os.environ.get("REPO_OWNER", "").strip()
    if author and owner and author.lower() != owner.lower():
        return reject(f"chỉ Issue do chủ kho ({owner}) mở mới được ghi vào Ledger")
    try:
        data = parse_issue_form(os.environ.get("ISSUE_BODY", ""))
    except ValueError as e:
        return reject(str(e))
    try:
        import jsonschema
    except ImportError:
        print(json.dumps({"ok": False, "message": "Lỗi hệ thống: thiếu thư viện jsonschema"}, ensure_ascii=False))
        return 1
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    created_day = vn_day(created)

    res_rows = load_rows(RES)
    if any(r.get("resolution_issue") == number for r in res_rows):
        print(json.dumps({"ok": True, "duplicate": True, "message": f"Phân định #{number} đã có trong Ledger, bỏ qua"}, ensure_ascii=False))
        return 3

    ids = list(dict.fromkeys(re.findall(r"F-\d+", str(data.get("forecast_ids", "")))))
    if not ids:
        return reject("forecast_ids phải liệt kê mã dạng F-<số Issue>, ví dụ F-101, F-102")
    outcome_key = str(data.get("outcome", "")).strip().upper()
    if outcome_key not in OUTCOMES:
        return reject("outcome phải là YES, NO hoặc VOID")
    resolver = str(data.get("resolver", "")).strip()
    if not resolver:
        return reject("thiếu resolver (ai đã đọc nguồn và phân định)")
    if not recognised_seat(resolver):
        return reject(f"L-09: resolver '{resolver}' phải BẮT ĐẦU bằng tên ghế: 'Owner', hoặc tên mô hình/nhà cung cấp (ví dụ 'ChatGPT (OpenAI)')")
    source, quote, void_reason = (str(data.get(k, "")).strip() for k in ("resolution_source", "quote", "void_reason"))
    if outcome_key == "VOID":
        if not void_reason:
            return reject("VOID phải có void_reason")
    elif not source or not quote:
        return reject("YES/NO phải có resolution_source và trích nguyên văn (quote) từ nguồn")
    hit = recommendation_hit(json.dumps(data, ensure_ascii=False))
    if hit:
        return reject(f"L-02: nội dung chứa từ khóa khuyến nghị '{hit}'")

    preds = {p.get("id"): p for p in load_rows(PRED) if "issue_number" in p}
    missing = [i for i in ids if i not in preds]
    if missing:
        return reject(f"không có dự báo Issue {missing} trong ledger/predictions.jsonl")
    keys = {qkey(preds[i]) for i in ids}
    if len(keys) != 1:
        return reject("các forecast_ids không cùng câu hỏi và cùng resolve_at; mỗi Issue Resolution chỉ phân định một câu hỏi")
    key = keys.pop()
    group = sorted((p for p in preds.values() if qkey(p) == key), key=lambda p: p.get("issue_number", 0))
    group_ids = [p["id"] for p in group]
    done = {r.get("prediction_id") for r in res_rows}
    already = [i for i in group_ids if i in done]
    if already:
        return reject(f"câu hỏi này đã được phân định ({', '.join(already)}); không phân định lại")

    unknown = [p["id"] for p in group if not recognised_seat(p.get("author_seat"))]
    if unknown:
        return reject(f"L-09: không nhận ra ghế viết (author_seat) của {', '.join(unknown)} nên không xác định được "
                      "người phân định độc lập; không ghi (đóng khi không chắc)")
    authors = {AUTHOR_PROVIDER}
    for p in group:
        authors |= _seats(p.get("author_seat"))          # ghế = nhà cung cấp mô hình HOẶC Owner
    clash = sorted(_seats(resolver) & authors)
    if clash:
        return reject(f"L-09: '{resolver}' chung ghế với người viết dự báo của câu hỏi ({', '.join(clash)}); "
                      "người phân định phải là ghế khác: khác nhà cung cấp, và Owner không phân định dự báo do Owner viết")

    try:
        resolve_at = date.fromisoformat(group[0]["resolve_at"])
    except (KeyError, ValueError):
        return reject(f"resolve_at của {group_ids[0]} không đọc được; không ghi")
    early_ok = outcome_key == "YES" and all(p.get("resolution_rule") == "event_before_date" for p in group)
    if created_day < resolve_at and not early_ok:
        return reject(f"L-05: chưa tới resolve_at {resolve_at.isoformat()} theo giờ Việt Nam (chỉ YES được phân định sớm, "
                      "và chỉ khi mọi dự báo của câu hỏi có luật event_before_date)")

    if outcome_key != "VOID":
        promised = set().union(*[domains(p.get("resolution_source")) for p in group])
        if promised and not source_allowed(promised, domains(source)):
            return reject(f"nguồn phân định phải thuộc tên miền đã hứa trong dự báo ({', '.join(sorted(promised))}); "
                          "nếu nguồn đó không công bố thì chọn VOID và ghi void_reason")

    prev = res_rows[-1]["hash"] if res_rows else "GENESIS"
    rows = []
    for i in group_ids:
        row = {"prediction_id": i, "resolved_at": created_day.isoformat(), "outcome": OUTCOMES[outcome_key],
               "resolution_issue": number, "resolution_issue_created_at": created, "resolver": resolver,
               "resolution_source": source, "quote": quote}
        if author:
            row["resolution_issue_author"] = author
        if data.get("observed_value"):
            row["observed_value"] = str(data["observed_value"]).strip()
        if outcome_key == "VOID":
            row["void"] = void_reason
        try:
            jsonschema.validate(row, schema)
        except Exception as e:  # noqa: BLE001
            return reject(f"không khớp resolution.schema.json — {str(e).splitlines()[0]}")
        row["prev_hash"] = prev
        row["hash"] = line_hash(row)
        prev = row["hash"]
        rows.append(row)
    RES.parent.mkdir(parents=True, exist_ok=True)
    with RES.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    extra = [i for i in group_ids if i not in ids]
    note = f" (gồm cả {', '.join(extra)} — cùng câu hỏi)" if extra else ""
    print(json.dumps({"ok": True, "message": f"Đã phân định {', '.join(group_ids)}: {outcome_key} (resolver: {resolver}){note}"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
