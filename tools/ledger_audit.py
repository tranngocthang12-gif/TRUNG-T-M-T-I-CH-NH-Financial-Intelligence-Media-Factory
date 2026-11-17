"""Kiểm toán sổ ngoài hash chuỗi (ADR-0003; L-05, L-06, L-10). Hash chuỗi chỉ bắt sửa nhầm: ai ghi được vào kho cũng tính lại
được hash. Ba kiểm tra ở đây neo sổ vào thứ nằm NGOÀI tệp:

1. CHỈ GHI THÊM — nội dung ledger/predictions.jsonl, ledger/resolutions.jsonl, research/trial_registry.jsonl ở commit gốc
   (--base) phải là tiền tố nguyên từng byte của bản hiện tại. Sửa, xóa hay chèn dòng cũ → lỗi.
2. ĐỐI CHIẾU ISSUE (--github) — mỗi dòng dự báo/phân định từ Issue phải ứng với một Issue thật của kho: có tồn tại, không
   phải PR, do chủ kho mở, và giờ tạo trùng issue_created_at trong sổ (giờ máy chủ GitHub, không do người ghi tự khai).
3. L-10 (--github) — cảnh báo (không chặn) khi nhánh main chưa có luật bảo vệ nào.

Giới hạn nói thẳng: chủ kho có quyền quản trị vẫn viết lại được lịch sử nếu không bật ruleset cấm force-push; mục 3 nhắc việc đó.

Dùng trong CI:  python tools/ledger_audit.py --base "$BASE_SHA" --github
Môi trường: GITHUB_TOKEN, GITHUB_REPOSITORY (owner/repo). Thoát 1 khi có lỗi.
"""
import argparse, json, os, pathlib, subprocess, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
APPEND_ONLY = ("ledger/predictions.jsonl", "ledger/resolutions.jsonl", "research/trial_registry.jsonl")
ZERO_SHA = "0" * 40


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


def _rows(path):
    p = ROOT / path
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.is_file() else []


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
                    errs += issue_crosscheck_errors(pred, res, fetch_issues(repo, token), repo.split("/")[0])
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
    print("OK — sổ chỉ-ghi-thêm và khớp Issue thật" if not errs else f"{len(errs)} lỗi")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
