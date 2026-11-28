# ADR-0026: Cổng bằng chứng, thu gọn phần đo và sổ kết quả

- Ngày: 2026-11-28
- Trạng thái: ACCEPTED 28/11/2026 theo lệnh Owner, hiệu lực khi Owner gộp PR này.
- Người đề xuất: Claude Project TTC (Anthropic), ghế kiến trúc sư trưởng. Chép vào kho: phiên Claude Code (Anthropic).
- Hội đồng AI về kế hoạch, ngày 28/11/2026: ChatGPT (OpenAI), Gemini (Google), Grok (xAI), mỗi ghế hai tin, làm độc lập; tin 1 lấy ý riêng của ghế trước khi ghế thấy kế hoạch. Bản tổng hợp: tài liệu Project `claude/TONG_HOP_HOI_DONG_CAI_TO_20261128.md`.
- Phản biện bản nháp: vòng 1, ChatGPT (OpenAI), ngày 28/11/2026: SỬA TRƯỚC, 18 lỗi chặn C01–C18, 8 góp ý không chặn. Vòng 2, Grok (xAI), ngày 29/11/2026, theo lệnh Owner giao vòng này cho Grok: SỬA TRƯỚC; 17 lỗi của vòng 1 đã sửa, C08 còn một chỗ; lỗi chặn mới C19–C25; góp ý G09–G16. Vòng 3, Grok (xAI), ngày 29/11/2026, vòng cuối: SỬA TRƯỚC; tám lỗi của vòng 2 đã sửa; ba lỗi chặn mới C26–C28, cả ba ở chữ mới của lần sửa sau vòng 2; góp ý G17–G19. Đã hết ba vòng. Owner quyết ngày 29/11/2026: sửa đúng ba lỗi C26–C28 theo cách ghế phản biện ghi rồi đi tiếp, không có vòng thứ tư. Bản này là bản đó; ba góp ý G17–G19 không đổi chữ. Nguyên văn ba vòng ở tài liệu Project `claude/PHAN_BIEN_ADR0026_CHATGPT_V1_20261128.md`, `claude/PHAN_BIEN_ADR0026_GROK_V2_20261129.md` và `claude/PHAN_BIEN_ADR0026_GROK_V3_20261129.md`. Người chấm PR: ghế khác hãng Anthropic, ghi trong thân PR (L-09).
- Owner duyệt: lệnh trong chat Project ngày 28/11/2026, 19:29 giờ Việt Nam, «lên một kế hoạch cải tổ kiến trúc, sửa chữa, hoặc loại bỏ phần yếu, thừa. phát huy tinh hoa. bổ xung đột phá. giao bạn toàn quyền quyết định về kiến trúc. tôi nghiệm thu. nhưng trước khi xây tiếp tục cần phản biện hội đồng AI»; và 20:34, «việc tiếp theo bạn toàn quyền quyết theo kế hoạch kiến trúc sau phản biện và tư vấn. tôi chỉ nghiệm thu dự án sau khi xong»; xác nhận bằng việc gộp PR này.

## Bối cảnh

- Tại `main` `820ffb1` ngày 28/11/2026: ADR-0019 tới ADR-0025 được gộp trong sáu ngày (23/11 tới 28/11). Ba hồ sơ mã đã giao, mỗi hồ sơ có phiếu máy ĐẠT với sha256 ghi ở Project: FPT bản 2, HPG bản 2, GAS bản 1 sửa 1. Chưa có lần hậu kiểm nào; lần đầu rơi vào khi có báo cáo quý IV/2026. Sổ dự báo có 16 dòng cũ, chưa dòng nào được phân định; vòng đầu của ADR-0024 mới khóa năm câu trên hai cụm.
- ADR-0019 đã ghi «phần giấy tờ đã lớn hơn phần sản phẩm». ADR-0024 nhắc lại điều đó. Hai ADR sau cùng vẫn thêm tám năng lực trước khi vòng dữ liệu, bằng chứng, bài học chạy trọn một lần.
- Kiến trúc sư tự đánh giá ngày 28/11/2026 (tài liệu Project `claude/DANH_GIA_KIEN_TRUC_VA_PHAN_BIEN_20261128.md`) và lập kế hoạch cải tổ (`claude/KE_HOACH_CAI_TO_KIEN_TRUC_20261128.md`). Owner yêu cầu hội đồng AI phản biện trước khi xây tiếp.
- Hội đồng, ba ghế, cùng nói: đích «đột phá chưa từng có trên thế giới» không phải đích đúng; dự án thiếu bằng chứng, không thiếu ý tưởng; ngừng mở rộng và làm hậu kiểm đầu tiên. Cả ba ghế cùng nói: với ba tới năm mã, phép so điểm Brier của ADR-0024 không ra kết luận thống kê trong hai năm.
- Vòng dự báo đầu cho thấy ba điều kiện sai ở Mục 11 của hai hồ sơ đã giao không vào được sổ câu hỏi vì thiếu ngưỡng hay mốc so sánh.

## Quyết định

### QĐ-B1 — Cổng bằng chứng

