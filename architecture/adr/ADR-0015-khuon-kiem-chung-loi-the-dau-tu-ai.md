# ADR-0015: Bổ sung khuôn kiểm chứng lợi thế đầu tư AI — thiết kế có điều kiện, không mở hệ điều hành mới

- Ngày: 2026-11-21
- Trạng thái: **PROPOSED — CHƯA HIỆU LỰC**. Chỉ là hồ sơ quyết định để phản biện và Owner cân nhắc; không thay đổi ARCHITECTURE v3.0.
- Người đề xuất / soạn chữ: ChatGPT (OpenAI), theo yêu cầu Owner tổng hợp chuỗi thảo luận về AI đầu tư, phản biện mù, xác suất, vĩ mô và tối ưu vốn.
- Người chấm (L-09): xem bình luận L-09 của PR #68; Claude (Anthropic), khác nhà cung cấp với người viết.
- Owner duyệt (L-10): **chưa**. Gộp PR này chỉ đưa văn bản lên `main` ở trạng thái **PROPOSED**; **ACCEPTED** chỉ được ghi bằng một PR riêng khi Owner quyết định, qua L-09 và Owner gộp.
- Mốc bằng chứng đọc: main tại commit **1d2f5c58acbeb3155118babc92bbb1bc9e06b382** (2026-11-20); các số bên dưới là trạng thái tại mốc này, không phải chỉ số hiện thời bất biến.
- Tính chất: bổ sung nguyên tắc lựa chọn năng lực và thiết kế thí nghiệm tương lai, **không** bổ sung model, API, hệ thống điều phối, dữ liệu, quyền giao dịch hay công tắc vốn vào runtime.

## 1. Bài toán thật: đo lợi thế, không đo độ thuyết phục của chatbot

Đích dài hạn là một cỗ máy nghiên cứu có thể tạo quyết định đầu tư **có chất lượng hơn** đối chứng công bằng, sau chi phí và trong ngân sách rủi ro; không cam kết thắng thị trường hoặc giỏi hơn mọi chuyên gia.

Ba phép thử phải tách riêng:
1. **Năng lực bằng chứng và dự báo sự kiện**: độ đúng, Brier, calibration của A so với B theo mẫu cố định của kiến trúc v3.0. Đây là phép thử **toàn TTC so với Claude trần**, không phải phép thử alpha, không phải so với chuyên gia giao dịch và không tự chứng minh hiệu quả Thư viện.
2. **Năng lực định lượng / đầu tư**: kết quả danh mục ngoài mẫu so với benchmark phù hợp, trên cùng universe và cùng quy tắc chi phí/khớp lệnh/rủi ro. Đo lợi nhuận ròng, alpha và độ bất định, max drawdown, thanh khoản, turnover, phơi nhiễm và tính ổn định qua các chế độ thị trường.
3. **Vượt con người**: chỉ được kết luận sau một thí nghiệm **tiến về tương lai, đăng ký trước**, đối chiếu chiến lược của máy với người/nhóm người có thông tin, vốn danh nghĩa, giới hạn rủi ro, lịch quyết định, giá có thể khớp và chi phí tương đương; đánh giá lợi nhuận *và* rủi ro. Không dùng thành tích A/B LLM hoặc một đường NAV đẹp để thay thế.

Không dùng một tỷ lệ đúng chiều đơn độc để tuyên bố thắng. Mọi kết luận phải có số mẫu, giai đoạn, khoảng bất định, mức độ thử nhiều giả thuyết và báo cáo cả kết quả âm.

## 2. Giữ ba nửa, một sổ; bổ sung năng lực theo adapter thay vì nhiều hệ AI

Tuyệt đối không dựng “Multi-AI OS” hoặc orchestrator độc lập trong giai đoạn hiện tại. Dùng khung sẵn có:

