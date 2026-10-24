# TRUNG TÂM TÀI CHÍNH — Tầng học hiểu (Thư viện + Học viện), thiết kế v0.2

Ngày: 22/10/2026 · Kiến trúc sư trưởng: Claude · Nền: bản hiểu 21/10 (commit `3c9f69d`) · Thay bản v0.1 (ĐTT) ở phần miền và tên gọi.
Trạng thái: THIẾT KẾ, chưa có mã. Các mặc định ở mục 9 do Claude chọn vì Owner chưa quyết; Owner đổi được bằng một câu.

---

## 0. Một câu

Lắp cỗ máy học hiểu đang chạy thật ở MINH TRÍ vào hai chỗ rỗng của kho này: `library/` (Thư viện 4 tầng) và `academy/` (Học viện), dùng đúng khuôn KNOWLEDGE_NOTE và các hợp đồng kho đã viết (`hypothesis`, `knowledge_item`, `prediction`, `resolution`), đo bằng **nhóm đối chứng B**, không mở ngân sách API.

## 1. Vai và kênh

| Ghế | Vai | Kênh |
|---|---|---|
| Owner | gộp `main`, ký OWNER_MISSION, đổi luật/phạm vi, giữ đề thi | chat, GitHub |
| Claude | thiết kế, soạn lệnh, chấm, ra đề thi, giữ đề | Gmail gửi lệnh `[TTC] #N — …`, kết `Dừng.` |
| Ghế thi công (chưa lập; không phải MINH TRÍ) | chép nguồn, viết ghi chú, viết mã công cụ theo đặc tả, mở PR | đọc Gmail `[TTC] #N`, trả lời `BAO CAO [TTC] #N`; ghi lên nhánh `hoc-hieu`, không merge |
| CI (`tools/validate.py` + test) | kiểm máy, fail-closed | GitHub Actions |
| Nhóm đối chứng B | Claude trần, không thư viện, trả lời cùng đề | chat riêng, kết quả ghi `academy/results/` |

Luật kế thừa nguyên văn từ MINH TRÍ: người viết khác nhà người chấm; mọi khẳng định có địa chỉ; trích nguyên văn máy kiểm; `self_check` thật; không in nội dung tệp ra chat/email; tệp cho Claude đi bằng ZIP nhánh hoặc Claude tự đọc kho công khai.

## 2. Đối chiếu: cỗ máy MINH TRÍ ↔ khuôn kho đã có

| MINH TRÍ | Kho TTC đã có | Quyết định |
|---|---|---|
| Ghi chú đọc `notes/<id>.json` (mã đoạn, trích Pāli, `not_said`, `self_check`) | KNOWLEDGE_NOTE (v2.0 III): sources có ngày truy cập, `effective_date`, `applies_to`, `testable_implications`, status DRAFT→CITED→TESTED→PROVEN, `review_by` | **Gộp hai khuôn** thành `contracts/knowledge_note.schema.json` (mục 4) |
| Mệnh đề có mắt xích, ≥3 bài, `supersedes`, verdicts | `knowledge_item` (evidence_refs, valid_regimes, invalidation_reason, review_by) + `hypothesis` (invalidation_conditions) | Mệnh đề = `knowledge_item`; cách sai = `hypothesis.invalidation_conditions`; thêm trường `chain` và `supports` (mục 5) |
| Bài kiểm Chặng 4, sổ điểm `learning_scores` | Học viện: đề loại 1/2/3, ca mù ẩn danh, `academy/exams/`, `academy/results/`, nhóm đối chứng B | Dùng khuôn kho; sổ điểm = `academy/results/<exam_id>.json` theo `exam_item` (mục 6) |
| Hàng đợi đọc ngắn→dài | `library/INFORMATION_MAP.md` 15 nhóm thông tin | Hàng đợi = `library/reading_queue.yaml` sinh từ danh mục nguồn (mục 3) |
| Công cụ `reading_notes.py`, `propositions.py` | `tools/validate.py`, `ledger.audit` | Chuyển hai công cụ sang `engine/knowledge_notes.py`, `engine/knowledge_items.py`; `validate.py` gọi chúng |
| Năm luật mạch nghĩa, năm tiêu chí lệch trọng yếu | — | Giữ nguyên tên; là luật đọc văn bản, không phụ thuộc miền |

## 3. Nguồn và địa chỉ ("kinh" của tầng học hiểu)