1. Từ ngày gộp PR này tới ngày cổng mở: không gộp ADR thêm năng lực mới cho hồ sơ mã hay cho việc đo; không mở phép thử tay mới (điểm 4 và 5); không bắt đầu gói Pha 2 nào của ADR-0024 hay ADR-0025. Chỉ các việc ở điểm 2 được làm.
2. Danh sách đóng các việc vẫn làm trong thời gian đó. Việc không có trong danh sách thì chờ cổng mở, hoặc cần một ADR mới do Owner gộp.

   | Mã | Việc | Căn cứ | Đầu ra | Hạn |
   |---|---|---|---|---|
   | NL-01 | Hồ sơ mã theo lệnh Owner, từ B1 tới B8, gồm mọi bước ADR-0020 tới ADR-0025 đã quy định cho hồ sơ và hai chỗ sửa của QĐ-B5 | ADR-0019 QĐ-P5; ADR-0020 | Hồ sơ, phiếu máy ĐẠT, bản phản biện | Theo lệnh |
   | NL-02 | Hậu kiểm định kỳ và theo sự kiện; ghi sổ kết quả | Quy trình B8 bước 5; ADR-0024 QĐ-N4; QĐ-B4 | Sổ kết quả ở Project | Khi báo cáo ra |
   | NL-03 | Vòng dự báo của sổ thành tích, Pha 1 làm tay: sổ câu hỏi, lịch, Issue, bằng chứng công bố, phân định, bảng chấm | ADR-0024 QĐ-N1; QĐ-N7 điểm 3 | Dòng sổ dự báo; bảng chấm ở Project | Theo lịch đã ghim |
   | NL-04 | Phân định 16 dự báo cũ | ADR-0019 QĐ-P12 | Issue «Resolution» | 04/12, 11/12 và 20/12/2026 |
   | NL-05 | Các việc làm tay còn lại của Pha 1 ở ADR-0024: bản đồ phơi nhiễm; nhãn độ phủ, gồm việc đếm lại hai mã theo quy tắc đã sửa; danh sách ứng viên bất đồng và sổ bất đồng; sổ lỗi đã xác minh | ADR-0024 QĐ-N2; QĐ-N3 điểm 1 tới 3; QĐ-N5 điểm 1, 2, 4 và 6; QĐ-B2 | Tài liệu ở Project | Mốc vận hành của ADR-0024, chậm nhất 31/03/2027 |
   | NL-06 | Thử các ca biên của ADR-0025 trước hồ sơ đầu tiên áp ADR đó. Đây là thi hành một quyết định đã gộp, không phải phép thử tay mới | ADR-0025 QĐ-L5 điểm 5 | Bản ghi ở Project, không tính vào số đo | Trước hồ sơ kế tiếp |
   | NL-07 | Bản thử ngoài sách, đã quyết ngày 28/11/2026 trước ADR này: ba cách viết (lời hứa; thuế; vật lý–kế toán) trên các hồ sơ đã giao. Theo luật của điểm 4 và 5 | Quyết định của kiến trúc sư theo lệnh Owner 13:58 ngày 28/11/2026; tài liệu Project `claude/QUYET_DINH_L02_VA_PHEP_THU_NGOAI_SACH_20261128.md` | Một bản thử, niêm phong sha256 ở Project | Niêm phong trước 31/12/2026; cách nào chưa xong thì bỏ, không lùi hạn |
   | NL-08 | Công cụ hậu kiểm `tools/hoso/hau_kiem.py` | ADR-0021 QĐ-K5; ADR-0024 QĐ-N7 điểm 5 | Một PR qua chấm L-09 | Gộp trước 15/01/2027 |
   | NL-09 | Trình kiểm thứ hai, làm trọn: ADR, bản kiểm do ghế khác hãng viết, PR, chấm L-09, gộp | ADR-0021 QĐ-K6, đã kích hoạt ngày 27/11/2026 | ADR và PR | Sau NL-08 |
   | NL-10 | Sửa lỗi của `tools/hoso/` lộ ra khi làm hồ sơ | ADR-0020 QĐ-H8 | PR qua chấm L-09 | Khi lỗi lộ ra |
   | NL-11 | PR chỉ sửa chữ để giấy tờ khớp các ADR đang hiệu lực, không thêm quy định mới | ADR mà giấy tờ phải khớp; L-09 | PR qua chấm L-09 | Không có |

   Ngày duyệt của mỗi việc là ngày của căn cứ ghi ở cột «Căn cứ». Kiến trúc sư giữ ở Project một bản của bảng này kèm trạng thái từng việc.

   Các gói Pha 2 có mã của ADR-0024 (QĐ-N7 điểm 5, phần «sau cổng»; QĐ-N2 điểm 7) và của ADR-0025 (QĐ-L2 điểm 6) không nằm trong danh sách. Mỗi gói chỉ bắt đầu khi đã đủ cổng riêng ghi ở ADR của nó và cổng bằng chứng đã mở. Chữ của các cổng riêng giữ nguyên.
3. Tập hậu kiểm của cổng là ba hồ sơ đã giao tới ngày 28/11/2026, mỗi hồ sơ có phiếu máy ĐẠT với sha256 ghi ở Project: FPT bản 2 (giao ngày 24/11/2026), HPG bản 2 (26/11/2026), GAS bản 1 sửa 1 (27/11/2026). FPT bản 2 và HPG bản 2 là «hồ sơ thứ nhất bản 2» và «hồ sơ thứ hai bản 2» của ADR-0021 QĐ-K7. Bối cảnh của ADR-0024 chỉ nêu HPG bản 2 và GAS bản 1 sửa 1; ADR này đưa thêm FPT bản 2 vào tập của cổng và không sửa chữ ADR-0024. FPT bản 2 giao trước khi ADR-0021 QĐ-K5 đặt luật niêm phong; bản được chấm là bản cuối có phiếu máy ĐẠT ghi ở Project ngày 24/11/2026. Kỳ đầu tiên là báo cáo tài chính quý IV/2026 của từng doanh nghiệp. Tập này không đổi; hồ sơ giao sau ngày 28/11/2026 không thêm vào và không thay hồ sơ nào trong tập.

   Trước lần hậu kiểm đầu tiên của tập, ghế phân tích lập ở Project «danh sách chấm của cổng» và niêm phong bằng sha256. Với từng hồ sơ, danh sách ghi: mã, bản, sha256 của bản đã giao, kỳ, và nguyên văn mọi điều kiện gốc của bản đó, gồm từng điều kiện sai ở Mục 11 và từng điều kiện đổi trạng thái ở Mục 9 nếu bản đó có bảng của ADR-0023. Trường mà bản đó không có thì ghi KHÔNG ÁP DỤNG. Không viết thêm điều kiện, ngưỡng hay trường nào cho bản đã giao (ADR-0021 QĐ-K5, ADR-0023 QĐ-T8, ADR-0025 QĐ-L5 điểm 2).

   Cổng mở khi đủ cả năm điều, xét trên toàn tập, tính tới ngày xét:

   - a. Mỗi điều kiện trong danh sách có một dòng ở sổ kết quả (QĐ-B4) cho lần hậu kiểm theo báo cáo quý IV/2026: một phán quyết theo B8 bước 5, hoặc CHƯA RÕ (giả thuyết) hay CHƯA CHẤM ĐƯỢC (dòng Mục 9) kèm lý do và tài liệu còn thiếu. Không điều kiện nào bị bỏ.
   - b. Mỗi giả thuyết có trạng thái hiện hành SAI có loại nguyên nhân chính theo QĐ-B4 điểm 2, kèm căn cứ theo QĐ-B4 điểm 3.
   - c. Một ghế khác hãng Anthropic đã đối chiếu danh sách với ba bản đã giao (đủ điều kiện, đúng chữ). Mọi dòng của tập trong sổ kết quả đã được đối chiếu theo QĐ-B4 điểm 3: không còn dòng CHƯA KIỂM, và mọi dòng KHÔNG ĐỒNG Ý đã được xử lý theo điểm đó.
   - d. Kiến trúc sư đã báo Owner danh sách lỗi của hồ sơ lộ ra ở các lần hậu kiểm của tập, kể cả khi danh sách rỗng.
   - e. Mỗi hồ sơ trong tập có ít nhất một giả thuyết của Mục 11 mà trạng thái hiện hành là ĐÚNG hoặc SAI, với trạng thái đối chiếu ĐỒNG Ý.

   Sau lần hậu kiểm theo báo cáo quý IV/2026, điều e chưa đủ ở một hồ sơ thì cổng chưa mở. Ở mỗi lần hậu kiểm kế tiếp của hồ sơ đó, định kỳ hay theo sự kiện (QĐ-B4 điểm 1), dòng mới được ghi và đối chiếu như mọi dòng, rồi xét lại cả năm điều trên toàn tập. Tới hết ngày 30/04/2027 cổng chưa mở, vì điều e hay vì điều khác: cổng vẫn đóng, và kiến trúc sư báo Owner theo điều kiện hoàn tác 1. Không mốc ngày nào tự mở cổng.

   Kiến trúc sư ghi ở Project ngày đủ từng điều, bằng chứng của từng điều, và ngày cổng mở. Cổng mở vào ngày kiến trúc sư báo Owner rằng đủ cả năm điều, kèm các bằng chứng đó.
