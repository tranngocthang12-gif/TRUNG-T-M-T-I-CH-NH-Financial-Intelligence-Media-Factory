# ADR-0021: Số SUY LUẬN gắn đúng khóa sổ, lớp định nghĩa và trạng thái kiểm của hồ sơ mã

- Ngày: 2026-11-27
- Trạng thái: ACCEPTED 27/11/2026 theo lệnh Owner, hiệu lực khi Owner gộp PR này.
- Người đề xuất: Claude Project TTC (Anthropic), ghế kiến trúc sư trưởng. Chép vào kho: phiên Claude Code (Anthropic).
- Vòng sửa 2 (27/11/2026, sau bản chấm L-09 vòng 2): phiên Claude Code (Anthropic) soạn và chép trực tiếp theo lệnh Owner «sửa tiếp»; vòng này không có gói giao của kiến trúc sư. Các chỗ sửa ở vòng 2 ghi rõ «vòng sửa 2» trong tệp này.
- Người chấm: theo L-09, ghi trong thân PR.
- Owner duyệt: lệnh trong chat Project ngày 26/11/2026, 23:53 giờ Việt Nam, giao kiến trúc sư toàn quyền quyết định sáu điều rút ra từ cách kiểm chứng minh VP ≠ VNP; xác nhận bằng việc gộp PR này.

## Bối cảnh

- Ngày 23/11/2026, kho `anthropics/formal-math` đăng chứng minh VP ≠ VNP bằng Lean. Cách kho đó tách phần kiểm: một tệp phát biểu ngắn (`Statement.lean`, 98 dòng) mà README nói thẳng là không máy nào kiểm được nghĩa; một tệp đề (`Challenge.lean`) và tệp cấu hình liệt kê đúng tên từng định lý, để trình so (Comparator) buộc chứng minh khớp đúng phát biểu đã đặt trước; một trình kiểm thứ hai viết độc lập (nanoda); một phụ lục đối chiếu từng phát biểu của bài với bản Lean và nói chỗ khác nhau.
- Soi phiếu máy của ADR-0020 theo cách đó, kiến trúc sư thấy một chỗ hở có thật trên `main` `b0c004b`: nhãn `[SUY LUẬN, sổ số liệu: <khóa>]` gọi tên khóa, nhưng `kiem_trich_dan.py` không đọc tên đó. Với đoạn SUY LUẬN, máy chỉ đếm: số trùng bất kỳ dòng nào của sổ thì xếp «SỔ», không trùng dòng nào thì «MÁY KHÔNG KIỂM»; cả hai không làm phiếu CHƯA ĐẠT. QĐ-H4 của ADR-0020 («mọi tỷ lệ, hiệu, tổng … máy tính lại; không tính nhẩm») vì thế chỉ được giữ bằng sự cẩn thận của người viết.
- Đã xảy ra thật: ở bản 1 của hồ sơ thứ hai, một câu in một tỷ lệ cho hai kỳ và nhãn gọi hai khóa; khóa của kỳ thứ hai làm tròn ra số khác. Phiếu máy ĐẠT; ghế phản biện khác hãng bắt ở B7. Cùng vòng đó, hai trong sáu điểm của ghế phản biện thuộc lớp định nghĩa: một công thức tính đúng số học nhưng hai kỳ không cùng phạm vi; một dòng của báo cáo lưu chuyển tiền tệ bị hiểu hẹp hơn nghĩa của nó.
- Ở hồ sơ thứ hai, ghế phản biện không mở được bốn tệp gốc vì quá dung lượng, trong đó có tệp gốc của luận điểm trung tâm. Điều này nằm trong bản phản biện; hồ sơ giao Owner không ghi.
- Mục 11 của mỗi hồ sơ có ngày xem lại; ngày gần nhất rơi vào cuối tháng 1/2027. Công cụ chưa có bước hậu kiểm; người chấm hậu kiểm cùng hãng với người viết.
- QĐ-H8 của ADR-0020: sau mốc dựng xong, thêm việc mới vào kiến trúc cần lệnh Owner. Lệnh 23:53 ngày 26/11/2026 là lệnh đó.

