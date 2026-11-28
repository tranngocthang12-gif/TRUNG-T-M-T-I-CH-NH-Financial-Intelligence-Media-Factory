# Giải thích bộ mẫu kỷ luật bằng lời thường

- Theo ADR-0026 QĐ-B6. Đọc cùng `templates/ky_luat/MAU_KY_LUAT_TRONG.md`.
- Tệp này chỉ nói mỗi dòng hỏi gì và vì sao phải trả lời trước. Nó không gợi ý con số nào và không chọn thay Owner.
- Tệp này không thêm và không đổi quy tắc nào của mẫu. Chỗ nào tệp này khác mẫu trống hay khác ADR-0019 QĐ-P8 thì mẫu trống và ADR có hiệu lực.
- Đây là nguyên tắc chung, không phải lời khuyên đầu tư. Dự án không hỏi và không ghi câu trả lời của Owner (L-03).

## Vì sao viết trước

Bản quy tắc được viết lúc không có lệnh nào đang chờ. Lúc đó người viết không bị giá vừa tăng, tin vừa nghe hay khoản lỗ đang treo kéo đi. Phiếu trước quyết định dùng để đối chiếu một lệnh sắp đặt với điều đã viết lúc bình tĩnh. Nhật ký dùng để về sau tách hai chuyện: luận điểm đúng hay sai, và có làm đúng quy tắc không.

## Mẫu 1. Bản quy tắc riêng

| Dòng | Dòng này hỏi gì | Vì sao phải trả lời trước |
|---|---|---|
| 1. Trường phái chính | Owner mua một cổ phiếu vì lý do loại nào: giá trị dài hạn, hay tăng trưởng theo xu hướng | Hai loại có nguyên tắc thoát khác nhau. Không chọn trước thì dễ đổi lý do sau khi mua để khỏi phải thoát |
| 2. Số mã tối đa | Cùng lúc giữ nhiều nhất bao nhiêu mã | Mỗi mã cần thời gian đọc và theo dõi. Con số này nói Owner theo dõi nổi bao nhiêu |
| 3. Tỷ trọng tối đa một mã | Một mã được chiếm nhiều nhất bao nhiêu phần danh mục | Giới hạn mức tập trung của danh mục vào một mã. Tỷ trọng không bảo đảm phần mất thực tế nằm trong một giới hạn ở mọi tình huống |
| 4. Tỷ trọng tối đa một ngành | Một ngành được chiếm nhiều nhất bao nhiêu phần danh mục | Giới hạn mức tập trung vào một ngành. Các mã cùng ngành thường cùng chịu một biến bên ngoài |
| 5. Tiền mặt tối thiểu | Luôn giữ lại ít nhất bao nhiêu phần là tiền | Để không phải bán vội khi cần tiền hay khi có việc bất ngờ |
| 6. Đòn bẩy | Có dùng tiền vay không, và tới mức nào | Tiền vay làm cả lãi lẫn lỗ lớn hơn, và có thể buộc phải bán |
| 7a, 7b. Mức lỗ tối đa một vị thế | Với mỗi nhãn, Owner tự đặt phần mất nhiều nhất chấp nhận cho một vị thế | Giới hạn này được đối chiếu ở câu 5 của phiếu, trước khi đặt lệnh. Khi nào thoát thì theo bảng «Hai nhãn vị thế» của mẫu, không theo dòng giải thích này |
| 8. Mức sụt của cả danh mục | Danh mục giảm bao nhiêu từ đỉnh thì ngừng mua mới | Một khoảng nghỉ định trước, để xem lại trước khi làm thêm |
| 9. Số lệnh mua mới mỗi tháng | Mỗi tháng mua mới nhiều nhất mấy lần | Giao dịch nhiều thì tốn phí và dễ làm theo cảm xúc |
| 10. Thời gian chờ | Từ lúc đọc xong hồ sơ tới lúc đặt lệnh cách bao lâu | Khoảng chờ để cái hứng lúc đọc xong lắng xuống |

**Hai nhãn vị thế.** Nhãn ghi lúc mua và không đổi sau đó. Lý do: đổi nhãn sau khi mua là một cách để giữ lại một vị thế lẽ ra đã phải thoát.

Cột «Thoát khi» của bảng hai nhãn ghi nguyên tắc rời vị thế của từng nhãn, đã định ở ADR-0019 QĐ-P8. Hai nhãn có hai nguyên tắc khác nhau:

- Nhãn giá trị–dài hạn: rời theo luận điểm, tức khi điều kiện sai của luận điểm xảy ra; hoặc theo khoảng giá trị do Owner tự lập và tự ghi ở chỗ riêng. Hồ sơ mã không có khoảng giá trị, và dự án không lập khoảng đó thay Owner. Dòng 7a không phải điều kiện thoát của nhãn này trong bảng; nó là giới hạn được đối chiếu ở câu 5.
- Nhãn tăng trưởng–xu hướng: rời khi chạm mức lỗ ở dòng 7b, hoặc khi quy tắc xu hướng Owner đã viết bị phá. Dự án không viết quy tắc xu hướng thay Owner.

## Mẫu 2. Phiếu trước quyết định