4. Sau khi cổng mở, một năng lực mới chỉ được đề xuất bằng ADR khi một phép thử tay của nó đã đạt theo phiếu thử (điểm 5) và ý đó đã qua chín phép lọc (điểm 6). Thêm việc mới vào kiến trúc vẫn cần lệnh Owner (ADR-0020 QĐ-H8). Hai loại việc sau khác nhau và không gọi lẫn tên:

   - Phép thử tay, tức thử quy trình: viết thử, ngoài kho, một phần của hồ sơ hay một bước của quy trình trên tệp gốc đã ghim, để xem bước đó làm được không, chấm được không và tốn bao nhiêu công. Giả thuyết trong bản thử là giả thuyết về chỉ tiêu của doanh nghiệp, có điều kiện sai và ngày xem lại như Mục 11, và được hậu kiểm như B8 bước 5. Phép thử tay không chấm điểm một mô hình hay một ghế, không so ghế này với ghế khác, không thử một chiến lược. Kết quả của nó chỉ trả lời một câu: thử tiếp, đề xuất ADR, hay bỏ. Kết quả đó không được dẫn làm bằng chứng về năng lực của LLM hay của dự án.
   - Việc mà L-05 gọi là «kiểm định hay chấm điểm năng lực của LLM», và việc mà L-06 gọi là «lần thử chiến lược/giả thuyết»: không làm dưới tên phép thử tay. Chỉ làm theo đúng L-05 và L-06, bằng đường đã có của kho (Ledger, `research/trial_registry.jsonl`). Không có đường hợp lệ thì không làm cho tới khi Owner sửa luật và luật có hiệu lực.

   Chưa rõ một việc thuộc loại nào thì coi là loại thứ hai: dừng và hỏi Owner. Owner hay ghế chấm L-09 coi một phép thử tay đang chạy là việc thuộc L-05 hay L-06 thì dừng phép thử đó cho tới khi Owner quyết.
5. Phiếu thử. Trước khi bắt đầu một phép thử tay, ghế phân tích ghi ở Project một phiếu thử và niêm phong bằng sha256: mục đích; dữ liệu được dùng; tiêu chí đạt và tiêu chí không đạt; cách chấm; hạn; ghế chấm, khác hãng với ghế viết. Sau khi niêm phong không sửa tiêu chí. Bản thử được niêm phong sha256 ở Project trước sự kiện và chấm bằng tài liệu ra sau ngày niêm phong; hậu kiểm của bản thử được một ghế khác hãng đối chiếu như QĐ-B4 điểm 3, và ghi riêng, không vào sổ kết quả của hồ sơ. Kết quả không đạt được lưu kèm lý do, như kết quả đạt. Làm lại là một phép thử mới, có phiếu mới, đếm riêng. Với NL-07, ghế phân tích lập phiếu thử theo điểm này từ luật đã ghi ngày 28/11/2026 ở tài liệu căn cứ, không đổi nội dung của luật đó, và niêm phong phiếu trước khi viết bản thử.
6. Chín phép lọc cho một ý mới, áp trước khi lập phiếu thử:
   1. có trọng tài: chấm được bằng tài liệu ra sau ngày ghi;
   2. thử tay được trong hai kỳ báo cáo, ngoài kho;
   3. nằm trong L-01 tới L-10. Ý nào cần sửa luật thì không thử, kể cả thử tay, trước khi Owner sửa luật và luật đã sửa có hiệu lực;
   4. công của Owner và tổng công vận hành đo được bằng phút;
   5. có giá trị thêm so với quy trình đang có;
   6. chính phương pháp có điều kiện bị bác;
   7. nêu được cái giá khi nó kết luận sai;
   8. ghế chấm khác hãng với ghế viết (L-09). Ý có dùng lỗi gài để thử một ghế thì ghế gài không phải ghế bị thử và khác hãng với ghế bị thử;
   9. không tạo đầu ra nêu hay ngụ ý lời mua, bán, nắm giữ, giá tương lai, khoảng giá trị, hệ số định giá mục tiêu, điểm hấp dẫn hay thứ hạng của mã. Chỉ tiêu quá khứ có nguồn mà hồ sơ đang được nêu theo quy trình B5 không bị phép lọc này cấm.

   Việc tra tiền lệ vẫn làm và ghi rõ đã tìm ở đâu. «Đã tìm, không thấy» không chứng minh tính mới và không là phép lọc.
7. Ứng viên được hội đồng nêu để xét sau khi cổng mở. Ghi lại để không mất; đây là ứng viên, không phải cam kết làm: lỗi gài cho lập luận (ghế gài khác hãng ghế viết; có cả đoạn đúng lẫn đoạn sai; đếm cả lần bắt nhầm; chỉ là kiểm chất lượng nội bộ); «chứng chỉ bất khả phân biệt» (dựng hai cấu hình kế toán trái kết luận mà cùng khớp mọi dữ kiện đã ghim, để chỉ ra một câu hỏi chưa phân định được); «chứng thực hai đầu giao dịch» (đối chiếu một sự kiện qua tài liệu của hai chủ thể độc lập). Mỗi ứng viên phải qua điểm 4, 5 và 6 như mọi ý khác.

### QĐ-B2 — Ngừng hai phép thống kê của ADR-0024

