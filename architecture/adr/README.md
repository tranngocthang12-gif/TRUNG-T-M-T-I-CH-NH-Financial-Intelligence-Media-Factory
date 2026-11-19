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
