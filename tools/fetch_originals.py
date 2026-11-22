"""Tải bản gốc theo danh sách URL, ghi bằng chứng tải, KHÔNG ghi kho (P0-3; lượt chạy thử phục vụ S0a của ADR-0017).

Chạy trong GitHub Actions (`.github/workflows/fetch_originals.yml`): tệp tải về và `manifest.json` được đưa lên artifact của
lượt chạy; workflow chỉ có quyền đọc kho và không đẩy commit nào. Người muốn đưa một tệp vào kho tải artifact về rồi mở PR
riêng (ghim sha256 theo ADR-0012), không phải việc của công cụ này.

Với mỗi URL công cụ ghi: URL gốc và URL cuối (sau chuyển hướng), mã HTTP, toàn bộ header trả về, giờ máy chủ (header
`Date`), giờ bắt đầu và kết thúc tải theo đồng hồ máy chạy (UTC), sha256 và số byte của nội dung, tên tệp đã lưu. Có thể
khai sha256 mong đợi cho từng URL; lệch thì ghi lỗi.

Đóng khi nghi ngờ:
  - mỗi bước, gồm URL ban đầu và MỌI bước chuyển hướng, được kiểm TRƯỚC khi kết nối: chỉ `https://`, không hạ từ https
    xuống scheme khác, không có thông tin đăng nhập trong URL, host phải nằm trong danh sách duyệt (mặc định ALLOW_HOSTS,
    thêm bằng `--allow-host`), và mọi địa chỉ IP mà host phân giải ra phải là địa chỉ công khai (không loopback, mạng
    riêng, link-local, dành riêng). Bước không đạt bị ghi lỗi và không được gọi;
  - `--max-bytes`, `--timeout` (mỗi lần đọc socket) và `--deadline` (tổng thời gian cho một URL) phải dương; quá
    `--deadline` thì dừng URL đó, ghi lỗi, không lưu phần đã tải;
  - mã khác 200, lỗi mạng, vượt giới hạn dung lượng, hay lệch sha256 mong đợi đều là lỗi; công cụ thoát mã 1 nếu có
    bất kỳ lỗi nào (nội dung trả về vẫn được lưu để làm bằng chứng, trừ khi vượt giới hạn dung lượng);
  - thư mục `--out` phải chưa tồn tại và phải nằm ngoài kho mã (không có đường nào ghi vào kho);
  - tên tệp chỉ giữ ký tự an toàn, không thể thoát khỏi thư mục `--out`.

Đầu ra không ghi giá trị nhạy cảm: thông tin đăng nhập trong URL, giá trị tham số truy vấn có tên giống khóa bí mật (token,
signature, key, …) và giá trị header Set-Cookie được thay bằng REDACTED ở manifest, summary và stdout.

Trạng thái pháp lý (ADR-0017 QĐ-S9 mục 2): manifest ghi `legal_status` = CHUA_KIEM_DIEU_KHOAN cho mọi host đã gọi, kèm
nguồn và thời điểm đối chiếu điều khoản (null khi chưa đối chiếu). Công cụ không tự ghi trạng thái "được phép".

Danh sách URL: mỗi URL cách nhau bằng khoảng trắng, xuống dòng hoặc dấu phẩy; dòng bắt đầu bằng `#` là chú thích; một mục
`sha256=<64 ký tự hex>` đứng ngay sau một URL là hash mong đợi của URL đó.

Mỗi URL xong là ghi ngay một dòng vào `progress.jsonl` và in một dòng tiến độ (đã che giá trị nhạy cảm), nên nếu lượt chạy
bị dừng giữa chừng thì vẫn còn bằng chứng của các URL đã xong.

Dùng: python tools/fetch_originals.py --urls DANH_SACH --out THU_MUC [--max-bytes N] [--timeout GIAY] [--deadline GIAY]
      [--allow-host H ...]
Thoát: 0 khi mọi URL đạt; 1 khi có URL lỗi; 2 khi từ chối `--out`, tham số sai hoặc danh sách rỗng (không tạo gì)."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import pathlib
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

REPO = pathlib.Path(__file__).resolve().parents[1]
TOOL_VERSION = "2"
USER_AGENT = "ttc-fetch-originals/2 (GitHub Actions; doc ban goc cong bo thong tin)"
DEFAULT_MAX_BYTES = 50 * 1024 * 1024
DEFAULT_DEADLINE = 600.0
CHUNK = 64 * 1024
# Host được duyệt mặc định: trang, API và kho tệp của HOSE; cổng văn bản pháp luật. Thêm host khác bằng --allow-host.
ALLOW_HOSTS = ("www.hsx.vn", "api.hsx.vn", "staticfile.hsx.vn", "vbpl.vn")
LEGAL_STATUS = "CHUA_KIEM_DIEU_KHOAN"
LEGAL_NOTE = ("Chưa đối chiếu điều khoản sử dụng của trang nguồn về việc tải tự động. L-04 cho chép nguyên văn BCTC; điều đó "
              "không thay cho kiểm điều khoản. ADR-0017 QĐ-S9 mục 2 chưa xong cho tới khi có nguồn và thời điểm đối chiếu.")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_SECRET = re.compile(r"(token|sig|signature|key|auth|password|passwd|secret|credential|session|x-amz-|x-goog-)", re.I)


def redact(url):
    """URL an toàn để ghi: bỏ thông tin đăng nhập; giá trị tham số truy vấn có tên giống khóa bí mật thành REDACTED."""
    if not isinstance(url, str):
        return url
    try:
        p = urllib.parse.urlsplit(url)
        port = p.port
    except ValueError:
        return "URL_KHONG_HOP_LE"
    netloc = p.hostname or ""
    if port:
        netloc += f":{port}"
    q = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
    query = urllib.parse.urlencode([(k, "REDACTED" if _SECRET.search(k) else v) for k, v in q]) if q else p.query
    return urllib.parse.urlunsplit((p.scheme, netloc, p.path, query, ""))


def url_problem(url, prev=None, *, allow_schemes=("https",), allow_hosts=ALLOW_HOSTS, allow_private=False,
                resolve=socket.getaddrinfo):
    """Lý do KHÔNG được kết nối tới `url` (bước đầu khi prev=None, hoặc bước chuyển hướng từ `prev`), hoặc None."""
    try:
        p = urllib.parse.urlsplit(url)
        port = p.port
    except ValueError as e:
        return f"URL không hợp lệ: {e}"
    scheme = p.scheme.lower()
    if scheme not in allow_schemes:
        return f"chỉ nhận {', '.join(x + '://' for x in allow_schemes)}; scheme '{scheme}' không được gọi"
    if prev is not None and urllib.parse.urlsplit(prev).scheme.lower() == "https" and scheme != "https":
        return f"chuyển hướng hạ từ https xuống {scheme}://, không được gọi"
    if p.username is not None or p.password is not None:
        return "URL chứa thông tin đăng nhập, không được gọi"
    host = (p.hostname or "").lower().rstrip(".")
    if not host:
        return "URL không có host"
    if host not in {h.lower() for h in allow_hosts}:
        return f"host '{host}' không nằm trong danh sách duyệt, không được gọi"
    if not allow_private:
        try:
            infos = resolve(host, port or (443 if scheme == "https" else 80), proto=socket.IPPROTO_TCP)
        except OSError as e:
            return f"không phân giải được host '{host}': {e}"
        ips = {info[4][0] for info in infos}
        if not ips:
            return f"host '{host}' không có địa chỉ IP"
        for ip in sorted(ips):
            if not ipaddress.ip_address(ip.split("%", 1)[0]).is_global:
                return f"host '{host}' phân giải ra địa chỉ không công khai {ip}, không được gọi"
    return None


class _GuardedRedirect(urllib.request.HTTPRedirectHandler):
    """Kiểm mỗi bước chuyển hướng TRƯỚC khi urllib kết nối tới đích mới; không đạt thì dừng, không gọi đích."""

    def __init__(self, policy, hops):
        super().__init__()
        self.policy, self.hops = policy, hops

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        why = url_problem(newurl, req.full_url, **self.policy)
        self.hops.append({"from": redact(req.full_url), "to": redact(newurl), "code": code, "refused": why})
        if why:
            raise urllib.error.URLError(f"từ chối chuyển hướng: {why}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def parse_url_list(text: str) -> list[dict]:
    """[{url, expected_sha256}] theo thứ tự xuất hiện. Lỗi định dạng ném ValueError."""
    entries: list[dict] = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        for tok in re.split(r"[\s,]+", line.strip()):
            if not tok:
                continue
            if tok.lower().startswith("sha256="):
                h = tok.split("=", 1)[1].lower()
                if not entries or entries[-1]["expected_sha256"] is not None:
                    raise ValueError(f"'{tok}' không đứng ngay sau một URL")
                if not _HEX64.match(h):
                    raise ValueError(f"sha256 mong đợi không hợp lệ: {h!r}")
                entries[-1]["expected_sha256"] = h
            else:
                entries.append({"url": tok, "expected_sha256": None})
    return entries


def safe_name(url: str, index: int, digest: str) -> str:
    """Tên tệp an toàn: số thứ tự, 16 ký tự đầu sha256, phần cuối đường dẫn URL chỉ giữ [A-Za-z0-9._-]."""
    tail = urllib.parse.unquote(urllib.parse.urlsplit(url).path.rsplit("/", 1)[-1]) or "index"
    tail = re.sub(r"[^A-Za-z0-9._-]+", "_", tail).strip("._") or "index"
    return f"{index:03d}_{digest[:16]}_{tail[:100]}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _check_limits(max_bytes, timeout, deadline=DEFAULT_DEADLINE):
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0:
        raise ValueError(f"max_bytes phải là số nguyên dương, nhận {max_bytes!r}")
    for name, v in (("timeout", timeout), ("deadline", deadline)):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not v > 0 or v == float("inf"):
            raise ValueError(f"{name} phải là số dương hữu hạn, nhận {v!r}")


def _read_body(resp, max_bytes, deadline, start):
    """Đọc từng khúc; quá `deadline` giây kể từ `start` thì ném TimeoutError. Đọc tối đa max_bytes + 1 byte."""
    chunks, total = [], 0
    while total <= max_bytes:
        if time.monotonic() - start > deadline:
            raise TimeoutError(f"vượt thời hạn {deadline:g} giây cho một URL sau {total} byte; không lưu")
        b = resp.read(min(CHUNK, max_bytes + 1 - total))
        if not b:
            break
        chunks.append(b)
        total += len(b)
    return b"".join(chunks)


def fetch_one(entry: dict, index: int, files_dir: pathlib.Path, *, max_bytes: int, timeout: float,
              deadline=DEFAULT_DEADLINE, allow_schemes=("https",), allow_hosts=ALLOW_HOSTS, allow_private=False,
              opener=None) -> dict:
    _check_limits(max_bytes, timeout, deadline)
    start = time.monotonic()
    url = entry["url"]
    rec = {"index": index, "url": redact(url), "expected_sha256": entry.get("expected_sha256"), "final_url": None,
           "redirects": [], "http_status": None, "reason": None, "headers": None, "server_date": None,
           "fetched_at_start": _now(), "fetched_at_end": None, "sha256": None, "bytes": None, "file": None,
           "sha256_match": None, "ok": False, "error": None}
    policy = {"allow_schemes": tuple(allow_schemes), "allow_hosts": tuple(allow_hosts), "allow_private": allow_private}
    why = url_problem(url, **policy)
    if why:
        rec["error"] = why
        rec["fetched_at_end"] = _now()
        return rec
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    open_ = (opener or urllib.request.build_opener(_GuardedRedirect(policy, rec["redirects"]))).open
    body = b""
    try:
        try:
            resp = open_(req, timeout=timeout)
        except urllib.error.HTTPError as e:            # vẫn có mã, header và nội dung: giữ làm bằng chứng
            resp = e
        with resp:
            rec["http_status"] = int(resp.status if hasattr(resp, "status") else resp.code)
            rec["reason"] = getattr(resp, "reason", None)
            rec["final_url"] = redact(resp.geturl())
            rec["headers"] = [[k, "REDACTED" if k.lower() == "set-cookie" else v] for k, v in resp.headers.items()]
            rec["server_date"] = resp.headers.get("Date")
            body = _read_body(resp, max_bytes, deadline, start)
    except Exception as e:                              # noqa: BLE001 — lỗi mạng, hết giờ, TLS: ghi lại, không ném
        rec["error"] = f"{type(e).__name__}: {e}"[:500]
        rec["fetched_at_end"] = _now()
        return rec
    rec["fetched_at_end"] = _now()
    if len(body) > max_bytes:
        rec["error"] = f"nội dung vượt giới hạn {max_bytes} byte; không lưu"
        return rec
    digest = hashlib.sha256(body).hexdigest()
    rec["sha256"], rec["bytes"] = digest, len(body)
    name = safe_name(url, index, digest)
    path = (files_dir / name).resolve()
    if files_dir.resolve() not in path.parents:
        rec["error"] = "tên tệp thoát khỏi thư mục xuất; không lưu"
        return rec
    with open(path, "xb") as f:
        f.write(body)
    rec["file"] = f"files/{name}"
    errs = []
    if rec["http_status"] != 200:
        errs.append(f"mã HTTP {rec['http_status']} khác 200")
    if rec["expected_sha256"] is not None:
        rec["sha256_match"] = digest == rec["expected_sha256"]
        if not rec["sha256_match"]:
            errs.append("sha256 lệch giá trị mong đợi")
    rec["error"] = "; ".join(errs) or None
    rec["ok"] = not errs
    return rec


def out_problem(out: pathlib.Path) -> str | None:
    if out.is_symlink() or out.exists():
        return f"{out} đã tồn tại; chọn thư mục mới"
    res = out.resolve()
    try:
        res.relative_to(REPO.resolve())
    except ValueError:
        return None
    return f"{res} nằm trong kho mã; công cụ không ghi vào kho"


def run_info() -> dict:
    keys = ("GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_SHA", "GITHUB_REF", "GITHUB_WORKFLOW", "GITHUB_EVENT_NAME",
            "GITHUB_REPOSITORY", "RUNNER_OS")
    return {k: os.environ.get(k) for k in keys}


def fetch_all(entries: list[dict], out: pathlib.Path, *, max_bytes=DEFAULT_MAX_BYTES, timeout=60.0,
              deadline=DEFAULT_DEADLINE, allow_schemes=("https",), allow_hosts=ALLOW_HOSTS, allow_private=False,
              opener=None) -> dict:
    _check_limits(max_bytes, timeout, deadline)
    files_dir = out / "files"
    files_dir.mkdir(parents=True, exist_ok=False)
    items = []
    with open(out / "progress.jsonl", "x", encoding="utf-8") as prog:
        for i, e in enumerate(entries, 1):
            r = fetch_one(e, i, files_dir, max_bytes=max_bytes, timeout=timeout, deadline=deadline,
                          allow_schemes=allow_schemes, allow_hosts=allow_hosts, allow_private=allow_private, opener=opener)
            items.append(r)
            prog.write(json.dumps(r, ensure_ascii=False) + "\n")
            prog.flush()
            print(f"[{i}/{len(entries)}] {r['url']} HTTP {r['http_status']} {r['bytes']} byte "
                  f"{'OK' if r['ok'] else 'LỖI: ' + str(r['error'])}", flush=True)
    hosts = sorted({urllib.parse.urlsplit(r["url"]).hostname or "" for r in items} - {""})
    manifest = {"tool": "tools/fetch_originals.py", "tool_version": TOOL_VERSION, "generated_at": _now(),
                "run": run_info(), "user_agent": USER_AGENT, "max_bytes": max_bytes, "timeout": timeout, "deadline": deadline,
                "allow_hosts": sorted(allow_hosts),
                "legal": [{"host": h, "legal_status": LEGAL_STATUS, "terms_source": None, "terms_checked_at": None,
                           "note": LEGAL_NOTE} for h in hosts],
                "all_ok": all(r["ok"] for r in items), "items": items}
    with open(out / "manifest.json", "x", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    lines = ["| # | URL | HTTP | byte | sha256 | khớp mong đợi | lỗi |", "|---|---|---|---|---|---|---|"]
    for r in items:
        lines.append(f"| {r['index']} | {r['url']} | {r['http_status']} | {r['bytes']} | "
                     f"{(r['sha256'] or '')[:16]} | {r['sha256_match']} | {r['error'] or ''} |")
    lines += ["", f"Trạng thái pháp lý của việc tải tự động: {LEGAL_STATUS} cho {', '.join(hosts) or 'không host nào'}. "
              + LEGAL_NOTE]
    with open(out / "summary.md", "x", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--urls", required=True, help="tệp danh sách URL")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--deadline", type=float, default=DEFAULT_DEADLINE, help="tổng thời gian tối đa cho một URL (giây)")
    ap.add_argument("--allow-host", action="append", default=[], help="thêm host được duyệt (lặp lại được)")
    a = ap.parse_args(argv)
    try:
        _check_limits(a.max_bytes, a.timeout, a.deadline)
    except ValueError as e:
        print("TỪ CHỐI:", e, file=sys.stderr)
        return 2
    out = pathlib.Path(a.out)
    why = out_problem(out)
    if why:
        print("TỪ CHỐI:", why, file=sys.stderr)
        return 2
    try:
        entries = parse_url_list(pathlib.Path(a.urls).read_text(encoding="utf-8"))
    except ValueError as e:
        print("TỪ CHỐI: danh sách URL sai định dạng:", e, file=sys.stderr)
        return 2
    if not entries:
        print("TỪ CHỐI: danh sách URL rỗng", file=sys.stderr)
        return 2
    print(f"{len(entries)} URL; host: " + ", ".join(sorted({urllib.parse.urlsplit(e['url']).hostname or '?' for e in entries})),
          flush=True)
    m = fetch_all(entries, out, max_bytes=a.max_bytes, timeout=a.timeout, deadline=a.deadline,
                  allow_hosts=tuple(ALLOW_HOSTS) + tuple(h.lower() for h in a.allow_host))
    print((out / "summary.md").read_text(encoding="utf-8"))
    return 0 if m["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
