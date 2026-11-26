# Quy trình làm một hồ sơ mã (ADR-0019, ADR-0020, ADR-0021)

Tệp này là việc phải làm theo thứ tự của **ghế phân tích**. Ghế phân tích là một phiên Claude trong Project TTC, đã đọc tệp này và ADR-0019, ADR-0020 ở `main` mới nhất. Sản phẩm chỉ được gọi là "hồ sơ mã của dự án" khi có phiếu máy ĐẠT đi kèm.

Hồ sơ là phân tích cho Owner đọc. Hồ sơ không nêu hành động nào với cổ phiếu. Owner tự quyết định và tự đặt lệnh.

## 1. Chỗ để đồ

| Thứ | Ở đâu | Vì sao |
|---|---|---|
| Công cụ, quy trình, mẫu, ví dụ số liệu bịa | Kho này: `tools/hoso/`, `docs/`, `templates/hoso/`, `templates/ky_luat/` | Công khai, có test |
| **Thư mục mã**: tệp gốc, văn bản từng trang, sổ số liệu, hồ sơ, phiếu máy, bản phản biện | Máy của Owner, ví dụ `Downloads\TTC_HO_SO\<MÃ>\`; bản đọc để trong Project | Riêng tư (ADR-0019 QĐ-P13, L-03, L-04) |
| Bản quy tắc riêng, phiếu trước quyết định, nhật ký của Owner | Chỉ ở chỗ Owner | L-03. Ghế phân tích không hỏi và không ghi các con số này |

Không đưa thư mục mã, hồ sơ thật hay tệp gốc vào kho. Không mở PR chứa chúng.

Thư mục mã có dạng:

```
<MÃ>/
  goc/                 tệp gốc đã tải (PDF, CSV…), không sửa
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

### B5. Viết hồ sơ