## Quyết định

### QĐ-K1 — Số SUY LUẬN gắn đúng khóa nhãn gọi tên

- Nhãn: cụm «sổ số liệu:» đứng trước dấu «;» đầu tiên; phần sau nó tới dấu «;» hoặc hết nhãn là danh sách khóa, cách nhau bằng dấu phẩy. «a05 tới a09» là dãy khóa cùng phần chữ, phần số tăng từng một, giữ số chữ số. Chữ sau dấu «;» là ghi chú, máy không đọc. Khóa không có trong sổ, dãy sai, hay phần không phải tên khóa trước dấu «;» là lỗi. Nhãn gọi khóa phải phủ ít nhất một chữ (vòng sửa 2).
- Chữ máy đọc (vòng sửa 2): máy đọc số và nhãn trên chữ người đọc thấy, tức sau khi bỏ dấu đậm «**» và dấu backtick mà không chèn gì vào chỗ đó. Dấu định dạng vì thế không tách được dấu âm, ngoặc, phần lẻ hay dấu % khỏi con số và không cắt một con số làm hai. Cổng định dạng báo lỗi mọi dòng mà cách đọc này khác cách đọc lúc thay dấu định dạng bằng dấu cách. Cụm chữ số không đọc được theo kiểu số Việt Nam («63.4», «1,234,567») ở đoạn SUY LUẬN hay đoạn không nhãn là lỗi.
- Phạm vi: mỗi lần nhãn xuất hiện là một phạm vi riêng, nhận theo vị trí của nhãn, không theo chữ của nhãn (vòng sửa 2): một nhãn cùng chữ ở chỗ khác không gộp vào. Phạm vi của một lần xuất hiện gồm phần chữ kết bằng nhãn đó, cộng các hàng dữ liệu của bảng mà đúng lần xuất hiện đó phủ: nhãn đứng đầu dòng ngay sau bảng, hoặc nhãn cuối của đoạn ngay trước bảng, chỉ cách bảng bằng dòng trống. Hàng bảng có nhãn trong ô là phạm vi riêng; một hàng chỉ mang một nhãn. Hàng tiêu đề của bảng và tiêu đề phụ không mang nhãn; số liệu viết ở đó là lỗi CHƯA GẮN NHÃN. Bảng phải là bảng thật của trình dựng: có dòng kẻ ngay dưới hàng tiêu đề, mọi hàng đủ đúng số ô; bảng giả và ô thừa là lỗi định dạng, vì trình dựng không hiện chúng như máy đọc.
- Chiều xuôi: mỗi con số trong đoạn SUY LUẬN, kể cả số viết trong backtick, phải khớp giá trị của một khóa nhãn gọi tên (làm tròn tới số chữ số đã viết, đổi đơn vị 10^3, 10^6, 10^9), hoặc là hằng số viết trong công thức của khóa đó, hoặc trùng một số ĐÃ KIỂM đã lần ra trong hồ sơ. Không thì KHÔNG GẮN KHÓA, phiếu CHƯA ĐẠT. Đoạn SUY LUẬN không gọi khóa nào thì mọi con số phải là số ĐÃ KIỂM nhắc lại. Số đứng đầu một mục liệt kê chỉ là số thứ tự khi nó dưới 10 hoặc danh sách được đánh đúng 1, 2, …, n; ở giữa đoạn hay trong ô bảng thì «63. » là con số; danh sách đánh số sai có số đầu mục từ 10 trở lên là lỗi (vòng sửa 2). Bộ lọc «không phải số liệu» chỉ nhận ngày tháng, giờ và năm hợp lệ, số mục không kèm «%», mã tài liệu L-, ADR-, QĐ-, PR-: «mỗi quý 63%», «cả năm 1300 tỷ», «63:37» là con số (vòng sửa 2).
- Chiều ngược: phạm vi có số liệu thì mỗi khóa nhãn gọi tên phải hiện ở ít nhất một con số của phạm vi đó; ở chiều này máy đọc cả số nhỏ, năm, số đếm thời gian và số trong backtick. «Có số liệu» là có một con số mà chiều xuôi xét, hoặc một số đếm thời gian từ 10 trở lên; năm, số nhỏ dưới 10, số thứ tự thật đầu mục liệt kê và số thứ tự trong bảng không tính. Ngày tháng («tháng 12 năm 2025») được bỏ trước khi tìm số đếm thời gian (vòng sửa 2). Câu dẫn hay câu định tính không có số liệu thì không xét. Khóa chỉ làm căn cứ thì đặt sau dấu «;».
- Đoạn GIẢ ĐỊNH và CHƯA BIẾT giữ như cũ: máy chỉ đếm. Ngưỡng của điều kiện sai ở Mục 11 là lựa chọn của ghế phân tích, viết dưới nhãn GIẢ ĐỊNH.
- Phiếu in thêm ba đường: KHÓA, HẰNG SỐ, KHÔNG GẮN KHÓA. Đường «SỔ» từ nay chỉ còn cho số ĐÃ KIỂM khớp dòng gốc đúng nguồn, đúng trang.

