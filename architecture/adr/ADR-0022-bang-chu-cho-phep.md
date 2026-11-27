# ADR-0022: Bảng chữ cho phép của hồ sơ mã, để chữ người đọc thấy là chữ máy đọc

- Ngày: 2026-11-27
- Trạng thái: ACCEPTED 27/11/2026 theo lệnh Owner, hiệu lực khi Owner gộp PR này.
- Người đề xuất: Claude Project TTC (Anthropic), ghế kiến trúc sư trưởng. Chép vào kho: phiên Claude Code (Anthropic).
- Người chấm: theo L-09, ghi trong thân PR.
- Owner duyệt: lệnh trong chat Project ngày 27/11/2026, 11:02 giờ Việt Nam, giao kiến trúc sư toàn quyền quyết định các việc còn mở sau khi PR #120 gộp; xác nhận bằng việc gộp PR này.

## Bối cảnh

- Cổng định dạng của phiếu máy (ADR-0020, `kiem_luat.kiem_dinh_dang`) cho phép một bộ Markdown hẹp theo dòng, nhưng trong dòng vẫn là danh sách cấm: cấm `~~` mà không cấm một dấu `~`, cấm thực thể HTML mà không cấm `$`. Mỗi bản chấm tìm thêm một cách viết làm chữ người đọc thấy khác chữ máy đọc, và mỗi vòng sửa vá thêm một mẫu.
- Ba lần cùng một việc: PR #117 (ADR-0020) bốn vòng sửa, gộp xong thì bản chấm vòng 5 vẫn tìm ra một dấu `~`; PR #119 vá ba cách viết (`~`, `$…$`, định nghĩa liên kết trong mục liệt kê), ba vòng sửa, hai vòng là sửa lỗi do vòng trước gây ra, rồi đóng mà không gộp; PR #120 (ADR-0021) hai vòng sửa, lỗi chặn vòng 2 cùng loại (dấu định dạng cắt con số). PR #120 qua được ở vòng 3 vì ADR-0021 đã công bố ba cách viết của PR #119 là điểm yếu đã biết, và người chấm không tính giới hạn đã công bố là lỗi chặn.
- Sau khi PR #120 gộp (`main` `2ca1c55`), kiến trúc sư đo lại: một mức giá cổ phiếu không nguồn, viết ngay sau một nhãn khác trong mục đánh số («1. … [CHƯA BIẾT] 30. Đó là giá cổ phiếu MAU, nghìn đồng. [GIẢ ĐỊNH]»), vẫn cho phiếu ĐẠT (chỗ hở có từ ADR-0020); nhãn lẫn hai loại «[GIẢ ĐỊNH, SUY LUẬN, sổ số liệu: …]» làm máy bỏ qua luật khóa; con số nằm trong một địa chỉ web không bị đọc.

## Quyết định

### QĐ-C1 — Bảng chữ cho phép

