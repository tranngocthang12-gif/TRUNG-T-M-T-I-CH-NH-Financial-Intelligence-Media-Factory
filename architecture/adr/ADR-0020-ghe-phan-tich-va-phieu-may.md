# ADR-0020: Ghế phân tích của dự án và phiếu máy cho hồ sơ mã

- Ngày: 2026-11-24
- Trạng thái: ACCEPTED 24/11/2026 theo lệnh Owner, hiệu lực khi Owner gộp PR này.
- Người đề xuất: Claude Project TTC (Anthropic), ghế kiến trúc sư trưởng. Chép vào kho: phiên Claude Code (Anthropic).
- Người chấm: theo L-09, ghi trong thân PR.
- Owner duyệt: lệnh trong chat Project ngày 24/11/2026, 00:48 và 00:54 giờ Việt Nam; xác nhận bằng việc gộp PR này.

## Bối cảnh

- ADR-0019 đặt ba sản phẩm (hồ sơ mã, bản phản biện, phiếu kỷ luật) và ba lớp kiểm (QĐ-P9). Lớp 1 ghi "Máy: mỗi số và câu trích khớp tài liệu gốc đã ghim", nhưng QĐ-P14 xếp việc viết máy kiểm sau khi Owner dùng xong hồ sơ đầu tiên.
- Hồ sơ đầu tiên (một mã trong VN30, bản 1 ngày 24/11/2026, nằm ở nơi riêng tư của Owner) được viết tay từ 21 tệp gốc đã ghim. Sáu bài học:
  1. Máy nhận dạng chữ đọc sai một chữ số ở vài ô. Số sai vẫn "có trên trang máy đọc", nên đối chiếu trích dẫn không bắt được. Phép trừ của chính hàng đó thì bắt được.
  2. Một trang giải trình của báo cáo quý bị bỏ sót vì chỉ đọc các trang có bảng chính.
  3. Ghế phản biện trả lời từ tài liệu trên mạng vì tệp hồ sơ không được đính kèm. Không có gì chứng minh ghế đó đã đọc tệp.
  4. Hai ghế khác hãng hết hạn mức trong cùng một đêm.
  5. Lỗi gài cố ý nằm ở chỗ ghế phản biện không được giao đối chiếu, nên vòng đó không đo được gì.
  6. Một mã sha256 trong bảng nguồn bị chép tay sai một ký tự.
- Lệnh Owner ngày 24/11/2026, 00:48: làm xong kiến trúc trước; việc phân tích mã cổ phiếu về sau do Claude của kiến trúc làm, không phải Claude ngoài dự án. Owner giao kiến trúc sư chọn cách làm.

## Quyết định

### QĐ-H1 — Ghế phân tích

- Ghế phân tích là một phiên Claude trong Project TTC (Anthropic) làm việc theo `docs/QUY_TRINH_HO_SO_MA.md` tại `main` mới nhất. Phiên bắt đầu bằng chỉ dẫn Project ở `docs/CHI_DAN_PROJECT.md`; Owner dán tệp đó vào ô chỉ dẫn của Project.
- Một bản phân tích chỉ được gọi là **hồ sơ mã của dự án** khi đi kèm phiếu máy ĐẠT (QĐ-H3) do bộ công cụ `tools/hoso/` của kho in ra. Bản phân tích không có phiếu ĐẠT, dù do Claude nào viết, không phải sản phẩm của dự án.
- Ghế phân tích và ghế kiến trúc sư cùng hãng. Vì vậy: sửa `tools/hoso/` hay quy trình phải qua PR và L-09, không sửa trong lúc đang làm một hồ sơ; phản biện và đối chiếu số do ghế khác hãng làm (QĐ-P7, QĐ-H5).
- Ghế phân tích không chọn mã thay Owner, không nêu hành động với cổ phiếu, không nêu khoảng giá trị (L-02, QĐ-P13), không hỏi và không ghi số vốn hay vị thế của Owner (L-03).

### QĐ-H2 — Quy trình tám bước

