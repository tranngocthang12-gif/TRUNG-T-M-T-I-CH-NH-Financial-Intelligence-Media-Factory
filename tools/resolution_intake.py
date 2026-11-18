"""Nhận một phân định từ GitHub Issue 'Resolution' và ghi vào ledger/resolutions.jsonl (ARCHITECTURE v3.0 §4.1 bước 4, ADR-0003).
Chạy trong workflow resolution_intake.yml. Đầu vào qua biến môi trường:
  ISSUE_NUMBER, ISSUE_CREATED_AT (ISO, giờ máy chủ GitHub), ISSUE_BODY (thân Issue dạng form),
  ISSUE_AUTHOR và REPO_OWNER (tùy chọn; có đủ cả hai mà khác nhau → từ chối).
Đầu ra: in JSON {"ok": bool, "message": str, "attest": [...]}; thoát 0 khi ghi được, 2 khi từ chối (không ghi), 3 khi Issue
này đã được ghi, 1 khi lỗi hệ thống. "attest" là dấu nhận "resolutions F-<n> <hash>" cho từng dòng (xem ledger_intake.py).

Luật — decide() — (mọi "ngày" tính theo giờ Việt Nam, UTC+7). CI chạy LẠI đúng các luật này trên mọi dòng phân định đã
có trong sổ (replay(), gọi từ tools/validate.py):
- Một Issue phân định MỘT CÂU HỎI, và ghi cùng một outcome cho MỌI dự báo Issue của câu hỏi đó (cùng question + resolve_at),
  dù forecast_ids chỉ liệt kê một phần: một câu hỏi chỉ có một sự thật, A và B nhận cùng outcome.
- THỨ TỰ (ADR-0003 quyết định 10): một Issue phân định chỉ ghi kết quả cho dự báo mở TRƯỚC nó. Nếu trong sổ đang có dự
  báo của câu hỏi mở cùng lúc hoặc sau Issue phân định này (robot nhận dự báo chạy xong trước robot phân định) thì KHÔNG
  ghi gì — không ghi kết quả cho dự báo mở sau, cũng không bỏ sót nó: mở Issue Resolution mới. Chiều ngược lại (dự báo mở
  trước nhưng robot ghi sau khi đã có kết quả) do tools/ledger_intake.py từ chối. Nhờ vậy, ở mọi thứ tự chạy xong của
  hai robot, sổ luôn thỏa: mọi dự báo của một câu hỏi đã phân định đều mở trước Issue phân định và đều có dòng kết quả.
- Câu hỏi đã có bất kỳ dự báo nào được phân định thì không phân định lại (kể cả VOID).
- L-05: không phân định trước resolve_at — kể cả VOID; ngoại lệ duy nhất: YES khi MỌI dự báo của câu hỏi có luật
  event_before_date. (Vòng chấm 9: cho VOID trước hạn là mở đường chọn mẫu — hủy câu hỏi khi triển vọng của một ghế xấu
  đi. VOID lúc tới hạn cũng là một quyền chọn, nên phép kiểm định A–B tính mọi cặp bất đồng bị VOID theo hướng BẤT LỢI cho
  kết luận đang xét: engine/ledger.issue_summary.)
- L-09: resolver bắt đầu bằng tên ghế (Owner hoặc mô hình/nhà cung cấp) và không chung GHẾ với bất kỳ người viết dự báo nào
  của câu hỏi (đọc author_seat từng dòng: nhà cung cấp mô hình hoặc Owner; Anthropic luôn bị chặn). author_seat không nhận
  ra được ghế → không ghi. resolver là người ĐỌC NGUỒN và quyết định, không phải người bấm nút.
- Nguồn: YES/NO phải có trích nguyên văn (quote) và resolution_source chứa ít nhất một đường dẫn http(s) đầy đủ. Máy tách
  TÊN MÁY CHỦ của từng đường dẫn bằng urllib (không dò chuỗi): MỌI đường dẫn phải thuộc tên miền đã hứa trong dự báo
  (hoặc tên miền con). Tên miền nằm trong đường dẫn, tham số, hay phần đăng nhập (https://nso.gov.vn@evil.com) không
  được tính; đường dẫn có '@' hoặc '\' bị từ chối. Nguồn đã hứa không công bố → VOID kèm void_reason.
- L-02: không chứa từ khóa khuyến nghị mua bán.
- Mỗi dòng khớp contracts/resolution.schema.json và nối hash chuỗi (prev_hash/hash) như predictions.jsonl.
- Mọi đường dẫn nguồn phải dùng https:// (http:// bị từ chối).
- Mọi dòng của sổ phải đến từ Issue 'Resolution': dòng không có resolution_issue là lỗi (đường ghi của engine đang đóng).
- Trước khi ghi, main() tự chạy lại toàn bộ luật kiểm trên trạng thái sổ sau khi ghi (ledger_intake.post_write_errors) —
  xem phần THỨ TỰ trong tools/ledger_intake.py. Chạy lại job của một Issue đã ghi: không ghi trùng, chỉ trả lại dấu nhận,
  và chỉ khi các dòng trong sổ đúng là kết quả của luật phân định trên thân Issue lúc mở.
Giới hạn: máy không mở được nguồn để kiểm quote; quote và resolver là lời khai có ghi tên, kiểm được bởi người đọc sổ.
"""
import json, os, pathlib, re, sys
from datetime import date
from urllib.parse import urlsplit

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tools.laws_checks import line_hash, recommendation_hit, recognised_seat, _seats  # noqa: E402
from tools.ledger_intake import (parse_issue_form, qkey, vn_day, ts, load_rows, dumps, strict_loads, promised_domains,  # noqa: E402
                                 post_write_errors, system_error, _URL_RE, ATTEST_MARK)

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRED = ROOT / "ledger" / "predictions.jsonl"
RES = ROOT / "ledger" / "resolutions.jsonl"
SCHEMA = ROOT / "contracts" / "resolution.schema.json"
OUTCOMES = {"YES": 1, "NO": 0, "VOID": None}
AUTHOR_PROVIDER = "anthropic"            # prompt chuẩn của A và B đều chạy trên Claude → luôn chặn
OUTCOME_KEYS = {1: "YES", 0: "NO", None: "VOID"}
_HOST_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+")
_ID_RE = re.compile(r"F-[0-9]+")                      # chữ số ASCII: '\d' của Python nhận cả chữ số Ả Rập, Devanagari…
SYSTEM_FIELDS = {"prev_hash", "hash"}


