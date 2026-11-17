# Hướng dẫn vận hành

## 1. Bật quyền ghi cho GitHub Actions (bắt buộc)
Settings → Actions → General → *Workflow permissions* → chọn **Read and write permissions** → Save.

## 2. (Tùy chọn) Bật LLM phản biện
Settings → Secrets and variables → Actions → New repository secret
- Name: `ANTHROPIC_API_KEY`
- Value: API key từ console.anthropic.com
Không có key thì bước phản biện tự bỏ qua; engine vẫn chạy.

## 3. Chạy lần đầu
Tab **Actions** → *Vong hoc hang tuan* → **Run workflow** → trials = `16`. Lịch tự chạy: thứ Sáu hằng tuần, 16:30 giờ Việt Nam (ARCHITECTURE §4.3).
Lần đầu tải dữ liệu từ 2016 cho 30 mã, có thể mất 10–30 phút.

## 4. Đọc kết quả
- `reports/cycle_<ngày>.md` — báo cáo từng vòng
- `state/ENGINE_STATE.json` — trạng thái tóm tắt
- `state/model_registry.json` — mô hình và lịch sử trạng thái
- `knowledge/candidates/` — phát hiện đã qua kiểm định
- `paper/` — giao dịch giấy, NAV, quyết định
- `reports/attribution_latest.json` — tách beta / alpha

## 5. Chạy thử trên máy (không cần mạng)
```bash
pip install -r requirements.txt
TTC_HOME=/tmp/ttc_demo python -m tests.demo_synthetic init
TTC_HOME=/tmp/ttc_demo python -m tests.demo_synthetic run 1051 1540
```

## 6. Ghi một cặp dự báo A/B (Owner làm tay — ARCHITECTURE §4.1–4.2)
1. Ghế A (Claude trong Project) soạn câu hỏi có/không, nguồn phân định, ngày phân định, xác suất.
2. Ghế B: mở một chat Claude **mới**, không Project, không tệp, tắt tìm web; dán nguyên khối prompt trong `governance/CONTROL_B_PROMPT.md` rồi dán câu hỏi; chép ba dòng trả lời.
3. Tab **Issues** → **New issue** → mẫu **Forecast**. Mở hai Issue **trong cùng một ngày**: một cho ghế A, một cho ghế B, **cùng một câu chữ** ở ô question, cùng nguồn, cùng luật, cùng ngày phân định.
   - `p`, `base_rate`: chỉ ghi con số (0.35 hoặc 0,35 đều được).
   - `model_cutoff`: dạng `2026-06`.
   - `author_seat`: bắt đầu bằng tên mô hình ("Claude Project TTC", "Claude trần").
   - `prompt_hash`: ghế B dán mã hash ghi trong `CONTROL_B_PROMPT.md`; ghế A để trống.
4. Trong 1–2 phút robot `ttc-ledger` bình luận ✅ (đã ghi, kèm mã `F-<số Issue>`) hoặc ❌ kèm lý do. Bị ❌ thì mở Issue mới đã sửa; không sửa Issue cũ (sửa không có tác dụng).
5. Mỗi ghế chỉ một dự báo cho một câu hỏi. Ghi nhầm thì không xóa được: sổ chỉ ghi thêm.

## 7. Phân định khi tới hạn
1. Tới ngày `resolve_at` (giờ Việt Nam), **Owner hoặc một ghế AI khác nhà cung cấp với ghế viết** (ví dụ ChatGPT) mở nguồn đã ghi trong dự báo, tìm con số hoặc sự kiện.
2. **Issues** → **New issue** → mẫu **Resolution**: mã dự báo (`F-101`), YES/NO/VOID, đường dẫn nguồn (phải cùng tên miền đã ghi trong dự báo), đoạn trích nguyên văn, `resolver` = người đã đọc nguồn ("Owner" hoặc "ChatGPT (OpenAI)"; không được là Claude).
3. Một Issue phân định một câu hỏi; ghế A và ghế B của câu hỏi nhận cùng kết quả. Đã phân định thì không sửa được. Nguồn đã hứa không công bố → chọn VOID và ghi lý do.
4. Điểm số cập nhật ở vòng học kế tiếp: `reports/scorecard.json` mục `issue_forecasts`, và cuối tệp `reports/cycle_<ngày>.md`.

## 8. Chấm và gộp một PR (L-09, L-10)
1. PR phải có hai dòng trong mô tả: `authored_by: <ghế viết>` và `reviewed_by:` (để trống lúc mở).
2. Đưa PR cho một ghế **khác nhà cung cấp** với ghế viết để chấm, ghi rõ commit cần chấm (7 ký tự đầu SHA). Yêu cầu ghế chấm mở đầu câu trả lời bằng `GỘP ĐƯỢC — commit <7 ký tự>` hoặc `SỬA TRƯỚC — commit <7 ký tự>`.
3. Kết luận GỘP ĐƯỢC: (a) dán nguyên bản chấm thành một **bình luận** của PR; (b) rồi sửa mô tả PR, điền `reviewed_by: <ghế chấm>`. Việc "L-09 nguoi cham" chuyển xanh.
4. Có commit mới sau khi chấm → việc đó đỏ lại → chấm lại bản mới.
5. Owner bấm **Merge pull request**. Không ghế AI nào bấm thay.

## 9. Bảo vệ nhánh main (làm một lần — L-10)
Settings → Rules → Rulesets → New branch ruleset → áp cho `main` → bật **Restrict deletions** và **Block force pushes** → Create. Hai luật này không cản vòng học và robot ghi dự báo. **Không** bật "Require a pull request before merging": bật là robot không ghi được vào sổ.

## 10. Khi CI đỏ
- "Test bat buoc (chan merge)" đỏ: không gộp; đọc dòng `LỖI:` trong log và giao ghế viết sửa.
- "L-09 nguoi cham" đỏ: thiếu người chấm hoặc thiếu bình luận bản chấm đúng commit — xem mục 8.
- Vòng học đỏ ở bước "Kiem lai sau khi chay": kết quả vòng đó trái luật nên không được ghi; chụp log gửi kiến trúc sư.
