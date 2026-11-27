# ADR-0023: Bảng phơi nhiễm thời thế ở Mục 9 của hồ sơ mã

- Ngày: 2026-11-27
- Trạng thái: ACCEPTED 27/11/2026 theo lệnh Owner, hiệu lực khi Owner gộp PR này.
- Người đề xuất: Claude Project TTC (Anthropic), ghế kiến trúc sư trưởng. Chép vào kho: phiên Claude Code (Anthropic).
- Người chấm: theo L-09, ghi trong thân PR.
- Owner duyệt: lệnh trong chat Project ngày 27/11/2026, 16:47 giờ Việt Nam, «Bạn tự quyết công việc. Tôi chỉ nghiệm thu.»; xác nhận bằng việc gộp PR này.

## Bối cảnh

- Ngày 27/11/2026 Owner giao kiến trúc sư hỏi ba ghế khác hãng (Gemini, ChatGPT, Grok) một ý kiến trúc giúp nhìn «thời thế» khi phân tích một mã. Ba ghế, làm độc lập, cùng đề xuất một ý: đo mức doanh nghiệp phơi ra trước các biến bên ngoài, không đoán các biến đó đi hướng nào; cùng bác «điểm số thời thế».
- Mục 9 «Thị trường chung và chu kỳ» của khung hồ sơ chưa có cấu trúc. Hồ sơ HPG bản 2 (đã niêm phong 26/11/2026) có ba câu ở Mục 9 và ghi thiếu số liệu ngành ở danh sách CHƯA BIẾT.
- Ý này được làm tay trước trên HPG, theo tiền lệ của ADR-0019 QĐ-P14: một bản thử và hai bản sửa, ba vòng phản biện khác hãng, mỗi bản có phiếu máy ĐẠT trên `tools/hoso` tại `7197c80`. Tệp nằm trên máy Owner và trong Project, không vào kho (L-03, ADR-0019 QĐ-P13).

## Quyết định

### QĐ-T1 — Mục 9 viết thành bảng phơi nhiễm thời thế

Từ hồ sơ mã đầu tiên làm sau khi PR này gộp, Mục 9 gồm:

1. Một đoạn ngắn nêu những lý do doanh nghiệp tự nêu trong báo cáo, có nhãn ĐÃ KIỂM.
2. Mỗi biến thời thế một tiêu đề phụ `###`, dưới đó bốn thứ theo thứ tự: trạng thái ở ngày ghi, lấy từ một tệp ngoài đã ghim (mã N); mức phơi nhiễm của doanh nghiệp, lấy từ tệp gốc của chính doanh nghiệp; giả thuyết nào ở Mục 11 dựa vào biến, qua dòng nào của báo cáo (doanh thu, giá vốn, chi phí tài chính, dòng tiền); điều kiện làm trạng thái đã ghi đổi.
3. Một bảng tóm tắt năm cột: biến; trạng thái đã ghim (mã N); phơi nhiễm từ tệp gốc (mã D); giả thuyết dựa vào; chấm được ở ngày xem lại hay không.
4. Một đoạn cuối nói cách chấm ở ngày xem lại (QĐ-T6).

Mục 11 thêm một dòng «Biến thời thế» nêu mỗi giả thuyết dựa vào những biến nào.

### QĐ-T2 — Phơi nhiễm là quy mô, không phải độ nhạy

- Mức phơi nhiễm là quy mô của phần hoạt động gắn với biến (tỷ trọng sản lượng, tỷ trọng chi phí, số dư nợ vay theo đồng tiền, tỷ trọng doanh thu xuất khẩu), lấy từ báo cáo của doanh nghiệp. Hồ sơ ghi rõ điều đó, và ghi độ nhạy của lợi nhuận với từng biến là CHƯA BIẾT khi chưa đo được.
- Không viết câu tác động có điều kiện («nếu tỷ giá tăng 5% thì chi phí tài chính tăng …»). Máy không bắt loại câu này; cách viết và ghế phản biện giữ.
- Được một phép thử cơ học cho mỗi biến, với cú sốc đúng một đơn vị (một điểm phần trăm, một phần trăm), là dòng tính trong sổ, nhãn SUY LUẬN có khóa, kèm một câu GIẢ ĐỊNH ghi rõ giả định của phép thử và rằng đó không phải mức lợi nhuận sẽ đổi.