def url_hosts(text) -> set:
    """Tên máy chủ (bỏ 'www.') của MỌI đường dẫn trong chuỗi nguồn, tách bằng urllib chứ không dò chuỗi.
    ValueError nếu có đường dẫn không dùng https:// (ADR-0003 quyết định 2 đòi https; http:// bị từ chối), hoặc không tách
    được chắc chắn: có phần đăng nhập ('@'), dấu '\\' (trình duyệt coi là '/'), hoặc tên máy chủ có ký tự ngoài a-z, 0-9,
    '-', '.'."""
    hosts = set()
    for u in _URL_RE.findall(str(text or "")):
        try:
            parts = urlsplit(u)
            host = (parts.hostname or "").lower().rstrip(".")
            parts.port                                   # cổng không phải số → ValueError
        except ValueError:
            raise ValueError(f"đường dẫn '{u}' không đọc được") from None
        if parts.scheme.lower() != "https":
            raise ValueError(f"đường dẫn '{u}' không dùng https:// — nguồn phân định phải là đường dẫn https:// đầy đủ")
        if "@" in parts.netloc or "\\" in u:
            raise ValueError(f"đường dẫn '{u}' có '@' hoặc '\\' trong phần máy chủ — ghi đường dẫn thẳng tới trang nguồn")
        if not _HOST_RE.fullmatch(host):
            raise ValueError(f"đường dẫn '{u}' có tên máy chủ không hợp lệ")
        hosts.add(host[4:] if host.startswith("www.") else host)
    return hosts