### QĐ-K2 — Bảng định nghĩa

- `tools/hoso/bang_dinh_nghia.py` in một bảng: mỗi khóa mà nhãn SUY LUẬN gọi tên, theo thứ tự gặp, kèm giá trị, đơn vị, công thức, các dòng gốc nó dựa vào (nguồn, trang, chuỗi máy đọc, dòng đã sửa) và các dòng hồ sơ dùng nó. Bảng không có giờ chạy.
- B7: ghế phân tích lập bảng cho bản gửi phản biện; ghế đối chiếu số nhận bảng và trả lời ba câu cho từng dòng: công thức có tính đúng điều câu hồ sơ nói không; cùng chỉ tiêu ở các kỳ có cùng phạm vi không; dòng gốc có đúng là khoản mục câu hồ sơ nói tới không. Mẫu C của `templates/hoso/LENH_MAU.md` thêm việc này.
- Bảng nằm trong thư mục mã, riêng tư như hồ sơ.

### QĐ-K3 — Mục «Trạng thái kiểm»

- Tiêu đề cấp hai đầu tiên của hồ sơ là «Trạng thái kiểm», bốn dòng: Phiếu máy; Đối chiếu số khác hãng; Phản biện khác hãng; Owner tự mở ba số. Ở B8, ghế phân tích ghi: ghế nào, kết quả, tệp gốc nào mỗi ghế không mở được, ý nào ở «Một trang» chưa được ghế khác hãng nào đối chiếu.
- Máy kiểm tiêu đề ở đúng chỗ và mỗi tên mở đầu đúng một mục liệt kê riêng. Bốn dòng phải là mục liệt kê thật, bắt đầu bằng «- ». Mỗi tiêu đề cấp hai của khung chỉ được xuất hiện một lần và đứng theo thứ tự của khung; tiêu đề lặp hay sai thứ tự là lỗi, và khi lặp máy xét thân của lần xuất hiện đầu tiên (vòng sửa 2). Mục nằm ngoài phạm vi đối chiếu trích dẫn như «Lịch sử sửa»; định dạng, L-02 và cổng giá vẫn áp.

### QĐ-K4 — Ba số Owner tự mở do máy chọn

- Sửa cách chọn ở QĐ-P9 của ADR-0019 («ba con số bất kỳ»). Cuối phiếu có mục «Owner tự mở ba số»: máy chọn theo sha256 của hồ sơ một số ĐÃ KIỂM ở «Một trang», một dòng máy đọc sai đã sửa và chứng minh, và một dòng gốc sau một khóa SUY LUẬN ở «Một trang». Thiếu loại nào thì lấy số ĐÃ KIỂM khác. Cùng hồ sơ ra cùng ba số; ghế phân tích không chọn trực tiếp, và sửa hồ sơ một chữ thì máy tính lại ba số theo sha256 mới (ba số có thể đổi, không chắc đổi). Ghế phân tích không sửa hồ sơ để đổi ba số.
- Mục này không ảnh hưởng kết luận ĐẠT hay CHƯA ĐẠT. Owner muốn mở thêm số nào cũng được.

