"""Kiểm toán sổ ngoài hash chuỗi (ADR-0003; L-05, L-06, L-10). Hash chuỗi chỉ bắt sửa nhầm: ai ghi được vào kho cũng tính lại
được hash, và hash đúng chỉ nói nội dung nhất quán, không nói nội dung ấy có từ LÚC NÀO. Các kiểm tra ở đây neo sổ vào
thứ nằm NGOÀI tệp:

1. CHỈ GHI THÊM — nội dung ledger/predictions.jsonl, ledger/resolutions.jsonl, research/trial_registry.jsonl và các tệp
   paper/*.csv ở commit gốc (--base) phải là tiền tố nguyên từng byte của bản hiện tại. Sửa, xóa hay chèn dòng cũ → lỗi.
   research/trials.csv kiểm theo dòng: mọi kết quả đã có ở commit gốc phải còn nguyên từng ô.
1b. KẾT QUẢ THỬ (L-06) — trong một Pull Request không được thêm kết quả vào research/trials.csv hay thêm dòng vào sổ đăng
   ký: hai tệp đó chỉ do vòng học trên main ghi. Trên main, mỗi commit thêm kết quả phải có dòng đăng ký của kết quả đó
   nằm sẵn ở commit liền trước (đăng ký được đẩy lên main trước khi backtest chạy).
2. ĐỐI CHIẾU ISSUE (--github) — mỗi dòng dự báo/phân định từ Issue phải ứng với một Issue thật của kho: có tồn tại, không
   phải PR, do chủ kho mở, và giờ tạo trùng issue_created_at trong sổ (giờ máy chủ GitHub, không do người ghi tự khai).
3. DẤU NHẬN (--github) — không có khoảng miễn kiểm: dòng nào thiếu dấu nhận là lỗi, kể cả khi Issue vừa mở. Bằng chứng
   gốc về NỘI DUNG lúc Issue mở: workflow nhận (chạy khi Issue mở, đọc thân Issue lúc mở)
   đăng một bình luận dưới tên github-actions[bot] chứa "ledger-attest: <sổ> <mã> <hash dòng>". Mỗi dòng Issue trong sổ
   phải có một bình luận ✅ như thế trên đúng Issue của nó: do bot đăng, chưa từng bị sửa (updated_at = created_at), đăng
   trong vòng 6 giờ sau giờ tạo Issue và (với dự báo) trước ngày resolve_at, chứa đúng hash của dòng; bot không được
   đăng hash nào khác cho cùng mã. Giờ đăng bình luận do máy chủ GitHub ghi, không ai đặt lùi được; hash dòng phủ toàn
   bộ nội dung và cả chuỗi phía trước. Vì vậy một dòng viết sau khi biết kết quả không thể mượn giờ của một Issue cũ,
   kể cả khi thân Issue bị sửa cho khớp. Thân Issue về sau có bị sửa cũng không ảnh hưởng. Thân Issue chứa chuỗi
   "ledger-attest" bị workflow nhận từ chối, và bình luận ❌ không bao giờ mang dấu nhận.
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
import argparse, csv, io, json, os, pathlib, re, subprocess, sys, urllib.request
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
APPEND_ONLY = ("ledger/predictions.jsonl", "ledger/resolutions.jsonl", "research/trial_registry.jsonl",
               "paper/nav.csv", "paper/decisions.csv", "paper/trades.csv")
TRIALS, REGISTRY = "research/trials.csv", "research/trial_registry.jsonl"
V302_MARKER = "tools/registry_push.py"   # có từ v3.0.2 và thuộc danh sách tệp bắt buộc của validate.py
ZERO_SHA = "0" * 40
BOT = "github-actions[bot]"
ATTEST_WINDOW = timedelta(hours=6)       # dấu nhận phải có trong 6 giờ sau khi Issue mở (bình thường: khoảng 1 phút)


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


def issue_crosscheck_errors(pred_rows, res_rows, issues: dict, owner: str) -> list[str]:
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
    return errs


def _ts(iso):
    return datetime.fromisoformat(str(iso).replace("Z", "+00:00"))


_MARK_RE = re.compile(r"ledger-attest:\s*(predictions|resolutions)\s+(\S+)\s+([0-9a-f]{64})(?![0-9a-f])")
VN = timezone(timedelta(hours=7))


def attestation_errors(pred_rows, res_rows, issues: dict, comments: dict) -> list[str]:
    """comments: {số Issue: [{"user": login, "created_at": iso, "updated_at": iso, "body": str}]}.
    Trả về danh sách lỗi; KHÔNG có khoảng miễn kiểm cho Issue vừa mở. Một dòng đạt khi Issue của nó có bình luận ✅ của github-actions[bot], chưa sửa, đăng trong
    ATTEST_WINDOW sau giờ tạo Issue (với dự báo: còn phải trước ngày resolve_at, giờ Việt Nam), chứa
    'ledger-attest: <sổ> <mã> <hash>' đúng hash của dòng — và mọi bình luận của bot trên Issue đó không nêu hash nào
    KHÁC cho cùng mã (không ai "đặt trước" hai nội dung rồi chọn một)."""
    errs = []
    def check(label, number, ledger, rid, rhash, before_day=None):
        it = issues.get(number)
        if it is None:
            return                                                # issue_crosscheck_errors đã báo
        try:
            opened = _ts(it.get("created_at"))
        except ValueError:
            errs.append(f"L-05: {label} — không đọc được giờ tạo Issue #{number}"); return
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
            if posted < opened or posted - opened > ATTEST_WINDOW:
                why = (f"dấu nhận đăng lúc {c.get('created_at')}, cách giờ tạo Issue {it.get('created_at')} quá "
                       f"{int(ATTEST_WINDOW.total_seconds() // 3600)} giờ"); continue
            if before_day and posted.astimezone(VN).date().isoformat() >= str(before_day):
                why = f"dấu nhận đăng lúc {c.get('created_at')}, không trước ngày resolve_at {before_day} (giờ Việt Nam)"; continue
            ok = True
        if ok and other:
            ok, why = False, f"robot còn đăng dấu nhận với hash khác cho cùng mã {rid} — không xác định được nội dung nào có trước"
        if ok:
            return
        errs.append(f"L-05: {label} — Issue #{number}: {why}. Dòng này không có bằng chứng là nội dung đã có từ lúc Issue mở "
                    "(dòng ghi vòng qua workflow nhận, hoặc dấu nhận bị xóa/sửa; nếu workflow nhận vừa chạy xong thì chạy lại "
                    "kiểm toán sau ít phút)")
    for r in pred_rows:
        if "issue_number" in r:
            check(f"dự báo {r.get('id')}", r.get("issue_number"), "predictions", r.get("id"), r.get("hash"), r.get("resolve_at"))
    for r in res_rows:
        if r.get("resolution_issue") is not None:
            check(f"phân định {r.get('prediction_id')}", r.get("resolution_issue"), "resolutions", r.get("prediction_id"), r.get("hash"))
    return errs


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
    """Mọi kết quả thử đã có ở commit gốc phải còn nguyên từng ô, đúng thứ tự (so theo tên cột của commit gốc)."""
    bh, br = _trials(base_trials)
    _, hr = _trials(head_trials)
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
      ở commit liền trước nó. Chỉ bỏ qua commit của kho TRƯỚC v3.0.2 (nhận biết bằng việc chưa có tools/registry_push.py —
      tệp bắt buộc từ v3.0.2, thiếu nó thì validate đỏ): đó là vòng học bản cũ, kết quả của nó do ghim trong config.yaml
      và dòng neo lịch sử chốt. Từ v3.0.2 trở đi không commit nào được miễn."""
    def git(*a):
        return subprocess.run(["git", "-C", str(root), *a], capture_output=True)
    def show(rev, path):
        r = git("show", f"{rev}:{path}")
        return r.stdout if r.returncode == 0 else None
    errs = trials_rows_errors(show(base, TRIALS), show("HEAD", TRIALS))
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
    commits = git("rev-list", "--reverse", f"{base}..HEAD", "--", TRIALS).stdout.decode().split()
    for c in commits:
        parent = git("rev-parse", "--verify", "-q", f"{c}^").stdout.decode().strip()
        if not parent:
            continue
        if show(c, V302_MARKER) is None:
            continue          # commit của kho trước v3.0.2 (vòng học bản cũ, chưa có sổ đăng ký): kết quả đó do ghim và dòng neo chốt
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
    a = ap.parse_args()
    errs = []
    base = (a.base or "").strip()
    if base and base != ZERO_SHA:
        if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{base}^{{commit}}"], capture_output=True).returncode != 0:
            errs.append(f"L-05: không đọc được commit gốc {base[:12]} để kiểm chỉ-ghi-thêm (lịch sử bị viết lại, hoặc checkout thiếu lịch sử)")
        else:
            head = {p: ((ROOT / p).read_bytes() if (ROOT / p).is_file() else None) for p in APPEND_ONLY}
            errs += append_only_errors({p: _git_show(base, p) for p in APPEND_ONLY}, head)
            errs += trials_history_errors(ROOT, base, pull_request=os.environ.get("GITHUB_EVENT_NAME", "").startswith("pull_request"))
    else:
        print("(bỏ qua kiểm chỉ-ghi-thêm: không có commit gốc)")
    if a.github:
        repo, token = os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_TOKEN", "")
        pred, res = _rows("ledger/predictions.jsonl"), _rows("ledger/resolutions.jsonl")
        need = any("issue_number" in r for r in pred) or any(r.get("resolution_issue") is not None for r in res)
        if not repo:
            print("(bỏ qua đối chiếu Issue: không có GITHUB_REPOSITORY)")
        else:
            try:
                if need:
                    issues = fetch_issues(repo, token)
                    errs += issue_crosscheck_errors(pred, res, issues, repo.split("/")[0])
                    errs += attestation_errors(pred, res, issues, fetch_comments(repo, token))
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
