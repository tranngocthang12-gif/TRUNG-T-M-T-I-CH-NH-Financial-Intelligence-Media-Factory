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
   - `p`, `base_rate`: chỉ ghi con số (0.35 hoặc 0,35 đều được); không ghi %, không ghi chữ.
   - `resolve_at`: đúng dạng `2026-12-10`.
   - `resolution_source`: phải có **tên miền** của nguồn, ví dụ `nso.gov.vn` hoặc `https://www.sbv.gov.vn`. Lúc phân định máy chỉ nhận đường dẫn thuộc tên miền ghi ở đây.
   - `model_cutoff`: dạng `2026-06`.
   - `author_seat`: bắt đầu bằng tên mô hình ("Claude Project TTC", "Claude trần").
   - `prompt_hash`: ghế B dán mã `sha256` ở **dòng cuối** của `governance/control_b_prompts.jsonl` (mã của prompt chuẩn đang có hiệu lực); ghế A để trống.
4. Trong 1–2 phút robot `github-actions` bình luận ✅ (đã ghi, kèm mã `F-<số Issue>` và dòng **dấu nhận** `ledger-attest: …`) hoặc ❌ kèm lý do. Bị ❌ thì mở Issue mới đã sửa; không sửa Issue cũ (sửa không có tác dụng).
   - **Không sửa, không xóa bình luận ✅ của robot.** Dòng dấu nhận là bằng chứng dự báo đã có từ lúc Issue mở; mất nó thì kiểm toán sổ báo đỏ.
   - Nếu việc "Ledger intake" đỏ mà dự báo đã vào sổ nhưng chưa có bình luận ✅: vào tab **Actions**, mở lần chạy đó, bấm **Re-run all jobs** trong vòng 6 giờ kể từ lúc mở Issue (và trước ngày `resolve_at`). Robot sẽ đăng bổ sung dấu nhận, không ghi trùng.
   - Quá 6 giờ mà dự báo đã nằm trong sổ nhưng chưa có dấu nhận: vẫn bấm **Re-run all jobs** để robot đăng dấu nhận muộn. Việc "Kiem toan so" sẽ còn đỏ ở dòng đó; tới ngày `resolve_at` thì **hủy câu hỏi đó** — mở Issue mẫu **Resolution**, chọn `VOID`, ghi lý do ở `void_reason` (ví dụ "F-123 không có dấu nhận đúng hạn do sự cố ngày …") — kiểm toán xanh lại. VOID không ghi được trước `resolve_at`. Vì vậy **khi thấy "Ledger intake" đỏ, bấm chạy lại ngay trong ngày**.
   - Mở Issue dự báo **ít nhất 30 phút trước nửa đêm** của ngày liền trước `resolve_at`; sát hơn thì robot từ chối (dấu nhận sẽ rơi sang ngày phân định).
5. Mỗi ghế chỉ một dự báo cho một câu hỏi. Ghi nhầm thì không xóa được: sổ chỉ ghi thêm. Câu hỏi viết sai thì tới `resolve_at` chọn `VOID` trong Issue **Resolution** (cả hai ghế của câu hỏi cùng bị hủy). VOID không làm đẹp được kết quả: phép kiểm định A–B dùng đúng 194 cặp bất đồng đầu tiên theo thứ tự ghi dự báo; một cặp bị VOID vẫn giữ chỗ của nó và bị tính theo hướng bất lợi cho kết luận đang xét; một cặp bị bỏ mặc không phân định thì phép kiểm định chưa ra kết luận.

## 7. Phân định khi tới hạn
1. Tới ngày `resolve_at` (giờ Việt Nam), **Owner hoặc một ghế AI khác nhà cung cấp với ghế viết** (ví dụ ChatGPT) mở nguồn đã ghi trong dự báo, tìm con số hoặc sự kiện.
2. **Issues** → **New issue** → mẫu **Resolution**: mã dự báo (`F-101`), YES/NO/VOID, đường dẫn nguồn, đoạn trích nguyên văn, `resolver` = người đã đọc nguồn ("Owner" hoặc "ChatGPT (OpenAI)"; không được là Claude).
   - Đường dẫn nguồn: dán **đường dẫn đầy đủ bắt đầu bằng `https://`** tới đúng trang đã đọc (`http://` bị từ chối). Mọi đường dẫn ghi trong ô này phải thuộc tên miền đã ghi trong dự báo (tên miền con như `data.nso.gov.vn` được nhận); không dán kèm đường dẫn của trang khác.
   - Robot bình luận ✅ kèm dấu nhận như ở mục 6; cũng không sửa, không xóa bình luận đó.
   - Việc "Resolution intake" đỏ mà kết quả đã vào sổ nhưng chưa có bình luận ✅: bấm **Re-run all jobs** (lúc nào cũng được; phân định không có hạn 6 giờ).
3. Một Issue phân định một câu hỏi; ghế A và ghế B của câu hỏi nhận cùng kết quả. Đã phân định thì không sửa được. Nguồn đã hứa không công bố → chọn VOID và ghi lý do.
   - **Chỉ mở Issue phân định khi mọi dự báo của câu hỏi đã có bình luận ✅.** Robot nhận dự báo và robot phân định chạy riêng. Nếu một dự báo của câu hỏi được mở sau (hoặc cùng lúc với) Issue phân định, robot phân định trả ❌ và không ghi gì: mở Issue Resolution mới. Nếu Issue phân định đã được ghi trước khi robot kịp ghi một dự báo mở trước đó, dự báo ấy bị ❌ (câu hỏi đã có kết quả). Cả hai trường hợp sổ đều không hỏng và không phải sửa gì.
