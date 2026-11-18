"""Kiểm toán sổ ngoài hash chuỗi (ADR-0003; L-05, L-06, L-10). Hash chuỗi chỉ bắt sửa nhầm: ai ghi được vào kho cũng tính lại
được hash, và hash đúng chỉ nói nội dung nhất quán, không nói nội dung ấy có từ LÚC NÀO. Các kiểm tra ở đây neo sổ vào
thứ nằm NGOÀI tệp:

1. CHỈ GHI THÊM — nội dung ledger/predictions.jsonl, ledger/resolutions.jsonl, research/trial_registry.jsonl và các tệp
   paper/*.csv ở commit gốc (--base) phải là tiền tố nguyên từng byte của bản hiện tại. Sửa, xóa hay chèn dòng cũ → lỗi.
   research/trials.csv kiểm theo dòng: mọi kết quả đã có ở commit gốc phải còn nguyên từng ô; tiêu đề chỉ được giữ
   nguyên hoặc đi từ 13 cột gốc lên đúng 17 cột (khuôn của tệp do laws_checks.trials_format_errors kiểm).
1a. KHO GIÁ (ADR-0006, C2) — từ khi config.yaml ở commit gốc có data.store_dir: kho cũ data.store (prices.csv.gz) phải
   giữ nguyên từng byte; mỗi tệp tháng trong data.store_dir ở commit gốc phải còn và là tiền tố nguyên từng byte của bản
   hiện tại (chỉ nối thêm). Tệp tháng mới thì được thêm.
1b. KẾT QUẢ THỬ (L-06) — trong một Pull Request không được thêm kết quả vào research/trials.csv hay thêm dòng vào sổ đăng
   ký: hai tệp đó chỉ do vòng học trên main ghi. Trên main, mỗi commit thêm kết quả phải có dòng đăng ký của kết quả đó
   nằm sẵn ở commit liền trước (đăng ký được đẩy lên main trước khi backtest chạy).
2. ĐỐI CHIẾU ISSUE (--github) — mỗi dòng dự báo/phân định từ Issue phải ứng với một Issue thật của kho: có tồn tại, không
   phải PR, do chủ kho mở, và giờ tạo trùng issue_created_at trong sổ (giờ máy chủ GitHub, không do người ghi tự khai).
3. DẤU NHẬN (--github) — bằng chứng gốc về NỘI DUNG lúc Issue mở. Workflow nhận (chạy khi Issue mở, đọc thân Issue lúc
   mở) đăng một bình luận dưới tên github-actions[bot] chứa "ledger-attest: <sổ> <mã> <hash dòng>". Mỗi dòng của sổ phải
   có một bình luận ✅ như thế trên đúng Issue của nó: do bot đăng, chưa từng bị sửa (updated_at = created_at), đăng
   không trước giờ tạo Issue, chứa đúng hash của dòng; bot không được đăng hash nào khác cho cùng mã. Với DỰ BÁO, dấu
   nhận còn phải đăng trong 6 giờ sau giờ tạo Issue và trước ngày resolve_at. Giờ đăng bình luận do máy chủ GitHub ghi,
   không ai đặt lùi được; hash dòng phủ toàn bộ nội dung và cả chuỗi phía trước. Vì vậy một dự báo viết sau khi biết
   kết quả không thể mượn giờ của một Issue cũ, kể cả khi thân Issue bị sửa cho khớp. Thân Issue về sau có bị sửa cũng
   không ảnh hưởng. Thân Issue chứa chuỗi "ledger-attest" bị workflow nhận từ chối, và bình luận ❌ không bao giờ mang
   dấu nhận. Chạy lại job nhận chỉ trả lại dấu nhận cho dòng đúng là dòng robot dựng từ thân Issue lúc mở.
   - Không có khoảng miễn kiểm: dòng nào thiếu dấu nhận là lỗi, kể cả khi Issue vừa mở. Nhưng robot nhận đẩy commit
     TRƯỚC rồi mới đăng dấu nhận, và hai robot có thể chạy xen kẽ; nên khi thấy một dòng thiếu dấu nhận mà Issue của nó
     còn trong hạn 6 giờ, kiểm toán ĐỌC LẠI bình luận trong một khoảng chờ hữu hạn (mặc định 15 lượt cách nhau 30 giây =
     420 giây — dài hơn toàn bộ chuỗi thử lại của bước đăng dấu nhận ở hai workflow nhận, vốn chờ 20 + 40 + 60 + 80 =
     200 giây) rồi mới kết luận. Hết lượt vẫn thiếu thì vẫn là lỗi; không dòng nào được coi là đạt khi chưa có dấu nhận.
   - Dấu nhận của dòng PHÂN ĐỊNH không có hạn 6 giờ. Lùi giờ một phân định không đổi được gì: thứ tự chấm là thứ tự dòng
     trong sổ, và luật phân định đã buộc Issue phân định mở sau mọi dự báo của câu hỏi, không trước resolve_at. Nhờ vậy
     job phân định hỏng ở bước đăng dấu nhận luôn chạy lại được.
   - Phục hồi cho dự báo (ghi thêm, không sửa sổ): một dự báo CÓ dấu nhận của robot nhưng dấu nhận tới quá hạn (job nhận
     phải chạy lại sau 6 giờ), nếu câu hỏi của nó đã bị hủy bằng một dòng VOID có dấu nhận hợp lệ, thì không còn là lỗi —
     dự báo VOID không bao giờ có điểm. Việc đó được in ra thành ghi chú. Dự báo không có dấu nhận nào của robot thì VOID
     cũng không gỡ được. VOID chỉ ghi được từ resolve_at, nên cho tới lúc đó kiểm toán vẫn đỏ ở dòng ấy.
   - Kiểm toán đọc lại bình luận cho dòng PHÂN ĐỊNH thiếu dấu nhận bất kể Issue mở từ bao giờ (job phân định có thể vừa
     được chạy lại); cho dòng DỰ BÁO thì chỉ khi Issue còn trong hạn 6 giờ.
4. L-10 (--github) — cảnh báo (không chặn) khi nhánh main chưa có luật bảo vệ nào.

Việc từng dòng có đúng LUẬT NHẬN hay không (hợp đồng, L-05, mỗi ghế một dự báo…) do tools/validate.py chạy lại
(laws_checks.check_ledger_rows), không cần GitHub.

Giới hạn nói thẳng: chủ kho có quyền quản trị vẫn viết lại được lịch sử nếu không bật ruleset cấm force-push (mục 4 nhắc
việc đó), và xóa được bình luận dấu nhận — khi đó kiểm toán báo đỏ chứ không im lặng. Người có quyền quản trị cố ý gian
lận vẫn có một đường: tự viết workflow khác để bot đăng trước nhiều dấu nhận trong nhiều bình luận rồi xóa bớt (GitHub
không lưu vết bình luận đã xóa). Máy không chặn được việc này; nó cần chủ ý, nhiều bước, và để lại workflow lạ trong
lịch sử kho.

Chạy ở hai nơi: trong tests.yml (mọi PR và mọi push lên main) và trong ledger_audit.yml — tự chạy SAU mỗi lần workflow
nhận dự báo, nhận phân định hoặc vòng học kết thúc (commit do GITHUB_TOKEN đẩy không kích hoạt sự kiện push, nên phải
gọi qua workflow_run), và mỗi ngày một lần.

Dùng trong CI:  python tools/ledger_audit.py --base "$BASE_SHA" --github
Môi trường: GITHUB_TOKEN, GITHUB_REPOSITORY (owner/repo). Thoát 1 khi có lỗi.
"""
import argparse, csv, io, json, math, os, pathlib, re, subprocess, sys, time, urllib.request
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.laws_checks import ATTEST_WINDOW, TRIAL_HEADERS  # noqa: E402  một định nghĩa cho bên ghi và bên kiểm