- Mỗi ký tự của hồ sơ phải thuộc bảng chữ cho phép; ký tự ngoài bảng là lỗi định dạng, bất kể nghĩa. Bảng gồm: 26 chữ Latin hoa và thường; Đ, đ và các nguyên âm tiếng Việt có dấu (chữ dựng sẵn, sau chuẩn hóa NFC); chữ số 0–9; dấu cách thường; các dấu `. , ; : ! ? ' " “ ” ‘ ’ « » ( ) / % + = × ÷ ± ≈ ≠ ≤ ≥ → ← … # & - – — −`; và sáu dấu Markdown còn hiệu lực, mỗi dấu một luật riêng đã có hay thêm ở QĐ-C2: `|` (bảng), `*` (chữ đậm), `` ` `` (mã), `_` (khóa sổ trong nhãn, tên tệp trong mã), `[` `]` (nhãn). Trong mã được thêm dấu `\` (đường dẫn tệp).
- Hệ quả: một dấu `~`, công thức `$…$`, `<`, `>`, `^`, `@`, `{`, `}`, dấu `\` ngoài mã, chữ khác bảng mã trông như chữ Latin (chữ Kirin, chữ Hy Lạp), chữ số khác 0–9 (chữ số mũ, toàn khổ, A-rập, khoanh tròn), dấu phẩy, dấu % và gạch ngang dạng khác đều là lỗi. Các ký tự vô hình, dấu cách khác dấu cách thường và dấu kết hợp đứng riêng vẫn là lỗi như ADR-0020.
- Mục đích: chuyển cổng định dạng từ danh sách cấm sang danh sách cho phép ở mức ký tự. Một cách viết mới không cần mẫu mới để bị chặn; chỉ sáu dấu Markdown còn hiệu lực, và mỗi dấu có luật.

### QĐ-C2 — Ngoặc vuông chỉ dùng cho nhãn, nhãn đúng dạng

- Mọi ngoặc vuông của hồ sơ phải là ngoặc của một nhãn. Ngoặc vuông ngoài nhãn là lỗi: liên kết, định nghĩa liên kết (kể cả trong mục liệt kê), chú thích chân trang, ô đánh dấu đều dùng ngoặc vuông. Sau nhãn không có `(`, `[`, `:`. Trong mã không có `|`, `[`, `]`.
- Nhãn mở đầu ngay bằng loại: ĐÃ KIỂM, SUY LUẬN, GIẢ ĐỊNH hay CHƯA BIẾT. «sổ số liệu» chỉ đứng trong nhãn SUY LUẬN. Nhãn GIẢ ĐỊNH, CHƯA BIẾT không nhắc loại nào khác: máy không kiểm số của hai loại này, nên nhắc «SUY LUẬN» hay «ĐÃ KIỂM» trong đó làm người đọc tưởng số đã được kiểm. Nhãn ĐÃ KIỂM, SUY LUẬN được nhắc loại khác trong ghi chú, vì máy kiểm theo loại đứng đầu là loại chặt hơn. Nhãn không chứa dấu `|`.

### QĐ-C3 — Cách viết số mà người đọc và máy đọc khác nhau là lỗi

Xét ngoài mã và ngoài nhãn, sau khi bỏ dấu `**`:

- Chữ cái dính liền trước chữ số («tăng63,4%», «ROE15%», «P/E15») là lỗi, vì máy coi cả cụm là một mã và không đọc con số. Được: mã một chữ hoa với một hai chữ số không kèm phần lẻ hay dấu % (D1, H0, Q3, P13); các tên VN30, VN100, HNX30, VNX50, SHA256, sha256, CO2, m2, m3, km2; mã băm từ bảy ký tự 0–9, a–f; kỳ báo cáo «9T2026», «6M2025», «Q3.2025», «H1/2025».
- Chữ cái dính sau chữ số mà kẹp giữa hai con số («5O,5%»), hay là O, o, I, l («1O tỷ»); dấu % đứng sát sau chữ cái («lO%»); dấu nháy giữa hai chữ số («1'200») là lỗi: người đọc thấy một con số mà máy không đọc.
- Dấu trừ dính sau chữ cái («giảm-36,4%»), sau dấu chấm hay dấu phẩy («20,0%,-36,4%»), đứng trước ngoặc («-(36,4%)»), hay đứng cách con số một dấu cách («biến động - 36,4%») là lỗi: máy đọc số không dấu. Được: ký hiệu mục liệt kê «- »; khoảng sau một con số («2020 - 2025», «5% - 10%»); mã viết hoa nối gạch với số nguyên (L-02, ADR-0019, PR-120).
- Số tách hàng nghìn bằng dấu cách («1 200») là lỗi.
- Địa chỉ web (`://`, `www.`), kể cả trong mã, và mã biểu tượng («:one:», «:100:») là lỗi.

### QĐ-C4 — Số kiểu Anh ở đoạn ĐÃ KIỂM là lỗi

- Cụm chữ số không đọc được theo kiểu số Việt Nam («63.4», «1,555.5») ở đoạn ĐÃ KIỂM là KHÔNG LẦN RA. Trước ADR này máy bỏ qua cụm đó, nên một con số ĐÃ KIỂM sai viết kiểu Anh không bị đối chiếu (điểm yếu đã công bố của ADR-0021).

### QĐ-C5 — Cổng giá: số thứ tự chỉ bỏ ở đúng đầu mục liệt kê

- Trong ngữ cảnh giá, số «12. » chỉ được bỏ như số thứ tự khi nó đứng ở đúng đầu một mục liệt kê đánh đúng 1, 2, …, n. Phần chữ đứng sau một nhãn giữa mục liệt kê không còn được bỏ số đứng đầu. Sửa chỗ hở có từ ADR-0020.

### QĐ-C6 — Vạch đích của bản chấm L-09 cho PR sửa `tools/hoso/`

- Mục 4 của `docs/QUY_TRINH_HO_SO_MA.md` là danh sách giới hạn đã công bố của máy. Lệnh chấm L-09 cho mọi PR sửa `tools/hoso/` ghi rõ: lỗi chặn là (a) một đầu vào qua được cổng định dạng mà người đọc thấy một con số khác con số máy đọc, hay một số sai lọt, hay một mức giá không nguồn qua cổng giá, và đầu vào đó không thuộc giới hạn đã công bố; (b) một cách viết B5 cho phép mà máy báo lỗi; (c) hồi quy so với `main`; (d) PR chạm ngoài phạm vi đã nêu.
- Đầu vào thuộc giới hạn đã công bố không là lỗi chặn. Người chấm thấy một giới hạn đã công bố là không chấp nhận được thì ghi vào góp ý không chặn kèm lý do; kiến trúc sư đưa Owner quyết bằng một ADR mới. L-09 không đổi: người chấm vẫn độc lập, khác hãng, và mọi lỗi ngoài giới hạn đã công bố vẫn chặn.
- Giới hạn ba vòng sửa giữ nguyên.

### QĐ-C7 — Hồ sơ đã giao

- Đo bằng công cụ của ADR này, hai hồ sơ đã giao và hai bản gửi phản biện của chúng không có lỗi mới nào. QĐ-K7 của ADR-0021 giữ nguyên: không làm lại hồ sơ đã giao.

## Trạng thái từng quyết định

| QĐ | Trạng thái | Owner | Ngày |
|---|---|---|---|
| QĐ-C1 tới QĐ-C7 | ACCEPTED theo lệnh Owner giao kiến trúc sư toàn quyền quyết định | Owner (lệnh 11:02 ngày 27/11/2026) | 27/11/2026 |

## Lý do (bằng chứng, số đo)

Đo ngày 27/11/2026, chỉ đọc, ở máy phân tích và máy Owner, ngoài kho:

- Hồ sơ mẫu số liệu bịa, 84 đầu vào chèn dưới Mục 9, chạy `phieu_may.lap_phieu` toàn trình (lớp `BangChuTests` của `tests/test_hoso.py`): 64 đầu vào phải ra CHƯA ĐẠT (ba cách viết của PR #119, HTML, Unicode, chữ dính số, dấu trừ, số tách nghìn bằng dấu cách, địa chỉ web, mã biểu tượng, nhãn, cổng giá, số kiểu Anh ở đoạn ĐÃ KIỂM), 20 đầu vào là cách viết hợp lệ phải ra ĐẠT. Trên `main` `2ca1c55`: 36 trong 64 đầu vào cho phiếu ĐẠT sai, 20 đầu vào hợp lệ đều ĐẠT. Trên bản sửa: cả 84 ra đúng.
- Bộ 145 đầu vào kiến trúc sư soạn cho vòng sửa 2 của PR #120 (gói giao 18, không dùng): `main` xử khác kỳ vọng ban đầu 18 ca, bản sửa 13 ca. Trong 13 ca: 3 ca là cách đọc chữ hiển thị ADR-0021 đã chọn («**36,4**%» đọc là 36,4%, đúng số); 8 ca thuộc giới hạn đã công bố (số sai trùng hằng số 100 của công thức, số trong ghi chú của nhãn, nhãn ở mục ngoài phạm vi đối chiếu); 2 ca không có con số nào bị đọc sai (một nhãn thừa không phủ số nào, bốn dòng «Trạng thái kiểm» viết thành mục con).
- Bốn hồ sơ thật (hai hồ sơ đã giao và hai bản gửi phản biện của chúng; 101 tới 180 nhãn mỗi hồ sơ), đo trên máy Owner bằng công cụ của bản sửa: không lỗi mới nào; mọi nhãn đã đúng dạng của QĐ-C2; không có ký tự ngoài bảng chữ, không có chữ dính số ở phạm vi đối chiếu ngoài mã nguồn và mã giả thuyết, không có số kiểu Anh ở đoạn ĐÃ KIỂM. Bản 1 của hồ sơ thứ nhất (trước ADR-0020, không giao) thêm ba lỗi định dạng, trên 56 lỗi định dạng sẵn có.

Điểm yếu đã biết (chép đủ ở mục 4 của quy trình):

- Mã một chữ hoa với số nguyên («X55»), các tên được phép ở QĐ-C3 và mã viết hoa nối gạch với số nguyên («PR-55») máy coi là mã: số trong đó không bị đối chiếu.
- Chữ cái trông như chữ số viết thay cả con số («lO phần trăm») máy không đọc, như số viết bằng chữ.
- Các giới hạn của ADR-0021 không do ADR này đóng vẫn còn: số trùng tình cờ, số nhỏ và năm, số trong chính nhãn, mục ngoài phạm vi đối chiếu, hai số đổi chỗ trong một nhãn gọi nhiều khóa, số viết bằng chữ, công thức đúng số học sai nghĩa, máy văng lỗi với đầu vào cực đoan.
- Ghế viết công cụ, ghế viết hồ sơ và ghế kiến trúc cùng hãng (QĐ-K6 của ADR-0021).

## Không đổi

- L-01…L-10 và `governance/LAWS.md` không sửa. PR này không chạm `governance/`, `ledger/`, `paper/`, `research/`, `engine/`, `data/`.
- `autonomous_order_execution: false` và `live_trading_enabled: false` giữ nguyên. Không mở API trả phí. Công cụ chỉ dùng thư viện chuẩn của Python.
- Chữ của ADR-0019, ADR-0020 và ADR-0021 không sửa. ADR này đóng ba cách viết ADR-0021 ghi là điểm yếu (đề tài của PR #119), các điểm yếu «chữ đồng dạng khác bảng mã», «ký tự thay cho chữ số», «con số dính liền sau một chữ cái», «dấu trừ cách con số, dính sau chữ hay dấu câu, đứng trước ngoặc», «số kiểu Anh ở đoạn ĐÃ KIỂM», và chỗ hở ở cổng giá.
- Năm phép kiểm của phiếu, luật khóa, cổng giá, khoảng giá giữ nguyên; mọi luật mới theo hướng chặt hơn.

## Điều kiện hoàn tác

1. Sau hai hồ sơ làm theo luật mới: nếu một hồ sơ có hơn 20 lỗi định dạng của ADR này mà không lỗi nào là cách viết che một con số, kiến trúc sư báo Owner trong 7 ngày. Owner chọn bằng một ADR mới: giữ, thêm ký tự cụ thể vào bảng chữ, hay bỏ QĐ-C1.
2. Nếu ghế khác hãng hay hậu kiểm tìm ra một con số sai trong hồ sơ thật lọt qua một giới hạn đã công bố, kiến trúc sư đưa giới hạn đó lên đầu hàng đợi và sửa bằng một PR riêng; QĐ-C6 không che việc này.
3. Hoàn tác không cần khôi phục gì: gỡ bằng một PR đảo các thay đổi của PR này. Hồ sơ làm trong thời gian ADR có hiệu lực giữ phiếu của chúng, vì phiếu ghi commit công cụ.

## Ảnh hưởng tới ARCHITECTURE.md

- Dòng trạng thái đầu tệp: thêm ADR-0022.
- Thêm một đoạn ngắn sau đoạn «Từ ADR-0021», trỏ tới ADR này.
- Chữ của §0–§10 giữ nguyên.
