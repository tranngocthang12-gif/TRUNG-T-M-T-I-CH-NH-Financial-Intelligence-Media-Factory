# ADR-0009: Bản giá dẫn xuất có phiên bản, không sửa bảng giá gốc

- Ngày: 2026-11-18
- Trạng thái: PROPOSED (chỉ ACCEPTED khi Owner gộp PR được L-09 chấm). PR #32 ngày 18/11/2026 gộp `docs/RESEARCH_POINT_IN_TIME_LIMITATIONS.md`; bản đó tự nhận là disclosure, không đổi engine và không làm ADR này có hiệu lực.
- Người đề xuất: ChatGPT (OpenAI), dựa trên khoảng trống đã xác nhận sau ADR-0006
- Người chấm: ghế độc lập khác nhà cung cấp (L-09; chờ)
- Owner duyệt: chờ PR tương ứng, không tự merge

## Phạm vi và bất biến

ADR-0006 đã bảo vệ **kho quan sát gốc**: `data/store/prices.csv.gz` đóng băng và các tệp `data/store/prices/YYYY-MM.csv` chỉ nối thêm. ADR này **không đổi** khóa `(date,ticker)`, thứ tự `observed_at` hay quy tắc chọn bản quan sát đầu tiên trong kho gốc.

## Quyết định

1. **Tách rõ hai tầng.** Raw price store giữ nguyên theo ADR-0006. Mọi sửa sai giá, thay nguồn, điều chỉnh corporate action, sửa ngày hưởng quyền phải được thể hiện trong **bản dẫn xuất mới** có phiên bản, tuyệt đối không chỉnh sửa/raw-backfill.
2. **Manifest dẫn xuất.** Mỗi bản có `derivation_id`, `created_at`, `raw_snapshot_hash`, `code_commit`, `config_hash`, `corporate_events_hash`, `source_documents[]` (URL/hash/issuer/date), `validity_scope` và `supersedes` khi cần. Giá trị giá/sự kiện không rõ nguồn hoặc chưa xác minh phải bị cách ly hoặc báo `UNVERIFIED`, không bị tự chuyển sang `VERIFIED` chỉ vì biến động giá khớp hệ số.
3. **Chỉ trạng thái nguồn có bằng chứng và ngày công bố hợp lệ** được tác động tới chuỗi 'verified-adjusted'. Tách loại `observed_at`, `published_at` và `effective_at`; không lấy `ex_date` làm ngày công bố nếu thiếu.
4. **Phân biệt cách dùng.** Phân tích hồi cứu có thể chạy trên bản dữ liệu tái dựng với nhãn `RETROSPECTIVE`; replay lịch sử thực sự biết được phải dùng bằng chứng time-of-knowledge và chỉ nhận thông tin sẵn có trước cutoff; không tuyên bố 'full point-in-time' cho nguồn không có vintage.
5. **Đối chiếu bắt buộc khi đổi bản.** Tạo báo cáo trước/sau theo số dòng, số mã/phiên, trả về giá điều chỉnh, quality flags, feature, nhãn, backtest/Paper và các sự kiện quyền. Không tự nâng cấp model từ thành tích trên bản mới.
6. **Rollback không xóa chứng cứ.** Chuyển con trỏ sử dụng về bản dẫn xuất đã được kiểm trước; lưu manifest, báo cáo diff và hash của cả hai bản. Không chạy tái tạo dữ liệu dẫn xuất tự động đè bản đã công bố.
7. **Cổng triển khai.** ADR này là quy trình; **chưa thêm adapter, chưa đổi `data.sources`, chưa ghi dữ liệu, chưa thay `engine/adjust.py`**. Bản vá engine theo PR riêng với test end-to-end và L-09/Owner L-10. TCB/VCB chưa được coi là xác minh bằng việc gắn URL chung.

## Lý do

Một nguồn/cấu hình mới có thể sửa kết quả tính toán mà không sửa file raw; nếu thiếu phiên bản và nguồn gốc của bản dẫn xuất thì không thể giải thích vì sao kết quả nghiên cứu thay đổi. Cần phân biệt nguyên tắc append-only của ADR-0006 với quyền 'sửa' dữ liệu dẫn xuất có kiểm toán.

## Tiêu chí nghiệm thu

- Test chứng minh raw gốc từng byte không thay đổi.
- Cùng raw + code + config + event evidence tạo cùng bản dẫn xuất có hash tương ứng.
- Event chưa xác minh hoặc không có ngày công bố không vào verified-adjusted.
- Hai bản dẫn xuất có thể so sánh và chuyển đổi có audit; rollback không mất provenance.
- Đầu ra nghiên cứu gắn `derivation_id` và nhãn mức bằng chứng point-in-time.

## Điều kiện hoàn tác

Sau 8 vòng chạy verified-adjusted đầu tiên (nếu có), nếu chi phí lưu manifest/dẫn xuất làm CI thường xuyên quá giới hạn hoặc không tái dựng được cùng digest, mở ADR mới để thay đổi cách lưu **bản dẫn xuất**. Không hoàn tác nguyên tắc bất biến raw của ADR-0006.

## Ảnh hưởng tới ARCHITECTURE.md

§4.3: bổ sung đường dẫn tới ADR này **sau khi được phê duyệt**; không viết kiến trúc phiên bản mới.