- Chép khung từ `templates/hoso/vi_du/HO_SO_MAU.md`: đầu hồ sơ, "Cách đọc", "Một trang", Mục 1 tới Mục 12, "Kết quả 15 điểm soi", "Danh sách CHƯA BIẾT", "Bảng nguồn", "Lịch sử sửa".
- Chỉ dùng bộ định dạng của hồ sơ mẫu: tiêu đề `#` sát lề (tiêu đề `##` giữ đúng tên của khung, không thêm chữ), đoạn chữ sát lề, bảng bắt đầu bằng `|`, mục liệt kê `- ` hay `1. ` (mục con thụt 2, 4… dấu cách), chữ đậm `**…**`, mã `` `…` `` tách khỏi chữ bằng dấu cách hay dấu câu, dấu `_` chỉ trong khóa sổ nằm trong nhãn (`[SUY LUẬN, sổ số liệu: dt_tang_25]`) hay tên tệp trong mã. Không dùng `_` hay `*` để nhấn mạnh, thẻ hay thực thể HTML, liên kết, trích dẫn `>`, khối mã, tiêu đề gạch chân, dòng thụt lề không phải mục liệt kê, dấu `\`, tab hay dấu cách đặc biệt. Máy báo mọi dòng ngoài bộ này (`kiem_luat.kiem_dinh_dang`).
- Dấu định dạng không được đổi con số. Chữ đậm và mã mở, đóng trên cùng một dòng, không có dấu cách sát mép trong, và bọc trọn con số, kể cả dấu âm, ngoặc và dấu %: viết «**-36,4%**», không viết dấu trừ ngoài rồi số trong mã hay trong chữ đậm, không in đậm một phần con số, không dán chữ đậm vào chữ đứng trước. Trong mã không dùng dấu `*`. Dấu âm viết bằng «-» hay «−» sát con số; gạch dài «—» và các ký tự gạch ngang khác không được dính liền trước chữ số. Máy đọc số trên chữ người đọc thấy (bỏ dấu `**` và dấu backtick, không chèn gì), và báo lỗi định dạng khi cách đọc đó khác cách đọc lúc thay dấu định dạng bằng dấu cách.
- Số viết theo kiểu Việt Nam: dấu chấm tách hàng nghìn, dấu phẩy là phần lẻ («1.234,5»). Cụm chữ số máy không đọc được theo kiểu này («63.4», «1,234,567», «31.12.2025», «3.1») là lỗi ở đoạn SUY LUẬN, đoạn không nhãn, hàng tiêu đề bảng và tiêu đề phụ; ở đoạn GIẢ ĐỊNH, CHƯA BIẾT máy chỉ đếm. Ngày tháng viết theo dạng máy nhận: «ngày 31 tháng 12 năm 2025», «31/12/2025», «12/2025», «31/12», «tháng 12», «quý 4», «năm 2025»; dạng khác («31-12-2025») máy đọc thành con số.
- Mỗi câu có số phải kết bằng một nhãn: `[ĐÃ KIỂM D1 tr.12]`, `[SUY LUẬN …]`, `[GIẢ ĐỊNH]`, `[CHƯA BIẾT]`. Nhãn phủ phần chữ đứng trước nó, tới nhãn liền trước. Bảng nhận nhãn đứng đầu dòng ngay sau nó, hoặc nhãn cuối của đoạn ngay trước nó; giữa bảng và nhãn chỉ được có dòng trống. Một hàng bảng chỉ mang một nhãn. Hàng tiêu đề của bảng và tiêu đề phụ (`###` trở xuống) không mang nhãn: không viết số liệu ở đó (năm, ngày tháng, số dưới 10 thì được; tiêu đề phụ không đánh số nhiều tầng kiểu «3.1»).
- Số đứng đầu một mục liệt kê («12. …») chỉ là số thứ tự khi nó dưới 10 hoặc danh sách được đánh đúng 1, 2, …, n liền nhau (chỉ cách nhau bằng dòng trống); ngoài ra nó là con số như mọi con số khác. «63. » ở giữa đoạn hay trong ô bảng luôn là con số.
- Số trong đoạn ĐÃ KIỂM phải có trên trang đã ghi, hoặc là một dòng gốc của sổ, hoặc tính được từ các số cùng đoạn. Số nguyên nhỏ, năm và số trong dấu backtick cũng vậy, và không đi đường tính. Số tự tính mà không có số gốc đứng cạnh thì đưa vào sổ thành dòng tính và dán nhãn SUY LUẬN.
- Nhãn SUY LUẬN gọi tên khóa sổ (ADR-0021 QĐ-K1): `[SUY LUẬN, sổ số liệu: khóa_a, khóa_b]`. Dãy khóa cùng phần chữ viết `[SUY LUẬN, sổ số liệu: kl_tb_t06 tới kl_tb_t11]`. Ghi chú đặt sau dấu `;`: `[SUY LUẬN, sổ số liệu: dt_tang_25; căn cứ thêm phai_thu_tang_25]`; cụm «sổ số liệu:» phải đứng trước dấu `;` đầu tiên, đứng sau thì máy coi là ghi chú. Mỗi lần nhãn xuất hiện là một phạm vi riêng, máy nhận theo vị trí của nhãn chứ không theo chữ của nhãn: một nhãn cùng chữ ở chỗ khác không gộp vào. Nhãn phủ cả bảng thì các hàng dữ liệu của bảng thuộc phạm vi của đúng lần xuất hiện đó (cộng phần đoạn dẫn kết bằng nhãn đó, khi nhãn đứng cuối đoạn ngay trên bảng); hàng bảng có nhãn trong ô là phạm vi riêng. Nhãn gọi khóa phải phủ ít nhất một chữ. Máy kiểm hai chiều:
  - mỗi con số trong đoạn SUY LUẬN, kể cả số viết trong backtick, phải khớp giá trị của một khóa nhãn gọi tên, hoặc là hằng số viết nguyên văn trong công thức của khóa đó (ví dụ 49 trong `g2_cp_luu_hanh * 49 / 100`; câu viết «nhân 1,1» thì công thức viết `* 1.1`, không viết `* 11 / 10`), hoặc trùng một số ĐÃ KIỂM đã lần ra trong hồ sơ. Đoạn SUY LUẬN không gọi khóa nào thì mọi con số phải là số ĐÃ KIỂM nhắc lại: không tính nhẩm;
  - phạm vi có số liệu thì mỗi khóa nhãn gọi tên phải hiện ra ở ít nhất một con số của chính phạm vi đó. Năm, ngày tháng («tháng 12 năm 2025»), số nhỏ dưới 10, số thứ tự thật đầu mục liệt kê và số thứ tự trong bảng không làm phạm vi «có số liệu»; số đếm thời gian từ 10 trở lên («95 ngày», «12 tháng») thì có. Một con số không đứng thay cho hai khóa làm tròn ra hai số khác nhau. Khóa chỉ làm căn cứ cho một câu định tính («đều âm», «khoảng một nửa») thì đặt sau dấu `;`.
  - Ngưỡng của điều kiện sai ở Mục 11 («tăng trưởng dưới 15%») là lựa chọn của ghế phân tích, không phải số tính: viết dưới nhãn `[GIẢ ĐỊNH]`.
