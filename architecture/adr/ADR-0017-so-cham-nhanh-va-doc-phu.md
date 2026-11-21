# ADR-0017: Sổ chấm nhanh SCN-001 — dự báo chỉ tiêu doanh nghiệp tự chấm theo bản gốc, lớp đọc phủ, cổng cấp tín hiệu

- Ngày: 2026-11-21
- Trạng thái: **PROPOSED — chưa hiệu lực.** Gộp tệp này không tự duyệt quyết định nào; xem mục "Trạng thái từng quyết định".
- Người đề xuất: Claude Project TTC (Anthropic), ghế kiến trúc sư trưởng. Chép vào kho: phiên Claude Code (Anthropic). Vòng 2: phiên Claude Code sửa QĐ-S2, QĐ-S3, QĐ-S6, QĐ-S9 và mục Lý do theo bản chấm L-09 của ChatGPT (OpenAI) trên `5ba61b4`.
- Người chấm: chưa có. Phải là ChatGPT (OpenAI) hoặc Gemini (Google), chấm đúng commit.
- Owner duyệt: chưa.
- Số: 0015 (PR #68) và 0016 (PR #73) đã dùng.

## Bối cảnh

- Thước đo kinh tế hiện có chậm. Sổ giấy kỳ 20 phiên cho khoảng 12,6 điểm chấm mỗi năm. Sổ dự báo A/B có 6 dự báo, 0 dòng phân định; mỗi dòng cần Owner mở Issue và một người phân định, nên không lên được hàng trăm điểm mỗi quý.
- Engine chỉ có 13 đặc trưng giá (§4.3); 222/222 lần thử REJECTED.
- Thư viện có 1/40 tài liệu gốc; kiến trúc chưa có đường đọc công bố thông tin của doanh nghiệp.
- Đường ghi dự báo của engine đóng theo ADR-0003 quyết định 11; mở lại cần ADR kèm cơ chế bằng chứng xuất xứ. ADR này **không** mở lại đường đó và không chạm `ledger/*`. Nó lập một sổ riêng với cơ chế xuất xứ riêng (QĐ-S3).

## Quyết định

### QĐ-S1. Phạm vi

1. Lập phép thử SCN-001 trong `experiments/SCN-001/`, mã câu hỏi tiền tố `SCN-`.
2. Không dùng `ledger/predictions.jsonl`, `ledger/resolutions.jsonl`. Không tính vào mẫu 194 cặp. Không đổi FWD-001, `frozen_space`, sổ giấy hiện có. Nếu HAI-001 (PR #72, đề xuất) được duyệt, hai phép thử có thể dùng chung bộ thu và bộ chấm nhưng đếm riêng.
3. Giả thuyết: một quy trình AI đọc văn bản gốc dự báo chỉ tiêu và sự kiện doanh nghiệp tốt hơn một baseline thống kê ghim trước.
4. Đầu ra là xác suất về chỉ tiêu và sự kiện (L-02 cho phép). Không xuất mua, bán, nắm giữ hay giá mục tiêu.
5. Tập mã: cổ phiếu niêm yết trên HOSE đã có ít nhất 4 BCTC quý trong chỉ mục của SCN tại ngày lập danh sách. Không giới hạn ở VN30.

### QĐ-S2. Ba họ câu hỏi (pha 1)

| Họ | Câu hỏi | Tài liệu phân định | Quy tắc |
|---|---|---|---|
| SCN-LN | Lợi nhuận sau thuế thuộc cổ đông công ty mẹ của quý Q có lớn hơn số của cùng quý năm trước không | Bản đầu tiên của BCTC quý Q trên trang công bố thông tin của sở; số cùng kỳ lấy từ cột so sánh của chính báo cáo đó | Dùng BCTC hợp nhất nếu có, không thì BCTC riêng. Ngân hàng, công ty chứng khoán, bảo hiểm theo bảng ánh xạ chỉ tiêu ghim ở pha 0. Bằng nhau là NO |
| SCN-CT | Trong quý Q+1, sở có công bố thông báo ngày đăng ký cuối cùng để trả cổ tức (tiền hoặc cổ phiếu) của mã không | Chỉ mục công bố thông tin của sở | Tiêu đề khớp bảng cụm từ ghim ở pha 0 |
| SCN-PH | Trong quý Q+1, sở có công bố niêm yết bổ sung cổ phiếu của mã không | Chỉ mục công bố thông tin của sở | Như trên |

- `resolve_at`:
  - SCN-LN: hạn công bố BCTC quý theo văn bản đang hiệu lực tại giờ niêm phong, cộng 10 ngày. Văn bản đó được ghim ở pha 0 kèm `effective_from` (L-08).
  - SCN-CT, SCN-PH: ngày cuối quý Q+1, cộng 3 ngày làm việc.
- Loại trước khi chấm, theo luật cơ học, áp như nhau cho mọi nhánh: câu có tài liệu phân định mang `published_at` trước giờ niêm phong.
- **Chỉ mục đầy đủ** cho một khoảng ngày nghĩa là:
  - bộ thu (QĐ-S4) có bản chụp chỉ mục thành công, đã ghim hash, cho mọi ngày của khoảng đó;
  - mỗi bản chụp chồng lấn bản liền trước: bản sau còn chứa mục mới nhất của bản trước, nên không có khe giữa hai bản.

  Thiếu một ngày, hoặc hai bản liền nhau không chồng lấn, thì chỉ mục không đầy đủ.
- **SCN-CT, SCN-PH.** Khoảng tính sự kiện là [00:00 ngày đầu quý Q+1, 23:59 ngày cuối quý Q+1] giờ Việt Nam, theo `published_at` trong metadata của sở. Tài liệu công bố ngoài khoảng này không tính là YES.
  - YES: có ít nhất một tài liệu khớp quy tắc, có `published_at` trong khoảng tính, bản gốc đã ghim đúng hash.
  - NO: không có tài liệu khớp quy tắc trong khoảng tính, **và** chỉ mục đầy đủ từ ngày đầu khoảng tính tới `resolve_at`.
  - VOID (`VOID_CHI_MUC`): chỉ mục không đầy đủ, nguồn không truy cập được, hoặc chưa chứng minh được tính đầy đủ. Không suy ra NO từ việc không thấy tài liệu.
- **SCN-LN.**
  - Chấm theo bản đầu tiên của BCTC quý Q có `published_at` trước `resolve_at`, kể cả khi công bố sau hạn luật định. Bản đó được ghi cờ `CONG_BO_TRE` và chấm bình thường.
  - VOID (`VOID_KHONG_NOP`): chỉ mục đầy đủ tới `resolve_at` nhưng chưa có BCTC quý Q.
  - VOID (`VOID_NGUON`): chỉ mục không đầy đủ, hoặc bản gốc không tải được, hoặc bản gốc lệch hash.
  - Máy không trích được hai con số thì theo QĐ-S5 mục 2 (`CAN_NGUOI_PHAN_DINH`), không VOID ngay.
- **Câu VOID.**
  - Phân tích chính loại câu VOID khỏi d̄.
  - Phân tích độ nhạy là bắt buộc: mỗi câu VOID được chấm với kết quả (YES hoặc NO) làm d lớn nhất, tức bất lợi nhất cho SCN. PASS phải đạt ở cả hai phân tích (QĐ-S6 mục 5).
  - Số câu theo từng loại VOID và số cờ `CONG_BO_TRE` được báo riêng.
  - VOID (mọi loại) quá 10% số câu của lô thì lô không hợp lệ.
- Họ "vào hoặc ra rổ VN30" không vào pha 1: mỗi năm chỉ khoảng 2 kỳ xét, không đủ cỡ mẫu của QĐ-S6 trong thời hạn xét.

### QĐ-S3. Niêm phong và công bố (cơ chế bằng chứng xuất xứ)

1. **Danh sách câu.** Công cụ sinh danh sách câu của lô từ chỉ mục đã ghim. Nếu lô nhỏ hơn tập mã đủ điều kiện, công cụ chọn N mã theo thứ tự `sha256(batch_id ‖ mã)`. Danh sách được commit lên `main` ít nhất 30 ngày trước giờ niêm phong. Danh sách không chứa dự báo.
2. **Giờ niêm phong.** 23:59 giờ Việt Nam ngày cuối quý Q, chung cho cả ba họ của lô.
3. **Niêm phong kiểu commit–reveal.**
   - Ghế dự báo đẩy lên `main` một dòng `{batch_id, family, sha256(tệp lô ‖ muối), n_rows, protocol_hash}` vào `experiments/SCN-001/seals.jsonl` (`protocol_hash` theo QĐ-S6 mục 9), bằng cơ chế ghi một tệp như `tools/registry_push.py`.
   - Workflow đăng dấu nhận dưới tên `github-actions[bot]` trên Issue theo dõi của SCN-001.
   - Giờ niêm phong được tính là giờ máy chủ của dấu nhận. Dấu nhận sau giờ niêm phong thì lô VOID và tính thất bại.
4. **Mỗi (họ, lô) đúng một dòng niêm phong.** Dòng thứ hai bị từ chối. Luật này chặn việc niêm nhiều lô rồi chỉ công bố lô đẹp.
5. **Công bố.**
   - Tệp lô và muối được thêm bằng PR sau khi mọi câu của lô đã tới `resolve_at`. Hạn chót là `resolve_at` muộn nhất của lô cộng 30 ngày.
   - CI kiểm hash khớp dòng niêm phong.
   - Không công bố đúng hạn hoặc sai hash: mọi câu được chấm với xác suất bất lợi nhất (0,05 nếu kết quả là YES, 0,95 nếu NO) và lô tính thất bại.
6. **Không được bỏ câu.** Mỗi câu trong danh sách phải có một dòng dự báo. Câu bị bỏ được chấm với p = 0,5. Bỏ quá 10% số câu thì lô không hợp lệ và tính thất bại.
7. **Dòng dự báo** có các trường `question_id`, `p` (kẹp trong [0,05; 0,95]), `card_refs`, `model_id`, `model_cutoff`, `prompt_hash`, `seat`. `resolve_at` phải sau `model_cutoff` (L-05).
8. **Ngoại lệ ghi thẳng `main`.** Việc ghi ở mục 3 là một ngoại lệ ghi sổ cùng loại với các ngoại lệ ADR-0013 đã ghi nhận:
   - chỉ một tệp, chỉ ghi thêm;
   - kiểm toán bắt mọi lần viết lại;
   - không phải quyền sửa luật, mã hay `SAFETY_STATE`.

   Đây là một đường ghi **mới**. ADR-0013 không tự bao đường này. Gộp ADR-0017 **không** cho quyền kích hoạt workflow ghi `seals.jsonl`. Trước khi chạy lần đầu phải có đủ:
   - Owner ghi ACCEPTED cho QĐ-S3 trong bảng trạng thái, và chấp thuận riêng, bằng chữ, ngoại lệ ghi `main` cho đúng tệp `experiments/SCN-001/seals.jsonl` và đúng workflow đó;
   - PR S0f có test cho: chỉ-ghi-thêm; dấu nhận của `github-actions[bot]`; từ chối dòng trùng (họ, lô); kiểm toán trực tuyến trong `tools/ledger_audit.py`; khôi phục khi workflow lỗi giữa chừng mà không tạo dòng thứ hai hay dấu nhận giả;
   - L-09 và Owner gộp PR S0f.

### QĐ-S4. Lớp đọc phủ

1. **Bộ thu**, chạy trên GitHub Actions, không dùng AI, chi phí 0.
   - Mỗi ngày đọc chỉ mục công bố thông tin của sở và ghi metadata vào `experiments/SCN-001/index/`: mã, tiêu đề, url, `published_at` theo metadata của sở, `accessed_at`, `sha256`, `bytes`.
   - Pha 0 nạp lại chỉ mục và BCTC quý của 8 quý gần nhất để tính baseline.
   - Bản gốc nguyên byte lưu thành tệp đính kèm GitHub Release theo tháng (object storage theo `STORAGE_POLICY.md`), không commit vào git.
   - Mất tệp hoặc lệch hash thì tài liệu không dùng được (fail-closed).
2. **THẺ ĐỌC.** Ghế AI đọc tài liệu của các mã trong lô, trong khoảng trước giờ niêm phong, và ra một thẻ cho mỗi tài liệu:
   - các con số và sự kiện, mỗi mục kèm trích nguyên văn và địa chỉ `<doc_id>:p<trang>:<đoạn>`;
   - mục "so với lời cũ": dẫn các phát biểu cùng chủ đề của chính doanh nghiệp đó ở tài liệu trước (có địa chỉ), và ghi khớp, lệch hay đổi.
3. CI chỉ nhận thẻ khi mỗi trích dẫn có trong văn bản của tệp đã ghim và số liệu đọc được từ chính câu trích. Đây là máy kiểm trích nguyên văn của §5.
4. Thẻ là đầu vào của dự báo, không phải KNOWLEDGE_NOTE. Thẻ không nâng hạng tri thức, không làm căn cứ cho CITED hay mệnh đề.
5. Ghế khác nhà cung cấp với ghế đọc kiểm 5% số thẻ mỗi lô, chọn theo hash ghim trước. Tỷ lệ sai quá 5% thì báo lỗi cho họ đó (như cột dừng G2); lô vẫn được tính.
6. Lô dùng chế độ "sách mở": được dùng mọi thông tin công khai trước giờ niêm phong. Thẻ đã dùng phải được dẫn trong `card_refs`.

### QĐ-S5. Máy chấm

1. Công cụ chấm là mã, không dùng AI.
   - SCN-LN: trích hai con số từ tài liệu phân định đã ghim.
   - SCN-CT, SCN-PH: khớp tiêu đề với bảng cụm từ.
   - Kết quả ghi vào `experiments/SCN-001/resolutions.jsonl`, kèm trích nguyên văn và địa chỉ. CI kiểm như kiểm thẻ.
2. Khi công cụ không chắc (PDF dạng ảnh, nhiều bảng, tiêu đề ngoài bảng cụm từ), câu được ghi `CAN_NGUOI_PHAN_DINH`. Khi đó một ghế khác nhà cung cấp với ghế dự báo phân định, theo luật của ADR-0003.
3. Mỗi lô, một ghế khác nhà cung cấp đối chiếu 5% số câu máy đã chấm. Chỉ cần một lỗi YES/NO là dừng chấm họ đó cho tới khi sửa công cụ và chấm lại cả họ.
4. Người thiết kế (Claude) không phân định.

### QĐ-S6. Phép thử và phán quyết (đăng ký L-06 trước lô đầu)

1. **Đăng ký.** Mỗi họ có một dòng trong sổ đăng ký thử trước lô sơ bộ, ghi baseline, thước đo, cách chọn N và ngưỡng.
2. **Baseline,** ghim trước và tính tại giờ niêm phong: p0 = (k + 4m) / (n + 4), kẹp trong [0,05; 0,95].
   - SCN-LN: k là số quý lợi nhuận tăng so với cùng kỳ trong n ≤ 8 quý gần nhất của mã; m là tỷ lệ mã tăng của quý gần nhất đã có số.
   - SCN-CT, SCN-PH: k là số năm có sự kiện ở cùng quý trong n ≤ 3 năm; m là tỷ lệ mã có sự kiện ở cùng quý năm trước.
3. **Thước đo chính:** hiệu ghép cặp từng câu d = Brier(SCN) − Brier(baseline).
4. **Lô sơ bộ.** Lô niêm phong cuối quý đầu tiên sau pha 0 chỉ dùng để đo σ_d, thông lượng và tỷ lệ VOID. Lô này không vào phán quyết. Sau lô sơ bộ, N được chốt theo:
   - n = ((z₁₋₀,₀₅/₆ + z₀,₈₀) · σ_d / Δ)², với Δ = 0,02 (hai phía 5%, hiệu chỉnh cho 3 họ, độ mạnh 80%);
   - với σ_d = 0,10 thì n ≈ 262 câu mỗi họ;
   - sàn là 300 câu mỗi họ cho tổng 4 lô xác nhận.
   - **262 và 300 là ước lượng sơ bộ**, giả định các hiệu d độc lập. Đó không phải bảo đảm độ mạnh 80%. Câu cùng quý, cùng ngành hay cùng doanh nghiệp tương quan với nhau, nên số đơn vị độc lập hiệu dụng nhỏ hơn số câu.
   - Sau lô sơ bộ, ước lượng hệ số tương quan nội cụm (ICC) của d theo hai cách gom cụm ở mục 5: theo doanh nghiệp, và theo quý × ngành cấp 1.
   - N yêu cầu = n × DEFF lớn nhất của hai cách, với DEFF = 1 + (m̄ − 1) · ICC, m̄ là cỡ cụm trung bình dự kiến.
   - Thông lượng không đủ N yêu cầu thì bỏ họ đó (QĐ-S8 mục 3), không hạ N.
5. **Phán quyết** chỉ ra một lần, trên đúng 4 lô xác nhận kế tiếp (đủ 4 quý). Một họ PASS khi đạt đồng thời:
   - khoảng tin cậy 95% của d̄ nằm hẳn dưới 0 dưới **mỗi** cách gom cụm đăng ký trước, sau hiệu chỉnh Holm cho 3 họ:
     - (i) bootstrap theo doanh nghiệp: lấy lại cả doanh nghiệp với mọi câu của nó qua 4 lô, phân tầng theo lô;
     - (ii) bootstrap theo quý × ngành cấp 1 (phân ngành ghim ở pha 0);
   - kết luận không đổi khi đổi cách gom cụm: một cách cho khoảng chứa 0 thì không PASS. Báo cả hai khoảng;
   - đạt ở cả phân tích chính và phân tích độ nhạy VOID (QĐ-S2);
   - d̄ < 0 ở ít nhất 3 trong 4 lô;
   - ECE ≤ 0,10 (5 nhóm);
   - không lô nào không hợp lệ.
6. **Không đạt** thì ghi NO_EDGE hoặc INCONCLUSIVE.
   - Không dùng kết quả giữa chừng để đổi giao thức (mục 9, 10).
   - Không đổi baseline hay thước đo sau khi thấy số.
   - Lần phán quyết sau phải dùng lô mới và đăng ký thử mới.
7. **Phần đo phụ.** Chọn 20% số câu theo hash ghim trước. Một phiên Claude trần dự báo các câu đó trước giờ niêm phong, với prompt riêng có hash; không dùng `CONTROL_B_PROMPT`. Báo cáo hiệu SCN trừ Claude trần để đo phần đóng góp của lớp đọc. Đây không phải điều kiện PASS.
8. **Tập VN30** được báo riêng. Nếu d̄ của tập VN30 ≥ 0 thì họ đó không được dùng cho sổ trên rổ VN30, dù đã PASS.
9. **Khóa giao thức.**
   - Trước giờ niêm phong của lô xác nhận đầu tiên, ghim vào sổ đăng ký thử (L-06) `protocol_hash`. Đó là hash của: prompt, `model_id`, khuôn THẺ ĐỌC, bảng ánh xạ chỉ tiêu, bảng cụm từ, công thức baseline, mã máy chấm, mã phân tích phán quyết, N, các cách gom cụm và ngưỡng của mục 11.
   - Mỗi dòng niêm phong mang `protocol_hash` (QĐ-S3 mục 3). CI từ chối dòng có hash khác hash đã đăng ký.
   - Đổi bất kỳ thành phần nào sau đó thì các lô xác nhận đã niêm không vào phán quyết. Các lô đó vẫn được công bố và chấm. Muốn phán quyết phải đăng ký mới và chạy lại đủ 4 lô mới.
   - Ngày niêm phong của 4 lô xác nhận được ấn định từ trước.
   - Không có quy tắc nào cho dừng sớm, bỏ lô, kéo dài, đổi N hay đổi thước đo dựa vào kết quả.
10. **Điểm trung gian và giới hạn.**
    - Tệp lô và muối được công bố từng lô (QĐ-S3 mục 5), nên điểm từng lô tính được từ dữ liệu công khai, kể cả bởi ghế dự báo. ADR này thừa nhận không bảo đảm được việc không ai xem điểm trung gian.
    - Cơ chế ngăn chọn kết quả thuận lợi là khóa giao thức ở mục 9, cùng các luật đã có: mỗi (họ, lô) đúng một dòng niêm phong, không bỏ câu.
    - Xem điểm không đổi được phán quyết. Công cụ phân tích không xuất d̄ gộp trước khi đủ 4 lô.
11. **Đơn vị độc lập không đủ thì INCONCLUSIVE**, kể cả khi đủ 300 câu. Một họ là INCONCLUSIVE khi có bất kỳ điều sau:
    - một trong hai cách gom cụm có dưới 30 cụm;
    - cỡ mẫu hiệu dụng n_eff = (số câu đã chấm) / DEFF, với DEFF đo lại trên 4 lô xác nhận, nhỏ hơn n của công thức ở mục 4.
12. **Bốn quý là số cụm thời gian rất nhỏ.** Biến thiên giữa quý không ước lượng tin cậy được từ 4 lô. Điều kiện "d̄ < 0 ở ít nhất 3 trong 4 lô" chỉ là kiểm tính nhất quán, không thay ước lượng đó. Báo d̄ và khoảng tin cậy của từng lô.

### QĐ-S7. Cổng cấp tín hiệu

1. Họ PASS chỉ được gọi là "ĐỦ ĐIỀU KIỆN TÍN HIỆU". Đó không phải mô hình ACTIVE và không đổi thang vốn.
2. Muốn dùng cho danh mục giấy thì phải có:
   - một ADR riêng cho phép thử tiến FWD-002: sổ bóng dùng tín hiệu của họ đó trên rổ VN30 đã ghim, cùng luật F1, R1, phí, lô, khóa trần/sàn;
   - đăng ký L-06 trước ngày bắt đầu của FWD-002;
   - L-09 và Owner gộp.
3. FWD-001 không đổi.
4. Lý do tách: đoán đúng chỉ tiêu chưa chắc ra lãi vượt sau phí, vì giá có thể đã phản ánh thông tin đó. Chỉ phép thử tiến trên giá trả lời được câu này.

### QĐ-S8. Vận hành và chi phí

1. Không mở API trả phí; ARCHITECTURE §7 giữ nguyên.
2. Ghế dự báo và ghế đọc chạy trong gói thuê bao (Claude Project hoặc Claude Code, kể cả chạy theo lịch).
3. Thông lượng đo ở lô sơ bộ quyết định N. Nếu không đủ sàn 300 câu cho một họ thì bỏ họ đó, không hạ sàn.
4. Bộ thu, máy chấm và kiểm toán chạy trên GitHub Actions.
5. Mở API (ví dụ để đọc phủ hằng ngày cho FWD-002) là quyết định riêng của Owner theo mốc xem xét ở §8.

### QĐ-S9. Điều kiện của pha 0 (trước lô sơ bộ)

1. Một lượt GitHub Actions tải được trang chỉ mục công bố thông tin và một tệp BCTC từ trang của HOSE. Môi trường đám mây của Claude đang bị chặn (403); GitHub Actions chưa được thử.
2. Ghi trạng thái pháp lý của việc tải tự động trang công bố thông tin vào manifest. L-04 cho chép nguyên văn BCTC; điều khoản sử dụng của trang chưa được kiểm.
3. Máy chấm SCN-LN đạt trên 200 BCTC quý cũ chọn ngẫu nhiên, do ghế khác nhà cung cấp đối chiếu: 0 lỗi YES/NO và ít nhất 98% con số khớp tuyệt đối. Đây là kiểm công cụ, không phải dự báo, nên L-05 không áp.
4. Ghim và có test cho bảng ánh xạ chỉ tiêu theo mẫu BCTC của từng ngành (doanh nghiệp, ngân hàng, chứng khoán, bảo hiểm) và bảng cụm từ tiêu đề của SCN-CT, SCN-PH.
5. Ghim phân ngành dùng làm cụm bootstrap, từ nguồn gốc.
6. Test niêm phong và công bố phải bắt được: niêm hai lần, công bố sai muối, công bố trễ, bỏ câu. Có kiểm đột biến.
7. Test máy chấm (QĐ-S2) phải có đủ các ca sau, kèm kiểm đột biến:
   - không có sự kiện, chỉ mục đầy đủ: ra NO;
   - có sự kiện: ra YES;
   - chỉ mục thiếu ngày hoặc hai bản chụp liền nhau không chồng lấn: ra `VOID_CHI_MUC`;
   - tài liệu công bố ngoài khoảng tính: không tính là YES;
   - BCTC công bố trễ nhưng trước `resolve_at`: chấm bình thường, có cờ `CONG_BO_TRE`;
   - không nộp tới `resolve_at`, chỉ mục đầy đủ: ra `VOID_KHONG_NOP`;
   - bản gốc lệch hash: ra `VOID_NGUON`.
8. Test phân tích phán quyết phải bắt được:
   - dòng niêm phong có `protocol_hash` khác hash đã đăng ký;
   - dưới 30 cụm;
   - n_eff dưới mức yêu cầu;
   - hai cách gom cụm cho kết luận khác nhau.

## Trạng thái từng quyết định

| Mã | Owner | Ngày |
|---|---|---|
| QĐ-S1 | PROPOSED | |
| QĐ-S2 | PROPOSED | |
| QĐ-S3 | PROPOSED | |
| QĐ-S4 | PROPOSED | |
| QĐ-S5 | PROPOSED | |
| QĐ-S6 | PROPOSED | |
| QĐ-S7 | PROPOSED | |
| QĐ-S8 | PROPOSED | |
| QĐ-S9 | PROPOSED | |

- Gộp ADR này chỉ ghi nhận văn bản, không tự duyệt quyết định nào.
- Một quyết định chỉ có hiệu lực khi Owner ghi ACCEPTED kèm ngày trong bảng này, bằng PR do Owner gộp.
- DEFERRED, REJECTED hoặc ô trống nghĩa là chưa có hiệu lực.
- Mỗi PR triển khai vẫn phải qua L-09 và Owner gộp riêng.

## Triển khai (chỉ sau khi quyết định tương ứng ACCEPTED)

Mỗi dòng là một PR nháp do Claude Code viết, ChatGPT hoặc Gemini chấm.

| Mã | Việc |
|---|---|
| S0a | Lượt Actions thử tải chỉ mục và một BCTC của HOSE; ghi chú pháp lý (QĐ-S9 mục 1–2) |
| S0b | Bộ thu chỉ mục hằng ngày; nạp lại 8 quý; lưu bản gốc vào Release |
| S0c | Máy chấm SCN-LN, bảng ánh xạ chỉ tiêu, phép thử 200 BCTC |
| S0d | Bảng cụm từ và máy chấm SCN-CT, SCN-PH |
| S0e | Tính baseline; phân ngành ghim |
| S0f | Công cụ danh sách câu, niêm phong, công bố; workflow dấu nhận; kiểm toán; test |
| S0g | Khuôn THẺ ĐỌC và máy kiểm trích dẫn |

Mốc kế hoạch, không phải cam kết:

| Thời gian | Việc |
|---|---|
| 01–03/2027 | Pha 0, sau F1 |
| 31/03/2027 | Niêm phong lô sơ bộ |
| 30/06/2027, 30/09/2027, 31/12/2027, 31/03/2028 | Niêm phong 4 lô xác nhận |
| Khoảng quý 3/2028 | Phán quyết |

## Lý do (bằng chứng, số đo)

- **Số điểm chấm.** Mỗi họ có ít nhất 300 câu đã chấm trên 4 lô, so với khoảng 12,6 điểm mỗi năm của sổ giấy.
  - Phép tính cỡ mẫu ở QĐ-S6 mục 4 là ước lượng sơ bộ, giả định câu độc lập; σ_d được đo lại ở lô sơ bộ.
  - Số đơn vị độc lập hiệu dụng nhỏ hơn số câu vì các câu tương quan theo quý, ngành và doanh nghiệp. QĐ-S6 mục 4 và mục 11 xử lý phần này.
- **Vì sao vẫn cần 4 quý.** Các câu cùng quý cùng chịu một cú sốc vĩ mô và ngành, nên tăng số câu không thay được tăng số quý; 4 lô cũng phủ đủ mùa vụ. Phán quyết đầu tiên (khoảng quý 3/2028) vì vậy không sớm hơn phán quyết của FWD-001. Cái được là:
  - phán quyết dựa trên nhiều câu hơn 12 kỳ. Tuy vậy, sức mạnh thống kê bị giới hạn bởi số cụm độc lập và chỉ có 4 quý, không phải bởi số câu;
  - đo một giả thuyết mà engine giá không đo được: lợi thế đến từ việc đọc văn bản.
- **Tập mã toàn HOSE.** Tới 30/6/2025, nhà đầu tư cá nhân đóng góp hơn 80% giá trị giao dịch ([Nhân Dân](https://nhandan.vn/chuyen-nghiep-hoa-nha-dau-tu-ca-nhan-truoc-them-nang-hang-post898192.html)). Nếu có lợi thế đọc, nó nhiều khả năng nằm ở nhóm mã ít được phân tích chứ không ở VN30.
- **Dùng lại, không thay.** Kiến trúc đã có niêm phong và dấu nhận (ADR-0003), khóa thông tin (ADR-0011), sổ thử (L-06), ghim tệp gốc (ADR-0012) và máy kiểm trích nguyên văn (§5). ADR này dùng lại các phần đó.

## Điều kiện hoàn tác (đo được, có hạn)

1. Pha 0 không đạt QĐ-S9 mục 1–3 sau 3 vòng sửa, hoặc chưa đạt tới 30/06/2027: báo Owner. Owner chọn nguồn khác bằng ADR mới, hoặc chuyển ADR này sang REVERTED.
2. Lô sơ bộ không đủ thông lượng cho sàn 300 câu của ít nhất một họ: dừng và báo Owner.
3. Hai lô liên tiếp của cùng một họ không hợp lệ, hoặc có lỗi YES/NO của máy chấm, hoặc kiểm mẫu thẻ sai quá 5%: dừng họ đó.
4. Sau phán quyết, nếu cả ba họ NO_EDGE: ghi NO_EDGE cho ba họ này. Owner quyết mở họ mới (bằng ADR mới) hoặc dừng SCN.
5. Hoàn tác không xóa lô, dấu nhận hay kết quả âm.
6. Nếu một quyết định ở đây xung đột với ADR đã ACCEPTED hoặc với L-01…L-10, phần triển khai liên quan dừng. ADR này không ghi đè ADR cũ.

## Ảnh hưởng tới ARCHITECTURE.md

Không sửa trong PR này. Khi có quyết định được ACCEPTED, một PR riêng thêm:

- §4.4 trỏ tới ADR này;
- một dòng ở §5 về THẺ ĐỌC;
- một dòng ở §7 về bộ thu và máy chấm chạy trên GitHub Actions.

Không viết bản kiến trúc mới (L-07).
