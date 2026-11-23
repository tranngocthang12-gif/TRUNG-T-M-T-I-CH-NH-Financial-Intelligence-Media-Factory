# ADR-0019: Đổi phạm vi — phân tích một mã cổ phiếu và kỷ luật đầu tư

- Ngày: 2026-11-23
- Trạng thái: ACCEPTED 23/11/2026 theo lệnh Owner, hiệu lực khi Owner gộp PR này. QĐ-P12 và QĐ-P13 là mặc định do kiến trúc sư đề xuất; Owner đổi được trước khi gộp.
- Người đề xuất: Claude Project TTC (Anthropic), ghế kiến trúc sư trưởng. Chép vào kho: phiên Claude Code (Anthropic).
- Người chấm: theo L-09, ghi trong thân PR.
- Owner duyệt: lệnh trong chat Project ngày 23/11/2026, 18:05 và 18:38 giờ Việt Nam; xác nhận bằng việc gộp PR này.

## Bối cảnh

- v3.0 cùng ADR-0002, ADR-0013, ADR-0016 và ADR-0017 đặt hai phép đo: bộ máy TTC so với Claude trần (sổ dự báo A–B), và tín hiệu trên giá so với đối chứng (máy dò 13 feature × 3 mô hình, FWD-001). ADR-0017 thêm sổ chấm nhanh SCN-001 cho dự báo chỉ tiêu doanh nghiệp.
- Tại `main` `db33327` ngày 23/11/2026: sổ dự báo có 16 dòng, chưa dòng nào được phân định; `research/trials.csv` có 222 lần thử và không cho kết luận; thư viện 1/40; kho chưa có hồ sơ mã nào.
- Phép thử A–B cần khoảng 194 bất đồng đã chấm (§4.2). Kiến trúc sư ước tính: với nhịp làm tay hiện nay, phán quyết sớm nhất rơi vào năm 2028.
- Lệnh Owner ngày 23/11/2026: không xây kiến trúc để đo thắng thị trường hay hơn AI ngoài dự án. Xây cách phân tích một mã cổ phiếu từ chi tiết nhỏ, kiến trúc kỷ luật đầu tư, bài học của người thành công và người thất bại, và dùng Sàn Zero làm phòng thí nghiệm trên chỉ số mô phỏng. Xây trên nền đang có, loại phần thừa. Việc đầu tư là của Owner; Owner dựa vào phân tích, nhận định và phản biện của dự án để tự quyết.
- L-07: v3.0 gộp ngày 24/10/2026; tới 23/11/2026 là đủ 30 ngày vận hành. ADR này sửa phạm vi của v3.0 và không lập tệp kiến trúc thứ hai.

## Quyết định

### QĐ-P1 — Mục đích và ranh giới

Dự án giúp Owner phân tích một mã cổ phiếu và giữ kỷ luật đầu tư. Owner quyết định và tự đặt lệnh.

| Dự án làm | Dự án không làm |
|---|---|
| Phân tích một doanh nghiệp từ tài liệu gốc, soi chi tiết nhỏ | Chứng minh thắng thị trường; so tài với AI ngoài dự án |
| Nêu nhận định kèm mức chắc chắn và điều kiện sai | Đưa lời khuyên mua, bán hay nắm giữ một mã (L-02) |
| Phản biện chính bản phân tích của mình | Tự đặt lệnh; giữ tiền |
| Giúp Owner viết và giữ quy tắc của riêng mình | Chọn trường phái, tỷ trọng hay mức lỗ thay Owner |
| Cho Owner tập kỷ luật trên chỉ số mô phỏng | Dùng kết quả mô phỏng làm bằng chứng cho mã thật |
| Rút bài học từ ca thành công và ca thất bại | Dò mẫu trên giá; giao dịch trong ngày, ngoại hối, tiền mã hóa |

### QĐ-P2 — Ba sản phẩm, một phòng tập, một nền

- Ba sản phẩm: hồ sơ mã (ghế viết); bản phản biện (ghế khác hãng); phiếu kỷ luật (riêng tư, của Owner).
- Một phòng tập: Sàn Zero, tách hẳn khỏi ba sản phẩm.
- Một nền: nền dữ kiện, gồm tài liệu gốc ghim sha256, ghi chú có địa chỉ, giá và sự kiện quyền.
- Hình này thay hình "ba nửa, một sổ" ở §2. Không thêm tác tử, không thêm máy mới.

