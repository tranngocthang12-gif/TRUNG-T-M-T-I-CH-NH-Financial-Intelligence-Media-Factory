# ADR — Bản ghi quyết định kiến trúc

Theo L-07: chỉ `architecture/ARCHITECTURE.md` có hiệu lực; mọi thay đổi kiến trúc đi qua một ADR ở đây, không viết bản kiến trúc mới khi bản hiện hành chưa vận hành ≥ 30 ngày.

Mẫu tệp `ADR-NNNN-<slug>.md`:

```markdown
# ADR-NNNN: <tên quyết định>
- Ngày: YYYY-MM-DD
- Trạng thái: PROPOSED | ACCEPTED | SUPERSEDED by ADR-MMMM | REVERTED
- Người đề xuất: <ghế>
- Người chấm: <ghế khác nhà cung cấp>
- Owner duyệt: <ngày, nơi ghi: PR/Issue>

## Quyết định
## Lý do (bằng chứng, số đo)
## Điều kiện hoàn tác (đo được, có hạn)
## Ảnh hưởng tới ARCHITECTURE.md (mục nào đổi)
```

## Danh mục
| ADR | Tên | Trạng thái |
|---|---|---|
| ADR-0001 | Hợp nhất sáu bản kiến trúc thành ARCHITECTURE.md v3.0 | ACCEPTED 24/10/2026 (PR #3) |
| ADR-0002 | Không thu hẹp v3.0; dự báo là việc dài hạn; phạm vi phép thử A–B | ACCEPTED 17/11/2026 (PR #29) |
| ADR-0003 | Phân định dự báo qua Issue, chấm A–B, luật vào máy kiểm, engine hằng tuần | ACCEPTED 17/11/2026 (PR #28) |
| ADR-0004 | Đóng bốn việc tồn sau gộp PR #28 | ACCEPTED 17/11/2026 (PR #29) |
| ADR-0005 | Tạm gác "engine cờ kinh tế" (engine kịch bản) | ACCEPTED 17/11/2026 (PR #29); điều kiện mở lại sửa bởi ADR-0007 |
| ADR-0006 | Kho giá ghi tăng dần (C2) | ACCEPTED 17/11/2026 (PR #30) |
| ADR-0007 | Hai góp ý sau gộp PR #29: điều kiện mở lại engine kịch bản; tên khóa bất đồng | ACCEPTED 17/11/2026 (PR #30) |
| ADR-0008 | Thiên lệch sống sót, ngày công bố BCTC, khóa biên độ trong giấy, sụt giảm lớn nhất | ACCEPTED 18/11/2026. Căn cứ: Owner gộp PR #31, merge `8c4fd4305b8154adda2ea0e1abf4e43cd7b647ab`. Không viện bản disclosure của PR #32 |
| ADR-0009 | Phiên bản và nguồn gốc giá dẫn xuất, không sửa raw ADR-0006 | ACCEPTED 18/11/2026. PR #32 đưa chính tệp này lên main (merge `432f456`); L-09 `GỘP ĐƯỢC — commit c4d8a03`, người viết ChatGPT (OpenAI), người chấm Grok (xAI); hai job L-09 success. Điều 7 chưa đổi engine |
| ADR-0010 | Lập ghế thi công là Grok (xAI); sửa lệch giấy tờ | ACCEPTED 18/11/2026 (PR #35, merge `400de5775f6d832ff453ccc2d88c91eb35936d1a`; L-09 trên `de9e682`) |
| ADR-0011 | Khóa nhận dự báo theo ngày thông tin có thể công bố | ACCEPTED 19/11/2026 giờ Việt Nam ([PR #45](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/45), merge `cb931b44274eec4f2cbc104230c9fcae17b526a4`; [L-09](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/45#issuecomment-6986598442) trên `7078dc50b2c3988b08338c6c31ae8d31271642a3`, Gemini (Google)) |
| ADR-0012 | Ghim tệp gốc riêng khỏi text.md; SOURCED chỉ sau đối chiếu từng trang | ACCEPTED 19/11/2026 giờ Việt Nam ([PR #46](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/46), merge `8f0174cd5c08257277579d44437a4f43e0ce9f8b`; [L-09](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/46#issuecomment-6985573601) trên `cedbbc784586402c92d0b4adb26974648872dba0`, ChatGPT (OpenAI)) |
| ADR-0013 | Đồng bộ §8 sau sáu dự báo; phân quyền; ruleset L-09; phạm vi A/B; mốc sáu tháng | ACCEPTED 18/11/2026 giờ Việt Nam ([PR #47](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/47), merge `fc8077cf2f892dc1093b5bb26312db90886d339e`; [L-09](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/47#issuecomment-6984297276) trên `563f689e23b99c471d188c89df7194a14b34e599`, ChatGPT (OpenAI)) |
| ADR-0014 | Nhiều tệp gốc cho một tài liệu; không nối PDF làm original | PROPOSED 20/11/2026 — chưa chấm, chưa gộp, chưa hiệu lực trên main |
| ADR-0015 | Khuôn kiểm chứng lợi thế đầu tư AI và lộ trình có cổng | PROPOSED 21/11/2026 — văn bản PR #68; chưa hiệu lực |
| ADR-0016 | Đường từ dữ liệu tới vốn: quyết định Owner QĐ-1…QĐ-11a (gồm QĐ-2a, QĐ-5a, QĐ-11a), tiêu chí số của thang vốn, giao thức FWD-001 và phần làm rõ, điều kiện dừng | ACCEPTED 21/11/2026, hiệu lực khi Owner gộp PR này (#75). Văn bản: [PR #73](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/73), merge `b75250184b553560a0ea31c909766a1f11f1a6f3`; [L-09](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/73#issuecomment-7061811768) trên `cee8e98d7ff92c724260c79e7c6526f115219702`, ChatGPT (OpenAI). QĐ-1…QĐ-8 và QĐ-2a ACCEPTED 21/11/2026; QĐ-9, QĐ-5a, QĐ-10, QĐ-11, QĐ-11a ACCEPTED 22/11/2026 (Owner) |
| ADR-0017 | Sổ chấm nhanh SCN-001 — dự báo chỉ tiêu doanh nghiệp tự chấm theo bản gốc, lớp đọc phủ, cổng cấp tín hiệu | ACCEPTED 21/11/2026, hiệu lực khi Owner gộp PR này (#75). Văn bản: [PR #74](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/74), merge `c1ca046dc7bc8e8f51b7e08bb7cbc08ccb0ba9b3`; [L-09](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/74#issuecomment-7062394688) trên `fe9b7cadabd8fd97f9959eb65026a9420b73544a`, ChatGPT (OpenAI). QĐ-S1…QĐ-S9 ACCEPTED 21/11/2026 (Owner) |
| ADR-0018 | Cột dừng/đảo 3 tuần của G0: Owner không áp cột «quá 3 tuần → chỉ giữ Ledger»; giữ các điều kiện dừng đo được | QĐ-G0 ACCEPTED 22/11/2026 (Owner), hiệu lực khi Owner gộp PR này |
| ADR-0019 | Đổi phạm vi: phân tích một mã cổ phiếu và kỷ luật đầu tư; ngừng phần đo của ADR-0002, 0013, 0016, 0017 | ACCEPTED 23/11/2026 (Owner), hiệu lực khi Owner gộp PR này |
| ADR-0020 | Ghế phân tích của dự án và phiếu máy cho hồ sơ mã; sửa thứ tự thi công của ADR-0019 QĐ-P14 | ACCEPTED 24/11/2026 (Owner), hiệu lực khi Owner gộp PR này |
| ADR-0021 | Số SUY LUẬN gắn đúng khóa sổ, bảng định nghĩa, mục Trạng thái kiểm, ba số Owner tự mở do máy chọn, niêm phong bản đã giao | ACCEPTED 27/11/2026 (Owner), hiệu lực khi Owner gộp PR này |
| ADR-0022 | Bảng chữ cho phép của hồ sơ mã; ngoặc vuông chỉ cho nhãn đúng dạng; cách viết số người đọc và máy đọc khác nhau là lỗi; số kiểu Anh ở đoạn ĐÃ KIỂM; cổng giá bỏ số thứ tự đúng đầu mục; vạch đích của bản chấm L-09 cho PR sửa `tools/hoso/` | ACCEPTED 27/11/2026 (Owner), hiệu lực khi Owner gộp PR này |
| ADR-0023 | Bảng phơi nhiễm thời thế ở Mục 9 của hồ sơ mã: trạng thái theo tệp ngoài đã ghim, phơi nhiễm là quy mô, điều kiện đổi trạng thái chấm được, hậu kiểm TRONG BẢNG hay NGOÀI BẢNG; không sửa `tools/hoso/` | ACCEPTED 27/11/2026 (Owner), hiệu lực khi Owner gộp PR này |
| ADR-0024 | Năm năng lực kiểm chứng được: sổ thành tích nhiều ghế so với ghế B trên câu hỏi về chỉ tiêu doanh nghiệp; bản đồ phơi nhiễm nhiều mã và từ điển biến; nhãn độ phủ báo cáo công khai; hậu kiểm theo sự kiện và câu 11 của phiếu; sổ bất đồng; mở lại một phần hẹp của ADR-0019 QĐ-P1, QĐ-P11, QĐ-P12; L-02 không đổi | ACCEPTED 28/11/2026 (Owner), hiệu lực khi Owner gộp PR này |
| ADR-0025 | Nhìn ngược và loại trừ trong hồ sơ mã: khám nghiệm trước ở Mục 11; điểm cờ đỏ kế toán (điểm F, điểm M, điểm Z) ở Mục 6; dừng khi doanh thu giải thích được bằng tệp gốc dưới ba phần tư; không sửa `tools/hoso/` | ACCEPTED 28/11/2026 (Owner), hiệu lực khi Owner gộp PR này |
| ADR-0026 | Cổng bằng chứng: chỉ mở khi đủ cả năm điều ở QĐ-B1 điểm 3 (ba hồ sơ đã giao tới ngày 28/11/2026: FPT bản 2, HPG bản 2, GAS bản 1 sửa 1; từ báo cáo quý IV/2026); tới ngày đó không thêm năng lực mới, không mở phép thử tay mới, không bắt đầu gói Pha 2, chỉ làm danh sách đóng NL-01 tới NL-11; ngừng phép so theo độ phủ và số đo theo nhãn lập luận của ADR-0024; phép so A với B chạy như đã khóa; sổ kết quả, loại nguyên nhân chính khi SAI, đối chiếu khác hãng ở mỗi lần hậu kiểm; tiểu mục tổng kết ở «Một trang» và câu hỏi bắt buộc thứ tư của mẫu B; điều kiện sai đủ bốn thứ; sửa mẫu kỷ luật; viết lại `BOOT.md`; không sửa `tools/hoso/`; L-02 không đổi | ACCEPTED 28/11/2026 (Owner), hiệu lực khi Owner gộp PR này |