### QĐ-K5 — Niêm phong bản đã giao và hậu kiểm theo đúng chữ

- Khi giao Owner, ghế phân tích ghi phiếu máy ĐẠT, có sha256 của hồ sơ, vào tài liệu của Project; Project ghi giờ. Từ lúc đó không sửa bản đã giao; muốn sửa thì làm bản mới, có phiếu mới.
- Hậu kiểm mở đúng bản đã giao, kiểm sha256, chép nguyên văn điều kiện sai của từng giả thuyết rồi mới ghi ĐÚNG, SAI hoặc CHƯA RÕ.
- Công cụ hậu kiểm (`tools/hoso/hau_kiem.py`) làm bằng một PR riêng, gộp trước ngày 15/01/2027. Không ghi sha256 hồ sơ lên kho công khai: Project đã ghi giờ, và mốc thời gian công khai không cần cho việc tự kiểm của Owner.

### QĐ-K6 — Trình kiểm thứ hai: hoãn, có điều kiện kích hoạt

- Phiếu máy là một bộ duy nhất, cùng hãng với ghế phân tích. Chưa viết trình kiểm thứ hai.
- Kích hoạt khi xảy ra một trong hai: (1) sau khi PR này gộp, ghế khác hãng hay hậu kiểm tìm ra một con số sai mà luật đã công bố của phiếu máy lẽ ra phải bắt; (2) phiếu máy cần thêm một vòng sửa vì một lỗi cùng loại với chỗ hở ở bối cảnh. Khi kích hoạt: kiến trúc sư soạn ADR mới; một ghế khác hãng viết bản kiểm nhỏ cho sha256 tệp gốc và cho việc mỗi con số lần ra trang, dòng gốc hay đúng khóa, chỉ từ chữ của quy trình, không đọc mã phiếu máy; hai bản phải ra cùng kết quả.
- Đã kích hoạt ngày 27/11/2026 theo điều kiện (2): lỗi chặn 1 của bản chấm L-09 vòng 1 (số trong backtick ở đoạn SUY LUẬN không bị xét) cùng loại với chỗ hở ở bối cảnh, và phiếu máy phải thêm vòng sửa 1. Bản chấm vòng 2 lại tìm ra lỗi cùng loại (dấu định dạng đổi con số SUY LUẬN mà phiếu vẫn ĐẠT), nên phải thêm vòng sửa 2. Sau khi PR này gộp, kiến trúc sư soạn ADR cho trình kiểm thứ hai.

### QĐ-K7 — Hai hồ sơ đã giao

- Hồ sơ thứ nhất bản 2 và hồ sơ thứ hai bản 2 giữ nguyên, với phiếu ĐẠT theo công cụ tại commit đã ghi. Không làm lại.
- Bản kế tiếp của mỗi hồ sơ, kể cả bản hậu kiểm, theo luật của ADR này.

## Trạng thái từng quyết định

| QĐ | Trạng thái | Owner | Ngày |
|---|---|---|---|
| QĐ-K1 tới QĐ-K7 | ACCEPTED theo lệnh Owner giao kiến trúc sư toàn quyền quyết định | Owner (lệnh 23:53 ngày 26/11/2026) | 27/11/2026 |
| QĐ-K6 | Điều kiện (2) đã xảy ra ở vòng sửa 1; ADR trình kiểm thứ hai soạn sau khi PR này gộp | Owner (khi gộp) | 27/11/2026 |

## Lý do (bằng chứng, số đo)

Đo ngày 27/11/2026, chỉ đọc, ở máy phân tích, ngoài kho:

