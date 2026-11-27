# ADR-0024: Năm năng lực kiểm chứng được

- Ngày: 2026-11-28
- Trạng thái: ACCEPTED 28/11/2026 theo lệnh Owner, hiệu lực khi Owner gộp PR này.
- Người đề xuất: Claude Project TTC (Anthropic), ghế kiến trúc sư trưởng. Chép vào kho: phiên Claude Code (Anthropic).
- Phản biện bản nháp: ChatGPT (OpenAI), ngày 28/11/2026. Vòng 1 (PB-ADR24-V1): SỬA TRƯỚC, mười một lỗi chặn C01–C11. Vòng 2 (PB-ADR24-V2): mười lỗi đã đóng; SỬA TRƯỚC với chín lỗi chặn, C01 và C12–C19. Vòng 3 (PB-ADR24-V3): tám lỗi đã đóng; còn C18 (tập chấm của sổ bất đồng khi một bên thiếu p). Ngày 28/11/2026 Owner chọn sửa C18 đúng theo cách ghế phản biện ghi rồi đi tiếp, thay cho vòng thứ tư. Bản này sửa C18 như vậy và nhận góp ý không chặn G01–G12. Người chấm PR: ghế khác hãng Anthropic, ghi trong thân PR (L-09).
- Owner duyệt: lệnh trong chat Project ngày 28/11/2026, 00:12 giờ Việt Nam, «Năm chỗ đột phá có thể có, mỗi chỗ đều kiểm chứng được; rất hay tôi nhất trí và giao toàn quyền cho bạn hoàn thành ý tưởng trên vào kiến trúc. tôi chỉ nghiệm thu sau khi xong»; xác nhận bằng việc gộp PR này.

## Bối cảnh

- Thước đo của ADR-0019 QĐ-P14 đã đạt. Hai hồ sơ đã giao và đã niêm phong: HPG bản 2 (26/11/2026, Mục 9 viết trước ADR-0023) và GAS bản 1 sửa 1 (27/11/2026, Mục 9 theo ADR-0023). Cả hai trong phạm vi L-02, có phiếu máy ĐẠT, qua phản biện và đối chiếu số khác hãng, Owner đã đọc. Bản thử thời thế HPG sửa 2 (27/11/2026) là bản thử để đánh giá ADR-0023 (QĐ-T8), không phải hồ sơ đã giao. Hồ sơ nằm ở máy Owner và trong Project, không vào kho.
- Ngày 27–28/11/2026 Owner hỏi kiến trúc tìm «sức mạnh» ở đâu khi mọi nhà đầu tư đều dùng AI mạnh. Ghế kiến trúc sư tổng hợp nghiên cứu công khai (tài liệu Project `claude/TONG_HOP_KINH_NGHIEM_AI_DAU_TU_20261127.md`): kết quả AI đoán giá trong kiểm thử quá khứ dễ bị thổi phồng vì mô hình đã thấy diễn biến sau đó; các cuộc thi bằng tiền thật cho thấy phần lớn mô hình lỗ và quyết định khác nhau dù cùng lệnh; mô hình đọc báo cáo tài chính vẫn sai nhiều và tự tin quá mức; nhà đầu tư cá nhân thua chủ yếu vì hành vi; dự báo xác suất chỉ tiến bộ khi được chấm.
- Từ đó ghế kiến trúc sư đề xuất năm năng lực, mỗi năng lực có số đo, mốc đọc và điều kiện bỏ. Owner duyệt cả năm.
- ADR-0019 QĐ-P1 không làm việc «so tài với AI ngoài dự án»; QĐ-P11 ngừng sổ dự báo A–B, ghế đối chứng B và lịch công bố; QĐ-P12 không mở dự báo mới sau khi phân định 16 dòng đang mở. ADR này mở lại một phần hẹp, liệt kê đủ ở QĐ-N6.
- Thứ tự ưu tiên không đổi: hồ sơ mã trước, việc đo sau. ADR-0019 đã ghi nhận giấy tờ từng lớn nhanh hơn sản phẩm; năm năng lực này không được lặp lại điều đó (QĐ-N7 điểm 2).

## Quyết định

### QĐ-N1 — Sổ thành tích nhiều ghế

Điều được đo, nói đúng phạm vi: quy trình TTC (hồ sơ đã giao, tệp gốc đã ghim, nhiều ghế) dự báo chỉ tiêu doanh nghiệp tốt hơn, kém hơn hay chưa phân biệt được so với Claude trần không hồ sơ, không tìm kiếm, trên tập câu đã đăng ký trước. Phép so chính không cho biết lợi thế có đến riêng từ việc gộp nhiều ghế hay không; phép so phụ ở điểm 9 đo phần đó.

1. Câu đủ điều kiện. Chỉ về chỉ tiêu hay sự kiện của doanh nghiệp có hồ sơ đã giao và đã niêm phong (ADR-0021 QĐ-K5). Phân định bằng báo cáo tài chính hay công bố thông tin của chính doanh nghiệp, trên trang của doanh nghiệp hay của sở giao dịch có tên miền ghi trong nguồn phân định. Câu lấy từ ba chỗ:
   - mọi điều kiện sai ở Mục 11 của bản đã giao mà báo cáo của kỳ được hỏi chấm được: lấy hết, không chọn bớt;
   - dòng Mục 9 chỉ khi điều kiện của dòng nói về kết quả của chính doanh nghiệp; điều kiện về biến bên ngoài ở lại hậu kiểm của ADR-0023 và không thành câu hỏi (ADR-0023 QĐ-T3);
   - điểm bất đồng còn lại sau khi giao (QĐ-N5).

   Không câu nào về giá cổ phiếu, khối lượng giao dịch, chỉ số thị trường hay hướng đi của một biến bên ngoài.
