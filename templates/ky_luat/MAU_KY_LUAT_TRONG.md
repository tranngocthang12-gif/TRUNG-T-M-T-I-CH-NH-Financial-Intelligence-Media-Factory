# Bộ mẫu kỷ luật (trống): bản quy tắc riêng, phiếu trước quyết định, nhật ký

- Theo ADR-0019 QĐ-P8. Đây là mẫu trống. Owner tự điền. Dự án không chọn con số nào thay Owner.
- Bản đã điền giữ ở nơi riêng tư do Owner chọn. Không đưa bản đã điền vào kho công khai (L-03).
- Ghi bằng tỷ lệ phần trăm. Không ghi số tiền.
- Không phải lời khuyên đầu tư.

---

## Mẫu 1. Bản quy tắc riêng (mười dòng)

Điền một lần. Muốn sửa thì sửa lúc không có lệnh nào đang chờ, ghi ngày sửa và lý do.

| # | Quy tắc | Owner điền |
|---|---|---|
| 1 | Trường phái chính (giá trị–dài hạn, hoặc tăng trưởng–xu hướng) | |
| 2 | Số mã tối đa giữ cùng lúc | |
| 3 | Tỷ trọng tối đa cho một mã (% danh mục) | |
| 4 | Tỷ trọng tối đa cho một ngành (% danh mục) | |
| 5 | Tỷ lệ tiền mặt tối thiểu (% danh mục) | |
| 6 | Đòn bẩy: có dùng không; nếu có, tối đa bao nhiêu % | |
| 7a | Mức lỗ tối đa cho một vị thế mang nhãn "giá trị–dài hạn" (%) | |
| 7b | Mức lỗ tối đa cho một vị thế mang nhãn "tăng trưởng–xu hướng" (%) | |
| 8 | Cả danh mục sụt bao nhiêu % từ đỉnh thì ngừng mua mới | |
| 9 | Số lệnh mua mới tối đa mỗi tháng | |
| 10 | Thời gian chờ từ lúc đọc xong hồ sơ tới lúc đặt lệnh (số ngày) | |

Ngày lập: ……  Ngày sửa gần nhất: ……  Lý do sửa: ……

**Hai nhãn vị thế.** Ghi nhãn lúc mua. Không đổi nhãn sau khi mua.

| Nhãn | Thoát khi |
|---|---|
| Giá trị–dài hạn | Điều kiện sai của luận điểm xảy ra, hoặc giá vượt khoảng giá trị trong hồ sơ |
| Tăng trưởng–xu hướng | Chạm mức lỗ ở dòng 7b, hoặc quy tắc xu hướng Owner đã viết bị phá |

---

## Mẫu 2. Phiếu trước quyết định (mười một câu)

Điền mỗi lần định mua mới hoặc mua thêm. Một câu trả lời "chưa" hoặc "vượt" thì dừng, không đặt lệnh hôm đó.

Ngày: ……  Mã: ……  Nhãn vị thế: ……

| # | Câu hỏi | Trả lời |
|---|---|---|
| 1 | Tôi đã đọc hết hồ sơ và bản phản biện chưa? | |
| 2 | Tôi nói được luận điểm trong ba câu không? Ghi ba câu đó | |
| 3 | Điều gì xảy ra thì tôi sai? Tôi biết bằng cách nào, khi nào? | |
| 4 | Vị thế này mang nhãn nào? | |
| 5 | Nếu sai, phần mất có nằm trong giới hạn ở dòng 7a hoặc 7b không? | |
| 6 | Sau lệnh, tỷ trọng mã và ngành có vượt dòng 3 và dòng 4 không? | |
| 7 | Mã có đủ thanh khoản để thoát trong vài phiên không? | |
| 8 | Lệnh này có dùng tiền vay không? Có vượt dòng 6 không? | |
| 9 | Điều gì khiến tôi muốn làm hôm nay: hồ sơ, hay giá vừa tăng và tin vừa nghe? | |
| 10 | Tôi đã chờ đủ thời gian ở dòng 10 chưa? | |
| 11 | Từ ngày giao hồ sơ, điều kiện sai nào ở Mục 11 hay điều kiện đổi trạng thái nào ở Mục 9 đã chạm? Tôi đã đọc hậu kiểm của điều kiện đó chưa? Ghi một trong năm: KHÔNG CÓ ĐIỀU KIỆN NÀO CHẠM; ĐÃ CHẠM, ĐÃ ĐỌC HẬU KIỂM; ĐÃ CHẠM, CÓ HẬU KIỂM NHƯNG CHƯA ĐỌC; ĐÃ CHẠM, CHƯA CÓ HẬU KIỂM; CHƯA ĐỦ BẰNG CHỨNG. Ba câu sau tính là «chưa». Nhiều điều kiện thì ghi trạng thái kém nhất. Không biết thì không ghi KHÔNG CÓ ĐIỀU KIỆN NÀO CHẠM (ADR-0024 QĐ-N4) | |

Kết quả phiếu: ĐƯỢC ĐI TIẾP / DỪNG. Câu làm dừng (nếu có): ……

---

## Mẫu 3. Nhật ký và xem lại mỗi quý

**Nhật ký.** Mỗi quyết định một dòng, kể cả quyết định không làm.

| Ngày | Mã | Việc (mua, bán, không làm) | Nhãn | Luận điểm (một câu) | Điều kiện sai | Ngày xem lại | Kết quả phiếu |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

**Xem lại mỗi quý.** Chấm hai thứ riêng nhau. Lệnh lãi mà làm sai quy tắc vẫn là lỗi.

| Mã | Luận điểm: ĐÚNG, SAI hay CHƯA RÕ | Có làm đúng bản quy tắc và phiếu không | Bài học (một câu) |
|---|---|---|---|
| | | | |

Bài học đáng giữ thì chuyển thành một ca trong thư viện của dự án, không kèm số tiền.
