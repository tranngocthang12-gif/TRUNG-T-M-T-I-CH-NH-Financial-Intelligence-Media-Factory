# Changelog

## v3.0.7b — 2026-11-18 (PR-B, L-01 ghim tệp gốc) — Grok (xAI) soạn; ADR-0012 PROPOSED; chưa gộp
- `sha256`/`bytes` giữ nghĩa hash của `text.md`. Mọi dòng manifest phải có `original_sha256`, `original_bytes`, `original_path`, `text_sha256`, `text_bytes`. Bỏ các trường đó không qua cổng nguồn. Manifest trên `main` đang rỗng, không giữ đường vòng cho dòng cũ.
- Hash từng trang tính cả bảng, không chỉ đoạn văn. `page_crosscheck()` không phải biên bản đối chiếu PDF. `SOURCED` và ghi chú `CITED`/`TESTED`/`PROVEN` cần thêm `pdf_check` gắn đúng hash `text.md` và hash PDF, do ghế khác người đọc ghi chú. Máy không đọc ảnh trang.
- Luật Kế toán 88/2015: nếu khai tệp gốc thì chỉ nhận SHA-256 `1fd9336a…cca50`, 2566253 byte, 35 trang. Kho này chưa ghim PDF và hàng đợi vẫn `QUEUED`.

## v3.0.7c — 2026-11-18 (PR-C, giấy tờ) — Grok (xAI) soạn; ADR-0013 PROPOSED; chưa gộp
- §8 khớp sáu dự báo F-37–F-42 và pha `V3_G0_DAT_DIEU_KIEN_KY_THUAT`. Không hủy cột dừng/đảo 3 tuần và không dời mốc ADR-0002.
- Header ADR-0010 và dòng danh mục chuyển ACCEPTED theo PR #35 đã gộp (merge `400de577`). Quyết định 1–7 không viết lại.
- Ghi phạm vi phép thử: cả bộ TTC so với Claude trần, không đo riêng Thư viện. Báo cáo tương lai tách câu trả lời ghế B khỏi phần biểu mẫu. “Sau sáu tháng” là mốc xem xét. Không sửa `SAFETY_STATE.yaml`, không sửa Ledger, không sửa mẫu 194.
- Ruleset `Protect main history` chỉ có cấm xóa nhánh và cấm force-push. Không gọi PR #43 là vi phạm L-09. Không yêu cầu Owner bật required status checks: `ledger_intake.yml` và `resolution_intake.yml` đẩy thẳng `main`, chưa chứng minh rule đó vẫn cho đẩy. Việc này chờ quyết định riêng.


## v3.0.6 — 2026-11-18 (ghế thi công; sửa giấy tờ) — nội dung do Grok (xAI) soạn theo lệnh Owner; ADR-0010; Owner gộp sau L-09
- **Ai soạn:** `authored_by: Grok (xAI)` là lời khai attribution, không phải kết luận của lịch sử Git. Commit `7ff741b5833179d597c8751d838e23aa5eecf427` (tạo ADR-0010, `requirements.txt`, `state/PROJECT_STATE.yaml`, `architecture/ARCHIVE.md`, `BOOT.md`, sửa handoff): Git author và Git committer đều `tranngocthang12-gif <tranngocthang12@gmail.com>`, login `tranngocthang12-gif`. Commit `02e5d7e` và `4641fcf`: author và committer `Grok (xAI)`, login `grok-xai`. Metadata chỉ chứng minh ai ghi commit lên Git. Không sửa tác giả commit đã đẩy.
- **Ba điểm trên `4641fcf`:** (A) metadata `7ff741b` như dòng trên. (B) ARCHITECTURE §4.3 thêm một câu trỏ ADR-0009; không sửa quyết định 1–7 của ADR đó. (C) header ADR-0009: Owner duyệt là 18/11/2026 giờ Việt Nam (17/11 18:32:23 UTC).
- **Ghế thi công:** Grok (xAI). Không phải MINH TRÍ. Không được gộp, sửa luật, mở API, chạm engine ngoài lệnh. Quyết định 9 của ADR-0003 giữ nguyên chữ đã chấm; không thêm câu vào tệp đó.
- **Pha:** `state/PROJECT_STATE.yaml` ghi `V3_G0_CHUA_THOAT`. Không có biên bản Owner bác riêng nhánh "chỉ giữ Ledger" ngày 17/11. Kết luận đang lưu là ADR-0002: không thu hẹp v3.0; mốc 31/03/2027. Hai đồng hồ không phải một luật.
- **ADR-0008:** header lật ACCEPTED chỉ vì Owner gộp PR #31 (merge `8c4fd4305b8154adda2ea0e1abf4e43cd7b647ab`). Không viện `docs/RESEARCH_POINT_IN_TIME_LIMITATIONS.md`.
- **ADR-0009:** ACCEPTED. PR #32 đưa chính tệp lên main (merge `432f456`), không phải chỉ disclosure. L-09: `GỘP ĐƯỢC — commit c4d8a0348e8edfc8526a7440c5b73eb9d0446b36`, người viết ChatGPT (OpenAI), người chấm Grok (xAI), hai job L-09 success. Điều 7 chưa đổi engine. Câu "PR #32 không chấp nhận ADR-0009" ở commit `02e5d7e` là sai và đã bỏ.
- **TTC-2:** làm một phần. Có `engine/knowledge_notes.py`. Không có `engine/knowledge_items.py`. CI là `.github/workflows/tests.yml`. `daily_cycle.yml` không chạy đủ 7 test.
- **Kênh:** không đặt kênh mới. Gmail `[TTC] #N` (handoff mục 2) chưa bị thu hồi. Lên `main` là PR (ADR-0003 quyết định 6). `hoc-hieu` là mặc định Claude, Owner chưa chọn.
- **`requirements.txt`:** ghim pandas 2.3.3, numpy 2.2.6, scikit-learn 1.7.2, pyyaml 6.0.3, joblib 1.6.0, yfinance 1.8.0, jsonschema 4.26.0. pandas 2.3.3 là hạ major so với pandas 3.0.5 mà máy rà soát cài từ trần cũ. Không có log CI chứng minh bộ pin là bộ CI đã phân giải. Không đổi số pin trong commit sửa này.
- **Chữ khác:** tiêu đề §5, đường dẫn `docs/TTC_TANG_HOC_HIEU_v0.2.md`, các chỗ gọi MINH TRÍ là ghế hoặc là ghế A, BOOT bước 10, ARCHIVE các tệp trước v3.0, bàn giao 22/10.
- **Không làm:** không thu v3.0, không đổi mẫu 194, không thêm ghế C, không điền OWNER_MISSION hay GOVERNOR_POLICY, không chép thư viện. Không gán cho ADR-0002/0003 một điều cấm "cắt vòng chấm" mà hai tệp không viết.

