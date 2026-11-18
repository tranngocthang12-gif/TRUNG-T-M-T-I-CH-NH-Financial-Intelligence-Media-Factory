# ADR-0010: Lập ghế thi công; sửa lệch giấy tờ đã xác nhận
- Ngày: 2026-11-18
- Trạng thái: PROPOSED (ACCEPTED khi Owner gộp PR chứa tệp này, sau bản chấm L-09 của ghế khác nhà cung cấp)
- Người đề xuất: Grok (xAI), theo lệnh Owner cùng ngày: sửa các vấn đề đã nêu và giao ghế thi công cho ghế này
- Người chấm: ghế khác nhà cung cấp (L-09), ghi ở PR. Ghế này không tự chấm.
- Owner duyệt: lệnh trong chat vận hành 18/11/2026; hiệu lực khi Owner gộp

## Quyết định
1. **Ghế thi công là Grok (xAI).** Không phải MINH TRÍ. Owner lập ghế ngày 18/11/2026. Ghế được: chép nguồn, viết ghi chú, mệnh đề, mã công cụ theo đặc tả, mở PR. Ghế không được: gộp `main`, sửa `governance/LAWS.md`, mở API, chạm `engine/` ngoài một lệnh riêng, tự chấm PR của mình, điền `OWNER_MISSION` hay `GOVERNOR_POLICY`.
2. **Pha đúng là G0 chưa thoát.** Cột thoát §8 ("Action xanh trên 3 dự báo thử") chưa đạt. Cột dừng/đảo ("quá 3 tuần → chỉ giữ Ledger") đã quá hạn tính từ 22/10/2026 và từ ngày gộp 24/10/2026. Ngày 17/11/2026 Owner không thi hành nhánh đó. ADR-0002 đã xét điều kiện hoàn tác của ADR-0001 và giữ v3.0; mốc xét lại vẫn là 31/03/2027, dưới 20 dự báo hợp lệ thì mở ADR mới. Dời mốc đó thêm lần nữa phải bằng ADR mới nêu bằng chứng đã đổi. `state/PROJECT_STATE.yaml` ghi `V3_G0_CHUA_THOAT`.
3. **ADR-0008 đã có hiệu lực từ khi Owner gộp PR #31.** Header và bảng ADR còn chữ PROPOSED là lệch giấy tờ, được lật thành ACCEPTED. Không quyết định lại nội dung ADR-0008.
4. **ADR-0009 giữ PROPOSED.** PR #32 gộp `docs/RESEARCH_POINT_IN_TIME_LIMITATIONS.md`. Bản đó tự nhận là disclosure, không phải ADR-0009 và không đổi engine.
5. **Sửa chữ đang hiệu lực cho khớp quyết định 1.** Tiêu đề §5 và sơ đồ §2 của `architecture/ARCHITECTURE.md` không còn gọi cỗ máy học hiểu là MINH TRÍ. Đường dẫn §5 trỏ đúng `docs/TTC_TANG_HOC_HIEU_v0.2.md`. `BOOT.md` bước 10 không còn bảo mọi AI lấy `orchestrator/` làm cách làm việc. `architecture/ARCHIVE.md` ghi các tệp trước v3.0 còn nằm trong kho nhưng không có hiệu lực. `requirements.txt` ghim đúng phiên bản đã phân giải ngày 18/11/2026.
6. **Không làm trong ADR này:** không thu v3.0 về "chỉ Ledger"; không đổi mẫu 194 cặp; không thêm ghế C; không mở API; không nhập nguồn giá mới; không điền sứ mệnh hay tham số vốn; không chép tài liệu thư viện khi chưa có bản gốc và sha256 (L-01).

## Lý do
Bản rà soát 18/11/2026 đo đúng sổ trống và giấy tờ lệch. Phần giấy tờ lệch được sửa tại đây. Phần "thu hẹp / thêm ghế đối chứng / cắt vòng chấm" không được Owner lệnh, và trái ADR-0002, ADR-0003. Việc nửa Học không có người làm được đóng bằng quyết định 1, không bằng cách viết thêm một bản kiến trúc.

`governance/ARCHITECT_HANDOFF_20261022.md` mục 4(c) từng giao việc đầu của ghế thi công là phản biện hồi cứu vào ADR-0002. ADR-0002 đã ACCEPTED với một việc khác (phạm vi v3.0). Không chèn thêm chữ vào ADR đã chấm. Phản biện hồi cứu, nếu Owner còn muốn, là một tài liệu riêng.

## Điều kiện hoàn tác
- Owner nói một câu thu ghế: ADR mới ghi ghế thi công là trống trở lại. PR đang mở của ghế này không vì thế được gộp.
- Nếu một PR của ghế này được gộp khi chưa có bản chấm L-09 của ghế khác nhà cung cấp, coi việc lập ghế là tạm dừng cho tới khi có bản chấm đó.
- Quyết định 2 chỉ hoàn tác bằng ADR của Owner. Sửa `phase` trong `PROJECT_STATE.yaml` mà không có 3 dự báo thử qua Action xanh là lỗi giấy tờ, không phải thoát G0.
- Ghim `requirements.txt`: nếu CI Python 3.12 không cài được đúng phiên bản đã ghim, nới bằng PR riêng có ghế khác chấm. Không trả về ràng buộc mở kiểu `pandas>=2.1`.

## Ảnh hưởng tới ARCHITECTURE.md
Dòng trạng thái; §2; §3; §5 (tiêu đề và đường dẫn); §8 (một đoạn về hai đồng hồ); §10.
