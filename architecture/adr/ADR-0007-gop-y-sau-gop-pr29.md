# ADR-0007: Hai góp ý sau gộp PR #29 — điều kiện mở lại engine kịch bản; tên khóa bất đồng
- Ngày: 2026-11-17
- Trạng thái: ACCEPTED 17/11/2026 (Owner gộp PR #30, commit gộp `f9f3417`)
- Người đề xuất: Claude (kiến trúc sư trưởng), theo phản biện tư vấn của Grok (xAI) đăng ở PR #29 sau khi gộp (không phải bản chấm L-09)
- Người chấm: Gemini (Google) — `GỘP ĐƯỢC — commit 5b90973` (bình luận PR #30)
- Owner duyệt: khi gộp PR

## Quyết định
1. **Sửa điều kiện mở lại của ADR-0005** (engine kịch bản). Bỏ điều kiện "(a) sổ có ≥ 60 dự báo A+B hợp lệ". Thay bằng: (a) kiểm định chốt mẫu A–B đã ra phán quyết — đủ 194 cặp bất đồng trong phạm vi phép thử đã đóng (ADR-0003 quyết định 3, ADR-0002) — và ADR mở lại phải dẫn phán quyết đó. Giữ (b) Thư viện có ≥ 10 ghi chú CITED.
2. **Tên khóa bất đồng trong `reports/scorecard.json`**: thêm `disagreements_all` = mọi cặp bất đồng (gồm cả `event_before_date`). Từ ADR-0002, `disagreements` chỉ đếm bất đồng trong phạm vi phép thử, còn `disagreement_rate` = `disagreements_all / pairs`. Không đổi tên khóa cũ để không làm vỡ báo cáo đã có; test buộc `disagreements_all = disagreements + disagreements_out_of_scope`.

## Lý do
- 60 dự báo là cửa thoát G1 (ARCHITECTURE §8), không phải bằng chứng thư viện giúp được gì. Engine kịch bản là một tầng xây trên thư viện; mở lại nó trước khi phép thử duy nhất có phán quyết là xây tầng thứ hai trước khi biết tầng thứ nhất có tác dụng (L-KT6, L-KT10 nêu ở ADR-0005).
- Với khóa cũ có thể thấy `disagreements = 0` mà `disagreement_rate = 1`; người đọc tính lại tỷ lệ bằng `disagreements / pairs` sẽ ra số sai.

## Điều kiện hoàn tác
Điều 1: Owner ra lệnh khác (đổi phạm vi là quyền của Owner, L-10). Điều 2: không có.

## Ảnh hưởng tới ARCHITECTURE.md
Không. ADR-0005 có dòng trỏ tới ADR này.
