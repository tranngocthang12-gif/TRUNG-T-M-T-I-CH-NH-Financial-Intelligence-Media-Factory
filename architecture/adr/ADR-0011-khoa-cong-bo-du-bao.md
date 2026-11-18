# ADR-0011: Khóa nhận dự báo theo lúc thông tin có thể được công bố
- Ngày: 2026-11-18
- Trạng thái: PROPOSED (ACCEPTED khi Owner gộp PR chứa tệp này, sau bản chấm L-09 của ghế khác nhà cung cấp)
- Người đề xuất: Grok (xAI), ghế thi công, theo lệnh thi công cùng ngày; sửa mã và quyết định 5, 7, 8, 9–11 bởi Claude (Anthropic) theo lệnh Owner "[TTC] Sửa dứt điểm PR #45 / L-05" ngày 18/11/2026
- Người chấm: để trống đến khi ghế khác nhà cung cấp chấm
- Owner duyệt: hiệu lực khi Owner gộp

## Quyết định
1. Dự báo mới phải khai `info_lock_at` (YYYY-MM-DD, giờ Việt Nam): ngày đầu tiên thông tin dùng để phân định **có thể** được công bố. Điều kiện nhận: ngày tạo Issue < `info_lock_at` ≤ `resolve_at`. Hạn này độc lập với hạn phân định. Thiếu trường, sai dạng, hoặc khóa không sau ngày tạo thì không ghi.
2. `info_lock_at` nằm trong dòng sổ và trong hash chuỗi. Ghế thứ hai của cùng câu hỏi phải ghi đúng hạn đã có. Không đặt lại sau khi ghi. Chạy lại job chỉ cấp dấu nhận khi thân Issue khớp dòng đã ghi.
3. Dấu nhận của dự báo phải được đăng trước 00:00 ngày `info_lock_at` lẫn trước 00:00 ngày `resolve_at`. Robot không ghi nếu còn dưới 30 phút tới hạn sớm hơn.
4. Khi có bằng chứng kết quả đã công bố, ghi một dòng `ledger/publication_evidence.jsonl` qua Issue `[Publication]` (cùng workflow nhận phân định, không ghi `resolutions.jsonl`). `published_at` là mốc ISO có múi giờ. Chỉ có ngày thì từ chối. Không ghi công bố ở tương lai. Không ghi dòng thứ hai cho cùng câu hỏi. Có dòng đó trong sổ thì không nhận thêm dự báo cho câu hỏi, kể cả trước `resolve_at`.
5. `tools.ledger_intake.capability_test_eligible` chỉ đúng khi chứng minh được dự báo được ghi trước hạn khóa, trước `published_at` sớm nhất nếu có bằng chứng, và xuất xứ đã được kiểm toán GitHub xác nhận (quyết định 10). Hàm này **không** đổi mẫu 194 cặp, không đổi điều kiện chốt mẫu.
6. F-37 đến F-42 giữ nguyên từng byte. Chúng không có `info_lock_at`. Hash sáu dòng được ghim. Gắn thêm trường hoặc sửa nội dung là lỗi. Khi chưa có bằng chứng công bố đứng sau giờ tạo Issue, trạng thái là `legacy_unproven`: không đưa vào phép kiểm định hợp lệ. Nếu sau này có bằng chứng với `published_at` sau giờ tạo Issue, trạng thái thành `legacy_proven_by_evidence` và được coi là đã chứng minh — vẫn không viết lại dòng.
7. Ngày `info_lock_at` do người gửi tự khai không phải bằng chứng. **Dự báo mới bắt buộc `calendar_id`**; robot không nhận dự báo thiếu `calendar_id`, trỏ tới lịch không có, lịch khác tên miền với `resolution_source`, lịch khác ngày khóa, lịch do cùng nhà cung cấp với người viết ghi, hoặc lịch mà Issue `[Calendar]` mở không trước Issue dự báo.
8. `engine.ledger.issue_summary` gọi `timing_verification_status`. Mẫu vẫn là 194 cặp bất đồng đầu tiên. Nếu một cặp trong mẫu không ở trạng thái `eligible` / `legacy_proven_by_evidence` thì phán quyết là `CHƯA ĐỦ ĐIỀU KIỆN KẾT LUẬN`. Không rút cặp sau vào thay. Brier, `hit_rate`, hiệu chuẩn, `a_correct`, `a_accuracy`, `disagreements_resolved`, `brier_void_worst` chỉ tính trên dự báo hợp lệ; số trên toàn sổ nằm trong `raw_audit` với nhãn "SỐ LIỆU THÔ ĐỂ KIỂM TOÁN — KHÔNG PHẢI BẰNG CHỨNG NĂNG LỰC"; `counts` tách số được ghi / có bằng chứng hợp lệ / đã phân định / đã phân định và hợp lệ.
9. **Lịch chỉ vào sổ qua robot.** Owner mở Issue `[Calendar]` (mẫu `calendar.yml`); `resolution_intake.yml` ghi một dòng vào `governance/release_calendar.jsonl` (chuỗi hash, chỉ ghi thêm, nằm trong `APPEND_ONLY` của `tools/ledger_audit.py`) và bot đăng dấu nhận `ledger-attest: calendars <calendar_id> <hash>`. Dòng lịch không có trường thời gian tự khai (`recorded_at` bị bỏ; Issue có trường lạ bị từ chối). Mốc thời gian là `issue_number` và `issue_created_at` do GitHub cấp. `calendar_id` đã ghim không sửa, không ghi đè; ngày khác dùng mã khác. `info_lock_at` của lịch phải sau ngày mở Issue lịch.
10. **Xuất xứ chỉ do GitHub xác nhận, fail closed.** `tools/ledger_audit.provenance_verified_ids` (chạy trong `ledger_audit.py --github`) đòi: Issue lịch có thật, không phải PR, do chủ kho mở, giờ tạo khớp dòng; có dấu nhận của bot chưa sửa, trong 6 giờ; số Issue lịch nhỏ hơn số Issue dự báo; **giờ bot đăng dấu nhận của lịch trước giờ mở Issue dự báo**. Không tin `recorded_at`, ngày author/committer của Git. Lịch commit sau Issue dự báo, hay dòng lịch ghi tay khai giờ sớm, đều đỏ ở kiểm toán và không được xác nhận. Engine chỉ coi dự báo là hợp lệ khi mã của nó nằm trong tập đã xác nhận; vòng học hằng tuần gọi API với `TTC_PROVENANCE_ONLINE=1`; không gọi được API → tập rỗng → không có điểm năng lực (`provenance_unverified`). Với F-37–F-42, xác nhận là mọi bằng chứng công bố của câu hỏi có dấu nhận hợp lệ.
11. **Bằng chứng phát hiện sau.** Một câu hỏi có thể có thêm dòng `publication_evidence.jsonl`, nhưng chỉ khi `published_at` mới **sớm hơn** mọi mốc đã ghi (chỉ siết, không nới). Trạng thái dùng mốc sớm nhất. Dòng dự báo bất biến; nếu mốc sớm nhất không sau giờ mở Issue dự báo thì dự báo là `after_publication` và bị loại khỏi kết luận năng lực, cặp vẫn giữ chỗ trong mẫu 194.

