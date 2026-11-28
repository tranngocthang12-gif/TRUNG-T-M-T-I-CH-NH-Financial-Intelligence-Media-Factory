# ADR-0025: Nhìn ngược và loại trừ trong hồ sơ mã

- Ngày: 2026-11-28
- Trạng thái: ACCEPTED 28/11/2026 theo lệnh Owner, hiệu lực khi Owner gộp PR này. PR này dựng trên chữ của ADR-0024 và chỉ gộp sau ADR-0024.
- Người đề xuất: Claude Project TTC (Anthropic), ghế kiến trúc sư trưởng. Chép vào kho: phiên Claude Code (Anthropic).
- Phản biện bản nháp: ChatGPT (OpenAI), 28/11/2026. Vòng 1 (PB-ADR25-V1): SỬA TRƯỚC, mười ba lỗi chặn C01–C13, đồng ý giữ cả ba năng lực. Vòng 2 (PB-ADR25-V2): mười ba lỗi đã đóng, công thức và hệ số khớp nghiên cứu gốc; còn ba lỗi chặn mới C14–C16. Bản v3 sửa ba lỗi đó và nhận các góp ý G13–G17. Vòng 3 (PB-ADR25-V3, vòng cuối): ĐẠT, mười sáu lỗi chặn đã đóng, không còn lỗi chặn, đồng ý giữ cả ba năng lực; ba góp ý không chặn G19–G21 không đổi chữ ADR. Sau vòng 3 chỉ sửa dòng ghi phản biện này. Người chấm PR: ghế khác hãng Anthropic, ghi trong thân PR (L-09).
- Owner duyệt: lệnh trong chat Project ngày 28/11/2026, 01:35 giờ Việt Nam, «bạn thấy ý trên kiến trúc mình cần và phù hợp thì bạn ghép vào kiến trúc»; xác nhận bằng việc gộp PR này.

## Bối cảnh

- Ngày 28/11/2026 Owner hỏi các cách phân tích khác: nhìn ngược, loại trừ, phản biện. Ghế kiến trúc sư so mười hai cách thường dùng với kiến trúc đang có.
- Dự án đã có phần lớn: mười lăm điểm soi (ADR-0019 QĐ-P6) là danh sách cờ đỏ đọc tay; bản phản biện khác hãng mở đầu bằng luận điểm ngược mạnh nhất (QĐ-P7); điều kiện sai ở Mục 11; ca tương tự thành và bại ở Mục 12; danh sách CHƯA BIẾT; đối chiếu số khác hãng và lỗi gài; phiếu trước quyết định.
- Còn thiếu ba cách: khám nghiệm trước (giả sử hồ sơ đã sai rồi tìm lý do); điểm cờ đỏ tính từ báo cáo tài chính theo công thức đã công bố; dừng khi chưa giải thích được doanh nghiệp kiếm tiền từ đâu bằng tệp gốc.
- Tài liệu Project `claude/TONG_HOP_KINH_NGHIEM_AI_DAU_TU_20261127.md` (phát hiện 7) ghi: chấm theo quy tắc có hay không từ báo cáo tài chính có bằng chứng ở một số thị trường, có giai đoạn đảo chiều, phải thử trên dữ liệu của chính thị trường mình.

## Quyết định

### QĐ-L1 — Khám nghiệm trước

1. Cuối Mục 11, tiêu đề phụ «### Khám nghiệm trước», viết trước khi giao, gồm:
   - Nhận định được khám nghiệm, mã ND-1: chỉ rõ câu quan trọng nhất của «Một trang» (gạch đầu dòng thứ mấy) và nêu lại nó trong một câu không có con số; ghi giả thuyết của Mục 11 mà nhận định đó dựa vào. Điều kiện sai của giả thuyết đó là điều kiện bác ND-1. Chọn nhận định mà điều kiện đó bác được thật, không chỉ làm yếu một phần lập luận; câu chỉ mô tả dữ kiện quá khứ không chọn làm ND-1.
   - Ba lý do chính, mã LD-1, LD-2, LD-3 (mã viết có gạch nối để qua máy kiểm chữ của ADR-0022): mỗi lý do nêu cơ chế làm ND-1 sai (khoản mục nào của báo cáo, đổi theo chiều nào), và chỗ chấm được trong hồ sơ: một điều kiện sai ở Mục 11, một điều kiện đổi trạng thái ở Mục 9, một điểm soi, hay một dòng của danh sách CHƯA BIẾT. Lý do không có chỗ chấm thì thêm một dòng vào danh sách CHƯA BIẾT.