1. Phép so của QĐ-N3 điểm 4 (Δ giữa nhóm ĐỘ PHỦ THẤP và nhóm còn lại) ngừng. QĐ-N3 điểm 1 tới 3 giữ nguyên: nhãn độ phủ vẫn ghi khi giao hồ sơ, theo quy tắc đếm đã ghi ở Project.
2. Việc hai ghế đếm riêng ở mã đầu tiên (QĐ-N3 điểm 2) đã làm ngày 28/11/2026 cho HPG và GAS, ghi ở Project. Phần còn lại của điểm đó, đếm lại hai mã theo quy tắc đã sửa trước mã kế tiếp, vẫn phải làm (NL-05). Hàng QĐ-N3 trong bảng cổng sang Pha 2 của ADR-0024 QĐ-N7 điểm 4 giữ nguyên chữ; bằng chứng nộp cho hàng đó là bản ghi ngày 28/11/2026. ADR-0024 không bắt hai ghế đếm cho các mã về sau, và ADR này cũng không.
3. Nhãn loại lập luận và số đo theo nhãn của QĐ-N5 điểm 3 và điểm 5 ngừng. Ở B7 bước 7 không ghi nhãn. Giữ nguyên: danh sách ứng viên bất đồng (QĐ-N5 điểm 1, trừ nhãn); việc đưa ứng viên còn lại vào sổ câu hỏi (QĐ-N5 điểm 2); sổ bất đồng, không có cột nhãn (QĐ-N5 điểm 4); sổ lỗi đã xác minh (QĐ-N5 điểm 6). Nhãn đã ghi trước ngày gộp PR này, nếu có, giữ nguyên.
4. Hai phép so ngừng trước mốc quyết định của ADR-0024, nên phần «bỏ phép so» ở điều kiện hoàn tác 4 và phần «ngừng ghi nhãn» ở điều kiện hoàn tác 5 của ADR-0024 không còn việc để áp. Quyền của Owner chọn giữ nhãn độ phủ làm mô tả hay bỏ nhãn (điều kiện hoàn tác 4 của ADR-0024) giữ nguyên.
5. Lý do: nhóm ĐỘ PHỦ THẤP đang có 0 mã, và mỗi nhóm cần 20 cặp chấm được cùng tám cụm; mỗi nhãn cần mười câu đã phân định cùng tám cụm. Với ba mã, các ngưỡng đó không tới kịp hạn của ADR-0024 với đủ lực để đọc.
6. Cái mất: từ ngày gộp, bất đồng mới không có nhãn chốt trước kết quả. Phần này không bù lại được bằng cách gán nhãn về sau (điều kiện hoàn tác 3).

### QĐ-B3 — Cách đọc sổ thành tích của ADR-0024

1. Chữ của ADR-0024 QĐ-N1 và ba mốc đọc giữ nguyên. Phép so A với B chạy như đã khóa: vòng đã khóa và các vòng sau làm đúng quy định. Trong phép so đó, Δ và khoảng tin cậy vẫn là số đo chính như QĐ-N1 điểm 9.
2. Ghi nhận trước khi có kết quả đầu tiên: mô phỏng của kiến trúc sư, ở 64 cặp chấm được trên 16 cụm, cho khả năng ra kết luận «A tốt hơn B» là 15,0%, 28,5% và 47,0% trong ba kịch bản A hơn B ít, vừa và nhiều; ở cả ba kịch bản, khả năng ra CHƯA ĐỦ BẰNG CHỨNG là 82,5%, 71,0% và 52,8%, lớn nhất trong ba kết luận. 64 cặp là kịch bản của mô phỏng, không phải ngưỡng: ngưỡng của mốc quyết định vẫn là 60 cặp chấm được và 16 cụm như ADR-0024. Mức chênh giữa A và B trong mô phỏng là giả định, không phải dữ liệu. Giả định, đoạn mã, hạt giống và tỷ lệ của cả ba kết luận (A tốt hơn B, A kém hơn B, CHƯA ĐỦ BẰNG CHỨNG) lưu ở tài liệu Project `claude/MO_PHONG_LUC_THONG_KE_ADR0026_20261128.md`. Ba ghế của hội đồng, không chạy mô phỏng này, cùng nhận định rằng phép so khó ra kết luận với số mã hiện có.
3. CHƯA ĐỦ BẰNG CHỨNG nghĩa là chưa kết luận được. Không đọc nó thành «A không có lợi thế».
4. Vì vậy dự án không chờ kết luận của phép so A với B để biết phần phân tích sai ở đâu. Việc đó đọc ở sổ kết quả (QĐ-B4). Sổ dự báo và bảng chấm vẫn được ghi đủ như ADR-0024.
5. Nếu A thắng B, kết luận chỉ nói về tổ hợp (hồ sơ, tệp gốc, ba ghế) so với ghế B hiện có. Nó không nói riêng về việc gộp ghế; phần đó thuộc phép so phụ của QĐ-N1 điểm 9.
6. Hội đồng nêu hướng đổi đối chứng: ghế đối chứng nhận cùng tệp gốc đã ghim, không nhận hồ sơ và quy trình của dự án; hai ghế thêm rằng ghế đó nên khác hãng với người viết. Việc đổi chỉ được xét sau khi cổng mở (QĐ-B1), bằng ADR riêng, vì phải đổi `governance/CONTROL_B_PROMPT.md`, tệp chỉ Owner sửa. Không trộn kết quả của đối chứng cũ và đối chứng mới trong một phép so.

### QĐ-B4 — Sổ kết quả

1. Sổ kết quả là một tài liệu ở Project, do ghế phân tích giữ, mỗi hồ sơ đã niêm phong một khối. Mỗi hồ sơ trong tập của cổng (QĐ-B1 điểm 3) cũng có một khối, kể cả FPT bản 2. Bản đóng của FPT bản 2 là bản cuối có phiếu máy ĐẠT và sha256 ghi ở Project ngày 24/11/2026; từ ngày gộp PR này không sửa bản đó. Câu mở đầu mục 5 của quy trình («Chỉ dùng hồ sơ đã giao và đã niêm phong») không chặn khối này.
   - Khóa của một dòng gồm bốn phần: mã; sha256 của bản đã giao; mã điều kiện (giả thuyết của Mục 11, hay tên biến của dòng Mục 9); kỳ báo cáo mà điều kiện nêu. Giả thuyết có hơn một điều kiện sai thì mã điều kiện kèm số thứ tự của điều kiện. Điều kiện nêu nhiều kỳ thì mỗi kỳ một khóa.
   - Mỗi lần chấm một khóa là một dòng lịch sử: nguyên văn điều kiện trong bản đã giao; lần hậu kiểm (hồ sơ nào, báo cáo nào, định kỳ hay theo sự kiện); ngày chấm; phán quyết đúng như B8 bước 5; mã tệp và trang dùng để chấm. Không xóa dòng lịch sử.
   - Trạng thái hiện hành của một khóa là lần chấm hợp lệ mới nhất, theo luật của quy trình mục 5.4: phán quyết đã đủ nguồn và đúng kỳ thì giữ; CHƯA RÕ hay CHƯA CHẤM ĐƯỢC thì được chấm lại ở lần sau. Dòng còn bất đồng sau lượt đối chiếu có trạng thái hiện hành theo điểm 3.
   - Một lần hậu kiểm là một lần chạy B8 bước 5 của một hồ sơ trên một báo cáo tài chính (quý, bán niên hay năm) của doanh nghiệp. Chạy lại trên cùng báo cáo đó, kể cả khi lần đầu là theo sự kiện và lần sau là định kỳ, không phải một lần hậu kiểm mới.