`docs/QUY_TRINH_HO_SO_MA.md` là quy trình có hiệu lực: B1 nhận mã; B2 tìm và tải tệp gốc; B3 nhận tệp, ghim sha256, tách văn bản từng trang; B4 lập sổ số liệu và soát; B5 viết hồ sơ; B6 phiếu máy; B7 phản biện và đối chiếu số; B8 sửa, giao Owner, hậu kiểm. Sửa quy trình bằng PR thường, có L-09.

### QĐ-H3 — Phiếu máy

`tools/hoso/phieu_may.py` chạy năm phép kiểm và in một phiếu:

| # | Kiểm | Đạt khi |
|---|---|---|
| 1 | Danh mục nguồn | Mỗi tệp gốc còn đúng sha256 đã ghim; đủ trang văn bản |
| 2 | Sổ số liệu | Mỗi dòng gốc có trên trang đã ghi; mọi quan hệ trong `quan_he.csv` đúng; có đẳng thức đúng cho cả ba báo cáo (`cdkt`, `kqkd`, `lctt`); chỗ ghế phân tích ghi khác máy đọc phải có ghi chú và hiện trên phiếu |
| 3 | Soát bảng | Mọi hàng "a − b lệch c đúng một chữ số" trên trang hồ sơ có dùng đã được ghế phân tích kết luận trong sổ |
| 4 | Trích dẫn | Mỗi con số trong đoạn ĐÃ KIỂM có trên trang đã ghi, hoặc là một dòng của sổ, hoặc tính được từ các số đã lần ra cùng đoạn; không đoạn nào có số mà thiếu nhãn; ngoại lệ phải có lý do và hiện trên phiếu |
| 5 | Luật và khung | Không cụm từ L-02 cấm; đủ mười hai mục; mục 8 trống; mục 11 đủ ba giả thuyết, điều kiện sai, ngày xem lại; đủ mười lăm điểm soi; kết bằng danh sách CHƯA BIẾT; bảng nguồn khớp sha256 |

- Phiếu ghi sha256 của hồ sơ và commit của công cụ. Phiếu không có giờ chạy: cùng đầu vào, cùng công cụ thì ra cùng phiếu. Ai có thư mục mã cũng chạy lại được. Phiếu là bằng chứng chạy lại được, không phải chữ ký.
- Phiếu ĐẠT nghĩa là con số lần ra được và hồ sơ đúng khung. Phiếu không nói lập luận đúng.
- Mục 8 bị khóa bằng máy. Khi Owner sửa L-02, việc mở khóa đi bằng một ADR và một PR sửa `tools/hoso/kiem_luat.py`.

### QĐ-H4 — Số trong hồ sơ đi qua sổ

- Mọi tỷ lệ, hiệu, tổng do ghế phân tích tự tính được ghi thành dòng tính trong `so_lieu.csv` và máy tính lại. Không tính nhẩm trong lúc viết.
- Số ghế phân tích kết luận là máy đọc sai được ghi cùng chuỗi máy đọc, giá trị sửa và phép tính chứng minh. Không sửa chuỗi máy đọc.
- Đọc hết mọi trang của báo cáo quý mới nhất và phần thuyết minh của báo cáo năm mới nhất.

### QĐ-H5 — Phản biện và đối chiếu số

- Bản gửi ghế khác hãng mang một mã nhận tệp. Bản trả lời không chép lại được mã thì coi như ghế đó chưa đọc tệp.
- Lỗi gài cố ý (QĐ-P9) phải là lỗi mà phép đối chiếu số bắt được: `tools/hoso/gai_loi.py` từ chối lỗi gài nào mà máy đối chiếu không báo thêm đúng một con số. Bảng đối chiếu gửi đi phải có dòng chứa chỗ gài.
- Ghế hết hạn mức thì chuyển sang ghế khác hãng còn lại trong ChatGPT (OpenAI), Gemini (Google), Grok (xAI). Không dùng Claude cho hai việc này.
- Sửa theo phản biện tối đa ba vòng. Chưa hội tụ thì dừng và báo Owner.

### QĐ-H6 — Công khai và riêng tư