### QĐ-P3 — Cách làm việc

1. Chia bài phân tích thành mệnh đề nhỏ có đáp án kiểm được.
2. Mỗi mệnh đề một trọng tài: số và trích dẫn do máy kiểm; lập luận do ghế khác hãng phản biện; dự đoán do thời gian, qua hậu kiểm.
3. Mỗi câu trong hồ sơ mang một trong bốn nhãn, lấy từ bốn trường của `contracts/research_report.schema.json`: ĐÃ KIỂM (`verified_facts`), SUY LUẬN (`inferences`), GIẢ ĐỊNH (`assumptions`), CHƯA BIẾT (`unknowns`).
4. Mỗi hồ sơ giữ ít nhất ba giả thuyết cạnh tranh: tốt, xấu, và "không có gì đặc biệt". Giả thuyết bị bác vẫn được ghi kèm lý do.
5. Số do mã tính. AI đọc, lập luận và viết.

### QĐ-P4 — Nền dữ kiện

- Tài liệu gốc ghim sha256 (L-01, ADR-0012). Mỗi con số trong hồ sơ trỏ về `<doc_id>:p<trang>` hoặc `<doc_id>:t<bảng>:<dòng>`.
- Giá chỉ dùng để mô tả, không để tính tín hiệu.
- Sách có bản quyền: chỉ lưu địa chỉ trang và trích không quá 15 từ (L-04).
- Thư viện mở theo đúng tài liệu mà hồ sơ đang làm cần.

### QĐ-P5 — Hồ sơ mã

Dùng khuôn đã có: `dossier`, `research_report`, `valuation_case`, `hypothesis`. Mười hai mục:

1. Doanh nghiệp làm gì: tiền đến từ đâu.
2. Loại doanh nghiệp: tăng trưởng nhanh, ổn định, theo chu kỳ, đang phục hồi, hay giàu tài sản.
3. Lợi thế cạnh tranh: bằng chứng số 5–10 năm.
4. Ban lãnh đạo và cổ đông: lợi ích có cùng chiều cổ đông nhỏ không; người nội bộ đang làm gì.
5. Sức khỏe tài chính: nợ, khả năng trả, dòng tiền.
6. Chất lượng lợi nhuận: kết quả các điểm soi ở QĐ-P6.
7. Tăng trưởng gần đây: quý gần nhất và ba năm.
8. Định giá theo khoảng: hai tới ba phương pháp, giả định ghi rõ.
9. Thị trường chung và chu kỳ.
10. Cung cầu và xu hướng giá: chỉ mô tả.
11. Ba kịch bản và điều kiện sai; ngày xem lại.
12. Ca tương tự, cả thành lẫn bại (`library/casebook/`).

Luật của hồ sơ:

- Mục 8 ghi khoảng giá trị ước tính theo từng giả định, không kèm hành động.
- Mục 10 không sinh tín hiệu.
- Hồ sơ kết bằng danh sách CHƯA BIẾT, không kết bằng việc nên làm gì.
- Không lập hội đồng tác tử. Các vai trong `experts/investment/` là các mục của hồ sơ.

### QĐ-P6 — Đọc soi chi tiết

Mỗi tài liệu cho một thẻ đọc theo thiết kế của ADR-0017: con số kèm câu trích nguyên văn, và phần so với lời cũ của chính doanh nghiệp. Mười lăm điểm soi, bản đầu:

1. Lợi nhuận so với dòng tiền kinh doanh, nhiều năm.
2. Phải thu và tồn kho tăng nhanh hơn doanh thu.
3. Lợi nhuận một lần: thanh lý, đánh giá lại, thu nhập khác.
4. Đổi chính sách kế toán, đổi ước tính khấu hao hay dự phòng.
5. Chi phí được vốn hóa; chi phí trả trước tăng bất thường.
6. Giao dịch với bên liên quan; cho vay, ủy thác, trả trước lớn.
7. Ý kiến kiểm toán; đổi công ty kiểm toán; chênh lệch số trước và sau kiểm toán.
8. Nợ vay, lịch đáo hạn, trái phiếu, bảo lãnh ngoài bảng.
9. Pha loãng: phát hành riêng lẻ, cổ phiếu thưởng cho nhân viên, trái phiếu chuyển đổi.
10. Giao dịch của người nội bộ; cổ phiếu của lãnh đạo bị cầm cố.
11. Thay kế toán trưởng, giám đốc tài chính, thành viên hội đồng quản trị.
12. Lời ban lãnh đạo kỳ trước so với kết quả kỳ này.
13. Cổ phiếu có bị sở cảnh báo, kiểm soát hay hạn chế giao dịch không.
14. Thanh khoản và tỷ lệ cổ phiếu tự do chuyển nhượng.
15. Dấu hiệu bị "phím hàng".