APPEND_ONLY = ("ledger/predictions.jsonl", "ledger/resolutions.jsonl", "ledger/publication_evidence.jsonl",
               "research/trial_registry.jsonl",
               "paper/nav.csv", "paper/decisions.csv", "paper/trades.csv",
               "governance/control_b_prompts.jsonl")   # phiên bản prompt ghế B đã có hiệu lực: không sửa, không xóa
TRIALS, REGISTRY = "research/trials.csv", "research/trial_registry.jsonl"
V302_MARKER = "tools/registry_push.py"   # có từ v3.0.2 và thuộc danh sách tệp bắt buộc của validate.py
ZERO_SHA = "0" * 40
BOT = "github-actions[bot]"
# ATTEST_WINDOW (6 giờ, từ laws_checks): dấu nhận phải có trong khoảng đó sau khi Issue mở (bình thường: khoảng 1 phút).
# Khoảng chờ của kiểm toán phải PHỦ HẾT chuỗi thử lại của robot (vòng chấm 10). Bước đăng dấu nhận của hai workflow nhận
# (.github/workflows/ledger_intake.yml, resolution_intake.yml) thử tối đa POST_TRIES lần và chờ POST_BACKOFF giây × số lần đã
# hỏng: 20 + 40 + 60 + 80 = 200 giây từ lần thử đầu tới lần thử cuối. Bản trước chỉ đọc lại trong 150 giây, nên một dấu
# nhận hợp lệ tới ở lần thử thứ năm của robot bị báo đỏ giả. tests/test_governance.py buộc hai bộ số này đi cùng nhau.
POST_TRIES, POST_BACKOFF = 5, 20
POST_SPAN = POST_BACKOFF * sum(range(1, POST_TRIES))                        # 200 giây
ATTEST_MARGIN = 220                                                         # biên: thời gian của các lần gọi API hỏng, độ trễ hiển thị bình luận
ATTEST_WAIT = 30.0                                                          # giây giữa hai lượt đọc bình luận
ATTEST_TRIES = 1 + math.ceil((POST_SPAN + ATTEST_MARGIN) / ATTEST_WAIT)     # 15 lượt đọc: 420 giây từ lượt đầu tới lượt cuối


