# ADR-0013: Đồng bộ giấy tờ sau sáu dự báo; không thêm ghế, không đổi mẫu
- Ngày: 2026-11-18
- Trạng thái: ACCEPTED (Owner đã gộp [PR #47](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/47), merge `fc8077cf2f892dc1093b5bb26312db90886d339e`; quyết định giữ nguyên)
- Người đề xuất: Grok (xAI), ghế thi công, theo lệnh thi công cùng ngày
- Người chấm: ChatGPT (OpenAI) (theo `reviewed_by` của PR); [bản chấm L-09](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/47#issuecomment-6984297276) trên HEAD `563f689e23b99c471d188c89df7194a14b34e599`. Hai lượt L-09 cuối trên HEAD này đều SUCCESS: [pull_request_target](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/actions/runs/44346211998/job/134949187288); [pull_request](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/actions/runs/44346208218/job/134949164881).
- Owner duyệt: 18/11/2026 23:21:08 giờ Việt Nam (UTC+07:00; GitHub `merged_at`: `2026-11-18T16:21:08Z`), [PR #47](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/47); merge `fc8077cf2f892dc1093b5bb26312db90886d339e`.

## Quyết định
1. **§8 khớp sổ, không hủy đồng hồ 3 tuần.** Ngày 18/11/2026 sổ có F-37–F-42, ba cặp A/B, dấu nhận robot khớp hash. `state/PROJECT_STATE.yaml` ghi `V3_G0_DAT_DIEU_KIEN_KY_THUAT`. Đó là điều kiện kỹ thuật của G0, không phải G1 (thư viện 0/40, dự báo 6/60). Cột dừng/đảo “quá 3 tuần → chỉ giữ Ledger” không bị hủy. ADR-0002 và mốc 31/03/2027 không đổi. Quyết định 1–7 của ADR-0010 không viết lại; câu pha cũ trong quyết định 2 của ADR đó giữ nguyên chữ đã chấm. Pha hiện tại đọc ở tệp trạng thái và ở §8.
2. **ADR-0010 chỉ lật trạng thái.** Header và dòng danh mục chuyển ACCEPTED vì Owner đã gộp PR #35 (merge `400de5775f6d832ff453ccc2d88c91eb35936d1a`). L-09 của PR đó success trên HEAD `de9e682e833da6f27a871ad5d47bcf4f12251b5c`, bình luận `GỘP ĐƯỢC — commit de9e682`, `reviewed_by: Claude (Anthropic)`.
3. **Phân quyền.** ChatGPT (OpenAI) có thể soạn chữ PR khi được giao: đó là người viết. Ghế thi công là Grok (xAI), quyền đúng quyết định 1 của ADR-0010. Phản biện độc lập là nhà cung cấp khác người viết. Không lập ghế nào đứng trên Owner.
4. **L-09 và ruleset, đo ngày 18/11/2026. Không bật required status checks.** Ruleset `Protect main history` (id 27474018) đang active trên nhánh mặc định, bypass rỗng, chỉ có rule `deletion` và `non_fast_forward`. API branch protection của `main` trả 404. GitHub hiện không chặn merge khi check đỏ. PR #43 không bị gọi là vi phạm L-09: rollup có lượt L-09 đỏ rồi lượt L-09 success (cả `pull_request` và `pull_request_target`) và “Test bat buoc (chan merge)” success trước merge `d36ca18817bdfd2980567a4f2292f113abb90790`. Ghế thi công không sửa ruleset.
   Robot ghi sổ không đi qua PR. `ledger_intake.yml` có `permissions: contents: write` và `git push -q origin HEAD:main` (khoảng dòng 62). `resolution_intake.yml` cùng kiểu (khoảng dòng 60). `daily_cycle.yml` cũng `git pull -q --rebase origin main && git push`. Tài liệu GitHub mô tả required status checks là luật lúc merge. Ghế này chưa chứng minh bật rule đó thì các lệnh đẩy thẳng `main` của robot vẫn thành công. Chưa có phương án an toàn. Việc bật required status checks chờ một quyết định hoặc thiết kế riêng. ADR này không yêu cầu Owner bật. Cũng không bật “Require a pull request before merging”.
5. **A/B.** Phép thử hiện tại đo cả bộ TTC so với Claude trần, không đo riêng Thư viện. Báo cáo sau này được đếm thêm theo `library_refs` của ghế A nếu trường đó có. Không có thì ghi “không khai mức dùng thư viện”. Không đổi `engine/ledger.py` và không đổi mẫu 194. PR này không thêm mã báo cáo vì sáu dòng hiện không mang `library_refs`; suy mức dùng thư viện từ tên ghế A sẽ là bịa.
6. **Ghế B.** Báo cáo tương lai tách câu trả lời của ghế B khỏi phần biểu mẫu người khác hoàn thiện. Không viết lại Ledger. F-38, F-40, F-42 đã ghi trong `invalidation_conditions` rằng phần hoàn thiện biểu mẫu là theo lệnh G0 của Owner, không phải lời nguyên văn của ghế B.
7. **G4 và Media.** “Sau sáu tháng” là mốc xem xét, không phải cam kết có 194 bất đồng. 194 vẫn là điều kiện để cân nhắc API/Media, không phải sản lượng phải đạt đúng ngày đó. `governance/SAFETY_STATE.yaml` không đổi.

## Required status checks — chưa bật
Không có bước nào trong ADR này bảo Owner mở ruleset và thêm required status checks. `ledger_intake.yml` và `resolution_intake.yml` đẩy thẳng `main`. Chưa chạy thử rule đó với token của robot, nên chưa biết push trực tiếp có bị chặn hay không. Khi nào có phương án đã thử và robot vẫn ghi được sổ, một ADR khác sẽ nói Owner có bật hay không. Không bật “Require a pull request before merging” trong lúc chờ.

## Lý do
§8 còn chữ “sổ chưa có dự báo thử” và pha `V3_G0_CHUA_THOAT` sau khi PR #43 đã ghi sáu dự báo. Header ADR-0010 còn PROPOSED sau khi PR #35 đã gộp. Ruleset không có required checks nên L-09 đỏ không tự chặn merge; chặn bằng rule đó chưa có phương án an toàn với robot ghi thẳng `main`, nên còn chờ quyết định riêng. Câu “thư viện chưa đổi gì” và “sau sáu tháng” đang đọc được như thể phép thử đo riêng Thư viện và như thể 194 là hạn phải đạt.

## Điều kiện hoàn tác
- Owner nói một câu giữ §8 ở chữ cũ: ADR mới khôi phục đoạn “G0 chưa thoát”. Không xóa F-37–F-42.
- Nếu một quyết định sau này bật required checks và robot hoặc vòng học không ghi được `main` nữa: tắt riêng rule required status checks, không tắt rule cấm force-push và cấm xóa nhánh. ADR này không yêu cầu bật rule đó.
- Muốn đo riêng Thư viện: ADR khác, có ghế đối chứng thứ ba. Không làm bằng cách sửa mẫu 194.

## Ảnh hưởng tới ARCHITECTURE.md
§3 (một đoạn phân quyền); §4.1 bước 5 (câu tỷ lệ bất đồng); §4.2 (hai đoạn phạm vi A/B và attribution ghế B); §6 (Media); §7 (ô API); §8 (dòng G4 và đoạn trạng thái G0). `SAFETY_STATE.yaml` không đổi. Quyết định 1–7 của ADR-0010 không đổi.
