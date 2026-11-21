# Giao thức thử nghiệm HUMAN_ONLY / AI_ONLY / HUMAN_AI — bản đề xuất có cổng (21/11/2026)

- Trạng thái: **PROPOSED, chưa hiệu lực.** Chỉ là thiết kế nghiên cứu để Owner quyết phạm vi về sau. Văn bản này không mở hệ thống dự báo mới, không thêm model, API, workflow hay tệp sổ nào.
- Người viết: Claude (Anthropic). Người chấm L-09: chưa có. Owner L-10: chưa.
- Liên quan: ADR-0015 (PR #68, PROPOSED; "vượt con người" cần thí nghiệm tiến về tương lai, đăng ký trước). Giao thức này có thể thành phụ lục của ADR-0015 **nếu** Owner chấp nhận ADR đó. Không tự coi ADR-0015 là ACCEPTED.

## 0. Ranh giới với phép thử A/B hiện hành

| | Ledger A/B hiện hành | Giao thức này |
|---|---|---|
| Câu hỏi | Bộ TTC (ghế A) có hơn Claude trần (ghế B) không | Người, máy và kết hợp: bên nào tốt hơn đối chứng |
| Nhãn | ghế `A`, `B` | nhánh `HUMAN_ONLY`, `AI_ONLY`, `HUMAN_AI` (không gọi A/B/C) |
| Tệp | `ledger/predictions.jsonl`, `ledger/resolutions.jsonl` | không dùng các tệp đó; nếu được duyệt sẽ có không gian riêng (ví dụ `experiments/HAI-001/`) và mã câu hỏi tiền tố `HAI-` |
| Cỡ mẫu và phán quyết | 194 cặp bất đồng đã ghim (ADR-0003, ADR-0004) | riêng; **không đổi, không cộng dồn vào 194** |
| Nhóm B | prompt chuẩn có hash, phiên trần | **không đụng**. Không dùng `CONTROL_B_PROMPT`, không dùng câu trả lời ghế B làm nhánh AI_ONLY |

## 1. Bốn kết luận đo riêng, không suy cái này từ cái kia

| Mã | Giả thuyết | Đối chứng | Kết luận khi không đạt |
|---|---|---|---|
| H1 | AI_ONLY tốt hơn đối chứng đơn giản | baseline độc lập (mục 4) | NO_EDGE cho AI |
| H2 | AI_ONLY tốt hơn HUMAN_ONLY | cùng câu hỏi, ghép cặp | không nói "AI hơn chuyên gia" |
| H3a | HUMAN_AI tốt hơn AI_ONLY | ghép cặp | không nói "kết hợp hơn máy" |
| H3b | HUMAN_AI tốt hơn HUMAN_ONLY | ghép cặp | không nói "kết hợp hơn người" |
| H4 | Kết quả đủ tin cậy để áp dụng | khoảng tin cậy sau hiệu chỉnh nhiều phép thử, hiệu chuẩn, độ ổn định | INCONCLUSIVE (mặc định) |

- H1 đạt không kéo theo H2.
- H2 đạt không kéo theo "AI có alpha".
- H3 chỉ được nói là "kết hợp tốt hơn cả hai" khi H3a **và** H3b cùng đạt.

## 2. Hai loại bài toán

- **Track E (sự kiện, xác suất).**
  - Câu hỏi nhị phân, giải bằng nguồn chính thức đã hứa trước: chỉ tiêu BCTC quý của ngân hàng VN30, số liệu NHNN, GSO.
  - Mỗi câu có `resolve_at`, `resolution_source`, `resolution_rule`, `info_lock_at` theo đúng khuôn ADR-0011.
  - Track này khả thi trước.
- **Track P (xếp hạng / danh mục giấy).**
  - Xếp hạng các mã của rổ VN30 **đã ghim tại ngày quyết định** theo lợi suất vượt 20 phiên.
  - **Bị chặn** tới khi ma trận PIT (`PIT_RESEARCH_ELIGIBILITY_MATRIX_20261121.md`) có khoảng đủ điều kiện, và chỉ chạy tiến về tương lai.
  - Không backtest bằng LLM (L-05).

## 3. Thông tin, thời điểm và niêm phong

1. **Gói thông tin:**
   - Mỗi câu hỏi có một gói tài liệu, gồm danh sách tệp, sha256 và `published_at` < `decision_time` (công bố đúng tại `decision_time` không được dùng), ghim trước `decision_time`.
   - Ba nhánh dùng cùng gói, theo một trong hai chế độ đăng ký trước:
     - "sách đóng": chỉ gói;
     - "sách mở": gói cộng tìm kiếm, và ghi nhật ký truy vấn.
   - Không trộn hai chế độ trong một phép thử.
2. **`decision_time` cố định theo giờ Việt Nam**, ví dụ 16:30 ngày làm việc. Mọi dự báo nộp từ `decision_time` trở đi (thời điểm nộp ≥ `decision_time`) thì loại.
3. **Niêm phong kiểu commit–reveal:**
   - Mỗi nhánh nộp `sha256(dự báo ‖ muối)` lên kênh công khai có dấu thời gian của máy chủ (Issue, dấu nhận robot như Ledger) trước `decision_time`.
   - Lộ nội dung sau khi khóa.
   - Không nhánh nào thấy dự báo nhánh khác trước khi tự niêm phong.
4. **Thứ tự cho HUMAN_AI**, tránh nhiễm HUMAN_ONLY:
   - (a) chuyên gia niêm phong dự báo độc lập; đây là HUMAN_ONLY;
   - (b) AI niêm phong độc lập; đây là AI_ONLY;
   - (c) chuyên gia chỉ nhận dự báo AI và lập luận của AI sau (a) và (b), rồi niêm phong bản sửa; đây là `HUMAN_AI_REVISED`;
   - (d) song song, `HUMAN_AI_MECH`: trung bình log-odds của (a) và (b) với trọng số w = 0,5 ghim trước, không tối ưu sau.
   - Hai biến thể kết hợp tính là hai phép thử trong họ nhiều phép thử.
5. **AI_ONLY:**
   - ghi `model_id`, `model_cutoff`, hash prompt, nhiệt độ, công cụ được phép;
   - câu hỏi giải sau `model_cutoff` (L-05);
   - không dùng API trả phí khi Owner chưa mở (ARCHITECTURE §7).
6. **Chấm mù:**
   - Nhãn nhánh được thay bằng mã ngẫu nhiên khi phân định.
   - Người phân định khác người viết (như ADR-0003).
   - Quy tắc phân định là cơ học khi có thể.

## 4. Baseline độc lập (ghim trước, cùng thông tin)

- **Track E:**
  - tần suất nền tính từ dữ liệu đã ghim trước `decision_time`;
  - dự báo "giữ nguyên" khi câu hỏi là tăng/giảm;
  - đồng xu 0,5 chỉ là sàn, không phải baseline chính.
- **Track P:**
  - bình quân đều của rổ đã ghim;
  - "giữ danh mục kỳ trước" (vòng quay 0);
  - tiền mặt (vượt trội 0).
  - Không tạo feature hay mô hình mới làm baseline: không gian 13 × 3 đang khóa.

## 5. Không dự báo / không giao dịch

- Mỗi nhánh được khai "không dự báo" cho một câu **trước khi khóa**.
- Chỉ số chính chấm câu bỏ trống bằng dự báo baseline của chính câu đó, để không ai chọn câu dễ.
- Chỉ số phụ chỉ chấm các câu đã trả lời, và báo kèm tỷ lệ bao phủ.
- Track P có trạng thái CASH hợp lệ.

## 6. Thước đo

**Ba mốc thời gian, mỗi câu hỏi hoặc mỗi kỳ có đủ ba, ghim trước:**

| Mốc | Nghĩa | Dùng cho |
|---|---|---|
| `decision_time` | Mốc chốt thông tin; dự báo hoặc quyết định niêm phong trước mốc này | Mọi đầu vào (gói thông tin, giá, thành phần rổ, sự kiện quyền, nhãn chế độ thị trường) chỉ gồm thông tin có `published_at` trước `decision_time` |
| `target_end_at` | Hết kỳ nắm giữ hoặc hết kỳ mà câu hỏi đo | Định nghĩa phạm vi của kết quả; không phải lúc có dữ liệu |
| `label_available_at` | Lúc dữ liệu kết quả được công bố và quan sát được (ví dụ giá đóng cửa của `target_end_at` đã có trong kho, hoặc nguồn phân định đã công bố) | Nhãn kết quả chỉ được tính và chấm **sau** mốc này |

Quy tắc:

- `decision_time` < `target_end_at` ≤ `label_available_at`.
- Không đầu vào nào có `published_at` từ `decision_time` trở đi: đầu vào hợp lệ khi `published_at` < `decision_time`. Đúng tại `decision_time` tính là sau mốc khóa (đóng khi nghi ngờ).
- Không nhãn nào được tính, xem hay chấm trước `label_available_at`.

- **Track E:**
  - Brier là chỉ số chính.
  - Log loss, với p kẹp [0,05; 0,95] như Ledger.
  - Hiệu chuẩn: đường tin cậy theo 5 nhóm và ECE.
  - Phân biệt: AUC.
  - Brier skill so với baseline.
  - Mọi so sánh là hiệu theo từng câu ghép cặp.
- **Track P:**
  - lợi suất vượt rổ bình quân đều **sau** phí, thuế, trượt giá và lệnh không khớp ở khóa trần/sàn (như giấy ADR-0008), có giới hạn tham gia khối lượng;
  - sụt giảm lớn nhất, vòng quay, tỷ lệ lệnh không khớp;
  - độ ổn định theo chế độ thị trường. Nhãn chế độ thị trường (dùng để phân nhóm) chỉ dùng thông tin công bố trước `decision_time`; nhãn kết quả chỉ tính và chấm sau `label_available_at`.

## 7. Thống kê, cỡ mẫu, dừng

- **Họ phép thử đăng ký trước:** H1, H2, H3a, H3b, nhân với hai biến thể kết hợp ở H3. Hiệu chỉnh Holm với α = 0,05 hai phía.
- **Khoảng tin cậy:** bootstrap theo khối, cụm theo ngày phân định (các câu giải cùng ngày tương quan).
- **Cỡ mẫu Track E** là giả định lập kế hoạch, phải kiểm bằng thử sơ bộ; dữ liệu thử sơ bộ không vào phép thử xác nhận.
  - Với hiệu Brier cần phát hiện Δ = 0,02 và độ lệch chuẩn của hiệu ghép cặp khoảng 0,10, độ mạnh 80%:
    - α = 0,05 cần khoảng 196 câu;
    - ngưỡng Holm chặt nhất (α/6) cần khoảng 300 câu đã phân định cho mỗi nhánh.
- **Track P:** với 20 phiên một kỳ, khoảng 12 kỳ một năm. Muốn phát hiện vượt trội 2% mỗi kỳ khi độ lệch chuẩn 5% cần khoảng 49 kỳ, tức khoảng 4 năm. **Mặc định chờ INCONCLUSIVE nhiều năm.** Không rút ngắn bằng cách đổi thước đo sau khi nhìn số.
- **Dừng:**
  - Cỡ mẫu cố định. Phán quyết chỉ trên N câu đầu tiên đã đăng ký, theo thứ tự đăng ký. Không nhìn trộm, không kéo dài.
  - Câu VOID tính theo hướng bất lợi cho giả thuyết đang xét (như ADR-0003).

## 8. Điều kiện bác bỏ và hủy, đăng ký trước

| Điều kiện | Hệ quả |
|---|---|
| Khoảng tin cậy hiệu Brier (AI − baseline) chứa 0 hoặc nghiêng về baseline | H1 thất bại: NO_EDGE |
| ECE của AI_ONLY > 0,10 | AI không hiệu chuẩn: H4 thất bại dù Brier tốt |
| HUMAN_AI không tốt hơn **cả** HUMAN_ONLY lẫn AI_ONLY | Không tuyên bố kết hợp |
| Dự báo niêm phong từ lúc khóa trở đi (≥ `decision_time`), sai hash gói, tài liệu `published_at` ≥ `decision_time` | Câu đó VOID, tính bất lợi |
| VOID > 10% số câu, hoặc một vi phạm quy trình có chủ đích | Hủy phép thử, giữ toàn bộ dữ liệu, báo cáo âm |
| Track P: tỷ lệ lệnh không khớp > 5% (ngưỡng ADR-0008) | Xét lại mô hình khớp trước mọi kết luận |

## 9. Quản trị và pháp lý

- **L-02:** đầu ra là xác suất về sự kiện và chỉ tiêu, hoặc xếp hạng nghiên cứu trên danh mục giấy. Không phải lời khuyên giao dịch cho mã cụ thể.
- **L-03:** danh tính chuyên gia được ẩn danh bằng mã. Không đưa thông tin cá nhân, vốn hay vị thế thật vào kho.
- **L-05:** AI chỉ được chấm trên câu giải sau ngày cắt dữ liệu của mô hình.
- **L-06:** mọi biến thể (nhánh, trọng số, chế độ sách) đăng ký trước trong một sổ có hash chuỗi riêng.
- **L-09:** người thiết kế giao thức (Claude) không chấm phán quyết của giao thức.

## 10. Cổng trước khi chạy

1. Owner quyết phạm vi: Track E trước; có tuyển chuyên gia hay không.
2. ADR riêng hoặc phụ lục ADR-0015 đã ACCEPTED, gồm tệp, workflow nhận Issue, sổ đăng ký thử nghiệm.
3. L-09 khác nhà cung cấp chấm ADR và mã intake.
4. Thử sơ bộ để ước lượng độ lệch chuẩn, rồi ghim N và ngưỡng.
5. Track P thêm điều kiện: có khoảng PIT đủ điều kiện, thành phần rổ đã ghim tại mọi ngày quyết định, giá đủ cho mọi mã.

**Mặc định khi chưa đủ bằng chứng: INCONCLUSIVE. Kết quả âm được giữ và công bố như kết quả dương.**
