"""P0-3: công cụ tải bản gốc (tools/fetch_originals.py). Máy chủ HTTP cục bộ trên 127.0.0.1, không ra mạng ngoài,
không ghi vào kho. Hàm lõi được gọi với scheme http cho máy chủ cục bộ; đường CLI chỉ nhận https và được kiểm riêng."""
from __future__ import annotations

import hashlib
import http.server
import json
import pathlib
import shutil
import subprocess
import sys
import threading

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from tools import fetch_originals as fo   # noqa: E402

PDF = b"%PDF-1.4 ban goc gia lap " + bytes(range(256))
BIG = b"x" * 5000


class _H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        p = self.path
        if p.startswith("/doc.pdf"):
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
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def _run(entries, out, **kw):
    return fo.fetch_all(entries, out, allow_schemes=("http",), timeout=10, **kw)


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