### QĐ-T3 — Điều kiện đổi trạng thái chấm được

- Mỗi điều kiện ghi rõ bốn thứ: văn bản hay bản tin nào dùng để chấm; chỉ tiêu nào; so với kỳ nào; ngưỡng nào thì gọi là đổi. Thiếu một trong bốn thì dòng ghi «chưa chấm được», không suy ra trạng thái.
- Trạng thái đã ghi viết thành một quan hệ («bình quân quý gần nhất thấp hơn cùng kỳ năm trước»); điều kiện đổi là quan hệ đó không còn đúng. Biến là một khoảng thì xét cả hai đầu mút và cả hai chiều.
- Biến là sự kiện pháp lý thì chỉ văn bản có hiệu lực làm đổi trạng thái (một quyết định, không phải một kết luận hay kiến nghị); ghi rõ khi nào trạng thái giữ nguyên.
- Một dòng có nhiều chỉ tiêu thì mỗi chỉ tiêu chấm riêng, và ghi luật gộp («ít nhất một chỉ tiêu đổi thì dòng ghi là đổi, kèm tên chỉ tiêu»).
- Ngưỡng là lựa chọn của ghế phân tích: viết dưới nhãn GIẢ ĐỊNH, bằng chữ («nửa điểm phần trăm»).
- Không câu nào nêu hay ngụ ý biến sẽ đi hướng nào. Không cộng các dòng thành điểm. Không từ hành động.

### QĐ-T4 — Chọn biến

- Không giới hạn cứng số dòng. Quá tám dòng thì ghi một câu lý do ở đầu Mục 9.
- Giả thuyết dựa vào biên lợi nhuận thì bảng có cả biến phía chi phí lẫn biến phía doanh thu; thiếu nguồn cho phía nào thì vẫn lập dòng, ô trạng thái ghi «Chưa», dòng ghi «chưa chấm được».
- Biến không nối được vào một dòng của báo cáo doanh nghiệp thì không lập dòng; nếu quan trọng thì ghi vào danh sách CHƯA BIẾT.
- Nguồn ngành có thể chứa số của chính doanh nghiệp (số do hội viên báo) thì ghi rõ «không độc lập với» doanh nghiệp, ở câu và ở bảng tóm tắt.

### QĐ-T5 — Tệp ngoài (B2)

- Tệp ngoài mang mã N, đặt trong `goc/ngoai/` của thư mục mã, nhận bằng `nhan_tep.py` như tệp gốc khác.
- Chỉ dùng bản gốc của cơ quan ban hành, cơ quan thống kê, ngân hàng trung ương, tổ chức quốc tế hay hiệp hội ngành. Trang web không có tệp thì in thành PDF, giờ in hiện ở đầu trang. Trang viết lại tin của nơi khác và báo cáo của công ty chứng khoán không dùng làm nguồn ghim.

### QĐ-T6 — Hậu kiểm (B8 bước 5)