def source_allowed(promised: set, hosts: set) -> bool:
    """Hợp lệ khi có ít nhất một đường dẫn và MỌI máy chủ đều trùng hoặc là tên miền con của một tên miền đã hứa."""
    return bool(hosts) and bool(promised) and all(any(h == p or h.endswith("." + p) for p in promised) for h in hosts)


def reject(msg) -> int:
    print(json.dumps({"ok": False, "message": f"Từ chối: {msg}"}, ensure_ascii=False))
    return 2


def decide(data, number, created, author, pred_rows, res_rows, schema=None):
    """Luật phân định. data: các trường của form; pred_rows: CẢ sổ dự báo (lúc ghi: sổ ngay lúc đó; lúc kiểm lại: sổ đầy
    đủ — câu hỏi đã phân định không nhận thêm dự báo nên hai thứ trùng nhau với câu hỏi đang xét); res_rows: các dòng phân
    định đã có TRƯỚC Issue này. Trả về (lỗi hoặc None, các dòng sẽ ghi — chưa có prev_hash/hash, ghi chú). Hàm thuần —
    intake và replay() gọi với cùng đầu vào, nên kiểm lại không thể ra kết quả khác lúc ghi."""
    import jsonschema
    schema = schema or json.loads(SCHEMA.read_text(encoding="utf-8"))
    created_day = vn_day(created)
    ids = list(dict.fromkeys(_ID_RE.findall(str(data.get("forecast_ids", "")))))
    if not ids:
        return "forecast_ids phải liệt kê mã dạng F-<số Issue>, ví dụ F-101, F-102", [], ""
    outcome_key = str(data.get("outcome", "")).strip().upper()
    if outcome_key not in OUTCOMES:
        return "outcome phải là YES, NO hoặc VOID", [], ""
    resolver = str(data.get("resolver", "")).strip()
    if not resolver:
        return "thiếu resolver (ai đã đọc nguồn và phân định)", [], ""
    if not recognised_seat(resolver):
        return f"L-09: resolver '{resolver}' phải BẮT ĐẦU bằng tên ghế: 'Owner', hoặc tên mô hình/nhà cung cấp (ví dụ 'ChatGPT (OpenAI)')", [], ""
    source, quote, void_reason = (str(data.get(k, "")).strip() for k in ("resolution_source", "quote", "void_reason"))
    if any(ATTEST_MARK in str(v).lower() for v in data.values()):
        return f"nội dung chứa chuỗi dành riêng '{ATTEST_MARK}' (chỉ robot được viết dấu nhận)", [], ""
    if outcome_key == "VOID":
        if not void_reason:
            return "VOID phải có void_reason", [], ""
    elif not source or not quote:
        return "YES/NO phải có resolution_source và trích nguyên văn (quote) từ nguồn", [], ""
    hit = recommendation_hit(json.dumps(data, ensure_ascii=False))
    if hit:
        return f"L-02: nội dung chứa từ khóa khuyến nghị '{hit}'", [], ""

    preds = {p.get("id"): p for p in pred_rows if "issue_number" in p}
    missing = [i for i in ids if i not in preds]
    if missing:
        return f"không có dự báo Issue {missing} trong ledger/predictions.jsonl", [], ""
    keys = {qkey(preds[i]) for i in ids}
    if len(keys) != 1:
        return "các forecast_ids không cùng câu hỏi và cùng resolve_at; mỗi Issue Resolution chỉ phân định một câu hỏi", [], ""
    key = keys.pop()
    group = sorted((p for p in preds.values() if qkey(p) == key), key=lambda p: p.get("issue_number", 0))
    group_ids = [p["id"] for p in group]
    try:
        opened = ts(created)
        late = [p["id"] for p in group if ts(p.get("issue_created_at")) >= opened]
    except (TypeError, ValueError):
        return f"không đọc được giờ tạo Issue của một dự báo trong câu hỏi ({', '.join(group_ids)}); không ghi", [], ""
    if late:
        return (f"L-05: dự báo {', '.join(late)} của câu hỏi này được mở cùng lúc hoặc sau Issue phân định này ({created}). Một "
                "Issue phân định chỉ ghi kết quả cho dự báo mở TRƯỚC nó và phải ghi cho mọi dự báo của câu hỏi, nên lần này "
                "không ghi gì. Mở Issue Resolution mới — nó sẽ phân định cả các dự báo đó"), [], ""
    done = {r.get("prediction_id") for r in res_rows}
    already = [i for i in group_ids if i in done]
    if already:
        return f"câu hỏi này đã được phân định ({', '.join(already)}); không phân định lại", [], ""

    unknown = [p["id"] for p in group if not recognised_seat(p.get("author_seat"))]
    if unknown:
        return (f"L-09: không nhận ra ghế viết (author_seat) của {', '.join(unknown)} nên không xác định được "
                "người phân định độc lập; không ghi (đóng khi không chắc)"), [], ""
    authors = {AUTHOR_PROVIDER}
    for p in group:
        authors |= _seats(p.get("author_seat"))          # ghế = nhà cung cấp mô hình HOẶC Owner
    clash = sorted(_seats(resolver) & authors)
    if clash:
        return (f"L-09: '{resolver}' chung ghế với người viết dự báo của câu hỏi ({', '.join(clash)}); "
                "người phân định phải là ghế khác: khác nhà cung cấp, và Owner không phân định dự báo do Owner viết"), [], ""

    try:
        resolve_at = date.fromisoformat(group[0]["resolve_at"])
    except (KeyError, TypeError, ValueError):
        return f"resolve_at của {group_ids[0]} không đọc được; không ghi", [], ""
    early_ok = outcome_key == "YES" and all(p.get("resolution_rule") == "event_before_date" for p in group)
    if created_day < resolve_at and not early_ok:
        return (f"L-05: chưa tới resolve_at {resolve_at.isoformat()} theo giờ Việt Nam (trước hạn chỉ ghi được YES, và chỉ khi "
                "mọi dự báo của câu hỏi có luật event_before_date; VOID cũng phải chờ tới hạn)"), [], ""

    if outcome_key != "VOID":
        promised = set().union(*[promised_domains(p.get("resolution_source")) for p in group])
        if not promised:
            return ("dự báo của câu hỏi này không hứa tên miền nguồn nào nên máy không kiểm được nguồn phân định; "
                    "chỉ ghi được VOID kèm void_reason (đóng khi không chắc)"), [], ""
        try:
            hosts = url_hosts(source)
        except ValueError as e:
            return f"nguồn phân định: {e}", [], ""
        if not hosts:
            return ("resolution_source phải có đường dẫn đầy đủ bắt đầu bằng https:// tới trang nguồn "
                    f"(thuộc {', '.join(sorted(promised))})"), [], ""
        hosts |= promised_domains(source)              # cả tên miền viết trần (không https://) cũng phải thuộc nguồn đã hứa
        if not source_allowed(promised, hosts):
            return (f"mọi đường dẫn và tên miền trong nguồn phân định phải thuộc tên miền đã hứa trong dự báo ({', '.join(sorted(promised))}); "
                    f"đang có {', '.join(sorted(hosts))}. Nếu nguồn đã hứa không công bố thì chọn VOID và ghi void_reason"), [], ""

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
            return f"không khớp resolution.schema.json — {str(e).splitlines()[0]}", [], ""
        rows.append(row)
    extra = [i for i in group_ids if i not in ids]
    note = f" (gồm cả {', '.join(extra)} — cùng câu hỏi)" if extra else ""
    return None, rows, f"Đã phân định {', '.join(group_ids)}: {outcome_key} (resolver: {resolver}){note}"