2. Sổ câu hỏi, ở Project, khóa trước khi thu xác suất. Mỗi câu ghi: mã câu `ADR24-<MÃ>-<kỳ>-<số>`; bản hồ sơ và sha256; điều kiện gốc (mục, giả thuyết); chỉ tiêu; báo cáo hợp nhất hay riêng; kỳ riêng hay lũy kế; số công bố lần đầu, không theo số điều chỉnh về sau; ngưỡng và cách tính khi đúng bằng ngưỡng; một câu điều kiện sai chung cho mọi ghế; nguồn phân định có tên miền; `calendar_id`, `info_lock_at`, `resolve_at`; cụm (mã × kỳ báo cáo). Một chỉ tiêu của một kỳ chỉ có một câu. Ghế độc lập (điểm 5) duyệt sổ theo mẫu E của `templates/hoso/LENH_MAU.md`. Duyệt xong thì khóa: mọi câu đã khóa đều được gửi cho mọi ghế và ghi vào sổ dự báo; không bỏ câu nào vì nội dung câu trả lời của ghế nào. Câu chỉ rời vòng theo điểm 3 hay điểm 6, và sổ câu hỏi ghi lý do.
3. Ghế dự án, cố định cho cả phép thử: Claude Project TTC (Anthropic, ghế phân tích), ChatGPT (OpenAI), Gemini (Google). Chỉ đổi thành phần khi một ghế không dùng được trong cả một vòng; quyết và ghi vào Project trước khi thấy xác suất nào của vòng đó. Không đổi ghế vì điểm cũ. Một câu cần ít nhất hai ghế dự án có trả lời hợp lệ, trong đó ít nhất một ghế khác Anthropic; thiếu thì câu đó không ghi ở vòng này và sổ câu hỏi ghi lý do. Bảng chấm ghi riêng số câu có hai ghế và số câu có ba ghế. Ghế độc lập (điểm 5) không bao giờ thay một ghế dự án.
4. Thu xác suất theo mẫu D. Mọi ghế dự án nhận cùng câu trung tính, cùng bản hồ sơ đã giao, cùng tệp gốc đã ghim. Không ghế nào nhận bản phản biện, lập luận của một bên bất đồng hay trả lời của ghế khác. Mỗi ghế một cuộc chat mới. Ghế phân tích ghi trả lời của mình vào Project trước khi Owner gửi lệnh cho ghế khác. Mỗi ghế khai: tên và phiên bản mô hình, hãng, tháng cắt dữ liệu tự khai, có dùng tìm kiếm không, tệp nào mở được. Mỗi câu: p, tỷ lệ nền và cách lấy, điều làm trả lời sai, lý do. Ghế ghi KHÔNG TRẢ LỜI ở một câu, hoặc thiếu tháng cắt dữ liệu hay danh sách tệp mở được, thì không được tính ở câu đó. Trả lời sai mẫu được hỏi lại một lần, trước khi tính dòng A.
5. Ghế độc lập: Grok (xAI) duyệt sổ câu hỏi, đọc lịch công bố, ghi bằng chứng công bố và phân định. Owner làm thay khi Grok không dùng được. Grok và Owner không góp xác suất. Cách chia này giữ đúng luật của kho: người ghi lịch và người phân định phải khác nhà cung cấp với mọi ghế có tên trong `author_seat` của câu (`tools/ledger_intake.py`, `tools/resolution_intake.py`).
6. Lịch công bố (L-05, ADR-0011). Trước ngày thu xác suất, mỗi báo cáo được hỏi có một dòng lịch ghim qua Issue «Calendar»: Owner mở Issue, nội dung do ghế độc lập trả theo mẫu E, `recorder` ghi tên ghế độc lập; robot đăng dấu nhận trước khi mở Issue dự báo. Dòng lịch là một trong hai loại:
   - Lịch chính thức: doanh nghiệp hay sở giao dịch đã công bố ngày sẽ đưa ra con số phân định, hay một con số sơ bộ của cùng chỉ tiêu, cùng kỳ. Ghi đúng như ADR-0011: `info_lock_at` là ngày đó, `evidence_url` là trang nêu ngày, `quote` trích nguyên văn câu nêu ngày.
   - Lịch suy ra, chỉ khi không có lịch chính thức. Đây là ngoại lệ hẹp của ADR này đối với chữ «lịch chính thức» của ADR-0011 và mô tả trường của mẫu `calendar.yml`, chỉ cho câu của QĐ-N1. `info_lock_at` là ngày sớm hơn giữa ngày cuối của kỳ được hỏi và ngày tương ứng năm nay của lần sớm nhất doanh nghiệp đã công bố một con số của cùng chỉ tiêu cho cùng kỳ năm trước (kể cả số ước tính hay sơ bộ), lùi thêm 14 ngày. `calendar_id` bắt đầu bằng `CAL-ADR24-SUYRA-`. `quote` mở đầu bằng câu «LỊCH SUY RA THEO ADR-0024, KHÔNG PHẢI LỊCH CHÍNH THỨC.», sau đó trích nguyên văn câu có ngày của lần công bố năm trước; `evidence_url` trỏ tới chính lần công bố đó. Ghế độc lập kiểm ngày, trang và cách tính. Robot chỉ kiểm được tên miền, độ dài trích dẫn và người ghi, không kiểm được nghĩa; ngày suy ra không được trình bày như lịch chính thức ở bất kỳ đâu.
   - Một dòng lịch cho một báo cáo. Các câu dùng chung một dòng lịch có ngày suy ra khác nhau thì lấy ngày sớm nhất.
   - Không có bằng chứng đáng tin cho loại nào thì câu không vào phép đo. Quyết định 11 của ADR-0011 giữ nguyên: bằng chứng công bố có mốc sớm hơn ngày khóa thì dự báo ghi sau mốc đó bị loại khỏi kết luận.
