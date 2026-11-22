"""Bằng chứng quyền VCB, TCB, FPT: chỉ đọc manifest và chạy công cụ. Không ghi kho."""
import hashlib
import json
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "evidence" / "corporate_actions" / "EVIDENCE_MANIFEST.json"
REPORT = ROOT / "reports" / "CORPORATE_ACTION_EVIDENCE_20261119.md"
TOOL = ROOT / "tools" / "corporate_action_evidence.py"


def _docs():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["source_documents"]


class CorporateActionEvidenceTests(unittest.TestCase):
    def test_manifest_files_and_ex_date(self):
        docs = _docs()
        self.assertGreaterEqual(len(docs), 3)
        tickers = set()
        for doc in docs:
            for key in ("source_id", "url", "issuer", "published_at", "accessed_at",
                        "effective_date", "path", "sha256", "bytes", "ticker",
                        "event_type", "official_ex_date", "official_ratio"):
                self.assertIn(key, doc)
            self.assertRegex(doc["official_ex_date"], r"^\d{4}-\d{2}-\d{2}$")
            path = ROOT / doc["path"]
            self.assertTrue(path.is_file(), doc["path"])
            blob = path.read_bytes()
            self.assertEqual(len(blob), doc["bytes"])
            self.assertEqual(hashlib.sha256(blob).hexdigest(), doc["sha256"])
            tickers.add(doc["ticker"])
        self.assertEqual(tickers, {"VCB", "TCB", "FPT"})

    def test_tool_same_hash_twice(self):
        hashes = []
        for _ in range(2):
            with tempfile.NamedTemporaryFile(prefix="ca-evidence-", suffix=".md") as handle:
                out = handle.name
            proc = subprocess.run(
                ["python", str(TOOL), "--out", out],
                cwd=ROOT, check=False, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            blob = pathlib.Path(out).read_bytes()
            pathlib.Path(out).unlink()
            hashes.append(hashlib.sha256(blob).hexdigest())
        self.assertEqual(hashes[0], hashes[1])

    def test_tool_does_not_write_store_or_engine(self):
        before = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            out = str(pathlib.Path(tmp) / "report.md")
            proc = subprocess.run(
                ["python", str(TOOL), "--out", out],
                cwd=ROOT, check=False, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
        after = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
        self.assertEqual(before, after)

    def test_report_has_three_events_and_sections(self):
        text = REPORT.read_text(encoding="utf-8")
        for ticker in ("VCB", "TCB", "FPT"):
            self.assertIn(ticker, text)
        for mark in ("(a)", "(b)", "(c)", "(d)"):
            self.assertIn(mark, text)
        self.assertTrue("CHƯA ĐỦ BẰNG CHỨNG" in text or "ngày giao dịch không hưởng quyền" in text)


# --- Phân biệt ngày ký với ngày công bố, loại sự kiện nguồn với loại kỹ thuật (lệnh Owner 19/11/2026, sửa hẹp PR #54) ---
# Ánh xạ loại nguồn → loại kỹ thuật chỉ được coi là khớp nguyên văn khi văn bản ghi đúng loại đó. Cổ phiếu thưởng (phát hành
# tăng vốn từ nguồn vốn chủ sở hữu) KHÔNG phải cổ tức bằng cổ phiếu dù công thức điều chỉnh giá tương đương.
EXACT_MAP = {"CO_TUC_BANG_CO_PHIEU": "stock_dividend"}
DATE_RE = r"^\d{4}-\d{2}-\d{2}$"


class EvidenceSemanticsTests(unittest.TestCase):
    def test_signed_date_is_recorded_separately_from_publication(self):
        for doc in _docs():
            self.assertRegex(doc.get("signed_date") or "", DATE_RE, doc["source_id"])
            self.assertTrue(doc.get("signed_date_basis"), doc["source_id"])

    def test_published_at_needs_hose_publication_evidence(self):
        """published_at chỉ được điền khi tools/publication_proof.proof_errors kiểm được ngày đó từ metadata HOSE đã ghim (QĐ-9,
        ADR-0016): JSON tin và JSON danh sách đính kèm (đường dẫn + sha256), không suy từ ngày ký hay tên tệp. Chưa có thì
        published_at = null và published_at_status = CHUA_XAC_MINH."""
        import sys
        sys.path.insert(0, str(ROOT))
        from tools.publication_proof import proof_errors

        for doc in _docs():
            sid = doc["source_id"]
            self.assertIn(doc.get("published_at_status"), ("DA_XAC_MINH", "CHUA_XAC_MINH"), sid)
            if doc["published_at"] is None:
                self.assertEqual(doc["published_at_status"], "CHUA_XAC_MINH", sid)
                self.assertTrue(doc.get("published_at_note"), sid)
                continue
            self.assertEqual(doc["published_at_status"], "DA_XAC_MINH", sid)
            ev = doc.get("published_at_evidence") or {}
            for key in ("path", "sha256", "field", "accessed_at", "media_path", "media_sha256"):
                self.assertIn(key, ev, sid)
            for path_key, sha_key in (("path", "sha256"), ("media_path", "media_sha256")):
                blob = (ROOT / ev[path_key]).read_bytes()
                self.assertEqual(hashlib.sha256(blob).hexdigest(), ev[sha_key], sid)
                self.assertNotEqual(ev[path_key], doc["path"], f"{sid}: ngày công bố không lấy từ chính văn bản")
            self.assertEqual(proof_errors(doc, ROOT), [], sid)
            bad = {**doc, "published_at": doc["signed_date"]}
            self.assertTrue(proof_errors(bad, ROOT), f"{sid}: ngày ký gõ tay phải bị từ chối")

    def test_source_event_class_is_separate_from_technical_type(self):
        for doc in _docs():
            sid = doc["source_id"]
            for key in ("source_event_text", "source_event_class", "technical_event_type", "technical_mapping_status",
                        "technical_mapping_note"):
                self.assertTrue(doc.get(key), f"{sid}: thiếu {key}")
            status = doc["technical_mapping_status"]
            self.assertIn(status, ("KHOP_NGUYEN_VAN", "CHUA_XAC_MINH"), sid)
            if status == "KHOP_NGUYEN_VAN":
                self.assertEqual(EXACT_MAP.get(doc["source_event_class"]), doc["technical_event_type"], sid)
                self.assertEqual(doc["event_type"], doc["technical_event_type"], sid)
            else:
                # `event_type` là trường cổng verified-adjusted đọc: ánh xạ chưa xác minh không được đặt vào đó.
                self.assertIsNone(doc["event_type"], sid)

    def test_bonus_issue_is_not_mapped_as_verified_stock_dividend(self):
        for doc in _docs():
            if "tăng vốn cổ phần từ nguồn vốn chủ sở hữu" in doc["source_event_text"]:
                self.assertNotEqual(doc["source_event_class"], "CO_TUC_BANG_CO_PHIEU", doc["source_id"])
                self.assertEqual(doc["technical_mapping_status"], "CHUA_XAC_MINH", doc["source_id"])

    def test_verified_gate_cannot_use_unverified_publication_or_mapping(self):
        """Dựng chuỗi giá tổng hợp khớp đúng từng văn bản (ngày, tỷ lệ, loại stock_dividend, bước gãy thật) rồi chạy cổng
        verified-adjusted với manifest thật. Lớp của bản gốc do bảng đóng trong engine quyết định (ADR-0016 QĐ-2, QĐ-2a),
        không theo technical_mapping_status. Với từng bản gốc:
        - nguyên trạng: DA_KIEM_CHUNG khi và chỉ khi có published_at và lớp STOCK; ngoài ra không được xác minh, không vào chuỗi;
        - chỉ bổ sung published_at: DA_KIEM_CHUNG khi và chỉ khi lớp STOCK; ngoài ra trạng thái cách ly;
        - đối chứng âm 1: bỏ published_at thì không được xác minh;
        - đối chứng âm 2: event_type trống, nguyên văn loại ngoài bảng (phát hành quyền mua), có published_at → LOAI_CHUA_ANH_XA;
        - đối chứng dương: event_type stock_dividend và có published_at thì cổng xác minh được (lỗi nằm đúng ở các trường trên)."""
        import sys
        sys.path.insert(0, str(ROOT))
        import numpy as np
        import pandas as pd
        from engine import adjust, verified_adjust as va

        rights = "phát hành cổ phiếu cho cổ đông hiện hữu theo phương thức thực hiện quyền mua"
        for doc in _docs():
            sid = doc["source_id"]
            off = pd.Timestamp(doc["official_ex_date"])
            idx = pd.bdate_range(end=off + pd.Timedelta(days=40), periods=320)
            pos = int(idx.searchsorted(off))
            close = pd.DataFrame(100.0, index=idx, columns=[doc["ticker"]])
            close = close.mul(np.where(np.arange(len(idx)) % 2 == 0, 1.002, 0.998), axis=0)
            close.iloc[pos:] = close.iloc[pos:] / float(doc["official_ratio"])
            obs = pd.DataFrame(pd.Timestamp("2000-01-01"), index=idx, columns=close.columns)
            manual = pd.DataFrame([{"ticker": doc["ticker"], "ex_date": off, "type": "stock_dividend",
                                    "ratio": float(doc["official_ratio"]), "cash_per_share": np.nan, "source": "manual",
                                    "source_status": "CAN_DOI_CHIEU", "note": ""}], columns=adjust.EV_COLS)
            events = adjust.build_events(close, obs, manual, pd.DataFrame(columns=adjust.EV_COLS))
            self.assertEqual(events.status.tolist(), ["APPLIED"], sid)

            def run(d):
                ev = va.verify_events(events, close, [d], evidence_root=ROOT, as_of=idx[-1])
                return ev.verify_state.iloc[0], bool(ev.in_verified_chain.iloc[0]), ev.verify_reason.iloc[0]

            stock = va._doc_class(doc)[0] == "STOCK"
            pub = str((off - pd.Timedelta(days=6)).date())
            # Bản gốc nguyên trạng.
            state, chain, why = run(doc)
            if doc.get("published_at") and stock:
                self.assertEqual(state, va.OK, f"{sid}: {why}")
            else:
                self.assertNotEqual(state, va.OK, f"{sid}: {why}")
                self.assertFalse(chain, sid)
            # Chỉ bổ sung ngày công bố, giữ nguyên loại và nguyên văn của manifest.
            state, chain, why = run({**doc, "published_at": pub})
            if stock:
                self.assertEqual(state, va.OK, f"{sid}: {why}")
            else:
                self.assertTrue(state.startswith(va.Q), f"{sid}: {state}")
                self.assertFalse(chain, sid)
            # Đối chứng âm 1: thiếu ngày công bố.
            state, chain, why = run({**doc, "published_at": None})
            self.assertNotEqual(state, va.OK, f"{sid}: {why}")
            self.assertFalse(chain, sid)
            # Đối chứng âm 2: loại chưa ánh xạ.
            unmapped = {**doc, "event_type": None, "event_type_verbatim": rights, "source_event_text": rights,
                        "published_at": pub}
            state, chain, why = run(unmapped)
            self.assertEqual(state, va.Q + "LOAI_CHUA_ANH_XA", f"{sid}: {why}")
            self.assertFalse(chain, sid)
            # Đối chứng dương.
            control = {**doc, "event_type": "stock_dividend", "published_at": pub}
            state, chain, why = run(control)
            self.assertEqual(state, va.OK, f"đối chứng {sid}: {why}")

    def test_report_is_regenerated_from_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "report.md"
            proc = subprocess.run(["python", str(TOOL), "--out", str(out)], cwd=ROOT, check=False,
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(out.read_bytes(), REPORT.read_bytes(), "báo cáo đã commit lệch đầu ra của công cụ")

    def test_report_states_publication_and_mapping_status(self):
        text = REPORT.read_text(encoding="utf-8")
        for doc in _docs():
            line = next(l for l in text.splitlines() if l.startswith(f"- {doc['ticker']} ({doc['source_id']})"))
            self.assertIn(f"ngày ký {doc['signed_date']}", line)
            self.assertIn("ngày công bố CHƯA XÁC MINH" if doc["published_at"] is None
                          else f"ngày công bố {doc['published_at']}", line)
            self.assertIn(f"loại theo văn bản {doc['source_event_class']}", line)
            self.assertIn(f"ánh xạ kỹ thuật {doc['technical_event_type']} ({doc['technical_mapping_status']})", line)


if __name__ == "__main__":
    unittest.main()