def chain(rows, prev):
    out = []
    for r in rows:
        r = {**r, "prev_hash": prev}
        r["hash"] = line_hash(r)
        prev = r["hash"]
        out.append(r)
    return out


def attest(row) -> str:
    return f"resolutions {row.get('prediction_id')} {row.get('hash')}"


def replay(pred_rows, res_rows) -> list[str]:
    """Chạy lại luật phân định trên MỌI dòng phân định đã có trong sổ, theo thứ tự: gom các dòng theo Issue phân định,
    dựng lại form từ các dòng, cho qua decide() với đúng đầu vào lúc ghi, kết quả phải ra đúng các dòng đang có.
    Trả về danh sách lỗi."""
    errs, prior, seen, i = [], [], set(), 0
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    while i < len(res_rows):
        r = res_rows[i]
        n = r.get("resolution_issue")
        if n is None:
            # Không loại dòng nào được miễn (vòng chấm 7 và 8): dòng thiếu resolution_issue né được chạy lại luật, né đối
            # chiếu Issue và né dấu nhận. Đường ghi của engine đang đóng nên không còn dòng "engine tự chấm" hợp lệ nào.
            errs.append(f"L-05: dòng phân định cho {r.get('prediction_id')!r} không có resolution_issue — mọi dòng của sổ phải "
                        "đến từ Issue 'Resolution' (đường ghi của engine đang đóng: config.yaml ledger.engine_forecasts, "
                        "ADR-0003 quyết định 11)")
            prior.append(r); i += 1; continue
        j = i
        while j < len(res_rows) and res_rows[j].get("resolution_issue") == n:
            j += 1
        group, label = res_rows[i:j], f"phân định Issue #{n}"
        if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
            errs.append(f"L-05: {label}: resolution_issue không phải số Issue")
        elif n in seen:
            errs.append(f"L-05: {label} xuất hiện ở hai chỗ trong sổ")
        else:
            seen.add(n)
            g0 = group[0]
            data = {"forecast_ids": ", ".join(str(x.get("prediction_id")) for x in group),
                    "outcome": OUTCOME_KEYS.get(g0.get("outcome") if not isinstance(g0.get("outcome"), bool) else "?", "?"),
                    "resolver": g0.get("resolver", ""), "resolution_source": g0.get("resolution_source", ""),
                    "quote": g0.get("quote", ""), "void_reason": g0.get("void", "")}
            if g0.get("observed_value"):
                data["observed_value"] = g0["observed_value"]
            try:
                msg, want, _ = decide(data, n, g0.get("resolution_issue_created_at"), g0.get("resolution_issue_author", ""),
                                      pred_rows, prior, schema)
            except Exception as e:  # noqa: BLE001
                msg, want = f"không đọc được ({str(e).splitlines()[0]})", []
            have = [{k: v for k, v in x.items() if k not in SYSTEM_FIELDS} for x in group]
            if msg:
                errs.append(f"L-05: {label} trong sổ không qua luật phân định: {msg}")
            elif want != have:
                errs.append(f"L-05: {label}: các dòng trong sổ không khớp kết quả chạy lại luật phân định "
                            f"(phải có đúng {len(want)} dòng cho {', '.join(w['prediction_id'] for w in want)}, cùng nội dung)")
        prior += group
        i = j
    return errs