- Hồ sơ mẫu số liệu bịa: viết sai một số SUY LUẬN thành số của khóa khác, hoặc thành số không có trong sổ, thì phiếu trên `b0c004b` vẫn ĐẠT (ca thứ nhất cho các con đếm giống hệt bản đúng). Sau bản sửa: cả hai CHƯA ĐẠT.
- Bản 1 của hồ sơ thứ hai (bản gửi phản biện): luật mới bắt đúng tỷ lệ in một số cho hai khóa ở chiều ngược.
- Hồ sơ thứ hai bản 2: 79 số KHÓA, 2 HẰNG SỐ; luật mới báo 6 lỗi, cả 6 là cách ghi nhãn: hai lỗi ở cùng một câu viết «nhân 1,1» trong khi công thức sổ viết `* 11 / 10` (chiều xuôi và chiều ngược), bốn khóa làm căn cứ cho câu định tính chưa đặt sau «;»; không lỗi giá trị. Bản đo trước vòng sửa 1 chỉ ra 5 lỗi: số thứ tự «6.» đầu mục bị đọc như con số và, sau khi làm tròn, khớp một khóa căn cứ.
- Hồ sơ thứ nhất bản 2: 157 số KHÓA, 40 số NHẮC LẠI; luật mới báo 34 lỗi: 26 số chưa gắn khóa, 2 khóa làm căn cứ, 4 nhãn sai cú pháp, 2 nhãn đặt «sổ số liệu:» sau dấu «;». Thử trên bản sao, đưa «sổ số liệu:» của hai nhãn đó lên trước dấu «;» thì còn đúng 30 lỗi của bản đo trước vòng sửa 1: 23 số chưa gắn khóa, 3 khóa làm căn cứ, 4 nhãn sai cú pháp (161 KHÓA, 39 NHẮC LẠI). Kiến trúc sư soát 23 số chưa gắn khóa: số tính nhẩm đúng giá trị (một tổng hai đợt giao dịch, một hiệu hai tỷ lệ); ngưỡng của giả thuyết và khoảng viết bằng lời; số đọc từ tài liệu nhưng đặt dưới nhãn SUY LUẬN; số trong bảng mang nhãn chữ thay cho khóa; một số đúng giá trị nhưng ngược dấu với dòng sổ. Không thấy số sai. Một số đọc từ tài liệu trùng tình cờ một dòng sổ khác chỉ tiêu: đúng loại trùng mà phiếu cũ đếm là «SỔ».
- Ba số máy chọn cho hồ sơ thứ hai bản 2: số lãi một lần ở «Một trang», một dòng máy đọc sai đã sửa, và một dòng gốc của công thức nợ vay ròng — đúng công thức ghế phản biện bắt sai phạm vi ở vòng một.
- `tests/test_hoso.py` và `tests/test_hoso_khoa.py`: 134 phép thử đạt, có đủ năm đầu vào của bản chấm vòng 1 và bốn đầu vào của bản chấm vòng 2 (lớp `VongSua2Tests`), kèm các ca cùng loại; lớp `VongSua2TanCongTests` chứa các đầu vào do một lượt tấn công độc lập tìm ra trên bản sửa đầu của vòng 2 (`42e42da`).
- Vòng sửa 2 chỉ đo trên hồ sơ mẫu số liệu bịa: 128 đầu vào chèn vào hồ sơ mẫu, chạy `phieu_may.lap_phieu`; 76 đầu vào phải ra CHƯA ĐẠT, 52 phải ra ĐẠT; trong đó có bốn đầu vào của bản chấm vòng 2. Trên mã vòng sửa 1 (`c5becc5`) 71 đầu vào cho kết quả sai (59 ca phiếu ĐẠT sai, 11 ca bắt nhầm, 1 ca văng lỗi). Trên bản sửa đầu của vòng 2 (`42e42da`) còn 25 ca sai (19, 5, 1): đó là các ca do một lượt tấn công độc lập tìm ra sau khi `42e42da` đã đẩy. Trên bản sửa cuối của vòng 2 cả 128 đúng. Trong 50 đầu vào lượt tấn công độc lập báo về, vòng này sửa 30 và không sửa 20 (9 ca phiếu ĐẠT sai, 5 ca bắt nhầm, 6 ca văng lỗi); 20 ca đó nằm ở các dòng «Điểm yếu đã biết» dưới đây và ở mục 4 của quy trình. Vòng sửa 2 chưa đo lại trên hai hồ sơ thật, vì phiên Claude Code không có hồ sơ thật: các số đo trên hồ sơ thật ở trên là của mã vòng sửa 1. Luật vòng sửa 2 chặt hơn (số kiểu Anh, số liệu ở tiêu đề, dấu định dạng, số thứ tự, bảng, bộ lọc ngày tháng), nên số lỗi trên hồ sơ thật có thể tăng; kiến trúc sư đo lại trước khi dùng luật này cho bản kế tiếp.

