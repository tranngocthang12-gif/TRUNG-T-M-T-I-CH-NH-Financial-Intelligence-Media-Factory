"""P0-3: công cụ tải bản gốc (tools/fetch_originals.py). Máy chủ HTTP cục bộ trên 127.0.0.1, không ra mạng ngoài,
không ghi vào kho. Hàm lõi được gọi với scheme http, host 127.0.0.1 và cho phép địa chỉ nội bộ chỉ để nói chuyện với máy
chủ cục bộ; chính sách mặc định (https, host duyệt, IP công khai, kiểm từng bước chuyển hướng) được kiểm riêng."""
from __future__ import annotations

import hashlib
import http.server
import json
import pathlib
import shutil
import subprocess
import sys
import threading
import time

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from tools import fetch_originals as fo   # noqa: E402

PDF = b"%PDF-1.4 ban goc gia lap " + bytes(range(256))
BIG = b"x" * 5000


HITS = {"b": 0}
OTHER = {"port": None}


class _B(http.server.BaseHTTPRequestHandler):
    """Máy chủ đích thứ hai: đếm số lần bị gọi, để chứng minh chuyển hướng bị từ chối thì đích không nhận yêu cầu nào."""

    def log_message(self, *a):
        pass

    def do_GET(self):
        HITS["b"] += 1
        self.send_response(200)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"ok")


