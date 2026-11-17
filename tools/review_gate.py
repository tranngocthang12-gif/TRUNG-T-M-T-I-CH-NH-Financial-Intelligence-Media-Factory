"""Cổng L-09 cho một Pull Request (workflow review_gate.yml; luật: tools/laws_checks.py, ADR-0003).

PR chỉ xanh khi:
1. Thân PR có đúng một dòng authored_by và một dòng reviewed_by, cả hai bắt đầu bằng tên ghế, không chung ghế
   (check_pr_review).
2. Bản chấm nằm TRÊN KHO: có bình luận PR (hoặc review) do chủ kho đăng, dòng đầu mở đầu "GỘP ĐƯỢC", và chứa 7 ký tự đầu
   SHA của commit đang đứng đầu PR (check_review_evidence). Đẩy commit mới → SHA đổi → cổng đỏ lại cho tới khi chấm bản mới.

Thứ tự thao tác của Owner: (a) dán nguyên bản chấm của ghế khác nhà thành bình luận PR; (b) sửa mô tả PR, điền reviewed_by.
Bước (b) làm cổng chạy lại. Nếu làm ngược thứ tự, bấm "Re-run jobs" ở việc này.

Giới hạn nói thẳng: máy kiểm được bản chấm có trên kho, đúng commit, đúng dạng; không kiểm được bản chấm có thật do ghế
đó viết. Người đọc sổ kiểm bằng cách đọc bình luận.

Môi trường: GITHUB_TOKEN, GITHUB_REPOSITORY (owner/repo), PR_NUMBER. Đọc thân PR và bình luận qua API lúc chạy (không dùng
bản chụp trong sự kiện) nên chạy lại luôn thấy trạng thái mới nhất. Thoát 1 khi chưa đạt.
"""
import json, os, pathlib, sys, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tools.laws_checks import check_pr_review, check_review_evidence  # noqa: E402


def evaluate(body, comments, head_sha, owner_login) -> list[str]:
    """Hàm thuần để test: trả về danh sách lỗi (rỗng = đạt)."""
    errs = check_pr_review(body)
    if errs:
        return errs
    return check_review_evidence(comments, head_sha, owner_login)


def _api(url, token):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "ttc-review-gate",
                                               **({"Authorization": f"Bearer {token}"} if token else {})})
    with urllib.request.urlopen(req, timeout=30) as f:
        return json.loads(f.read().decode("utf-8"))


def _paged(url, token):
    out, page = [], 1
    while True:
        batch = _api(f"{url}{'&' if '?' in url else '?'}per_page=100&page={page}", token)
        if not batch:
            return out
        out += batch
        page += 1


def main() -> int:
    repo, token, number = os.environ["GITHUB_REPOSITORY"], os.environ.get("GITHUB_TOKEN", ""), os.environ["PR_NUMBER"]
    base = f"https://api.github.com/repos/{repo}"
    pr = _api(f"{base}/pulls/{number}", token)
    comments = [{"user": (c.get("user") or {}).get("login"), "body": c.get("body")}
                for c in _paged(f"{base}/issues/{number}/comments", token) + _paged(f"{base}/pulls/{number}/reviews", token)]
    errs = evaluate(pr.get("body") or "", comments, (pr.get("head") or {}).get("sha", ""), repo.split("/")[0])
    print("\n".join(errs) if errs else f"OK: L-09 — có người chấm khác ghế và bản chấm GỘP ĐƯỢC cho commit {pr['head']['sha'][:7]}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