- **Nửa CHỨNG MINH**: nguồn dữ liệu có bản gốc → giả thuyết được đăng ký → baseline → đánh giá ngoài mẫu → Ledger/scorecard/negative findings. Engine định lượng hiện nay là đối chứng âm; không đổi không gian 13 feature × 3 model, không đổi top-5/horizon 20 phiên chỉ bằng ADR này.
- **Nửa HỌC**: tài liệu gốc và trích nguyên văn đã CITED → trích đặc trưng định tính *có thể kiểm toán* (ví dụ thay đổi kế toán, khoản thu bất thường, rủi ro pháp lý) → kiểm tra người/thuật toán. LLM không được nhớ giá, EPS, nợ, lãi suất hay tự tạo số liệu; số liệu đến từ parser/nguồn bảng và được xác minh. Bản DRAFT hoặc không có ngày công bố không vào quyết định.
- **Nửa QUẢN TRỊ**: L-01…L-10, Risk/Capital/Human Gate, source provenance, quyền từ chối/giữ tiền mặt. Không mở API trả phí và không thêm ghế chính thức chỉ vì đề xuất phản biện mù.

## 3. Bốn năng lực nghiên cứu được nhận, kèm giới hạn

**A. Evidence Bus / point-in-time.** GitHub, manifest, Ledger và hash hiện là trục bằng chứng đủ nhỏ. SHA-256 chứng minh byte không đổi, **không chứng minh số liệu đúng**. Mỗi giá trị ảnh hưởng nghiên cứu phải liên kết được tới nguồn/phiên bản, kỳ dữ liệu, ngày công bố, ngày có thể sử dụng, ngày quan sát, lần sửa đổi và bản dẫn xuất. Thiếu timestamp quan trọng → cách ly hoặc gắn nhãn RETROSPECTIVE, không tự nâng thành PIT.

**B. Proposer–Critic độc lập.** Người/mô hình đề xuất nêu giả thuyết, phản chứng và điều kiện bác bỏ trước khi thấy kết quả. Ghế khác nhà cung cấp kiểm dữ liệu, leakage, giả định, nguồn. Nếu có phản biện mù, che tác giả và kết luận để giảm thiên kiến, nhưng **không che nguồn, thời gian hay hash**. Không lấy đa số GPT/Gemini/Grok làm chân lý. Phán quyết PASS/FAIL/INCONCLUSIVE phải dựa trên chứng cứ và cổng L-09; không có thêm “ghế C” hoặc quyền vượt Owner.

**C. Dự báo phân phối có hiệu chuẩn.** Ước lượng xác suất tăng, lợi nhuận vượt benchmark, phân vị thua lỗ và bất định chỉ khi đủ dữ liệu/số lượng sự kiện. Mô hình xếp hạng hiện thời KHÔNG được gọi là mô hình lợi nhuận xác suất. Phải kiểm Brier/log loss cho biến nhị phân, quantile/pinball loss hoặc CRPS cho phân phối, reliability và coverage ngoài mẫu, so với baseline cố định. Ba tỷ lệ bull/base/bear gán tay hay Monte Carlo từ phân phối chưa xác minh chỉ là kịch bản minh họa, không phải xác suất đo lường.

**D. Risk Veto + học có cổng.** Khả năng không ra quyết định là tính năng bắt buộc. Sai nguồn, dữ liệu nhìn trước, thiếu lịch sử thành phần, giá/sự kiện quyền chưa xác minh, không mô hình ACTIVE hoặc trượt giới hạn rủi ro → từ chối bằng chứng hoặc để tiền danh nghĩa ở trạng thái CASH tùy phạm vi. Drawdown trigger phải tính đến khả năng HOSE khóa sàn, thiếu đối ứng và gap; cắt lỗ theo luật không đồng nghĩa bảo đảm thoát ở giá dự kiến. New data → kiểm drift + performance → đề nghị retrain → kiểm định độc lập → Owner/deployment gate; **không tự retrain và tự promote**.