## v3.0.5 — 2026-11-18 (dữ liệu và rủi ro sau nghiên cứu GitHub; thứ tự Owner duyệt) — Claude soạn, Owner gộp; ADR-0008
- **Thiên lệch sống sót:** `config.yaml` `universe_basis: CURRENT`; báo cáo chu kỳ và `state/ENGINE_STATE.json` (`universe_basis`, `universe_bias`) ghi rõ backtest dùng VN30 hiện tại cho toàn bộ lịch sử nên kết quả bị đẩy lên. Danh sách theo từng kỳ: khuôn `data/vn30_history.csv` ở ADR-0008, việc dữ liệu giao ghế thi công hoặc Owner.
- **BCTC theo ngày công bố:** `kind: FINANCIAL_STATEMENT` trong `SOURCE_MANIFEST.json` bắt buộc `period_end`, `published_on` (`period_end ≤ published_on ≤ accessed_on`); `engine/knowledge_notes.usable_on`; ghi chú trích BCTC có `effective_date` ≥ ngày công bố (`contracts/knowledge_note.schema.json` mô tả, `library/sources/README.md`).
- **Giấy:** phiên khớp có biến động ≥ 95% biên độ của mã (`adjust.limits`) coi như khóa — không mua ở khóa trần, không bán ở khóa sàn; ghi `UNFILLED_LIMIT_UP`/`UNFILLED_LIMIT_DOWN`, lệnh giữ lại thử phiên sau (`engine/paper.locked`).
- **Sụt giảm lớn nhất:** `research.max_drawdown`, `nav_drawdown`; báo cáo có cột "Sụt giảm lớn nhất" cho từng lần thử và dòng sụt giảm lớn nhất của NAV giấy; `ENGINE_STATE.json` `paper_max_drawdown`. `research/trials.csv` giữ 17 cột.
- Test: `tests/test_governance.py` `RiskAndBiasTests`; `tests/test_knowledge_notes.py` `test_financial_statements_are_usable_only_from_publication_date`.
- Văn bản: ADR-0006, ADR-0007 ghi ACCEPTED (PR #30); `state/PROJECT_STATE.yaml` ghi PR #30 đã gộp.

## v3.0.4 — 2026-11-17 (giấy tờ sau PR #29; kho giá ghi tăng dần; lệnh Owner) — Claude soạn, Owner gộp; ADR-0006, ADR-0007
- Danh mục ADR và ba tệp ADR-0002, ADR-0004, ADR-0005: ACCEPTED 17/11/2026 (PR #29, commit gộp `b8158be`; người chấm Gemini, `GỘP ĐƯỢC — commit 6201090`).
- `governance/LAWS.md` (Owner ra lệnh; hiệu lực khi Owner gộp): cột "Máy kiểm" của L-09 thêm "bản chấm GỘP ĐƯỢC kèm SHA dán thành bình luận PR"; của L-10 thay "Branch protection trên `main`" bằng "ruleset cho `main` cấm force-push và cấm xóa nhánh; CI cảnh báo khi chưa bật" (ADR-0003 mục "Hai chỗ chữ"). Nội dung các luật không đổi.
- Đóng 19 PR nháp dòng UMLF và 5 Issue đi kèm theo L-07 (một kiến trúc; hướng song song chưa có ADR). Nhánh giữ nguyên, mở lại được. `state/PROJECT_STATE.yaml` cập nhật.
- **ADR-0006 — kho giá ghi tăng dần (C2).** `data/store/prices.csv.gz` đóng băng; dòng mới vào `data/store/prices/YYYY-MM.csv`, chỉ nối thêm (`engine/data.save_store`, `load_store`; `config.yaml` `data.store_dir`). Kiểm toán mục 1a (`tools/ledger_audit.store_errors`, `store_snapshot_errors`): kho cũ giữ nguyên từng byte, tệp tháng cũ là tiền tố của bản mới; chỉ kiểm khi commit gốc đã có `data.store_dir`. `tests/test_quality_gate.py` cấy lỗi bằng cách dựng lại kho tạm.
- **ADR-0007** (theo phản biện tư vấn của Grok ở PR #29): điều kiện mở lại engine kịch bản (ADR-0005) là phán quyết của phép thử A–B, không phải 60 dự báo; scorecard thêm `disagreements_all` (mẫu số của `disagreement_rate`).

## v3.0.3 — 2026-11-17 (hoàn thiện kiến trúc sau PR #28) — Claude soạn, Owner gộp; ADR-0002, ADR-0004, ADR-0005
- **ADR-0002** (quyết định của Owner 17/11/2026): không thu hẹp v3.0 theo điều kiện hoàn tác của ADR-0001; dự báo là việc dài hạn; mốc xét lại mới 31/03/2027. Câu hỏi `event_before_date` không vào phép kiểm định chốt mẫu A–B (ghế A được tìm web, ghế B thì không) — vẫn là cặp, vẫn vào tỷ lệ bất đồng; báo riêng `disagreements_out_of_scope` (`engine/ledger.py`, báo cáo vòng học).
- **ADR-0004** — đóng bốn việc tồn của bản chấm vòng 10: (1) giữ hành vi kiểm toán đỏ tới `resolve_at` cho dự báo thiếu dấu nhận đúng hạn, kèm lý do; (2) gọi đúng khóa chọn mẫu: "theo số Issue hoàn tất cặp"; (3) Brier theo ghế khi VOID tính là sai (`brier_void_worst`); (4) mốc v3.0.2 cố định `research.v302_boundary` trong `config.yaml` — kiểm toán chỉ miễn commit nằm trong lịch sử của mốc; mốc không đổi được (PR so với đầu `main` lúc gộp, không so với `base.sha` có thể đã cũ); `tools/validate.py` đòi mốc khi đã có `research.legacy_pin` (`tools/laws_checks.check_v302_boundary`).
- **ADR-0005**: tạm gác "engine cờ kinh tế" (engine kịch bản), kèm điều kiện mở lại.
- **L-06**: `tools/registry_push.py` không còn coi sổ trên `main` trùng từng byte với bản đang chạy là "đã đẩy xong". Hai vòng học đăng ký cùng một giây ra cùng một dòng JSON (`registered_at` chỉ tới giây); vòng sau từng chạy tiếp backtest. Nay dừng, không ghi đè, không chạy backtest — mã đã nằm trên `main` thì lần sau lấy số tiếp theo.
- ADR-0003 chuyển ACCEPTED (PR #28, commit `0b0bffc`). Không sửa `governance/LAWS.md`.

## v3.0.2 — 2026-11-17 (làm nốt G0/G1: phân định, chấm A–B, mười luật vào máy kiểm) — Claude soạn, Owner đưa lên kho; ADR-0003
Sau mười vòng chấm độc lập của ghế khác nhà cung cấp (năm vòng đầu 25 điểm; vòng 6 thêm 4 điểm HIGH; vòng 7 thêm 2 HIGH và 2 MEDIUM; vòng 8 thêm 2 HIGH và 2 MEDIUM; vòng 9 thêm 2 HIGH, 2 MEDIUM và 1 LOW; vòng 10 — vòng cuối — thêm 1 MEDIUM chặn gộp — đều đã sửa) và một lượt Claude tự rà toàn bộ theo lệnh Owner. Bảng luật ↔ máy kiểm và các giới hạn: `architecture/adr/ADR-0003-phan-dinh-va-van-hanh.md`. Hướng dẫn thao tác cho Owner: `docs/HUONG_DAN_VAN_HANH.md` mục 6–10.
- **Nhận dự báo** (`tools/ledger_intake.py`): ngày tính theo giờ Việt Nam; `model_cutoff` dạng YYYY-MM và `resolve_at` phải sau ngày cắt dữ liệu (L-05); `author_seat` bắt đầu bằng tên ghế (L-09); ghế B bắt buộc `prompt_hash` đúng phiên bản prompt chuẩn có hiệu lực ngày Issue mở (vòng 9); mỗi ghế một dự báo cho một câu hỏi, A và B cùng luật và cùng nguồn; thân Issue không được trùng tiêu đề; nhận dấu phẩy thập phân; ghi `issue_author`. Vòng 6: `p`/`base_rate` chỉ nhận số thập phân viết bằng chữ số 0–9 (`NaN`, `Infinity`, `1e309`… bị từ chối; sổ ghi với `allow_nan=False` và kiểm chuỗi từ chối JSON không chuẩn); `resolve_at` đúng dạng `YYYY-MM-DD`; `resolution_source` phải nêu tên miền; câu hỏi đã phân định không nhận thêm dự báo.
- **Phân định** (Issue mẫu "Resolution", `tools/resolution_intake.py`, `resolution_intake.yml`) → `ledger/resolutions.jsonl` có chuỗi hash, khớp `contracts/resolution.schema.json`: một câu hỏi một sự thật cho mọi dự báo; đã phân định thì khóa (kể cả VOID); không trước hạn — kể cả VOID (vòng 9) — trừ YES khi cả câu hỏi là `event_before_date`; người phân định khác ghế với mọi người viết; nguồn phải thuộc tên miền đã hứa. Vòng 6: tên máy chủ tách bằng `urllib` từ từng đường dẫn `https://` (không dò chuỗi) và mọi đường dẫn phải thuộc tên miền đã hứa — `https://nso.gov.vn@evil.com`, `https://evil.com/path/nso.gov.vn`, `https://evil.com/?referer=nso.gov.vn` bị từ chối.
- **Chấm A–B** (`engine/ledger.py` → `reports/scorecard.json` mục `issue_forecasts`, báo cáo vòng học): Brier theo ghế (so với xác suất nền và 0,5), hiệu chuẩn, VOID đếm riêng; cặp = cùng câu hỏi, cùng ngày; chỉ chấm khi cả hai đã phân định cùng sự thật; kiểm định nhị thức hai phía chốt trên 194 cặp bất đồng đầu tiên theo thứ tự ghi dự báo, cặp VOID tính bất lợi cho kết luận đang xét (vòng 9); dòng hỏng không làm vỡ vòng học.
- **Sổ thử L-06 + Deflated Sharpe** (`engine/research.py`): đăng ký có hash chuỗi trước khi chạy; không gian giả thuyết đóng băng trong `config.yaml`; CI đối chiếu sổ với `trials.csv`; báo cáo in Sharpe và DSR. Vòng 6: trong vòng học trên GitHub, dòng đăng ký được đẩy lên `main` trước khi backtest chạy (`tools/registry_push.py`, `TTC_REGISTRY_PUSH=1`); đẩy không được thì không chạy; vòng học hỏng giữa chừng không làm mất lần thử, mã thử không bị dùng lại, báo cáo liệt kê mã bỏ dở.
- **Thư viện có máy kiểm** (`engine/knowledge_notes.py`): L-01 ghim sha256, địa chỉ, trích nguyên văn; L-04 giấy phép và nguồn được phép; L-08 hiệu lực, tự chuyển OUTDATED; L-09 biên bản chấm gắn nội dung (`note_sha256`), khác ghế; TESTED/PROVEN đóng cho tới khi có Học viện.
- **Cổng chấm PR** (`tools/review_gate.py`, `review_gate.yml`, mẫu PR): hai trường khác ghế + bản chấm dán thành bình luận PR có dòng đầu đúng `GỘP ĐƯỢC — commit <SHA>` (không chữ nào khác trên dòng đó); chạy bằng mã của `main`.
- **Kiểm toán sổ** (`tools/ledger_audit.py` trong CI): sổ chỉ-ghi-thêm so với commit gốc; mỗi dòng đối chiếu với Issue thật trên GitHub; cảnh báo khi `main` chưa có luật bảo vệ. Vòng 6: **dấu nhận** — workflow nhận đăng hash của dòng vừa ghi thành bình luận của `github-actions[bot]`, kiểm toán đòi mỗi dòng có dấu nhận trên đúng Issue, chưa sửa, trong 6 giờ sau khi Issue mở và trước ngày `resolve_at`, không có hash thứ hai cho cùng mã (dòng viết sau khi biết kết quả không mượn được giờ của Issue cũ); và `tools/validate.py` **chạy lại luật nhận và luật phân định** trên mọi dòng Issue đã có trong sổ.
- **Vòng 7** (chấm commit `2ba54fc`): (1) dòng phân định thiếu `resolution_issue` chỉ được trỏ tới dự báo của engine, engine không dùng nó để chấm dự báo Issue; dòng dự báo không từ Issue phải đúng là dòng engine (`P-…`). (2) Kết quả thử: 210 kết quả đầu ghim sha256 trong `config.yaml`; dòng neo lịch sử có sha256 ở đầu sổ đăng ký; engine chỉ ghi thêm vào `research/trials.csv` (`research.append_trial_results`), không viết lại dòng cũ; PR không được thêm kết quả hay dòng đăng ký; trên `main` commit ghi kết quả phải có đăng ký ở commit liền trước; thêm `paper/*.csv` vào danh sách chỉ-ghi-thêm. (3) Tổng số lần thử ở báo cáo và trạng thái gồm cả lần bỏ dở (`research.total_trials`). (4) Dấu nhận không còn 15 phút miễn kiểm; workflow mới `ledger_audit.yml` chạy kiểm toán sau mỗi lần robot ghi sổ, sau vòng học và mỗi ngày. Thiếu `jsonschema` là lỗi, không còn bỏ qua lặng lẽ.
- **Vòng 8** (chấm commit `69e282a`; ADR-0003 quyết định 10 và 11): (1) **Thứ tự ghi của hai robot.** Robot nhận dự báo và robot phân định chạy xong khác thứ tự mở Issue thì bản trước ghi ra một sổ mà kiểm lại đánh đỏ mãi. Nay luật lúc ghi dựa vào trạng thái sổ: câu hỏi đã có dòng phân định thì không nhận thêm dự báo (kể cả dự báo mở trước Issue phân định); một Issue phân định chỉ ghi kết quả cho dự báo mở trước nó và không ghi gì nếu sổ đang có dự báo của câu hỏi mở cùng lúc hoặc sau nó. Trước khi ghi, robot tự chạy lại toàn bộ luật kiểm (`ledger_intake.ledger_errors`, đúng hàm của `validate`) trên trạng thái sau khi ghi; có lỗi mới thì không ghi. Robot không ghi dự báo khi dấu nhận sẽ không kịp hạn (job chạy lại sau 5 giờ 30 phút, hoặc Issue mở trong 30 phút cuối trước ngày `resolve_at`). Có test chạy đúng đoạn lệnh của hai workflow trên kho git thật với hai robot xen kẽ giữa lúc commit và lúc đẩy. **Phục hồi không sửa sổ:** Issue bị từ chối thì mở Issue mới; chạy lại job chỉ trả dấu nhận cho dòng khớp thân Issue lúc mở; dự báo có dấu nhận muộn mà câu hỏi đã VOID thì kiểm toán không tính là lỗi; dấu nhận của dòng phân định không có hạn 6 giờ. (Hai điều của vòng 8 — VOID ghi được trước `resolve_at`, và dự báo VOID bị bỏ khỏi cặp A–B — đã bị vòng 9 thay: xem dưới.) (2) **Đường ghi dự báo của engine đóng** (`config.yaml` `ledger.engine_forecasts: closed`): sổ chỉ nhận dòng từ Issue; dòng mang mã `P-…` — thiếu trường hay đủ trường — đều làm `validate` đỏ trước khi vòng học chạy; engine không ghi, không chấm, không tính điểm dòng engine; `engine/ledger.py` có hợp đồng đầy đủ cho dòng engine (`engine_row_error`) và không còn vỡ vì dòng thiếu trường; `validate` chỉ chấp nhận `closed`. (3) **Khuôn `research/trials.csv`**: tiêu đề phải là đúng 13 cột gốc hoặc đúng 17 cột, mỗi dòng đủ số ô, từng byte đúng dạng chuẩn; kết quả lịch sử phải để trống bốn cột mới; kiểm toán theo commit gốc chỉ cho tiêu đề giữ nguyên hoặc từ 13 lên 17 cột. (4) **Kiểm toán sau khi ghi** đọc lại bình luận dấu nhận tối đa 6 lượt cách nhau 30 giây (vòng 10 đổi thành 15 lượt) khi Issue còn trong hạn (robot đẩy commit trước rồi mới đăng bình luận; hai robot có thể xen kẽ) — hết lượt vẫn thiếu thì vẫn là lỗi; bước đăng dấu nhận của workflow tự thử lại tối đa 5 lần.
- **Vòng 9** (chấm commit `a69f204`; ADR-0003 quyết định 12 và phần sửa ở quyết định 1, 2, 3, 4, 7, 10). Lượt sửa này chỉ đóng năm điểm của bản chấm, không thêm đường mới. (1) **Dấu nhận cho dự báo B đã bị từ chối.** Phiên bản prompt chuẩn của ghế B ghim theo ngày trong `governance/control_b_prompts.jsonl` (tệp chỉ ghi thêm); `prompt_hash` phải là phiên bản có hiệu lực ngày Issue mở — cùng một luật lúc nhận và lúc kiểm lại (trước đó kiểm lại chỉ đòi 64 ký tự hex). Chạy lại job chỉ trả dấu nhận khi dòng trong sổ khớp thân Issue **và** việc có dòng đó qua được phép tự kiểm của đường ghi; áp dụng cho cả robot phân định. (2) **VOID và mẫu của phép thử A–B.** VOID không ghi được trước `resolve_at` nữa. Mẫu chốt là 194 cặp bất đồng đầu tiên theo thứ tự ghi dự báo — cố định trước khi có kết quả — và chỉ ra phán quyết khi cả 194 cặp đã đóng; cặp VOID vẫn giữ chỗ trong mẫu và tính bất lợi cho kết luận đang xét; báo cáo in tỷ lệ VOID theo ghế, theo cặp, theo cặp bất đồng. Hệ quả vận hành: dự báo thiếu dấu nhận đúng hạn làm kiểm toán đỏ tới `resolve_at`, lúc đó mới hủy được câu hỏi. (3) **Mốc v3.0.2** của kiểm toán kết quả thử xác định bằng tổ tiên (tệp mốc từng có trong lịch sử), không bằng việc tệp có mặt ở commit và commit cha. (4) **Kiểm toán đọc lại dấu nhận** theo loại dòng: dòng phân định bất kể Issue mở từ bao giờ; dòng dự báo khi còn trong hạn 6 giờ và trước ngày `resolve_at`. (5) Nguồn phân định chỉ nhận `https://`.
- **Vòng 10 — vòng chấm cuối** (chấm commit `9367976`): năm điểm vòng 9 được xác nhận đã đóng; còn 1 MEDIUM chặn gộp, đã sửa: kiểm toán đọc lại dấu nhận 15 lượt cách nhau 30 giây (420 giây) thay cho 6 lượt (150 giây), để phủ hết chuỗi thử lại của bước đăng dấu nhận ở hai workflow nhận (5 lần, chờ 20 + 40 + 60 + 80 = 200 giây); khoảng chờ được tính từ lịch thử lại đó (`tools/ledger_audit.py` `POST_TRIES`, `POST_BACKOFF`, `ATTEST_TRIES`) và một test đọc hai tệp workflow để giữ hai bộ số khớp nhau. Bốn việc tồn sau gộp (không chặn gộp) ghi ở cuối ADR-0003.
- **Luật khác**: L-03 quét số định danh/số tài khoản; L-07 kiểm theo từng dòng của ARCHIVE; L-10 đề thi trong kho phải đã phát hành; công tắc an toàn lệch là lỗi.
- **Vận hành**: engine hằng tuần (thứ Sáu), kiểm luật trước và sau khi chạy; CI chặn gộp chạy mọi tệp test, test sửa tệp của kho thì đỏ; workflow không chèn biểu thức `${{ }}` nào vào lệnh (có test soát; vòng 6 sửa nốt ô `trials` của vòng học). Sửa `tests/test_adjustment.py`: kiểm point-in-time theo bảng sự kiện (chặt hơn bản gốc).
- **Văn bản**: ARCHITECTURE §3, §4.1, §4.2, §4.3; ADR-0001 ACCEPTED; ADR-0003; `state/PROJECT_STATE.yaml` cập nhật theo BOOT; README của `library/sources/` và `library/notes/` khớp với mã kiểm.
- **Không sửa**: `governance/LAWS.md` (chỉ Owner sửa; hai chỗ cần sửa chữ ghi ở ADR-0003).
- **Còn lại (ADR riêng):** kho dữ liệu ghi tăng dần (C2).

## v3.0.1 — 2026-11-16 (sửa lỗi Ledger P0 của G0) — Claude soạn, Owner đưa lên kho
- **Vòng học không vỡ khi có dự báo Issue.** Dòng từ Issue "Forecast" không có `id` và `resolution_rule` là chuỗi, nên `engine/ledger.py` (`resolve`, `scorecard`) ném lỗi → `daily_cycle` dừng ngay sau dự báo đầu tiên. Nay engine chỉ chấm bằng giá dòng của chính nó; dòng Issue được đếm theo ghế A/B trong `reports/scorecard.json` (`issue_forecasts`) và báo cáo vòng học.
- **Một hash chuỗi cho mọi bên ghi.** Đường experts của engine ghi `prev_hash`/`hash` như `tools/ledger_intake.py` (trước đó sẽ làm đỏ `validate`). Dòng Issue có `id` = `F-<số Issue>`.
- **L-02 kiểm ngay khi nhận.** Dự báo chứa từ khóa khuyến nghị bị từ chối trước khi ghi (Ledger chỉ ghi thêm; một dòng sai sẽ làm `validate` đỏ và dừng vòng học vĩnh viễn).
- **`ledger_intake.yml`.** Chỉ nhận Issue lúc mở (`opened`) do chính Owner mở (kho công khai: người lạ không ghi được vào sổ); bỏ sự kiện `labeled` (Issue cũ gắn nhãn muộn có thể đã bị sửa sau khi biết kết quả, trái L-05); bỏ nhóm concurrency chung (GitHub hủy run đang chờ → mất dự báo khi mở nhiều Issue liền); mỗi run tự lấy `main` mới nhất, tính lại chuỗi và thử lại khi bị trùng.
- **`daily_cycle.yml`.** Rebase rồi mới đẩy, thử lại tối đa 5 lần (Ledger intake có thể đã đẩy trong lúc vòng học chạy).
- **Test.** `tests/test_ledger_compat.py` (chặn merge): Issue A/B + dự báo engine + Issue tiếp theo trong một tệp; engine chấm đúng một dòng, đếm đúng theo ghế, chuỗi hash nguyên vẹn; L-02 từ chối khi nhận. Thêm `tools/__init__.py`.

## v3.0 — 2026-10-22 (G0: hợp nhất kiến trúc, luật, đường ghi dự báo) — Claude soạn, Owner đưa lên kho
- **Một kiến trúc.** `architecture/ARCHITECTURE.md` thay v0.1–v2.2; bản cũ liệt kê SUPERSEDED trong `architecture/ARCHIVE.md`; ADR-0001 có điều kiện hoàn tác 30 ngày.
- **Luật vận hành.** `governance/LAWS.md` L-01…L-10; `tools/laws_checks.py` kiểm máy L-02 (không khuyến nghị), L-07 (một kiến trúc), hash chuỗi Ledger; gọi từ `tools/validate.py`.
- **Ledger không cần API.** Mẫu Issue "Forecast" + `ledger_intake.yml` + `tools/ledger_intake.py`: kiểm schema `contracts/forecast_issue.schema.json`, từ chối ngày đã qua (L-05), ghi `ledger/predictions.jsonl` với `issue_created_at`, `sha256`, `prev_hash`.
- **Hợp đồng.** Thêm `knowledge_note`, `exam_item`, `dossier` (v2.0 IX) và `forecast_issue`; tổng 25.
- **Học viện / Thư viện.** `academy/curriculum.md` v0.1 theo thứ tự có bằng chứng; `library/INDEX.md`, `library/SOURCE_MANIFEST.json`, `library/reading_queue.yaml` (miền hẹp đầu tiên, đã cập nhật TT 99/2025, NĐ 245/2025, Luật 56/2024).
- **CI.** `tests.yml`: việc `gate` (test luật, chống nhìn trước, validate) chặn merge; việc `full-suite` chạy đủ 7 test ở chế độ thông tin (`continue-on-error`) vì 4 test engine hiện lỗi khi thu thập trong môi trường mới (C5 bản hiểu, sửa ở ADR riêng); `daily_cycle.yml` không đổi.
- **Chưa làm (ADR riêng):** hạ engine về hằng tuần, sổ thử + Deflated Sharpe, kho dữ liệu append.

## v1.1 — 2026-09-26 (phiên sửa lỗi sau kiểm tra)
- **Giá điều chỉnh (engine/adjust.py).** Kho `data/store` vẫn giữ GIÁ GỐC append-only làm bằng chứng. Hệ số điều chỉnh
  (chia tách / cổ tức cổ phiếu / cổ tức tiền) là dữ liệu DẪN XUẤT, tính lại toàn bộ mỗi lần, point-in-time, ghi
  `data/derived/adjustment_factors.csv` kèm `computed_at`. Sự kiện quyền: `data/corporate_actions.csv` (nhập tay, có nguồn)
  + `data/derived/yahoo_actions.csv` (tải lại mỗi lần). Feature, nhãn, regime, paper trading, Ledger resolution dùng giá điều chỉnh;
  paper áp sự kiện quyền vào vị thế đang nắm giữ.
- **Kiểm tra chất lượng.** Biến động vượt biên độ sàn (HOSE ±7%, SHB ±10% khi còn ở HNX) mà không có sự kiện quyền → cờ lỗi
  (`data/derived/quality_flags.csv`); ô lỗi bị loại khỏi feature (121 phiên nhìn lại), nhãn và chấm Ledger (VOID). Tỷ lệ lỗi
  20 phiên gần nhất > 1% → hôm đó không nghiên cứu, không dự báo, không khớp lệnh giấy. Hiện tại: 147/72.172 ô bị cờ (0,20%),
  0% trong 20 phiên gần nhất.
- **Xóa kết quả nghiên cứu đã học trên giá SAI**: `research/trials.csv` (16 thử nghiệm), `state/bandit.json`,
  `state/model_registry.json`. Lý do: giá Yahoo chưa điều chỉnh cổ tức cổ phiếu (TCB −49,5% ngày 11/06/2024, VCB −33,1% ngày
  03/03/2025 là cú rơi giả) và còn ~145 ô biến động vượt biên độ không có sự kiện → feature/nhãn của vòng 25/09 bị nhiễm.
  `knowledge/candidates/` chưa từng được tạo (không phát hiện nào sống sót) nên không có gì để xóa. `data/store` KHÔNG bị xóa.
  `state/ENGINE_STATE.json` và báo cáo 25/09 giữ làm lịch sử, sẽ được vòng kế tiếp ghi đè.
- **Nguồn dữ liệu.** PyPI đang cách ly (quarantined) gói `vnstock` và phụ thuộc `vnai` → không cài; bỏ bước
  `pip install vnstock` khỏi workflow. Yahoo là nguồn giá chính (`config.yaml: data.sources: [yahoo]`, `--source live`).
  Lỗi nguồn dữ liệu (từng mã, từng nguồn, kể cả sự kiện quyền Yahoo và RSS) ghi đầy đủ vào báo cáo chu kỳ và
  `state/ENGINE_STATE.json` (`data_ingest`, `news_errors`), kể cả ngày bỏ qua vòng học. Cập nhật `governance/DATA_SOURCES.yaml`.
  Test: `tests/test_ingest_errors.py`.
- **tools/validate.py** kiểm cấu trúc v2.x: file/thư mục bắt buộc (library/, academy/, DATA_SOURCES.yaml, OWNER_PROFILE.md,
  3 bản kiến trúc hiện hành), MỌI file YAML trong repo, cấp độ hợp lệ trong competency_map, đường dẫn `library:` của
  competency_map (cảnh báo nếu chưa có), contract đếm theo kiến trúc v2.0 (21/24 — thiếu knowledge_note, exam_item, dossier:
  cảnh báo, chưa chặn). Thiếu file bắt buộc / YAML hỏng / cấp độ sai → LỖI.
- `ARCHITECTURE_v2.0.md` chuyển vào `architecture/` cho khớp BOOT.md. `llm_review.py` đi qua Budget Governor
  (`tests/test_llm_review_budget.py`).
- `academy/competency_map.yaml`: hạ `tin_tuc_su_kien` và `dinh_luong` từ PRACTICED về SYNTHESIZED cho tới khi có bằng chứng
  dữ liệu thật.
- Test mới: `tests/test_adjustment.py` (TCB/VCB trên dữ liệu thật, point-in-time, loại ô lỗi, VOID, paper),
  `tests/test_quality_gate.py` (cổng chất lượng); `tests/test_no_lookahead.py` kiểm thêm trường hợp có cờ lỗi.
  Dữ liệu giả lập nay tôn trọng biên độ ±7%.
- **Chưa làm được / còn mở:** sự kiện quyền TCB, VCB nhập từ hiểu biết + khớp tỷ lệ với bước nhảy giá, CHƯA gắn đường dẫn CBTT
  (không truy cập được HOSE/VSD từ môi trường phiên này); 147 ô Yahoo vượt biên độ chưa giải thích (đang bị loại);
  phần tải sự kiện quyền Yahoo chưa chạy với mạng thật (Yahoo bị chặn trong môi trường phiên, sẽ chạy lần đầu trên Actions);
  3 contract v2.0 và khung Thư viện/Học viện GĐ1 chưa có.

## v1.0-GĐ1 — 2026-09-26 (AUTO HỌC)
- Prediction Ledger: dự báo ghi trước khi biết kết quả (ledger/predictions.jsonl), kết quả ghi riêng (ledger/resolutions.jsonl).
- Auditor (code): loại dự báo có nguồn không tồn tại, mã ngoài universe, horizon/xác suất sai luật → ledger/rejected.jsonl.
- Resolution + Scorecard (code): Brier, calibration, so với baseline MẠNH NHẤT (xác suất nền lịch sử, luôn 50%).
- Fact Layer tin tức (RSS) với id = hash(link).
- Chuyên gia Claude: news@v1 và devils_advocate@v1 (lần gọi riêng, xác suất riêng, cũng bị chấm).
- Budget Governor: chuyên gia chỉ chạy khi Owner bật chi tiêu, đặt trần ngày/tháng và đơn giá; nhật ký memory/economic/api_spend.csv.
- 3 contract mới: PREDICTION, RESOLUTION, PROCEDURE.
- Kiểm thử tests/test_ledger_pipeline.py (chuyên gia giả lập, không tốn API).

## v0.2 — 2026-09-26
- Thêm bộ não học máy `engine/`: data append-only, 13 feature, regime, walk-forward có embargo, ngưỡng t tăng theo số thử, cổng 12 tháng gần nhất, meta-learning Thompson sampling, model registry, decay từ dự báo thực tế, paper trading khớp T+1, attribution, LLM phản biện tùy chọn.
- GitHub Actions chạy vòng học 16:30 mỗi ngày giao dịch và tự commit kết quả.
- Test chống look-ahead và diễn tập trên dữ liệu giả lập có quy luật đảo chiều.

## v0.1 — 2026-09-26
- Khởi tạo bộ não Trung Tâm Tài Chính theo Architecture v0.1.
- 18 core contracts, governance, safety state, orchestrator, auto mode, state, memory.