- Ngay sau đầu hồ sơ là mục «Trạng thái kiểm» (ADR-0021 QĐ-K3), bốn dòng: `- **Phiếu máy:**`, `- **Đối chiếu số khác hãng:**`, `- **Phản biện khác hãng:**`, `- **Owner tự mở ba số:**`. Lúc viết, ba dòng sau ghi «chưa làm». Mục này nằm ngoài phạm vi đối chiếu trích dẫn; máy kiểm mỗi tên mở đầu đúng một mục liệt kê riêng. Mỗi tiêu đề cấp hai của khung, kể cả «Trạng thái kiểm», chỉ xuất hiện một lần.
- Mục 8 để trống cho tới khi Owner sửa L-02: thân mục chỉ có đúng câu của hồ sơ mẫu, «**Chưa viết.** Theo ADR-0019 QĐ-P13, mục này chỉ viết sau khi Owner sửa L-02.». Máy bắt mọi chữ, số hay bảng thêm vào.
- Giá cổ phiếu, hệ số định giá (P/E, P/B, P/S, EV/EBITDA) và vốn hóa chỉ được nêu dưới dạng số quá khứ có nguồn: trong đoạn ĐÃ KIỂM, mọi chữ số có trên trang đã ghi (hoặc là dòng gốc của sổ), năm không vượt năm lớn nhất của trang đó, không kèm từ chỉ tương lai hay tín hiệu (dự báo, dự kiến, kỳ vọng, mục tiêu, sẽ, có thể, kịch bản, nếu, giả định, năm sau, ngắn hạn, nên, chờ, … tới, hỗ trợ, kháng cự…). Máy nhận ra "ngữ cảnh giá" qua: số mang đơn vị giá (đồng, nghìn đồng, VND, đ, "/cp", "30 nghìn mỗi cp"…); chữ "giá" (giá vốn, giá bán, đánh giá, "giá trị" thường… chỉ được bỏ qua khi phần chữ không có từ chỉ cổ phiếu: cổ phiếu, cổ phần, cp, "giá MAU"); hệ số định giá hay vốn hóa; nhãn ĐÃ KIỂM dẫn nguồn G. Từ tương lai đi cùng từ chỉ cổ phiếu là lỗi kể cả khi không có con số. Tiêu đề, hàng tiêu đề bảng và bảng nguồn không mang nhãn, nên không được nêu giá kèm số (năm đứng riêng thì được). Danh sách đầy đủ ở docstring `tools/hoso/kiem_luat.py`.
- Bảng hay danh sách đặt ngay dưới một câu có chữ «giá», và mọi đoạn dưới một tiêu đề phụ có chữ «giá», sẽ bị xét như ngữ cảnh giá. Trong phần chữ nói về giá, mọi chữ số đều phải có trên trang nguồn: số thứ tự chỉ được bỏ qua khi cột đầu tên là #, STT, TT, Số TT hoặc Số thứ tự và đánh đúng 1, 2, …, n; «điểm 30», «12 tháng», «25/4» đều là con số.
- Không viết khoảng giá trị hay giá mục tiêu ở bất kỳ mục nào khác, dù nhãn là gì. Máy bắt hai số nối bằng gạch ngang hoặc "đến/tới" kèm đơn vị tiền (đồng, nghìn đồng, VND, đ; trong bảng tính cả đơn vị ở tiêu đề cột), và các cụm "khoảng giá", "vùng giá", "mức giá", "giá mục tiêu", "giá trị nội tại", "giá trị một/mỗi cổ phiếu" đi với số. Chỉ giá quá khứ trong đoạn ĐÃ KIỂM, mọi số có trên trang đã ghi, mới được qua.
- Mục 10 chỉ mô tả giá và khối lượng.
- Mục 11: ba giả thuyết H1 (tốt), H2 (xấu), H0 (không có gì đặc biệt). Mỗi giả thuyết có điều kiện làm nó sai. Có ngày xem lại.
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
5. Chép nguyên văn bản trả lời vào `phan_bien/`. Ghi vào tệp niêm phong: ghế nào nhận được tệp, ghế nào bắt được lỗi gài.