2. Giả thuyết được ghi SAI thì ghi đúng một loại nguyên nhân chính, xét về phía hồ sơ. Chọn theo thứ tự dưới đây và dừng ở loại đầu tiên đủ căn cứ:
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

   Trường này thêm vào, không thay và không trộn với các trường của ADR-0023 QĐ-T6 (TRONG BẢNG, NGOÀI BẢNG, CHƯA RÕ; «không báo») và ADR-0025 QĐ-L1 (ĐÃ LƯỜNG TRƯỚC, KHÔNG LƯỜNG TRƯỚC, CHƯA RÕ). Nó áp cho mọi lần hậu kiểm sau ngày gộp PR này, kể cả của hồ sơ đã niêm phong trước đó, vì chỉ dùng chữ của bản đã giao và tài liệu ra sau.
3. Căn cứ và đối chiếu. Mỗi phân loại nguyên nhân ghi kèm: nguyên văn điều kiện đã niêm phong; nguồn trước ngày giao (mã tệp, trang của tệp đã ghim) và nguồn sau ngày giao (mã tệp, trang của báo cáo mới); lý do chọn loại; các lỗi phụ. Ở mỗi lần hậu kiểm, một ghế khác hãng Anthropic đối chiếu từng phán quyết và từng loại nguyên nhân với báo cáo gốc; ghế phân tích soạn lệnh, Owner gửi. Mỗi dòng ghi một trạng thái đối chiếu: ĐỒNG Ý, KHÔNG ĐỒNG Ý hay CHƯA KIỂM, kèm ghế đối chiếu và ngày. Dòng KHÔNG ĐỒNG Ý: ghi nguyên văn ý của cả hai ghế; ghế phân tích mở lại trang gốc. Ghế phân tích nhận ý của ghế đối chiếu thì ghi một dòng lịch sử mới theo ý đó, trạng thái đối chiếu ĐỒNG Ý. Còn bất đồng thì cả hai ý được báo lên Owner, và trạng thái hiện hành của dòng như sau: bất đồng về phán quyết của một giả thuyết thì phán quyết là CHƯA RÕ; bất đồng về trạng thái của một dòng Mục 9 thì trạng thái là CHƯA CHẤM ĐƯỢC; hai trường hợp này ghi kèm chữ «bất đồng giữa hai ghế», và không tính là ĐÚNG, SAI hay một trạng thái đổi ở bất kỳ bảng đếm nào, cũng không tính cho điều e của cổng bằng chứng (ADR-0026 QĐ-B1 điểm 3). Hai ghế cùng ghi SAI mà chỉ bất đồng về loại nguyên nhân thì phán quyết SAI giữ, loại nguyên nhân là CHƯA RÕ. Dòng CHƯA KIỂM không được tính là kết quả lỗi hay không lỗi đã xác minh. Hạn 7 ngày gửi Owner danh sách của ADR-0024 QĐ-N4 điểm 2 không chờ lượt đối chiếu này: dòng chưa đối chiếu được gửi với trạng thái CHƯA KIỂM.
4. Các số đếm của sổ, ghi sau mỗi lần hậu kiểm. Mỗi bảng ghi ba số: số mới (khóa lần đầu có phán quyết ở lần này), số chấm lại (khóa đã có dòng, nay đổi trạng thái), và tổng lũy kế, trong đó mỗi khóa tính một lần theo trạng thái hiện hành.
   - Bảng 1: giả thuyết theo phán quyết mà B8 bước 5 ghi cho giả thuyết đó: ĐÚNG, SAI, CHƯA RÕ. ADR này không đổi cách B8 bước 5 ra phán quyết.
   - Bảng 2: riêng các giả thuyết SAI theo sáu loại nguyên nhân chính của điểm 2; ghi riêng số dòng CHƯA KIỂM.
   - Bảng 3: dòng Mục 9 theo bốn trạng thái của ADR-0023 QĐ-T6 (ĐỔI, ĐỔI MỘT PHẦN, GIỮ NGUYÊN, CHƯA CHẤM ĐƯỢC); ghi riêng số hồ sơ không có bảng Mục 9 (KHÔNG ÁP DỤNG).
   - Ghi riêng, không gộp vào ba bảng trên: số lần «không báo» (ADR-0023 QĐ-T6); số lần KHÔNG LƯỜNG TRƯỚC (ADR-0025 QĐ-L1); số lỗi ghế khác hãng bắt được ở B7 của mỗi hồ sơ, theo sổ lỗi đã xác minh (ADR-0024 QĐ-N5 điểm 6); lỗi gài của mỗi hồ sơ, ghế nào bắt được, ghế nào không (ADR-0020 QĐ-H5).
   - Số phút Owner tự ước, tách hai số: phút đọc hồ sơ, và phút làm việc cho từng năng lực như ADR-0024 QĐ-N7 điểm 2 và ADR-0025 đã quy định. Owner không khai thì ghi CHƯA GHI, không ghi 0.
5. Cách đọc. Sổ kết quả là thước chẩn đoán vận hành của phần phân tích: nó cho biết hồ sơ sai ở đâu và vì sao. Nó không phải bằng chứng thống kê về năng lực của mô hình hay của dự án, không đo hiệu quả đầu tư, không đo hồ sơ có ích cho Owner tới đâu, và không thay việc Owner nghiệm thu. Không cộng các số thành một điểm. Không dùng chúng để xếp hạng mã. Không đặt đích giảm số giả thuyết SAI: đích như vậy khuyến khích viết giả thuyết khó bác.
6. Công cụ hậu kiểm (NL-08) in được các trường của điểm 1 tới 3. Trước khi có công cụ, ghế phân tích ghi tay.

### QĐ-B5 — Hai chỗ sửa trong hồ sơ mã