2. Lý do liên quan tới biến thời thế chỉ trỏ tới điều kiện đã ghi ở Mục 9, không nêu biến sẽ đi hướng nào (ADR-0023 QĐ-T3). Không lý do nào nói về giá cổ phiếu, khoảng giá trị hay hành động với cổ phiếu. Viết dưới nhãn GIẢ ĐỊNH, không thêm con số mới.
3. B7: lệnh phản biện (mẫu B) có câu hỏi bắt buộc thứ ba: hồ sơ chưa lường trước lý do nào. Ở B8 bước 1, lý do mới ghế phân tích nhận thì thêm vào tiểu mục với mã LD-4 trở đi, ghi «từ phản biện». Ba lý do chính giữ mã. Lỗi đã xác minh trong ND-1, điều kiện bác hay một lý do thì sửa theo B8 bước 1 như mọi lỗi khác, ghi chữ cũ và chữ mới vào «Lịch sử sửa». Hậu kiểm chỉ dùng chữ của bản đã giao và đã niêm phong.
4. Hậu kiểm: chỉ một sự kiện được chấm, ND-1 bị bác, tức điều kiện bác của ND-1 đã xảy ra. Một giả thuyết cạnh tranh bị loại mà ND-1 không bị bác thì không chấm. Khi ND-1 bị bác, ghi một trong ba: ĐÃ LƯỜNG TRƯỚC (nguyên nhân có bằng chứng, kèm mã tệp và trang, trùng cơ chế của một LD: cùng khoản mục và cùng chiều; trùng tên chủ đề không đủ), KHÔNG LƯỜNG TRƯỚC (nguyên nhân rõ, không trùng LD nào), CHƯA RÕ (nguyên nhân là CHƯA RÕ theo ADR-0023 QĐ-T6). ĐÃ LƯỜNG TRƯỚC ghi rõ trùng lý do chính hay lý do từ phản biện.

### QĐ-L2 — Điểm cờ đỏ kế toán

1. Mục 6 thêm tiêu đề phụ «### Điểm cờ đỏ kế toán», gồm ba điểm theo đúng định nghĩa, cách ánh xạ khoản mục và luật viết của `templates/hoso/DIEM_CO_DO_KE_TOAN.md`: điểm F (Piotroski 2000, chín tiêu chí có hay không), điểm M (Beneish 1999, mô hình tám biến, định nghĩa biến theo bảng 2 của nghiên cứu), điểm Z (Altman, bản bốn biến dùng vốn chủ sở hữu theo sổ sách). Không điểm nào dùng giá cổ phiếu.
2. Thi công với máy hiện có: đầu vào là dòng gốc của sổ; mỗi tỷ số, điểm M và điểm Z là dòng tính, viết trong hồ sơ dưới nhãn SUY LUẬN gọi khóa; ngưỡng và mọi chỗ ánh xạ khoản mục sang báo cáo Việt Nam viết dưới nhãn GIẢ ĐỊNH. Bộ tính của sổ không có phép so sánh, nên điểm F không là dòng tính: hồ sơ ghi đạt hay không của từng tiêu chí kèm khóa của tỷ số, rồi ghi tổng. Máy kiểm các tỷ số; ghế đối chiếu số (mẫu C) kiểm cách ánh xạ đầu vào, từng tiêu chí của điểm F, tổng điểm F, và công thức của điểm M, điểm Z so với tệp mẫu. Phiếu máy ĐẠT không thay phần kiểm nghĩa kế toán này.
3. Thiếu đầu vào, mẫu số bằng không hay phép so không làm được: theo luật của tệp mẫu (không lập dòng tính đó, ghi CHƯA BIẾT kèm lý do, không thay bằng giá trị trung tính). Điểm F chỉ có tổng và cờ khi đủ chín tiêu chí. Doanh nghiệp tài chính: «không áp dụng».
4. Điểm là cờ để soi kỹ hơn. Tiểu mục mở bằng câu cố định của tệp mẫu. Cờ bật thì nêu các tỷ số đóng góp lớn nhất và khoản mục cần soi, nối với điểm soi tương ứng; không gọi đó là nguyên nhân; không viết rằng doanh nghiệp làm đẹp lợi nhuận, gian lận hay sắp vỡ nợ. Không xếp hạng mã theo điểm; không cộng các điểm; không coi ba cờ là ba bằng chứng độc lập; không đưa điểm vào câu đánh giá doanh nghiệp, câu về giá cổ phiếu, khoảng giá trị hay lời hành động.
5. Sự cố, theo danh sách đóng: ý kiến kiểm toán khác «chấp nhận toàn phần»; điều chỉnh hồi tố số đã công bố; chậm trả gốc hay lãi của khoản vay hay trái phiếu; cổ phiếu bị sở giao dịch đưa vào diện cảnh báo, kiểm soát hay hạn chế giao dịch; lợi nhuận sau thuế sau kiểm toán hay soát xét thấp hơn số doanh nghiệp tự lập đã công bố cho cùng kỳ. Kỳ theo dõi của một hồ sơ chạy từ ngày giao tới ngày xem lại đã niêm phong của bản đó; Mục 11 ghi nhiều ngày xem lại thì lấy ngày cuối. Chỉ tính sự cố mới phát sinh hay lần đầu được công bố trong kỳ theo dõi; sự cố đã biết khi giao không tính. Hậu kiểm theo sự kiện ghi thêm bằng chứng nhưng không đóng kỳ sớm. Kỳ theo dõi đóng ở lần hậu kiểm định kỳ tại ngày xem lại; chỉ khi đó hồ sơ mới vào bảng A, B, C, D; trước đó ghi «chưa hết kỳ theo dõi». Mỗi sự cố ghi loại, mã tệp, trang, ngày phát sinh, ngày công bố, ngày ghế phân tích phát hiện.
6. PR này không sửa `tools/hoso/`. Pha 2 (gói riêng, có mã): một hàm tính ba điểm từ sổ, chỉ làm khi đã có năm hồ sơ đã giao có điểm tính tay mà ghế đối chiếu số đã kiểm đủ đầu vào và công thức của loại điểm đó, và không phải sửa công thức hay cách ánh xạ nào kể từ lần gửi đối chiếu đầu tiên. Đếm riêng cho từng loại điểm: điểm nào có dưới năm hồ sơ như vậy thì chưa qua cổng. Hồ sơ mà ghế đối chiếu không mở được tệp gốc của điểm đó không được tính.