## Lý do
Luật nhận cũ chỉ đòi `resolve_at` sau ngày tạo. Số liệu (CPI, IIP, bán lẻ) có thể công bố trước ngày phân định. Một dự báo nộp sau khi số đã công khai vẫn vào sổ và có thể vào chấm năng lực. L-05 cấm kiểm định bằng câu đã biết kết quả. Hạn khóa khai trước lúc nhận, gắn vào hash, nên không dời được sau khi đã biết kết quả.

## Điều kiện hoàn tác
- Owner nói một câu hủy hạn khóa: ADR mới bỏ `info_lock_at` khỏi luật nhận dự báo **mới**. Không sửa F-37–F-42. Không xóa dòng bằng chứng đã ghi (tệp chỉ nối thêm).
- Nếu hạn khóa làm robot từ chối nhầm mọi dự báo hợp lệ trong 14 ngày sau khi gộp, ADR sửa điều kiện so ngày — không nới bằng cách sửa dòng đã ghi.

## Ảnh hưởng tới ARCHITECTURE.md
Một câu ở §4.1 bước 3: dự báo mới khai `info_lock_at`, trích `calendar_id` của lịch đã ghim trước Issue, và không được nhận sau ngày đó hoặc sau khi đã có bằng chứng công bố. Mẫu 194 ở §4.2 không đổi.

## Giới hạn nói thẳng
- Robot nhận dự báo chỉ kiểm được phần có trong sổ (dòng lịch, giờ tạo Issue lịch). Phần chỉ GitHub chứng minh được (dấu nhận của bot đăng trước Issue dự báo) được kiểm sau, ở `ledger_audit.py --github` trên mỗi lần đẩy lên `main` và hằng ngày; dòng không đạt làm CI đỏ và không bao giờ có điểm năng lực, nhưng dòng vẫn nằm trong sổ (sổ chỉ ghi thêm).
- Lịch chính thức sai (cơ quan công bố sớm hơn lịch) không bị chặn ở lúc nhận; nó bị bắt khi có dòng bằng chứng công bố với mốc sớm hơn (quyết định 11).
- Không bật required status checks; robot vẫn đẩy thẳng lên `main` như trước.