- Kho công khai giữ: công cụ, quy trình, mẫu, bộ test, và một ví dụ số liệu bịa (`templates/hoso/vi_du/`).
- Thư mục mã (tệp gốc, văn bản từng trang, sổ số liệu, hồ sơ, phiếu máy, bản phản biện, tệp niêm phong lỗi gài) nằm ở nơi riêng tư của Owner. Không PR nào chứa chúng (QĐ-P13, L-03, L-04).
- Bộ mẫu kỷ luật trống vào kho ở `templates/ky_luat/` (QĐ-P8). Bản đã điền không vào kho.

### QĐ-H7 — Sửa thứ tự của QĐ-P14

- Theo lệnh Owner ngày 24/11/2026: hai việc của bước 3 ở QĐ-P14 — chốt mẫu vào kho và viết máy kiểm trích dẫn — làm ngay bằng PR này, không chờ Owner dùng xong hồ sơ đầu tiên. Việc thứ ba (xét xóa phần mã đã ngừng) vẫn để sau.
- Thước đo ở QĐ-P14 của ADR-0019 giữ nguyên chữ và nguyên tiêu chí. Phiếu máy ĐẠT là cổng kỹ thuật của sản phẩm theo ADR này: một bản phân tích chưa có phiếu ĐẠT thì chưa được gọi là hồ sơ mã của dự án (QĐ-H1), nên chưa được đem ra đo theo QĐ-P14.
- Hồ sơ đầu tiên bản 1 không bị thu hồi. Owner vẫn đọc được. Ghế phân tích làm bản 2 theo quy trình này.

### QĐ-H8 — "Kiến trúc xong" là gì

Hai mốc, tách nhau:

- **Dựng xong** khi đủ hai điều: (1) ADR này, `tools/hoso/`, `docs/QUY_TRINH_HO_SO_MA.md` và bộ test nằm trên `main`, CI xanh; (2) Owner đã dán `docs/CHI_DAN_PROJECT.md` vào chỉ dẫn của Project. Từ mốc này, mọi việc phân tích mã do ghế phân tích làm theo quy trình.
- **Nghiệm thu** khi đủ thêm hai điều: (3) hồ sơ đầu tiên bản 2 đạt phiếu máy; (4) một hồ sơ cho mã thứ hai được làm từ B1 tới B6 mà không phải sửa `tools/hoso/`. Nếu phải sửa: sửa bằng PR, rồi tính lại điều (4) với mã kế tiếp.

Sau mốc dựng xong, thêm việc mới vào kiến trúc cần lệnh Owner. Sửa lỗi của `tools/hoso/` lộ ra khi làm hồ sơ không tính là việc mới.

## Trạng thái từng quyết định

| QĐ | Trạng thái | Owner | Ngày |
|---|---|---|---|
| QĐ-H1 tới QĐ-H8 | ACCEPTED theo lệnh Owner giao kiến trúc sư chọn cách làm; Owner đổi được trước khi gộp | Owner (lệnh 00:48 và 00:54) | 24/11/2026 |

## Lý do (bằng chứng, số đo)

Chạy thử bộ công cụ ngày 24/11/2026 trên thư mục mã của hồ sơ đầu tiên (21 tệp gốc, 406 con số trong hồ sơ bản 1), ở máy phân tích, ngoài kho:

- **Soát bảng:** 79 hàng so sánh khớp phép tính; 6 hàng nghi máy đọc sai. Bốn hàng nằm trên cùng một trang giải trình và cả bốn là lỗi máy đọc thật: hai lỗi ghế phản biện khác hãng đã bắt, hai lỗi chưa ai bắt.
- **Sổ số liệu:** 46 dòng, 16 quan hệ. Chép đúng theo máy đọc thì 5 quan hệ sai, trong đó một lỗi mới ở báo cáo lưu chuyển tiền tệ năm. Sau khi ghi giá trị sửa kèm phép tính chứng minh: 16 trên 16 đúng.
- **Trích dẫn:** 200 con số có trên trang đã ghi; 41 tính được từ số cùng đoạn; 8 khớp sổ; 43 là số nhắc lại; 71 thuộc đoạn SUY LUẬN hoặc GIẢ ĐỊNH, máy không kiểm. Còn 32 con số dán nhãn ĐÃ KIỂM mà máy không lần ra — phần lớn là số tự tính hoặc ghi thiếu trang — và 11 con số không có nhãn.
- **Lỗi gài:** ở bản có lỗi gài, máy báo thêm đúng một con số, đúng dòng đã gài.
- **Luật và khung:** một dòng phạm bộ mẫu L-02 (câu phủ định ở đầu hồ sơ chứa cụm cấm); một mã sha256 chép sai một ký tự.
- Kết luận: hồ sơ bản 1 viết tay CHƯA ĐẠT phiếu máy (45 lỗi). Các lỗi này có làm đổi nhận định nào của hồ sơ hay không thì chưa kiểm xong; đó là việc của bản 2 (QĐ-H7).
- Ví dụ số liệu bịa trong kho đạt phiếu máy; `tests/test_hoso.py` thử từng phép kiểm bằng cách làm hỏng ví dụ đó.