7. Ghi sổ. Owner mở hai Issue «Forecast», dòng A và dòng B, trong cùng một ngày giờ Việt Nam, cùng câu chữ, nguồn phân định, luật phân định, `resolve_at`, `info_lock_at`, `calendar_id`.
   - Dòng A: `p` là trung bình cộng p của các ghế hợp lệ, làm tròn ba chữ số thập phân (5 làm tròn lên), giữ trong 0,05–0,95; `base_rate` là trung bình cộng tỷ lệ nền của các ghế hợp lệ, làm tròn như p; `model_cutoff` là tháng muộn nhất trong các ghế hợp lệ; `invalidation_conditions` là câu điều kiện sai chung của sổ câu hỏi; `author_seat` là «Claude Project TTC + ChatGPT (OpenAI) + Gemini (Google), ADR-0024», chỉ nêu các ghế hợp lệ của câu.
   - `library_refs` của dòng A theo một dạng cố định: `ADR24; cau=<mã câu>; <ghế>=<p>; …; tra_loi=<12 ký tự đầu sha256 của tệp nguyên văn các trả lời>`. Không ghi sha256 hồ sơ lên kho (ADR-0021 QĐ-K5); mã câu nối với bản hồ sơ và sha256 của nó ở sổ câu hỏi trong Project. Trường này vốn dành cho mã ghi chú thư viện; ở Pha 1 nó chứa xác suất từng ghế theo đúng dạng trên, bắt đầu bằng `ADR24;` để phân biệt. Pha 2 thêm trường đúng nghĩa và đọc được dòng Pha 1 mà không viết lại.
   - Dòng B: ghế B theo `governance/CONTROL_B_PROMPT.md`, không đổi prompt; `invalidation_conditions` là câu chung như dòng A.
   - Trước khi Owner mở Issue, ghế phân tích chạy cục bộ `parse_issue_form` và `forecast_error` của `tools/ledger_intake.py` trên bản nháp từng Issue, không sửa mã. Lỗi thì sửa bản nháp, không mở.
   - Hai dòng có dấu nhận hợp lệ trong cùng một ngày là một **cặp cùng ngày**. Cặp không cùng ngày vẫn nằm trong sổ và được đếm riêng ở bảng chấm.
8. Bằng chứng đã dự báo trước hạn, ở Project. Mỗi ghế một bản ghi: mã lệnh, mô hình, hãng, tháng cắt dữ liệu, giờ gửi, giờ trả lời, trạng thái tìm kiếm, tệp mở được, bản trả lời nguyên văn. sha256 của tệp gộp các bản nguyên văn ghi vào `library_refs` của dòng A, trước `info_lock_at`.
9. Chấm. Pha 1 tính ở Project; Pha 2 tính bằng máy của kho. Phương pháp chốt ở đây, trước kết quả đầu tiên:
   - **Cặp chấm được**: cặp cùng ngày (điểm 7), đã phân định CÓ hay KHÔNG, và cả hai dòng đạt `capability_test_eligible` của `tools/ledger_intake.py` với xuất xứ đã được kiểm toán GitHub xác nhận (ADR-0011 quyết định 5 và 10), không chỉ nhìn dấu nhận trên Issue. Mọi số lượng dùng để đạt mốc ở mục «Số đo và mốc đọc» đếm trên cặp chấm được. Cặp VOID, quá hạn, chưa phân định, không cùng ngày hay không đạt bằng chứng thời điểm được đếm riêng, không bỏ.
   - Số đo chính: Δ là trung bình của d = (p của B − y)² − (p của A − y)² trên các cặp chấm được, y bằng 1 khi kết quả là CÓ và 0 khi là KHÔNG. Δ dương nghĩa là A có điểm Brier tốt hơn B.
   - Khoảng tin cậy 90% của Δ: bootstrap theo cụm (mã × kỳ báo cáo), 10.000 lần lấy lại, hạt giống 20261128, phân vị 5% và 95%. Câu cùng cụm phụ thuộc nhau nên không lấy lại từng câu. Dưới tám cụm thì không tính khoảng tin cậy. Phép tính chạy bằng một đoạn mã cục bộ ngoài kho; Project lưu đoạn mã, phiên bản Python và thư viện, dữ liệu đầu vào và kết quả để ghế độc lập chạy lại.
   - Số đo phụ: Δ của A so với từng ghế dự án đứng riêng, trên cùng câu, lấy p từ `library_refs`. Một ghế đứng riêng có cùng hồ sơ là đối chứng «một AI có cùng tài liệu»; số này cho biết gộp ghế có thêm gì.
   - Kiểm độ bền: ở mỗi mốc, báo thêm Δ khi thêm vào tập chấm mọi cặp cùng ngày đủ bằng chứng thời điểm, đã qua `resolve_at` mà VOID hay chưa phân định; mỗi cặp đó lấy d nhỏ hơn trong hai giá trị (p của B)² − (p của A)² và (1 − p của B)² − (1 − p của A)², tức kết quả bất lợi nhất cho Δ.
   - Chỉ đọc kết luận ở ba mốc của mục «Số đo và mốc đọc». Không xem khoảng tin cậy giữa các mốc rồi dừng sớm.
   - Ghế phân tích tính; ghế độc lập tính lại từ sổ công khai ở mỗi mốc. Hai bên lệch thì báo Owner trước khi đọc.
   - Scorecard hiện có của kho (`engine/ledger.py`) tính theo cách khác và còn phép kiểm của kiến trúc cũ; không dùng nó để kết luận ADR này.
10. Giữ trung bình cộng. Trọng số theo điểm Brier quá khứ chỉ được nghiên cứu khi mỗi ghế có từ 20 câu đã phân định, phải kiểm trên câu mới chưa dùng để chọn trọng số, và chỉ đổi bằng ADR riêng.
11. Trình bày cho Owner: luôn kèm p từng ghế, p nhỏ nhất và lớn nhất, giả định chung của các ghế, nguồn mà ghế nào đó không kiểm được. Không đưa riêng một con số trung bình như mức chắc chắn đã được kiểm chứng: ba ghế khác hãng không phải ba nguồn bằng chứng độc lập.

### QĐ-N2 — Bản đồ phơi nhiễm nhiều mã

