# ADR-0002: Không thu hẹp v3.0; dự báo là việc dài hạn; phạm vi phép thử A–B
- Ngày: 2026-11-17
- Trạng thái: ACCEPTED 17/11/2026 (Owner gộp PR #29, commit gộp `b8158be`)
- Người đề xuất: Claude (kiến trúc sư trưởng)
- Người chấm: Gemini (Google) — `GỘP ĐƯỢC — commit 6201090` (bình luận PR #29)
- Owner duyệt: gộp PR #29 ngày 17/11/2026. Quyết định gốc của Owner (17/11/2026, chat vận hành): tập trung hoàn thiện kiến trúc; dự báo và các việc khác là việc lâu dài. Cùng ngày Owner giao Claude quyền tổng công trình sư ("tự quyết, tôi nghiệm thu"): Claude quyết định và thực hiện, Owner nghiệm thu bằng nút Merge; ba tay người của L-10 giữ nguyên, người viết vẫn phải được ghế khác nhà cung cấp chấm (L-09).

## Quyết định
1. **Không thu hẹp v3.0.** Điều kiện hoàn tác của ADR-0001 ("sau 30 ngày kể từ ngày gộp — tức 23/11/2026 — sổ có dưới 20 dự báo hợp lệ thì mở ADR-0002 xét thu hẹp") được xét tại đây và kết luận: giữ nguyên v3.0.
2. **Dự báo là việc dài hạn**, không có hạn chót trong giai đoạn hoàn thiện kiến trúc. Thay điều kiện của ADR-0001 bằng điều kiện mới ở mục "Điều kiện hoàn tác".
3. **Phạm vi phép thử A–B** (câu hỏi ADR-0003 để ngỏ cho ADR này): câu hỏi có luật `event_before_date` **không vào** phép kiểm định chốt mẫu 194 cặp. Các cặp đó vẫn là cặp, vẫn vào tỷ lệ bất đồng, vẫn được ghi, phân định và tính Brier theo ghế; số cặp bất đồng ngoài phạm vi được báo riêng (`disagreements_out_of_scope` trong `reports/scorecard.json`, dòng "Cặp A–B" của báo cáo vòng học). Các luật khác của phép thử (ADR-0003 quyết định 3) giữ nguyên.

## Lý do
- Sổ dự báo trống không phải vì kiến trúc quá rộng mà vì đường dự báo chưa đi trọn vòng: tới 17/11/2026 (gộp PR #28) mới có phân định, chấm A–B và kiểm toán. Điều kiện của ADR-0001 đo việc dùng một đường ống chưa tồn tại; áp nó vào 23/11 sẽ thu hẹp kiến trúc vì một lý do không liên quan tới kiến trúc.
- Owner quyết thứ tự ưu tiên: hoàn thiện kiến trúc trước.
- `event_before_date`: ghế A được tìm web, ghế B (Claude trần) thì không. Với loại câu hỏi mà sự kiện có thể đã xảy ra trước khi hỏi, A có thể đọc được kết quả, nên bất đồng A–B đo việc tìm web chứ không đo giá trị của thư viện — đúng thứ phép thử muốn đo. Máy không biết sự kiện xảy ra lúc nào (ADR-0003, mục giới hạn), nên loại cả nhóm khỏi phép thử là cách duy nhất máy kiểm được. Với `numeric_range` và `comparison`, số liệu chỉ công bố sau `resolve_at`.

## Giới hạn (nói thẳng)
- **Phép thử A–B đo cả bộ máy, không đo riêng thư viện.** Ghế A là Claude trong Project TTC: có thư viện, có quy trình và được tìm web. Ghế B là Claude trần, không tìm kiếm. Vì vậy "A hơn B" nghĩa là bộ máy TTC hơn mô hình trần; nó không tách được phần đóng góp của thư viện khỏi phần của việc tìm web. Với `numeric_range` và `comparison`, kết quả chưa công bố lúc hỏi, nhưng A vẫn đọc được số liệu mới hơn ngày cắt dữ liệu của B. Muốn tách riêng thư viện cần một ghế đối chứng thứ ba (Claude có tìm web, không có thư viện) — việc đó đổi thiết kế nhóm đối chứng, phải qua ADR riêng. Mỗi dự báo ghế A ghi rõ trong `author_seat` có tìm web hay không.
- **Máy chỉ biết nhãn `resolution_rule`.** Một câu hỏi về sự kiện có thể đã xảy ra mà ghi nhãn `comparison` hay `numeric_range` thì máy không nhận ra, và nó sẽ vào phép thử. Người đặt câu hỏi chịu trách nhiệm chọn đúng nhãn; người đọc sổ thấy câu chữ, nhãn và giờ mở Issue.

## Điều kiện hoàn tác
- Nếu tới 31/03/2027 `ledger/predictions.jsonl` có dưới 20 dự báo hợp lệ, mở ADR mới xét thu hẹp v3.0 về đúng phần Ledger + Thư viện tầng 1 (như ý của ADR-0001).
- Nếu sau 60 cặp, quá nửa số cặp bất đồng nằm ngoài phạm vi (`event_before_date`), mở ADR xét lại bộ câu hỏi: phép thử khi đó không đủ mẫu.

## Ảnh hưởng tới ARCHITECTURE.md
Dòng trạng thái đầu tệp; §4.2 (phạm vi phép thử).