Điểm yếu đã biết:

- Số SUY LUẬN sai mà tình cờ trùng một số ĐÃ KIỂM khác trong hồ sơ (sau làm tròn tới số chữ số đã viết và đổi đơn vị), hay trùng một hằng số trong công thức của khóa (ví dụ 100 của phép đổi phần trăm), vẫn lọt chiều xuôi; chiều ngược bắt được nếu khóa nhãn gọi tên không hiện số nào.
- Chiều xuôi không xét số nguyên dưới 10 không kèm ký hiệu % («tăng 4 lần», «5 phần trăm»), năm, ngày tháng, số mục và số đếm thời gian: máy không coi chúng là số liệu. Số thứ tự dưới 10 đầu mục liệt kê cũng vậy.
- Con số dính liền sau một chữ cái («tăng63,4%») máy coi là mã như «VN30», không đọc. Dấu trừ viết cách con số một dấu cách («- 36,4»), dính sau một chữ cái hay dấu câu («là-36,4%»), hay đứng trước ngoặc («-(36,4%)») máy đọc là số không dấu. Con số đứng sau «mục, điểm, bản, vòng, đợt, lớp, bước, lần thứ», sau «tháng» (1–12), «quý» (1–4), «ngày» (1–31), và cặp số dạng ngày tháng hay giờ hợp lệ, máy coi là số mục, ngày tháng, giờ («mỗi tháng 12 tỷ đồng» không bị xét).
- Cổng định dạng chưa chặn ba cách viết làm chữ hiển thị khác chữ máy đọc: gạch bỏ bằng một dấu «~», công thức «$…$», định nghĩa liên kết đặt trong mục liệt kê. Ba cách này có từ ADR-0020 và là đề tài của PR #119 (đã đóng, chưa gộp); với chúng, một số SUY LUẬN sai vẫn có thể lọt. ADR này không sửa; cần Owner quyết riêng.
- Máy văng lỗi, không ra phiếu, với vài đầu vào cực đoan có từ ADR-0020: số trang hay số mục dài hơn 4300 chữ số, khoảng trang hàng tỷ trang, công thức sổ hàng nghìn số hạng, tệp không phải UTF-8. Không ra phiếu thì hồ sơ không ĐẠT, nhưng thông báo lỗi không rõ. Ký tự trông như dấu âm nhưng không thuộc nhóm gạch ngang của Unicode, và ký tự thay cho chữ số, máy không nhận ra.
- Con số viết trong chính nhãn (ghi chú sau dấu «;» và chữ tự do của nhãn) máy không đọc. Số viết ở phần đầu hồ sơ và ở các mục ngoài phạm vi đối chiếu (Trạng thái kiểm, Cách đọc, Bảng nguồn, Lịch sử sửa, Phiếu máy) máy không đối chiếu. Ở hàng tiêu đề bảng và tiêu đề phụ, máy chỉ bắt số liệu; năm, số nhỏ và số đếm thời gian thì không.
- Con số viết kiểu Anh («1,234.5») ở đoạn ĐÃ KIỂM máy bỏ qua như trước ADR này; vòng sửa 2 chỉ bắt ở đoạn SUY LUẬN, đoạn không nhãn, hàng tiêu đề bảng và tiêu đề phụ. Đây là chỗ hở có từ ADR-0020, cần một PR riêng.
- Trong một nhãn gọi nhiều khóa, máy không biết con số nào ứng với khóa nào: hai số đổi chỗ cho nhau vẫn qua.
- Số viết bằng chữ («ba mươi sáu phần trăm») máy không đọc.
- Chiều ngược bỏ qua phạm vi không có số liệu; khóa gọi tên ở đó chỉ được bảng định nghĩa đưa ra cho người đọc. Một câu định tính có số đếm thời gian từ 10 trở lên («12 tháng») bị coi là có số liệu: khóa căn cứ của câu đó phải đặt sau dấu «;».
- Máy vẫn không biết công thức có đúng nghĩa không. Bảng định nghĩa chỉ chuyển phần này tới đúng người đọc.
- Hai hồ sơ đã giao không đạt luật mới nếu chạy lại; QĐ-K7 nói rõ vì sao không làm lại.
- Ghế viết công cụ, ghế viết hồ sơ và ghế kiến trúc cùng hãng. QĐ-K6 đã kích hoạt nhưng trình kiểm thứ hai chưa viết.

