# Ba điểm cờ đỏ kế toán (ADR-0025 QĐ-L2)

Dùng ở Mục 6 của hồ sơ mã. Ba điểm tính từ báo cáo tài chính năm của chính doanh nghiệp, không dùng giá cổ phiếu. Năm t là năm tài chính gần nhất có báo cáo đã kiểm toán; t − 1 và t − 2 là hai năm liền trước. Cần báo cáo năm t và năm t − 1 kèm thuyết minh (báo cáo năm t − 1 cho số cuối năm t − 2).

## Luật dùng

- Mỗi đầu vào là một dòng gốc của sổ số liệu. `ghi_chu` ghi: chế độ kế toán của báo cáo, tên khoản mục, mã số chỉ tiêu, kỳ, đơn vị, hợp nhất hay riêng. Không giả định mã số chỉ tiêu giống nhau giữa hai chế độ kế toán. Cả ba điểm dùng cùng một loại báo cáo (hợp nhất khi doanh nghiệp có báo cáo hợp nhất).
- Mỗi tỷ số, điểm M và điểm Z là một dòng tính của sổ. Điểm F không là dòng tính, vì bộ tính của sổ không có phép so sánh: hồ sơ ghi đạt hay không của từng tiêu chí kèm khóa của tỷ số, rồi ghi tổng; ghế đối chiếu số kiểm lại từng tiêu chí và tổng.
- Không tính cho ngân hàng, công ty bảo hiểm, công ty chứng khoán, công ty tài chính: ghi «không áp dụng». Ba nghiên cứu gốc không dùng mẫu doanh nghiệp tài chính.
- Thiếu đầu vào trên tệp đã ghim, hoặc một mẫu số bằng không, hoặc phép so không làm được: không lập dòng tính đó; tiêu chí hay tỷ số ghi CHƯA BIẾT kèm lý do. Không thay bằng giá trị trung tính.
- Điểm M hay điểm Z thiếu một tỷ số thì cả điểm ghi CHƯA BIẾT. Điểm F chỉ ghi tổng và cờ khi đủ chín tiêu chí; thiếu thì ghi ba số: số tiêu chí đạt, số tiêu chí tính được, trên chín, và cờ ghi CHƯA BIẾT.
- Mọi đầu vào của một phép tính phải cùng đơn vị tiền. Báo cáo hai năm khác đơn vị thì lập dòng tính quy đổi, giữ nguyên dòng gốc.
- So với ngưỡng và chấm từng tiêu chí bằng giá trị trong sổ trước khi làm tròn, không bằng số đã làm tròn để trình bày.
- Ngưỡng lấy từ nghiên cứu gốc trên dữ liệu Mỹ, chưa thử trên doanh nghiệp Việt Nam: viết dưới nhãn GIẢ ĐỊNH. Mọi chỗ ánh xạ khoản mục sang báo cáo Việt Nam ghi dưới đây cũng là GIẢ ĐỊNH.

## Cách viết trong hồ sơ

- Tiêu đề phụ «### Điểm cờ đỏ kế toán». Câu đầu, giữ nguyên chữ: «Ba điểm dưới đây chỉ nêu khoản mục cần soi thêm; không phải kết luận về doanh nghiệp, không phải xác suất sai phạm, không phải căn cứ hành động với cổ phiếu.»
- Tên viết bằng chữ («điểm F», «điểm M», «điểm Z»); ký hiệu tiếng Anh dưới đây chỉ dùng trong khóa sổ.
- Cờ bật thì viết đúng tên điểm bật cờ («cờ F bật», «cờ M bật» hay «cờ Z bật», theo ngưỡng giả định), nêu các tỷ số đóng góp lớn nhất và khoản mục cần soi, nối với điểm soi tương ứng. Không viết rằng doanh nghiệp làm đẹp lợi nhuận, gian lận hay sắp vỡ nợ; không gọi tỷ số đóng góp là nguyên nhân.
- Ba điểm dùng chung nhiều khoản mục: ba cờ cùng bật không phải ba bằng chứng độc lập.
- Không xếp hạng mã theo điểm, không cộng các điểm, không đưa điểm vào câu đánh giá doanh nghiệp tốt hay xấu, câu về giá cổ phiếu, khoảng giá trị hay lời hành động.