Danh sách này được sửa sau hồ sơ đầu tiên bằng PR thường.

### QĐ-P7 — Bản phản biện

Một ghế khác hãng với ghế viết hồ sơ đọc hồ sơ và tài liệu gốc, rồi viết bốn phần: luận điểm ngược mạnh nhất; ba điều hồ sơ nói mà chưa chứng minh; các con số then chốt đã đối chiếu lại với tài liệu gốc; một việc Owner nên tự kiểm.

### QĐ-P8 — Kỷ luật

- Bản quy tắc riêng: mười dòng do Owner tự điền, ghi bằng tỷ lệ phần trăm. Mười dòng là: trường phái chính; số mã tối đa; tỷ trọng tối đa cho một mã; tỷ trọng tối đa cho một ngành; tỷ lệ tiền mặt tối thiểu; đòn bẩy; mức lỗ tối đa cho một vị thế theo từng nhãn; mức sụt giảm của cả danh mục thì ngừng mua mới; số lệnh mua mới tối đa mỗi tháng; thời gian chờ từ lúc đọc xong hồ sơ tới lúc đặt lệnh.
- Hai nhãn vị thế, ghi lúc mua và không đổi sau khi mua. "Giá trị–dài hạn": thoát khi điều kiện sai của luận điểm xảy ra, hoặc giá vượt khoảng giá trị. "Tăng trưởng–xu hướng": thoát khi chạm mức lỗ định trước, hoặc quy tắc xu hướng bị phá.
- Phiếu trước quyết định: mười câu. Một câu trả lời "chưa" hoặc "vượt" thì dừng.
- Nhật ký: mỗi quyết định một dòng. Mỗi quý xem lại hai thứ riêng nhau: luận điểm đúng hay sai; có làm đúng quy tắc không.
- Bản quy tắc đã điền, phiếu đã điền và nhật ký nằm ngoài kho công khai (L-03). Kho chỉ giữ mẫu trống, thêm sau hồ sơ đầu tiên.
- Dự án không chọn trường phái, tỷ trọng hay mức lỗ thay Owner.

### QĐ-P9 — Kiểm để đúng

| Lớp | Ai kiểm | Kiểm gì |
|---|---|---|
| 1. Nguồn | Máy | Mỗi số và câu trích khớp tài liệu gốc đã ghim |
| 2. Phản biện | Ghế khác hãng | Lập luận, điều chưa chứng minh |
| 3. Hậu kiểm | Thời gian | Tới ngày xem lại: điều kiện sai có xảy ra không |

- Mỗi hồ sơ gài một lỗi cố ý để xem ghế phản biện có bắt được không.
- Owner tự mở ba con số bất kỳ trong tài liệu gốc ở mỗi hồ sơ.
- Hậu kiểm ghi ĐÚNG, SAI hoặc CHƯA RÕ cho từng luận điểm. Kết quả dùng để sửa cách phân tích, không dùng để tuyên bố thắng thị trường.

### QĐ-P10 — Sàn Zero

Sàn Zero là phòng tập kỷ luật trên chỉ số mô phỏng. Mã do Owner giữ ngoài kho. Năm điều kiện:

1. Tách hẳn: không đọc giá thật, không có tên mã thật, không nối vào ba sản phẩm.
2. Công khai bộ sinh giá và hạt giống. Mỗi luật phải có chế độ nó thua, trong đó có một chế độ độ lệch gần chỉ số thật.
3. Kết quả ghi dạng phân bố qua nhiều băng: lãi lỗ, sụt giảm lớn nhất, tỷ lệ cháy tài khoản. Màn hình mở đầu hiện kết quả trên nhiều băng, không hiện một băng đẹp.
4. Không dẫn kết quả Sàn Zero vào hồ sơ mã, phiếu kỷ luật hay nhật ký như bằng chứng.
5. Khi Owner tập, thứ được chấm là mức làm đúng quy tắc, không phải lãi.

### QĐ-P11 — Ngừng