1. Mục 9 của mọi hồ sơ dùng đúng tên biến trong từ điển `templates/hoso/TU_DIEN_BIEN_THOI_THE.md`. Từ điển có mã biến cố định, dùng ở bản đồ, và cột tên cũ để ánh xạ tên đã dùng trước đây; từ điển không ghi mã chứng khoán nào đã dùng biến. Biến chưa có: thêm một dòng bằng PR chữ, trước hoặc cùng lúc với hồ sơ đầu tiên dùng nó.
2. Đầu vào của bản đồ: chỉ hồ sơ đã giao và đã niêm phong, ghi rõ bản và sha256. Bản thử (như bản thử thời thế HPG sửa 2, ADR-0023 QĐ-T8) không vào bản đồ. Hồ sơ đã giao có Mục 9 viết trước ADR-0023 (HPG bản 2): ô của mã đó ghi CHƯA PHÂN TÍCH cho tới bản đã giao kế tiếp.
3. Mỗi ô (biến × mã) ghi một trong sáu trạng thái: CÓ PHƠI NHIỄM (quy mô, mã tệp, trang, giả thuyết dựa vào); KHÔNG PHƠI NHIỄM (theo tệp gốc, có mã tệp và trang); CHƯA BIẾT; THIẾU NGUỒN; CHƯA CHẤM ĐƯỢC; CHƯA PHÂN TÍCH. Không để ô trống. Cùng tên biến không có nghĩa là cùng mức tác động. Bản đồ nằm ở Project.
4. Cảnh báo: hậu kiểm của một mã ghi một dòng ĐỔI hay ĐỔI MỘT PHẦN thì trong 7 ngày ghế phân tích báo Owner các mã khác có ô CÓ PHƠI NHIỄM với cùng biến, đề nghị xem lại sớm hơn ngày xem lại đã niêm phong. Mỗi cặp (biến, mã được báo) là một cảnh báo, ghi ngày báo. Cảnh báo không đoán biến đi hướng nào.
5. Chấm cảnh báo ở hậu kiểm kế tiếp của mã được báo. Khi ghi một nguyên nhân TRONG BẢNG, hậu kiểm của mã đó ghi tên dòng là nguyên nhân. Mỗi cảnh báo nhận đúng một kết quả, xét theo thứ tự:
   1. dòng của biến đã cảnh báo ghi GIỮ NGUYÊN: KHÔNG XÁC NHẬN;
   2. dòng ghi CHƯA CHẤM ĐƯỢC: CHƯA ĐỦ BẰNG CHỨNG;
   3. dòng ghi ĐỔI hay ĐỔI MỘT PHẦN, và có giả thuyết dựa vào biến mà nguyên nhân đứng hay gãy là TRONG BẢNG với chính dòng của biến đó được ghi là nguyên nhân: HỮU ÍCH;
   4. dòng ghi ĐỔI hay ĐỔI MỘT PHẦN, không như 3, và có giả thuyết dựa vào biến mà nguyên nhân CHƯA RÕ: CHƯA ĐỦ BẰNG CHỨNG;
   5. còn lại (nguyên nhân NGOÀI BẢNG, TRONG BẢNG ở dòng của biến khác, hay không giả thuyết nào dựa vào biến): KHÔNG HỮU ÍCH.

   **Cảnh báo đã chấm** là cảnh báo HỮU ÍCH, KHÔNG HỮU ÍCH hay KHÔNG XÁC NHẬN; cảnh báo CHƯA ĐỦ BẰNG CHỨNG không vào mẫu số. BỎ SÓT đếm riêng: hậu kiểm của một mã ghi ĐỔI hay ĐỔI MỘT PHẦN ở một biến mà mã khác có ô CÓ PHƠI NHIỄM nhưng không có cảnh báo. Với cảnh báo HỮU ÍCH, ghi số ngày cảnh báo đến trước ngày xem lại đã niêm phong.
6. Bản đồ giữ nguyên luật ADR-0023: phơi nhiễm là quy mô, không phải độ nhạy; không đoán hướng; không cộng biến thành điểm.
7. Pha 2 (gói riêng, có mã): công cụ gom bản đồ, chỉ bắt đầu khi có ít nhất ba hồ sơ đã giao viết Mục 9 theo ADR-0023.

### QĐ-N3 — Độ phủ báo cáo công khai

1. Mỗi hồ sơ đã giao ghi hai số trong tài liệu Project của hồ sơ, không trong thân hồ sơ:
   - khối lượng khớp lệnh bình quân mỗi phiên có giao dịch trong ba tháng dương lịch kết thúc ở ngày giao, từ tệp G1; ghi số phiên đã tính, số phiên không có giao dịch, số phiên thiếu dữ liệu;
   - số báo cáo phân tích công khai về doanh nghiệp trong mười hai tháng trước ngày tìm.
2. Quy tắc đếm báo cáo, như nhau cho mọi mã, ghi vào Project từ lần dùng đầu: ngày tìm; bộ từ khóa cố định (mã, tên doanh nghiệp, kèm «báo cáo phân tích»); các nguồn đã tìm; một báo cáo là một tài liệu phân tích riêng doanh nghiệp đó, do một tổ chức phát hành, có ngày trong mười hai tháng; bản đăng lại tính một lần; nguồn không mở được thì ghi tên, không tính. «Không tìm thấy» không có nghĩa là không có. Ở mã đầu tiên, ghế phân tích và ghế độc lập đếm riêng theo cùng quy tắc; lệch thì ghi cả hai số, sửa quy tắc và đếm lại mã đầu tiên theo quy tắc đã sửa, trước mã kế tiếp.
3. Nhãn: ĐỘ PHỦ THẤP khi số báo cáo từ hai trở xuống (ngưỡng là GIẢ ĐỊNH, chưa đo); còn lại ĐỘ PHỦ KHÔNG THẤP. Nhãn mô tả số báo cáo tìm được; không phải đánh giá doanh nghiệp, không phải lợi thế đầu tư đã chứng minh. Nhãn chốt khi lập, trước mọi câu hỏi của mã, và không đổi sau khi biết kết quả; mỗi bản giao mới ghi lại nhãn. Với GAS và HPG, giao trước khi ADR này có hiệu lực, nhãn ghi ngày lập thật, không ghi lùi về ngày giao.
4. Số đo: so Δ của QĐ-N1 (A so với B) giữa nhóm ĐỘ PHỦ THẤP và nhóm còn lại, bootstrap theo cụm như QĐ-N1. Không so điểm Brier tuyệt đối giữa hai nhóm.
5. Owner vẫn chọn mã (ADR-0019 QĐ-P15). Thanh khoản thấp là rủi ro riêng: điểm soi 14 và câu 7 của phiếu trước quyết định giữ nguyên.

