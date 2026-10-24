# Học viện — Chương trình v0.1 (22/10/2026)

Thứ tự xếp theo bằng chứng về mức ảnh hưởng tới kết quả đầu tư (nghiên cứu 22/10/2026; ARCHITECTURE v3.0 §5), không theo "toàn bộ vĩ mô rồi vi mô". Mỗi mảng có mức cần đạt, đề thi và dự báo chấm được. Đề thi do Claude ra, giữ kín ngoài kho tới khi thi (L-10); mỗi kỳ cùng đề cho A (có thư viện) và B (Claude trần).

| # | Mảng | Mức | Nguồn trong hàng đợi | Đề thi (loại) | Dự báo chấm được (mẫu) |
|---|---|---|---|---|---|
| 1 | Kỷ luật, chi phí, quy mô vị thế | Vận dụng | nghiên cứu Barber–Odean, Mind the Gap (lưu địa chỉ) | 2: tính chi phí quay vòng; Kelly phân số | "Quay vòng danh mục giấy quý tới ≤ X%" |
| 2 | Kế toán và BCTC, đặc thù ngân hàng | Chuyên sâu | Luật Kế toán, TT 99/2025, VAS 1/21/22/24, chế độ kế toán TCTD, BCTC 10 ngân hàng | 1: trích đúng điều khoản; 2: tính NIM, nợ nhóm 3–5, dự phòng/nợ xấu từ BCTC thật | "Nợ nhóm 3–5 của X tại 31/12 cao hơn 30/9?" |
| 3 | Chất lượng lợi nhuận, dấu hiệu gian lận | Vận dụng | Piotroski, Sloan, Beneish (địa chỉ); bản án FLC | 2: M-score từ BCTC; 3: ca mù | "Doanh nghiệp dồn tích cao năm t có ROA giảm năm t+1?" |
| 4 | Thống kê và xác suất cho đầu tư | Chuyên sâu | OpenIntro, FPP3, Brier, HLZ, Bailey–LdP | 2: Bonferroni cho 108 thử, DSR | Chính các dự báo của hệ thống: Brier, hiệu chuẩn |
| 5 | Cấu trúc vi mô thị trường và luật VN | Vận dụng | Luật CK 54/2019 + 56/2024, NĐ 155 + 245, TT 96, HOSE, BLHS 209–211 | 1: tình huống công bố thông tin, nêu điều luật và trích | "UBCK công bố ≥ 1 quyết định xử phạt thao túng trong tháng?" |
| 6 | Định giá, vi mô ứng dụng, cấu trúc ngành ngân hàng | Vận dụng | Damodaran (địa chỉ), OpenStax Economics | 2: thu nhập thặng dư cho một ngân hàng | "P/B của X sau 12 tháng trong khoảng…" |
| 7 | Vĩ mô ở mức kênh truyền dẫn | Nền → Vận dụng | dữ liệu NHNN, GSO, IMF Article IV | 1: vẽ chuỗi lãi suất → NIM → lợi nhuận | "Tăng trưởng tín dụng tháng tới theo NHNN ≥ x%?" |
| 8 | Địa chính trị, chiến tranh kinh tế | Nền (bản đồ phơi nhiễm) | văn bản chính thức về thuế quan, chỉ số GPR | 1: liệt kê mã VN30 phơi nhiễm xuất khẩu Mỹ | "Mức thuế Mỹ áp với hàng VN thay đổi trước ngày D?" |
| 9 | Kinh tế xã hội | Nền | Điều tra dân số, Khảo sát mức sống | — | gần như không thành dự báo ngắn hạn |

Điều kiện lên cấp `competency_map`: chỉ do mã gán từ `academy/results/` (A ≥ 80% trên đề kín với trích dẫn kiểm được → PRACTICED; ≥ 30 dự báo đã chấm trong mảng với Brier ≤ B → VALIDATED). Thước đo chính của toàn Học viện: độ đúng của A khi bất đồng với B; cần ~194 bất đồng đã chấm để kết luận.
