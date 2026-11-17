# ADR-0004: Đóng bốn việc tồn sau gộp PR #28 (bản chấm vòng 10 của ADR-0003)
- Ngày: 2026-11-17
- Trạng thái: PROPOSED (ACCEPTED khi Owner gộp PR chứa tệp này)
- Người đề xuất: Claude (kiến trúc sư trưởng)
- Người chấm: ghế khác nhà cung cấp (L-09), ghi ở PR
- Owner duyệt: khi gộp PR

Bản chấm vòng 10 của PR #28 (ChatGPT, 17/11/2026; nguyên văn ở bình luận PR #28) xếp bốn việc vào nhóm "việc tồn sau gộp", không chặn gộp. ADR này đóng cả bốn.

## Quyết định
1. **MEDIUM — dự báo thiếu dấu nhận đúng hạn làm kiểm toán đỏ tới `resolve_at`.** Giữ nguyên hành vi; đóng bằng quyết định, không bằng mã. Lý do: mọi cơ chế "hủy sớm" chỉ có thể dựa vào bằng chứng "dòng thiếu dấu nhận hợp lệ", mà chủ kho tự tạo được bằng chứng đó (xóa bình luận dấu nhận — giới hạn đã công khai ở ADR-0003). Cơ chế như thế là một cửa hủy tùy ý trước hạn, đúng thứ vòng chấm 9 đã đóng. Kiểm toán đỏ trong trường hợp này là đỏ thật (chưa có bằng chứng hợp lệ), không phải đỏ giả, và có đường phục hồi khi tới hạn. Điều kiện xét lại giữ như ADR-0003 (xảy ra ≥ 2 lần trong 90 ngày → ADR mới).
2. **LOW — tên gọi khóa chọn mẫu.** Mẫu chốt là 194 cặp bất đồng đầu tiên **theo số Issue hoàn tất cặp** (số Issue lớn hơn trong hai dự báo A, B của cặp), không phải "theo thứ tự ghi dự báo" — vị trí dòng trong sổ có thể khác thứ tự số Issue khi hai robot chạy xen kẽ. Mã không đổi; sửa cách gọi ở `engine/ledger.py`, ARCHITECTURE §4.2, hướng dẫn vận hành.
3. **MEDIUM — Brier theo ghế chịu ảnh hưởng của VOID có chọn lọc.** Báo cáo in thêm cho mỗi ghế `brier_void_worst` (khóa `void.by_seat` của `issue_forecasts` trong `reports/scorecard.json`, và dòng VOID của báo cáo vòng học): Brier trên mọi dự báo đã đóng, trong đó mỗi dự báo VOID tính như kết quả ngược với phía nó đứng (`max(p, 1−p)²`). Hủy có chọn lọc chỉ làm con số này xấu đi, nên khoảng cách giữa `brier` và `brier_void_worst` cho thấy VOID ảnh hưởng tới đâu. Phán quyết A–B vẫn chỉ dựa vào phép kiểm định chốt mẫu.
4. **MEDIUM — khoảng chuyển tiếp của mốc v3.0.2.** Ghim mốc cố định trong `config.yaml`: `research.v302_boundary = c777f91392946ed613417c4e9ae494dfcbc9322f` (đầu `main` ngay trước khi gộp PR #28, tức cha thứ nhất của commit gộp `0b0bffc`). `tools/ledger_audit.py` chỉ miễn kiểm "đăng ký trước kết quả" cho commit **nằm trong lịch sử của mốc** (vòng học bản cũ). Mọi commit khác — kể cả nhánh tách từ lịch sử cũ rồi gộp vào sau — bị kiểm ở mọi lượt, bất kể commit gốc của lượt kiểm. Mốc không đổi được: khác giá trị ở commit gốc, hoặc bị xóa, là lỗi ở cả chế độ PR (so với đầu `main` lúc gộp — cha thứ nhất của commit gộp mà GitHub dựng cho PR — không so với `base.sha` có thể đã cũ của sự kiện) lẫn `main`, và lượt kiểm đó vẫn dùng mốc của commit gốc nên đổi mốc không miễn được commit nào; commit mốc vắng trong kho là lỗi; kho có `research.legacy_pin` mà thiếu mốc là lỗi của `tools/validate.py`. Kho chưa khai mốc (kho giả lập trong test) dùng lại cách cũ theo tệp mốc.

## Lý do
Bốn việc đều do người chấm độc lập nêu và xếp loại. Việc 2–4 sửa được bằng một thay đổi nhỏ có test; việc 1 không có cách sửa nào không mở lại cửa đã đóng, nên quyết định giữ và ghi rõ lý do.

## Giới hạn (nói thẳng)
- Việc 4: như mọi phép kiểm chỉ-ghi-thêm của kho, phép kiểm "mốc không đổi" so với commit gốc của lượt kiểm. Người có quyền quản trị xóa mốc, để `main` đỏ quá 26 giờ (`tools/validate.py` báo thiếu mốc suốt thời gian đó), rồi thêm lại một mốc khác thì các lượt kiểm sau không còn commit gốc mang mốc cũ để so. Việc đó để lại hai lượt kiểm đỏ và hai commit sửa `config.yaml` trong lịch sử; máy không chặn được.
- Việc 3: `brier_void_worst` là cận xấu nhất, không phải ước lượng: nó coi mọi dự báo VOID là sai.

## Điều kiện hoàn tác
- Việc 4: kiểm toán báo lỗi mốc (commit mốc không tìm thấy) cho một lượt kiểm có lịch sử đầy đủ → sửa bằng PR riêng; không bỏ mốc.
- Việc 3: `brier_void_worst` làm vỡ báo cáo vòng học → gỡ trường đó bằng PR riêng.

## Ảnh hưởng tới ARCHITECTURE.md
§4.2 (cách gọi khóa chọn mẫu).