1. Cuối «Một trang» có tiểu mục «### Tổng kết: điểm mạnh, điểm yếu, điểm nghi vấn», theo lệnh Owner ngày 27/11/2026. Ba danh sách ngắn.
   - Mỗi dòng chép lại một mệnh đề hồ sơ đã viết ở một mục, ghi tên mục đó, và giữ nguyên phạm vi, kỳ, điều kiện, nguồn và mức bất định của câu gốc. Dòng mang đúng nhãn của câu gốc, kèm khóa sổ hay mã tệp và trang như ADR-0020 tới ADR-0022 bắt buộc. Không nâng nhãn: câu GIẢ ĐỊNH hay SUY LUẬN không viết lại thành ĐÃ KIỂM; dòng CHƯA BIẾT không viết thành nhận định. Không thêm dữ kiện mới.
   - «Điểm nghi vấn» lấy từ kết quả điểm soi và danh sách CHƯA BIẾT.
   - Không có câu kết luận chung; không câu nào gộp các danh sách thành nhận xét tốt hay xấu về doanh nghiệp hay về mã. Không điểm số, không xếp hạng, không so với mã khác, không từ hành động.
   - Không nêu giá cổ phiếu, hệ số định giá, vốn hóa hay khoảng giá trị ở tiểu mục này. Không nhắc điểm F, điểm M, điểm Z hay trạng thái cờ của chúng ở tiểu mục này, kể cả bằng chữ không có số (ADR-0025 QĐ-L2 điểm 4).
   - Danh sách lỗi của tiểu mục, dùng ở B7 và ở điều kiện hoàn tác 5: (i) dòng không có mệnh đề gốc ở mục được ghi tên, hay thêm dữ kiện mới; (ii) dòng bỏ điều kiện, phạm vi, kỳ, nguồn hay mức bất định của câu gốc, hay nâng nhãn; (iii) câu kết luận chung tốt hay xấu về doanh nghiệp hay về mã, điểm số, thứ hạng, hay so với mã khác; (iv) nêu hay ngụ ý hành động với cổ phiếu, giá tương lai, khoảng giá trị hay hệ số định giá mục tiêu; (v) nêu giá cổ phiếu, hệ số định giá hay vốn hóa, kể cả số quá khứ có nguồn; (vi) nhắc điểm F, điểm M, điểm Z hay trạng thái cờ của chúng, kể cả bằng chữ không có số.
   - Mẫu B của `templates/hoso/LENH_MAU.md` thêm câu hỏi bắt buộc thứ tư, kiểm từng dòng của tiểu mục theo danh sách lỗi trên.
   - Nhận định ND-1 của ADR-0025 đếm gạch đầu dòng ở phần «Một trang» đứng trước tiểu mục này.
2. Mỗi điều kiện sai ở Mục 11 phải tự đủ bốn thứ: chỉ tiêu, kỳ, mốc so sánh, ngưỡng. Ngưỡng viết dưới nhãn GIẢ ĐỊNH như đã quy định. Chỉ tiêu không được là giá cổ phiếu, khối lượng giao dịch hay chỉ số thị trường.
   - Điều kiện là một sự kiện có hay không: bốn thứ là sự kiện, nguồn dùng để xác nhận, kỳ, và tiêu chí coi là đã xảy ra.
   - Điều kiện không viết được đủ bốn thứ: giữ nguyên câu điều kiện, ghi ngay sau nó «chưa chấm được: thiếu» kèm tên thứ còn thiếu, và thêm một dòng vào danh sách CHƯA BIẾT nêu tài liệu nào sẽ cho thứ còn thiếu.
   - Ở B8 bước 5, điều kiện «chưa chấm được» ghi CHƯA RÕ. Không thêm ngưỡng hay mốc so sánh sau khi giao.
   - Giả thuyết có điều kiện «chưa chấm được» không được chọn làm căn cứ của ND-1 (ADR-0025 QĐ-L1 điểm 1). Không giả thuyết nào của Mục 11 có điều kiện đủ bốn thứ: dừng trước B6 và báo Owner; không tự bỏ tiểu mục «Khám nghiệm trước».
3. Hai điểm trên áp cho hồ sơ giao sau ngày gộp PR này. Hồ sơ đã niêm phong không sửa (ADR-0021 QĐ-K5). PR này không sửa `tools/hoso/` và hồ sơ mẫu `templates/hoso/vi_du/`. Thử ngày 28/11/2026, ngoài kho: một bản sao hồ sơ mẫu thêm tiểu mục này với ba dòng có nhãn vẫn đạt phiếu máy ở cả năm cổng, công cụ tại `820ffb1`. Kết quả đó chỉ cho thấy ca đó hợp cú pháp của máy; nó không cho thấy tiểu mục an toàn về nghĩa. Lớp giữ về nghĩa là câu hỏi bắt buộc thứ tư ở B7. Không mở PR mã chỉ để máy bắt lỗi về nghĩa của tiểu mục.

### QĐ-B6 — Kỷ luật và người dùng

1. `templates/ky_luat/MAU_KY_LUAT_TRONG.md`: dòng nhãn «Giá trị–dài hạn» đang ghi thoát khi «giá vượt khoảng giá trị trong hồ sơ». Hồ sơ không có khoảng giá trị (Mục 8 khóa theo ADR-0019 QĐ-P13). Sửa thành khoảng giá trị do Owner tự lập và tự ghi ở chỗ riêng. ADR-0019 QĐ-P8 vốn không nói khoảng giá trị lấy từ hồ sơ. Đầu tệp thêm một dòng trỏ tới trang giải thích. Không quy tắc, câu hỏi hay nguyên tắc thoát nào khác của mẫu bị đổi.
2. `templates/ky_luat/GIAI_THICH_MAU_KY_LUAT.md` (mới): giải thích bằng lời thường từng dòng của bản quy tắc, từng câu của phiếu và từng cột của nhật ký. Chỉ nêu dòng đó hỏi gì và vì sao phải trả lời trước; không gợi ý con số, không chọn thay Owner, không thêm và không đổi nguyên tắc thoát nào của ADR-0019 QĐ-P8. Câu 11 được giải thích đủ năm câu trả lời chuẩn của ADR-0024 QĐ-N4 điểm 1.
3. Ở B8 bước 3, Owner đọc xong thì gõ trong Project «đã đọc», kèm mã và bản; ghế phân tích ghi dòng đó kèm ngày vào tài liệu Project của hồ sơ. Owner có thể ghi thêm chỗ còn vướng và số phút đã đọc. Không ghi số vốn, vị thế hay mức lỗ (L-03).
   - Dòng này là tự khai của Owner. Nó ghi ngày Owner báo đã đọc; nó không chứng minh Owner đã hiểu, đã dùng, đã mở ba số hay đã giữ kỷ luật.
   - Áp cho hồ sơ giao sau ngày gộp PR này. Hồ sơ đã giao trước đó không cần khai lại: ADR-0024 đã ghi thước đo của ADR-0019 QĐ-P14 là đạt.
   - Owner không gõ thì tài liệu Project của hồ sơ ghi CHƯA GHI; không suy thành chưa đọc.

### QĐ-B7 — Đồng bộ giấy tờ

