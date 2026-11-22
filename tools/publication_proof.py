"""Máy kiểm chứng cứ ngày công bố của bản gốc HOSE (QĐ-9, ADR-0016). Chỉ đọc tệp đã ghim, không gọi mạng, không ghi gì.

QĐ-9: ngày HOSE đăng tin được ghi vào `published_at` kể cả khi trùng ngày ký văn bản, khi máy kiểm được ngày đó từ metadata
HOSE đã ghim. Ngày gõ tay, hay suy từ ngày ký, tên tệp, ngày hưởng quyền, vẫn bị từ chối.

`proof_errors(doc, root)` trả danh sách lỗi (rỗng là đạt) cho MỘT bản gốc có `published_at`. Bản gốc đạt khi đủ cả:
  1. tệp tin HOSE (JSON) tồn tại và khớp sha256 ghi trong manifest;
  2. id của tin trong JSON bằng số trong `source_id` (và mã trong JSON bằng `ticker`);
  3. `published_at` bằng đúng `data.postedDate` đổi sang ISO 8601 theo UTC, không gắn múi giờ;
  4. tệp danh sách đính kèm tồn tại, khớp sha256, và có đúng một tệp đính kèm với `filePath` trùng `url` của bản gốc;
  5. ngày của `published_at` không sớm hơn `signed_date`;
  6. ngày của (`published_at` + 7 giờ) sớm hơn `official_ex_date`. Lý do: chưa rõ múi giờ của `postedDate`; lấy cách đọc
     muộn hơn (giờ Việt Nam nếu giá trị là UTC thật) cho an toàn.
Bản gốc không có `published_at` thì không có gì để chứng minh: trả danh sách rỗng (trạng thái kiểm ở nơi gọi).

Trường chứng cứ theo lược đồ manifest:
  - EVIDENCE_MANIFEST_2026H2.json và EVIDENCE_MANIFEST_VN30_BO_SUNG.json: `publication_evidence`,
    `publication_evidence_sha256`, `publication_media_evidence`, `publication_media_sha256`;
  - EVIDENCE_MANIFEST.json: `published_at_evidence` = {path, sha256, field, accessed_at, media_path, media_sha256}.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import urllib.parse

SHIFT = dt.timedelta(hours=7)


def posted_iso(seconds) -> str:
    """Giây Unix → ISO 8601 theo phép đổi chuẩn của Unix (UTC), không gắn múi giờ."""
    return dt.datetime.fromtimestamp(seconds, dt.timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")


def evidence_fields(doc) -> tuple:
    """(đường dẫn JSON tin, sha256 khai, đường dẫn JSON đính kèm, sha256 khai) theo lược đồ của bản gốc."""
    if "publication_evidence" in doc:
        return (doc.get("publication_evidence"), doc.get("publication_evidence_sha256"),
                doc.get("publication_media_evidence"), doc.get("publication_media_sha256"))
    ev = doc.get("published_at_evidence")
    ev = ev if isinstance(ev, dict) else {}
    return ev.get("path"), ev.get("sha256"), ev.get("media_path"), ev.get("media_sha256")


def _pinned(root, rel, sha, what, pdf_path):
    """(bytes, lỗi) của một tệp chứng cứ đã ghim."""
    if not isinstance(rel, str) or not rel.strip():
        return None, f"thiếu đường dẫn {what}"
    if rel == pdf_path:
        return None, f"{what} trỏ vào chính bản gốc PDF"
    p = pathlib.Path(root) / rel
    if not p.is_file():
        return None, f"không có tệp {what} {rel}"
    blob = p.read_bytes()
    if not isinstance(sha, str) or hashlib.sha256(blob).hexdigest() != sha:
        return None, f"sha256 của {what} {rel} không khớp manifest"
    return blob, None


def proof_errors(doc, root) -> list[str]:
    pub = doc.get("published_at")
    if pub is None:
        return []
    sid = str(doc.get("source_id"))
    errors = []
    news_rel, news_sha, media_rel, media_sha = evidence_fields(doc)
    news_blob, err = _pinned(root, news_rel, news_sha, "JSON tin HOSE", doc.get("path"))
    if err:
        errors.append(f"{sid}: {err}")
    media_blob, err = _pinned(root, media_rel, media_sha, "JSON danh sách đính kèm", doc.get("path"))
    if err:
        errors.append(f"{sid}: {err}")
    if news_blob is not None:
        try:
            news = json.loads(news_blob)["data"]
        except (ValueError, KeyError, TypeError):
            news = None
            errors.append(f"{sid}: JSON tin HOSE hỏng")
        if news is not None:
            nid = sid.split("-", 1)[1] if sid.startswith("hose-") else None
            if str(news.get("id")) != nid:
                errors.append(f"{sid}: JSON tin có id {news.get('id')}, khác số trong source_id")
            if news.get("code") != doc.get("ticker"):
                errors.append(f"{sid}: JSON tin có mã {news.get('code')}, khác ticker {doc.get('ticker')}")
            posted = news.get("postedDate")
            if isinstance(posted, bool) or not isinstance(posted, int):
                errors.append(f"{sid}: JSON tin không có data.postedDate dạng số")
            elif pub != posted_iso(posted):
                errors.append(f"{sid}: published_at {pub!r} khác data.postedDate đổi theo UTC {posted_iso(posted)!r}")
    if media_blob is not None:
        try:
            files = json.loads(media_blob)["data"]["list"]
            paths = [str(m.get("filePath", "")).replace("~", "", 1) for m in files]
        except (ValueError, KeyError, TypeError, AttributeError):
            paths = None
            errors.append(f"{sid}: JSON danh sách đính kèm hỏng")
        want = urllib.parse.unquote(str(doc.get("url", "")).split("staticfile.hsx.vn", 1)[-1])
        if paths is not None and paths.count(want) != 1:
            errors.append(f"{sid}: danh sách đính kèm không có đúng một tệp trùng url của bản gốc")
    try:
        when = dt.datetime.fromisoformat(str(pub))
    except ValueError:
        return errors + [f"{sid}: published_at {pub!r} không phải ISO 8601"]
    if when.tzinfo is not None:
        errors.append(f"{sid}: published_at không được gắn múi giờ")
    signed, ex = doc.get("signed_date"), doc.get("official_ex_date")
    if not isinstance(signed, str) or when.date().isoformat() < signed:
        errors.append(f"{sid}: ngày đăng {when.date()} sớm hơn ngày ký {signed}")
    if not isinstance(ex, str) or (when + SHIFT).date().isoformat() >= ex:
        errors.append(f"{sid}: ngày đăng cộng 7 giờ ({(when + SHIFT).date()}) không sớm hơn ngày không hưởng quyền {ex}")
    return errors