### QĐ-L3 — Dừng khi chưa hiểu doanh nghiệp từ tệp gốc

1. Ở cuối B4, trước B5, tính độ phủ doanh thu:
   - Tử số: tổng các khoản doanh thu từ bên ngoài trong một bảng chia duy nhất của tệp gốc đã ghim (theo mảng, theo sản phẩm hay dịch vụ, hay theo nhóm khách hàng; có nhiều bảng chia thì chọn một bảng, không trộn hai bảng), cùng kỳ và cùng phạm vi hợp nhất hay riêng với mẫu số, các khoản không chồng lên nhau.
   - Mẫu số: doanh thu thuần năm gần nhất. Doanh nghiệp tài chính: tổng thu nhập hoạt động ở cả tử số và mẫu số.
   - Đầu vào là dòng gốc của sổ, đã qua `kiem_so_lieu.py`; tử số và tỷ lệ là dòng tính.
2. Tỷ lệ dưới ba phần tư (GIẢ ĐỊNH), hoặc không xác định được tử số hay mẫu số: ghế phân tích dừng, báo Owner «chưa đủ tài liệu để hiểu doanh nghiệp kiếm tiền từ đâu», kèm tỷ lệ và danh sách tài liệu còn thiếu.
3. Owner chọn: tìm thêm tài liệu (quay lại B2), đi tiếp với tài liệu đang có, hay bỏ mã. Ghế phân tích ghi ở Project: tỷ lệ trước khi dừng, tài liệu tìm thêm, tỷ lệ sau khi bổ sung, lựa chọn của Owner, kể cả khi Owner bỏ mã. Dừng vì thiếu nguồn là việc của quy trình, không phải đánh giá doanh nghiệp; quyết định bỏ mã là của Owner (ADR-0019 QĐ-P15).
4. Độ phủ đạt ngưỡng chỉ cho biết nguồn doanh thu đã được giải thích, không chứng nhận hồ sơ đã hiểu doanh nghiệp.

### QĐ-L4 — Không đưa vào

- Đọc ngược kỳ vọng trong giá (từ giá hiện tại suy ra tăng trưởng thị trường đang ngầm kỳ vọng): cần giá cổ phiếu và định giá, đang bị khóa theo L-02 và ADR-0019 QĐ-P13.
- Báo cáo của quỹ bán khống làm nguồn bắt buộc: hiếm ở Việt Nam. Khi có, ghim ở B2 như tài liệu phản biện bổ trợ; cáo buộc trong đó không phải số ĐÃ KIỂM và không phải kết luận đã xác minh.
- Một «điểm hồ sơ» gộp các cờ: trái QĐ-L2 điểm 4 và ADR-0024 QĐ-N6.

