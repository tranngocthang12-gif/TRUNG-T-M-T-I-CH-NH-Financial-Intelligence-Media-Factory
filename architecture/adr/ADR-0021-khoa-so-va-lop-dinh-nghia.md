# ADR-0021: Số SUY LUẬN gắn đúng khóa sổ, lớp định nghĩa và trạng thái kiểm của hồ sơ mã

- Ngày: 2026-11-27
- Trạng thái: ACCEPTED 27/11/2026 theo lệnh Owner, hiệu lực khi Owner gộp PR này.
- Người đề xuất: Claude Project TTC (Anthropic), ghế kiến trúc sư trưởng. Chép vào kho: phiên Claude Code (Anthropic).
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

- Nhãn: phần sau «sổ số liệu:» tới dấu «;» hoặc hết nhãn là danh sách khóa, cách nhau bằng dấu phẩy. «a05 tới a09» là dãy khóa cùng phần chữ, phần số tăng từng một, giữ số chữ số. Chữ sau dấu «;» là ghi chú, máy không đọc. Khóa không có trong sổ, dãy sai, hay phần không phải tên khóa trước dấu «;» là lỗi.
- Chiều xuôi: mỗi con số trong đoạn SUY LUẬN phải khớp giá trị của một khóa nhãn gọi tên (làm tròn tới số chữ số đã viết, đổi đơn vị 10^3, 10^6, 10^9), hoặc là hằng số viết trong công thức của khóa đó, hoặc trùng một số ĐÃ KIỂM đã lần ra trong hồ sơ. Không thì KHÔNG GẮN KHÓA, phiếu CHƯA ĐẠT. Đoạn SUY LUẬN không gọi khóa nào thì mọi con số phải là số ĐÃ KIỂM nhắc lại.
- Chiều ngược: phần chữ nhãn phủ (cả bảng, khi nhãn phủ bảng) có chữ số thì mỗi khóa nhãn gọi tên phải hiện ở ít nhất một con số của phần chữ đó; ở chiều này máy đọc cả số nhỏ, năm và số đếm thời gian. Câu dẫn hay câu định tính không có chữ số thì không xét. Khóa chỉ làm căn cứ thì đặt sau dấu «;».
- Đoạn GIẢ ĐỊNH và CHƯA BIẾT giữ như cũ: máy chỉ đếm. Ngưỡng của điều kiện sai ở Mục 11 là lựa chọn của ghế phân tích, viết dưới nhãn GIẢ ĐỊNH.
- Phiếu in thêm ba đường: KHÓA, HẰNG SỐ, KHÔNG GẮN KHÓA. Đường «SỔ» từ nay chỉ còn cho số ĐÃ KIỂM khớp dòng gốc đúng nguồn, đúng trang.

### QĐ-K2 — Bảng định nghĩa

- `tools/hoso/bang_dinh_nghia.py` in một bảng: mỗi khóa mà nhãn SUY LUẬN gọi tên, theo thứ tự gặp, kèm giá trị, đơn vị, công thức, các dòng gốc nó dựa vào (nguồn, trang, chuỗi máy đọc, dòng đã sửa) và các dòng hồ sơ dùng nó. Bảng không có giờ chạy.
- B7: ghế phân tích lập bảng cho bản gửi phản biện; ghế đối chiếu số nhận bảng và trả lời ba câu cho từng dòng: công thức có tính đúng điều câu hồ sơ nói không; cùng chỉ tiêu ở các kỳ có cùng phạm vi không; dòng gốc có đúng là khoản mục câu hồ sơ nói tới không. Mẫu C của `templates/hoso/LENH_MAU.md` thêm việc này.
- Bảng nằm trong thư mục mã, riêng tư như hồ sơ.

### QĐ-K3 — Mục «Trạng thái kiểm»

- Tiêu đề cấp hai đầu tiên của hồ sơ là «Trạng thái kiểm», bốn dòng: Phiếu máy; Đối chiếu số khác hãng; Phản biện khác hãng; Owner tự mở ba số. Ở B8, ghế phân tích ghi: ghế nào, kết quả, tệp gốc nào mỗi ghế không mở được, ý nào ở «Một trang» chưa được ghế khác hãng nào đối chiếu.
- Máy chỉ kiểm có tiêu đề ở đúng chỗ và đủ bốn dòng. Mục nằm ngoài phạm vi đối chiếu trích dẫn như «Lịch sử sửa»; định dạng, L-02 và cổng giá vẫn áp.