def append_only_errors(base: dict, head: dict) -> list[str]:
    """base/head: {đường dẫn: bytes hoặc None nếu tệp không tồn tại}."""
    errs = []
    for path in APPEND_ONLY:
        b, h = base.get(path), head.get(path)
        if b is None or b == b"":
            continue
        if h is None:
            errs.append(f"L-05: {path} có ở commit gốc nhưng đã bị xóa"); continue
        if not h.startswith(b):
            n = next((i for i, (x, y) in enumerate(zip(b.splitlines(), h.splitlines()), 1) if x != y),
                     min(len(b.splitlines()), len(h.splitlines())) + 1)
            errs.append(f"L-05: {path} không còn là chỉ-ghi-thêm — dòng {n} của commit gốc đã bị sửa, xóa hoặc chèn")
    return errs


def store_errors(base: dict, head: dict, legacy: str) -> list[str]:
    """ADR-0006 (C2). base/head: {đường dẫn: bytes hoặc None} cho kho cũ `legacy` và mọi tệp tháng có ở commit gốc.
    Gọi khi commit gốc đã ở chế độ ghi tăng dần (config.yaml có data.store_dir)."""
    errs = []
    b, h = base.get(legacy), head.get(legacy)
    if b is not None and h != b:
        errs.append(f"L-05: {legacy} (kho giá cũ) đã {'bị xóa' if h is None else 'bị ghi lại'} — kho cũ đóng băng từ ADR-0006; "
                    "dòng mới chỉ được nối vào tệp tháng")
    for path in sorted(k for k in base if k != legacy):
        b, h = base[path], head.get(path)
        if b is None:
            continue
        if h is None:
            errs.append(f"L-05: {path} (tệp tháng của kho giá) có ở commit gốc nhưng đã bị xóa"); continue
        if not h.startswith(b):
            errs.append(f"L-05: {path} (tệp tháng của kho giá) không còn là chỉ-ghi-thêm — dòng cũ bị sửa, xóa hoặc chèn (ADR-0006)")
    return errs


def store_snapshot_errors(root, base) -> list[str]:
    """Dựng base/head cho store_errors từ git (commit gốc) và cây tệp hiện tại; chỉ kiểm khi commit gốc đã có data.store_dir."""
    import yaml
    def cfg_of(text):
        try:
            c = yaml.safe_load(text or b"")
            return (c.get("data") or {}) if isinstance(c, dict) else {}
        except Exception:  # noqa: BLE001
            return {}
    def show(rev, path):
        r = subprocess.run(["git", "-C", str(root), "show", f"{rev}:{path}"], capture_output=True)
        return r.stdout if r.returncode == 0 else None
    base_data = cfg_of(show(base, "config.yaml"))
    sdir = base_data.get("store_dir")
    if not sdir:
        return []                    # commit gốc còn ở trước ADR-0006: kho cũ còn được vòng học bản cũ ghi lại
    legacy = base_data.get("store") or "data/store/prices.csv.gz"
    ls = subprocess.run(["git", "-C", str(root), "ls-tree", "-r", "--name-only", base, "--", sdir], capture_output=True)
    paths = [legacy] + [x for x in ls.stdout.decode().split("\n") if x.endswith(".csv")]
    base_files = {x: show(base, x) for x in paths}
    head_files = {x: ((pathlib.Path(root) / x).read_bytes() if (pathlib.Path(root) / x).is_file() else None) for x in paths}
    return store_errors(base_files, head_files, legacy)


def issue_crosscheck_errors(pred_rows, res_rows, issues: dict, owner: str, pub_rows=()) -> list[str]:
    """issues: {số: {"created_at": iso, "user": login, "is_pr": bool}} lấy từ GitHub."""
    errs = []
    def check(label, number, created):
        it = issues.get(number)
        if it is None:
            errs.append(f"L-05: {label} trỏ tới Issue #{number} không tồn tại trên GitHub"); return
        if it.get("is_pr"):
            errs.append(f"L-05: {label} trỏ tới #{number} là Pull Request, không phải Issue")
        if (it.get("user") or "").lower() != (owner or "").lower():
            errs.append(f"L-05: {label} — Issue #{number} do '{it.get('user')}' mở, không phải chủ kho '{owner}'")
        if it.get("created_at") != created:
            errs.append(f"L-05: {label} ghi giờ tạo {created} nhưng GitHub ghi Issue #{number} tạo lúc {it.get('created_at')}")
    for r in pred_rows:
        if "issue_number" in r:
            check(f"dự báo {r.get('id')}", r.get("issue_number"), r.get("issue_created_at"))
    seen = set()
    for r in res_rows:
        n = r.get("resolution_issue")
        if n is not None and n not in seen:
            seen.add(n)
            check(f"phân định {r.get('prediction_id')}", n, r.get("resolution_issue_created_at"))
    for r in pub_rows or ():
        n = r.get("issue_number")
        if n is not None and n not in seen:
            seen.add(n)
            check(f"bằng chứng công bố {r.get('prediction_ids')}", n, r.get("issue_created_at"))
    return errs