### QĐ-L5 — Phạm vi, ranh giới và thi công

1. L-01 tới L-10 và `governance/LAWS.md` không sửa. Không sửa `tools/`, `tests/`, `ledger/`, `governance/`, `templates/hoso/vi_du/`. Chữ của ADR-0001 tới ADR-0024 không đổi.
2. ADR này áp cho hồ sơ giao sau ngày gộp: mã mới, hay bản kế tiếp của GAS và HPG. Hồ sơ đã niêm phong trước đó (GAS bản 1 sửa 1, HPG bản 2) không sửa, không thêm hồi tố, và hậu kiểm của chúng không ghi các trường của ADR này (ADR-0021 QĐ-K5).
3. Hai tiểu mục mới và điều dừng ở cuối B4 là bước của hồ sơ, không phải việc đo. Nguyên tắc «hồ sơ trước, đo sau» của ADR-0024 QĐ-N7 điểm 2 không cho bỏ chúng. Điều dừng không được ghi CHƯA BIẾT để đi tiếp: chưa tính được độ phủ thì cũng dừng và hỏi Owner. Chỉ phần đo sau khi giao (bảng hậu kiểm, số phút) được hoãn khi thiếu thời gian.
4. Đơn vị đếm: mỗi kết quả gắn với một bộ (mã, bản đã niêm phong, ND-1 hay loại điểm hay sự cố). Một kết quả chỉ đếm một lần, dù được nhắc lại ở hậu kiểm theo sự kiện và hậu kiểm định kỳ (ADR-0024 QĐ-N4 điểm 2). Điểm và trạng thái cờ lấy từ bản đã niêm phong, không tính lại sau khi biết sự cố.
5. Trước hồ sơ đầu tiên áp ADR này, ghế phân tích thử ngoài kho, trên bản sao một hồ sơ đã giao hay số giả định, các ca biên: đủ đầu vào; thiếu một đầu vào của điểm M; điểm F thiếu hai tiêu chí; mẫu số bằng không; hai năm khác đơn vị; nợ dài hạn chuyển sang đến hạn trả; hai bảng chia doanh thu chồng nhau; doanh nghiệp tài chính; Owner chọn đi tiếp sau khi dừng; một sự cố xuất hiện ở hai lần hậu kiểm. Kết quả ghi ở Project, không tính vào số đo.

## Số đo và mốc đọc

| Năng lực | Số đo | Ai tính | Khi nào đọc |
|---|---|---|---|
| Khám nghiệm trước | Số lần ND-1 bị bác; trong đó ĐÃ LƯỜNG TRƯỚC (từ lý do chính, từ lý do phản biện), KHÔNG LƯỜNG TRƯỚC, CHƯA RÕ; số lý do trong mỗi bản đã giao | Ghế phân tích, ở Project | Khi có 10 lần ND-1 bị bác với nguyên nhân rõ (ĐÃ LƯỜNG TRƯỚC hay KHÔNG LƯỜNG TRƯỚC), hoặc ngày 31/12/2027, tùy mốc nào đến trước |
| Điểm cờ đỏ kế toán | Mỗi loại điểm một bảng, chỉ gồm hồ sơ đã đóng kỳ theo dõi (QĐ-L2 điểm 5): A cờ bật và có sự cố; B cờ bật, không ghi nhận sự cố; C cờ không bật, có sự cố; D cờ không bật, không ghi nhận sự cố. Đếm riêng ngoài bảng: CHƯA BIẾT, KHÔNG ÁP DỤNG, chưa đủ bằng chứng về sự cố, chưa hết kỳ theo dõi. Số phụ: A chia (A + C), A chia (A + B), (A + B) chia tổng bảng; mẫu số bằng không thì ghi CHƯA ĐỦ BẰNG CHỨNG. Tách theo loại sự cố. Số lần ghế đối chiếu số phải sửa công thức hay cách ánh xạ | Ghế phân tích, ở Project | Khi có 10 hồ sơ thuộc phạm vi ADR này đã đóng kỳ theo dõi, hoặc ngày 31/12/2027, tùy mốc nào đến trước |
| Dừng khi chưa hiểu | Số lần dừng; tỷ lệ trước và sau khi bổ sung tài liệu; mỗi lần Owner chọn gì | Ghế phân tích, ở Project | Cùng mốc với điểm cờ đỏ |