### QĐ-K4 — Ba số Owner tự mở do máy chọn

- Sửa cách chọn ở QĐ-P9 của ADR-0019 («ba con số bất kỳ»). Cuối phiếu có mục «Owner tự mở ba số»: máy chọn theo sha256 của hồ sơ một số ĐÃ KIỂM ở «Một trang», một dòng máy đọc sai đã sửa và chứng minh, và một dòng gốc sau một khóa SUY LUẬN ở «Một trang». Thiếu loại nào thì lấy số ĐÃ KIỂM khác. Cùng hồ sơ ra cùng ba số; ghế phân tích không chọn được.
- Mục này không ảnh hưởng kết luận ĐẠT hay CHƯA ĐẠT. Owner muốn mở thêm số nào cũng được.

### QĐ-K5 — Niêm phong bản đã giao và hậu kiểm theo đúng chữ

- Khi giao Owner, ghế phân tích ghi phiếu máy ĐẠT, có sha256 của hồ sơ, vào tài liệu của Project; Project ghi giờ. Từ lúc đó không sửa bản đã giao; muốn sửa thì làm bản mới, có phiếu mới.
- Hậu kiểm mở đúng bản đã giao, kiểm sha256, chép nguyên văn điều kiện sai của từng giả thuyết rồi mới ghi ĐÚNG, SAI hoặc CHƯA RÕ.
- Công cụ hậu kiểm (`tools/hoso/hau_kiem.py`) làm bằng một PR riêng, gộp trước ngày 15/01/2027. Không ghi sha256 hồ sơ lên kho công khai: Project đã ghi giờ, và mốc thời gian công khai không cần cho việc tự kiểm của Owner.

### QĐ-K6 — Trình kiểm thứ hai: hoãn, có điều kiện kích hoạt

- Phiếu máy là một bộ duy nhất, cùng hãng với ghế phân tích. Chưa viết trình kiểm thứ hai.
- Kích hoạt khi xảy ra một trong hai: (1) sau khi PR này gộp, ghế khác hãng hay hậu kiểm tìm ra một con số sai mà luật đã công bố của phiếu máy lẽ ra phải bắt; (2) phiếu máy cần thêm một vòng sửa vì một lỗi cùng loại với chỗ hở ở bối cảnh. Khi kích hoạt: kiến trúc sư soạn ADR mới; một ghế khác hãng viết bản kiểm nhỏ cho sha256 tệp gốc và cho việc mỗi con số lần ra trang, dòng gốc hay đúng khóa, chỉ từ chữ của quy trình, không đọc mã phiếu máy; hai bản phải ra cùng kết quả.

### QĐ-K7 — Hai hồ sơ đã giao

- Hồ sơ thứ nhất bản 2 và hồ sơ thứ hai bản 2 giữ nguyên, với phiếu ĐẠT theo công cụ tại commit đã ghi. Không làm lại.
- Bản kế tiếp của mỗi hồ sơ, kể cả bản hậu kiểm, theo luật của ADR này.

## Trạng thái từng quyết định

| QĐ | Trạng thái | Owner | Ngày |
|---|---|---|---|
| QĐ-K1 tới QĐ-K7 | ACCEPTED theo lệnh Owner giao kiến trúc sư toàn quyền quyết định | Owner (lệnh 23:53 ngày 26/11/2026) | 27/11/2026 |

## Lý do (bằng chứng, số đo)

Đo ngày 27/11/2026, chỉ đọc, ở máy phân tích, ngoài kho:

