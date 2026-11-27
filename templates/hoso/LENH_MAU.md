# Năm mẫu lệnh của quy trình hồ sơ mã

Mẫu A, B, C dùng ở bước B2 và B7 của `docs/QUY_TRINH_HO_SO_MA.md`; mẫu D và mẫu E dùng ở mục 5 của tệp đó (ADR-0024). Thay phần trong ngoặc nhọn. Owner là người dán lệnh cho từng ghế.

---

## Mẫu A. Lệnh tải tệp gốc (gửi Cowork, bước B2)

Việc: tải các tệp dưới đây về thư mục `Downloads\TTC_HO_SO\<MÃ>\goc\` trên máy này. Không đổi tên tệp. Không mở, không sửa.

| # | Tài liệu | Đường dẫn |
|---|---|---|
| 1 | <tên tài liệu> | <đường dẫn từ bảng của ghế tìm nguồn> |

Tải xong, báo lại một bảng: tên tệp, dung lượng, SHA256 đầy đủ. Tệp nào không tải được thì ghi rõ lỗi, không thay bằng tệp khác.

Không đăng nhập ở đâu. Không gửi tệp đi đâu.

---

## Mẫu B. Lệnh phản biện (gửi một ghế khác hãng Anthropic, bước B7)

Bạn là ghế phản biện của dự án TTC. Tệp đính kèm là hồ sơ phân tích mã <MÃ>, bản phản biện. Tài liệu gốc ở các đường dẫn cuối lệnh.

**Dòng đầu bản trả lời: chép lại "Mã nhận tệp" in ở đầu tệp đính kèm.** Không thấy tệp đính kèm thì trả lời đúng một câu: "Chưa nhận được tệp", và dừng.

Viết bốn phần:

1. Luận điểm ngược mạnh nhất với hồ sơ.
2. Ba điều hồ sơ nói mà chưa chứng minh.
3. Các con số then chốt bạn đã tự mở tài liệu gốc để đối chiếu: ghi số trong hồ sơ, số trong tài liệu gốc, trang, KHỚP hay LỆCH.
4. Một việc Owner nên tự kiểm.

Sau bốn phần, trả lời câu hỏi bắt buộc (máy chỉ bắt câu giá theo dấu hiệu, không bắt hết): **Liệt kê mọi câu trong hồ sơ nêu hoặc ngụ ý giá tương lai, khoảng giá trị, hệ số định giá mục tiêu, hay hành động với cổ phiếu. Không có thì ghi "không có".**

Câu hỏi bắt buộc thứ hai (ADR-0023): **Với từng điều kiện đổi trạng thái ở Mục 9, hai người đọc độc lập cùng một văn bản có thể chấm khác nhau không? Có câu nào ở Mục 9 nêu hay ngụ ý biến sẽ đi hướng nào, cộng các biến thành điểm, hay viết tác động có điều kiện lên lợi nhuận không? Không có thì ghi "không có".**

Luật:

- Không nêu hành động nào với cổ phiếu. Không nêu khoảng giá trị hay mức giá nào.
- Chỉ dùng tài liệu gốc trong danh sách. Điều gì lấy từ nơi khác thì ghi rõ nơi đó.
- Không sửa hồ sơ. Chỉ viết bản phản biện.

Tài liệu gốc:

| Mã | Tài liệu | Đường dẫn |
|---|---|---|
| D1 | <tên> | <đường dẫn> |

---

## Mẫu C. Lệnh đối chiếu số (gửi một ghế khác hãng Anthropic, khác ghế ở mẫu B nếu được, bước B7)

Bạn là ghế đối chiếu số của dự án TTC. Tệp đính kèm là hồ sơ phân tích mã <MÃ>, bản phản biện.

**Dòng đầu bản trả lời: chép lại "Mã nhận tệp" in ở đầu tệp đính kèm.** Không thấy tệp đính kèm thì trả lời đúng một câu: "Chưa nhận được tệp", và dừng.

Việc: với từng dòng trong bảng dưới, mở tài liệu gốc ở đúng trang, đọc con số, rồi ghi KHỚP hoặc LỆCH kèm số bạn đọc được. Không suy luận, không giải thích, không nhận xét về doanh nghiệp.

| # | Hồ sơ ghi | Ở đâu trong hồ sơ | Tài liệu gốc, trang |
|---|---|---|---|
| 1 | <con số> | <mục, dòng> | <D1 tr.12> |

Bảng phải phủ mọi mục có nhãn ĐÃ KIỂM của hồ sơ, mỗi mục ít nhất một dòng, và phải có dòng chứa chỗ đã gài lỗi (ghế phân tích tự lo việc này; không đánh dấu dòng đó).

**Việc thứ hai (ADR-0021 QĐ-K2): bảng định nghĩa.** Tệp đính kèm thứ hai là `BANG_DINH_NGHIA_<…>.md`. Mỗi dòng là một số hồ sơ tự tính: công thức, giá trị, các dòng gốc (nguồn, trang, chuỗi máy đọc) và dòng hồ sơ dùng nó. Với từng dòng, ghi KHỚP NGHĨA hoặc LỆCH NGHĨA kèm một câu lý do, theo ba câu hỏi:

1. Công thức có tính đúng điều câu hồ sơ ở cột «Dùng ở» nói không?
2. Cùng một chỉ tiêu ở các kỳ khác nhau có cùng công thức, cùng phạm vi không?
3. Dòng gốc có đúng là khoản mục câu hồ sơ nói tới không? Mở trang để xem tên dòng in trên báo cáo.

Tệp gốc nào bạn không mở được thì ghi rõ tên tệp; không ghi KHỚP cho dòng dựa vào tệp đó.

Tài liệu gốc: như bảng ở mẫu B.

---

## Mẫu D. Lệnh dự báo chỉ tiêu (ghế dự án; ADR-0024 QĐ-N1)

Chỉ gửi câu trong sổ câu hỏi đã khóa. Gửi cho ChatGPT và Gemini, mỗi ghế một cuộc chat mới, tắt bộ nhớ hội thoại nếu được. Ghế phân tích tự trả lời đúng mẫu này và ghi vào Project trước khi Owner gửi. Không gửi bản phản biện, lập luận của bên nào trong một điểm bất đồng, hay trả lời của ghế khác.

[TTC] DỰ BÁO CHỈ TIÊU — mã lệnh <D-MÃ-kỳ-ngày>

Bạn là một ghế dự báo của dự án TTC. Các ghế khác nhận cùng câu hỏi; bạn không thấy trả lời của họ. Tệp đính kèm: hồ sơ mã <MÃ> bản đã giao (sha256 <…>), tệp gốc <danh sách mã tệp>. Được dùng tệp đính kèm và nguồn công khai; nguồn nào ngoài tệp đính kèm thì ghi rõ.

Câu hỏi đã khóa, không sửa:
<mã câu>: <câu nêu đủ chỉ tiêu, báo cáo hợp nhất hay riêng, kỳ riêng hay lũy kế, số công bố lần đầu, ngưỡng, cách tính khi đúng bằng ngưỡng, nguồn phân định, ngày phân định>

Phần khai: tên và phiên bản mô hình; hãng; tháng cắt dữ liệu dạng YYYY-MM, theo mô hình tự biết; có dùng tìm kiếm không; tệp đính kèm nào mở được, tệp nào không.

Với mỗi câu, trả lời bốn thứ:
- p: xác suất từ 0,05 tới 0,95 để câu trả lời là CÓ.
- Tỷ lệ nền, và cách lấy (ví dụ: số kỳ trong tám kỳ gần nhất chỉ tiêu vượt ngưỡng).
- Điều làm trả lời của bạn sai, một câu.
- Lý do chính, tối đa ba câu; câu dùng số thì ghi mã tệp và trang.

Câu nào bạn thấy không phân định được thì ghi «KHÔNG TRẢ LỜI: <lý do>» và không cho p.

Luật: không nêu hành động với cổ phiếu, không nêu giá cổ phiếu hay khoảng giá trị.

Trả lời đúng mẫu, trong một khối mã:
MÃ LỆNH: <D-MÃ-kỳ-ngày>
GHẾ: <tên và phiên bản mô hình, hãng>
CẮT DỮ LIỆU: <YYYY-MM>
TÌM KIẾM: <có hoặc không>
TỆP MỞ ĐƯỢC: <…>; KHÔNG MỞ ĐƯỢC: <…>
<mã câu>: p=…; tỷ lệ nền=… (cách lấy: …); sai khi: …; lý do: …
Dừng.

---

## Mẫu E. Lệnh cho ghế độc lập: duyệt sổ câu hỏi và đọc lịch công bố (ADR-0024 QĐ-N1, QĐ-N5)

Gửi cho Grok, cuộc chat mới. Ghế độc lập không góp xác suất. Owner làm thay khi Grok không dùng được. Owner mở Issue «Calendar» bằng nội dung ghế độc lập trả, `recorder` ghi tên ghế độc lập.

[TTC] DUYỆT SỔ CÂU HỎI VÀ LỊCH CÔNG BỐ — vòng <MÃ>-<kỳ> — mã lệnh <E-MÃ-kỳ-ngày>

Bạn là ghế độc lập của vòng dự báo này; bạn không trả lời xác suất. Đính kèm: sổ câu hỏi của vòng. Với câu đến từ một điểm bất đồng, có thêm nguyên văn hai lập luận, chỉ để bạn kiểm câu hỏi trung tính.

Việc 1. Duyệt từng câu theo bốn điều:
- Rõ: đủ chỉ tiêu, báo cáo hợp nhất hay riêng, kỳ riêng hay lũy kế, số công bố lần đầu, ngưỡng, cách tính khi đúng bằng ngưỡng.
- Phân định được bằng nguồn đã nêu, trên tên miền đã nêu.
- Trung tính: không nghiêng về lập luận nào, không chứa đoạn hồ sơ.
- Không nói về giá cổ phiếu, khối lượng giao dịch, chỉ số thị trường hay hướng đi của biến bên ngoài; không có lời hành động.

Việc 2. Lịch công bố cho từng báo cáo được hỏi (ADR-0024 QĐ-N1 điểm 6). Tên miền phải nằm trong nguồn phân định; evidence_url là https trên tên miền đó.
- Doanh nghiệp hay sở giao dịch đã công bố ngày sẽ đưa ra con số phân định, hay một con số sơ bộ của cùng chỉ tiêu, cùng kỳ: đó là LỊCH CHÍNH THỨC. info_lock_at là ngày đó; evidence_url là trang nêu ngày; trích dẫn là nguyên văn câu nêu ngày.
- Không có lịch chính thức: LỊCH SUY RA. Tìm lần sớm nhất doanh nghiệp đã công bố một con số của cùng chỉ tiêu cho cùng kỳ năm trước, kể cả số ước tính hay sơ bộ. info_lock_at là ngày sớm hơn giữa ngày cuối của kỳ được hỏi và ngày tương ứng năm nay của ngày vừa tìm, lùi thêm 14 ngày. calendar_id bắt đầu bằng CAL-ADR24-SUYRA-. Trích dẫn mở đầu bằng câu «LỊCH SUY RA THEO ADR-0024, KHÔNG PHẢI LỊCH CHÍNH THỨC.», sau đó là nguyên văn câu có ngày của lần công bố năm trước; evidence_url trỏ tới chính lần công bố đó.
- Nhiều câu dùng chung một báo cáo mà ngày suy ra khác nhau: lấy ngày sớm nhất.
- Không có bằng chứng đáng tin cho cả hai loại: ghi KHÔNG ĐỦ BẰNG CHỨNG.

Trả lời đúng mẫu, trong một khối mã:
MÃ LỆNH: <E-MÃ-kỳ-ngày>
GHẾ: <tên mô hình, hãng>
<mã câu>: ĐẠT, hoặc SỬA: <điều phải sửa>
LỊCH <báo cáo>: loại=<LỊCH CHÍNH THỨC hoặc LỊCH SUY RA>; calendar_id=…; domains=…; evidence_url=…; trích dẫn="…"; ngày năm trước=… (chỉ với lịch suy ra); info_lock_at=…, hoặc KHÔNG ĐỦ BẰNG CHỨNG: <lý do>
Dừng.