4. Điểm số cập nhật ở vòng học kế tiếp: `reports/scorecard.json` mục `issue_forecasts`, và cuối tệp `reports/cycle_<ngày>.md`.

## 8. Chấm và gộp một PR (L-09, L-10)
1. PR phải có hai dòng trong mô tả: `authored_by: <ghế viết>` và `reviewed_by:` (để trống lúc mở).
2. Đưa PR cho một ghế **khác nhà cung cấp** với ghế viết để chấm, ghi rõ commit cần chấm (7 ký tự đầu SHA). Yêu cầu ghế chấm viết **dòng đầu tiên** của câu trả lời là đúng `GỘP ĐƯỢC — commit <7 ký tự>` hoặc `SỬA TRƯỚC — commit <7 ký tự>`, không thêm chữ nào khác trên dòng đó. Máy chỉ nhận dòng đầu đúng dạng này: "GỘP ĐƯỢC nếu sửa…" không được tính.
3. Kết luận GỘP ĐƯỢC: (a) dán nguyên bản chấm thành một **bình luận** của PR; (b) rồi sửa mô tả PR, điền `reviewed_by: <ghế chấm>`. Việc "L-09 nguoi cham" chuyển xanh.
4. Có commit mới sau khi chấm → việc đó đỏ lại → chấm lại bản mới.
5. Owner bấm **Merge pull request**. Không ghế AI nào bấm thay.

## 9. Bảo vệ nhánh main (làm một lần — L-10)
Settings → Rules → Rulesets → New branch ruleset → áp cho `main` → bật **Restrict deletions** và **Block force pushes** → Create. Hai luật này không cản vòng học và robot ghi dự báo. **Không** bật "Require a pull request before merging": bật là robot không ghi được vào sổ.

## 10. Khi CI đỏ
- "Test bat buoc (chan merge)" đỏ: không gộp; đọc dòng `LỖI:` trong log và giao ghế viết sửa.
- "L-09 nguoi cham" đỏ: thiếu người chấm hoặc thiếu bình luận bản chấm đúng commit — xem mục 8.
- Vòng học đỏ ở bước "Kiem lai sau khi chay": kết quả vòng đó trái luật nên không được ghi; chụp log gửi kiến trúc sư.
- Vòng học đỏ với dòng `LỖI L-06` (không đẩy được đăng ký thử lên `main`): backtest chưa chạy, không mất gì; bấm **Re-run all jobs**. Lần thử đã đăng ký mà không có kết quả vẫn nằm trong sổ và vẫn được đếm — đó là chủ ý.
- "Kiem toan so sau khi ghi" đỏ: đây là việc kiểm tự chạy sau mỗi lần robot ghi sổ, sau vòng học và mỗi sáng. Nó đã tự chờ và đọc lại dấu nhận khoảng 2,5 phút trước khi báo đỏ, nên đỏ là có việc phải làm: đọc dòng `LỖI:` trong log và xem các mục dưới đây.
- Bình luận ❌ ghi "Lỗi hệ thống: ghi … sẽ làm sổ không qua kiểm lại luật … nên KHÔNG ghi": robot tự phát hiện luật ghi và luật kiểm lệch nhau và đã dừng trước khi ghi. Sổ không bị đụng tới. Chụp bình luận gửi kiến trúc sư; sau khi sửa mã, mở Issue mới.
- Log có `L-06: Pull Request thêm … kết quả` hoặc `kết quả … đã bị sửa`: có người đưa kết quả thử vào kho không qua vòng học, hoặc sửa kết quả cũ. Không gộp PR đó.
- Log có `L-05: … không có bình luận dấu nhận` hoặc `… quá 6 giờ`: một dòng trong sổ không có dấu nhận hợp lệ của robot. Dòng phân định: chạy lại job "Resolution intake" của Issue đó. Dòng dự báo: làm theo mục 6 bước 4 (chạy lại job; quá 6 giờ thì chạy lại job, và tới `resolve_at` hủy câu hỏi bằng VOID). Không tự sửa sổ. Nếu dòng đó không do robot ghi (không ai mở Issue ấy cho dự báo ấy): chụp log gửi kiến trúc sư.
- Log có `L-05: dòng … trong sổ không qua luật nhận`, `không có issue_number` hoặc `không có resolution_issue`: một dòng trong sổ không đến từ Issue hoặc trái luật nhận (ghi không qua robot). Không gộp PR chứa dòng đó; chụp log gửi kiến trúc sư.
- Log có `L-06: tiêu đề research/trials.csv…` hoặc `…không ở dạng chuẩn`: tệp kết quả thử bị sửa tay hoặc ghi lại bằng công cụ khác. Không gộp PR đó.
- Log có `ledger.engine_forecasts`: ai đó đổi công tắc đường ghi dự báo của engine trong `config.yaml`. Giá trị duy nhất được nhận là `closed` (ADR-0003 quyết định 11).
- Log có `control_b_prompts.jsonl`: khối prompt trong `governance/CONTROL_B_PROMPT.md` bị đổi mà chưa thêm dòng phiên bản, hoặc tệp phiên bản bị sửa. Đổi prompt của ghế B phải qua ADR và **thêm một dòng** vào cuối `governance/control_b_prompts.jsonl` (không sửa, không xóa dòng cũ), với `valid_from` là một ngày SAU ngày gộp PR đó (ADR-0003 quyết định 12). Trong lúc hai tệp chưa khớp, robot không nhận dự báo ghế B.