### B8. Sửa, giao Owner, hậu kiểm

1. Với từng điểm ghế khác hãng nêu: mở trang gốc kiểm lại. Đúng thì sửa hồ sơ và sổ; không đúng thì ghi lý do. Ghi vào "Lịch sử sửa". Viết lại mục «Trạng thái kiểm»: ghế nào đối chiếu số và kết quả (số dòng KHỚP, LỆCH, có bắt được lỗi gài không); ghế nào phản biện; tệp gốc nào mỗi ghế không mở được; ý nào ở «Một trang» chưa được ghế khác hãng nào đối chiếu.
2. Chạy lại B6 cho bản đã sửa. Chạy `python tools/hoso/gai_loi.py kiem --ho-so … --niem-phong …` để chắc bản Owner không còn lỗi gài.
3. Giao Owner ba thứ: hồ sơ, phiếu máy ĐẠT, bản phản biện. Owner tự mở ba con số mà phiếu máy chọn (ADR-0021 QĐ-K4, thay cách chọn «ba con số bất kỳ» của QĐ-P9); Owner muốn mở thêm số nào cũng được.
4. Niêm phong bản đã giao (ADR-0021 QĐ-K5): ghế phân tích ghi phiếu máy ĐẠT, có sha256 của hồ sơ, vào tài liệu của Project ngay khi giao. Từ lúc đó không sửa bản đã giao; muốn sửa thì làm bản mới, có phiếu mới.
5. Tới ngày xem lại ở Mục 11: mở đúng bản đã giao, kiểm sha256 của tệp khớp sha256 trên phiếu đã ghi vào Project. Lấy báo cáo mới, làm lại từ B2 cho phần mới. Với từng giả thuyết, chép nguyên văn điều kiện sai của bản đã giao, rồi ghi ĐÚNG, SAI hoặc CHƯA RÕ kèm bằng chứng có nhãn. Không chấm theo chữ của một bản sửa sau.
6. Sửa quá ba vòng phản biện mà chưa hội tụ: dừng, báo Owner.

## 3. Khi nào dừng và báo Owner

- sha256 tệp gốc lệch giữa hai máy.
- Thiếu chương trình đọc PDF.
- Có hơn mười con số trên trang mà máy không đọc được sau khi đã đọc lại.
- Hai ghế khác hãng cùng không nhận được tệp, hoặc cùng hết hạn mức.
- Việc được giao đòi nêu hành động với cổ phiếu, khoảng giá trị, hoặc số vốn của Owner.

## 4. Giới hạn của máy

