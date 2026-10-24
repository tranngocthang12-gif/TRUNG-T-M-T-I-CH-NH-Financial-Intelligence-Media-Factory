# Nguồn gốc (Thư viện tầng 1–2)

Mỗi tài liệu gốc nằm trong `library/sources/<doc_id>/` gồm: `text.md` (văn bản thuần, có số trang `[p12]` và số đoạn), `meta.json` (issuer, issued_on, accessed_on, source_url, legal_status, license, effective_from, effective_to, superseded_by) và được ghim trong `library/SOURCE_MANIFEST.json` bằng `sha256` + `bytes`.

Luật: chỉ tài liệu gốc công khai (văn bản quy phạm, chuẩn mực, BCTC kiểm toán, công bố cơ quan quản lý); không sửa nội dung; nguồn chưa duyệt trong `governance/DATA_SOURCES.yaml` thì không chép (L-01, L-04). Văn bản pháp lý phải có trạng thái hiệu lực (L-08). Địa chỉ trích dẫn: `<doc_id>:p<trang>:<đoạn>` hoặc `<doc_id>:t<bảng>:<dòng>`.