class _H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        p = self.path
        if p == "/redirect-localhost":
            self.send_response(302)
            self.send_header("Location", f"http://localhost:{OTHER['port']}/doc.pdf")
            self.end_headers()
        elif p == "/slow":
            self.send_response(200)
            self.send_header("Content-Length", str(20 * 70000))
            self.end_headers()
            try:
                for _ in range(20):
                    self.wfile.write(b"s" * 70000)
                    self.wfile.flush()
                    time.sleep(0.15)
            except (BrokenPipeError, ConnectionResetError):
                pass
        elif p.startswith("/cookie"):
            self.send_response(200)
            self.send_header("Set-Cookie", "phien=bi-mat-123")
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"ok")
        elif p.startswith("/doc.pdf"):
            self._send(200, PDF, "application/pdf")
        elif p == "/forbidden":
            self._send(403, b"<html>bi chan</html>", "text/html")
        elif p == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/doc.pdf")
            self.end_headers()
        elif p == "/big":
            self._send(200, BIG, "application/octet-stream")
        else:
            self._send(404, b"khong co", "text/plain")

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture(scope="module")
def server():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _H)
    other = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _B)
    OTHER["port"] = other.server_address[1]
    for x in (srv, other):
        threading.Thread(target=x.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    other.shutdown()


def _run(entries, out, **kw):
    kw = {"allow_schemes": ("http",), "allow_hosts": ("127.0.0.1",), "allow_private": True, "timeout": 10, **kw}
    return fo.fetch_all(entries, out, **kw)


def _public(*a, **k):
    return [(2, 1, 6, "", ("8.8.8.8", 443)), (10, 1, 6, "", ("2001:4860:4860::8888", 443, 0, 0))]


def _e(url, h=None):
    return {"url": url, "expected_sha256": h}


def test_ok_records_hash_bytes_headers_server_time_and_saves_file(server, tmp_path):
    out = tmp_path / "o"
    m = _run([_e(f"{server}/doc.pdf", hashlib.sha256(PDF).hexdigest())], out)
    r = m["items"][0]
    assert m["all_ok"] and r["ok"] and r["error"] is None and r["sha256_match"] is True
    assert r["http_status"] == 200 and r["bytes"] == len(PDF) and r["sha256"] == hashlib.sha256(PDF).hexdigest()
    assert r["server_date"] and any(k.lower() == "content-type" for k, _ in r["headers"])
    assert r["fetched_at_start"] <= r["fetched_at_end"]
    assert (out / r["file"]).read_bytes() == PDF
    assert json.loads((out / "manifest.json").read_text(encoding="utf-8")) == m
    assert (out / "summary.md").is_file()


def test_expected_hash_mismatch_is_an_error(server, tmp_path):
    m = _run([_e(f"{server}/doc.pdf", "0" * 64)], tmp_path / "o")
    r = m["items"][0]
    assert not m["all_ok"] and not r["ok"] and r["sha256_match"] is False and "sha256" in r["error"]


def test_non_200_is_an_error_but_body_is_kept_as_evidence(server, tmp_path):
    out = tmp_path / "o"
    m = _run([_e(f"{server}/forbidden")], out)
    r = m["items"][0]
    assert not m["all_ok"] and r["http_status"] == 403 and "403" in r["error"]
    assert (out / r["file"]).read_bytes() == b"<html>bi chan</html>"


def test_redirect_records_final_url(server, tmp_path):
    r = _run([_e(f"{server}/redirect")], tmp_path / "o")["items"][0]
    assert r["ok"] and r["final_url"].endswith("/doc.pdf") and r["url"].endswith("/redirect")


def test_over_size_limit_is_an_error_and_nothing_saved(server, tmp_path):
    out = tmp_path / "o"
    r = _run([_e(f"{server}/big")], out, max_bytes=1000)["items"][0]
    assert not r["ok"] and "giới hạn" in r["error"] and r["file"] is None
    assert not any((out / "files").iterdir())


def test_network_error_is_recorded_not_raised(tmp_path):
    r = _run([_e("http://127.0.0.1:1/khong-co")], tmp_path / "o")["items"][0]
    assert not r["ok"] and r["http_status"] is None and r["error"]


def test_only_https_is_called_by_default(tmp_path):
    called = []

    class _Opener:
        def open(self, *a, **k):
            called.append(a)
            raise AssertionError("không được gọi mạng")

    m = fo.fetch_all([_e("http://example.invalid/x"), _e("ftp://example.invalid/y")], tmp_path / "o", opener=_Opener())
    assert not called and not m["all_ok"]
    assert all("chỉ nhận https://" in r["error"] for r in m["items"])


def test_file_names_cannot_escape_output_dir(server, tmp_path):
    out = tmp_path / "o"
    r = _run([_e(f"{server}/doc.pdf/..%2F..%2F..%2Fescape.pdf")], out)["items"][0]
    assert r["file"] and "/" not in r["file"].split("files/", 1)[1]
    assert (out / r["file"]).resolve().parent == (out / "files").resolve()


def test_url_list_parsing():
    h = "a" * 64
    text = f"# chu thich\nhttps://a.vn/x sha256={h}\nhttps://b.vn/y, https://c.vn/z\n\n"
    assert fo.parse_url_list(text) == [{"url": "https://a.vn/x", "expected_sha256": h},
                                       {"url": "https://b.vn/y", "expected_sha256": None},
                                       {"url": "https://c.vn/z", "expected_sha256": None}]
    for bad in (f"sha256={h}", "https://a.vn/x sha256=zz", f"https://a.vn/x sha256={h} sha256={h}"):
        with pytest.raises(ValueError):
            fo.parse_url_list(bad)


def _cli(*args):
    return subprocess.run([sys.executable, str(REPO / "tools" / "fetch_originals.py"), *args], capture_output=True,
                          text=True, cwd=REPO)


def test_cli_refuses_output_inside_repo_or_existing_and_creates_nothing(tmp_path):
    urls = tmp_path / "u.txt"
    urls.write_text("https://example.invalid/x\n", encoding="utf-8")
    inside = REPO / "reports" / "_fetch_originals_should_not_exist"
    assert not inside.exists()
    try:
        r = _cli("--urls", str(urls), "--out", str(inside))
        assert r.returncode == 2 and "kho mã" in r.stderr and not inside.exists()
    finally:                                   # hồi quy làm test đỏ nhưng không để lại rác trong kho
        if inside.exists():
            shutil.rmtree(inside)
    existing = tmp_path / "da_co"
    existing.mkdir()
    r = _cli("--urls", str(urls), "--out", str(existing))
    assert r.returncode == 2 and not any(existing.iterdir())


def test_cli_rejects_non_https_without_network_and_exits_1(tmp_path):
    urls = tmp_path / "u.txt"
    urls.write_text("http://127.0.0.1:1/x\n", encoding="utf-8")
    out = tmp_path / "o"
    r = _cli("--urls", str(urls), "--out", str(out))
    m = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert r.returncode == 1 and m["items"][0]["http_status"] is None and "https://" in m["items"][0]["error"]


def test_cli_refuses_empty_or_malformed_list(tmp_path):
    urls = tmp_path / "u.txt"
    for text in ("# chi co chu thich\n", "sha256=" + "a" * 64):
        urls.write_text(text, encoding="utf-8")
        out = tmp_path / f"o{len(text)}"
        r = _cli("--urls", str(urls), "--out", str(out))
        assert r.returncode == 2 and not out.exists()


def test_smoke_list_is_https_and_pins_the_known_pdf_hash():
    entries = fo.parse_url_list((REPO / "tools" / "fetch_originals_smoke.txt").read_text(encoding="utf-8"))
    assert entries and all(e["url"].startswith("https://") for e in entries)
    man = json.loads((REPO / "data/evidence/corporate_actions/EVIDENCE_MANIFEST.json").read_text(encoding="utf-8"))
    tcb = next(d for d in man["source_documents"] if d["source_id"] == "hose-1705374")
    assert {"url": tcb["url"], "expected_sha256": tcb["sha256"]} in entries


# ---------- Bản chấm L-09 vòng 1 (PR #76): chuyển hướng, host, IP, giới hạn, lộ URL, trạng thái pháp lý ----------

def test_redirect_to_unapproved_host_is_refused_before_connecting(server, tmp_path):
    HITS["b"] = 0
    r = _run([_e(f"{server}/redirect-localhost")], tmp_path / "o")["items"][0]
    assert not r["ok"] and "từ chối chuyển hướng" in r["error"] and "localhost" in r["error"]
    assert r["redirects"] and r["redirects"][0]["refused"] and HITS["b"] == 0
    # Đối chứng: cùng đích nhưng host được duyệt thì đích nhận đúng một yêu cầu.
    r = _run([_e(f"http://localhost:{OTHER['port']}/doc.pdf")], tmp_path / "o2", allow_hosts=("localhost",))["items"][0]
    assert r["ok"] and HITS["b"] == 1


def test_https_to_http_redirect_is_refused_without_a_request():
    class _Req:
        full_url = "https://www.hsx.vn/a"
    hops = []
    guard = fo._GuardedRedirect({"allow_schemes": ("https", "http"), "allow_hosts": fo.ALLOW_HOSTS,
                                 "allow_private": False, "resolve": _public}, hops)
    with pytest.raises(fo.urllib.error.URLError) as e:
        guard.redirect_request(_Req(), None, 302, "Found", {}, "http://www.hsx.vn/b")
    assert "hạ từ https" in str(e.value) and hops[0]["refused"]
    assert fo.url_problem("https://www.hsx.vn/b", "https://www.hsx.vn/a", resolve=_public) is None


@pytest.mark.parametrize("ip", ["127.0.0.1", "10.1.2.3", "172.16.0.9", "192.168.1.1", "169.254.169.254", "0.0.0.0",
                                "::1", "fc00::1", "fe80::1", "100.64.0.1"])
def test_non_public_addresses_are_refused(ip):
    fake = lambda *a, **k: [(2, 1, 6, "", (ip, 443))]   # noqa: E731
    assert "không công khai" in fo.url_problem("https://www.hsx.vn/x", resolve=fake)
    assert fo.url_problem("https://www.hsx.vn/x", resolve=_public) is None


@pytest.mark.parametrize("url,word", [("https://evil.example/x", "danh sách duyệt"), ("https://u:p@www.hsx.vn/x", "đăng nhập"),
                                      ("http://www.hsx.vn/x", "https://"), ("https:///x", "không có host"),
                                      ("https://www.hsx.vn:99999/x", "không hợp lệ")])
def test_first_hop_policy_refuses_without_calling(url, word, tmp_path):
    assert word in fo.url_problem(url, resolve=_public)
    called = []

    class _Opener:
        def open(self, *a, **k):
            called.append(a)
            raise AssertionError("không được gọi mạng")

    r = fo.fetch_all([_e(url)], tmp_path / "o", opener=_Opener())["items"][0]
    assert not called and not r["ok"] and r["http_status"] is None


@pytest.mark.parametrize("kw", [{"max_bytes": 0}, {"max_bytes": -2}, {"max_bytes": 1.5}, {"timeout": 0}, {"timeout": -1},
                                {"timeout": float("nan")}, {"deadline": 0}, {"deadline": -1}, {"deadline": float("inf")}])
def test_limits_must_be_positive(kw, tmp_path):
    with pytest.raises(ValueError):
        fo.fetch_all([_e("https://www.hsx.vn/x")], tmp_path / "o", **kw)
    assert not (tmp_path / "o").exists()


def test_cli_refuses_non_positive_limits_and_creates_nothing(tmp_path):
    urls = tmp_path / "u.txt"
    urls.write_text("https://www.hsx.vn/x\n", encoding="utf-8")
    for args in (["--max-bytes", "-2"], ["--max-bytes", "0"], ["--timeout", "0"], ["--timeout", "-5"], ["--deadline", "0"]):
        out = tmp_path / ("o" + "_".join(args))
        r = _cli("--urls", str(urls), "--out", str(out), *args)
        assert r.returncode == 2 and not out.exists(), args


def test_sensitive_values_are_redacted_in_manifest_summary_and_stdout(server, tmp_path):
    assert fo.redact("https://u:p@api.hsx.vn/x?pageIndex=2&token=abc&X-Amz-Signature=s") == \
        "https://api.hsx.vn/x?pageIndex=2&token=REDACTED&X-Amz-Signature=REDACTED"
    out = tmp_path / "o"
    m = _run([_e(f"{server}/cookie?pageIndex=1&access_token=bi-mat-456")], out)
    r = m["items"][0]
    assert r["ok"] and "bi-mat-456" not in r["url"] and "pageIndex=1" in r["url"]
    assert ["Set-Cookie", "REDACTED"] in r["headers"]
    for f in ("manifest.json", "summary.md"):
        text = (out / f).read_text(encoding="utf-8")
        assert "bi-mat-456" not in text and "bi-mat-123" not in text, f


def test_manifest_records_legal_status_without_claiming_permission(server, tmp_path):
    out = tmp_path / "o"
    m = _run([_e(f"{server}/doc.pdf")], out)
    assert m["legal"] == [{"host": "127.0.0.1", "legal_status": "CHUA_KIEM_DIEU_KHOAN", "terms_source": None,
                           "terms_checked_at": None, "note": fo.LEGAL_NOTE}]
    assert "CHUA_KIEM_DIEU_KHOAN" in (out / "summary.md").read_text(encoding="utf-8")


def test_smoke_list_covers_s0a_index_and_a_quarterly_report_on_approved_hosts():
    entries = fo.parse_url_list((REPO / "tools" / "fetch_originals_smoke.txt").read_text(encoding="utf-8"))
    hosts = {fo.urllib.parse.urlsplit(e["url"]).hostname for e in entries}
    assert hosts <= set(fo.ALLOW_HOSTS)
    urls = [e["url"] for e in entries]
    assert any("/n/api/v1/1/news?" in u for u in urls)               # chỉ mục công bố thông tin chung
    assert any("/m/api/v1/1/mediafiles/5/" in u for u in urls)       # danh sách BCTC theo mã
    assert any("BCTC" in u and u.endswith(".pdf") for u in urls)     # một BCTC quý


def test_workflow_does_not_print_the_raw_url_list():
    wf = (REPO / ".github" / "workflows" / "fetch_originals.yml").read_text(encoding="utf-8")
    assert 'cat "$RUNNER_TEMP/urls.txt"' not in wf


def test_slow_download_past_the_deadline_is_an_error_and_nothing_saved(server, tmp_path):
    out = tmp_path / "o"
    t0 = time.monotonic()
    r = _run([_e(f"{server}/slow")], out, deadline=0.5)["items"][0]
    assert not r["ok"] and "thời hạn" in r["error"] and r["file"] is None and r["sha256"] is None
    assert time.monotonic() - t0 < 2.5
    assert not any((out / "files").iterdir())


def test_progress_is_written_per_url_as_it_finishes(server, tmp_path, capsys):
    out = tmp_path / "o"
    m = _run([_e(f"{server}/doc.pdf"), _e(f"{server}/forbidden")], out)
    lines = [json.loads(x) for x in (out / "progress.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [x["index"] for x in lines] == [1, 2] and lines == m["items"]
    printed = capsys.readouterr().out
    assert "[1/2]" in printed and "[2/2]" in printed and "LỖI" in printed