- Máy bắt được: con số không có trên trang đã ghi (kể cả số nhỏ, năm, số trong backtick ở đoạn ĐÃ KIỂM), hoặc sai dấu; trang ghi trong nhãn không có thật; phép tính không khớp; số SUY LUẬN không khớp khóa nhãn gọi tên, khóa gọi tên mà không hiện số, khóa không có trong sổ, nhãn gọi khóa mà không phủ chữ nào, số liệu ở hàng tiêu đề bảng hay tiêu đề phụ, hàng bảng có hơn một nhãn, con số viết kiểu Anh («63.4») ở đoạn SUY LUẬN hay đoạn không nhãn, dấu định dạng cắt ngang con số, tiêu đề cấp hai lặp (ADR-0021); dòng sửa trong sổ không gần chuỗi máy đọc hoặc không có đẳng thức cộng trừ chứng minh; tệp gốc bị đổi; tệp trang bị sửa, thêm hay mất; hồ sơ sai khung; cụm từ L-02 cấm; khoảng giá viết theo các mẫu ở B5; giá cổ phiếu, hệ số định giá, vốn hóa nêu ngoài đoạn ĐÃ KIỂM, không có trên trang, năm vượt nguồn, hay kèm từ chỉ tương lai trong danh sách — ở chính phần chữ có dấu hiệu giá, ở bảng hay danh sách ngay dưới nó, và dưới tiêu đề phụ có dấu hiệu giá.
- Máy không bắt được: con số có trên trang nhưng lấy nhầm ô; ở phần chữ không nói về giá, ngày tháng, số mục và số đếm thời gian («9 tháng», «66 ngày»), vì máy không coi chúng là con số (riêng chiều ngược của luật khóa có đọc số đếm thời gian); đẳng thức chứng minh dòng sửa đúng về số học nhưng không có nghĩa kế toán (phiếu in tên đẳng thức để ghế phản biện đọc); công thức của một dòng tính đúng về số học nhưng sai nghĩa hay sai phạm vi (bảng định nghĩa đưa phần này cho ghế đối chiếu số); số SUY LUẬN sai mà tình cờ trùng một số ĐÃ KIỂM khác trong hồ sơ (sau làm tròn và đổi đơn vị), hay trùng hằng số trong công thức của khóa; hai số đổi chỗ cho nhau trong một nhãn gọi nhiều khóa; số SUY LUẬN viết bằng chữ; số nguyên dưới 10 không kèm ký hiệu % («tăng 4 lần», «5 phần trăm») và năm ở đoạn không phải ĐÃ KIỂM, kể cả ở hàng tiêu đề bảng và tiêu đề phụ; số thứ tự dưới 10 đầu mục liệt kê; con số dính liền sau một chữ cái («tăng63,4%»), máy coi là mã như «VN30»; dấu trừ viết cách con số một dấu cách («- 36,4»), máy đọc là số không dấu; con số viết trong chính nhãn (ghi chú sau dấu «;» và chữ tự do của nhãn); số viết ở phần đầu hồ sơ và ở các mục ngoài phạm vi đối chiếu (Trạng thái kiểm, Cách đọc, Bảng nguồn, Lịch sử sửa, Phiếu máy); con số viết kiểu Anh («1,234.5») ở đoạn ĐÃ KIỂM, máy bỏ qua như trước ADR-0021; khoảng giá viết không theo mẫu (hai ô "thấp | cao" không kèm cụm nào, hai câu rời mỗi câu một giá); lập luận sai; điều hồ sơ bỏ sót.
- Định dạng: máy chỉ nhận bộ Markdown hẹp ở B5, nên cách viết làm chữ hiển thị khác chữ máy đọc bị chặn theo loại, không theo từng mẫu. Chữ đồng dạng khác bảng mã (ví dụ chữ Kirin trông như chữ Latin), ký tự thay cho chữ số, và ký tự trông như dấu âm nhưng không thuộc nhóm gạch ngang của Unicode vẫn thuộc giới hạn 5 dưới đây.
- Cổng giá cổ phiếu không bắt:
  1. câu nêu giá tương lai mà phần chữ, dòng dẫn và tiêu đề phụ của nó không có dấu hiệu nào (không chữ «giá», không đơn vị tiền, không hệ số định giá, không dẫn nguồn G; từ ghép như «giá bán» không kèm từ chỉ cổ phiếu cũng không phải dấu hiệu), ví dụ «Cổ phiếu MAU kỳ tới về 25,40. [GIẢ ĐỊNH]», «Giá bán của MAU kỳ tới là 31,70. [GIẢ ĐỊNH]»;
  2. dấu hiệu ở một đoạn, con số ở một đoạn khác không phải bảng hay danh sách ngay dưới;
  3. ý tương lai viết bằng từ ngoài danh sách `TU_TUONG_LAI`, với số quá khứ có nguồn (hay số phần trăm, số tính kèm «lần») và năm không vượt nguồn;
  4. số viết bằng chữ, khi phần chữ không có từ chỉ cổ phiếu và không có từ chỉ tương lai;
  5. chữ không dấu ngoài bốn cụm «gia co phieu», «gia co phan», «gia cp», «thi gia»; ký tự thay cho chữ số;
  6. tệp giá không đặt mã G thì nhãn dẫn nguồn giá không được nhận ra.
- Các việc máy không bắt thuộc ghế phản biện khác hãng (B7, có câu hỏi bắt buộc về giá tương lai), Owner, và hậu kiểm theo thời gian.