def _ts(iso):
    return datetime.fromisoformat(str(iso).replace("Z", "+00:00"))


_MARK_RE = re.compile(r"ledger-attest:\s*(predictions|resolutions|publications)\s+(\S+)\s+([0-9a-f]{64})(?![0-9a-f])")
VN = timezone(timedelta(hours=7))


def _forecast_attest_bound(row):
    """Mốc dấu nhận phải đứng trước: info_lock_at nếu sớm hơn resolve_at, không thì resolve_at."""
    resolve_at = str(row.get("resolve_at") or "")
    lock = str(row.get("info_lock_at") or "")
    if lock and (not resolve_at or lock < resolve_at):
        return lock, "info_lock_at"
    return (resolve_at or None), "resolve_at"


def attestation_failures(pred_rows, res_rows, issues: dict, comments: dict, notes=None, pub_rows=()) -> list:
    """comments: {số Issue: [{"user": login, "created_at": iso, "updated_at": iso, "body": str}]}.
    Trả về [(số Issue, lỗi, "predictions" | "resolutions")]; KHÔNG có khoảng miễn kiểm cho Issue vừa mở. Một dòng đạt khi Issue của nó có bình luận ✅
    của github-actions[bot], chưa sửa, đăng không trước giờ tạo Issue, chứa 'ledger-attest: <sổ> <mã> <hash>' đúng hash
    của dòng — và mọi bình luận của bot trên Issue đó không nêu hash nào KHÁC cho cùng mã (không ai "đặt trước" hai nội
    dung rồi chọn một). Riêng DỰ BÁO: dấu nhận còn phải đăng trong ATTEST_WINDOW sau giờ tạo Issue và trước ngày resolve_at
    (giờ Việt Nam) — đó là thứ chặn một dự báo viết sau mà mượn giờ Issue cũ.
    Phục hồi (ghi thêm, không sửa sổ): một dự báo CÓ dấu nhận của robot nhưng dấu nhận ấy tới quá hạn (job nhận phải chạy
    lại muộn), nếu câu hỏi của nó đã bị hủy bằng một dòng VOID có dấu nhận hợp lệ, thì không còn là lỗi — dự báo VOID không
    bao giờ có điểm, và trong phép kiểm định A–B nó bị tính theo hướng bất lợi cho kết luận đang xét. Việc đó được ghi vào
    `notes` để in ra. Dự báo không có dấu nhận nào của robot thì VOID cũng không gỡ được. (VOID chỉ ghi được từ resolve_at,
    nên cho tới lúc đó dòng ấy vẫn là lỗi.)"""
    def find(number, ledger, rid, rhash, before_day=None, window=ATTEST_WINDOW, before_label="resolve_at"):
        """→ (True, "") khi có dấu nhận hợp lệ; (False, lý do) khi không; (None, "") khi Issue không có trên GitHub
        (issue_crosscheck_errors đã báo)."""
        it = issues.get(number)
        if it is None:
            return None, ""
        try:
            opened = _ts(it.get("created_at"))
        except ValueError:
            return False, f"không đọc được giờ tạo Issue #{number}"
        why, ok, other = "không có bình luận dấu nhận nào chứa hash của dòng", False, set()
        for c in comments.get(number, []):
            marks = {m[2] for m in _MARK_RE.findall(c.get("body") or "") if m[0] == ledger and m[1] == str(rid)}
            if (c.get("user") or "") == BOT:
                other |= marks - {rhash}
            if rhash not in marks:
                continue
            if (c.get("user") or "") != BOT:
                why = f"dấu nhận do '{c.get('user')}' đăng, không phải {BOT}"; continue
            if c.get("created_at") != c.get("updated_at"):
                why = "bình luận dấu nhận đã bị sửa sau khi đăng"; continue
            if not (c.get("body") or "").lstrip().startswith("✅"):
                why = "dấu nhận nằm trong bình luận không phải thông báo ✅ của workflow nhận"; continue
            try:
                posted = _ts(c.get("created_at"))
            except ValueError:
                why = "không đọc được giờ đăng dấu nhận"; continue
            if posted < opened:
                why = f"dấu nhận đăng lúc {c.get('created_at')}, trước cả giờ tạo Issue {it.get('created_at')}"; continue
            if window is not None and posted - opened > window:
                why = (f"dấu nhận đăng lúc {c.get('created_at')}, cách giờ tạo Issue {it.get('created_at')} quá "
                       f"{int(window.total_seconds() // 3600)} giờ"); continue
            if before_day and posted.astimezone(VN).date().isoformat() >= str(before_day):
                why = f"dấu nhận đăng lúc {c.get('created_at')}, không trước ngày {before_label} {before_day} (giờ Việt Nam)"; continue
            ok = True
        if ok and other:
            ok, why = False, f"robot còn đăng dấu nhận với hash khác cho cùng mã {rid} — không xác định được nội dung nào có trước"
        return ok, ("" if ok else why)

    def error(label, number, why, how):
        return (number, f"L-05: {label} — Issue #{number}: {why}. Dòng này không có bằng chứng là nội dung do robot ghi từ thân "
                        f"Issue (dòng ghi vòng qua workflow nhận, hoặc dấu nhận bị xóa/sửa, hoặc bước đăng dấu nhận bị hỏng — "
                        f"khi đó {how})")

    res_errs, voided = [], {}
    for r in res_rows:                      # phân định trước: cần biết câu hỏi nào đã bị hủy bằng dòng VOID có dấu nhận hợp lệ
        n = r.get("resolution_issue")
        if n is None:
            continue
        ok, why = find(n, "resolutions", r.get("prediction_id"), r.get("hash"), window=None)
        if ok is False:
            res_errs.append(error(f"phân định {r.get('prediction_id')}", n, why, "chạy lại job phân định của Issue này (lúc nào cũng được)")
                            + ("resolutions",))
        elif ok and "outcome" in r and r["outcome"] is None:
            voided[r.get("prediction_id")] = n
    pred_errs = []
    for r in pred_rows:
        if "issue_number" not in r:
            continue
        n, rid = r.get("issue_number"), r.get("id")
        before, label = _forecast_attest_bound(r)
        ok, why = find(n, "predictions", rid, r.get("hash"), before, before_label=label)
        if ok is not False:
            continue
        if rid in voided and find(n, "predictions", rid, r.get("hash"), None, None)[0]:
            if notes is not None:
                notes.append(f"dự báo {rid} (Issue #{n}): dấu nhận của robot tới quá hạn ({why}), nhưng câu hỏi đã bị hủy bằng VOID ở "
                             f"phân định Issue #{voided[rid]} có dấu nhận — dự báo này không được chấm, không tính là lỗi")
            continue
        pred_errs.append(error(f"dự báo {rid}", n, why,
                               "chạy lại job nhận của Issue này trong vòng 6 giờ kể từ lúc Issue mở; đã quá hạn thì vẫn chạy lại job "
                               "để robot đăng dấu nhận muộn, và khi tới resolve_at thì hủy câu hỏi của dòng này bằng Issue Resolution "
                               "chọn VOID") + ("predictions",))
    pub_errs = []
    for r in pub_rows or ():
        n = r.get("issue_number")
        ok, why = find(n, "publications", f"PBN-{n}", r.get("hash"), window=ATTEST_WINDOW)
        if ok is False:
            pub_errs.append(error(f"bằng chứng công bố PBN-{n}", n, why,
                                  "chạy lại job của Issue bằng chứng trong vòng 6 giờ kể từ lúc Issue mở") + ("publications",))
    return pred_errs + res_errs + pub_errs