### QĐ-N4 — Chống lỗi hành vi

1. Giữ bộ mẫu kỷ luật của ADR-0019 QĐ-P8. Phiếu trước quyết định thêm câu 11: «Từ ngày giao hồ sơ, điều kiện sai nào ở Mục 11 hay điều kiện đổi trạng thái nào ở Mục 9 đã chạm? Tôi đã đọc hậu kiểm của điều kiện đó chưa?». Năm câu trả lời chuẩn: KHÔNG CÓ ĐIỀU KIỆN NÀO CHẠM; ĐÃ CHẠM, ĐÃ ĐỌC HẬU KIỂM; ĐÃ CHẠM, CÓ HẬU KIỂM NHƯNG CHƯA ĐỌC; ĐÃ CHẠM, CHƯA CÓ HẬU KIỂM; CHƯA ĐỦ BẰNG CHỨNG. Ba câu sau tính là «chưa» theo luật chung của phiếu. Nhiều điều kiện có trạng thái khác nhau thì ghi trạng thái kém nhất, theo thứ tự từ kém tới tốt: CHƯA ĐỦ BẰNG CHỨNG; CHƯA CÓ HẬU KIỂM; CÓ HẬU KIỂM NHƯNG CHƯA ĐỌC; ĐÃ ĐỌC HẬU KIỂM; KHÔNG CÓ ĐIỀU KIỆN NÀO CHẠM. Không biết thì không ghi KHÔNG CÓ ĐIỀU KIỆN NÀO CHẠM.
2. Hai đường hậu kiểm, cùng chữ của bản đã giao và cùng nhãn của B8 bước 5:
   - định kỳ: tới ngày xem lại đã niêm phong ở Mục 11, như cũ;
   - theo sự kiện: khi doanh nghiệp có hồ sơ công bố báo cáo tài chính quý, bán niên hay năm trước ngày xem lại. Ghế phân tích lập lịch theo dõi ở Project từ hạn công bố theo quy định và từ dòng lịch của QĐ-N1. Trong tuần sau mỗi hạn, Owner mở một phiên Project và gõ «hậu kiểm theo sự kiện <MÃ>»; Owner thấy báo cáo mới sớm hơn thì gõ ngay. Ghế phân tích ghi ngày công bố, ngày phát hiện, ngày gửi; gửi Owner danh sách điều kiện đã chạm, chưa chạm, chưa chấm được trong 7 ngày kể từ ngày phát hiện; phát hiện sau ngày công bố quá 14 ngày thì ghi «phát hiện muộn». Lần chạy theo sự kiện không thay lần chạy định kỳ: điều kiện đã chấm đủ nguồn và đúng kỳ ở lần chạy theo sự kiện giữ kết quả, ghi ngày đã chấm; điều kiện còn CHƯA CHẤM ĐƯỢC hay CHƯA RÕ được chấm lại ở ngày xem lại đã niêm phong, theo đúng văn bản và kỳ của điều kiện (ADR-0023 QĐ-T6).

   Pha 1 làm tay. V23 (`tools/hoso/hau_kiem.py`, hạn gộp 15/01/2027) chỉ in danh sách nhanh hơn, không thay người kích hoạt.
3. Owner tự đếm mỗi quý, ngoài kho: tổng số quyết định; số quyết định có phiếu và nhật ký đầy đủ; số lần làm trái quy tắc riêng; số danh sách hậu kiểm đã nhận và ngày đọc. Ghế phân tích chỉ ghi ngày gửi, để trễ của dự án không bị tính thành lỗi kỷ luật của Owner. Ghế phân tích không nhận số vốn, vị thế hay mức chịu lỗ (L-03). Không dùng lãi lỗ thay số đo tuân thủ.
4. Xem lại sau bốn quý kể từ ngày gộp PR này: Owner tự xem câu 11 và danh sách hậu kiểm theo sự kiện có được dùng không, rồi quyết giữ, sửa hay bỏ hai phần này bằng ADR mới. Bộ mẫu của ADR-0019 QĐ-P8 giữ nguyên dù quyết thế nào.

### QĐ-N5 — Sổ bất đồng