1. `BOOT.md` viết lại cho đúng phạm vi đang hiệu lực: thứ tự đọc không còn bắt đọc `governance/OWNER_MISSION.md` và `governance/GOVERNOR_POLICY.yaml`; thêm `state/PROJECT_STATE.yaml` cho việc kiến trúc; tách bảng các thứ đã ngừng khỏi bảng các thứ vẫn vận hành trong phạm vi hẹp; bỏ bảng lệnh và các nguyên lý của kiến trúc trước ADR-0019.
2. `state/PROJECT_STATE.yaml` ghi tình trạng tới ADR này.
3. Mục 5.2 của quy trình ghi hai điều đã lộ ra ở vòng đầu:
   - `model_cutoff`. Trường ghi tháng cắt dữ liệu muộn nhất trong các ghế hợp lệ, dạng `YYYY-MM`, như ADR-0024 QĐ-N1 điểm 7. Ngoại lệ hẹp của ADR này đối với điểm đó, chỉ khi tháng ấy trùng tháng mở Issue: máy nhận đọc `YYYY-MM` là ngày cuối tháng và từ chối ngày sau ngày tạo Issue, nên trường ghi ngày mở Issue dạng `YYYY-MM-DD`. Ngày đó là cận trên bảo thủ của ngày cắt, vì một mô hình không thể có dữ liệu sau lúc nó trả lời; nó không phải ngày cắt đo được. Tháng tự khai của từng ghế giữ nguyên trong bằng chứng trước hạn ở Project (QĐ-N1 điểm 8). Trước khi Owner mở Issue, ghế độc lập kiểm và ghi ở Project: tháng tự khai của từng ghế, ngày ghi vào trường, và cách suy ra ngày đó. Ghế không khai tháng cắt dữ liệu thì không được tính ở câu đó, như QĐ-N1 điểm 4.
   - `resolution_rule`: câu của QĐ-N1 chỉ dùng `comparison`, `numeric_range` hoặc `event_before_date`.
4. Không xóa và không dời mã đã ngừng (ADR-0019 QĐ-P11 giữ nguyên). `docs/CHI_DAN_PROJECT.md` không sửa: tệp đó trỏ tới `BOOT.md` và quy trình, hai tệp đã được cập nhật ở PR này.

### QĐ-B8 — Không đưa vào

- Coi ghế B là mô hình của «đám đông nhà đầu tư dùng AI»: cả ba ghế bác. Một mô hình của một hãng không đại diện cho đám đông; sai về chỉ tiêu không phải là định giá sai. Dữ liệu sai của ghế B, nếu ghi, chỉ gọi là điểm mù của mô hình B.
- Đổi kỳ vọng hàm ý trong giá thành câu hỏi chấm được: hai ghế bác, một ghế chỉ nhận khi mọi tham số bị khóa cứng. Nhiều bộ giả định khác nhau giải thích được cùng một mức giá. L-02, ADR-0019 QĐ-P13 và ADR-0025 QĐ-L4 giữ nguyên.
- Cho các ghế trao đổi với nhau để đi tới một kết luận chung: các ghế làm độc lập; chỗ khác nhau được báo lên Owner. Nhiều ghế cùng một kết luận không phải là nhiều bằng chứng độc lập.

## Số đo và mốc đọc

| Điều | Số đo | Ai ghi | Khi nào đọc |
|---|---|---|---|
| Cổng bằng chứng | Ngày đủ và bằng chứng của từng điều trong năm điều ở QĐ-B1 điểm 3; số ADR năng lực gộp, số phép thử tay mới và số gói Pha 2 ngoài NL-08 bắt đầu trước ngày cổng mở (cả ba phải bằng 0) | Kiến trúc sư, ở Project | Khi cổng mở, và ngày 30/04/2027 nếu cổng chưa mở |
| Sổ kết quả | Ba bảng đếm và các số ghi riêng của QĐ-B4 điểm 4 | Ghế phân tích; ghế khác hãng đối chiếu | Mỗi lần hậu kiểm |
| Tiểu mục tổng kết | Số hồ sơ có lỗi đã xác minh ở tiểu mục, theo danh sách lỗi của QĐ-B5 điểm 1; câu trả lời của Owner: CÓ DÙNG, KHÔNG DÙNG hay CHƯA PHẢN HỒI | Ghế phân tích, ở Project | Sau mỗi hồ sơ; hỏi Owner sau hồ sơ thứ ba có tiểu mục |

## Hệ quả

- Tới khi cổng mở, dự án không thêm năng lực và không bắt đầu gói Pha 2. Sức làm dồn cho các việc ở QĐ-B1 điểm 2 và cho hậu kiểm đầu tiên.
- Hai câu hỏi phụ của ADR-0024 (lợi thế theo độ phủ; bên nào đúng hơn theo loại lập luận) không còn được trả lời.
- Mỗi hồ sơ mới thêm một tiểu mục ngắn ở «Một trang», và lệnh phản biện thêm một câu hỏi bắt buộc.
- Mỗi lần hậu kiểm thêm: loại nguyên nhân và căn cứ cho giả thuyết bị ghi SAI, và một lượt đối chiếu của ghế khác hãng. Owner gửi thêm một lệnh cho mỗi lần hậu kiểm.

Điểm yếu đã biết:

- ADR này vẫn là một ADR nữa. Nó chỉ sửa chữ; phần thêm là sổ kết quả, một tài liệu ghi tay.
- Cổng không tự thi hành. Nó có lực khi kiến trúc sư và Owner cùng giữ.
- Điều e của QĐ-B1 điểm 3 có thể giữ cổng đóng lâu nếu điều kiện sai của các hồ sơ đã giao khó chấm. Khi đó điều kiện hoàn tác 1 đưa việc về Owner.
- Loại nguyên nhân ở QĐ-B4 do ghế phân tích ghi về hồ sơ của chính mình. Lớp giữ là ghế khác hãng đối chiếu từng phân loại ở mỗi lần hậu kiểm (QĐ-B4 điểm 3). Ghế đối chiếu cũng có thể sai. Còn bất đồng về phán quyết thì không tính là ĐÚNG hay SAI. Cùng ghi SAI mà chỉ bất đồng loại nguyên nhân thì SAI giữ, loại là CHƯA RÕ (QĐ-B4 điểm 3).
- Với ba hồ sơ, các số đếm của sổ kết quả rất nhỏ. Chúng dùng để tìm lỗi, không để suy ra tỷ lệ.
- Xếp bản thử ngoài sách (NL-07) vào loại thử quy trình là cách đọc của kiến trúc sư. Owner hay ghế chấm đọc khác thì dừng theo QĐ-B1 điểm 4.
- Tiểu mục tổng kết có thể bị đọc như một lời đánh giá. Lớp giữ là luật nhãn, phiếu máy về cú pháp, và câu hỏi bắt buộc thứ tư của ghế phản biện ở B7 về nghĩa.
- Kế hoạch do ghế soạn kiến trúc viết. Một ghế của hội đồng không đọc được kho; ghế chuyển thư của hội đồng cùng hãng với một ghế của hội đồng.
- Một lỗi gài về lập luận trong gói gửi hội đồng: một ghế bắt đúng, một ghế bắt được câu với lý do chưa trúng, một ghế không bắt. Ba ghế, một lần thử: không kết luận được gì.

## Không đổi