Hai ý tưởng **chưa mở**: mô hình agent-based và “phòng thí nghiệm tối ưu chính sách vĩ mô”; portfolio CVaR/optimal allocation và điều phối đa mô hình tự động. Chúng chỉ được xem xét khi nền đo lường và dữ liệu vượt cổng, không lấy độ phức tạp làm thành tích.

## 4. Đặc tả một bài toán hẹp — giữ cấu hình hiện hành cho tới khi Owner quyết

Bài toán nghiên cứu ban đầu vẫn là **xếp hạng lợi nhuận vượt universe sau 20 phiên** trong không gian mô hình đang khóa, danh mục giấy top-5, định kỳ 20 phiên. Đây là tập thử nghiệm hiện hành, **không** tự chuyển thành VN100, 15–30 mã hay hệ thống lướt sóng.

Khi chuẩn bị phép thử mới, đăng ký trước và đóng băng trong trial registry:
- Universe tại từng ngày, nguồn xác thực, điều kiện thanh khoản và cách xử lý mã mới/hủy niêm yết; không lựa mã theo thành tích về sau.
- Mốc dữ liệu được biết (information cutoff); bộ dữ liệu, bản dẫn xuất, source fingerprint; đặc trưng, nhãn, chân trời, ngày xử lý nhãn, quy tắc không dùng thông tin được công bố muộn.
- Baseline tối thiểu: mô hình ngây thơ/đều trọng số trong cùng universe và có thể chọn không giao dịch; benchmark chỉ số/ETF đầu tư được khi có chuỗi total-return và quy tắc so sánh nhất quán. VN-Index giá, VN30 theo kỳ và bình quân đều 30 mã **không được tráo tên**.
- Chia train/validation/test theo thời gian, walk-forward và purge/embargo cho nhãn chồng lấn; holdout không bị chọn lại sau khi nhìn kết quả.
- Phí, thuế, slippage, lô, biên độ, khóa trần/sàn, volume participation, lệnh không khớp, thanh khoản và quyền cổ đông; giả định thiếu bằng chứng phải nêu rõ và stress test.
- Metric chính, metric phụ, rủi ro, quy tắc dừng, ngân sách thử nghiệm, phương pháp xử lý nhiều phép thử (L-06), điều kiện chấp nhận và tiêu chí hoàn tác.
- Kết quả có thể là **NO_EDGE/INCONCLUSIVE**; giữ nguyên dự báo âm và lần thử bỏ dở để không tô đẹp thống kê.

Đo alpha bằng hiệu quả đầu tư đã chuẩn hóa rủi ro, độ không chắc chắn và so sánh hai bên trên cùng kỳ; công bố cả hiệu quả tuyệt đối lẫn tương đối. Không đặt mức lợi nhuận hứa hẹn. Các ngưỡng chấp nhận chính thức phải được đăng ký trước phép thử, không chọn sau khi nhìn đường NAV.

## 5. Khoảng trống đã đọc trên main — không diễn giải thành kết quả đầu tư

Tình trạng sau mốc ghim: xem `reports/PIT-001_20261121.json` và danh mục việc của ADR-0016. Các số dưới đây chỉ đúng tại commit đã ghim, không tự cập nhật theo `main`.