## Điểm F (Piotroski 2000): chín tiêu chí có hay không

Đạt được 1, không đạt được 0; điểm F là tổng, từ 0 tới 9. «Tài sản đầu năm» là tổng tài sản cuối năm trước.

| # | Tiêu chí | Được 1 khi |
|---|---|---|
| 1 | ROA: lợi nhuận sau thuế thu nhập doanh nghiệp năm t (cả phần của cổ đông không kiểm soát) chia tài sản đầu năm t. Nghiên cứu gốc dùng lợi nhuận trước khoản mục bất thường; chuẩn mực Việt Nam không tách khoản mục đó, nên dùng lợi nhuận sau thuế làm đại lượng thay thế | ROA dương |
| 2 | CFO: lưu chuyển tiền thuần từ hoạt động kinh doanh năm t chia tài sản đầu năm t | CFO dương |
| 3 | ROA năm t trừ ROA năm t − 1 | Dương |
| 4 | So CFO với ROA cùng năm t | CFO lớn hơn ROA |
| 5 | Đòn bẩy: (vay và nợ thuê tài chính dài hạn + phần vay dài hạn đến hạn trả, tách từ thuyết minh vay) chia tài sản bình quân, năm t so với năm t − 1. Không tách được phần đến hạn trả thì ghi CHƯA BIẾT | Giảm. Bằng nhau, kể cả cùng bằng 0, ghi 0 |
| 6 | Thanh khoản: tài sản ngắn hạn chia nợ ngắn hạn, cuối năm t so với cuối năm t − 1 | Tăng |
| 7 | Phát hành cổ phiếu phổ thông đã hoàn tất trong năm t: chào bán cho cổ đông hiện hữu, phát hành riêng lẻ, cổ phiếu cho người lao động, chuyển đổi trái phiếu. Không tính cổ phiếu thưởng, cổ tức bằng cổ phiếu, phát hành từ nguồn vốn chủ sở hữu, nghị quyết chưa thực hiện. Dẫn mã tệp và trang của thuyết minh vốn chủ sở hữu | Không phát hành |
| 8 | Biên lợi nhuận gộp: lợi nhuận gộp chia doanh thu thuần, năm t so với năm t − 1 | Tăng |
| 9 | Vòng quay tài sản: doanh thu thuần chia tài sản đầu năm, năm t so với năm t − 1. Nghiên cứu gốc ghi tài sản đầu năm ở phần định nghĩa và tài sản bình quân ở chú thích bảng 1; hồ sơ dùng tài sản đầu năm | Tăng |

Cờ: điểm F đủ chín tiêu chí và bằng 0 hoặc 1 (nghiên cứu gốc gọi 0–1 là thấp, 8–9 là cao).

## Điểm M (Beneish 1999): mô hình tám biến

M = −4,84 + 0,920 × DSRI + 0,528 × GMI + 0,404 × AQI + 0,892 × SGI + 0,115 × DEPI − 0,172 × SGAI + 4,679 × TATA − 0,327 × LVGI

Định nghĩa theo bảng 2 của nghiên cứu gốc; năm t so với năm t − 1.

