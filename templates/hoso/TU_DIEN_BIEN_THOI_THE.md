# Từ điển biến thời thế (ADR-0024 QĐ-N2)

- Mục 9 của mọi hồ sơ mã (ADR-0023) dùng đúng chữ ở cột «Tên biến» làm tiêu đề phụ `###` và ở bảng tóm tắt, để bảng của nhiều mã gom được thành một bản đồ. Mã biến dùng ở bản đồ, không viết vào hồ sơ.
- Mã biến cố định: không đổi, không dùng lại. Biến chưa có ở đây: thêm một dòng với mã kế tiếp bằng PR chữ, trước hoặc cùng lúc với hồ sơ đầu tiên dùng nó. Không đổi tên một dòng đã có; muốn đổi thì thêm dòng mới và ghi ở dòng cũ «thay bởi <mã biến>».
- Cột «Tên cũ» ghi tên khác đã dùng cho cùng biến ở hồ sơ trước từ điển, để gom bản đồ ánh xạ về một mã.
- Tên biến không có chữ «giá» (B5 của `docs/QUY_TRINH_HO_SO_MA.md`).
- Từ điển chỉ ghi tên và cách chấm thường dùng. Từ điển không ghi mã chứng khoán nào đã dùng biến: việc đó ở bản đồ, trong Project. Trạng thái, phơi nhiễm và điều kiện của từng mã ghi trong hồ sơ của mã đó. Cùng một biến không có nghĩa là cùng mức tác động ở hai doanh nghiệp.

| Mã biến | Tên biến | Tên cũ | Loại nguồn trạng thái đã dùng | Chỉ tiêu và kỳ thường chấm | Ghi chú |
|---|---|---|---|---|---|
| BT01 | Dầu Brent | | Ngân hàng Thế giới, The Pink Sheet | Bình quân quý, so với cùng quý năm trước | |
| BT02 | LNG nhập khẩu | | Ngân hàng Thế giới, The Pink Sheet (LNG nhập vào Nhật Bản) | Bình quân quý, so với cùng quý năm trước | Không phải mức doanh nghiệp mua vào |
| BT03 | LPG theo hợp đồng của Saudi Aramco | | Chưa ghim được nguồn | Chưa có | |
| BT04 | Huy động điện từ tua bin khí | | EVN, bản tin kết quả tháng | Tỷ trọng in sẵn trong bản tin lũy kế | Dùng tỷ trọng EVN in, không tự chia lại |
| BT05 | Cơ chế sản lượng điện hợp đồng cho điện khí LNG | | Văn bản quy phạm có hiệu lực; tin của Bộ Công Thương | Mức tối thiểu và thời gian áp dụng | Chỉ văn bản có hiệu lực làm đổi |
| BT06 | Nguồn khí khai thác trong nước | | Chưa ghim được nguồn độc lập | Chưa có | Tài liệu của công ty mẹ không độc lập |
| BT07 | Đồng đô la Mỹ so với đồng Việt Nam | Tỷ giá | Chưa ghim văn bản của Ngân hàng Nhà nước | Chưa có | |
| BT08 | Thuế phòng vệ thương mại với thép cán nóng nhập từ Trung Quốc | | Quyết định của Bộ Công Thương | Mức thuế, phạm vi hàng, thời hạn | |
| BT09 | Quặng sắt | | Ngân hàng Thế giới, The Pink Sheet | Bình quân quý, so với cùng quý năm trước | Hàng nhập vào Trung Quốc |
| BT10 | Than luyện cốc | | Chưa ghim được nguồn miễn phí | Chưa có | |
| BT11 | Lãi suất cho vay | | Ngân hàng Nhà nước, bản tin lãi suất tháng | Đầu mút của khoảng lãi suất VND và USD | Mặt bằng chung, không phải lãi suất doanh nghiệp vay |
| BT12 | Cung cầu thép trong nước và thép nhập khẩu | | Hiệp hội Thép Việt Nam; Cục Thống kê | Lũy kế so với cùng kỳ của từng chỉ tiêu | Số của Hiệp hội không độc lập với doanh nghiệp thành viên |
| BT13 | Doanh thu trên mỗi tấn thép | | Chưa ghim được nguồn | Chưa có | |
| BT14 | Thị trường xuất khẩu thép | | Văn bản phòng vệ của nước nhập khẩu (chưa ghim) | Chưa có | |