| Câu | Câu này kiểm điều gì |
|---|---|
| 1 | Đã đọc cả hồ sơ lẫn bản phản biện, không chỉ phần mình thích |
| 2 | Nói lại được luận điểm bằng lời của mình. Không nói được thì chưa hiểu đủ |
| 3 | Biết điều gì làm mình sai, và biết sẽ thấy điều đó ở đâu, khi nào |
| 4 | Nhãn được chọn trước khi mua |
| 5 | Phần có thể mất nằm trong giới hạn đã viết ở dòng 7a hay 7b |
| 6 | Sau lệnh, tỷ trọng mã và ngành không vượt dòng 3 và dòng 4 |
| 7 | Mã có đủ thanh khoản để thoát khi cần |
| 8 | Có dùng tiền vay không, và có vượt dòng 6 không |
| 9 | Điều thúc mình làm hôm nay là hồ sơ, hay là giá vừa tăng và tin vừa nghe |
| 10 | Đã chờ đủ thời gian ở dòng 10 |
| 11 | Từ ngày giao hồ sơ tới hôm nay, điều kiện nào hồ sơ đã ghi (điều kiện sai ở Mục 11, điều kiện đổi trạng thái ở Mục 9) đã chạm, và đã đọc hậu kiểm của điều kiện đó chưa. Trả lời bằng đúng một trong năm câu chuẩn giải thích ở dưới |

Một câu trả lời «chưa» hoặc «vượt» thì dừng trong ngày đó. Phiếu không nói lệnh đúng hay sai; nó chỉ nói lệnh có khớp điều Owner đã tự viết hay không.

**Năm câu trả lời chuẩn của câu 11 (ADR-0024 QĐ-N4 điểm 1).**

| Câu trả lời | Nghĩa | Tính là |
|---|---|---|
| KHÔNG CÓ ĐIỀU KIỆN NÀO CHẠM | Owner đã xem và biết chắc chưa điều kiện nào chạm | Không dừng vì câu này |
| ĐÃ CHẠM, ĐÃ ĐỌC HẬU KIỂM | Có điều kiện đã chạm, và Owner đã đọc hậu kiểm của nó | Không dừng vì câu này |
| ĐÃ CHẠM, CÓ HẬU KIỂM NHƯNG CHƯA ĐỌC | Có điều kiện đã chạm, đã có hậu kiểm, Owner chưa đọc | «chưa»: dừng |
| ĐÃ CHẠM, CHƯA CÓ HẬU KIỂM | Có điều kiện đã chạm, chưa có hậu kiểm | «chưa»: dừng |
| CHƯA ĐỦ BẰNG CHỨNG | Chưa biết có điều kiện nào chạm hay không | «chưa»: dừng |

- Nhiều điều kiện có trạng thái khác nhau thì ghi trạng thái kém nhất, theo thứ tự từ kém tới tốt: CHƯA ĐỦ BẰNG CHỨNG; CHƯA CÓ HẬU KIỂM; CÓ HẬU KIỂM NHƯNG CHƯA ĐỌC; ĐÃ ĐỌC HẬU KIỂM; KHÔNG CÓ ĐIỀU KIỆN NÀO CHẠM.
- Không biết thì không ghi KHÔNG CÓ ĐIỀU KIỆN NÀO CHẠM. Không biết là CHƯA ĐỦ BẰNG CHỨNG.
- Hai câu trả lời đầu chỉ có nghĩa là câu 11 không làm dừng. Chúng không nói lệnh nên hay không nên đặt; mười câu còn lại vẫn phải qua.

## Mẫu 3. Nhật ký và xem lại mỗi quý

- Mỗi quyết định một dòng, kể cả quyết định không làm. Quyết định không làm cũng có thể đúng hay sai.
- Mỗi quý chấm hai thứ riêng nhau: luận điểm đúng hay sai; có làm đúng bản quy tắc và phiếu không. Một lệnh lãi mà làm sai quy tắc vẫn là lỗi, vì lần sau cách làm đó có thể cho kết quả ngược lại.

Các cột của nhật ký:

| Cột | Ghi gì | Để làm gì |
|---|---|---|
| Ngày, Mã | Ngày quyết định và mã | Để tìm lại đúng hồ sơ và đúng bản đã đọc |
| Việc | Mua, bán hay không làm | Để quyết định không làm cũng được xem lại |
| Nhãn | Nhãn vị thế đã chọn lúc mua | Để về sau biết nguyên tắc thoát nào áp cho vị thế này |
| Luận điểm (một câu) | Lý do của quyết định, bằng lời của Owner | Để chấm luận điểm đúng hay sai mà không viết lại lý do sau khi biết kết quả |
| Điều kiện sai | Điều gì xảy ra thì luận điểm sai | Để có thứ đối chiếu ở ngày xem lại |
| Ngày xem lại | Ngày sẽ mở lại dòng này | Để việc xem lại không phụ thuộc vào giá lúc đó |
| Kết quả phiếu | ĐƯỢC ĐI TIẾP hay DỪNG, và câu làm dừng | Để mỗi quý đếm được số quyết định có phiếu và số lần làm trái quy tắc |

Cột của bảng «Xem lại mỗi quý» theo đúng mẫu trống: luận điểm ĐÚNG, SAI hay CHƯA RÕ; có làm đúng bản quy tắc và phiếu không; bài học một câu. Không ghi số tiền.
