"""Tải bản gốc theo danh sách URL, ghi bằng chứng tải, KHÔNG ghi kho (P0-3, đồng thời S0a của ADR-0017).

Chạy trong GitHub Actions (`.github/workflows/fetch_originals.yml`): tệp tải về và `manifest.json` được đưa lên artifact của
lượt chạy; workflow chỉ có quyền đọc kho và không đẩy commit nào. Người muốn đưa một tệp vào kho tải artifact về rồi mở PR
riêng (ghim sha256 theo ADR-0012), không phải việc của công cụ này.

Với mỗi URL công cụ ghi: URL gốc và URL cuối (sau chuyển hướng), mã HTTP, toàn bộ header trả về, giờ máy chủ (header
`Date`), giờ bắt đầu và kết thúc tải theo đồng hồ máy chạy (UTC), sha256 và số byte của nội dung, tên tệp đã lưu. Có thể
khai sha256 mong đợi cho từng URL; lệch thì ghi lỗi.

Đóng khi nghi ngờ:
  - chỉ nhận `https://`; URL khác bị ghi lỗi và không được gọi;
  - mã khác 200, lỗi mạng, vượt giới hạn dung lượng, hay lệch sha256 mong đợi đều là lỗi; công cụ thoát mã 1 nếu có
    bất kỳ lỗi nào (nội dung trả về vẫn được lưu để làm bằng chứng, trừ khi vượt giới hạn dung lượng);
  - thư mục `--out` phải chưa tồn tại và phải nằm ngoài kho mã (không có đường nào ghi vào kho);
  - tên tệp chỉ giữ ký tự an toàn, không thể thoát khỏi thư mục `--out`.

Danh sách URL: mỗi URL cách nhau bằng khoảng trắng, xuống dòng hoặc dấu phẩy; dòng bắt đầu bằng `#` là chú thích; một mục
`sha256=<64 ký tự hex>` đứng ngay sau một URL là hash mong đợi của URL đó.

Dùng: python tools/fetch_originals.py --urls DANH_SACH --out THU_MUC [--max-bytes N] [--timeout GIAY]
Thoát: 0 khi mọi URL đạt; 1 khi có URL lỗi; 2 khi từ chối `--out` hoặc danh sách rỗng (không tạo gì)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

REPO = pathlib.Path(__file__).resolve().parents[1]
TOOL_VERSION = "1"
USER_AGENT = "ttc-fetch-originals/1 (GitHub Actions; doc ban goc cong bo thong tin)"
DEFAULT_MAX_BYTES = 50 * 1024 * 1024
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


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


def fetch_one(entry: dict, index: int, files_dir: pathlib.Path, *, max_bytes: int, timeout: float,
              allow_schemes=("https",), opener=None) -> dict:
    url = entry["url"]
    rec = {"index": index, "url": url, "expected_sha256": entry.get("expected_sha256"), "final_url": None,
           "http_status": None, "reason": None, "headers": None, "server_date": None, "fetched_at_start": _now(),
           "fetched_at_end": None, "sha256": None, "bytes": None, "file": None, "sha256_match": None, "ok": False,
           "error": None}
    scheme = urllib.parse.urlsplit(url).scheme.lower()
    if scheme not in allow_schemes:
        rec["error"] = f"chỉ nhận {', '.join(s + '://' for s in allow_schemes)}; URL có scheme '{scheme}' không được gọi"
        rec["fetched_at_end"] = _now()
        return rec
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    open_ = (opener or urllib.request.build_opener()).open
    body = b""
    try:
        try:
            resp = open_(req, timeout=timeout)
        except urllib.error.HTTPError as e:            # vẫn có mã, header và nội dung: giữ làm bằng chứng
            resp = e
        with resp:
            rec["http_status"] = int(resp.status if hasattr(resp, "status") else resp.code)
            rec["reason"] = getattr(resp, "reason", None)
            rec["final_url"] = resp.geturl()
            rec["headers"] = [[k, v] for k, v in resp.headers.items()]
            rec["server_date"] = resp.headers.get("Date")
            body = resp.read(max_bytes + 1)
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
              allow_schemes=("https",), opener=None) -> dict:
    files_dir = out / "files"
    files_dir.mkdir(parents=True, exist_ok=False)
    items = [fetch_one(e, i, files_dir, max_bytes=max_bytes, timeout=timeout, allow_schemes=allow_schemes, opener=opener)
             for i, e in enumerate(entries, 1)]
    manifest = {"tool": "tools/fetch_originals.py", "tool_version": TOOL_VERSION, "generated_at": _now(),
                "run": run_info(), "user_agent": USER_AGENT, "max_bytes": max_bytes,
                "all_ok": all(r["ok"] for r in items), "items": items}
    with open(out / "manifest.json", "x", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    lines = ["| # | URL | HTTP | byte | sha256 | khớp mong đợi | lỗi |", "|---|---|---|---|---|---|---|"]
    for r in items:
        lines.append(f"| {r['index']} | {r['url']} | {r['http_status']} | {r['bytes']} | "
                     f"{(r['sha256'] or '')[:16]} | {r['sha256_match']} | {r['error'] or ''} |")
    with open(out / "summary.md", "x", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--urls", required=True, help="tệp danh sách URL")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    ap.add_argument("--timeout", type=float, default=60.0)
    a = ap.parse_args(argv)
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
    m = fetch_all(entries, out, max_bytes=a.max_bytes, timeout=a.timeout)
    print((out / "summary.md").read_text(encoding="utf-8"))
    return 0 if m["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