def publication_main(data, number, created, author, pred_rows) -> int:
    """Ghi ledger/publication_evidence.jsonl. Không ghi resolutions.jsonl, không đóng mẫu 194."""
    from tools.ledger_intake import PUB, publication_prepare, post_write_errors
    pub_rows = load_rows(PUB)
    old = [r for r in pub_rows if r.get("issue_number") == number]
    if old:
        try:
            msg, want = publication_prepare(data, number, created, author, pred_rows,
                                            [r for r in pub_rows if r.get("issue_number") != number])
        except Exception as e:  # noqa: BLE001
            msg, want = str(e).splitlines()[0], None
        have = [{k: v for k, v in r.items() if k not in SYSTEM_FIELDS} for r in old]
        if msg or want is None or [want] != have:
            return reject("sổ đã có bằng chứng công bố mang số Issue này nhưng nội dung không khớp thân Issue lúc mở")
        attest = "publications PBN-%s %s" % (number, old[0].get("hash"))
        print(json.dumps({"ok": True, "duplicate": True, "kind": "publication", "attest": [attest],
                          "message": "Bằng chứng công bố #%s đã có, bỏ qua" % number}, ensure_ascii=False))
        return 3
    try:
        msg, row = publication_prepare(data, number, created, author, pred_rows, pub_rows)
    except (TypeError, ValueError) as e:
        return reject(f"không đọc được mốc thời gian ({str(e).splitlines()[0]})")
    if msg:
        return reject(msg)
    rows = chain([row], pub_rows[-1]["hash"] if pub_rows else "GENESIS")
    res_rows = load_rows(RES)
    try:
        broken = post_write_errors(pred_rows, res_rows, pred_rows, res_rows, pub_rows, pub_rows + [strict_loads(dumps(r)) for r in rows])
    except Exception as e:  # noqa: BLE001
        broken = [f"không chạy được kiểm lại ({str(e).splitlines()[0]})"]
    if broken:
        return system_error("ghi bằng chứng công bố sẽ làm sổ không qua kiểm lại — " + broken[0] + " — nên KHÔNG ghi")
    PUB.parent.mkdir(parents=True, exist_ok=True)
    with PUB.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(dumps(r) + "\n")
    attest = "publications PBN-%s %s" % (number, rows[0]["hash"])
    ids = ", ".join(row["prediction_ids"])
    print(json.dumps({"ok": True, "kind": "publication", "attest": [attest],
                      "message": "Đã ghi bằng chứng công bố cho %s tại %s" % (ids, row["published_at"])},
                     ensure_ascii=False))
    return 0


