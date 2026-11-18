# ADR-0011: Khóa nhận dự báo theo lúc thông tin có thể được công bố
- Ngày: 2026-11-18
- Trạng thái: PROPOSED (ACCEPTED khi Owner gộp PR chứa tệp này, sau bản chấm L-09 của ghế khác nhà cung cấp)
- Người đề xuất: Grok (xAI), ghế thi công, theo lệnh thi công cùng ngày
- Người chấm: để trống đến khi ghế khác nhà cung cấp chấm
- Owner duyệt: hiệu lực khi Owner gộp

## Quyết định
1. Dự báo mới phải khai `info_lock_at` (YYYY-MM-DD, giờ Việt Nam): ngày đầu tiên thông tin dùng để phân định **có thể** được công bố. Điều kiện nhận: ngày tạo Issue < `info_lock_at` ≤ `resolve_at`. Hạn này độc lập với hạn phân định. Thiếu trường, sai dạng, hoặc khóa không sau ngày tạo thì không ghi.
2. `info_lock_at` nằm trong dòng sổ và trong hash chuỗi. Ghế thứ hai của cùng câu hỏi phải ghi đúng hạn đã có. Không đặt lại sau khi ghi. Chạy lại job chỉ cấp dấu nhận khi thân Issue khớp dòng đã ghi.
3. Dấu nhận của dự báo phải được đăng trước 00:00 ngày `info_lock_at` lẫn trước 00:00 ngày `resolve_at`. Robot không ghi nếu còn dưới 30 phút tới hạn sớm hơn.
4. Khi có bằng chứng kết quả đã công bố, ghi một dòng `ledger/publication_evidence.jsonl` qua Issue `[Publication]` (cùng workflow nhận phân định, không ghi `resolutions.jsonl`). `published_at` là mốc ISO có múi giờ. Chỉ có ngày thì từ chối. Không ghi công bố ở tương lai. Không ghi dòng thứ hai cho cùng câu hỏi. Có dòng đó trong sổ thì không nhận thêm dự báo cho câu hỏi, kể cả trước `resolve_at`.
5. `tools.ledger_intake.capability_test_eligible` chỉ đúng khi chứng minh được dự báo được ghi trước hạn khóa và trước `published_at` nếu có bằng chứng. Hàm này **không** đổi mẫu 194 cặp, không đổi điều kiện chốt mẫu, không sửa `engine/ledger.py`.
6. F-37 đến F-42 giữ nguyên từng byte. Chúng không có `info_lock_at`. Hash sáu dòng được ghim. Gắn thêm trường hoặc sửa nội dung là lỗi. Khi chưa có bằng chứng công bố đứng sau giờ tạo Issue, trạng thái là `legacy_unproven`: không đưa vào phép kiểm định hợp lệ. Nếu sau này có bằng chứng với `published_at` sau giờ tạo Issue, trạng thái thành `legacy_proven_by_evidence` và được coi là đã chứng minh — vẫn không viết lại dòng.
7. Ngày `info_lock_at` do người gửi tự khai không phải bằng chứng. Phép kiểm định chỉ nhận ngày đó khi nó khớp một dòng `governance/release_calendar.jsonl`: cùng tên miền, `recorded_at` trước Issue, người ghi lịch khác ghế với người viết, có URL và trích dẫn để reviewer kiểm. Không khớp thì trạng thái `self_declared_lock`.
8. `engine.ledger.issue_summary` gọi `capability_test_eligible`. Mẫu vẫn là 194 cặp bất đồng đầu tiên. Nếu một cặp trong mẫu là `after_publication`, `legacy_unproven`, `self_declared_lock` hoặc không đủ bằng chứng thời điểm thì phán quyết là `CHƯA ĐỦ ĐIỀU KIỆN KẾT LUẬN`. Không rút cặp sau vào thay.

## Lý do
Luật nhận cũ chỉ đòi `resolve_at` sau ngày tạo. Số liệu (CPI, IIP, bán lẻ) có thể công bố trước ngày phân định. Một dự báo nộp sau khi số đã công khai vẫn vào sổ và có thể vào chấm năng lực. L-05 cấm kiểm định bằng câu đã biết kết quả. Hạn khóa khai trước lúc nhận, gắn vào hash, nên không dời được sau khi đã biết kết quả.

## Điều kiện hoàn tác
- Owner nói một câu hủy hạn khóa: ADR mới bỏ `info_lock_at` khỏi luật nhận dự báo **mới**. Không sửa F-37–F-42. Không xóa dòng bằng chứng đã ghi (tệp chỉ nối thêm).
- Nếu hạn khóa làm robot từ chối nhầm mọi dự báo hợp lệ trong 14 ngày sau khi gộp, ADR sửa điều kiện so ngày — không nới bằng cách sửa dòng đã ghi.

## Ảnh hưởng tới ARCHITECTURE.md
Một câu ở §4.1 bước 3: dự báo mới khai `info_lock_at` và không được nhận sau ngày đó hoặc sau khi đã có bằng chứng công bố. Mẫu 194 ở §4.2 không đổi.