def attestation_errors(pred_rows, res_rows, issues: dict, comments: dict, pub_rows=()) -> list[str]:
    """Danh sách lỗi dấu nhận (xem attestation_failures) với MỘT lượt đọc bình luận."""
    return [f[1] for f in attestation_failures(pred_rows, res_rows, issues, comments, pub_rows=pub_rows)]


def attestation_errors_with_retry(pred_rows, res_rows, issues: dict, fetch, tries=ATTEST_TRIES, wait=ATTEST_WAIT,
                                  sleep=time.sleep, now=None, pub_rows=()) -> list[str]:
    """Như attestation_errors, nhưng ĐỌC LẠI bình luận khi còn dòng thiếu dấu nhận mà dấu nhận vẫn có thể tới đúng hạn.
    Lý do: robot nhận đẩy commit trước rồi mới đăng bình luận ✅; kiểm toán chạy sau khi MỘT robot xong nhưng đọc cả main,
    nên có thể thấy dòng của robot KHÁC vừa đẩy mà chưa kịp đăng dấu nhận. fetch(): hàm trả về {số Issue: [bình luận]}.
    - Chỉ đọc lại khi còn ít nhất một dòng lỗi mà dấu nhận VẪN CÓ THỂ tới hợp lệ: dòng phân định thì lúc nào cũng có thể
      (dấu nhận phân định không có hạn 6 giờ — job phân định của một Issue mở từ hôm trước có thể vừa được chạy lại); dòng
      dự báo thì chỉ khi Issue mở chưa quá ATTEST_WINDOW (quá hạn đó dấu nhận có tới cũng không hợp lệ, chờ là vô ích).
    - Tối đa `tries` lượt đọc, cách nhau `wait` giây. Hết lượt mà vẫn thiếu → trả về lỗi như thường: đây không phải
      khoảng miễn kiểm, không dòng nào được coi là đạt khi chưa có dấu nhận."""
    now = now or datetime.now(timezone.utc)
    due = {}
    for r in pred_rows:
        if "issue_number" in r:
            before, _ = _forecast_attest_bound(r)
            due[r.get("issue_number")] = str(before or "")
    def fresh(number):
        """Dự báo: dấu nhận còn có thể tới đúng hạn — Issue mở chưa quá ATTEST_WINDOW và chưa sang ngày resolve_at."""
        try:
            in_window = now - _ts((issues.get(number) or {}).get("created_at")) <= ATTEST_WINDOW
        except (TypeError, ValueError):
            return False
        return in_window and (not due.get(number) or now.astimezone(VN).date().isoformat() < due[number])
    def may_still_arrive(f):
        return f[2] == "resolutions" or fresh(f[0])
    notes = []
    fails = attestation_failures(pred_rows, res_rows, issues, fetch(), notes, pub_rows=pub_rows)
    for _ in range(max(1, int(tries)) - 1):
        if not any(may_still_arrive(f) for f in fails):
            break
        print(f"(còn {len(fails)} dòng chưa thấy dấu nhận mà dấu nhận vẫn có thể tới: chờ {wait:g} giây rồi đọc lại bình luận)")
        sleep(wait)
        notes = []
        fails = attestation_failures(pred_rows, res_rows, issues, fetch(), notes, pub_rows=pub_rows)
    for n in notes:
        print("::notice::" + n)
    return [f[1] for f in fails]


