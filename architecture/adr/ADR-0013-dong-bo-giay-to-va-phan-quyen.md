# ADR-0013: Đồng bộ giấy tờ sau sáu dự báo; không thêm ghế, không đổi mẫu
- Ngày: 2026-11-18
- Trạng thái: PROPOSED (ACCEPTED khi Owner gộp PR chứa tệp này, sau bản chấm L-09 của ghế khác nhà cung cấp)
- Người đề xuất: Grok (xAI), ghế thi công, theo lệnh thi công cùng ngày
- Người chấm: để trống đến khi ghế khác nhà cung cấp chấm
- Owner duyệt: hiệu lực khi Owner gộp

## Quyết định
1. **§8 khớp sổ, không hủy đồng hồ 3 tuần.** Ngày 18/11/2026 sổ có F-37–F-42, ba cặp A/B, dấu nhận robot khớp hash. `state/PROJECT_STATE.yaml` ghi `V3_G0_DAT_DIEU_KIEN_KY_THUAT`. Đó là điều kiện kỹ thuật của G0, không phải G1 (thư viện 0/40, dự báo 6/60). Cột dừng/đảo “quá 3 tuần → chỉ giữ Ledger” không bị hủy. ADR-0002 và mốc 31/03/2027 không đổi. Quyết định 1–7 của ADR-0010 không viết lại; câu pha cũ trong quyết định 2 của ADR đó giữ nguyên chữ đã chấm. Pha hiện tại đọc ở tệp trạng thái và ở §8.
2. **ADR-0010 chỉ lật trạng thái.** Header và dòng danh mục chuyển ACCEPTED vì Owner đã gộp PR #35 (merge `400de5775f6d832ff453ccc2d88c91eb35936d1a`). L-09 của PR đó success trên HEAD `de9e682e833da6f27a871ad5d47bcf4f12251b5c`, bình luận `GỘP ĐƯỢC — commit de9e682`, `reviewed_by: Claude (Anthropic)`.
3. **Phân quyền.** ChatGPT (OpenAI) có thể soạn chữ PR khi được giao: đó là người viết. Ghế thi công là Grok (xAI), quyền đúng quyết định 1 của ADR-0010. Phản biện độc lập là nhà cung cấp khác người viết. Không lập ghế nào đứng trên Owner.
4. **L-09 và ruleset, đo ngày 18/11/2026.** Ruleset `Protect main history` (id 27474018) đang active trên nhánh mặc định, bypass rỗng, chỉ có rule `deletion` và `non_fast_forward`. API branch protection của `main` trả 404. GitHub hiện không chặn merge khi check đỏ. PR #43 không bị gọi là vi phạm L-09: rollup có lượt L-09 đỏ rồi lượt L-09 success (cả `pull_request` và `pull_request_target`) và “Test bat buoc (chan merge)” success trước merge `d36ca18817bdfd2980567a4f2292f113abb90790`. Ghế thi công không sửa ruleset. Việc bật required status checks là của Owner, các bước ở mục dưới. Không bật “Require a pull request before merging”.
5. **A/B.** Phép thử hiện tại đo cả bộ TTC so với Claude trần, không đo riêng Thư viện. Báo cáo sau này được đếm thêm theo `library_refs` của ghế A nếu trường đó có. Không có thì ghi “không khai mức dùng thư viện”. Không đổi `engine/ledger.py` và không đổi mẫu 194. PR này không thêm mã báo cáo vì sáu dòng hiện không mang `library_refs`; suy mức dùng thư viện từ tên ghế A sẽ là bịa.
6. **Ghế B.** Báo cáo tương lai tách câu trả lời của ghế B khỏi phần biểu mẫu người khác hoàn thiện. Không viết lại Ledger. F-38, F-40, F-42 đã ghi trong `invalidation_conditions` rằng phần hoàn thiện biểu mẫu là theo lệnh G0 của Owner, không phải lời nguyên văn của ghế B.
7. **G4 và Media.** “Sau sáu tháng” là mốc xem xét, không phải cam kết có 194 bất đồng. 194 vẫn là điều kiện để cân nhắc API/Media, không phải sản lượng phải đạt đúng ngày đó. `governance/SAFETY_STATE.yaml` không đổi.

## Việc Owner làm nếu muốn GitHub chặn merge khi check đỏ
1. Mở Settings → Rules → Rulesets → `Protect main history` (id 27474018). Giữ enforcement Active, target nhánh mặc định, không thêm bypass.
2. Giữ hai rule đang có: Restrict deletions, Block force pushes.
3. Add rule → Require status checks to pass. Thêm đúng ba tên đã chạy trên kho:
   - `Test bat buoc (chan merge)`
   - `L-09 nguoi cham khac nha cung cap (pull_request)`
   - `L-09 nguoi cham khac nha cung cap (pull_request_target)`
4. Không bật Require a pull request before merging. Bật thì robot ghi sổ không đẩy được.
5. Save. Ghế thi công không có bước này trong PR.

## Lý do
§8 còn chữ “sổ chưa có dự báo thử” và pha `V3_G0_CHUA_THOAT` sau khi PR #43 đã ghi sáu dự báo. Header ADR-0010 còn PROPOSED sau khi PR #35 đã gộp. Ruleset không có required checks nên L-09 đỏ không tự chặn merge. Câu “thư viện chưa đổi gì” và “sau sáu tháng” đang đọc được như thể phép thử đo riêng Thư viện và như thể 194 là hạn phải đạt.

## Điều kiện hoàn tác
- Owner nói một câu giữ §8 ở chữ cũ: ADR mới khôi phục đoạn “G0 chưa thoát”. Không xóa F-37–F-42.
- Bật required checks mà robot hoặc vòng học không merge được nữa: Owner tắt riêng rule required status checks, không tắt rule cấm force-push và cấm xóa nhánh.
- Muốn đo riêng Thư viện: ADR khác, có ghế đối chứng thứ ba. Không làm bằng cách sửa mẫu 194.

## Ảnh hưởng tới ARCHITECTURE.md
§3 (một đoạn phân quyền); §4.1 bước 5 (câu tỷ lệ bất đồng); §4.2 (hai đoạn phạm vi A/B và attribution ghế B); §6 (Media); §7 (ô API); §8 (dòng G4 và đoạn trạng thái G0). `SAFETY_STATE.yaml` không đổi. Quyết định 1–7 của ADR-0010 không đổi.