- Hồ sơ mẫu số liệu bịa: viết sai một số SUY LUẬN thành số của khóa khác, hoặc thành số không có trong sổ, thì phiếu trên `b0c004b` vẫn ĐẠT (ca thứ nhất cho các con đếm giống hệt bản đúng). Sau bản sửa: cả hai CHƯA ĐẠT.
- Bản 1 của hồ sơ thứ hai (bản gửi phản biện): luật mới bắt đúng tỷ lệ in một số cho hai khóa ở chiều ngược.
- Hồ sơ thứ hai bản 2: 79 số KHÓA, 2 HẰNG SỐ; luật mới báo 5 lỗi, cả 5 là cách ghi nhãn (một hằng số viết trong công thức dưới dạng 11/10, bốn khóa làm căn cứ cho câu định tính chưa đặt sau «;»), không lỗi giá trị.
- Hồ sơ thứ nhất bản 2: 161 số KHÓA, 39 số NHẮC LẠI; luật mới báo 30 lỗi: 23 số chưa gắn khóa, 3 khóa làm căn cứ, 4 nhãn sai cú pháp. Kiến trúc sư soát 23 số chưa gắn khóa: số tính nhẩm đúng giá trị (một tổng hai đợt giao dịch, một hiệu hai tỷ lệ); ngưỡng của giả thuyết và khoảng viết bằng lời; số đọc từ tài liệu nhưng đặt dưới nhãn SUY LUẬN; số trong bảng mang nhãn chữ thay cho khóa; một số đúng giá trị nhưng ngược dấu với dòng sổ. Không thấy số sai. Một số đọc từ tài liệu trùng tình cờ một dòng sổ khác chỉ tiêu: đúng loại trùng mà phiếu cũ đếm là «SỔ».
- Ba số máy chọn cho hồ sơ thứ hai bản 2: số lãi một lần ở «Một trang», một dòng máy đọc sai đã sửa, và một dòng gốc của công thức nợ vay ròng — đúng công thức ghế phản biện bắt sai phạm vi ở vòng một.
- `tests/test_hoso.py` và `tests/test_hoso_khoa.py`: 100 phép thử đạt.

Điểm yếu đã biết:

- Số SUY LUẬN sai mà tình cờ trùng một số ĐÃ KIỂM khác trong hồ sơ, hay trùng một hằng số trong công thức của khóa (ví dụ 100 của phép đổi phần trăm), vẫn lọt chiều xuôi; chiều ngược bắt được nếu khóa nhãn gọi tên không hiện số nào.
- Chiều ngược bỏ qua câu không có chữ số; khóa gọi tên ở câu đó chỉ được bảng định nghĩa đưa ra cho người đọc.
- Máy vẫn không biết công thức có đúng nghĩa không. Bảng định nghĩa chỉ chuyển phần này tới đúng người đọc.
- Hai hồ sơ đã giao không đạt luật mới nếu chạy lại; QĐ-K7 nói rõ vì sao không làm lại.
- Ghế viết công cụ, ghế viết hồ sơ và ghế kiến trúc cùng hãng; QĐ-K6 mới chỉ là điều kiện, chưa là trình kiểm.

## Không đổi

- L-01…L-10 và `governance/LAWS.md` không sửa. PR này không chạm `governance/`, `ledger/`, `paper/`, `research/`, `engine/`, `data/`.
- `autonomous_order_execution: false` và `live_trading_enabled: false` giữ nguyên. Không mở API trả phí. Công cụ chỉ dùng thư viện chuẩn của Python.
- Chữ của ADR-0019 và ADR-0020 không sửa. ADR này sửa cách chọn ba số ở QĐ-P9 (QĐ-K4) và thêm luật cho đoạn SUY LUẬN vào phép kiểm 4 của QĐ-H3.
- Năm phép kiểm của phiếu, cổng giá, khoảng giá, định dạng cho phép giữ nguyên.

## Điều kiện hoàn tác

1. Sau hai hồ sơ làm theo luật mới: nếu luật khóa không bắt được con số sai thật nào và ghế phân tích phải sửa hơn 40 chỗ chỉ vì cách ghi nhãn, kiến trúc sư báo Owner trong 7 ngày. Owner chọn bằng một ADR mới: giữ, hạ chiều ngược thành cảnh báo, hoặc bỏ QĐ-K1.
2. Tới hết ngày 15/01/2027 chưa gộp công cụ hậu kiểm của QĐ-K5: hậu kiểm đầu tiên làm theo B8 bước 5 bằng tay; kiến trúc sư báo Owner.
3. Hoàn tác không cần khôi phục gì: gỡ bằng một PR đảo các thay đổi của PR này. Hồ sơ làm trong thời gian ADR có hiệu lực giữ phiếu của chúng, vì phiếu ghi commit công cụ.

## Ảnh hưởng tới ARCHITECTURE.md

- Dòng trạng thái đầu tệp: thêm ADR-0021.
- Thêm một đoạn ngắn sau đoạn «Từ ADR-0020», trỏ tới ADR này.
- Chữ của §0–§10 giữ nguyên.
