# GEMINI — Phản biện hồ sơ Luật Các tổ chức tín dụng 32/2024 chỉ bằng Markdown

**Phạm vi: MD-ONLY / KHÔNG ĐƯỢC KÝ `pdf_check`.** Hồ sơ do Grok (xAI) lập; tệp điều phối này do ChatGPT (OpenAI) thêm ngày 20/11/2026. Ghế độc lập dự kiến: Gemini (Google). Không ai được nhận mình đã xem PDF chỉ vì đọc tệp Markdown hoặc báo cáo của máy.

- Repository: `tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory`
- Pull request: [#60](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/60) — DRAFT.
- **HEAD chứa bộ hồ sơ gốc đã rà cấu trúc:** `adc2d2030350d356b4e6fa18f47652266cb26861`. Tệp điều phối này là commit bổ sung sau HEAD đó; khi chấm phải dùng **HEAD mới nhất của PR**, kiểm lại SHA trên GitHub.
- Main nguồn tại thời điểm lập hồ sơ: `b59be0e1d937b3b329deecfc51f91dd0cf5eeab7` (merge #58).
- Trạng thái: `luat_tctd_32_2024 = QUEUED`; `crosscheck.pdf_check` chưa có; G1 = **1/40 SOURCED**. Không tự nâng trạng thái.

## 1. Những tệp Markdown Gemini PHẢI đọc

Các đường dẫn dưới đây trỏ đúng bản đã kiểm cấu trúc ở HEAD `adc2d2030350d356b4e6fa18f47652266cb26861`; nếu PR có commit mới, đối chiếu lại với HEAD cuối trước khi chấm.

| Tệp Markdown | Phạm vi cần kiểm |
|---|---|
| [README.md](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/blob/adc2d2030350d356b4e6fa18f47652266cb26861/reports/LUAT_TCTD_32_DOI_CHIEU_20261120/README.md) | Tài liệu nguồn, giới hạn, hướng dẫn |
| [page_map.md](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/blob/adc2d2030350d356b4e6fa18f47652266cb26861/reports/LUAT_TCTD_32_DOI_CHIEU_20261120/page_map.md) | 152 ánh xạ `text_page → part_id/pdf_page` |
| [CHECKSUMS.txt](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/blob/adc2d2030350d356b4e6fa18f47652266cb26861/reports/LUAT_TCTD_32_DOI_CHIEU_20261120/CHECKSUMS.txt) | Danh sách checksum được công bố; đây là **tuyên bố**, không phải phép kiểm byte độc lập |
| [MAY_DOC_LAI.md](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/blob/adc2d2030350d356b4e6fa18f47652266cb26861/reports/LUAT_TCTD_32_DOI_CHIEU_20261120/MAY_DOC_LAI.md) | Báo cáo máy 0 dòng lệch, **không phải MATCH độc lập** |
| [lo-01-text.md](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/blob/adc2d2030350d356b4e6fa18f47652266cb26861/reports/LUAT_TCTD_32_DOI_CHIEU_20261120/lo-01-text.md) | p1–p40: 40 trang |
| [lo-02-text.md](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/blob/adc2d2030350d356b4e6fa18f47652266cb26861/reports/LUAT_TCTD_32_DOI_CHIEU_20261120/lo-02-text.md) | p41–p80: 40 trang |
| [lo-03-text.md](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/blob/adc2d2030350d356b4e6fa18f47652266cb26861/reports/LUAT_TCTD_32_DOI_CHIEU_20261120/lo-03-text.md) | p81–p93: 13 trang; còn PDF A trang 94 **bị loại**, chưa được Gemini kiểm qua MD |
| [lo-04-text.md](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/blob/adc2d2030350d356b4e6fa18f47652266cb26861/reports/LUAT_TCTD_32_DOI_CHIEU_20261120/lo-04-text.md) | p94–p133: 40 trang; bắt đầu PDF B trang 1, Điều 132 |
| [lo-05-text.md](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/blob/adc2d2030350d356b4e6fa18f47652266cb26861/reports/LUAT_TCTD_32_DOI_CHIEU_20261120/lo-05-text.md) | p134–p152: 19 trang |
| [PHIEU_CHAM.md](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/blob/adc2d2030350d356b4e6fa18f47652266cb26861/reports/LUAT_TCTD_32_DOI_CHIEU_20261120/PHIEU_CHAM.md) | Khuôn kết luận; **không điền MATCH nếu chỉ có MD** |
| [text.md trên main](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/blob/b59be0e1d937b3b329deecfc51f91dd0cf5eeab7/library/sources/luat_tctd_32_2024/text.md) | Văn bản toàn bộ 152 trang để đối chiếu các lô |
| [SOURCE_MANIFEST.json trên main](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/blob/b59be0e1d937b3b329deecfc51f91dd0cf5eeab7/library/SOURCE_MANIFEST.json) | `original_parts`, `page_map`, `excluded_pages`, `crosscheck` |

Nếu Gemini không thể đọc các tệp liên kết ở đây, ghi chính xác những tệp đã/không mở và kết luận BLOCKED đối với phần chưa đọc. Không dùng nội dung tóm tắt này thay nội dung gốc.

## 2. Metadata cần xác minh trên Markdown và manifest

| Tệp gốc | Bytes được công bố | SHA256 được công bố | Trang |
|---|---:|---|---:|
| `cb-369-370.pdf` | 1.188.965 | `b613a8f94e1955a776035be2b7cd14dc34a76c568973f8db7367324ebf50581a` | 94 |
| `cb-371-372.pdf` | 741.096 | `67852f403c7f368989ef47f98a47933d732d3d6b9d2db40cda2a9af84b969c49` | 59 |
| `text.md` | 406.064 | `8c69c6a2b0c516e8093a22dc2bdba68a0f62944cd25d5fa83789f0863f95aa5a` | 152 |

Phải phân biệt: **so hash viết trong hai tệp Markdown ≠ tự tính lại hash từ byte PDF**. Lô `lo-*.pdf` là PDF dẫn xuất để xem trang; hash của lô không phải hash PDF gốc.

### Ánh xạ và trang loại trừ

- p1–p93 → `cb-369-370` PDF 1–93.
- p94–p152 → `cb-371-372` PDF 1–59.
- `cb-369-370` PDF trang **94** bị loại; theo hồ sơ, là trang thông tin “VĂN PHÒNG CHÍNH PHỦ XUẤT BẢN”, không phải trang trống. Thông tin này **chưa phải xác nhận bằng byte PDF gốc của Gemini**.
- Chỗ nối: p93 có dấu “Xem tiếp Công báo số 371 + 372” sau Điều 131; p94 mở tiếp Công báo và Điều 132. Kiểm thứ tự 210 điều, ngày có hiệu lực, chữ số, đơn vị/dấu, nội dung các trang trong **MD**.

## 3. Hai kết luận phải TÁCH RIÊNG

### A — Đánh giá cấu trúc / nội dung bản chép MD (Gemini có thể làm)

Kiểm tệp Markdown thật, đếm trang `[pN]`, phát hiện thiếu/trùng/tráo, kiểm mọi phần liên quan đến `page_map`, metadata và tính liên tục nội dung. Báo `MD_REVIEW_PASS`, `MD_REVIEW_FAIL`, hoặc `MD_REVIEW_BLOCKED` với cụm chữ/trang cụ thể. Đây có thể dùng để phản biện **chất lượng bộ hồ sơ PR #60**, không chứng nhận nguồn đã chép đúng PDF.

### B — Xác nhận gốc PDF / `pdf_check` (Gemini không thể làm chỉ qua MD)

`PDF_VISUAL_MATCH` đòi người/ghế **thực sự mở và đối chiếu hình ảnh đầy đủ 152 trang PDF và trang loại trừ PDF A/94**, tự kiểm hash/byte hai PDF gốc, chữ vẽ path, bảng, dấu, số, ngày, chỗ nối Điều 131→132. Chưa kiểm đủ thì ghi `PDF_VISUAL_BLOCKED`. **Không ghi MATCH, không gắn `pdf_check`, không nâng QUEUED→SOURCED** chỉ từ kết quả A.

Để đạt B, chuyển bộ PDF hiện có cho một ghế khác Grok có **quyền mở ảnh/PDF thực tế**, chẳng hạn Claude Code (Anthropic) hoặc người kiểm độc lập được Owner chỉ định. Biên bản phải ghi rõ cách truy cập, từng trang, hash và ngoại lệ. Gemini chỉ đọc MD có thể **phản biện tính nhất quán của biên bản ấy**, không trở thành người trực tiếp nhìn PDF.

## 4. Khuôn trả lời Gemini (đăng bình luận GitHub / viết tệp MD phản biện)

```text
GEMINI MD-ONLY REVIEW — PR #60 — HEAD: <FULL_SHA_MOI_NHAT>
Reviewer: Gemini (Google)
Da mo thuc te: <cac tep .md va duong dan>
MD_REVIEW: PASS | FAIL | BLOCKED
Trang/lo/metadata da kiem: <chi tiet, khong nhan da kiem neu chua mo>
Danh sach loi: <trang, doan, chu/so/dau/truong>
PDF_VISUAL: NOT_REVIEWED (khong doc duoc PDF/anh)
Original binary SHA rechecked: NO
pdf_check: NOT SIGNED
SOURCED: NOT AUTHORIZED
L-09 packet packaging verdict: GỘP ĐƯỢC | REQUEST_CHANGES | BLOCKED
Dieu kien con thieu: nguoi khac Grok kiem anh 152 trang + trang bi loai, SHA binary, sau do moi xet MATCH
```

**Phán quyết “GỘP ĐƯỢC” về cách đóng gói PR #60 nếu có không đồng nghĩa `MATCH` của Luật 32.** Chủ kho giữ quyền merge L-10; phải có bản chấm L-09 kèm SHA đúng HEAD theo `tools/review_gate.py`. Không sửa PDF gốc, văn bản nguồn, governance hay luật để qua cổng.