- Ở ngày xem lại, mỗi dòng chấm theo văn bản và kỳ mà điều kiện riêng của nó nêu, và ghi một trong bốn: ĐỔI, ĐỔI MỘT PHẦN, GIỮ NGUYÊN, CHƯA CHẤM ĐƯỢC, kèm bằng chứng có nhãn.
- Với mỗi giả thuyết: ghi các dòng đã đổi; ghi nguyên nhân giả thuyết đứng hay gãy là TRONG BẢNG, NGOÀI BẢNG hay CHƯA RÕ. Một biến đổi cùng lúc với giả thuyết gãy chưa phải nguyên nhân. Báo cáo của doanh nghiệp tự nêu nguyên nhân thì ghi «nguyên nhân do doanh nghiệp nêu», kèm mã tệp và trang; còn lại ghi «chưa rõ nguyên nhân».
- Báo cáo của doanh nghiệp quy thay đổi của lợi nhuận cho một yếu tố bên ngoài không có dòng trong bảng, cũng không có trong danh sách CHƯA BIẾT: ghi một lần «không báo» kèm tên yếu tố.

### QĐ-T7 — Không sửa máy

- `tools/hoso/` không đổi; không thêm phép kiểm. Máy không đọc được nghĩa của điều kiện đổi trạng thái. Phần đó do ghế phản biện ở B7 kiểm: mẫu lệnh phản biện thêm một câu hỏi bắt buộc về Mục 9.
- Những gì máy đã kiểm vẫn áp cho Mục 9: số ĐÃ KIỂM phải có trên trang; số SUY LUẬN gắn khóa; cổng giá. Tiêu đề phụ, bảng nguồn và danh sách CHƯA BIẾT không có chữ «giá» kèm số; số giá hàng hóa chỉ đứng trong đoạn ĐÃ KIỂM.

### QĐ-T8 — Hồ sơ đã giao

- Không làm lại hồ sơ đã giao (ADR-0021 QĐ-K5). Hồ sơ HPG bản 2 hậu kiểm theo chính chữ của nó. Bảng ở bản thử HPG sửa vòng 2 (niêm phong 27/11/2026) hậu kiểm riêng ở ba ngày xem lại của bản thử, chỉ để quyết giữ, sửa hay gỡ ADR này.

## Trạng thái từng quyết định

| QĐ | Trạng thái | Owner | Ngày |
|---|---|---|---|
| QĐ-T1 tới QĐ-T8 | ACCEPTED theo lệnh Owner giao kiến trúc sư tự quyết công việc | Owner (lệnh 16:47 ngày 27/11/2026) | 27/11/2026 |

## Lý do (bằng chứng, số đo)

Làm ngày 27/11/2026, ngoài kho, trên HPG:

- Mười chín tệp ngoài tải về máy Owner (Bộ Công Thương, Cục Phòng vệ thương mại, Ngân hàng Thế giới, Ngân hàng Nhà nước, Cục Thống kê, Hiệp hội Thép Việt Nam), sha256 ghi vào Project; mười hai tệp vào bảng nguồn (N1 tới N12).
- Ba bản: bản thử (sáu biến), sửa vòng 1 (tám biến), sửa vòng 2. Cả ba có phiếu máy ĐẠT trên `7197c80`; không sửa `tools/hoso/`.
- Đối chiếu số khác hãng (Grok, hai vòng): 34 dòng; 32 KHỚP, 2 LỆCH, cả hai là lỗi gài; bốn khóa của Mục 9 trong bảng định nghĩa KHỚP NGHĨA. Phản biện khác hãng (ChatGPT, ba vòng): vòng 1 nêu 35 điểm; vòng 2 xác nhận 24 điểm đã xử lý, 6 một phần, 5 không sửa với lý do chấp nhận được, và nêu 6 lỗi chặn; vòng 3 xác nhận 9 trên 9 điểm đã xử lý, đối chiếu 43 số (42 KHỚP, 1 LỆCH là lỗi gài), lỗi chặn duy nhất là lỗi gài. Mỗi vòng, mỗi ghế bắt được lỗi gài.
- Điều kiện «khả thi» đặt trước khi thử (ba điều): ít nhất một dòng đủ năm ô từ tệp đã ghim — có bốn dòng (thuế phòng vệ thương mại, quặng sắt, lãi suất cho vay, cung cầu thép); phiếu máy ĐẠT — có; phản biện không nêu lỗi chặn — vòng cuối chỉ còn lỗi gài.
- Điều bản thử dạy, đã đưa vào QĐ: bảng đầu lẫn quy mô với độ nhạy (QĐ-T2); điều kiện «nằm ngoài khoảng» có ba cách hiểu, điều kiện một chiều, điều kiện trộn kết luận rà soát với quyết định (QĐ-T3); bảng chỉ có biến chi phí trong khi giả thuyết dựa vào biên lợi nhuận (QĐ-T4); nguồn ngành chứa số của doanh nghiệp (QĐ-T4); một điều kiện sai ở Mục 11 cần báo cáo quý sau ngày xem lại cuối (B8).
- Hai điều về máy gặp trong lúc làm. `gai_loi.py` từ chối ba số gài vì phép đối chiếu không báo chúng; ít nhất một ca là do trang đã ghi có một số khác bằng số gài sau làm tròn (3,6 và 3,55), thuộc loại «con số có trên trang nhưng lấy nhầm ô» ở mục 4 của quy trình. Cổng giá xét cả mục «Trạng thái kiểm»: một câu tóm tắt câu hỏi bắt buộc của B7 có chữ «giá» đi với chữ «tương lai» làm phiếu CHƯA ĐẠT, và ghế phân tích viết lại câu đó.