Tại commit ghim:
- reports/scorecard.json ngày 20/11/2026 ghi **6 dự báo, 0 resolved, 0 timing_valid**, 3 cặp A/B; chỉ 1 cặp bất đồng thô và chính cặp đó bị chặn tính năng lực vì chứng cứ thời điểm (legacy_unproven). Mẫu 194 cặp bất đồng hợp lệ **không được đổi**.
- state/ENGINE_STATE.json ngày 20/11/2026 ghi **222 trials, 0 model ACTIVE, paper_nav 1.000.000.000 (vốn giấy khởi tạo), max drawdown giấy 0**. Chưa có minh chứng alpha thực tế.
- config.yaml vẫn **universe_basis: CURRENT**, dùng 30 mã cố định để nghiên cứu giá từ 2016; nhãn thiên lệch sống sót đã bật. data/vn30_history.csv mới có lịch sử thành viên từ **04/08/2025** và có các mốc 2026; không thể tự suy danh sách trước đó.
- CSV VN30 thực tế dùng các cột effective_date/ticker/action/source_id; ADR-0008 mô tả khuôn effective_date/ticker/change/source_url/source_status. Tests/test_vn30_history.py xác minh schema CSV hiện có và hash tài liệu; chưa có kết luận đây là tương thích schema với khuôn ADR. Phải đối chiếu/chốt adapter/contract bằng một quyết định riêng, không tự ghi đè CSV.
- reports/G1_DATA_SPRINT0_20261120/A3_LO_HONG.md và reports/VN30_UNIVERSE_DIFF_20261119.md mô tả khác nhau về phạm vi PDF HOSE 2510691. Manifest có mô tả mục VN30 bên trong tài liệu VNAllshare. Cần mở **PDF gốc**, kiểm mục và ngày hiệu lực, không quyết từ tên tệp hoặc từ tóm tắt.
- Hai sự kiện quyền TCB và VCB trong hồ sơ G1 còn CAN_DOI_CHIEU; ADR-0009 đã yêu cầu tách raw bất biến và verified-adjusted, và **chưa cho phép sửa engine/adjust.py** chỉ bằng quyết định nền.
- Thư viện mới 1/40 nguồn SOURCED, ghi chú vẫn DRAFT theo PROJECT_STATE.yaml. Không trích DRAFT làm yếu tố quyết định.

Các bản ghi trên chứng minh nhu cầu sửa **chất lượng đo lường**, không chứng minh mô hình đang tốt hoặc xấu. Không có khảo sát người đầu tư để khẳng định “AI mạnh hơn con người”.

## 6. Roadmap cổng điều kiện — không xây module nếu đầu vào chưa đạt

### Quan hệ với ADR-0016 và ADR-0017 (đã ACCEPTED)

- ADR-0015 vẫn là **PROPOSED, chưa hiệu lực**, chỉ giải thích nguyên tắc kiểm chứng; không mở đường điều hành hay bảng tiêu chí thăng bậc thứ hai. Nếu có khác biệt về quyết định, cổng, thang vốn, lịch triển khai hay quyền mở việc thì **ADR-0016 và ADR-0017 đang ACCEPTED được áp dụng**. Không dùng ADR-0015 để thay thế hai ADR đó.
- **PIT-001 đã thực hiện**, bằng `tools/pit001_audit.py` và `reports/PIT-001_20261121.json`; kết luận **NOT_READY**, không phải đã đạt cổng PIT. Các việc khắc phục tiếp theo chỉ theo lệnh/phạm vi riêng được Owner duyệt.
- Hai hàng **BASELINE-001** và **PAPER/RISK** dưới đây là diễn giải của phép thử **FWD-001** theo **QĐ-5, ADR-0016**, không phải hai chương trình hay hai điều kiện mở vốn mới.
- **EDGE-001**, **FORECAST-001** và **PORTFOLIO/HUMAN** chỉ là **nguyên tắc nghiên cứu**, không phát lệnh, không khởi tạo thí nghiệm, không mở gate độc lập. Tiêu chí nâng bậc và trình tự bắt buộc theo mục **"Thang vốn: tiêu chí số" của ADR-0016**; cơ chế SCN-001 theo **ADR-0017** độc lập, không bị ADR-0015 thay đổi.
- Bảng sau chỉ lưu mục đích thẩm định đã đề xuất tại mốc ghim; **không tự chứng minh READY**, không thay thế quyết định Owner hay cổng có hiệu lực.

