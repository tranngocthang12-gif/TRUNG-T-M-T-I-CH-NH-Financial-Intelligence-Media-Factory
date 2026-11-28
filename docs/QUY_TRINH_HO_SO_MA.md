# Quy trình làm một hồ sơ mã (ADR-0019, ADR-0020, ADR-0021, ADR-0024, ADR-0025, ADR-0026)

Tệp này là việc phải làm theo thứ tự của **ghế phân tích**. Ghế phân tích là một phiên Claude trong Project TTC, đã đọc tệp này và ADR-0019, ADR-0020 ở `main` mới nhất. Sản phẩm chỉ được gọi là "hồ sơ mã của dự án" khi có phiếu máy ĐẠT đi kèm.

Hồ sơ là phân tích cho Owner đọc. Hồ sơ không nêu hành động nào với cổ phiếu. Owner tự quyết định và tự đặt lệnh.

## 1. Chỗ để đồ

| Thứ | Ở đâu | Vì sao |
|---|---|---|
| Công cụ, quy trình, mẫu, ví dụ số liệu bịa | Kho này: `tools/hoso/`, `docs/`, `templates/hoso/`, `templates/ky_luat/` | Công khai, có test |
| **Thư mục mã**: tệp gốc, văn bản từng trang, sổ số liệu, hồ sơ, phiếu máy, bản phản biện | Máy của Owner, ví dụ `Downloads\TTC_HO_SO\<MÃ>\`; bản đọc để trong Project | Riêng tư (ADR-0019 QĐ-P13, L-03, L-04) |
| Bản quy tắc riêng, phiếu trước quyết định, nhật ký của Owner | Chỉ ở chỗ Owner | L-03. Ghế phân tích không hỏi và không ghi các con số này |
| Sổ câu hỏi, bằng chứng trước hạn và bản nguyên văn của các ghế dự báo, bảng chấm, bản đồ phơi nhiễm nhiều mã, sổ độ phủ, sổ bất đồng, sổ lỗi đã xác minh, sổ kết quả, danh sách chấm của cổng, phiếu thử | Project | ADR-0024, ADR-0026; riêng tư như hồ sơ. Dòng sổ dự báo vào kho qua Issue, chỉ chứa câu hỏi về chỉ tiêu và xác suất (QĐ-N6) |

Không đưa thư mục mã, hồ sơ thật hay tệp gốc vào kho. Không mở PR chứa chúng.

Thư mục mã có dạng:

```
<MÃ>/
  goc/                 tệp gốc đã tải (PDF, CSV…), không sửa
  goc/ngoai/           tệp ngoài cho Mục 9, mã N (ADR-0023 QĐ-T5)
  ma_nguon.csv         ghế phân tích viết: ma,tep,ten,kieu_so
  nguon.csv            máy sinh: thêm sha256, số trang, cách đọc
  trang/<mã nguồn>/    máy sinh: pNNN.txt cho từng trang, không sửa tay
  trang_sha256.csv     máy sinh: sha256 từng tệp trong trang/ (kể cả bản đọc lại)
  so_lieu.csv          sổ số liệu
  quan_he.csv          đẳng thức phải đúng
  HO_SO_<MÃ>_<ngày>.md
  PHIEU_MAY_HO_SO_<MÃ>_<ngày>.txt
  BANG_DINH_NGHIA_HO_SO_<MÃ>_<ngày>_BAN_PHAN_BIEN.md   máy sinh ở B7 (ADR-0021 QĐ-K2)
  phan_bien/           bản trả lời của các ghế khác hãng, chép nguyên văn