- L-01 tới L-10 và `governance/LAWS.md` không sửa. PR này không chạm `governance/`, `ledger/`, `paper/`, `research/`, `engine/`, `data/`, `tools/`, `tests/`, `templates/hoso/vi_du/`.
- `autonomous_order_execution: false` và `live_trading_enabled: false` giữ nguyên. Không mở API trả phí.
- Chữ của ADR-0001 tới ADR-0025 không sửa. ADR này thêm hay đổi cách áp đúng các điểm sau, và chỉ các điểm này:
  - ADR-0019 QĐ-P5 (khung hồ sơ): «Một trang» thêm tiểu mục «Tổng kết»; mỗi điều kiện sai ở Mục 11 phải đủ bốn thứ (QĐ-B5). ADR-0019 QĐ-P7: lệnh phản biện (mẫu B) thêm câu hỏi bắt buộc thứ tư (QĐ-B5 điểm 1). ADR-0019 QĐ-P8: mẫu trống ghi khoảng giá trị là do Owner tự lập, và có thêm trang giải thích; mười dòng, hai nhãn và nguyên tắc thoát không đổi (QĐ-B6).
  - ADR-0020 QĐ-H8: thêm việc mới vào kiến trúc, ngoài lệnh Owner, còn phải qua cổng bằng chứng (QĐ-B1).
  - ADR-0024: QĐ-N3 điểm 4 và QĐ-N5 điểm 3, điểm 5 ngừng; phần nhãn loại lập luận ở QĐ-N5 điểm 1 và điểm 4 bỏ; phần «bỏ phép so» của điều kiện hoàn tác 4 và phần «ngừng ghi nhãn» của điều kiện hoàn tác 5 không còn việc để áp (QĐ-B2). QĐ-N1 điểm 7 có một ngoại lệ hẹp (QĐ-B7 điểm 3). Các gói Pha 2 ở QĐ-N7 điểm 5 và QĐ-N2 điểm 7 thêm cổng bằng chứng (QĐ-B1).
  - ADR-0025: ở QĐ-L1 điểm 1, nhận định ND-1 đếm gạch đầu dòng ở phần «Một trang» đứng trước tiểu mục «Tổng kết» (QĐ-B5 điểm 1); giả thuyết có điều kiện «chưa chấm được» không được làm căn cứ của ND-1, và không giả thuyết nào có điều kiện đủ bốn thứ thì dừng trước B6 (QĐ-B5 điểm 2); gói Pha 2 ở QĐ-L2 điểm 6 thêm cổng bằng chứng (QĐ-B1).
  - Hậu kiểm ở B8 bước 5 (ADR-0021 QĐ-K5, ADR-0023 QĐ-T6, ADR-0024 QĐ-N4, ADR-0025 QĐ-L1): thêm sổ kết quả, loại nguyên nhân chính và lượt đối chiếu khác hãng (QĐ-B4). Các trường đã có giữ nguyên, không trộn.
  - Phần còn lại của các ADR đó giữ nguyên.
- Hồ sơ đã niêm phong không sửa. Vòng dự báo đã khóa không đổi.

## Điều kiện hoàn tác

1. Cổng bằng chứng: Owner gỡ cổng bằng một ADR bất kỳ lúc nào. Tới hết ngày 30/04/2027 mà cổng chưa mở: kiến trúc sư báo Owner trong 7 ngày điều nào trong năm điều chưa đủ, ở hồ sơ nào; Owner chọn bằng một ADR mới giữ cổng, sửa điều kiện hay gỡ cổng.
2. QĐ-B2, phép so theo độ phủ: khi có ít nhất ba hồ sơ đã giao mang nhãn ĐỘ PHỦ THẤP, kiến trúc sư báo Owner. Đó là mốc xét lại, chưa phải đủ lực thống kê. Mở lại thì bằng một ADR mới ghi trước số cặp và số cụm cần có. Nhãn độ phủ được ghi suốt thời gian ngừng nên dùng lại được.
3. QĐ-B2, số đo theo loại lập luận: mở lại thì bằng một ADR mới, và bắt đầu một tập mới gồm các bất đồng có nhãn chốt lúc ghi ở B7, trước khi biết kết quả. Bất đồng ghi trong thời gian ngừng không có nhãn; không gán nhãn về sau để tính số đo; chúng chỉ dùng để mô tả.
4. QĐ-B4, loại nguyên nhân: sau bốn lần hậu kiểm (theo nghĩa của QĐ-B4 điểm 1) kể từ ngày gộp, tính trên các giả thuyết SAI của bốn lần đó, mỗi khóa một lần theo trạng thái hiện hành, chỉ tính dòng đã được ghế khác hãng đối chiếu. Loại CHƯA RÕ chiếm quá nửa: kiến trúc sư báo Owner trong 7 ngày, kèm tử số và mẫu số; Owner chọn sửa danh sách loại hay bỏ trường này. Không có giả thuyết SAI nào: ghi «không đủ mẫu», không tính tỷ lệ, và xét lại sau bốn lần hậu kiểm kế tiếp.
5. QĐ-B5 điểm 1, tiểu mục tổng kết:
   - Hai hồ sơ đã giao liên tiếp mà ở B7 của mỗi hồ sơ có ít nhất một lỗi thuộc danh sách lỗi của tiểu mục, do ghế phản biện nêu và ghế phân tích xác minh: bỏ tiểu mục bằng một PR chữ. Nhiều vòng phản biện của cùng một hồ sơ tính là một hồ sơ.
   - Sau hồ sơ thứ ba có tiểu mục, ghế phân tích hỏi Owner tiểu mục có được dùng không, và ghi ở Project một trong ba: CÓ DÙNG, KHÔNG DÙNG, CHƯA PHẢN HỒI. KHÔNG DÙNG: bỏ tiểu mục bằng một PR chữ. CHƯA PHẢN HỒI: nhắc lại ở lần giao kế tiếp; không suy thành không dùng.
6. Bất kỳ lúc nào, không chờ mốc nào ở trên: một câu ở tiểu mục tổng kết, ở sổ kết quả hay ở trang giải thích mẫu kỷ luật nêu giá cổ phiếu, khoảng giá trị, lời hành động, hay gợi ý một con số cho bản quy tắc của Owner: dừng phần đó và báo Owner ngay.
7. QĐ-B7 điểm 3: ngoại lệ về `model_cutoff` hết hiệu lực khi máy nhận được sửa để nhận tháng tự khai trùng tháng mở Issue. Việc sửa máy nhận là một PR mã riêng, không thuộc PR này.
8. Hoàn tác: một PR đảo các thay đổi chữ của PR này. Sổ kết quả đã ghi ở Project giữ nguyên.

## Ảnh hưởng tới ARCHITECTURE.md

- Dòng trạng thái đầu tệp: thêm ADR-0026.
- Thêm một đoạn ngắn sau đoạn «Từ ADR-0025», trỏ tới ADR này.
- Chữ của §0–§10 và bảng phạm vi hiệu lực của ADR-0019 giữ nguyên.