def _trials(data):
    """bytes của trials.csv → (tiêu đề, danh sách dict), giữ nguyên chuỗi từng ô."""
    rows = list(csv.reader(io.StringIO((data or b"").decode("utf-8", "replace"))))
    if not rows:
        return [], []
    return rows[0], [dict(zip(rows[0], r)) for r in rows[1:] if r]


def _reg_ids(data) -> set:
    out = set()
    for line in (data or b"").decode("utf-8", "replace").splitlines():
        if line.strip():
            try:
                out.add(json.loads(line).get("trial_id"))
            except ValueError:
                pass
    return out


def trials_rows_errors(base_trials, head_trials) -> list[str]:
    """Mọi kết quả thử đã có ở commit gốc phải còn nguyên từng ô, đúng thứ tự (so theo tên cột của commit gốc), và TIÊU ĐỀ
    chỉ được giữ nguyên hoặc đi từ 13 cột gốc lên đúng 17 cột (lần ghi đầu của v3.0.2). Thêm cột lạ, đổi tên, đổi chỗ hay
    bớt cột — dù mọi ô cũ còn nguyên — làm lần ghi kế tiếp của vòng học hỏng, nên là lỗi."""
    bh, br = _trials(base_trials)
    hh, hr = _trials(head_trials)
    if bh and hh != bh and not (bh == TRIAL_HEADERS[0] and hh == TRIAL_HEADERS[1]):
        return [f"L-06: tiêu đề {TRIALS} bị đổi so với commit gốc ({len(bh)} cột → {len(hh)} cột) — chỉ được giữ nguyên, hoặc từ "
                "13 cột gốc lên đúng 17 cột do vòng học ghi"]
    for i, row in enumerate(br):
        if i >= len(hr):
            return [f"L-06: {TRIALS} mất kết quả {row.get('trial_id')} (và các dòng sau) so với commit gốc"]
        if any(hr[i].get(c, "") != row.get(c, "") for c in bh):
            return [f"L-06: {TRIALS} — kết quả {row.get('trial_id')} đã bị sửa so với commit gốc (kết quả thử chỉ được ghi thêm)"]
    return []