1. Ở B7, điểm nào ghế phản biện kết luận ngược hồ sơ mà phân định được bằng báo cáo sau này: ghế phân tích ghi vào danh sách ứng viên ở Project, gồm nguyên văn hai lập luận, ghế của mỗi bên, mã hồ sơ và bản, nhãn loại lập luận chốt lúc ghi. Chưa soạn câu hỏi, chưa hỏi ghế nào.
2. Sau B8 bước 4 (bản đã giao đã niêm phong): bỏ ứng viên là lỗi gài, lỗi số liệu, hay điểm đã giải quyết bằng sửa hồ sơ. Ứng viên còn lại vào sổ câu hỏi của QĐ-N1 ở vòng kế tiếp, hỏi mọi ghế dự án bằng mẫu D trung tính như mọi câu khác. Ứng viên trùng một câu đã có từ Mục 11 thì không tạo câu thứ hai; sổ bất đồng trỏ tới mã câu đó.
3. Nhãn loại lập luận, chọn trong danh sách cố định: SỐ LIỆU GỐC, SẢN LƯỢNG, CHU KỲ HÀNG HÓA, CƠ CHẾ GIÁ VÀ CHÍNH SÁCH, KHOẢN MỘT LẦN VÀ KẾ TOÁN, QUẢN TRỊ VÀ CỔ ĐÔNG, KHÁC. Mỗi câu một nhãn chính.
4. Sổ bất đồng ở Project: mã câu của QĐ-N1, nguyên văn hai lập luận, ghế của mỗi bên, nhãn, p của mỗi bên lấy từ mẫu D, kết quả, chứng cứ phân định.
5. Số đo, chỉ trên câu bất đồng mà cả hai bên là ghế dự án, cả hai bên đều có p hợp lệ ở mẫu D, và câu là cặp chấm được theo QĐ-N1 điểm 9. Số câu và số cụm của từng nhãn chỉ đếm trên các câu này; câu thiếu p hợp lệ của một bên được lưu riêng, không tính vào ngưỡng mười câu hay tám cụm. Với mỗi câu đó, d = (p của bên phản biện − y)² − (p của bên hồ sơ − y)²; d dương là bên hồ sơ tốt hơn. Theo từng nhãn: trung bình của d và khoảng tin cậy 90% bootstrap theo cụm, cùng thông số với QĐ-N1 điểm 9. Nhãn có dưới mười câu đã phân định hay dưới tám cụm, hoặc có khoảng tin cậy chứa 0, ghi CHƯA ĐỦ BẰNG CHỨNG; nhãn còn lại ghi bên tốt hơn. Kết quả theo nhãn là thăm dò, không phải kết luận về năng lực. Tỷ lệ đúng hướng là số phụ; p bằng 0,5 không tính hướng. Bất đồng có một bên không phải ghế dự án (như Grok, ghế độc lập) chỉ lưu nội dung và câu hỏi, không vào phép so hai bên.
6. Lỗi xác minh được ngay bằng tài liệu (bắt ở B7, sửa ở B8) không phải câu bất đồng. Ghi vào sổ lỗi đã xác minh ở Project: loại lỗi, đã có quy tắc ngăn loại lỗi đó chưa, số ngày từ lúc bắt tới lúc sửa. Hai loại không gộp vào một tỷ lệ.

### QĐ-N6 — Phạm vi mở lại và ranh giới

| Thành phần của ADR-0019 | Từ ADR này |
|---|---|
| QĐ-P1, «so tài với AI ngoài dự án» | Ngoại lệ hẹp: so quy trình của dự án với ghế B, chỉ trên câu của QĐ-N1, để đo chính quy trình đó. Thắng AI khác không thành mục đích của dự án |
| QĐ-P11, sổ dự báo, ghế B, lịch công bố | Mở lại cho câu của QĐ-N1: Issue «Forecast», «Calendar», «Publication», «Resolution» theo ADR-0003 và ADR-0011; ghế B với prompt chuẩn hiện có |
| QĐ-P12, không mở dự báo mới | Thay bằng: chỉ mở dự báo mới theo QĐ-N1. Không câu hỏi vĩ mô mới như 16 dòng cũ |
| Mốc 194 bất đồng; lộ trình G1–G4 và mốc 31/03/2027 | Vẫn ngừng |
| Cảnh báo đổi nhóm B khi bất đồng dưới 10% sau 60 cặp | Vẫn ngừng |
| Phán quyết của scorecard cũ; scorecard hiện có làm căn cứ kết luận | Vẫn ngừng; ADR này chấm theo QĐ-N1 điểm 9 |
| Học viện với bài thi A so với B; máy dò tín hiệu; FWD-001; thang vốn; Media | Vẫn ngừng |

- Với ADR khác: một ngoại lệ hẹp đối với ADR-0011 là lịch suy ra ở QĐ-N1 điểm 6. Không có ngoại lệ nào đối với ADR-0021 QĐ-K5: không ghi sha256 hồ sơ lên kho. V23 vẫn theo ADR-0021 (QĐ-N7 điểm 5).

- L-01 tới L-10 và `governance/LAWS.md` không sửa. L-02 giữ nguyên: chỉ dự báo xác suất về sự kiện và chỉ tiêu; không mua, bán, nắm giữ; không giá mục tiêu; Mục 8 vẫn theo ADR-0019 QĐ-P13.
- Không ghép xác suất với quy tắc vị thế; không xếp hạng mã theo xác suất; không gộp các câu thành điểm hấp dẫn của doanh nghiệp. Xác suất chỉ nằm ở sổ câu hỏi, sổ dự báo và bảng chấm. Không cộng biến thời thế thành điểm. Không chọn mã, tỷ trọng hay mức lỗ thay Owner.
- Cổng chữ trước khi phát hành: trước khi ghi một câu vào sổ, mở một Issue, hay gửi Owner bản đồ, sổ độ phủ, sổ bất đồng, danh sách hậu kiểm, ghế phân tích soát chữ theo L-02 (không lời hành động, không giá cổ phiếu, không khoảng giá trị) và L-03. Câu hỏi còn qua ghế độc lập ở mẫu E.
- Riêng tư: ngoài các trường bắt buộc của mẫu Issue hiện hành («Forecast», «Calendar», «Publication», «Resolution»), phần nội dung của Issue chỉ chứa chỉ tiêu, kỳ, ngưỡng, nguồn phân định, xác suất, câu điều kiện sai chung, mã câu và sha256 rút gọn của tệp trả lời; không sha256 hồ sơ, không đoạn hồ sơ, tên tệp riêng, quy tắc riêng, nhật ký hay vị thế. Sổ câu hỏi, bằng chứng trước hạn, bản đồ, sổ độ phủ, sổ bất đồng, sổ lỗi đã xác minh nằm ở Project và máy Owner, không vào kho. Câu hỏi công khai cho người đọc kho biết dự án theo dõi doanh nghiệp nào; điều đó không thuộc L-03, và một dòng đã ghi thì không rút lại được.

