# ADR-0001: Hợp nhất sáu bản kiến trúc thành ARCHITECTURE.md v3.0
- Ngày: 2026-10-22
- Trạng thái: PROPOSED
- Người đề xuất: Claude (kiến trúc sư trưởng)
- Người chấm: chưa có (Owner quyết định giai đoạn xây kiến trúc do Claude làm một mình); ghế thi công độc lập sẽ phản biện hồi cứu khi được lập
- Owner duyệt: khi gộp PR TTC-0

## Quyết định
Một tệp kiến trúc duy nhất có hiệu lực (`architecture/ARCHITECTURE.md`, v3.0). Sáu bản cũ giữ nguyên chỗ, liệt kê trong `architecture/ARCHIVE.md` là SUPERSEDED. Ban hành `governance/LAWS.md` (L-01…L-10). Mở đường ghi dự báo qua GitHub Issue "Forecast" + workflow đóng dấu thời gian và hash chuỗi, không cần API trả phí.

## Lý do
Bản hiểu 21/10/2026 (commit 3c9f69d): 6 bản kiến trúc viết trong một ngày rồi đóng băng 24 ngày; 0 dự báo trong Ledger; thư viện và học viện rỗng; nửa học phụ thuộc hoàn toàn API đã đóng. Nghiên cứu bằng chứng 22/10: kỷ luật, chi phí, kế toán ảnh hưởng kết quả đầu tư nhiều hơn dự báo vĩ mô; LLM có thiên lệch nhìn trước nên kiểm định phải ghi trước ngày giải; thước đo A–B cần ~194 bất đồng đã chấm.

## Điều kiện hoàn tác
Nếu sau 30 ngày kể từ ngày gộp, `ledger/predictions.jsonl` có dưới 20 dự báo hợp lệ, mở ADR-0002 xét thu hẹp v3.0 về đúng phần Ledger + Thư viện tầng 1. Nếu `tools/validate.py` hoặc workflow nhận dự báo làm CI đỏ liên tục 5 ngày không sửa được, hoàn tác phần G của PR TTC-0 bằng PR riêng; ARCHITECTURE.md vẫn giữ.

## Ảnh hưởng tới ARCHITECTURE.md
Toàn bộ (bản đầu tiên của tệp).
