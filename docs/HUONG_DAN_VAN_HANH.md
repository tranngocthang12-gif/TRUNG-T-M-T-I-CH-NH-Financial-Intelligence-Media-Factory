# Hướng dẫn vận hành

## 1. Bật quyền ghi cho GitHub Actions (bắt buộc)
Settings → Actions → General → *Workflow permissions* → chọn **Read and write permissions** → Save.

## 2. (Tùy chọn) Bật LLM phản biện
Settings → Secrets and variables → Actions → New repository secret
- Name: `ANTHROPIC_API_KEY`
- Value: API key từ console.anthropic.com
Không có key thì bước phản biện tự bỏ qua; engine vẫn chạy.

## 3. Chạy lần đầu
Tab **Actions** → *Vòng học hằng ngày* → **Run workflow** → trials = `16`.
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