- Chỉ nhận **tài liệu gốc công khai**: văn bản quy phạm (luật, nghị định, thông tư, chuẩn mực kế toán VAS), báo cáo tài chính đã kiểm toán và báo cáo thường niên do doanh nghiệp công bố, công bố của NHNN/UBCK/HOSE. Bài báo, phân tích, sách là **thứ cấp**: chỉ được dẫn ở mức CROSS_TEXT_SYNTHESIS, không bao giờ là bằng chứng gốc.
- Mỗi tài liệu chép vào `library/sources/<doc_id>/` dạng văn bản thuần (PDF → text có số trang), ghim trong `library/SOURCE_MANIFEST.json`: `doc_id`, tên, cơ quan phát hành, ngày phát hành, ngày truy cập, đường dẫn gốc, `sha256`, bytes, trạng thái pháp lý (lấy từ `governance/DATA_SOURCES.yaml`; chưa duyệt → không chép).
- **Địa chỉ**: `<doc_id>:p<trang>:<đoạn>` cho văn bản; `<doc_id>:t<bảng>:<dòng>` cho số liệu trong bảng. Công cụ kiểm địa chỉ tồn tại và trích nguyên văn, cùng chuẩn với `_quote_ok` của MINH TRÍ.
- Ba điều ghi nghiêm hơn bên kinh: `not_said` bắt buộc ≥ 2; mọi con số **đọc/đếm từ tài liệu gốc**, không từ tóm tắt; `effective_date` bắt buộc với văn bản pháp luật và chuẩn mực.
- Văn bản quy phạm pháp luật Việt Nam không bị bảo hộ bản quyền; BCTC là công bố bắt buộc. Vẫn ghi điều khoản nguồn vào `DATA_SOURCES.yaml` trước khi chép (bản hiểu D2).

## 4. KNOWLEDGE_NOTE v1 (hợp đồng mới `contracts/knowledge_note.schema.json`)

Trường bắt buộc: `id` (`KN-<tầng>-<slug>`), `tier` (1–4), `topic`, `doc_ids[]`, `applies_to` (ngành / loại DN / regime), `effective_date` (bắt buộc với T2 luật và chuẩn mực; `null` được phép với T1/T3 kèm lý do), `points[]` (mỗi ý: `id`, `vi`, `addresses[]`, `quote` nguyên văn, `kind` ∈ TEXT_ATTESTED | CROSS_TEXT_SYNTHESIS), `counts[]` (số đếm từ nguồn), `not_said[]` (≥2), `testable_implications[]` (mỗi hệ quả: câu kiểm được, dữ liệu nào, ngưỡng nào, ngày nào), `translation_or_reading_flags[]` (lệch giữa bản/nguồn, `material` + tiêu chí), `status` (DRAFT khi viết; CITED chỉ do Auditor gán; TESTED/PROVEN/DISPUTED/OUTDATED do mã gán), `review_by`, `read_by`, `self_check` (năm luật mạch nghĩa + `doubts`).
Giới hạn: < 16.000 byte. Ghi chú DRAFT không được dùng cho bất kỳ quyết định hay mệnh đề nào.

## 5. Mệnh đề: `knowledge_item` + `hypothesis`

Mệnh đề cốt lõi ghi theo `knowledge_item` hiện có, thêm hai trường: `chain[]` (mỗi mắt: `addresses`, `text_says`, `move`, `inference`), `supports[]` (≥3 tài liệu gốc độc lập, mỗi cái có địa chỉ + trích). Cách sai bắt buộc ghi ở `hypothesis.invalidation_conditions` và nối bằng `hypothesis_id`. Không có `invalidation_conditions` → mệnh đề ở OPEN mãi, không lên STRONG. Trần 60 mệnh đề đang dùng; `supersedes` thay cho sửa tại chỗ; RETIRED khi hai kỳ thi liên tiếp không dùng. Mọi tài liệu trong `chain` phải nằm trong `supports` và phải có KNOWLEDGE_NOTE ≥ CITED (quy tắc "chỉ cái đã kiểm mới lên tầng trên").

## 6. Học viện và thước đo