def calendar_main(data, number, created, author) -> int:
    """Ghim một dòng lịch công bố vào governance/release_calendar.jsonl (chỉ ghi thêm, chuỗi hash, dấu nhận của bot).
    Mốc thời gian là số Issue và giờ tạo Issue do GitHub cấp; không có trường thời gian tự khai."""
    from tools.ledger_intake import (CALENDAR, calendar_attest, calendar_prepare, load_calendar, post_write_errors,
                                     write_deadline_error, now_utc)
    cal_rows = load_calendar()
    old = [r for r in cal_rows if r.get("issue_number") == number]
    if old:
        try:
            msg, want = calendar_prepare(data, number, created, author, [r for r in cal_rows if r.get("issue_number") != number])
        except Exception as e:  # noqa: BLE001
            msg, want = str(e).splitlines()[0], None
        have = [{k: v for k, v in r.items() if k not in SYSTEM_FIELDS} for r in old]
        if msg or want is None or [want] != have:
            return reject("lịch công bố đã có dòng mang số Issue này nhưng nội dung không khớp thân Issue lúc mở")
        print(json.dumps({"ok": True, "duplicate": True, "kind": "calendar", "attest": [calendar_attest(old[0])],
                          "message": "Lịch %s đã ghim, bỏ qua" % old[0].get("calendar_id")}, ensure_ascii=False))
        return 3
    try:
        msg, row = calendar_prepare(data, number, created, author, cal_rows)
    except (TypeError, ValueError) as e:
        return reject(f"không đọc được mốc thời gian ({str(e).splitlines()[0]})")
    if msg:
        return reject(msg)
    late = write_deadline_error(created, now_utc())      # dấu nhận phải đăng trong 6 giờ sau khi Issue lịch mở
    if late:
        return reject(late)
    rows = chain([row], cal_rows[-1]["hash"] if cal_rows else "GENESIS")
    pred_rows, res_rows = load_rows(PRED), load_rows(RES)
    after = cal_rows + [strict_loads(dumps(r)) for r in rows]
    try:
        broken = post_write_errors(pred_rows, res_rows, pred_rows, res_rows, cal_before=cal_rows, cal_after=after)
    except Exception as e:  # noqa: BLE001
        broken = [f"không chạy được kiểm lại ({str(e).splitlines()[0]})"]
    if broken:
        return system_error_cal("ghim lịch sẽ làm sổ không qua kiểm lại — " + broken[0] + " — nên KHÔNG ghi")
    CALENDAR.parent.mkdir(parents=True, exist_ok=True)
    with CALENDAR.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(dumps(r) + "\n")
    print(json.dumps({"ok": True, "kind": "calendar", "attest": [calendar_attest(rows[0])],
                      "message": "Đã ghim lịch %s: info_lock_at %s (%s)" % (row["calendar_id"], row["info_lock_at"],
                                                                         ", ".join(row["domains"]))}, ensure_ascii=False))
    return 0