Điểm yếu đã biết:

- Một mã đã thử. Chưa có hậu kiểm nào: chưa biết bảng có giải thích được giả thuyết đứng hay gãy không.
- Bốn trên tám dòng của HPG chưa chấm được vì thiếu nguồn miễn phí ghim được (than luyện cốc, tỷ giá, doanh thu trên mỗi tấn, văn bản của nước nhập khẩu).
- Ghế phản biện không mở được ba tệp lớn của HPG; các số dựa riêng vào chúng chỉ một ghế đối chiếu.
- Ghế soạn ADR, ghế viết hồ sơ thử và ghế chép vào kho cùng hãng (QĐ-K6 của ADR-0021).

## Không đổi

- L-01…L-10 và `governance/LAWS.md` không sửa. PR này không chạm `governance/`, `ledger/`, `paper/`, `research/`, `engine/`, `data/`, `tools/`, `tests/`.
- `autonomous_order_execution: false` và `live_trading_enabled: false` giữ nguyên. Không mở API trả phí.
- Chữ của ADR-0019 tới ADR-0022 không sửa. Khung mười hai mục, tên các mục và hồ sơ mẫu `templates/hoso/vi_du/` giữ nguyên.

## Điều kiện hoàn tác

1. Sau hậu kiểm của bản thử HPG ở ba ngày xem lại (báo cáo quý IV/2026, báo cáo năm 2026 đã kiểm toán, báo cáo quý I/2027) và hai hồ sơ mã làm theo ADR này: nếu ở cả hai hồ sơ quá nửa số dòng là «chưa chấm được», hoặc qua ít nhất ba lần chấm giả thuyết mà không lần nào nguyên nhân ở TRONG BẢNG, kiến trúc sư báo Owner trong 7 ngày. Owner chọn bằng một ADR mới: giữ, sửa hay gỡ.
2. Một ghế khác hãng hay hậu kiểm tìm thấy một dòng của bảng viết thành dự báo hướng, thành điểm số, hay kèm lời hành động: dừng dùng bảng ở hồ sơ kế tiếp và báo Owner ngay.
3. Hoàn tác không cần khôi phục gì: gỡ bằng một PR đảo các thay đổi chữ của PR này. Hồ sơ làm trong thời gian ADR có hiệu lực giữ nguyên Mục 9 của chúng.

## Ảnh hưởng tới ARCHITECTURE.md

- Dòng trạng thái đầu tệp: thêm ADR-0023.
- Thêm một đoạn ngắn sau đoạn «Từ ADR-0022», trỏ tới ADR này.
- Chữ của §0–§10 giữ nguyên.