"Ngừng" nghĩa là không làm việc mới và không dùng đầu ra làm căn cứ. Không xóa mã, không sửa sổ đã ghi, không sửa chữ các ADR cũ.

| Thành phần | Lý do |
|---|---|
| Sổ dự báo A–B, ghế đối chứng B, lịch công bố | So với Claude trần là so với AI ngoài dự án |
| Mốc 194 bất đồng, lộ trình G1–G4 ở §8, mốc xét lại 31/03/2027 của ADR-0002 | Thuộc hướng đo |
| Máy dò tín hiệu 13 feature × 3 mô hình và lượt thử hằng tuần của robot | Dò mẫu trên giá |
| FWD-001, sổ bóng, các điều kiện dừng của FWD-001 trong ADR-0016 và ADR-0018 | Chứng minh thắng đối chứng |
| Phần phán quyết và cổng cấp tín hiệu của SCN-001 (ADR-0017) | Chứng minh năng lực; thiết kế thẻ đọc thì giữ |
| Thang vốn 0–6, làn vốn của ADR-0016 | Vốn là việc riêng của Owner |
| `governance/OWNER_MISSION.md`, `governance/GOVERNOR_POLICY.yaml` làm đầu vào | Thay bằng bản quy tắc riêng ngoài kho; hai tệp giữ nguyên, AI không điền |
| Media và tường lửa đầu tư–truyền thông | Ngoài phạm vi của dự án phân tích cổ phiếu |
| Học viện với bài thi A so với B | So với AI ngoài dự án |

- Robot mỗi phiên (chế độ ops) tiếp tục chạy để giữ kho giá. Đầu ra dự báo mô hình và sổ giấy của robot không được dùng trong hồ sơ.
- Lượt thử hằng tuần được đặt về 0 bằng một PR riêng. Chạy tay với `trials=1` không được dùng.
- 222 lần thử đã ghi không đủ lực để kết luận. ADR này không ghi "thị trường không có lợi thế".

### QĐ-P12 — Sổ dự báo

16 dự báo đang mở được phân định khi tới hạn, theo ADR-0003: F-105…F-108 ngày 04/12/2026; F-109…F-114 ngày 11/12/2026; F-37…F-42 ngày 20/12/2026. Sau đó không mở dự báo mới. Sổ và scorecard giữ nguyên để tra cứu.

### QĐ-P13 — L-02 và nơi đặt hồ sơ

PR này không sửa `governance/LAWS.md`. L-02 hiện chỉ cho xuất dự báo xác suất về sự kiện và chỉ tiêu. Cho tới khi Owner tự sửa L-02 để cho phép ghi khoảng giá trị kèm giả định và không kèm hành động, hồ sơ mã (kể cả mục 8) nằm ở nơi riêng tư của Owner và không vào kho.

### QĐ-P14 — Đường thi công và thước đo

1. ADR này và PR tắt lượt thử hằng tuần.
2. Một hồ sơ chạy trọn cho một mã do Owner chọn: hồ sơ mười hai mục, bản phản biện của ghế khác hãng, bộ mẫu kỷ luật trống. Làm bằng tay, chưa cần mã mới.
3. Sau khi Owner đã dùng hồ sơ đầu tiên: chốt mẫu vào kho, viết máy kiểm trích dẫn, xét xóa phần mã đã ngừng.

Thước đo của ADR này: có một hồ sơ trọn vẹn cho một mã, đã qua phản biện khác hãng, Owner đã đọc. Trước mốc đó không mở việc nào ngoài ba bước trên.

### QĐ-P15 — Vai các ghế

| Ghế | Việc |
|---|---|
| Owner | Chọn mã; đọc hồ sơ và bản phản biện; điền bản quy tắc riêng; quyết định; tự đặt lệnh; gộp PR |
| Claude Project (Anthropic) | Kiến trúc; viết hồ sơ mã; soạn mẫu |
| ChatGPT (OpenAI) hoặc Gemini (Google) | Viết bản phản biện; đối chiếu số với tệp gốc; chấm PR do Claude viết (L-09) |
| Grok (xAI) | Tìm và đưa tài liệu gốc vào thư viện theo nhu cầu của hồ sơ |
| Claude Code (Anthropic) | Bảo trì kho; máy kiểm trích dẫn sau hồ sơ đầu tiên |

## Trạng thái từng quyết định

