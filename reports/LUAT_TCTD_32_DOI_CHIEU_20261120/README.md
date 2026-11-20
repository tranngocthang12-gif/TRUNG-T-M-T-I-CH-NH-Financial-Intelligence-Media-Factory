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

Phiếu trống: `PHIEU_CHAM.md`. Bản Markdown một tệp để tải: `GEMINI_FULL_MD_152_TRANG.md`. Bản MD-only cũ (HEAD `76a1ed9`, hash `8c69c6a2b0c516e8093a22dc2bdba68a0f62944cd25d5fa83789f0863f95aa5a`) là STALE; xem `GEMINI_MD_ONLY_REVIEW.md`.