```

Ví dụ chạy được, số liệu bịa: `templates/hoso/vi_du/`.

## 2. Tám bước

Mọi lệnh chạy từ gốc kho đã lấy về (`git clone` rồi `git checkout main`). `<TM>` là đường dẫn thư mục mã.

### B1. Nhận mã

Owner nêu mã. Ghế phân tích không tự chọn mã, trừ khi Owner giao việc chọn bằng lời trong chat. Ghi lại câu lệnh của Owner vào đầu hồ sơ.

### B2. Tìm và tải tệp gốc

- Danh sách tối thiểu: báo cáo tài chính kiểm toán của ba năm (mới nhất, lùi hai năm, lùi bốn năm), báo cáo bán niên soát xét mới nhất, báo cáo quý mới nhất, báo cáo thường niên mới nhất, tài liệu đại hội cổ đông mới nhất, công bố giao dịch của người nội bộ trong 12 tháng, nghị quyết phát hành trong 12 tháng.
- Nguồn: trang công bố của chính doanh nghiệp hoặc của sở giao dịch. Giá và số cổ phiếu lưu hành lấy từ một bảng giá, ghi rõ là nguồn phụ.
- Mã nguồn: tệp giá thị trường (bảng giá, giá đóng cửa, khối lượng giao dịch) mang mã bắt đầu bằng chữ **G** (G1, G2…); báo cáo và tài liệu khác dùng chữ khác (D1, D2…). Cổng giá của phiếu máy dựa vào quy ước này: nhãn ĐÃ KIỂM dẫn một nguồn G là dấu hiệu ngữ cảnh giá (B5).
- Tệp ngoài cho Mục 9 (ADR-0023 QĐ-T5): văn bản, bản tin, bảng số của cơ quan ban hành, cơ quan thống kê, ngân hàng trung ương, tổ chức quốc tế hay hiệp hội ngành về các biến thời thế của doanh nghiệp. Đặt trong `goc/ngoai/`, mang mã N (N1, N2…). Trang web không có tệp thì in thành PDF, giờ in hiện ở đầu trang. Trang viết lại tin của nơi khác và báo cáo của công ty chứng khoán không dùng làm nguồn ghim.
- Ghế tìm nguồn (Grok) lập bảng đường dẫn. Cowork tải về máy Owner theo mẫu lệnh ở `templates/hoso/LENH_MAU.md` và báo sha256 từng tệp.
- Thiếu tệp nào thì ghi vào danh sách CHƯA BIẾT. Không thay bằng số nhớ lại.

### B3. Nhận tệp

```
python tools/hoso/nhan_tep.py nhan --thu-muc <TM> --ma-nguon <TM>/ma_nguon.csv
```

- Đối chiếu sha256 máy in ra với sha256 Cowork báo. Lệch một tệp thì dừng.
- Trong `ma_nguon.csv`, tệp giá thị trường mang mã G… (B2). Đặt tệp giá dưới mã khác thì cổng giá không nhận ra nhãn dẫn nguồn giá.
- PDF dạng ảnh được máy nhận dạng chữ. Trang có bảng mà máy đọc không ra số thì đọc lại: `python tools/hoso/nhan_tep.py doc-lai --thu-muc <TM> --ma D7 --trang 16`.
- Máy thiếu `pdftotext`, `pdftoppm` hoặc `tesseract` (gói tiếng Việt) thì dừng và báo Owner. Không đoán số.
- Không sửa tay tệp nào trong `trang/`. Máy ghi sha256 từng tệp trang vào `trang_sha256.csv` khi nhận và khi đọc lại; tệp trang bị sửa, bị thêm hay bị mất thì phiếu máy CHƯA ĐẠT. Cách hợp lệ để sửa lỗi máy đọc là dòng `goc` trong `so_lieu.csv`: điền `gia_tri` và `ghi_chu` (B4).
- **Đọc hết mọi trang của báo cáo quý mới nhất và phần thuyết minh của báo cáo năm mới nhất.** Hồ sơ đầu tiên đã bỏ sót một trang giải trình vì chỉ đọc các trang có bảng chính.

### B4. Lập sổ số liệu và soát

1. Chép số từ trang vào `so_lieu.csv`: mỗi dòng một khóa, mã nguồn, trang, và `chuoi_goc` đúng như máy đọc được. Mọi tỷ lệ, hiệu, tổng sẽ dùng trong hồ sơ là **dòng tính** (`cong_thuc`), không tính nhẩm.
2. Viết `quan_he.csv`. Bắt buộc có ít nhất một đẳng thức đúng cho mỗi báo cáo, tên bắt đầu bằng `cdkt` (cân đối kế toán), `kqkd` (kết quả kinh doanh), `lctt` (lưu chuyển tiền tệ). Thêm mọi hàng so sánh mà báo cáo tự in cột chênh lệch.
3. Chạy:

```
python tools/hoso/kiem_so_lieu.py --thu-muc <TM>
python tools/hoso/kiem_so_lieu.py --thu-muc <TM> --soat-bang
```

4. Dòng nào máy báo lệch hoặc nghi đọc sai: mở ảnh trang ra xem. Nếu máy đọc sai, điền `gia_tri` đúng và viết `ghi_chu` nói phép tính nào chứng minh. Nếu máy đọc đúng, vẫn viết `ghi_chu` nêu kết luận. Không sửa `chuoi_goc`.
5. Dòng sửa (`gia_tri` khác giá trị máy đọc từ `chuoi_goc`, kể cả khi `chuoi_goc` không đọc được thành một con số) chỉ được máy nhận khi đủ hai điều. Thiếu một là CHỜ CHỨNG MINH, phiếu CHƯA ĐẠT, và số đó không dùng được cho đoạn ĐÃ KIỂM.
   - **Gần chuỗi máy đọc:** bỏ dấu chấm, dấu phẩy, khoảng trắng, ngoặc và dấu trừ ở cả hai bên; khoảng cách sửa (thêm, bớt, thay một ký tự) giữa hai dãy còn lại không quá 2.
   - **Có đẳng thức chứng minh trong `quan_he.csv`:** đẳng thức đúng; hai vế chỉ gồm tên khóa nối bằng cộng, trừ và ngoặc (không hằng số, không nhân chia); mọi khóa là dòng gốc; khóa đang sửa không tự triệt tiêu; `sai_so` không quá 2 đơn vị ở chữ số cuối của `gia_tri`; mọi khóa khác là dòng gốc chép đúng máy đọc hoặc dòng sửa đã được chứng minh trước. Phiếu in mỗi dòng sửa kèm tên đẳng thức chứng minh nó.

Lý do có bước này: ở hồ sơ đầu tiên máy đọc sai năm con số trên hai trang. Số sai vẫn "có trên trang" nên phép đối chiếu trích dẫn không bắt được. Chỉ phép tính của chính hàng đó bắt được.

6. Ba điểm cờ đỏ kế toán (ADR-0025 QĐ-L2): cần báo cáo năm t và năm t − 1 kèm thuyết minh; thiếu thì quay lại B2. Chép đầu vào thành dòng gốc; `ghi_chu` ghi chế độ kế toán, tên khoản mục, mã số chỉ tiêu, kỳ, đơn vị, hợp nhất hay riêng. Mỗi tỷ số, điểm M và điểm Z là dòng tính theo đúng `templates/hoso/DIEM_CO_DO_KE_TOAN.md`. Mẫu số bằng không hay thiếu đầu vào thì không lập dòng tính đó, ghi CHƯA BIẾT kèm lý do. Điểm F không là dòng tính. Doanh nghiệp tài chính: không tính. Thêm xong thì chạy lại bước 3.
7. Trước B5, tính độ phủ doanh thu (ADR-0025 QĐ-L3). Tử số: tổng các khoản doanh thu từ bên ngoài trong một bảng chia duy nhất của tệp gốc đã ghim (theo mảng, theo sản phẩm hay dịch vụ, hay theo nhóm khách hàng; không trộn hai bảng), cùng kỳ và cùng phạm vi hợp nhất hay riêng với mẫu số. Mẫu số: doanh thu thuần năm gần nhất; doanh nghiệp tài chính dùng tổng thu nhập hoạt động ở cả tử và mẫu. Đầu vào là dòng gốc; tử số và tỷ lệ là dòng tính; chạy lại bước 3. Tỷ lệ dưới ba phần tư, hoặc không tính được: dừng, báo Owner «chưa đủ tài liệu để hiểu doanh nghiệp kiếm tiền từ đâu» kèm tỷ lệ và danh sách tài liệu còn thiếu, chờ Owner chọn tìm thêm, đi tiếp hay bỏ mã; ghi ở Project tỷ lệ trước, tài liệu thêm, tỷ lệ sau và lựa chọn của Owner. Không ghi CHƯA BIẾT để đi tiếp.

### B5. Viết hồ sơ

- Chép khung từ `templates/hoso/vi_du/HO_SO_MAU.md`: đầu hồ sơ, "Cách đọc", "Một trang", Mục 1 tới Mục 12, "Kết quả 15 điểm soi", "Danh sách CHƯA BIẾT", "Bảng nguồn", "Lịch sử sửa".
- Chỉ dùng bộ định dạng của hồ sơ mẫu: tiêu đề `#` sát lề (tiêu đề `##` giữ đúng tên của khung, không thêm chữ), đoạn chữ sát lề, bảng bắt đầu bằng `|`, mục liệt kê `- ` hay `1. ` (mục con thụt 2, 4… dấu cách), chữ đậm `**…**`, mã `` `…` `` tách khỏi chữ bằng dấu cách hay dấu câu, dấu `_` chỉ trong khóa sổ nằm trong nhãn (`[SUY LUẬN, sổ số liệu: dt_tang_25]`) hay tên tệp trong mã. Không dùng `_` hay `*` để nhấn mạnh, thẻ hay thực thể HTML, liên kết, trích dẫn `>`, khối mã, tiêu đề gạch chân, dòng thụt lề không phải mục liệt kê, dấu `\`, tab hay dấu cách đặc biệt. Máy báo mọi dòng ngoài bộ này (`kiem_luat.kiem_dinh_dang`).
- Chỉ dùng ký tự trong bảng chữ cho phép (ADR-0022 QĐ-C1): chữ Latin, chữ Việt, chữ số 0–9, dấu cách thường, các dấu `. , ; : ! ? ' " “ ” ‘ ’ « » ( ) / % + = × ÷ ± ≈ ≠ ≤ ≥ → ← … # & - – — −`, và `|`, `*`, `` ` ``, `_`, `[`, `]` theo luật của chúng; trong mã được thêm `\`. Không dùng `~` (kể cả một dấu), `$`, `<`, `>`, `^`, `@`, `{`, `}`, ký hiệu tiền tệ, độ, mũ, phân số, chữ số dạng khác hay chữ của bảng mã khác: viết «USD», «khoảng» hay «≈», «≥», «mét vuông» hay «m2». Ngoặc vuông chỉ dùng cho nhãn; không viết liên kết, chú thích chân trang, ô đánh dấu, địa chỉ web (`://`, `www.`) hay mã biểu tượng («:one:»). Trong mã không dùng `|`, `[`, `]`.
- Viết số sao cho người đọc và máy đọc ra cùng một con số (ADR-0022 QĐ-C3): tách chữ và số bằng dấu cách («tăng 63,4%», không «tăng63,4%»; «ROE 15%», không «ROE15%»), trừ mã một chữ hoa với một hai chữ số (D1, H0, Q3), VN30, VN100, HNX30, VNX50, SHA256, CO2, m2, m3, km2, mã băm và kỳ báo cáo («9T2026», «Q3.2025», «H1/2025»); không viết chữ O, o, I, l sát sau chữ số; không tách hàng nghìn bằng dấu cách hay dấu nháy («1.200», không «1 200», «1'200»). Dấu trừ viết sát con số, sau dấu cách hay ngoặc mở («giảm -4,5%», «(-36,4)»); không viết dấu trừ dính sau chữ («giảm-4,5%»), sau dấu chấm hay dấu phẩy, trước ngoặc («-(36,4%)»), hay cách con số một dấu cách («biến động - 36,4%»), trừ ký hiệu mục liệt kê và khoảng sau một con số («2020 - 2025»). Trong phép tính viết bằng chữ và số, đặt số ở cả hai bên dấu trừ hoặc viết «trừ».
- Dấu định dạng không được đổi con số. Chữ đậm và mã mở, đóng trên cùng một dòng, không có dấu cách sát mép trong, và bọc trọn con số, kể cả dấu âm, ngoặc và dấu %: viết «**-36,4%**», không viết dấu trừ ngoài rồi số trong mã hay trong chữ đậm, không in đậm một phần con số, không dán chữ đậm vào chữ đứng trước. Trong mã không dùng dấu `*`. Dấu âm viết bằng «-» hay «−» sát con số; gạch dài «—» và các ký tự gạch ngang khác không được dính liền trước chữ số. Máy đọc số trên chữ người đọc thấy (bỏ dấu `**` và dấu backtick, không chèn gì), và báo lỗi định dạng khi cách đọc đó khác cách đọc lúc thay dấu định dạng bằng dấu cách.
- Số viết theo kiểu Việt Nam: dấu chấm tách hàng nghìn, dấu phẩy là phần lẻ («1.234,5»). Cụm chữ số máy không đọc được theo kiểu này («63.4», «1,234,567», «31.12.2025», «3.1») là lỗi ở đoạn SUY LUẬN, đoạn ĐÃ KIỂM (ADR-0022 QĐ-C4), đoạn không nhãn, hàng tiêu đề bảng và tiêu đề phụ; ở đoạn GIẢ ĐỊNH, CHƯA BIẾT máy chỉ đếm. Con số đứng sát sau một dấu phẩy hay dấu chấm («20,0%,63,4%», «36 ,9%») cũng là lỗi: thêm dấu cách. Ngày tháng viết theo dạng máy nhận, với giá trị hợp lệ: «ngày 31 tháng 12 năm 2025», «31/12/2025», «12/2025», «31/12», «tháng 12», «quý 4», «năm 2025», giờ «9:30»; dạng khác («31-12-2025») và giá trị không hợp lệ («quý 63», «tháng 99», «năm 1300», «63:37», «45/55») máy đọc thành con số.
- Dấu âm chỉ được đọc khi đứng sát trước con số và sau một dấu cách hay dấu mở ngoặc: «giảm -4,5%», «(1.193)». Khoảng viết «20,0–30,0%» (một dấu %); viết «20,0%-30,0%» thì máy đọc số sau gạch là số âm.
- Bảng có dòng kẻ `|---|` ngay dưới hàng tiêu đề, và mọi hàng có đúng số ô của hàng tiêu đề; ô thiếu thì để ô trống. Bảng không có dòng kẻ, hay hàng có ô thừa, là lỗi định dạng.
- Mỗi câu có số phải kết bằng một nhãn: `[ĐÃ KIỂM D1 tr.12]`, `[SUY LUẬN …]`, `[GIẢ ĐỊNH]`, `[CHƯA BIẾT]`. Nhãn phủ phần chữ đứng trước nó, tới nhãn liền trước. Bảng nhận nhãn đứng đầu dòng ngay sau nó, hoặc nhãn cuối của đoạn ngay trước nó; giữa bảng và nhãn chỉ được có dòng trống. Một hàng bảng chỉ mang một nhãn. Nhãn viết trọn trên một dòng. Nhãn mở đầu ngay bằng loại của nó; «sổ số liệu» chỉ đứng trong nhãn SUY LUẬN; nhãn GIẢ ĐỊNH, CHƯA BIẾT không nhắc loại nhãn nào khác (`[GIẢ ĐỊNH, SUY LUẬN, …]` là lỗi: tách thành hai nhãn); nhãn không chứa dấu `|` và không có `(`, `[`, `:` ngay sau (ADR-0022 QĐ-C2). Hàng tiêu đề của bảng và tiêu đề phụ (`###` trở xuống) không mang nhãn: không viết số liệu ở đó (năm, ngày tháng, số dưới 10 thì được; tiêu đề phụ không đánh số nhiều tầng kiểu «3.1»).
- Số đứng đầu một mục liệt kê («12. …») chỉ là số thứ tự khi nó dưới 10 hoặc danh sách được đánh đúng 1, 2, …, n liền nhau (chỉ cách nhau bằng dòng trống); ngoài ra nó là con số, và từ 10 trở lên thì máy báo lỗi «danh sách không được đánh đúng», vì trình dựng không hiện đúng số đã viết. «63. » ở giữa đoạn hay trong ô bảng luôn là con số. Dòng «63. …» viết ngay dưới một dòng chữ thường (không cách dòng trống) không mở danh sách mà nối vào đoạn đó.
- Số trong đoạn ĐÃ KIỂM phải có trên trang đã ghi, hoặc là một dòng gốc của sổ, hoặc tính được từ các số cùng đoạn. Số nguyên nhỏ, năm và số trong dấu backtick cũng vậy, và không đi đường tính. Số tự tính mà không có số gốc đứng cạnh thì đưa vào sổ thành dòng tính và dán nhãn SUY LUẬN.
- Nhãn SUY LUẬN gọi tên khóa sổ (ADR-0021 QĐ-K1): `[SUY LUẬN, sổ số liệu: khóa_a, khóa_b]`. Dãy khóa cùng phần chữ viết `[SUY LUẬN, sổ số liệu: kl_tb_t06 tới kl_tb_t11]`. Ghi chú đặt sau dấu `;`: `[SUY LUẬN, sổ số liệu: dt_tang_25; căn cứ thêm phai_thu_tang_25]`; cụm «sổ số liệu:» phải đứng trước dấu `;` đầu tiên, đứng sau thì máy coi là ghi chú. Mỗi lần nhãn xuất hiện là một phạm vi riêng, máy nhận theo vị trí của nhãn chứ không theo chữ của nhãn: một nhãn cùng chữ ở chỗ khác không gộp vào. Nhãn phủ cả bảng thì các hàng dữ liệu của bảng thuộc phạm vi của đúng lần xuất hiện đó (cộng phần đoạn dẫn kết bằng nhãn đó, khi nhãn đứng cuối đoạn ngay trên bảng); hàng bảng có nhãn trong ô là phạm vi riêng. Nhãn gọi khóa phải phủ ít nhất một chữ. Máy kiểm hai chiều:
  - mỗi con số trong đoạn SUY LUẬN, kể cả số viết trong backtick, phải khớp giá trị của một khóa nhãn gọi tên, hoặc là hằng số viết nguyên văn trong công thức của khóa đó (ví dụ 49 trong `g2_cp_luu_hanh * 49 / 100`; câu viết «nhân 1,1» thì công thức viết `* 1.1`, không viết `* 11 / 10`), hoặc trùng một số ĐÃ KIỂM đã lần ra trong hồ sơ. Đoạn SUY LUẬN không gọi khóa nào thì mọi con số phải là số ĐÃ KIỂM nhắc lại: không tính nhẩm;
  - phạm vi có số liệu thì mỗi khóa nhãn gọi tên phải hiện ra ở ít nhất một con số của chính phạm vi đó. Năm, ngày tháng («tháng 12 năm 2025»), số nhỏ dưới 10, số thứ tự thật đầu mục liệt kê và số thứ tự trong bảng không làm phạm vi «có số liệu»; số đếm thời gian từ 10 trở lên («95 ngày», «12 tháng») thì có. Một con số không đứng thay cho hai khóa làm tròn ra hai số khác nhau. Khóa chỉ làm căn cứ cho một câu định tính («đều âm», «khoảng một nửa») thì đặt sau dấu `;`.
  - Ngưỡng của điều kiện sai ở Mục 11 («tăng trưởng dưới 15%») là lựa chọn của ghế phân tích, không phải số tính: viết dưới nhãn `[GIẢ ĐỊNH]`.
- Ngay sau đầu hồ sơ là mục «Trạng thái kiểm» (ADR-0021 QĐ-K3), bốn dòng: `- **Phiếu máy:**`, `- **Đối chiếu số khác hãng:**`, `- **Phản biện khác hãng:**`, `- **Owner tự mở ba số:**`. Lúc viết, ba dòng sau ghi «chưa làm». Mục này nằm ngoài phạm vi đối chiếu trích dẫn; máy kiểm mỗi tên mở đầu đúng một mục liệt kê riêng. Bốn dòng phải là mục liệt kê thật, bắt đầu bằng «- ». Mỗi tiêu đề cấp hai của khung, kể cả «Trạng thái kiểm», chỉ xuất hiện một lần và đứng theo thứ tự của khung: Trạng thái kiểm, Cách đọc, Một trang, Mục 1 tới Mục 12, Kết quả 15 điểm soi, Danh sách CHƯA BIẾT, Bảng nguồn, Lịch sử sửa, Phiếu máy.
- Cuối «Một trang» là tiểu mục «### Tổng kết: điểm mạnh, điểm yếu, điểm nghi vấn» (ADR-0026 QĐ-B5). Ba danh sách ngắn. Mỗi dòng chép lại một mệnh đề hồ sơ đã viết ở một mục, ghi tên mục đó («Mục 5», «Mục 11»), giữ nguyên phạm vi, kỳ, điều kiện, nguồn và mức bất định của câu gốc, và mang đúng nhãn của câu gốc kèm khóa sổ hay mã tệp và trang. Không nâng nhãn: câu GIẢ ĐỊNH hay SUY LUẬN không viết lại thành ĐÃ KIỂM; dòng CHƯA BIẾT không viết thành nhận định. Không thêm dữ kiện mới. «Điểm nghi vấn» lấy từ kết quả điểm soi và danh sách CHƯA BIẾT. Không có câu kết luận chung; không câu nào gộp các danh sách thành nhận xét tốt hay xấu về doanh nghiệp hay về mã. Không điểm số, không xếp hạng, không so với mã khác, không từ hành động. Không nêu giá cổ phiếu, hệ số định giá, vốn hóa hay khoảng giá trị ở tiểu mục này; không nhắc điểm F, điểm M, điểm Z hay trạng thái cờ của chúng, kể cả bằng chữ không có số. Phiếu máy chỉ kiểm cú pháp của tiểu mục; phần nghĩa do câu hỏi bắt buộc thứ tư ở B7 kiểm.
- Mục 8 để trống cho tới khi Owner sửa L-02: thân mục chỉ có đúng câu của hồ sơ mẫu, «**Chưa viết.** Theo ADR-0019 QĐ-P13, mục này chỉ viết sau khi Owner sửa L-02.». Máy bắt mọi chữ, số hay bảng thêm vào.
- Giá cổ phiếu, hệ số định giá (P/E, P/B, P/S, EV/EBITDA) và vốn hóa chỉ được nêu dưới dạng số quá khứ có nguồn: trong đoạn ĐÃ KIỂM, mọi chữ số có trên trang đã ghi (hoặc là dòng gốc của sổ), năm không vượt năm lớn nhất của trang đó, không kèm từ chỉ tương lai hay tín hiệu (dự báo, dự kiến, kỳ vọng, mục tiêu, sẽ, có thể, kịch bản, nếu, giả định, năm sau, ngắn hạn, nên, chờ, … tới, hỗ trợ, kháng cự…). Máy nhận ra "ngữ cảnh giá" qua: số mang đơn vị giá (đồng, nghìn đồng, VND, đ, "/cp", "30 nghìn mỗi cp"…); chữ "giá" (giá vốn, giá bán, đánh giá, "giá trị" thường… chỉ được bỏ qua khi phần chữ không có từ chỉ cổ phiếu: cổ phiếu, cổ phần, cp, "giá MAU"); hệ số định giá hay vốn hóa; nhãn ĐÃ KIỂM dẫn nguồn G. Từ tương lai đi cùng từ chỉ cổ phiếu là lỗi kể cả khi không có con số. Tiêu đề, hàng tiêu đề bảng và bảng nguồn không mang nhãn, nên không được nêu giá kèm số (năm đứng riêng thì được). Danh sách đầy đủ ở docstring `tools/hoso/kiem_luat.py`.
- Bảng hay danh sách đặt ngay dưới một câu có chữ «giá», và mọi đoạn dưới một tiêu đề phụ có chữ «giá», sẽ bị xét như ngữ cảnh giá. Trong phần chữ nói về giá, mọi chữ số đều phải có trên trang nguồn: số thứ tự chỉ được bỏ qua khi cột đầu tên là #, STT, TT, Số TT hoặc Số thứ tự và đánh đúng 1, 2, …, n; «điểm 30», «12 tháng», «25/4» đều là con số.
- Không viết khoảng giá trị hay giá mục tiêu ở bất kỳ mục nào khác, dù nhãn là gì. Máy bắt hai số nối bằng gạch ngang hoặc "đến/tới" kèm đơn vị tiền (đồng, nghìn đồng, VND, đ; trong bảng tính cả đơn vị ở tiêu đề cột), và các cụm "khoảng giá", "vùng giá", "mức giá", "giá mục tiêu", "giá trị nội tại", "giá trị một/mỗi cổ phiếu" đi với số. Chỉ giá quá khứ trong đoạn ĐÃ KIỂM, mọi số có trên trang đã ghi, mới được qua.
- Mục 9 là bảng phơi nhiễm thời thế (ADR-0023):
  - Tên biến lấy đúng chữ ở cột «Tên biến» của `templates/hoso/TU_DIEN_BIEN_THOI_THE.md` (ADR-0024 QĐ-N2). Biến chưa có thì thêm một dòng vào từ điển bằng PR chữ, trước hoặc cùng lúc với hồ sơ đầu tiên dùng nó.
  - Mỗi biến một tiêu đề phụ `###`; dưới đó theo thứ tự: trạng thái ở ngày ghi theo tệp ngoài (mã N); mức phơi nhiễm theo tệp gốc của doanh nghiệp; giả thuyết nào ở Mục 11 dựa vào biến, qua dòng nào của báo cáo; điều kiện làm trạng thái đã ghi đổi. Sau các biến là bảng tóm tắt năm cột (biến, trạng thái đã ghim, phơi nhiễm từ tệp gốc, giả thuyết dựa vào, chấm được ở ngày xem lại) và một đoạn nói cách chấm ở ngày xem lại.
  - Phơi nhiễm là quy mô, không phải độ nhạy: ghi rõ điều đó, và ghi độ nhạy của lợi nhuận là CHƯA BIẾT. Không viết câu «nếu biến đổi chừng này thì lợi nhuận đổi chừng kia». Được một phép thử cơ học cho mỗi biến, cú sốc đúng một đơn vị, là dòng tính trong sổ, kèm câu GIẢ ĐỊNH nêu giả định của phép thử.
  - Điều kiện đổi trạng thái ghi rõ bốn thứ: văn bản hay bản tin dùng để chấm, chỉ tiêu, kỳ so sánh, ngưỡng. Trạng thái đã ghi viết thành một quan hệ; điều kiện là quan hệ đó không còn đúng; biến là khoảng thì xét cả hai đầu mút. Sự kiện pháp lý: chỉ văn bản có hiệu lực làm đổi, và ghi khi nào trạng thái giữ nguyên. Một dòng nhiều chỉ tiêu: ghi luật gộp. Thiếu một trong bốn thứ thì dòng ghi «chưa chấm được». Ngưỡng viết bằng chữ, dưới nhãn GIẢ ĐỊNH.
  - Không câu nào nêu hay ngụ ý biến sẽ đi hướng nào; không cộng các dòng thành điểm; không từ hành động.
  - Giả thuyết dựa vào biên lợi nhuận thì bảng có biến phía chi phí lẫn phía doanh thu; thiếu nguồn thì vẫn lập dòng, ô trạng thái ghi «Chưa». Nguồn ngành chứa số của chính doanh nghiệp thì ghi «không độc lập với» doanh nghiệp. Quá tám dòng thì ghi một câu lý do.
  - Tiêu đề phụ của Mục 9 không có chữ «giá». Số giá hàng hóa chỉ đứng trong đoạn ĐÃ KIỂM; điều kiện viết ở câu riêng, không có số giá.
  - Mục 11 thêm dòng «Biến thời thế». Điều kiện sai ở Mục 11 cần báo cáo của kỳ nào thì ngày xem lại phải gồm ngày có báo cáo kỳ đó.
- Mục 10 chỉ mô tả giá và khối lượng.
- Mục 6 có tiêu đề phụ «### Điểm cờ đỏ kế toán» (ADR-0025 QĐ-L2), viết theo mục «Cách viết trong hồ sơ» của `templates/hoso/DIEM_CO_DO_KE_TOAN.md`: mở bằng câu cố định của tệp mẫu; điểm M, điểm Z và các tỷ số dưới nhãn SUY LUẬN gọi khóa; ngưỡng và chỗ ánh xạ dưới nhãn GIẢ ĐỊNH; điểm F ghi đạt hay không của từng tiêu chí kèm khóa của tỷ số, tổng và cờ chỉ khi đủ chín tiêu chí. Cờ bật thì nêu các tỷ số đóng góp lớn nhất và khoản mục cần soi, nối với điểm soi tương ứng; không gọi đó là nguyên nhân, không viết doanh nghiệp làm đẹp lợi nhuận, gian lận hay sắp vỡ nợ. Không xếp hạng, không cộng các điểm, không đưa điểm vào câu đánh giá doanh nghiệp, câu về giá cổ phiếu, khoảng giá trị hay lời hành động. Doanh nghiệp tài chính ghi «không áp dụng».
- Mục 11: ba giả thuyết H1 (tốt), H2 (xấu), H0 (không có gì đặc biệt). Mỗi giả thuyết có điều kiện làm nó sai. Có ngày xem lại. Mỗi điều kiện sai tự đủ bốn thứ: chỉ tiêu, kỳ, mốc so sánh, ngưỡng (ADR-0026 QĐ-B5); ngưỡng viết dưới nhãn GIẢ ĐỊNH. Chỉ tiêu không được là giá cổ phiếu, khối lượng giao dịch hay chỉ số thị trường. Điều kiện là một sự kiện có hay không thì bốn thứ là: sự kiện, nguồn dùng để xác nhận, kỳ, và tiêu chí coi là đã xảy ra. Điều kiện không viết được đủ bốn thứ: giữ nguyên câu điều kiện, ghi ngay sau nó «chưa chấm được: thiếu» kèm tên thứ còn thiếu, và thêm một dòng vào danh sách CHƯA BIẾT nêu tài liệu nào sẽ cho thứ còn thiếu. Không thêm ngưỡng hay mốc so sánh sau khi giao.
- Cuối Mục 11 là tiêu đề phụ «### Khám nghiệm trước» (ADR-0025 QĐ-L1). Ghi nhận định được khám nghiệm, mã ND-1: chỉ rõ câu quan trọng nhất của «Một trang» (gạch đầu dòng thứ mấy, đếm ở phần đứng trước tiểu mục «Tổng kết»), nêu lại nó trong một câu không có con số, kèm giả thuyết của Mục 11 mà nó dựa vào; điều kiện sai của giả thuyết đó là điều kiện bác ND-1 và phải bác được thật nhận định đó. Mã viết có gạch nối (ND-1, LD-1), vì máy chặn chữ dính số. Rồi ba lý do chính LD-1, LD-2, LD-3: mỗi lý do nêu cơ chế làm ND-1 sai (khoản mục nào của báo cáo, đổi theo chiều nào) và chỗ chấm được: một điều kiện sai ở Mục 11, một điều kiện đổi trạng thái ở Mục 9, một điểm soi, hay một dòng CHƯA BIẾT; không có chỗ chấm thì thêm dòng vào danh sách CHƯA BIẾT. Viết dưới nhãn GIẢ ĐỊNH, không thêm con số mới. Lý do liên quan tới biến thời thế chỉ trỏ tới điều kiện ở Mục 9, không nêu biến sẽ đi hướng nào. Không lý do nào nói về giá cổ phiếu, khoảng giá trị hay hành động với cổ phiếu. Giả thuyết có điều kiện «chưa chấm được» không được chọn làm căn cứ của ND-1. Không giả thuyết nào của Mục 11 có điều kiện đủ bốn thứ: dừng trước B6 và báo Owner; không tự bỏ tiểu mục này (ADR-0026 QĐ-B5).
- Hồ sơ kết bằng danh sách CHƯA BIẾT.
- Sách và báo cáo có bản quyền: chỉ ghi địa chỉ trang và trích không quá 15 từ (L-04).

### B6. Phiếu máy

```
python tools/hoso/phieu_may.py --thu-muc <TM> --ho-so <TM>/HO_SO_<MÃ>_<ngày>.md
```

- Phiếu CHƯA ĐẠT: sửa hồ sơ hoặc sổ rồi chạy lại. Không gửi phản biện, không giao Owner.
- Không có ngoại lệ (ADR-0020, sửa theo bản chấm L-09 vòng 2). Con số ĐÃ KIỂM mà máy không lần ra thì xử lý theo thứ tự:
  1. đọc lại trang (`python tools/hoso/nhan_tep.py doc-lai --thu-muc <TM> --ma <mã> --trang <n>`);
  2. nếu máy đọc sai chữ số: dòng sửa trong sổ, kèm đẳng thức chứng minh (B4 bước 5);
  3. còn lại: không viết con số đó dưới ĐÃ KIỂM. Viết dưới `[CHƯA BIẾT]` và ghi vào Danh sách CHƯA BIẾT kèm «máy không đọc được <nguồn> tr.<n>».
- Thư mục mã còn tệp `ngoai_le.csv` thì phiếu báo lỗi: tệp không còn dùng, xóa đi.
- Phiếu ĐẠT nghĩa là con số lần ra được và hồ sơ đúng khung. Phiếu không nói lập luận đúng.
- Cuối phiếu có mục «Owner tự mở ba số» (ADR-0021 QĐ-K4): máy chọn theo sha256 của hồ sơ một số ĐÃ KIỂM ở «Một trang», một dòng máy đọc sai đã sửa, và một dòng gốc sau một khóa SUY LUẬN ở «Một trang». Ghế phân tích không sửa hồ sơ để đổi ba số này.

### B7. Phản biện và đối chiếu số (ghế khác hãng)

1. Gài một lỗi cố ý vào bản gửi đi:

```
python tools/hoso/gai_loi.py tao --thu-muc <TM> --ho-so <TM>/HO_SO_<MÃ>_<ngày>.md --tim "<số đúng>" --thay "<số sai>"
```

   Máy chỉ nhận lỗi gài mà phép đối chiếu số bắt được. Tệp `…_LOI_GAI.md` là niêm phong: không gửi ghế nào.
2. Lập bảng định nghĩa cho bản gửi đi (ADR-0021 QĐ-K2):

```
python tools/hoso/bang_dinh_nghia.py --thu-muc <TM> --ho-so <TM>/HO_SO_<MÃ>_<ngày>_BAN_PHAN_BIEN.md
```

   Gửi `…_BAN_PHAN_BIEN.md` cùng đường dẫn tệp gốc cho hai ghế khác hãng Anthropic, theo mẫu ở `templates/hoso/LENH_MAU.md`: một ghế viết bản phản biện bốn phần (QĐ-P7), một ghế đối chiếu số. Ghế đối chiếu số nhận thêm bảng định nghĩa và trả lời ba câu hỏi của bảng cho từng dòng.
3. Bản trả lời phải mở đầu bằng **mã nhận tệp** in ở đầu bản phản biện. Không có mã: coi như ghế đó chưa đọc tệp, gửi lại.
4. Ghế nào hết hạn mức thì chuyển sang ghế khác hãng còn lại (ChatGPT, Gemini, Grok). Không dùng Claude cho bước này.
5. Lệnh phản biện có câu hỏi bắt buộc thứ hai về Mục 9 (ADR-0023 QĐ-T7, mẫu B), câu hỏi bắt buộc thứ ba về lý do thất bại hồ sơ chưa lường trước (ADR-0025 QĐ-L1), và câu hỏi bắt buộc thứ tư về từng dòng của tiểu mục «Tổng kết» (ADR-0026 QĐ-B5). Lỗi ở tiểu mục mà ghế phản biện nêu và ghế phân tích xác minh thì ghi ở Project theo danh sách lỗi của ADR-0026 QĐ-B5 điểm 1; số hồ sơ có lỗi như vậy dùng cho điều kiện hoàn tác 5 của ADR đó.
6. Chép nguyên văn bản trả lời vào `phan_bien/`. Ghi vào tệp niêm phong: ghế nào nhận được tệp, ghế nào bắt được lỗi gài.
7. Điểm nào ghế phản biện kết luận ngược hồ sơ mà phân định được bằng báo cáo sau này: ghi vào danh sách ứng viên bất đồng ở Project, gồm nguyên văn hai lập luận, ghế của mỗi bên, mã hồ sơ và bản. Không ghi nhãn loại lập luận (đã ngừng theo ADR-0026 QĐ-B2). Chưa soạn câu hỏi, chưa hỏi ghế nào; việc đó làm sau khi giao, ở mục 5 (ADR-0024 QĐ-N5). Lỗi xác minh được ngay bằng tài liệu thì sửa ở B8 và ghi vào sổ lỗi đã xác minh, không phải ứng viên bất đồng.

### B8. Sửa, giao Owner, hậu kiểm

1. Với từng điểm ghế khác hãng nêu: mở trang gốc kiểm lại. Đúng thì sửa hồ sơ và sổ; không đúng thì ghi lý do. Lý do thất bại mới ghế phản biện thêm mà ghế phân tích nhận thì đưa vào «Khám nghiệm trước» với mã LD-4 trở đi, ghi «từ phản biện»; ba lý do chính giữ mã, lỗi đã xác minh trong ND-1 hay trong lý do thì sửa như mọi lỗi khác. Ghi vào "Lịch sử sửa". Viết lại mục «Trạng thái kiểm»: ghế nào đối chiếu số và kết quả (số dòng KHỚP, LỆCH, có bắt được lỗi gài không); ghế nào phản biện; tệp gốc nào mỗi ghế không mở được; ý nào ở «Một trang» chưa được ghế khác hãng nào đối chiếu.
2. Chạy lại B6 cho bản đã sửa. Chạy `python tools/hoso/gai_loi.py kiem --ho-so … --niem-phong …` để chắc bản Owner không còn lỗi gài.
3. Giao Owner ba thứ: hồ sơ, phiếu máy ĐẠT, bản phản biện. Owner tự mở ba con số mà phiếu máy chọn (ADR-0021 QĐ-K4, thay cách chọn «ba con số bất kỳ» của QĐ-P9); Owner muốn mở thêm số nào cũng được. Owner đọc xong thì gõ trong Project «đã đọc <MÃ> <bản>»; ghế phân tích ghi dòng đó kèm ngày vào tài liệu Project của hồ sơ (ADR-0026 QĐ-B6). Dòng này là tự khai của Owner; nó không chứng minh đã hiểu, đã dùng hay đã mở ba số. Owner không gõ thì ghi CHƯA GHI, không suy thành chưa đọc. Owner có thể ghi thêm chỗ còn vướng và số phút đã đọc; không ghi số vốn, vị thế hay mức lỗ (L-03). Sau hồ sơ thứ ba có tiểu mục «Tổng kết», ghế phân tích hỏi Owner tiểu mục có được dùng không, và ghi ở Project CÓ DÙNG, KHÔNG DÙNG hay CHƯA PHẢN HỒI.
4. Niêm phong bản đã giao (ADR-0021 QĐ-K5): ghế phân tích ghi phiếu máy ĐẠT, có sha256 của hồ sơ, vào tài liệu của Project ngay khi giao. Từ lúc đó không sửa bản đã giao; muốn sửa thì làm bản mới, có phiếu mới.
5. Tới ngày xem lại ở Mục 11: mở đúng bản đã giao, kiểm sha256 của tệp khớp sha256 trên phiếu đã ghi vào Project. Lấy báo cáo mới, làm lại từ B2 cho phần mới. Với từng giả thuyết, chép nguyên văn điều kiện sai của bản đã giao, rồi ghi ĐÚNG, SAI hoặc CHƯA RÕ kèm bằng chứng có nhãn. Điều kiện mà bản đã giao ghi «chưa chấm được» thì ghi CHƯA RÕ; không thêm ngưỡng hay mốc so sánh sau khi giao. Giả thuyết ghi SAI thì ghi thêm đúng một loại nguyên nhân chính về phía hồ sơ, chọn theo thứ tự và luật ở mục 5.5 bước 3 (ADR-0026 QĐ-B4): LỖI DỮ KIỆN; GIẢ ĐỊNH SAI; LỖI SUY LUẬN; KHÔNG LỖI, ĐÃ NÊU; KHÔNG LỖI, BIẾN CỐ MỚI; CHƯA RÕ. Mọi kết quả của bước này được chép vào sổ kết quả, và được một ghế khác hãng đối chiếu (mục 5.5). Không chấm theo chữ của một bản sửa sau. Với bảng thời thế ở Mục 9 (ADR-0023 QĐ-T6): mỗi dòng ghi ĐỔI, ĐỔI MỘT PHẦN, GIỮ NGUYÊN hay CHƯA CHẤM ĐƯỢC theo đúng điều kiện riêng của dòng; mỗi giả thuyết ghi nguyên nhân TRONG BẢNG, NGOÀI BẢNG hay CHƯA RÕ, và «nguyên nhân do doanh nghiệp nêu» kèm mã tệp và trang khi báo cáo tự nêu; báo cáo quy thay đổi lợi nhuận cho một yếu tố không có dòng trong bảng và không có trong CHƯA BIẾT thì ghi một lần «không báo». Doanh nghiệp công bố báo cáo tài chính trước ngày xem lại thì chạy hậu kiểm theo sự kiện ở mục 5.4 (ADR-0024 QĐ-N4). Với hồ sơ thuộc phạm vi ADR-0025 (giao sau ngày gộp ADR đó): nếu điều kiện bác ND-1 đã xảy ra, ghi ĐÃ LƯỜNG TRƯỚC (trùng cơ chế của một LD: cùng khoản mục, cùng chiều, có bằng chứng kèm mã tệp và trang), KHÔNG LƯỜNG TRƯỚC hay CHƯA RÕ; giả thuyết cạnh tranh bị loại mà ND-1 không bị bác thì không chấm. Ghi các sự cố mới phát sinh hay lần đầu được công bố trong kỳ theo dõi (từ ngày giao tới ngày xem lại cuối cùng đã niêm phong ở Mục 11) theo danh sách đóng của ADR-0025 QĐ-L2 điểm 5, mỗi sự cố kèm loại, mã tệp, trang, ngày phát sinh, ngày công bố, ngày phát hiện; kỳ theo dõi đóng ở hậu kiểm định kỳ tại ngày xem lại. Điểm và cờ lấy từ bản đã niêm phong, không tính lại. Mỗi kết quả chỉ đếm một lần dù nhắc lại ở hậu kiểm theo sự kiện và định kỳ. Hồ sơ niêm phong trước ADR-0025 không ghi các trường này.
6. Sửa quá ba vòng phản biện mà chưa hội tụ: dừng, báo Owner.
7. Sau khi niêm phong ở bước 4: làm các việc ở mục 5 (ADR-0024). Hồ sơ trước, đo sau: không hoãn hay rút bước nào ở trên để kịp vòng dự báo.

## 3. Khi nào dừng và báo Owner

- sha256 tệp gốc lệch giữa hai máy.
- Thiếu chương trình đọc PDF.
- Có hơn mười con số trên trang mà máy không đọc được sau khi đã đọc lại.
- Hai ghế khác hãng cùng không nhận được tệp, hoặc cùng hết hạn mức.
- Việc được giao đòi nêu hành động với cổ phiếu, khoảng giá trị, hoặc số vốn của Owner.
- Độ phủ doanh thu bằng tệp gốc dưới ba phần tư, hoặc không tính được (B4 bước 7, ADR-0025 QĐ-L3).
- Việc được giao là một năng lực mới, một phép thử tay mới hay một gói Pha 2, trong lúc cổng bằng chứng chưa mở và việc đó không có trong danh sách đóng (mục 6, ADR-0026 QĐ-B1).
- Chưa rõ một việc là phép thử tay hay là việc thuộc L-05, L-06 (mục 6).
- Soạn Mục 11 mà không giả thuyết nào có điều kiện sai đủ bốn thứ (B5, ADR-0026 QĐ-B5).

## 4. Giới hạn của máy

- Máy bắt được: con số không có trên trang đã ghi (kể cả số nhỏ, năm, số trong backtick ở đoạn ĐÃ KIỂM), hoặc sai dấu; trang ghi trong nhãn không có thật; phép tính không khớp; số SUY LUẬN không khớp khóa nhãn gọi tên, khóa gọi tên mà không hiện số, khóa không có trong sổ, nhãn gọi khóa mà không phủ chữ nào, số liệu ở hàng tiêu đề bảng hay tiêu đề phụ, hàng bảng có hơn một nhãn, con số viết kiểu Anh («63.4») ở đoạn SUY LUẬN hay đoạn không nhãn, dấu định dạng cắt ngang con số, bảng không có dòng kẻ hay có hàng thừa ô, danh sách đánh số sai, tiêu đề cấp hai lặp hay sai thứ tự (ADR-0021); ký tự ngoài bảng chữ cho phép, ngoặc vuông ngoài nhãn, nhãn sai dạng hay lẫn loại, địa chỉ web, mã biểu tượng, chữ dính số, dấu trừ viết sai chỗ, số tách nghìn bằng dấu cách, số kiểu Anh ở đoạn ĐÃ KIỂM (ADR-0022); dòng sửa trong sổ không gần chuỗi máy đọc hoặc không có đẳng thức cộng trừ chứng minh; tệp gốc bị đổi; tệp trang bị sửa, thêm hay mất; hồ sơ sai khung; cụm từ L-02 cấm; khoảng giá viết theo các mẫu ở B5; giá cổ phiếu, hệ số định giá, vốn hóa nêu ngoài đoạn ĐÃ KIỂM, không có trên trang, năm vượt nguồn, hay kèm từ chỉ tương lai trong danh sách — ở chính phần chữ có dấu hiệu giá, ở bảng hay danh sách ngay dưới nó, và dưới tiêu đề phụ có dấu hiệu giá.
- Máy không bắt được: con số có trên trang nhưng lấy nhầm ô; ở phần chữ không nói về giá, ngày tháng, số mục và số đếm thời gian («9 tháng», «66 ngày»), vì máy không coi chúng là con số (riêng chiều ngược của luật khóa có đọc số đếm thời gian); đẳng thức chứng minh dòng sửa đúng về số học nhưng không có nghĩa kế toán (phiếu in tên đẳng thức để ghế phản biện đọc); công thức của một dòng tính đúng về số học nhưng sai nghĩa hay sai phạm vi (bảng định nghĩa đưa phần này cho ghế đối chiếu số); số SUY LUẬN sai mà tình cờ trùng một số ĐÃ KIỂM khác trong hồ sơ (sau làm tròn và đổi đơn vị), hay trùng hằng số trong công thức của khóa; hai số đổi chỗ cho nhau trong một nhãn gọi nhiều khóa; số SUY LUẬN viết bằng chữ; số nguyên dưới 10 không kèm ký hiệu % («tăng 4 lần», «5 phần trăm») và năm ở đoạn không phải ĐÃ KIỂM, kể cả ở hàng tiêu đề bảng và tiêu đề phụ; số thứ tự dưới 10 đầu mục liệt kê; mã một chữ hoa với số nguyên («X55»), các tên VN30, VN100, HNX30, VNX50, SHA256, CO2, m2, m3, km2, mã băm, kỳ báo cáo («9T2026») và mã viết hoa nối gạch với số nguyên («PR-55»), máy coi là mã, không đối chiếu số trong đó (ADR-0022); chữ cái trông như chữ số viết thay cả con số («lO phần trăm»), như số viết bằng chữ; con số đứng sau «mục, điểm, bản, vòng, đợt, lớp, bước, lần thứ» (tới hai chữ số), sau «tháng» (1–12), «quý» (1–4), «ngày» (1–31), và cặp số dạng ngày tháng hay giờ hợp lệ («12/5», «9:30»), máy coi là số mục, ngày tháng, giờ («mỗi tháng 12 tỷ đồng», «đợt 63 tỷ đồng» không bị xét); con số viết trong chính nhãn (ghi chú sau dấu «;» và chữ tự do của nhãn); số viết ở phần đầu hồ sơ và ở các mục ngoài phạm vi đối chiếu (Trạng thái kiểm, Cách đọc, Bảng nguồn, Lịch sử sửa, Phiếu máy); số ĐÃ KIỂM viết trong backtick, số nhỏ và năm không được tính là số «đã lần ra» khi một đoạn SUY LUẬN nhắc lại chúng (máy báo KHÔNG GẮN KHÓA: bỏ backtick); khoảng giá viết không theo mẫu (hai ô "thấp | cao" không kèm cụm nào, hai câu rời mỗi câu một giá); lập luận sai; điều hồ sơ bỏ sót.
- Định dạng: máy chỉ nhận bộ Markdown hẹp ở B5 và bảng chữ cho phép (ADR-0022), nên cách viết làm chữ hiển thị khác chữ máy đọc bị chặn theo danh sách cho phép ở mức ký tự, không theo từng mẫu. Ba cách viết ADR-0021 ghi là chưa chặn (một dấu «~», công thức «$…$», định nghĩa liên kết trong mục liệt kê), chữ đồng dạng khác bảng mã, ký tự thay cho chữ số và ký tự trông như dấu âm đều là lỗi từ ADR-0022.
- Vạch đích của bản chấm L-09 cho PR sửa `tools/hoso/` (ADR-0022 QĐ-C6): đầu vào thuộc danh sách «Máy không bắt được» ở trên và các giới hạn của cổng giá dưới đây không là lỗi chặn; người chấm thấy một giới hạn không chấp nhận được thì ghi góp ý kèm lý do, Owner quyết bằng ADR mới. Lỗi ngoài các giới hạn này vẫn chặn.
- Cổng giá cổ phiếu không bắt:
  1. câu nêu giá tương lai mà phần chữ, dòng dẫn và tiêu đề phụ của nó không có dấu hiệu nào (không chữ «giá», không đơn vị tiền, không hệ số định giá, không dẫn nguồn G; từ ghép như «giá bán» không kèm từ chỉ cổ phiếu cũng không phải dấu hiệu), ví dụ «Cổ phiếu MAU kỳ tới về 25,40. [GIẢ ĐỊNH]», «Giá bán của MAU kỳ tới là 31,70. [GIẢ ĐỊNH]»;
  2. dấu hiệu ở một đoạn, con số ở một đoạn khác không phải bảng hay danh sách ngay dưới;
  3. ý tương lai viết bằng từ ngoài danh sách `TU_TUONG_LAI`, với số quá khứ có nguồn (hay số phần trăm, số tính kèm «lần») và năm không vượt nguồn;
  4. số viết bằng chữ, khi phần chữ không có từ chỉ cổ phiếu và không có từ chỉ tương lai;
  5. chữ không dấu ngoài bốn cụm «gia co phieu», «gia co phan», «gia cp», «thi gia» (ký tự thay cho chữ số bị bảng chữ của ADR-0022 chặn);
  6. tệp giá không đặt mã G thì nhãn dẫn nguồn giá không được nhận ra.
- Các việc máy không bắt thuộc ghế phản biện khác hãng (B7, có câu hỏi bắt buộc về giá tương lai), Owner, và hậu kiểm theo thời gian.

## 5. Việc sau khi giao (ADR-0024)

Chỉ dùng hồ sơ đã giao và đã niêm phong. Bản thử không dùng cho mục này. Trước khi ghi một câu vào sổ, mở một Issue, hay gửi Owner bất kỳ đầu ra nào dưới đây, soát chữ theo L-02 (không lời hành động, không giá cổ phiếu, không khoảng giá trị) và L-03 (ADR-0024 QĐ-N6).

### 5.1 Sổ độ phủ và bản đồ

1. Ghi sổ độ phủ của mã theo ADR-0024 QĐ-N3: thanh khoản ba tháng từ tệp G1, số báo cáo phân tích công khai theo quy tắc đếm đã ghi ở Project, nhãn ĐỘ PHỦ THẤP hay ĐỘ PHỦ KHÔNG THẤP chốt khi lập, ghi ngày lập thật. Nhãn là một dòng mô tả: phép so giữa hai nhóm đã ngừng (ADR-0026 QĐ-B2). Hai ghế đếm riêng chỉ bắt buộc ở mã đầu tiên (QĐ-N3 điểm 2); việc đó đã làm ngày 28/11/2026 cho HPG và GAS. Còn phải đếm lại hai mã đó theo quy tắc đã sửa, trước mã kế tiếp.
2. Thêm cột của mã vào bản đồ phơi nhiễm theo QĐ-N2: mỗi ô một trong sáu trạng thái, ghi bản hồ sơ và sha256; hồ sơ có Mục 9 viết trước ADR-0023 thì ô ghi CHƯA PHÂN TÍCH.

### 5.2 Vòng dự báo của sổ thành tích

1. Kiểm đầu vào: bản đã giao, sha256 khớp phiếu đã niêm phong ở Project, bản không còn lỗi gài.
2. Lập sổ câu hỏi ở Project theo QĐ-N1 điểm 1 và 2: lấy hết điều kiện sai ở Mục 11 chấm được bằng báo cáo của kỳ được hỏi; dòng Mục 9 chỉ khi điều kiện nói về kết quả của chính doanh nghiệp; thêm ứng viên bất đồng còn lại sau khi giao (5.3).
3. Gửi sổ câu hỏi cho ghế độc lập theo mẫu E của `templates/hoso/LENH_MAU.md`. Sửa câu bị ghi SỬA, gửi lại phần đó. Câu có lịch KHÔNG ĐỦ BẰNG CHỨNG thì rời vòng, ghi lý do. Khi mọi câu còn lại ĐẠT: khóa sổ. Owner mở Issue «Calendar» bằng nội dung ghế độc lập trả, lịch chính thức hay lịch suy ra đúng theo QĐ-N1 điểm 6; chờ dấu nhận của robot.
4. Ngày thu xác suất, trước `info_lock_at`: ghế phân tích trả lời mẫu D và ghi vào Project; Owner gửi mẫu D cho ChatGPT và Gemini, mỗi ghế một cuộc chat mới, và gửi prompt chuẩn `governance/CONTROL_B_PROMPT.md` cho ghế B. Chép nguyên văn mọi trả lời vào Project, kèm giờ gửi và giờ trả lời.
5. Kiểm và tổng hợp theo QĐ-N1 điểm 4 và 7: bỏ phần trả lời không hợp lệ; tính dòng A; tính sha256 của tệp nguyên văn; soát chữ; kiểm bản nháp không có sha256 hồ sơ; chạy cục bộ `parse_issue_form` và `forecast_error` của `tools/ledger_intake.py` trên bản nháp hai Issue, không sửa mã. Hai điều phải soát trên bản nháp của cả hai dòng (ADR-0026 QĐ-B7): `model_cutoff` ghi tháng cắt dữ liệu muộn nhất trong các ghế hợp lệ, dạng `YYYY-MM` (QĐ-N1 điểm 7). Ngoại lệ hẹp đối với điểm đó, chỉ khi tháng ấy trùng tháng mở Issue: máy nhận đọc `YYYY-MM` là ngày cuối tháng và từ chối ngày sau ngày tạo Issue, nên trường ghi ngày mở Issue dạng `YYYY-MM-DD`. Ngày đó là cận trên bảo thủ của ngày cắt, vì một mô hình không thể có dữ liệu sau lúc nó trả lời; nó không phải ngày cắt đo được. Tháng tự khai của từng ghế giữ nguyên trong bằng chứng trước hạn ở Project. Trước khi Owner mở Issue, ghế độc lập kiểm và ghi ở Project: tháng tự khai của từng ghế, ngày ghi vào trường, và cách suy ra ngày đó. Ghế không khai tháng cắt dữ liệu thì không được tính ở câu đó (QĐ-N1 điểm 4); `resolution_rule` chỉ dùng `comparison`, `numeric_range` hoặc `event_before_date`, không bao giờ chọn `excess_return_positive` (luật theo giá, ngoài phạm vi QĐ-N1 và trái L-02).
6. Owner mở hai Issue «Forecast», dòng A và dòng B, trong cùng một ngày giờ Việt Nam; kiểm dấu nhận của cả hai dòng.
7. Khi thấy kết quả đã công bố: ghế độc lập ghi bằng chứng công bố ngay, Owner mở Issue «Publication»; `published_at` phải có giờ và múi giờ, nguồn chỉ có ngày thì không tự điền giờ. Tới `resolve_at`: ghế độc lập phân định theo ADR-0003, Owner mở Issue «Resolution».
8. Cập nhật bảng chấm ở Project theo QĐ-N1 điểm 9, đếm trên cặp chấm được. Khoảng tin cậy tính bằng đoạn mã cục bộ ngoài kho; lưu đoạn mã, phiên bản, dữ liệu vào và kết quả. Chỉ đọc kết luận ở ba mốc của ADR-0024; ở mỗi mốc, ghế độc lập tính lại từ sổ công khai. Trước mốc không đọc kết luận. CHƯA ĐỦ BẰNG CHỨNG nghĩa là chưa kết luận được; không đọc thành «A không có lợi thế» (ADR-0026 QĐ-B3).

### 5.3 Sổ bất đồng và sổ lỗi

1. Sau khi niêm phong, xét danh sách ứng viên ghi ở B7 bước 7: bỏ ứng viên là lỗi gài, lỗi số liệu, hay điểm đã giải quyết bằng sửa hồ sơ. Ứng viên còn lại vào sổ câu hỏi của vòng kế tiếp và vào sổ bất đồng theo QĐ-N5, không ghi nhãn loại lập luận và không tính số đo theo nhãn (ADR-0026 QĐ-B2); trùng một câu đã có thì trỏ tới mã câu đó, không tạo câu thứ hai.
2. Lỗi đã sửa ở B8 ghi vào sổ lỗi đã xác minh: loại lỗi, đã có quy tắc ngăn loại lỗi đó chưa, số ngày từ lúc bắt tới lúc sửa.

### 5.4 Hậu kiểm theo sự kiện và bản đồ

1. Ghế phân tích giữ ở Project lịch theo dõi của từng mã, lập từ hạn công bố báo cáo tài chính theo quy định và từ dòng lịch của vòng dự báo. Trong tuần sau mỗi hạn, Owner mở một phiên Project và gõ «hậu kiểm theo sự kiện <MÃ>»; Owner thấy báo cáo mới sớm hơn thì gõ ngay.
2. Ghế phân tích chạy B8 bước 5 cho báo cáo mới, đúng chữ của bản đã giao; ghi ngày công bố, ngày phát hiện, ngày gửi. Trong 7 ngày kể từ ngày phát hiện, gửi Owner danh sách điều kiện đã chạm, chưa chạm, chưa chấm được. Phát hiện sau ngày công bố quá 14 ngày thì ghi «phát hiện muộn». Lần chạy theo sự kiện không thay lần chạy định kỳ: điều kiện đã chấm đủ nguồn và đúng kỳ giữ kết quả, ghi ngày đã chấm; điều kiện còn CHƯA CHẤM ĐƯỢC hay CHƯA RÕ được chấm lại ở ngày xem lại đã niêm phong (ADR-0023 QĐ-T6).
3. Dòng nào của Mục 9 ghi ĐỔI hay ĐỔI MỘT PHẦN: trong 7 ngày báo Owner các mã khác có ô CÓ PHƠI NHIỄM với cùng biến trên bản đồ, đề nghị xem lại sớm; mỗi cặp biến và mã là một cảnh báo, ghi ngày báo. Khi ghi nguyên nhân TRONG BẢNG ở bất kỳ hậu kiểm nào, ghi tên dòng là nguyên nhân. Ở hậu kiểm kế tiếp của mã được báo, chấm cảnh báo theo năm bước của QĐ-N2 điểm 5 (HỮU ÍCH, KHÔNG HỮU ÍCH, KHÔNG XÁC NHẬN, CHƯA ĐỦ BẰNG CHỨNG); ghi cả trường hợp BỎ SÓT.

### 5.5 Sổ kết quả (ADR-0026 QĐ-B4)

1. Sổ kết quả là một tài liệu ở Project, mỗi hồ sơ đã niêm phong một khối. Mỗi hồ sơ trong tập của cổng (mục 6) cũng có một khối, kể cả FPT bản 2. Bản đóng của FPT bản 2 là bản cuối có phiếu máy ĐẠT và sha256 ghi ở Project ngày 24/11/2026; từ ngày gộp ADR-0026 không sửa bản đó. Câu mở đầu mục 5 («Chỉ dùng hồ sơ đã giao và đã niêm phong») không chặn khối này. Khóa của một dòng gồm bốn phần: mã; sha256 của bản đã giao; mã điều kiện (giả thuyết của Mục 11, hay tên biến của dòng Mục 9); kỳ báo cáo mà điều kiện nêu. Giả thuyết có hơn một điều kiện sai thì mã điều kiện kèm số thứ tự của điều kiện. Điều kiện nêu nhiều kỳ thì mỗi kỳ một khóa.
2. Sau mỗi lần hậu kiểm, định kỳ hay theo sự kiện, mỗi khóa đã chấm thêm một dòng lịch sử: nguyên văn điều kiện trong bản đã giao; lần hậu kiểm (hồ sơ nào, báo cáo nào, định kỳ hay theo sự kiện); ngày chấm; phán quyết đúng như B8 bước 5; mã tệp và trang dùng để chấm. Không xóa dòng lịch sử. Trạng thái hiện hành của một khóa là lần chấm hợp lệ mới nhất, theo mục 5.4 bước 2: phán quyết đã đủ nguồn và đúng kỳ thì giữ; CHƯA RÕ hay CHƯA CHẤM ĐƯỢC thì được chấm lại ở lần sau. Dòng còn bất đồng sau lượt đối chiếu có trạng thái hiện hành theo bước 4. Một lần hậu kiểm là một lần chạy B8 bước 5 của một hồ sơ trên một báo cáo tài chính (quý, bán niên hay năm); chạy lại trên cùng báo cáo đó, kể cả khi lần đầu là theo sự kiện và lần sau là định kỳ, không phải một lần hậu kiểm mới.
3. Giả thuyết ghi SAI: ghi đúng một loại nguyên nhân chính, xét về phía hồ sơ. Chọn theo thứ tự dưới đây và dừng ở loại đầu tiên đủ căn cứ:
   1. LỖI DỮ KIỆN: hồ sơ ghi sai số hay sai trích dẫn so với tệp gốc đã ghim; hoặc bỏ sót một dữ kiện có trong tệp đã ghim; hoặc không ghim một tài liệu thuộc danh sách tối thiểu của B2 đã công bố trước ngày giao mà không ghi thiếu nó ở danh sách CHƯA BIẾT. Lỗi đó phải liên quan tới việc giả thuyết sai.
   2. GIẢ ĐỊNH SAI: không có lỗi dữ kiện liên quan; một câu mang nhãn GIẢ ĐỊNH mà giả thuyết dựa vào đã không đúng theo tài liệu ra sau.
   3. LỖI SUY LUẬN: dữ kiện và giả định mà giả thuyết dựa vào đều đứng; bước suy ra ở một câu mang nhãn SUY LUẬN không đứng.
   4. KHÔNG LỖI, ĐÃ NÊU: không chứng minh được lỗi liên quan nào thuộc ba loại trên; cơ chế làm giả thuyết sai (khoản mục nào của báo cáo, đổi theo chiều nào) đã được hồ sơ nêu đúng ở Mục 9, Mục 11, kết quả điểm soi hay danh sách CHƯA BIẾT. Trùng tên chủ đề không đủ.
   5. KHÔNG LỖI, BIẾN CỐ MỚI: không chứng minh được lỗi liên quan nào; hồ sơ không nêu cơ chế đó; bằng chứng về điều làm giả thuyết sai phát sinh hay lần đầu được công bố sau ngày giao.
   6. CHƯA RÕ: không đủ căn cứ để chọn một trong năm loại trên.

   Luật đi kèm:

   - Một lỗi là «liên quan» khi câu có lỗi là căn cứ mà Mục 11 nêu cho giả thuyết đó, hoặc là câu mà căn cứ đó dựa vào. Chỉ ghi một loại LỖI khi chỉ ra được: câu nào của hồ sơ, sai ở đâu so với tài liệu nào, và vì sao lỗi đó liên quan. Lỗi có thật nhưng không liên quan thì ghi vào sổ lỗi đã xác minh, không là nguyên nhân.
   - Có nhiều lỗi liên quan thì nguyên nhân chính là lỗi gốc theo thứ tự dữ kiện, giả định, suy luận; các lỗi còn lại ghi ở phần giải trình là lỗi phụ.
   - Dữ kiện có trong tệp đã ghim mà hồ sơ bỏ sót, sau ngày giao được công bố lại: là LỖI DỮ KIỆN, không là BIẾN CỐ MỚI.
   - Bằng chứng đã công bố trước ngày giao mà không có trong bộ tệp đã ghim: không là BIẾN CỐ MỚI. Xét theo thứ tự loại 1 tới loại 4; không loại nào đủ căn cứ thì ghi CHƯA RÕ kèm chữ «có trước ngày giao, ngoài bộ tệp ghim», và kiến trúc sư xét có cần thêm loại tài liệu đó vào B2 không.
   - Yếu tố hồ sơ đã nêu nhưng nêu sai cơ chế hay sai chiều: không là ĐÃ NÊU và không là BIẾN CỐ MỚI. Xét theo loại 1 tới 3; không loại nào trong ba loại đó đủ căn cứ thì ghi CHƯA RÕ.
   - Hồ sơ giữ ba giả thuyết cạnh tranh, nên luôn có giả thuyết bị loại. Giả thuyết cạnh tranh bị loại mà không có lỗi liên quan đã xác minh vẫn chọn loại theo đúng thứ tự trên: loại 4 khi cơ chế đúng đã được nêu; loại 5 khi hồ sơ không nêu cơ chế đó và bằng chứng phát sinh hay lần đầu được công bố sau ngày giao; còn lại CHƯA RÕ. Ghi thêm chữ «giả thuyết cạnh tranh bị loại». Không tính là lỗi của hồ sơ.
   - Hai việc xảy ra cùng lúc chưa phải là nguyên nhân. Nguyên nhân chỉ do doanh nghiệp tự nêu thì ghi «nguyên nhân do doanh nghiệp nêu» kèm mã tệp và trang (ADR-0023 QĐ-T6).
   - Trường này không thay và không trộn với các trường của ADR-0023 QĐ-T6 và ADR-0025 QĐ-L1.
4. Căn cứ và đối chiếu. Mỗi phân loại nguyên nhân ghi kèm: nguyên văn điều kiện đã niêm phong; nguồn trước ngày giao (mã tệp, trang của tệp đã ghim) và nguồn sau ngày giao (mã tệp, trang của báo cáo mới); lý do chọn loại; các lỗi phụ. Ở mỗi lần hậu kiểm, một ghế khác hãng Anthropic đối chiếu từng phán quyết và từng loại nguyên nhân với báo cáo gốc; ghế phân tích soạn lệnh, Owner gửi. Mỗi dòng ghi một trạng thái đối chiếu: ĐỒNG Ý, KHÔNG ĐỒNG Ý hay CHƯA KIỂM, kèm ghế đối chiếu và ngày. Dòng KHÔNG ĐỒNG Ý: ghi nguyên văn ý của cả hai ghế; ghế phân tích mở lại trang gốc. Ghế phân tích nhận ý của ghế đối chiếu thì ghi một dòng lịch sử mới theo ý đó, trạng thái đối chiếu ĐỒNG Ý. Còn bất đồng thì cả hai ý được báo lên Owner, và trạng thái hiện hành của dòng như sau: bất đồng về phán quyết của một giả thuyết thì phán quyết là CHƯA RÕ; bất đồng về trạng thái của một dòng Mục 9 thì trạng thái là CHƯA CHẤM ĐƯỢC; hai trường hợp này ghi kèm chữ «bất đồng giữa hai ghế», và không tính là ĐÚNG, SAI hay một trạng thái đổi ở bất kỳ bảng đếm nào, cũng không tính cho điều e của cổng bằng chứng (ADR-0026 QĐ-B1 điểm 3). Hai ghế cùng ghi SAI mà chỉ bất đồng về loại nguyên nhân thì phán quyết SAI giữ, loại nguyên nhân là CHƯA RÕ. Dòng CHƯA KIỂM không được tính là kết quả lỗi hay không lỗi đã xác minh. Hạn 7 ngày gửi Owner danh sách của ADR-0024 QĐ-N4 điểm 2 không chờ lượt đối chiếu này: dòng chưa đối chiếu được gửi với trạng thái CHƯA KIỂM.
5. Số đếm, ghi sau mỗi lần hậu kiểm. Mỗi bảng ghi ba số: số mới (khóa lần đầu có phán quyết ở lần này), số chấm lại (khóa đã có dòng, nay đổi trạng thái), và tổng lũy kế, trong đó mỗi khóa tính một lần theo trạng thái hiện hành.
   - Bảng 1: giả thuyết theo phán quyết mà B8 bước 5 ghi cho giả thuyết đó: ĐÚNG, SAI, CHƯA RÕ. ADR-0026 không đổi cách B8 bước 5 ra phán quyết.
   - Bảng 2: riêng các giả thuyết SAI theo sáu loại nguyên nhân chính; ghi riêng số dòng CHƯA KIỂM.
   - Bảng 3: dòng Mục 9 theo ĐỔI, ĐỔI MỘT PHẦN, GIỮ NGUYÊN, CHƯA CHẤM ĐƯỢC (ADR-0023 QĐ-T6); ghi riêng số hồ sơ không có bảng Mục 9 (KHÔNG ÁP DỤNG).
   - Ghi riêng, không gộp vào ba bảng trên: số lần «không báo»; số lần KHÔNG LƯỜNG TRƯỚC; số lỗi ghế khác hãng bắt được ở B7 của mỗi hồ sơ, theo sổ lỗi đã xác minh; lỗi gài của mỗi hồ sơ, ghế nào bắt được, ghế nào không.
   - Số phút Owner tự ước, tách hai số: phút đọc hồ sơ, và phút làm việc cho từng năng lực (ADR-0024 QĐ-N7 điểm 2, ADR-0025). Owner không khai thì ghi CHƯA GHI, không ghi 0.
6. Cách đọc. Sổ kết quả là thước chẩn đoán vận hành: nó cho biết hồ sơ sai ở đâu và vì sao. Nó không phải bằng chứng thống kê về năng lực của mô hình hay của dự án, không đo hiệu quả đầu tư, không đo hồ sơ có ích cho Owner tới đâu, và không thay việc Owner nghiệm thu. Không cộng các số đếm thành một điểm. Không dùng sổ kết quả để xếp hạng mã. Không đặt đích giảm số giả thuyết SAI. Trước khi gửi Owner, soát chữ theo L-02 và L-03 như mọi đầu ra của mục 5.

## 6. Cổng bằng chứng (ADR-0026 QĐ-B1)

- Tới ngày cổng mở: không nhận việc thêm năng lực mới cho hồ sơ mã hay cho việc đo, không mở phép thử tay mới, không bắt đầu gói Pha 2 nào của ADR-0024 hay ADR-0025. Chỉ làm các việc trong danh sách đóng NL-01 tới NL-11 ở ADR-0026 QĐ-B1 điểm 2. Việc không có trong danh sách thì chờ cổng mở, hoặc cần một ADR mới do Owner gộp.
- Tập hậu kiểm của cổng là ba hồ sơ đã giao tới ngày 28/11/2026, mỗi hồ sơ có phiếu máy ĐẠT với sha256 ghi ở Project: FPT bản 2 (giao ngày 24/11/2026; bản được chấm là bản cuối có phiếu máy ĐẠT ghi ở Project ngày đó), HPG bản 2 (26/11/2026), GAS bản 1 sửa 1 (27/11/2026). Kỳ đầu tiên là báo cáo tài chính quý IV/2026 của từng doanh nghiệp. Tập này không đổi. Trước lần hậu kiểm đầu tiên của tập, ghế phân tích lập ở Project «danh sách chấm của cổng» và niêm phong bằng sha256: với từng hồ sơ, mã, bản, sha256 của bản đã giao, kỳ, và nguyên văn mọi điều kiện gốc (từng điều kiện sai ở Mục 11; từng điều kiện đổi trạng thái ở Mục 9 nếu bản đó có bảng của ADR-0023). Trường mà bản đó không có thì ghi KHÔNG ÁP DỤNG. Không viết thêm điều kiện, ngưỡng hay trường nào cho bản đã giao.
- Cổng chỉ mở khi đủ cả năm điều ở ADR-0026 QĐ-B1 điểm 3, xét trên toàn tập, tính tới ngày xét:
  - a. mỗi điều kiện trong danh sách có một dòng ở sổ kết quả cho lần hậu kiểm theo báo cáo quý IV/2026: một phán quyết theo B8 bước 5, hoặc CHƯA RÕ (giả thuyết) hay CHƯA CHẤM ĐƯỢC (dòng Mục 9) kèm lý do và tài liệu còn thiếu; không điều kiện nào bị bỏ;
  - b. mỗi giả thuyết có trạng thái hiện hành SAI có loại nguyên nhân chính kèm căn cứ (mục 5.5 bước 3 và 4);
  - c. một ghế khác hãng Anthropic đã đối chiếu danh sách với ba bản đã giao (đủ điều kiện, đúng chữ); mọi dòng của tập trong sổ kết quả đã được đối chiếu theo mục 5.5 bước 4: không còn dòng CHƯA KIỂM, và mọi dòng KHÔNG ĐỒNG Ý đã được xử lý theo bước đó;
  - d. kiến trúc sư đã báo Owner danh sách lỗi của hồ sơ lộ ra ở các lần hậu kiểm của tập, kể cả khi danh sách rỗng;
  - e. mỗi hồ sơ trong tập có ít nhất một giả thuyết của Mục 11 mà trạng thái hiện hành là ĐÚNG hoặc SAI, với trạng thái đối chiếu ĐỒNG Ý.
- Sau lần hậu kiểm theo báo cáo quý IV/2026, điều e chưa đủ ở một hồ sơ thì cổng chưa mở. Ở mỗi lần hậu kiểm kế tiếp của hồ sơ đó, định kỳ hay theo sự kiện, dòng mới được ghi và đối chiếu như mọi dòng, rồi xét lại cả năm điều trên toàn tập. Tới hết ngày 30/04/2027 cổng chưa mở, vì điều e hay vì điều khác: cổng vẫn đóng, và kiến trúc sư báo Owner theo điều kiện hoàn tác 1 của ADR-0026. Không mốc ngày nào tự mở cổng.
- Kiến trúc sư ghi ở Project ngày đủ từng điều, bằng chứng của từng điều, và ngày cổng mở. Cổng mở vào ngày kiến trúc sư báo Owner rằng đủ cả năm điều, kèm các bằng chứng đó. Chưa có bản ghi ngày mở cổng thì cổng chưa mở.
- Sau khi cổng mở, một năng lực mới chỉ được đề xuất bằng ADR khi một phép thử tay của nó đã đạt theo phiếu thử và ý đó đã qua chín phép lọc của ADR-0026 QĐ-B1 điểm 6; vẫn cần lệnh Owner.
- Một việc chỉ được gọi là phép thử tay khi nó là thử quy trình: viết thử, ngoài kho, một phần của hồ sơ hay một bước của quy trình trên tệp gốc đã ghim; giả thuyết trong bản thử là giả thuyết về chỉ tiêu của doanh nghiệp, hậu kiểm như B8 bước 5; việc đó không chấm điểm một mô hình hay một ghế, không so ghế này với ghế khác, không thử một chiến lược. Kết quả của phép thử tay không được dẫn làm bằng chứng về năng lực của LLM hay của dự án. Việc mà L-05 gọi là «kiểm định hay chấm điểm năng lực của LLM» và việc mà L-06 gọi là «lần thử chiến lược/giả thuyết» không làm dưới tên phép thử tay: chỉ làm theo đúng L-05 và L-06 bằng đường đã có của kho, hoặc không làm. Chưa rõ thuộc loại nào thì dừng và hỏi Owner.
- Phiếu thử, lập và niêm phong sha256 ở Project trước khi bắt đầu một phép thử tay: mục đích; dữ liệu được dùng; tiêu chí đạt và tiêu chí không đạt; cách chấm; hạn; ghế chấm, khác hãng với ghế viết. Sau khi niêm phong không sửa tiêu chí. Bản thử được niêm phong trước sự kiện và chấm bằng tài liệu ra sau; hậu kiểm của bản thử được một ghế khác hãng đối chiếu và ghi riêng, không vào sổ kết quả của hồ sơ. Kết quả không đạt được lưu kèm lý do. Làm lại là một phép thử mới, có phiếu mới.
