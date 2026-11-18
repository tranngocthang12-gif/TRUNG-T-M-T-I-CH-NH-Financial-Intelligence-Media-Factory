# ADR-0008: Thiên lệch sống sót, ngày công bố BCTC, khóa biên độ trong giấy, sụt giảm lớn nhất
- Ngày: 2026-11-18
- Trạng thái: ACCEPTED 18/11/2026 (Owner gộp PR #31, merge `8c4fd43`, theo `docs/RESEARCH_POINT_IN_TIME_LIMITATIONS.md` đã nằm trên main). Header còn chữ PROPOSED sau khi gộp; ADR-0010 chỉ lật chữ trạng thái, không quyết định lại nội dung. Người chấm L-09 của PR #31 nằm ở bình luận PR đó, không được ghế thi công suy diễn.
- Người đề xuất: Claude (kiến trúc sư trưởng). Đầu vào: bản "Nghiên cứu GitHub — học tinh hoa đầu tư chứng khoán" (góp ý tư vấn, không phải quyết định kiến trúc) và bản đối chiếu của Claude với mã trên `main`
- Người chấm: ghế khác nhà cung cấp (L-09), ghi ở PR
- Owner duyệt: thứ tự bốn việc — Owner "ĐỒNG Ý" 18/11/2026 (chat vận hành); áp dụng khi gộp PR

## Quyết định (theo đúng thứ tự Owner đã duyệt)
1. **Thiên lệch sống sót — gắn nhãn ngay.** `config.yaml` `universe_basis: CURRENT`: danh sách `universe` là VN30 *hiện tại* dùng cho toàn bộ lịch sử backtest. Khi `universe_basis` là `CURRENT`, báo cáo chu kỳ (đầu báo cáo và trên bảng thử nghiệm) và `state/ENGINE_STATE.json` (`universe_basis`, `universe_bias`) ghi rõ: kết quả backtest bị đẩy lên so với danh sách VN30 theo từng kỳ.
   **Danh sách VN30 theo từng kỳ** là việc dữ liệu, giao ghế thi công hoặc Owner, vì cần nguồn chính thức (HOSE công bố kết quả xét duyệt định kỳ) mà máy trong phiên không đọc được. Khuôn khi nộp: `data/vn30_history.csv` với cột `effective_date,ticker,change,source_url,source_status` (`change` ∈ IN/OUT; `source_status` ∈ DA_DOI_CHIEU/CAN_DOI_CHIEU), phủ từ kỳ xét duyệt gần nhất trước ngày đầu của lịch sử giá. Engine chuyển sang thành phần theo từng ngày (`universe_basis: HISTORICAL`) bằng một PR riêng khi tệp đó phủ đủ — nhãn tự tắt khi đó.
2. **BCTC dùng theo ngày công bố.** Tài liệu `kind: FINANCIAL_STATEMENT` trong `library/SOURCE_MANIFEST.json` phải có `period_end` (ngày khóa sổ của kỳ) và `published_on` (ngày công bố công khai), với `period_end ≤ published_on ≤ accessed_on`. `engine/knowledge_notes.usable_on(man, doc_id, ngày)` là cửa duy nhất để hỏi "tại ngày này thị trường đã biết tài liệu chưa" — BCTC từ `published_on`, tài liệu khác từ `issued_on`, thiếu ngày thì trả False. Ghi chú trích BCTC phải có `effective_date` không sớm hơn ngày công bố của mọi BCTC nó trích. Mọi nơi dùng số BCTC cho một ngày về sau (dự báo, đề thi, backtest) phải qua `usable_on`.
3. **Giấy không khớp ở phiên khóa biên độ.** Ở phiên khớp, mã đóng cửa với biến động ≥ 95% biên độ (HOSE ±7%, theo `adjust.limits`, kể cả biên độ riêng của mã từng niêm yết sàn khác) coi như khóa: lệnh mua ở mã khóa trần và lệnh bán ở mã khóa sàn không khớp, ghi `UNFILLED_LIMIT_UP` / `UNFILLED_LIMIT_DOWN` vào `paper/trades.csv`, lệnh giữ lại và thử lại phiên sau.
4. **Sụt giảm lớn nhất.** `research.metrics` thêm `max_dd` (chuỗi lợi nhuận ròng theo kỳ của danh mục top-k); báo cáo có cột "Sụt giảm lớn nhất"; báo cáo và `ENGINE_STATE.json` có sụt giảm lớn nhất của NAV giấy (`paper_max_drawdown`). `research/trials.csv` giữ đúng 17 cột (L-06) — `max_dd` không vào sổ thử.

## Lý do
- Danh sách cố định hôm nay chọn trước những mã đã lớn lên; mọi IC, lợi nhuận ròng, Sharpe của backtest 2016–2026 vì thế lạc quan. Rủi ro này từng ghi ở kiến trúc v0.2 và `architecture/engines/data_evidence.md` nhưng không được mang sang v3.0. Gắn nhãn không làm kết quả đúng hơn, nhưng ngăn đọc nhầm; sửa tận gốc cần dữ liệu có nguồn.
- Với lịch sử giá tải về năm 2025–2026, lọc `observed_at ≤ as_of` sẽ xóa sạch lịch sử, không phải sửa nhìn trước. Giá đã được giữ bản quan sát đầu tiên (ADR-0006) và `test_no_lookahead` kiểm feature. Chỗ ngày quan sát thật sự quyết định là số liệu BCTC: quý IV khóa sổ 31/12 nhưng công bố cuối tháng 1 — dùng từ 31/12 là nhìn trước một tháng.
- Đóng cửa ở giá trần không luôn nghĩa là trắng bên bán, nhưng giấy không được giả định khớp ở nơi thị trường thật có thể không khớp: sai về phía thận trọng.
- Sharpe không nói danh mục có thể mất bao nhiêu từ đỉnh; Owner cần con số đó trước mọi bàn luận về tiền thật (`deployment_level: 0`).

## Không làm (theo bản nghiên cứu, đồng ý)
Không nhập Qlib, LEAN, FinRL, vectorbt hay bộ tối ưu danh mục vào kho; không chép mã thư viện có điều khoản riêng (vectorbt: Apache 2.0 kèm Commons Clause). CVaR và tối ưu danh mục để sau khi có lợi thế được chứng minh (L-KT6).

## Điều kiện hoàn tác
Điều 3: nếu sau 3 tháng `paper/trades.csv` cho thấy hơn 5% lệnh bị giữ vì khóa biên độ, xét lại ngưỡng 95% bằng dữ liệu khớp thực tế. Điều 1–2–4: không hoàn tác; điều 1 tự tắt khi có danh sách theo từng kỳ.

## Ảnh hưởng tới ARCHITECTURE.md
§4.3 và §5: thêm một dòng trỏ tới ADR này.