- «Không ghi nhận sự cố» không có nghĩa là không có sự cố.
- Kết quả ở mốc là đánh giá vận hành và thăm dò, không phải kiểm chứng khả năng phát hiện sai phạm ở Việt Nam.
- Ở mỗi mốc, ghi thêm số phút Owner bỏ ra cho từng phần (Owner tự ước).

## Hệ quả

- Mỗi hồ sơ thêm một tiểu mục ở Mục 11, một tiểu mục và vài chục dòng sổ ở Mục 6, và một phép tính độ phủ ở cuối B4. Cần thêm báo cáo năm t − 1 kèm thuyết minh.
- Lý do thất bại phải nêu cơ chế và nối được với một chỗ chấm được, nên khám nghiệm trước không thành đoạn văn tự do.
- Ghế đối chiếu số có thêm công thức và cách ánh xạ để kiểm.

Điểm yếu đã biết:

- Ba ngưỡng lấy từ nghiên cứu trên dữ liệu Mỹ; chuẩn mực và mẫu báo cáo Việt Nam khác, và mẫu báo cáo có thể đổi theo chế độ kế toán. Doanh nghiệp tăng trưởng nhanh, đầu tư lớn hay vừa sáp nhập dễ bật cờ M mà không có sai phạm.
- Ba điểm đo ba điều khác nhau (sức khỏe tài chính, dấu hiệu làm đẹp lợi nhuận, kiệt quệ tài chính); danh sách sự cố chung chỉ cho phép đọc thăm dò.
- Nhiều chỗ ánh xạ là giả định: lợi nhuận sau thuế thay lợi nhuận trước khoản mục bất thường, tiêu chí phát hành cổ phiếu, phải thu trước dự phòng khi không tách được.
- Khám nghiệm trước do chính ghế viết hồ sơ viết nên còn thiên kiến; câu hỏi bắt buộc thứ ba ở B7 chỉ giảm phần này.
- Sự cố kế toán hiếm và số lần ND-1 bị bác ít: tới 31/12/2027 có thể chưa đủ số để đọc.
- Ngưỡng ba phần tư doanh thu là tùy ý; doanh nghiệp không công bố doanh thu theo bảng chia sẽ dừng nhiều.

## Điều kiện hoàn tác

1. Khám nghiệm trước: ở mốc đọc, kiến trúc sư báo Owner trong 7 ngày các số ở bảng trên. Có từ 10 lần ND-1 bị bác với nguyên nhân rõ mà không lần nào ĐÃ LƯỜNG TRƯỚC, hoặc tới 31/12/2027 chưa đủ 10 lần (ghi CHƯA ĐỦ BẰNG CHỨNG): Owner chọn bằng ADR mới giữ, sửa cách viết hay bỏ tiểu mục.
2. Điểm cờ đỏ: ở mốc đọc, kiến trúc sư báo Owner trong 7 ngày ba bảng, các số đếm riêng, số phụ, số lần sửa công thức và số phút. Owner chọn bằng ADR mới giữ cả ba điểm, bỏ một hay hai điểm, hay bỏ cả ba.
3. Dừng khi chưa hiểu: ba hồ sơ liền bị dừng mà lần nào Owner cũng chọn đi tiếp với tài liệu đang có: kiến trúc sư báo Owner trong 7 ngày; Owner chọn sửa ngưỡng hay bỏ điều dừng bằng ADR mới.
4. Bất kỳ lúc nào: một câu ở tiểu mục mới nêu giá cổ phiếu, khoảng giá trị, hướng đi của biến thời thế hay lời hành động, một câu kết luận doanh nghiệp gian lận hay làm đẹp lợi nhuận chỉ từ điểm M, hoặc điểm cờ đỏ bị dùng để xếp hạng mã: dừng phần đó ở mọi hồ sơ đang làm và báo Owner ngay.
5. Hoàn tác: một PR đảo các thay đổi chữ của PR này. Hồ sơ đã giao giữ nguyên theo niêm phong.

## Ảnh hưởng tới ARCHITECTURE.md

- Dòng trạng thái đầu tệp: thêm ADR-0025.
- Thêm một đoạn ngắn sau đoạn «Từ ADR-0024», trỏ tới ADR này.
- Chữ của §0–§10 giữ nguyên.