| Tỷ số | Cách tính |
|---|---|
| DSRI | (phải thu ngắn hạn của khách hàng chia doanh thu thuần) năm t, chia cùng tỷ số năm t − 1. Phải thu lấy số thuần sau dự phòng khi thuyết minh tách được dự phòng của phải thu khách hàng; không tách được thì lấy số trước dự phòng cho cả hai năm |
| GMI | biên lợi nhuận gộp năm t − 1 chia biên lợi nhuận gộp năm t |
| AQI | (1 − (tài sản ngắn hạn + tài sản cố định hữu hình theo giá trị còn lại) chia tổng tài sản) năm t, chia cùng đại lượng năm t − 1 |
| SGI | doanh thu thuần năm t chia doanh thu thuần năm t − 1 |
| DEPI | (khấu hao chia (khấu hao + tài sản cố định hữu hình theo giá trị còn lại)) năm t − 1, chia cùng tỷ số năm t. Khấu hao là khấu hao trích trong năm của tài sản cố định hữu hình, lấy ở thuyết minh tài sản cố định hữu hình, không lấy dòng khấu hao gộp của báo cáo lưu chuyển tiền tệ |
| SGAI | ((chi phí bán hàng + chi phí quản lý doanh nghiệp) chia doanh thu thuần) năm t, chia cùng tỷ số năm t − 1 |
| LVGI | ((nợ ngắn hạn + vay và nợ thuê tài chính dài hạn) chia tổng tài sản) năm t, chia cùng tỷ số năm t − 1 |
| TATA | (Δ tài sản ngắn hạn − Δ tiền và các khoản tương đương tiền − Δ nợ ngắn hạn + Δ phần vay dài hạn đến hạn trả + Δ thuế thu nhập doanh nghiệp phải nộp − khấu hao và phân bổ năm t) chia tổng tài sản cuối năm t. Δ là số cuối năm t trừ số cuối năm t − 1. Phần vay dài hạn đến hạn trả lấy ở thuyết minh vay; thuế thu nhập doanh nghiệp phải nộp lấy ở thuyết minh thuế và các khoản phải nộp Nhà nước; khấu hao và phân bổ lấy ở báo cáo lưu chuyển tiền tệ |

Cờ: M lớn hơn −1,78. Đây là ngưỡng nghiên cứu gốc chọn theo một giả định về chi phí của hai loại phân loại sai, không phải ngưỡng đúng cho mọi thị trường.

## Điểm Z (Altman, bản bốn biến cho doanh nghiệp không sản xuất)

Z = 6,56 × X1 + 3,26 × X2 + 6,72 × X3 + 1,05 × X4, tính trên số cuối năm t (X3 dùng số của năm t).

| Biến | Cách tính |
|---|---|
| X1 | (tài sản ngắn hạn − nợ ngắn hạn) chia tổng tài sản |
| X2 | lợi nhuận sau thuế chưa phân phối lũy kế cuối năm chia tổng tài sản |
| X3 | (tổng lợi nhuận kế toán trước thuế + chi phí lãi vay) chia tổng tài sản |
| X4 | vốn chủ sở hữu chia nợ phải trả |

Bản này dùng vốn chủ sở hữu theo sổ sách, không dùng vốn hóa thị trường, nên không cần giá cổ phiếu; không cộng hằng số 3,25 của bản cho thị trường mới nổi. Cờ: Z nhỏ hơn 1,1 (vùng nguy hiểm); từ 1,1 tới 2,6 là vùng xám.

## Nguồn

- Piotroski, J. D. (2000). Value Investing: The Use of Historical Financial Statement Information to Separate Winners from Losers. Journal of Accounting Research 38. Mẫu nghiên cứu là doanh nghiệp Mỹ có tỷ lệ giá trị sổ sách trên giá thị trường cao; hồ sơ chỉ dùng phần tính kế toán, không kế thừa kết luận về lợi suất.
- Beneish, M. D. (1999). The Detection of Earnings Manipulation. Financial Analysts Journal 55(5). Bảng 2: định nghĩa các biến; bảng 3: hệ số.
- Altman, E. I. (2002). Revisiting Credit Scoring Models in a Basel 2 Environment, mục 8: mô hình Z bốn biến dùng vốn chủ sở hữu theo sổ sách và ngưỡng 1,1. Altman, E. I., Hartzell, J., Peck, M. (1995). Emerging Market Corporate Bonds: A Scoring System: bản cho thị trường mới nổi, hồ sơ không dùng.