| QĐ | Trạng thái | Owner | Ngày |
|---|---|---|---|
| QĐ-P1 tới QĐ-P11, QĐ-P14, QĐ-P15 | ACCEPTED | Owner (lệnh 18:05 và 18:38) | 23/11/2026 |
| QĐ-P12, QĐ-P13 | ACCEPTED theo mặc định của kiến trúc sư; Owner đổi được trước khi gộp | Owner | 23/11/2026 |

## Lý do (bằng chứng, số đo)

- Sổ dự báo: 16 dòng, 0 dòng đã phân định. Sổ thử: 222 lần thử trên 30 mã, không đủ lực để kết luận.
- AI vượt người ở nơi có trọng tài nhanh, thử được nhiều lần và luật ổn định. Chọn cổ phiếu thiếu cả ba. Đọc và kiểm tài liệu thì có trọng tài: tài liệu gốc.
- Sàn Zero, đo ngày 23/11/2026 trên mã Owner cung cấp (170 phiên, phí 0,10% mỗi lần đổi vị thế). Với bộ sinh giá có độ lệch +0,04% mỗi phiên, trên 400 băng, luật "Tìm kiếm" lãi trung bình 2,0%, mua và giữ lãi 7,9%. Ở chế độ đổi chế độ của mã gốc, trên 1.500 băng, "Tìm kiếm" hơn mua và giữ ở 46,9% số băng; sụt giảm trung bình 7,8% so với 23,6%. Vì vậy có điều kiện 4 của QĐ-P10.
- Các bản rà soát của ghế ngoài ngày 22–23/11/2026 nêu: phần giấy tờ đã lớn hơn phần sản phẩm. Thước đo ở QĐ-P14 vì thế là một hồ sơ, không phải số PR.
- Điểm yếu đã biết: bỏ đo thì dự án không trả lời được câu hỏi phân tích có giúp sinh lời không; AI viết và AI phản biện có thể cùng mù một chỗ; nền dữ kiện còn mỏng (thư viện 1/40, giá từ Yahoo còn lỗi).

## Không đổi

- L-01…L-10 và `governance/LAWS.md` không sửa. PR này không chạm `governance/`.
- `autonomous_order_execution: false` và `live_trading_enabled: false` giữ nguyên. Không mở API trả phí.
- Sổ đã ghi giữ nguyên: `ledger/`, `paper/`, `research/trials.csv`, `research/trial_registry.jsonl`. Không xóa mã, không xóa tệp.
- Tiếp tục dùng: thư viện, ghi chú có địa chỉ, bảng ghim tệp gốc và robot tải tệp gốc; thiết kế thẻ đọc của ADR-0017; các khuôn `dossier`, `research_report`, `valuation_case`, `hypothesis`, `risk_assessment`, `learning_lesson`; `library/casebook/`; mô tả vai trong `experts/investment/`; kho giá, cổng chứng cứ sự kiện quyền, lịch phiên; phép tính tỷ trọng và thanh khoản thoát của cổng rủi ro; cổng L-09, bộ test, `tools/validate.py`.
- Chữ của ADR-0001…ADR-0018 không sửa. Phần của ADR-0002, ADR-0011, ADR-0013, ADR-0015, ADR-0016, ADR-0017 và ADR-0018 thuộc các nhóm ở QĐ-P11 ngừng áp dụng.

## Điều kiện hoàn tác

1. Tới hết ngày 31/01/2027 chưa có hồ sơ mã đầu tiên đạt thước đo ở QĐ-P14: kiến trúc sư báo Owner trong 7 ngày. Owner chọn bằng một ADR mới: thu hẹp tiếp, hoặc quay lại phạm vi trước ADR này.
2. Owner muốn quay lại hướng đo vào bất kỳ lúc nào: một ADR mới đảo QĐ-P11 và QĐ-P12, và một PR đặt lại `research.trials_per_cycle`.
3. Hoàn tác không cần khôi phục gì, vì ADR này không xóa mã và không sửa sổ. Phần không bù được là khoảng thời gian không ghi dự báo A–B.

## Ảnh hưởng tới ARCHITECTURE.md

- Dòng trạng thái đầu tệp: thêm ADR-0019.
- Thêm mục "Phạm vi hiệu lực từ ADR-0019" trước §0. Mục đó cho biết từng mục §1–§10 còn áp dụng tới đâu.
- Chữ của §0–§10 giữ nguyên. Tên tệp và số bản v3.0 không đổi.