- `contracts/exam_item.schema.json`: `exam_id`, `kind` (1 tự luận có địa chỉ / 2 bài tập số có đáp án do mã tính / 3 ca mù ẩn danh), `question`, `competency`, `answer_key` (chỉ với loại 2; loại 1 và 3 chấm theo mắt xích), `authored_by`, `held_out: true`, `released_at`.
- Đề do Claude ra, **giữ ngoài kho** tới khi thi; sau kỳ thi mới commit vào `academy/exams/` cùng bài làm và điểm.
- Mỗi kỳ thi, cùng đề được trả lời bởi **A** (MINH TRÍ có thư viện, chỉ được dùng ghi chú ≥ CITED và mệnh đề ≥ SUPPORTED, phải dẫn id) và **B** (Claude trần, không thư viện). Điểm ghi `academy/results/<exam_id>.json`: từng mắt PASS/FAIL, điểm A, điểm B, **độ đúng của A khi bất đồng với B**. Chỉ số này là thước đo chính của tầng học hiểu (v1.0 III.4, v2.2 §1).
- Sau mỗi kỳ: phán quyết HELPED/HURT/UNUSED cho từng mệnh đề đã dùng (như MINH TRÍ); `competency_map` chỉ được nâng cấp bởi mã dựa trên kết quả, không bằng tay (A11).
- Mỗi kỳ thầy gài 1–2 ghi chú lỗi cố ý vào đợt chấm để đo người chấm.

## 7. Lộ trình: bốn PR, mỗi PR có điều kiện thoát

| PR | Nội dung | Ai | Thoát khi |
|---|---|---|---|
| **TTC-1** Khởi động | `governance/ARCHITECT_HANDOFF_20261022.md`; 3 hợp đồng `knowledge_note`, `exam_item`, `dossier`; `library/INDEX.md`, `library/SOURCE_MANIFEST.json` (rỗng đúng dạng), `library/reading_queue.yaml` (danh mục mục 9), `academy/curriculum.md` v0.1; cập nhật `contracts/README.md` (24) | MINH TRÍ viết, Claude chấm | CI xanh; `validate.py` bớt 3 cảnh báo tương ứng |
| **TTC-2** Công cụ | `engine/knowledge_notes.py`, `engine/knowledge_items.py` chuyển từ MINH TRÍ (địa chỉ trang/đoạn thay mã đoạn), test; `validate.py` gọi chúng; `daily_cycle.yml` chạy **đủ 7 test** (bản hiểu C5) | MINH TRÍ viết, Claude chấm | Test xanh; ghi chú mẫu bị từ chối đúng 12 ca lỗi |
| **TTC-3** Đọc rộng | Chép 30–50 tài liệu gốc miền hẹp; ghi chú DRAFT cho từng tài liệu; Auditor nâng CITED | MINH TRÍ đọc, Claude chấm mẫu ở mốc 10 và 20 | 20 ghi chú CITED; ≤2/20 sai nghĩa |
| **TTC-4** Thi lần một | 5 đề giữ kín; A và B cùng làm; sổ điểm; 3–5 mệnh đề OPEN đầu tiên có `invalidation_conditions` | Claude ra đề và chấm | Có số "độ đúng khi bất đồng với B" đầu tiên |

Không làm trong lộ trình này: mở API, chạm engine định lượng, Media OS, `OWNER_PROFILE`.

## 8. Quy tắc về kho công khai (bản hiểu D1) — mặc định

Kho **giữ công khai** (để Claude đọc thẳng và để kiểm chứng công khai). Đổi lại, luật cứng ghi vào `ARCHITECT_HANDOFF`: không commit vốn thật, mức lỗ chịu được, nhu cầu rút tiền, vị thế thật hay bất kỳ số liệu cá nhân nào; `OWNER_MISSION` chỉ điền phạm vi, khung thời gian và nguyên tắc; vốn giấy 1 tỷ VND là số giả lập, được phép. Nếu Owner muốn điền số thật thì chuyển kho sang riêng tư **trước**, và đường đọc của Claude đổi sang ZIP.

## 9. Mặc định Claude đã chọn (Owner đổi bằng một câu)

1. **Miền hẹp đầu tiên:** `doc_bctc` + `ngan_hang` + `chinh_sach_phap_luat` nền: Luật Kế toán 2015; Thông tư 200/2014 (chế độ kế toán DN) và các VAS liên quan BCTC (VAS 1, 21, 24); Luật Chứng khoán 2019; Nghị định 155/2020; Thông tư 96/2020 (công bố thông tin); Thông tư 41/2016 (tỷ lệ an toàn vốn ngân hàng); BCTC hợp nhất kiểm toán năm 2025 của 10 ngân hàng VN30. Khoảng 30–40 tài liệu, xếp ngắn → dài theo số trang.
2. **Ghế thi công:** chưa lập; **không phải MINH TRÍ** (dự án kinh Phật, không tham gia tài chính). Trong G0 Claude soạn một mình theo lệnh Owner 22/10; ghế thi công độc lập lập sau và phản biện hồi cứu.
3. **Nhánh làm việc:** `hoc-hieu`; Owner gộp khi Claude báo GỘP ĐƯỢC.
4. **Kho giữ công khai** theo mục 8.