def trials_history_errors(root, base, pull_request=False) -> list[str]:
    """L-06, cần git. base: commit gốc. Trả về lỗi về việc THÊM kết quả thử:
    - Pull Request: không được thêm kết quả, không được thêm dòng đăng ký (hai tệp chỉ do vòng học trên main ghi).
    - Trên main: với mỗi commit trong (base, HEAD] có thêm kết quả, dòng đăng ký của từng kết quả mới phải có sẵn trong sổ
      ở commit liền trước nó. Chỉ bỏ qua commit của kho TRƯỚC v3.0.2 — vòng học bản cũ, kết quả của nó do ghim trong
      config.yaml và dòng neo lịch sử chốt. "Trước v3.0.2":
      * kho có mốc cố định research.v302_boundary (ADR-0004; kho thật): commit nằm trong lịch sử của mốc đó. Mốc không đổi
        được: khác giá trị ở commit gốc (hoặc bị xóa) là lỗi ở cả chế độ PR lẫn main, và lượt kiểm vẫn dùng mốc của
        commit gốc; commit mốc không có trong kho là lỗi (đóng khi không chắc).
      * kho chưa khai mốc (kho giả lập trong test): tools/registry_push.py chưa từng xuất hiện trong lịch sử của commit đó
        VÀ commit gốc của lượt kiểm cũng còn ở trước v3.0.2.
      Từ v3.0.2 trở đi không commit nào được miễn, kể cả khi tệp mốc tạm thời bị xóa."""
    def git(*a):
        return subprocess.run(["git", "-C", str(root), *a], capture_output=True)
    def show(rev, path):
        r = git("show", f"{rev}:{path}")
        return r.stdout if r.returncode == 0 else None
    def ever_had_marker(rev):
        """Tệp mốc v3.0.2 đã TỪNG có trong lịch sử của commit này (kể cả khi về sau bị xóa)."""
        return bool(git("log", "--full-history", "-1", "--format=%H", rev, "--", V302_MARKER).stdout.strip())
    errs = trials_rows_errors(show(base, TRIALS), show("HEAD", TRIALS))
    if pull_request:
        # Cái PR tự thêm = commit gộp so với ĐẦU NHÁNH ĐÍCH lúc gộp (cha thứ nhất của commit gộp mà GitHub dựng cho PR).
        # Không so với base.sha của sự kiện: giá trị đó có thể cũ, khi ấy kết quả do vòng học ghi lên main sau lúc mở PR
        # sẽ bị tính nhầm là của PR — và mốc v3.0.2 mà main đã có sau lúc mở PR sẽ không được so (tự rà v3.0.3).
        parents = git("rev-list", "--parents", "-n", "1", "HEAD").stdout.decode().split()
        if len(parents) == 3:
            base = parents[1]
        else:
            mb = git("merge-base", base, "HEAD").stdout.decode().strip()
            base = mb or base
    # Mốc v3.0.2 cố định (ADR-0004), kiểm ở cả chế độ PR lẫn main: mốc đã có ở commit gốc thì không được đổi, không được xóa.
    # Lượt kiểm này vẫn dùng mốc CỦA COMMIT GỐC, nên đổi mốc không miễn được commit nào trong khoảng đang kiểm.
    from tools.laws_checks import v302_boundary, _SHA40_RE
    try:
        boundary = v302_boundary(root)
    except ValueError as e:
        return errs + [f"L-06: {e}"]
    try:
        import yaml
        base_cfg = yaml.safe_load(show(base, "config.yaml") or b"")
        base_boundary = (base_cfg.get("research") or {}).get("v302_boundary") if isinstance(base_cfg, dict) else None
    except Exception:  # noqa: BLE001
        base_boundary = None
    if isinstance(base_boundary, str) and _SHA40_RE.fullmatch(base_boundary) and base_boundary != boundary:
        errs.append("L-06: research.v302_boundary trong config.yaml khác giá trị ở commit gốc (hoặc bị xóa) — mốc v3.0.2 không "
                    "được đổi (ADR-0004)")
        boundary = base_boundary
    if boundary is not None:
        if git("cat-file", "-e", f"{boundary}^{{commit}}").returncode != 0:
            return errs + [f"L-06: không tìm thấy commit mốc v3.0.2 {boundary[:7]} trong kho (cần lịch sử đầy đủ: fetch-depth 0)"]
    if pull_request:
        nb, nh = len(_trials(show(base, TRIALS))[1]), len(_trials(show("HEAD", TRIALS))[1])
        if nh > nb:
            errs.append(f"L-06: Pull Request thêm {nh - nb} kết quả vào {TRIALS} — kết quả thử chỉ do vòng học trên main ghi, "
                        "sau khi đăng ký đã nằm trên main")
        extra = _reg_ids(show("HEAD", REGISTRY)) - _reg_ids(show(base, REGISTRY))
        if extra:
            errs.append(f"L-06: Pull Request thêm dòng vào sổ đăng ký thử ({', '.join(sorted(map(str, extra)))}) — sổ chỉ do vòng "
                        "học trên main ghi, trước khi chạy backtest")
        return errs
    # Mốc v3.0.2 xác định bằng TỔ TIÊN, không bằng việc tệp mốc đang có mặt hay không (vòng chấm 9: xóa tệp mốc ở một commit
    # rồi ghi kết quả ở commit sau, rồi trả tệp lại, là qua được phép kiểm "vắng ở commit và commit cha"):
    # - commit gốc của lượt kiểm đã thuộc v3.0.2 (tệp mốc từng có trong lịch sử của nó) → KHÔNG commit nào trong khoảng được
    #   miễn, kể cả commit nằm trên một nhánh tách ra từ lịch sử cũ rồi gộp vào sau;
    # - commit gốc còn ở trước v3.0.2 (khoảng kiểm vắt qua lúc gộp) → chỉ miễn commit mà lịch sử của nó chưa từng có tệp mốc.
    def pre_v302(c):
        if boundary is not None:
            return git("merge-base", "--is-ancestor", c, boundary).returncode == 0
        return not base_is_v302 and not ever_had_marker(c)
    base_is_v302 = boundary is None and ever_had_marker(base)
    commits = git("rev-list", "--reverse", f"{base}..HEAD", "--", TRIALS).stdout.decode().split()
    for c in commits:
        parent = git("rev-parse", "--verify", "-q", f"{c}^").stdout.decode().strip()
        if not parent:
            continue
        if pre_v302(c):
            continue          # vòng học bản cũ (trước v3.0.2, chưa có sổ đăng ký): kết quả đó do ghim và dòng neo chốt
        before, after = _trials(show(parent, TRIALS))[1], _trials(show(c, TRIALS))[1]
        new = [t.get("trial_id") for t in after[len(before):]]
        if not new:
            continue
        have = _reg_ids(show(parent, REGISTRY))
        missing = [t for t in new if t not in have]
        if missing:
            errs.append(f"L-06: commit {c[:7]} ghi kết quả {', '.join(map(str, missing))} khi sổ đăng ký ở commit liền trước chưa có "
                        "các mã đó — kết quả chỉ được ghi sau khi đăng ký đã nằm trên main")
    return errs