def system_error_cal(msg) -> int:
    print(json.dumps({"ok": False, "message": f"Lỗi hệ thống: {msg}"}, ensure_ascii=False))
    return 1


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
        import jsonschema  # noqa: F401
    except ImportError:
        print(json.dumps({"ok": False, "message": "Lỗi hệ thống: thiếu thư viện jsonschema"}, ensure_ascii=False))
        return 1
    res_rows, pred_rows = load_rows(RES), load_rows(PRED)
    if str(data.get("notice", "")).strip().upper() == "PUBLICATION":
        return publication_main(data, number, created, author, pred_rows)
    if str(data.get("notice", "")).strip().upper() == "CALENDAR":
        return calendar_main(data, number, created, author)
    old = [r for r in res_rows if r.get("resolution_issue") == number]
    if old:
        # Chạy lại job: không ghi trùng, và trả lại dấu nhận để workflow đăng nếu lần trước chưa đăng được — nhưng CHỈ khi các
        # dòng đang có trong sổ đúng là kết quả của luật phân định trên thân Issue lúc mở (job chạy lại nhận đúng thân Issue
        # của sự kiện gốc). Dòng mang số Issue này mà nội dung khác (ghi tay rồi chạy lại job để xin dấu nhận) không được cấp.
        first = next(i for i, r in enumerate(res_rows) if r.get("resolution_issue") == number)
        try:
            msg, want, _ = decide(data, number, created, author, pred_rows, res_rows[:first])
        except Exception as e:  # noqa: BLE001
            msg, want = str(e).splitlines()[0], []
        if msg or [strict_loads(dumps(w)) for w in want] != [{k: v for k, v in r.items() if k not in SYSTEM_FIELDS} for r in old]:
            return reject(f"sổ đã có dòng mang số Issue #{number} nhưng nội dung KHÔNG khớp kết quả của luật phân định trên thân "
                          "Issue lúc mở. Robot chỉ cấp dấu nhận cho dòng do chính nó ghi từ thân Issue")
        try:                            # và việc có các dòng đó trong sổ phải qua đúng phép tự kiểm của đường ghi
            broken = post_write_errors(pred_rows, [r for r in res_rows if r.get("resolution_issue") != number], pred_rows, res_rows)
        except Exception as e:  # noqa: BLE001
            broken = [f"không chạy được kiểm lại ({str(e).splitlines()[0]})"]
        if broken:
            return reject(f"sổ đã có dòng mang số Issue #{number}, nhưng các dòng đó không qua luật phân định — {broken[0]} — nên "
                          "robot không cấp dấu nhận")
        print(json.dumps({"ok": True, "duplicate": True, "attest": [attest(r) for r in old],
                          "message": f"Phân định #{number} đã có trong Ledger, bỏ qua"}, ensure_ascii=False))
        return 3
    try:
        msg, rows, note = decide(data, number, created, author, pred_rows, res_rows)
    except (TypeError, ValueError) as e:
        return reject(f"không đọc được mốc thời gian ({str(e).splitlines()[0]})")
    if msg:
        return reject(msg)
    rows = chain(rows, res_rows[-1]["hash"] if res_rows else "GENESIS")
    try:                                # tự kiểm: trạng thái sổ sau khi ghi các dòng này phải qua đúng luật mà validate.py chạy
        broken = post_write_errors(pred_rows, res_rows, pred_rows, res_rows + [strict_loads(dumps(r)) for r in rows])
    except Exception as e:  # noqa: BLE001
        broken = [f"không chạy được kiểm lại ({str(e).splitlines()[0]})"]
    if broken:
        return system_error(f"ghi phân định #{number} sẽ làm sổ không qua kiểm lại luật — {broken[0]} — nên KHÔNG ghi. Đây là "
                            "lỗi của máy (luật lúc ghi lệch luật kiểm lại), báo cho người giữ mã; sổ không bị đụng tới")
    RES.parent.mkdir(parents=True, exist_ok=True)
    with RES.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(dumps(r) + "\n")
    print(json.dumps({"ok": True, "attest": [attest(r) for r in rows], "message": note}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
