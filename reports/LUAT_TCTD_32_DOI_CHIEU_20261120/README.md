# Hồ sơ đối chiếu `luat_tctd_32_2024` — đóng lại sau PR #62

Bản trình bày để ghế khác Grok tự xem. **Không phải `pdf_check`. Không phải MATCH. Không nâng SOURCED.**

Người lập: Grok (xAI). Grok không phải người chấm.

## Nguồn hiện hành

Main `517f55024b2220b690e65191ee52c95c97d3be1c` (merge PR #62). CI main lúc merge #62 không được dùng thay CI của HEAD PR #60 này.

| Tệp | Bytes | SHA-256 | Vai trò |
|---|---:|---|---|
| `library/sources/luat_tctd_32_2024/cb-369-370.pdf` | 1188965 | `b613a8f94e1955a776035be2b7cd14dc34a76c568973f8db7367324ebf50581a` | VERIFIED, không đổi |
| `library/sources/luat_tctd_32_2024/cb-371-372.pdf` | 741096 | `67852f403c7f368989ef47f98a47933d732d3d6b9d2db40cda2a9af84b969c49` | VERIFIED, không đổi |
| `library/sources/luat_tctd_32_2024/text.md` | 406070 | `bd639d7951f68b6d41d502cb84a7fca53fe0490706c2aa8b84dd7b2b21961d44` | VERIFIED, bản sau bốn lỗi đã sửa |
| `library/SOURCE_MANIFEST.json` | 78551 | `9669c60a9c0e4599107a06eb034929382d6fb2356960fc12f5faa5e384c3a0dc` | VERIFIED lúc đóng gói |
| text.md cũ | 406064 | `8c69c6a2b0c516e8093a22dc2bdba68a0f62944cd25d5fa83789f0863f95aa5a` | **STALE** — hồ sơ PR #60 trước commit này |

`page_count` strict: PDF A 94, PDF B 59. `page_map` 152 dòng: text 1–93 → `cb-369-370` PDF 1–93; text 94–152 → `cb-371-372` PDF 1–59. `pdf_check` không có. Hàng đợi QUEUED. G1 vẫn 1/40 SOURCED.

## Trang loại trừ

PDF A trang 94 không nằm trong `text.md`. Ảnh: `trang-loai-tru-cb-369-370-p94.png`. Lý do manifest giữ nguyên (trang in Văn phòng Chính phủ xuất bản).

## Năm lô

PDF `lo-*.pdf` là lát cắt trình bày từ hai PDF gốc (byte gốc không đổi nên lát cắt không dựng lại). Hash lát cắt không phải hash gốc. Mỗi lô PDF ≤ 40 trang.

| Lô | text.md | PDF gốc | Tệp |
|---|---|---|---|
| lo-01 | 1–40 | `cb-369-370` 1–40 | `lo-01.pdf` + `lo-01-text.md` |
| lo-02 | 41–80 | `cb-369-370` 41–80 | `lo-02.pdf` + `lo-02-text.md` |
| lo-03 | 81–93 | `cb-369-370` 81–93, kèm trang 94 loại trừ ở cuối | `lo-03.pdf` + `lo-03-text.md` |
| lo-04 | 94–133 | `cb-371-372` 1–40 | `lo-04.pdf` + `lo-04-text.md` |
| lo-05 | 134–152 | `cb-371-372` 41–59 | `lo-05.pdf` + `lo-05-text.md` |

Bốn chỗ đã sửa trong text.md và trong lô: `[p9]` ngoặc kép, `[p81]` "Thực hiện", `[p83]` "kiều hối", `[p134]` "nghĩa vụ".

## Kiểm text-vs-text

Đã so từng khối `[p1]`…`[p152]` trong năm tệp lô với đúng lát `text.md` mới: **text-vs-text PASS**. Đây không phải đối chiếu ảnh PDF.

## PDF còn BLOCKED

Ghế khác Grok phải mở hai PDF gốc (hash ở trên), năm lát `lo-*.pdf`, và ảnh trang 94, rồi so **152 trang text + PDF A/94**. Chưa có người đó trong phiên này. Không dùng text-vs-text để ký `pdf_check`.

Phiếu trống: `PHIEU_CHAM.md`. Bảng 152 trang cộng PDF A/94, mọi ô để trống: `BANG_TRANG_CHO_CHAM.md`. Grok không đánh dấu đã mở. Bản Markdown một tệp để tải: `GEMINI_FULL_MD_152_TRANG.md`. Bản MD-only cũ (HEAD `76a1ed9`, hash `8c69c6a2b0c516e8093a22dc2bdba68a0f62944cd25d5fa83789f0863f95aa5a`) là STALE; xem `GEMINI_MD_ONLY_REVIEW.md`.

## Cập nhật sau bàn giao — 2026-11-20

Mục này bổ sung, không viết lại các đoạn lịch sử phía trên. Các nhãn tách riêng, không được gộp thành MATCH hoặc SOURCED.

| Nhãn | Giá trị | Nguồn |
|---|---|---|
| `MD_REVIEW` | `PASS` | Owner chuyển tiếp kết luận Gemini (Google). Bình luận GitHub [7040130725](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/60#issuecomment-7040130725). Phạm vi: Markdown, HEAD `70f195c4ccae0eff20586ac55f10acb4815500d9`. Đủ `[p1]`–`[p152]`; lô 05 đủ `[p134]`–`[p152]`; `[p145]` không bị cắt; đủ bảy trang cuối. Không sửa byte `text.md` hay PDF. **Không phải** `PDF_VISUAL_MATCH`. |
| `PDF_VISUAL` | `CLAUDE_REPORTED_MATCH` | Claude (Anthropic) báo đã đọc 152 trang text + PDF A/94 và bàn giao bốn tệp. ChatGPT đã đọc bốn tệp từ máy Owner và công bố SHA tại [7040305665](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/60#issuecomment-7040305665). Grok không có byte bốn tệp trong kho. |
| `INDEPENDENT_PDF_VISUAL_L09` | `PENDING` | Chưa có ghế khác hãng người viết mở ảnh PDF và chấm lại trên HEAD mới. |
| `pdf_check` | `NOT_COMMITTED` | Không ghi vào `SOURCE_MANIFEST.json`. |
| `luat_tctd_32_2024` | `QUEUED` | Không nâng. |
| `SOURCED` | `1/40` | Không đổi. |

Bốn tệp Claude: `EVIDENCE_PENDING`. Grok không tạo lại nội dung và không coi biên bản ChatGPT là bản gốc. Chi tiết: `TRANG_THAI_CHUNG_CU.md`.

Lệch 11/12 trang: `DISCREPANCY_OPEN`. Báo cáo tổng hợp ghi 12 trang xem lại ở 300 dpi; phiếu và bảng chi tiết liệt kê 11 trang (A31, A42, B5, B11, B17, B21, B31, B55, B57, B58, B59). Không tự sửa chứng cứ Claude. Chờ Claude xuất bản đính chính kèm SHA hoặc nhật ký trang thứ 12.

`PHIEU_CHAM.md` và `BANG_TRANG_CHO_CHAM.md` vẫn là mẫu trống của Grok. Không chép bảng Claude vào đó.

`reviewed_by` trên mô tả PR đang có tên ChatGPT. Đó không phải phê duyệt L-09 toàn diện. Grok không đổi trường này. Owner xử lý theo quy trình; L-09 vẫn đỏ cho đến khi có người chấm đúng HEAD mới.
