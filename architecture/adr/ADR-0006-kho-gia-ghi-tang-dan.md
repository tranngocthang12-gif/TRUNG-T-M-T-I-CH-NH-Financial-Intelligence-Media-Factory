# ADR-0006: Kho giá ghi tăng dần (C2)
- Ngày: 2026-11-17
- Trạng thái: ACCEPTED 17/11/2026 (Owner gộp PR #30, commit gộp `f9f3417`)
- Người đề xuất: Claude (kiến trúc sư trưởng)
- Người chấm: Gemini (Google) — `GỘP ĐƯỢC — commit 5b90973` (bình luận PR #30)
- Owner duyệt: khi gộp PR. Lệnh gốc của Owner (17/11/2026, chat vận hành): "Bạn làm được gì thì làm ngay" cho các việc còn lại sau rà soát kiến trúc.

## Quyết định
1. Kho cũ `data/store/prices.csv.gz` (73.282 dòng, 04/01/2016–16/11/2026) **đóng băng**: không ghi lại nữa, không xóa. Nó là bằng chứng giá gốc tới ngày gộp.
2. Dòng giá mới vào `data.store_dir` = `data/store/prices/`, mỗi **tháng giao dịch** một tệp CSV `YYYY-MM.csv` (không nén). `engine/data.save_store` chỉ **nối thêm** vào cuối tệp tháng các dòng `(date, ticker)` chưa có trong kho; thứ tự trong tệp là thứ tự quan sát (`observed_at`). Dòng đã có thì giữ nguyên bản quan sát đầu tiên, kể cả khi người gọi truyền vào giá đã sửa (đúng luật point-in-time vốn có của `append_rows`).
3. `engine/data.load_store` đọc kho cũ cùng mọi tệp tháng; trùng `(date, ticker)` thì giữ bản quan sát đầu tiên. Trên dữ liệu thật, kết quả trùng từng dòng với kho cũ.
4. Kiểm toán (`tools/ledger_audit.py`, mục 1a): từ khi `config.yaml` ở commit gốc có `data.store_dir`, kho cũ phải giữ nguyên từng byte và mỗi tệp tháng ở commit gốc phải còn và là tiền tố nguyên từng byte của bản hiện tại. Commit gốc còn ở trước ADR này (vòng học bản cũ còn ghi lại kho cũ) thì không kiểm, để lượt kiểm vắt qua lúc gộp không đỏ giả.

## Lý do
- §4.3 và C2: mỗi vòng học ghi lại cả tệp nén 1,3 MB, nên git lưu thêm một bản 1,3 MB mỗi tuần mà không bản nào chung phần với bản trước; lịch sử phình theo thời gian, và "giữ bản quan sát đầu tiên" chỉ được giữ bằng mã, không bằng thứ kiểm được từ bên ngoài.
- Tệp tháng không nén chỉ đổi ở phần đuôi: git nén chênh lệch, mỗi tuần thêm vài chục KB. Kiểm "tiền tố nguyên từng byte" là cùng một phép kiểm với sổ dự báo (L-05), nên dữ liệu gốc của engine được neo như sổ.
- Không di chuyển dữ liệu cũ: tránh một commit lớn và tránh phải chứng minh bản chuyển trùng bản gốc.

## Điều kiện hoàn tác (đo được, có hạn)
Sau 8 vòng học hằng tuần (khoảng 15/01/2027): nếu kiểm toán đỏ vì kho giá mà không do ai sửa tay, hoặc thời gian đọc kho (`load_store`) vượt 10 giây trên GitHub Actions, thì mở ADR xét lại cách chia tệp.

## Giới hạn
- Như mọi phép kiểm chỉ-ghi-thêm, phép kiểm so với commit gốc của lượt kiểm; force-push thì chỉ ruleset của `main` chặn được (L-10).
- Dòng trễ của một ngày cũ (một mã thiếu dữ liệu hôm đó, tuần sau mới có) được nối vào cuối tệp tháng của ngày đó; tệp vì vậy không sắp theo ngày. Người đọc dùng `load_store`, không đọc thẳng tệp.

## Ảnh hưởng tới ARCHITECTURE.md
§4.3: "Kho dữ liệu đổi sang ghi tăng dần (C2 — chưa làm, ADR riêng)" → "đã làm (ADR-0006)".