### QĐ-N7 — Thứ tự thi công

1. Pha 1, PR này, chỉ chữ: ADR này; từ điển biến; mẫu D, mẫu E; câu 11 của phiếu; mục 5 mới của quy trình. Không chạm `tools/`, `tests/`, `ledger/`, `governance/`.
2. Hồ sơ trước, đo sau: không hoãn hay rút bước nào của hồ sơ để đủ câu dự báo; thiếu thời gian thì bỏ vòng dự báo, không bỏ bước của hồ sơ. Pha 1 ghi số phút Owner bỏ ra cho từng năng lực (Owner tự ước), để xét ở mốc quyết định.
3. Vòng thật đầu tiên, sau khi PR này được gộp: câu cho GAS (bản 1 sửa 1) và HPG (bản 2), hai bản đã giao; kỳ là kỳ gần nhất còn ghim kịp lịch trước ngày khóa: quý IV/2026 nếu kịp, không thì quý I/2027. Bản đồ đầu tiên từ hai bản đã giao (ô của HPG theo QĐ-N2 điểm 2). Sổ độ phủ của hai mã.
4. Cổng sang Pha 2: các phần của Pha 2 ở điểm 5, trừ V23, chỉ bắt đầu khi chạy tay đã cho đủ năm bằng chứng:

| Năng lực | Bằng chứng chạy tay |
|---|---|
| QĐ-N1 | Ít nhất một cặp cùng ngày thật; sổ câu hỏi khóa trước khi thu xác suất; đủ bằng chứng trước hạn; ghế độc lập tính lại được p của dòng A từ `library_refs` |
| QĐ-N2 | Bản đồ từ hồ sơ đã giao; mỗi ô truy ngược được tới mã tệp và trang, hoặc có trạng thái |
| QĐ-N3 | Hai ghế đếm độ phủ của một mã theo cùng quy tắc |
| QĐ-N4 | Một danh sách hậu kiểm theo sự kiện đã gửi, đủ ngày công bố, ngày phát hiện, ngày gửi |
| QĐ-N5 | Một ca bất đồng hợp lệ, hoặc một lần thử bằng dữ liệu giả định ghi rõ không tính điểm |

5. Pha 2, mỗi phần một gói, một PR, qua chấm L-09, kèm mục hoàn tác riêng về tương thích dữ liệu:
   - V23 theo ADR-0021 QĐ-K5, hạn gộp 15/01/2027, không chờ cổng ở điểm 4. V23 được in danh sách điều kiện đã chạm, chưa chạm, chưa chấm được của QĐ-N4, vì danh sách đó chỉ là kết quả của chính hậu kiểm.
   - Sau cổng: sổ nhiều ghế (trường đúng nghĩa cho p từng ghế, đọc được dòng Pha 1) và bảng chấm theo QĐ-N1 điểm 9; rồi công cụ gom bản đồ (QĐ-N2 điểm 7).

## Số đo và mốc đọc

| Năng lực | Số đo | Ai tính | Khi nào đọc |
|---|---|---|---|
| Sổ thành tích nhiều ghế | Δ của A so với B trên cặp chấm được, khoảng tin cậy 90% theo cụm; Δ của A so với từng ghế đứng riêng; Δ kiểm độ bền; số cặp không cùng ngày, VOID, quá hạn, chưa phân định; số câu hai ghế và ba ghế | Ghế phân tích; ghế độc lập tính lại | Ba mốc dưới đây |
| Bản đồ phơi nhiễm | Tổng số cảnh báo; HỮU ÍCH; KHÔNG HỮU ÍCH; KHÔNG XÁC NHẬN; CHƯA ĐỦ BẰNG CHỨNG; BỎ SÓT; số ngày đến sớm của cảnh báo HỮU ÍCH | Ghế phân tích, ở bản đồ | Mỗi lần hậu kiểm; kết luận ở điều kiện hoàn tác 3 |
| Độ phủ báo cáo công khai | Khác nhau của Δ giữa nhóm ĐỘ PHỦ THẤP và nhóm còn lại | Ghế phân tích | Mốc quyết định |
| Chống lỗi hành vi | Tỷ lệ quyết định có phiếu và nhật ký đầy đủ trên tổng số quyết định; số danh sách gửi trễ; số danh sách đọc trễ | Owner, ngoài kho; ghế phân tích chỉ có ngày gửi | Mỗi quý; xem lại sau bốn quý |
| Sổ bất đồng | Trung bình d theo nhãn và khoảng tin cậy 90% (QĐ-N5 điểm 5); tỷ lệ đúng hướng là số phụ | Ghế phân tích | Mốc quyết định |

Ba mốc đọc của sổ thành tích. Mọi số lượng dùng để đạt mốc đếm trên cặp chấm được (QĐ-N1 điểm 9), các trường hợp bị loại vẫn đếm riêng; một cụm được đếm khi có ít nhất một cặp chấm được.

1. Mốc vận hành: khi đủ cổng sang Pha 2 (QĐ-N7 điểm 4), chậm nhất 31/03/2027. Chỉ báo bước nào chạy được, bước nào chưa; không đọc điểm.
2. Mốc sơ bộ: từ 30 cặp chấm được và 8 cụm. Báo Δ và khoảng tin cậy, ghi «sơ bộ»; không quyết định gì ngoài tiếp tục.
3. Mốc quyết định: từ 60 cặp chấm được và 16 cụm, hoặc ngày 31/12/2028, tùy mốc nào đến trước. Tới 31/12/2028 mà chưa đủ 60 cặp chấm được hay 16 cụm thì kết luận là CHƯA ĐỦ BẰNG CHỨNG; báo số cặp và số cụm đã có; Δ và khoảng tin cậy chỉ tính khi có từ tám cụm, và chỉ để Owner tham khảo.

Kết luận ở mốc đủ số lượng: khoảng tin cậy 90% của Δ nằm hẳn trên 0 thì A tốt hơn B; nằm hẳn dưới 0 thì A kém hơn B; chứa 0 thì ghi CHƯA ĐỦ BẰNG CHỨNG, và điều đó không có nghĩa A kém hơn B.

