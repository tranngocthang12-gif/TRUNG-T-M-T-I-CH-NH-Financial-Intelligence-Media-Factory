# Đối chiếu nghiên cứu AI đầu tư — bốn nhóm bằng chứng Owner nêu (21/11/2026)

- Người viết: Claude (Anthropic). Chưa L-09. Đây là ghi chú làm việc, không phải KNOWLEDGE_NOTE. Không có hạng `SOURCED` hay `CITED`, không vào thư viện, không dùng cho quyết định.
- **Không tài liệu gốc nào được mở trong phiên này.** Chính sách mạng của môi trường chặn các máy chủ: `arxiv.org`, `export.arxiv.org`, `internet.cnmv.es`, `gsb-faculty.stanford.edu`, `www.sec.gov`, `amplifyetfs.com` (kiểm bằng `curl`, cả 7 lần đều không kết nối được).
- Mọi chi tiết dưới đây đến từ **kết quả công cụ tìm kiếm**: tiêu đề, URL, đoạn trích do công cụ tóm tắt. Nguồn loại này có thể diễn đạt sai.
- Không chép nguyên văn quá 15 từ (L-04). URL được ghi là "thấy trong kết quả tìm kiếm, chưa mở", không phải URL đã kiểm.
- Thang trạng thái:
  - `VERIFIED`: đã đọc bản gốc.
  - `PARTIAL`: chỉ thấy tóm tắt hoặc bản thứ cấp.
  - `UNVERIFIED`: không tìm thấy.
  - **Không mục nào đạt VERIFIED.**

## Bảng đối chiếu

| # | Tuyên bố Owner nêu | Nguồn tìm được (chưa mở) | Trạng thái | Nó chứng minh gì (theo tóm tắt) | Backtest hay thực tế | Rủi ro phương pháp | So với ai | Phí, rủi ro, tác động thị trường |
|---|---|---|---|---|---|---|---|---|
| 1 | Stanford: danh mục AI so với nhà quản lý quỹ 1990–2020, "khoảng 7%" | deHaan, Lee, Liu, Noh, *The Shadow Price of "Public" Information*, working paper Stanford GSB, 05/2025, chưa bình duyệt. PDF trên `gsb-faculty.stanford.edu`; bài GSB Insights 06/2025 | PARTIAL | Mô hình học máy (rừng ngẫu nhiên, **không phải LLM**) điều chỉnh một phần danh mục thật của khoảng 3.300 quỹ cổ phiếu Mỹ chủ động mỗi quý, thay mã mô hình không ưa bằng vị thế thụ động. Theo tóm tắt, phần điều chỉnh vượt khoảng 93% nhà quản lý. "7%" nhiều khả năng là phần bù (khoảng 7% nhà quản lý không bị vượt); đây là suy luận, **chưa đọc thấy trong bản gốc** | Backtest phản thực tế | Nhiều biến dự báo (khoảng 170) dựa trên các bất thường được công bố sau 1990, nên có rủi ro nhìn trước hoặc khai thác dữ liệu. Giả định chỉ một quỹ dùng công cụ; tác giả được dẫn rằng lợi thế mất nếu ai cũng dùng | Nhà quản lý **trung bình**, không phải người giỏi nhất | Có nhắc chi phí giao dịch theo một đoạn trích; chưa kiểm được con số chính đã sau phí hay chưa |
| 2 | Cơ quan quản lý chứng khoán Tây Ban Nha, 03/2026: rủi ro chatbot khuyến nghị cổ phiếu, lỗi khái niệm, lỗi dây chuyền, tài liệu gốc | Crisóstomo, Mykhalyuk (CNMV), *Large Language Models and Stock Investing: Is the Human Factor Required?*, CNMV Documento de Trabajo số 96; arXiv 2603.19944 (03/2026, sửa 04/2026); SSRN | PARTIAL | Thử **thời gian thực, ngoài mẫu** 04/2025–01/2026 (10 vòng tháng) trên rổ IBEX 35. Bốn chatbot, ba kiểu prompt. Tóm tắt nêu lỗi khái niệm tài chính, lỗi lan sang vòng sau, thông tin lỗi thời hoặc bịa. Bám vào hồ sơ công bố chính thức làm kết quả tốt hơn; muốn vượt thị trường cần con người giám sát đáng kể. Diễn đạt của Owner đúng về ý; "tài liệu gốc" là **cách giảm lỗi**, không phải rủi ro | Thực tế tiến về tương lai, nhưng danh mục giấy | Mẫu rất nhỏ (10 tháng, 35 mã). Các con số báo chí (ví dụ lợi suất trên 80%) chưa kiểm và rất nhiễu | Chỉ số IBEX 35, không so với chuyên gia | Chưa xác nhận phí giao dịch |
| 3 | Nghiên cứu hai thập kỷ, hơn 100 cổ phiếu: lợi thế chiến lược LLM giảm khi thử dài hơn | Li, Kim, Cucuringu, Ma, *Can LLM-based Financial Investing Strategies Outperform the Market in Long Run?* (FINSABER), arXiv 2505.07078 (05/2025, nhiều phiên bản; một bản ghi chấp nhận tại KDD 2026, chưa kiểm); mã nguồn `waylonli/FINSABER` | PARTIAL | Backtest khoảng 20 năm (đoạn trích ghi 2004–2024; một đoạn khác ghi 2000–2024) trên hơn 100 mã. Lợi thế báo cáo trước đây của chiến lược LLM **suy giảm đáng kể** khi mở rộng thời gian và số mã. Chiến lược mua và giữ thụ động đứng gần đầu. LLM quá thận trọng khi thị trường lên, quá mạo hiểm khi xuống. Diễn đạt của Owner đúng | Backtest | Có xét thiên lệch sống sót (danh sách S&P 500 lịch sử) và data snooping theo tóm tắt. **Không loại được việc LLM đã "nhớ" kết quả** vì giai đoạn thử trùng dữ liệu huấn luyện; chính L-05 cấm kiểu kiểm định này ở TTC | Chiến lược thụ động, quy tắc, ML, RL; không so với người | Có phí ở một phiên bản (chưa kiểm chi tiết) |
| 4 | ETF AIEQ so với S&P 500, kèm giới hạn so sánh | Hồ sơ N-CSR trên `sec.gov` và trang tổ chức phát hành `amplifyetfs.com/aieq` (thấy trong kết quả tìm kiếm, chưa mở) | PARTIAL | Theo trích đoạn N-CSR (số tại 30/09/2025, NAV, bình quân năm): 1 năm 19,68% so với 17,60%; 5 năm 8,71% so với 16,47%; từ khi lập quỹ (17/10/2017) 9,60% so với 14,73% của S&P 500 TR. Tức là **kém khoảng 5 điểm phần trăm mỗi năm** từ khi lập. Phí quản lý 0,75%. Chiến lược đổi đơn vị quản lý năm 2024 | Thực tế (quỹ niêm yết) | Một quỹ còn sống không nói gì về các quỹ AI đã đóng (thiên lệch sống sót của sản phẩm). Rổ và phong cách khác S&P 500; phí và vòng quay khác quỹ chỉ số; người quản lý thay đổi | Chỉ số thị trường, không so với chuyên gia | Số là sau phí quỹ (NAV) |