Điểm yếu đã biết:

- Máy không bắt được con số có trên trang nhưng lấy nhầm ô, không kiểm lập luận, không biết hồ sơ bỏ sót gì.
- Phép "tính được từ số cùng đoạn" có thể cho qua nhầm một con số nhỏ trùng hợp. Phiếu in số lượng theo từng đường lần ra để người đọc biết.
- Bộ mẫu L-02 kiểm cứng: câu phủ định có cụm cấm cũng bị bắt. Cách xử lý là đổi cách viết.
- Phiếu là văn bản. Giá trị của nó ở chỗ chạy lại được, không ở chỗ không giả được.
- Công cụ mới thử trên một mã, là doanh nghiệp phi tài chính. Ngân hàng, bảo hiểm, chứng khoán có mẫu báo cáo khác; chưa thử.
- Ghế viết và ghế kiến trúc cùng hãng; phản biện khác hãng vẫn là lớp kiểm không thay được.

## Không đổi

- L-01…L-10 và `governance/LAWS.md` không sửa. PR này không chạm `governance/`, `ledger/`, `paper/`, `research/`, `engine/`, `data/`.
- `autonomous_order_execution: false` và `live_trading_enabled: false` giữ nguyên. Không mở API trả phí. Công cụ chỉ dùng thư viện chuẩn của Python; chương trình đọc PDF chỉ cần ở máy phân tích, CI không cần.
- ADR-0019 giữ nguyên chữ. ADR này chỉ sửa thứ tự thi công ở QĐ-P14 (QĐ-H7) và làm rõ vai Claude Project ở QĐ-P15 (QĐ-H1).
- `tools/laws_checks.py` không sửa. `tools/hoso/kiem_luat.py` dùng lại bộ mẫu L-02 của tệp đó.

## Điều kiện hoàn tác

1. Sau hai hồ sơ, nếu ở cả hai phiếu máy chỉ đạt được khi ghi ngoại lệ cho hơn một phần mười số con số ĐÃ KIỂM, hoặc cả hai lần máy đối chiếu không bắt được lỗi gài: kiến trúc sư báo Owner trong 7 ngày. Owner chọn bằng một ADR mới: sửa công cụ, hoặc bỏ điều kiện phiếu máy và quay về kiểm tay cộng phản biện khác hãng như ADR-0019.
2. Tới hết ngày 31/01/2027 chưa đạt điều (3) của QĐ-H8: xử lý theo điều kiện hoàn tác 1 của ADR-0019.
3. Hoàn tác không cần khôi phục gì: PR này chỉ thêm tệp mới và vài dòng chỉ đường; gỡ là xóa `tools/hoso/`, `tests/test_hoso.py`, `templates/hoso/`, `templates/ky_luat/`, hai tệp trong `docs/` và một tên trong `tests.yml`.

## Ảnh hưởng tới ARCHITECTURE.md

- Dòng trạng thái đầu tệp: thêm ADR-0020.
- Mục "Phạm vi hiệu lực từ ADR-0019": thêm một đoạn ngắn sau bảng, trỏ tới ADR-0020 và `docs/QUY_TRINH_HO_SO_MA.md`.
- Chữ của §0–§10 giữ nguyên.