## Hệ quả

- Dự án biết mình dự báo chỉ tiêu doanh nghiệp đúng tới đâu so với một AI không có hồ sơ, và gộp nhiều ghế có thêm gì so với một ghế có cùng hồ sơ, thay vì tin vào cảm giác.
- Một biến đổi ở mã này nhắc được mã khác có cùng biến, không cần đoán vĩ mô.
- Mỗi hồ sơ thêm việc: một vòng câu hỏi cho mỗi kỳ báo cáo, sổ độ phủ, ô trên bản đồ, hậu kiểm theo sự kiện. Chi phí là thời gian của các ghế và của Owner, không có API trả phí; thời gian của Owner được ghi để xét.

Điểm yếu đã biết:

- Ít mã, mỗi kỳ vài câu: tới mốc sơ bộ có thể mất nhiều quý.
- Ghế soạn ADR, ghế viết hồ sơ và một ghế góp xác suất cùng hãng với ghế B. Khác nhau giữa dòng A và dòng B là hồ sơ, tệp gốc và hai ghế khác hãng.
- Kết luận chỉ đúng với đối chứng B hiện có: Claude trần, không hồ sơ, không tìm kiếm.
- Ghế khác hãng có thể nhớ phản biện cũ của chính nó về mã đó qua bộ nhớ hội thoại; mẫu D đòi cuộc chat mới, nhưng không loại trừ hết.
- Câu cùng cụm phụ thuộc nhau; bootstrap theo cụm giảm phần này nhưng không xóa hết.
- Ngưỡng hai báo cáo của nhãn độ phủ và cách lùi 14 ngày khi đặt ngày khóa là GIẢ ĐỊNH, chưa đo.
- Lịch suy ra không phải lịch chính thức, và robot không kiểm được nghĩa của trích dẫn. Hai lớp giữ là ghế độc lập kiểm ngày và luật chỉ siết của ADR-0011.
- Câu hỏi công khai cho biết dự án theo dõi doanh nghiệp nào.

## Điều kiện hoàn tác

1. Sổ thành tích, ở mốc quyết định: kiến trúc sư báo Owner trong 7 ngày số cặp chấm được, số cụm, Δ và khoảng tin cậy khi tính được, Δ so với từng ghế đứng riêng, Δ kiểm độ bền, số phút Owner đã bỏ ra. A kém hơn B, CHƯA ĐỦ BẰNG CHỨNG, hay chưa đủ số cặp hoặc số cụm: Owner chọn bằng một ADR mới giữ, thu gọn về một ghế, hay ngừng sổ như QĐ-P12. A tốt hơn B: Owner chọn giữ hay thu gọn.
2. Tới 31/03/2027 chưa qua mốc vận hành: kiến trúc sư báo Owner trong 7 ngày bước nào chưa chạy được; Owner chọn sửa quy trình hay ngừng QĐ-N1.
3. Bản đồ: khi đã có ít nhất năm cảnh báo đã chấm (QĐ-N2 điểm 5: HỮU ÍCH, KHÔNG HỮU ÍCH hay KHÔNG XÁC NHẬN) mà không cảnh báo nào HỮU ÍCH, ngừng gom bản đồ; từ điển biến giữ nguyên. Chưa có cảnh báo đã chấm không phải là thất bại: tới 30/06/2028 chưa đủ năm cảnh báo đã chấm thì kiến trúc sư báo Owner, Owner chọn giữ hay ngừng.
4. Độ phủ: ở mốc quyết định, một nhóm có dưới 20 cặp chấm được hay dưới tám cụm, hoặc khoảng tin cậy 90% của khác nhau giữa hai nhóm chứa 0: bỏ phép so; Owner chọn giữ nhãn làm mô tả hay bỏ nhãn.
5. Sổ bất đồng: ở mốc quyết định, mọi nhãn ghi CHƯA ĐỦ BẰNG CHỨNG theo QĐ-N5 điểm 5 (kể cả nhãn dưới mười câu hay dưới tám cụm): ngừng ghi nhãn; câu hỏi vẫn ở sổ thành tích.
6. Chống lỗi hành vi: xem lại theo QĐ-N4 điểm 4.
7. Bất kỳ lúc nào: một câu hỏi dự báo về giá cổ phiếu, khối lượng giao dịch, chỉ số thị trường hay hướng đi của biến bên ngoài lọt vào sổ câu hỏi, sổ dự báo hay lệnh gửi ghế; hoặc một lời hành động với cổ phiếu, một giá cổ phiếu tương lai hay một khoảng giá trị lọt vào bất kỳ đầu ra nào của ADR này (sổ câu hỏi, sổ dự báo, lệnh gửi ghế, bản đồ, sổ độ phủ, sổ bất đồng, danh sách hậu kiểm, tin gửi Owner): dừng mọi việc mới của ADR này và báo Owner ngay. Số liệu quá khứ có nguồn, như thanh khoản ba tháng ở sổ độ phủ (QĐ-N3), không thuộc điều này.
8. Hoàn tác theo pha. Pha 1: một PR đảo các thay đổi chữ của PR này; dòng sổ dự báo đã ghi giữ nguyên, theo luật sổ chỉ ghi thêm. Pha 2: mỗi gói có mục hoàn tác riêng nói cách ngừng tiếp nhận và cách để dòng cũ vẫn đọc được bằng luật kiểm hiện hành; không xóa, không viết lại sổ.

## Ảnh hưởng tới ARCHITECTURE.md

- Dòng trạng thái đầu tệp: thêm ADR-0024.
- Thêm một đoạn ngắn sau đoạn «Từ ADR-0023», trỏ tới ADR này.
- Chữ của §0–§10 và bảng phạm vi hiệu lực của ADR-0019 giữ nguyên; phần mở lại ghi ở QĐ-N6.
