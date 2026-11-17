# ADR-0003: Phân định dự báo qua Issue, chấm A–B, đưa mười luật vào máy kiểm, engine hằng tuần
- Ngày: 2026-11-17
- Trạng thái: PROPOSED (ACCEPTED khi Owner gộp PR #28)
- Người đề xuất: Claude (kiến trúc sư trưởng)
- Người chấm: ghế khác nhà cung cấp. Đã chấm năm vòng trên các bản 1–5 (17/11/2026), mỗi vòng SỬA TRƯỚC; bản cuối do Claude tự rà toàn bộ theo lệnh Owner "rà soát kiến trúc rồi sửa một lần". Bản chấm bản cuối phải được Owner dán thành bình luận PR (mục 6) trước khi gộp.
- Owner duyệt: khi gộp PR #28
- Ghi chú số: ADR-0002 để dành cho việc xét thu hẹp v3.0 theo điều kiện hoàn tác của ADR-0001.

## Quyết định

1. **Nhận dự báo** (`tools/ledger_intake.py`, `.github/workflows/ledger_intake.yml`). Chỉ Issue do chủ kho mở, nhận lúc mở. Mọi "ngày" tính theo giờ Việt Nam. Luật: `resolve_at` sau ngày tạo; `model_cutoff` dạng `YYYY-MM` và không ở tương lai — cùng với điều trước, câu hỏi luôn giải sau ngày cắt dữ liệu (L-05); `author_seat` bắt đầu bằng tên ghế (L-09); không từ khóa khuyến nghị (L-02); ghế B phải có `prompt_hash` đúng bằng sha256 khối prompt hiện hành trong `governance/CONTROL_B_PROMPT.md`, ghế A không được có; mỗi ghế một dự báo cho một câu hỏi; A và B phải cùng `resolution_rule` và `resolution_source`; cùng câu chữ thì cùng `resolve_at`; thân Issue không được có hai tiêu đề cùng tên.
2. **Phân định** (`tools/resolution_intake.py`, `.github/workflows/resolution_intake.yml`, mẫu Issue "Resolution") → `ledger/resolutions.jsonl`. Một Issue phân định một câu hỏi và ghi cùng một outcome cho mọi dự báo của câu hỏi; câu hỏi đã phân định thì khóa, kể cả VOID; không trước `resolve_at` (trừ YES khi mọi dự báo của câu hỏi có luật `event_before_date`); người phân định bắt đầu bằng tên ghế và không chung ghế với bất kỳ người viết nào của câu hỏi; YES/NO phải có nguồn và trích nguyên văn, và nguồn phải thuộc tên miền đã hứa trong dự báo; nguồn không công bố thì VOID kèm lý do. Thay cho ý "engine tự chấm numeric_range/comparison" ở §4.1 bước 4: chỉ tiêu BCTC/NHNN không có nguồn máy đọc ổn định.
3. **Chấm A–B** (`engine/ledger.py` → `reports/scorecard.json`, mục `issue_forecasts`). Theo ghế: số dự báo, đã phân định, VOID, chờ; Brier, Brier của xác suất nền và của 0,5; hiệu chuẩn. Cặp A–B = cùng câu hỏi, ghi cùng ngày. Bất đồng = hai ghế ở hai phía 0,5. Chỉ chấm cặp mà cả hai đã phân định cùng một sự thật. **Kiểm định chốt mẫu:** phán quyết chỉ tính trên đúng 194 bất đồng được phân định đầu tiên, nhị thức hai phía với p0 = 0,5, α = 0,05 — khớp cách tính cỡ mẫu ở §4.2 và không xem lại trên mẫu lớn dần. Cảnh báo đổi nhóm B khi tỷ lệ bất đồng < 10% sau 60 cặp (đúng `governance/CONTROL_B_PROMPT.md`).
4. **Sổ thử và Deflated Sharpe** (`engine/research.py`, `engine/run_cycle.py`). Mỗi lần thử đăng ký vào `research/trial_registry.jsonl` trước khi chạy; không gian giả thuyết đóng băng ghi trong `config.yaml` (`research.frozen_space`: 13 feature × 3 mô hình), engine từ chối lần thử nằm ngoài; báo cáo vòng học in Sharpe năm hóa và Deflated Sharpe; N của DSR là mọi lần thử từ đầu; khi sổ chưa đủ 10 Sharpe thì dùng phương sai lý thuyết 1/(T−1).
5. **Thư viện** (`engine/knowledge_notes.py`). Tài liệu gốc ghim sha256; địa chỉ trang/đoạn/bảng phải tồn tại; trích nguyên văn (từ 15 ký tự, hoặc nguyên cả đoạn); biên bản chấm gắn với nội dung ghi chú bằng `note_sha256`; CITED cần biên bản PASS, DISPUTED cần biên bản FAIL, TESTED/PROVEN bị từ chối cho tới khi Học viện có mã gán; văn bản hết hiệu lực → vòng học tự chuyển OUTDATED.
6. **Cổng chấm PR** (`tools/review_gate.py`, `.github/workflows/review_gate.yml`). Thân PR ghi `authored_by` và `reviewed_by`, mỗi trường một dòng, bắt đầu bằng tên ghế, không chung ghế; **và** chủ kho phải dán bản chấm thành bình luận PR, dòng đầu "GỘP ĐƯỢC", có 7 ký tự đầu SHA của commit đang chấm. Đẩy commit mới thì cổng đỏ lại. Bản chấm vì thế nằm trên kho (GitHub-first), không chỉ trong chat. Cổng chạy bằng mã của nhánh `main` (sự kiện `pull_request_target`) nên một PR không tự nới lỏng được cổng của chính nó.
7. **Kiểm toán sổ** (`tools/ledger_audit.py`, chạy trong `.github/workflows/tests.yml`). Hash chuỗi không phải chữ ký. Thêm hai neo nằm ngoài tệp: sổ phải là chỉ-ghi-thêm so với commit gốc, và mỗi dòng phải ứng với một Issue thật do chủ kho mở, đúng giờ tạo GitHub ghi.
8. **Vận hành.** Engine chạy hằng tuần (thứ Sáu 16:30 giờ VN) đúng §4.3 và kiểm luật cả trước lẫn sau khi chạy (`.github/workflows/daily_cycle.yml`); mọi tệp `tests/test_*.py` chạy trong CI chặn gộp, test làm thay đổi tệp của kho thì đỏ; công tắc an toàn lệch khỏi `false` là lỗi chứ không chỉ cảnh báo (`tools/validate.py`).
9. **Đính chính §3**: ghế thi công chưa lập và không phải MINH TRÍ (Owner 22/10/2026). Mọi chỗ trong `docs/TTC_TANG_HOC_HIEU_v0.2.md` ghi MINH TRÍ là ghế thi công hoặc ghế A đọc là "ghế thi công (chưa lập)".

## Bảng đối chiếu luật ↔ máy kiểm (hiện trạng sau PR này)

| Luật | Máy kiểm | Ở đâu | Phần máy KHÔNG kiểm được |
|---|---|---|---|
| L-01 Nguồn | tài liệu ghim sha256/bytes; địa chỉ tồn tại; trích nguyên văn; thư mục nguồn chưa ghim → lỗi | `engine/knowledge_notes.py`, gọi từ `tools/validate.py` | ý tiếng Việt có diễn đúng đoạn trích không (người chấm) |
| L-02 Không khuyến nghị | quét `reports/`, `media/`, `ledger/`; từ chối ngay lúc nhận dự báo và phân định | `tools/laws_checks.py`, `tools/ledger_intake.py`, `tools/resolution_intake.py` | khuyến nghị diễn đạt vòng, không dùng từ khóa |
| L-03 Dữ liệu cá nhân | quét số định danh/số tài khoản đi kèm nhãn trong mọi tệp chữ (trừ tài liệu gốc đã ghim) | `tools/laws_checks.py` | vốn thật, mức lỗ, vị thế viết bằng lời |
| L-04 Bản quyền | manifest bắt buộc `license`, `legal_status`, `data_source` có trong DATA_SOURCES và không bị cấm | `engine/knowledge_notes.py` | độ dài trích từ tài liệu có bản quyền |
| L-05 Thời điểm | `resolve_at` sau ngày tạo và sau `model_cutoff`; không phân định trước hạn; sổ chỉ-ghi-thêm; đối chiếu Issue thật | `tools/ledger_intake.py`, `tools/resolution_intake.py`, `tools/ledger_audit.py` | `model_cutoff` là lời khai của mô hình; sự kiện đã xảy ra trước khi hỏi |
| L-06 Sổ thử | đăng ký trước khi chạy; không gian giả thuyết đóng băng; CI đối chiếu sổ với kết quả; báo DSR | `engine/research.py`, `engine/run_cycle.py`, `tools/laws_checks.py` | thử nghiệm chạy ngoài engine |
| L-07 Một kiến trúc | mỗi `ARCHITECTURE_v*.md` phải có dòng SUPERSEDED riêng trong ARCHIVE | `tools/laws_checks.py` | tài liệu kiến trúc đặt tên khác, nằm ngoài `architecture/` |
| L-08 Hiệu lực văn bản | văn bản pháp lý phải có `effective_from`; nguồn hết hiệu lực → ghi chú tự chuyển OUTDATED; cảnh báo quá hạn `review_by` | `engine/knowledge_notes.py`, `engine/run_cycle.py` | văn bản bị thay thế mà manifest chưa cập nhật |
| L-09 Người viết ≠ người chấm | PR: hai trường + bản chấm trên kho đúng commit; phân định: khác ghế mọi người viết; ghi chú: biên bản gắn nội dung, khác ghế | `tools/review_gate.py`, `tools/laws_checks.py`, `tools/resolution_intake.py`, `engine/knowledge_notes.py` | người điền có ghi đúng ai đã chấm/đọc nguồn không |
| L-10 Ba tay người | đề thi trong kho phải đã phát hành; công tắc an toàn lệch → lỗi; cảnh báo khi `main` chưa có luật bảo vệ | `tools/laws_checks.py`, `tools/validate.py`, `tools/ledger_audit.py` | Owner có thật là người bấm Merge không; bật ruleset là việc của Owner |

## Mô hình đe dọa và giới hạn (nói thẳng)

- Kho dùng một tài khoản GitHub (chủ kho) cho cả Owner và các ghế AI thao tác hộ. Máy vì thế không phân biệt được "Owner" với "AI dùng tài khoản Owner". Các trường `resolver`, `reviewed_by`, `auditor`, `read_by` là lời khai có ghi tên; máy kiểm dạng, ghế và sự nhất quán, không kiểm sự thật.
- Chủ kho có quyền quản trị viết lại được lịch sử nếu không bật ruleset. Kiểm toán chỉ-ghi-thêm bắt việc sửa sổ trong luồng thường (PR, push); force-push thì chỉ ruleset chặn được.
- Máy không mở nguồn để kiểm `quote` khi phân định.

## Hai chỗ chữ của `governance/LAWS.md` cần Owner sửa (PR này không sửa luật)

- L-10 cột "Máy kiểm" ghi "Branch protection trên main". Bắt buộc mọi thay đổi qua PR sẽ chặn vòng học và việc ghi dự báo tự động. Đề nghị ghi: "ruleset cấm force-push và cấm xóa nhánh; CI cảnh báo khi chưa bật".
- L-09 cột "Máy kiểm" nên thêm: "bản chấm GỘP ĐƯỢC kèm SHA dán thành bình luận PR".

## Lý do
- Đánh giá 16/11/2026: không có đường phân định thì Ledger không bao giờ ra điểm; sáu luật ghi "máy kiểm" nhưng chưa có mã; 4 test engine hỏng bị CI bỏ qua; engine chạy hằng ngày trái §4.3.
- Năm vòng chấm độc lập 17/11/2026 tìm ra 25 điểm, phần lớn cùng một gốc: luật L-09 so chuỗi rời rạc ở ba nơi, và một câu hỏi có thể nhận hai sự thật. Bản cuối gom về một định nghĩa ghế (`recognised_seat`, `same_provider`), một định nghĩa câu hỏi và ngày (`qkey`, `vn_day`), và thêm các neo nằm ngoài tệp (mục 6, 7).

## Điều kiện hoàn tác
- Workflow nhận/phân định làm CI đỏ hoặc mất dữ liệu Ledger 2 lần trong 30 ngày → hoàn tác mục 1–2 bằng PR riêng; dữ liệu đã ghi giữ nguyên.
- Vòng học hằng tuần thất bại 2 tuần liên tiếp vì thay đổi của PR này → hoàn tác mục 4 và 8 bằng PR riêng.
- Kiểm L-03 hoặc luật tên miền nguồn báo nhầm ≥ 3 lần trong 30 ngày → thu hẹp bằng PR riêng.
- Cổng chấm PR (mục 6) chặn nhầm ≥ 3 PR hợp lệ trong 30 ngày → nới bằng PR riêng, có ghế khác nhà chấm.

## Ảnh hưởng tới ARCHITECTURE.md
Dòng trạng thái đầu tệp; §3 (ghế thi công); §4.1 bước 2 và 4; §4.2 (kiểm định hai phía, chốt mẫu); §4.3 (ghi việc đã làm, còn C2).