| Cổng | Việc được phép chuẩn bị | Bằng chứng bắt buộc để đi tiếp |
|---|---|---|
| PIT-001 (đã chạy; NOT_READY) | Lập ma trận thiếu/đủ lịch sử VN30, đối chiếu source và CSV, PDF HOSE, kiểm quyền TCB/VCB, so actual universe engine với tuyên bố báo cáo | Bản kiểm toán có đường dẫn, hash, phạm vi ngày, trạng thái UNKNOWN; không sửa source/engine/config |
| G1 HIỆN HÀNH | Thu nguồn, phản biện ghi chú, dự báo A/B và đối chiếu dấu nhận theo luật | Điều kiện thoát G1 của §8; nguồn nguyên bản, lịch công bố, số dự báo hợp lệ; không gọi 6 dự báo hiện có là đã chấm |
| BASELINE-001 (tham chiếu FWD-001, ADR-0016) | Đặc tả một thí nghiệm 20 phiên dùng cùng dữ liệu, phí, lot, universe, benchmark, bộ negative controls | Đăng ký trước L-06, chứng minh PIT/khả năng khớp, test leakage; không đổi frozen_space bất hợp lệ |
| EDGE-001 (nguyên tắc, chưa mở việc) | Đánh giá thêm giá trị của đặc trưng doanh nghiệp/LLM đã CITED so với baseline; ablation có và không LLM | Có cải thiện ngoài mẫu với kiểm soát multiple testing, nguồn truy xuất được, kiểm tra sai phạm; thua/không rõ thì không promote |
| FORECAST-001 (nguyên tắc, chưa mở việc) | Dự báo phân phối/hiệu chuẩn với hợp đồng target riêng | Brier/quantile/coverage ngoài mẫu cải thiện hơn baseline; không suy xác suất từ score xếp hạng |
| PAPER/RISK (tham chiếu FWD-001; R1/R1a/R1b theo PR riêng) | Stress test khớp lệnh, chi phí, thanh khoản, regime; giữ mặc định CASH khi không đủ model | So kết quả giấy và backtest, biến động alpha, tail risk, giới hạn được Owner quy định và đủ nguồn |
| PORTFOLIO/HUMAN (HOÃN; không mở việc) | Sau alpha được xác nhận, mới xét optimizer, CVaR, phân bổ vốn danh nghĩa và đối chứng người | Bằng chứng tăng giá trị *so với phân bổ đơn giản* trên tương lai; luật/quyền/Owner gate, ADR riêng |

Bài toán **engine kịch bản** đang bị hoãn bởi ADR-0005 và điều kiện mở lại đã sửa trong **ADR-0007**: phán quyết cố định mẫu A/B với 194 cặp bất đồng thuộc phép thử + **ít nhất 10 ghi chú CITED**. ADR-0015 không tạo đường vòng để mở sớm. Portfolio optimizer/CVaR cũng đã hoãn tại ADR-0008 cho tới khi có lợi thế. Không coi bảng này là quyền khởi chạy các công việc bị hoãn.

## 7. Acceptance tests (dành cho PR triển khai sau, chưa thêm mã)

- **As-of / time travel:** với mỗi dòng BCTC, doanh nghiệp, vĩ mô, giá và sự kiện quyền, truy vấn trước ngày công bố không được thấy thông tin đó; không suy observed_at gần đây là bằng chứng dữ liệu lịch sử có PIT.
- **Universe:** đúng 30 thành phần theo nguồn tại mọi ngày đủ chứng cứ; ngày không có bản chính thức phải trả UNKNOWN/loại khỏi kết luận PIT, không dùng danh sách hiện tại thay thế.
- **Nguồn và dẫn xuất:** thay byte/hash, revision, ngày công bố hoặc một sự kiện CAN_DOI_CHIEU phải tác động cờ xác minh; raw giữ nguyên; không cho hàng chưa VERIFIED vào verified-adjusted; rollback có nguồn.
- **Leakage:** đưa feature mang thông tin tương lai, tráo ngày công bố, shuffle nhãn hay dùng thành viên biết sau cutoff phải làm test đỏ / dập tín hiệu.
- **Thước đo:** giữ đúng benchmark, phí, lệnh không khớp, dữ liệu test; đánh giá bằng confidence intervals thích hợp cho chuỗi phụ thuộc và tài liệu đầy đủ về số phép thử.
- **Đóng góp thật:** nếu loại dữ liệu LLM/macro/phản biện mà hiệu quả không kém đi ở holdout đã khóa, tầng bổ sung không được gọi là có lợi thế tăng thêm.
- **Fail closed:** khi thiếu dữ liệu hoặc 0 model ACTIVE, không tự tạo giao dịch; paper/research không tự nhảy lên live. Các trạng thái chưa đủ mẫu được ghi INCONCLUSIVE.
- **Học có cổng:** dữ liệu mới một mình không tự kích hoạt promote/retrain; cần chứng minh performance decay và gate độc lập.

