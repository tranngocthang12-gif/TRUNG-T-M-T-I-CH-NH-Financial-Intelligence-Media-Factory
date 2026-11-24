# Quy trình làm một hồ sơ mã (ADR-0019, ADR-0020)

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
  ngoai_le.csv         (nếu cần) con số máy không lần ra được, kèm lý do, nguồn và trang
  HO_SO_<MÃ>_<ngày>.md
  PHIEU_MAY_HO_SO_<MÃ>_<ngày>.txt
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
- Ghế tìm nguồn (Grok) lập bảng đường dẫn. Cowork tải về máy Owner theo mẫu lệnh ở `templates/hoso/LENH_MAU.md` và báo sha256 từng tệp.
- Thiếu tệp nào thì ghi vào danh sách CHƯA BIẾT. Không thay bằng số nhớ lại.

### B3. Nhận tệp

```
python tools/hoso/nhan_tep.py nhan --thu-muc <TM> --ma-nguon <TM>/ma_nguon.csv
```

- Đối chiếu sha256 máy in ra với sha256 Cowork báo. Lệch một tệp thì dừng.
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

Lý do có bước này: ở hồ sơ đầu tiên máy đọc sai năm con số trên hai trang. Số sai vẫn "có trên trang" nên phép đối chiếu trích dẫn không bắt được. Chỉ phép tính của chính hàng đó bắt được.

### B5. Viết hồ sơ

- Chép khung từ `templates/hoso/vi_du/HO_SO_MAU.md`: đầu hồ sơ, "Cách đọc", "Một trang", Mục 1 tới Mục 12, "Kết quả 15 điểm soi", "Danh sách CHƯA BIẾT", "Bảng nguồn", "Lịch sử sửa".
- Mỗi câu có số phải kết bằng một nhãn: `[ĐÃ KIỂM D1 tr.12]`, `[SUY LUẬN …]`, `[GIẢ ĐỊNH]`, `[CHƯA BIẾT]`.
- Số trong đoạn ĐÃ KIỂM phải có trên trang đã ghi, hoặc là một dòng của sổ, hoặc tính được từ các số cùng đoạn. Số tự tính mà không có số gốc đứng cạnh thì đưa vào sổ thành dòng tính và dán nhãn SUY LUẬN.
- Mục 8 để trống cho tới khi Owner sửa L-02: thân mục chỉ có đúng câu của hồ sơ mẫu, «**Chưa viết.** Theo ADR-0019 QĐ-P13, mục này chỉ viết sau khi Owner sửa L-02.». Máy bắt mọi chữ, số hay bảng thêm vào.
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
- Chỉ dùng `ngoai_le.csv` khi con số thật sự có trên trang mà máy không đọc được, sau khi đã đọc lại trang đó. Cột: `so,ngu_canh,ly_do,nguon,trang`. Máy chỉ kiểm địa chỉ của ngoại lệ: nguồn có trong `nguon.csv`, trang có trong thư mục `trang/`, và cặp nguồn, trang nằm trong nhãn ĐÃ KIỂM của đoạn chứa con số. Máy không kiểm được con số có trên trang, vì lý do ngoại lệ chính là máy đọc không ra. Ngoại lệ không dùng cho đoạn không có nhãn hay đoạn SUY LUẬN.
- Mỗi ngoại lệ hiện trên phiếu kèm nguồn và trang, cùng dòng tổng «NGOẠI LỆ n/N số ĐÃ KIỂM = x%»; trên 10% thì phiếu in CẢNH BÁO. Ghế phản biện phải đối chiếu mọi số NGOẠI LỆ với trang gốc (B7).
- Phiếu ĐẠT nghĩa là con số lần ra được và hồ sơ đúng khung. Phiếu không nói lập luận đúng.

### B7. Phản biện và đối chiếu số (ghế khác hãng)

1. Gài một lỗi cố ý vào bản gửi đi:

```
python tools/hoso/gai_loi.py tao --thu-muc <TM> --ho-so <TM>/HO_SO_<MÃ>_<ngày>.md --tim "<số đúng>" --thay "<số sai>"
```

   Máy chỉ nhận lỗi gài mà phép đối chiếu số bắt được. Tệp `…_LOI_GAI.md` là niêm phong: không gửi ghế nào.
2. Gửi `…_BAN_PHAN_BIEN.md` cùng đường dẫn tệp gốc cho hai ghế khác hãng Anthropic, theo mẫu ở `templates/hoso/LENH_MAU.md`: một ghế viết bản phản biện bốn phần (QĐ-P7), một ghế đối chiếu số.
3. Bản trả lời phải mở đầu bằng **mã nhận tệp** in ở đầu bản phản biện. Không có mã: coi như ghế đó chưa đọc tệp, gửi lại.
4. Ghế nào hết hạn mức thì chuyển sang ghế khác hãng còn lại (ChatGPT, Gemini, Grok). Không dùng Claude cho bước này.
5. Chép nguyên văn bản trả lời vào `phan_bien/`. Ghi vào tệp niêm phong: ghế nào nhận được tệp, ghế nào bắt được lỗi gài.

### B8. Sửa, giao Owner, hậu kiểm

1. Với từng điểm ghế khác hãng nêu: mở trang gốc kiểm lại. Đúng thì sửa hồ sơ và sổ; không đúng thì ghi lý do. Ghi vào "Lịch sử sửa".
2. Chạy lại B6 cho bản đã sửa. Chạy `python tools/hoso/gai_loi.py kiem --ho-so … --niem-phong …` để chắc bản Owner không còn lỗi gài.
3. Giao Owner ba thứ: hồ sơ, phiếu máy ĐẠT, bản phản biện. Nhắc Owner tự mở ba con số bất kỳ trong tệp gốc (QĐ-P9).
4. Tới ngày xem lại ở Mục 11: lấy báo cáo mới, làm lại từ B2 cho phần mới, ghi ĐÚNG, SAI hoặc CHƯA RÕ cho từng giả thuyết.
5. Sửa quá ba vòng phản biện mà chưa hội tụ: dừng, báo Owner.

## 3. Khi nào dừng và báo Owner

- sha256 tệp gốc lệch giữa hai máy.
- Thiếu chương trình đọc PDF.
- Phiếu máy không thể ĐẠT nếu không viết ngoại lệ cho hơn mười con số.
- Hai ghế khác hãng cùng không nhận được tệp, hoặc cùng hết hạn mức.
- Việc được giao đòi nêu hành động với cổ phiếu, khoảng giá trị, hoặc số vốn của Owner.

## 4. Giới hạn của máy

- Máy bắt được: con số không có trên trang đã ghi, hoặc sai dấu; trang ghi trong nhãn không có thật; phép tính không khớp; tệp gốc bị đổi; tệp trang bị sửa, thêm hay mất; hồ sơ sai khung; cụm từ L-02 cấm; khoảng giá viết theo các mẫu ở B5.
- Máy không bắt được: con số có trên trang nhưng lấy nhầm ô; con số NGOẠI LỆ có thật trên trang hay không (máy chỉ kiểm nguồn và trang của nó); khoảng giá viết không theo mẫu (hai ô "thấp | cao" không kèm cụm nào, hai câu rời mỗi câu một giá); lập luận sai; điều hồ sơ bỏ sót. Các việc này thuộc ghế phản biện khác hãng, Owner, và hậu kiểm theo thời gian.
