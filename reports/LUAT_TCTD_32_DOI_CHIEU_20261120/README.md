# Hồ sơ đối chiếu `luat_tctd_32_2024` — chờ ghế khác hãng

Bản trình bày để Gemini (Google) hoặc Claude (Anthropic) tự xem. **Không phải biên bản `pdf_check`. Không phải MATCH. Không nâng SOURCED.**

Người lập hồ sơ: Grok (xAI). Grok không phải người chấm.

## Nguồn đã ghim (không sửa byte trong hồ sơ này)

Lấy từ `main` `b59be0e1d937b3b329deecfc51f91dd0cf5eeab7` (merge PR #58). CI trên main: run `44721210174` SUCCESS. Hash dưới đây là của tệp gốc, không phải của PDF lô.

| Tệp | Bytes | SHA-256 |
|---|---:|---|
| `library/sources/luat_tctd_32_2024/cb-369-370.pdf` | 1188965 | `b613a8f94e1955a776035be2b7cd14dc34a76c568973f8db7367324ebf50581a` |
| `library/sources/luat_tctd_32_2024/cb-371-372.pdf` | 741096 | `67852f403c7f368989ef47f98a47933d732d3d6b9d2db40cda2a9af84b969c49` |
| `library/sources/luat_tctd_32_2024/text.md` | 406064 | `8c69c6a2b0c516e8093a22dc2bdba68a0f62944cd25d5fa83789f0863f95aa5a` |
| `library/SOURCE_MANIFEST.json` | 78551 | `fb2b045df6f498b04109dad7685db0e14aba3d557f6365daddf1939865d378c3` |

`text_sha256` và `sha256` của tài liệu đều là hash `text.md` ở trên. `page_count` parser strict: PDF A **94**, PDF B **59**. `page_map` **152** dòng: text 1–93 → `cb-369-370` PDF 1–93; text 94–152 → `cb-371-372` PDF 1–59. Không thiếu, không trùng, không nhảy.

## Trang loại trừ

PDF A trang 94 không có trong `text.md`. Ảnh render: `trang-loai-tru-cb-369-370-p94.png`. Chữ vẽ bằng path (trang in Văn phòng Chính phủ xuất bản: Số 1 Hoàng Hoa Thám, `congbao@chinhphu.vn`). Không phải điều khoản. Điều 131 nằm ở PDF A trang 93. Lý do trong manifest giữ nguyên.

## Cách xem từng trang

PDF `lo-*.pdf` là **lát cắt trình bày** (pypdf thêm trang từ bản gốc). Hash của chúng khác hash gốc và không được ghi vào manifest. Mỗi lô ≤ 40 trang PDF.

| Lô | text.md | PDF gốc | Tệp |
|---|---|---|---|
| lo-01 | 1–40 | `cb-369-370` trang 1–40 | `lo-01.pdf` + `lo-01-text.md` |
| lo-02 | 41–80 | `cb-369-370` trang 41–80 | `lo-02.pdf` + `lo-02-text.md` |
| lo-03 | 81–93 | `cb-369-370` trang 81–93, kèm trang 94 loại trừ ở cuối | `lo-03.pdf` + `lo-03-text.md` |
| lo-04 | 94–133 | `cb-371-372` trang 1–40 | `lo-04.pdf` + `lo-04-text.md` |
| lo-05 | 134–152 | `cb-371-372` trang 41–59 | `lo-05.pdf` + `lo-05-text.md` |

Bảng đủ 152 dòng: `page_map.md`. Hash các tệp hồ sơ: `CHECKSUMS.txt`.

## Việc ghế chấm phải làm

Đọc **cả 152 trang** chữ trong `text.md` cạnh đúng trang PDF, cộng trang PDF A/94. Kiểm chữ, số, dấu âm, ngày hiệu lực, chỗ ngắt Điều 131 (hết PDF A trang 93) sang Điều 132 (PDF B trang 1). `text.md` không có mốc `[tN]`; nếu PDF có bảng thì bảng đang là từng dòng chữ — ghế chấm phải nhìn trang, không tin máy đã thấy bảng.

Điền `PHIEU_CHAM.md` (hoặc bình luận PR) với tên ghế, HEAD, ba hash gốc, danh sách trang đã xem, và MATCH hoặc BLOCKED/MISMATCH kèm trang và cụm chữ. Thiếu trang thì BLOCKED. Không nhờ Grok điền hộ.

## Những gì máy đã làm — không phải MATCH

Xem `MAY_DOC_LAI.md`. Tóm tắt: đọc lại lớp chữ của 152 trang đã ánh xạ, 0 dòng lệch so với `text.md`; PDF A trang 94 không có toán tử chữ. Cùng họ công cụ đã tạo `text.md`, không thấy chữ vẽ bằng path. Grok chỉ mở ảnh bốn trang (text 1, text 93, text 94, PDF A/94) để kiểm hồ sơ mở được. **Chưa có ghế độc lập. G1 vẫn 1/40 SOURCED** (`luat_ke_toan_88_2015`). `luat_tctd_32_2024` vẫn QUEUED, không `pdf_check`. ADR-0014 không sửa trong hồ sơ này.