## Không đổi

- L-01…L-10 và `governance/LAWS.md` không sửa. PR này không chạm `governance/`, `ledger/`, `paper/`, `research/`, `engine/`, `data/`.
- `autonomous_order_execution: false` và `live_trading_enabled: false` giữ nguyên. Không mở API trả phí. Công cụ chỉ dùng thư viện chuẩn của Python.
- Chữ của ADR-0019 và ADR-0020 không sửa. ADR này sửa cách chọn ba số ở QĐ-P9 (QĐ-K4) và thêm luật cho đoạn SUY LUẬN vào phép kiểm 4 của QĐ-H3.
- Năm phép kiểm của phiếu, cổng giá, khoảng giá giữ nguyên. Định dạng cho phép giữ nguyên bộ Markdown hẹp; vòng sửa 2 thêm vào đó luật «dấu định dạng không đổi con số» (`kiem_luat._dd_so`) và cấm thêm ký tự trống thuộc nhóm chữ. Cách lần số ĐÃ KIỂM về trang và sổ giữ nguyên. Sáu luật của vòng sửa 2 áp cho mọi nhãn, kể cả ĐÃ KIỂM, và đều theo hướng chặt hơn: đọc số trên chữ hiển thị (dấu đậm không cắt được con số, dấu âm sát ngoài backtick được giữ); «63. » chỉ là số thứ tự ở đầu mục của danh sách đánh đúng; nhãn đứng sau bảng chỉ được cách bảng bằng dòng trống; một hàng bảng một nhãn; hàng tiêu đề bảng và tiêu đề phụ không chứa số liệu; mỗi tiêu đề cấp hai một lần.

## Điều kiện hoàn tác

1. Sau hai hồ sơ làm theo luật mới: nếu luật khóa không bắt được con số sai thật nào và ghế phân tích phải sửa hơn 40 chỗ chỉ vì cách ghi nhãn, kiến trúc sư báo Owner trong 7 ngày. Owner chọn bằng một ADR mới: giữ, hạ chiều ngược thành cảnh báo, hoặc bỏ QĐ-K1.
2. Tới hết ngày 15/01/2027 chưa gộp công cụ hậu kiểm của QĐ-K5: hậu kiểm đầu tiên làm theo B8 bước 5 bằng tay; kiến trúc sư báo Owner.
3. Hoàn tác không cần khôi phục gì: gỡ bằng một PR đảo các thay đổi của PR này. Hồ sơ làm trong thời gian ADR có hiệu lực giữ phiếu của chúng, vì phiếu ghi commit công cụ.

## Ảnh hưởng tới ARCHITECTURE.md

- Dòng trạng thái đầu tệp: thêm ADR-0021.
- Thêm một đoạn ngắn sau đoạn «Từ ADR-0020», trỏ tới ADR này.
- Chữ của §0–§10 giữ nguyên.