## Điều có thể chuyển sang cổ phiếu Việt Nam (đều chưa kiểm định tại HOSE)

1. **Kiểm thử ngắn thổi phồng lợi thế** (nhóm 3). TTC đã có cơ chế cùng hướng: L-06 sổ thử, Bonferroni, DSR. 222 lần thử của engine đều REJECTED.
2. **Bám tài liệu gốc và có người giám sát làm giảm lỗi của chatbot** (nhóm 2). Cùng hướng với L-01 và cổng `SOURCED/CITED`, nhưng mẫu của CNMV quá nhỏ để coi là bằng chứng hiệu quả.
3. **Kết quả sống thật của sản phẩm AI có thể thua chỉ số rẻ sau phí** (nhóm 4). Đối chứng thụ động phải luôn có trong mọi phép thử.
4. **"Vượt nhà quản lý trung bình" khác "vượt người giỏi nhất" và khác "tạo alpha sau phí"** (nhóm 1). Ba kết luận phải đo riêng, như giao thức HUMAN/AI/HYBRID cùng ngày.

## Điều không suy rộng được sang HOSE

- **Biên độ ±7% và khóa trần/sàn** cắt phân phối lợi suất và làm lệnh không khớp. Các nghiên cứu Mỹ và Tây Ban Nha không có ràng buộc này.
- **Không bán khống phổ thông, thanh toán T+2:** thiết kế long-short (CNMV có vế bán khống theo báo chí) không thực hiện được.
- **Giới hạn sở hữu nước ngoài, thanh khoản tập trung ở vài mã, nhà đầu tư cá nhân chiếm ưu thế.**
- **Dữ liệu:** lịch sử ngắn và chắp vá. Kho TTC chưa có thành phần VN30 trước 2025-08-04, sự kiện quyền chưa xác minh, nguồn giá điều chỉnh một phần, ngày nghỉ có dòng giá (báo cáo `PRICE_INTEGRITY_B1_20261121.md`).
- **Không có ngành quỹ chủ động đủ lớn** để lặp lại thiết kế của nhóm 1.
- **Nhìn trước qua dữ liệu huấn luyện của LLM:** kết quả Việt Nam trước ngày cắt dữ liệu của mô hình có thể đã nằm trong dữ liệu huấn luyện. Chỉ phép thử tiến về tương lai là sạch (L-05).

## Việc cần để nâng lên VERIFIED

- Owner hoặc ghế khác cho phép truy cập các máy chủ trên, hoặc tải bản gốc vào kho theo quy trình ghim (sha256, ngày truy cập, giấy phép).
- Đọc phần phương pháp và bảng kết quả.
- Đối chiếu từng con số ở đây; sửa bảng nếu lệch.
- Chưa làm việc đó thì mọi con số trong bảng là **chưa kiểm**.