def _no_constant(name):
    raise ValueError(name)


def _rows(path):
    p = ROOT / path
    return ([json.loads(l, parse_constant=_no_constant) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
            if p.is_file() else [])


def _git_show(sha, path):
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"{sha}:{path}"], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def _api(url, token):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "ttc-ledger-audit",
                                               **({"Authorization": f"Bearer {token}"} if token else {})})
    with urllib.request.urlopen(req, timeout=30) as f:
        return json.loads(f.read().decode("utf-8"))


def fetch_issues(repo, token) -> dict:
    out, page = {}, 1
    while True:
        batch = _api(f"https://api.github.com/repos/{repo}/issues?state=all&per_page=100&page={page}", token)
        if not batch:
            return out
        for it in batch:
            out[it["number"]] = {"created_at": it.get("created_at"), "user": (it.get("user") or {}).get("login"),
                                 "is_pr": "pull_request" in it}
        page += 1


def fetch_comments(repo, token) -> dict:
    """Mọi bình luận Issue của kho, gom theo số Issue (một lượt phân trang, không gọi riêng từng Issue)."""
    out, page = {}, 1
    while True:
        batch = _api(f"https://api.github.com/repos/{repo}/issues/comments?sort=created&direction=asc&per_page=100&page={page}", token)
        if not batch:
            return out
        for c in batch:
            try:
                n = int(str(c.get("issue_url", "")).rsplit("/", 1)[-1])
            except ValueError:
                continue
            out.setdefault(n, []).append({"user": (c.get("user") or {}).get("login"), "created_at": c.get("created_at"),
                                          "updated_at": c.get("updated_at"), "body": c.get("body")})
        page += 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="")
    ap.add_argument("--github", action="store_true")
    ap.add_argument("--attest-tries", type=int, default=ATTEST_TRIES, help="số lượt đọc bình luận dấu nhận (>=1)")
    ap.add_argument("--attest-wait", type=float, default=ATTEST_WAIT, help="giây chờ giữa hai lượt đọc")
    a = ap.parse_args()
    errs = []
    base = (a.base or "").strip()
    if base and base != ZERO_SHA:
        if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{base}^{{commit}}"], capture_output=True).returncode != 0:
            errs.append(f"L-05: không đọc được commit gốc {base[:12]} để kiểm chỉ-ghi-thêm (lịch sử bị viết lại, hoặc checkout thiếu lịch sử)")
        else:
            head = {p: ((ROOT / p).read_bytes() if (ROOT / p).is_file() else None) for p in APPEND_ONLY}
            errs += append_only_errors({p: _git_show(base, p) for p in APPEND_ONLY}, head)
            errs += store_snapshot_errors(ROOT, base)
            errs += trials_history_errors(ROOT, base, pull_request=os.environ.get("GITHUB_EVENT_NAME", "").startswith("pull_request"))
    else:
        print("(bỏ qua kiểm chỉ-ghi-thêm: không có commit gốc)")
    if a.github:
        repo, token = os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_TOKEN", "")
        pred, res = _rows("ledger/predictions.jsonl"), _rows("ledger/resolutions.jsonl")
        pub = _rows("ledger/publication_evidence.jsonl")
        need = any("issue_number" in r for r in pred) or any(r.get("resolution_issue") is not None for r in res) or bool(pub)
        if not repo:
            print("(bỏ qua đối chiếu Issue: không có GITHUB_REPOSITORY)")
        else:
            try:
                if need:
                    issues = fetch_issues(repo, token)
                    errs += issue_crosscheck_errors(pred, res, issues, repo.split("/")[0], pub)
                    errs += attestation_errors_with_retry(pred, res, issues, lambda: fetch_comments(repo, token),
                                                          tries=a.attest_tries, wait=a.attest_wait, pub_rows=pub)
                br = _api(f"https://api.github.com/repos/{repo}/branches/main", token)
                rules = _api(f"https://api.github.com/repos/{repo}/rules/branches/main", token)
                if not br.get("protected") and not rules:
                    print("::warning::L-10: nhánh main chưa có luật bảo vệ nào. Bật ruleset 'cấm force-push' và 'cấm xóa nhánh' "
                          "(Settings → Rules) để lịch sử sổ không viết lại được; hai luật này không chặn vòng học và việc ghi dự báo tự động.")
            except Exception as e:  # noqa: BLE001
                if need:
                    errs.append(f"L-05: không gọi được GitHub API để đối chiếu Issue ({str(e).splitlines()[0]})")
                else:
                    print(f"(không gọi được GitHub API: {str(e).splitlines()[0]})")
    for e in errs:
        print("LỖI: " + e)
    print("OK — sổ chỉ-ghi-thêm, khớp Issue thật và có dấu nhận" if not errs else f"{len(errs)} lỗi")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
