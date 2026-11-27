# Ba mẫu lệnh của quy trình hồ sơ mã

Dùng ở bước B2 và B7 của `docs/QUY_TRINH_HO_SO_MA.md`. Thay phần trong ngoặc nhọn. Owner là người dán lệnh cho từng ghế.

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