## 8. Phạm vi không làm và bảo vệ ranh giới

- **Không sửa** architecture/ARCHITECTURE.md, governance/LAWS.md, governance/SAFETY_STATE.yaml, config.yaml, engine, trial ledger, forecast ledger, danh mục giấy, ruleset; không mở API hoặc giao dịch.
- **Không đưa** vốn thật, vị thế thật, khẩu vị rủi ro/khả năng chịu lỗ của Owner vào kho công khai (L-03).
- **Không đưa ra** lệnh khuyến nghị mua/bán mã cụ thể, target giá kèm hành động (L-02).
- **Không đổi** mẫu A/B 194, benchmark hiện hành bằng cách đổi tên, danh sách frozen model/feature, hay mốc xét lại 31/03/2027.
- **Không áp** mô hình tối ưu chính sách vĩ mô như bằng chứng nhân quả nếu chỉ là tương quan; macro là tín hiệu/điều kiện stress test khi đủ dữ liệu, không là “đầu não” ra quyết định.
- **Không hợp thức hóa** văn bản pháp lý bằng text-only hoặc SHA-256 của bản chép, khi thiếu PDF gốc và pdf_check (ADR-0012/0014 nếu được duyệt).

## 9. Điều kiện hoàn tác (L-07)

Đây là một đề xuất chưa hiệu lực nên có thể đóng PR mà không tác động runtime. Nếu Owner sau này chấp nhận:
- Sau **hai kỳ rà soát quý** đầu tiên, nếu kế hoạch này không tạo được một đánh giá baseline ngoài mẫu có nguồn, hoặc gây thêm số thành phần vận hành mà không nâng chất lượng kiểm định, đề nghị Owner dừng mở rộng và giữ duy nhất PIT + Ledger + baseline.
- Nếu có xung đột bằng chứng với ADR-0005/0007/0008/0009, ADR-0016/0017 đang ACCEPTED hoặc cổng L-01…L-10, phần triển khai liên quan **mặc định dừng**, không âm thầm ghi đè quyết định có hiệu lực.
- Bất kỳ nâng cấp model, universe, optimization hay deployment đều có ADR/PR riêng, L-09 khác nhà cung cấp và Owner gộp; rollback phải giữ nguyên kết quả âm và lịch sử dữ liệu.

## 10. Ảnh hưởng dự kiến tới kiến trúc hiệu lực (CHỈ SAU KHI DUYỆT)

Chỉ nếu một PR riêng sau này được Owner phê duyệt để đưa ADR-0015 thành ACCEPTED, mới xem xét một đoạn ngắn bổ sung ở architecture/ARCHITECTURE.md §4.3 hoặc §8, trỏ tới ADR-0015 để xác nhận: **phát triển theo bằng chứng ngoài mẫu; PIT và baseline trước; xác suất, phản biện và portfolio optimization là năng lực có cổng, không được tự sinh thêm runtime hay quyền vốn**. Không có ARCHITECTURE v4, không sửa các ADR đang ACCEPTED.

**PIT-001 đã có báo cáo NOT_READY; các việc tiếp theo tuân theo ADR-0016/0017 và PR/lệnh riêng, không “mở một AI mới”.**
