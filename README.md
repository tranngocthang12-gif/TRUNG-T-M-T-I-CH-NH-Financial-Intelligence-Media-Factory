# TRUNG TÂM TÀI CHÍNH — Bộ não

**Financial Intelligence & Media Factory — Architecture v3.0 (cập nhật theo các ADR hiện hành)**

Hai bộ não: **bộ não lập luận** (LLM, đọc `BOOT.md`) và **bộ não học máy** (`engine/`, chạy theo lịch thứ Sáu 16:30 giờ Việt Nam trên GitHub Actions). Kiến trúc có hiệu lực duy nhất: `architecture/ARCHITECTURE.md` (v3.0), bổ sung bằng `architecture/adr/`. Xem `docs/HUONG_DAN_VAN_HANH.md` để ghi dự báo A/B, phân định và chấm PR. Các kiến trúc v0.1–v2.2 là bản lưu trữ, không còn hiệu lực.

Repo này là **bộ não** của Trung Tâm Tài Chính: kiến trúc, luật quản trị, hợp đồng dữ liệu (contracts), trạng thái hệ thống và tri thức đã được kiểm chứng.
Mọi AI làm việc cho dự án phải đọc `BOOT.md` trước khi làm bất cứ việc gì.

> KHÔNG XÂY AI ĐOÁN THỊ TRƯỜNG.
> XÂY MỘT HỆ THỐNG biết thu thập bằng chứng, biết nghi ngờ chính nó, biết đo độ không chắc chắn,
> biết quản trị rủi ro, biết học từ kết quả, và biết cải thiện cách nó học.

## Cấu trúc

```text
trung-tam-tai-chinh/
├── BOOT.md                      # Lệnh khởi động: AI đọc gì, theo thứ tự nào
├── governance/                  # Tầng quyền lực: Owner, Governor, an toàn, firewall
│   ├── OWNER_MISSION.md
│   ├── GOVERNOR_POLICY.yaml
│   ├── SAFETY_STATE.yaml
│   ├── GATES.md
│   └── INVESTMENT_MEDIA_FIREWALL.md
├── architecture/                # Một kiến trúc hiện hành: ARCHITECTURE.md v3.0
│   ├── ARCHITECTURE.md
│   ├── adr/                     # Quyết định kiến trúc (ADR)
│   └── ARCHIVE.md               # Bản cũ (SUPERSEDED)
├── orchestrator/                # Vòng điều phối + AUTO MODE
├── experts/                     # Vai trò chuyên gia (đầu tư + newsroom)
├── contracts/                   # 25 JSON Schema — ranh giới dữ liệu duy nhất
├── state/                       # Trạng thái dự án, năng lực, mô hình
├── knowledge/                   # Tri thức canonical (chỉ ghi sau validation)
├── memory/                      # 6 loại bộ nhớ + nhật ký episodic
├── research/                    # Hypothesis, báo cáo, backtest
├── media/                       # Financial Media OS
├── templates/                   # Mẫu điền nhanh
├── engine/                      # BỘ NÃO HỌC MÁY — vòng học tự động
├── tests/                       # Chống look-ahead + diễn tập giả lập
├── .github/workflows/           # Vòng học thứ Sáu 16:30 VN; nhận dự báo/phân định qua Issue; CI
├── config.yaml                  # Universe, chi phí, ngưỡng thống kê
├── data/ paper/ reports/        # Engine tự ghi
├── docs/HUONG_DAN_VAN_HANH.md
├── tools/validate.py            # Kiểm tra repo & contract
├── STORAGE_POLICY.md
└── CHANGELOG.md
```

## Nguyên tắc cốt lõi

1. **Owner + GitHub Actions + hợp đồng dữ liệu chặt** trong giai đoạn đầu; chưa triển khai Orchestrator tự trị (kiến trúc v3.0 §2).
2. **Bằng chứng trước kết luận.** Mọi claim trỏ tới evidence, có bằng chứng ngược và ngày hết hạn.
3. **Không tự nhảy tầng vốn.** Research → Simulation → Backtest → Paper → Vốn nhỏ → Bình thường → Scale.
4. **Risk Gate có quyền chặn.** Lợi nhuận kỳ vọng cao không vượt được Risk Gate.
5. **Chỉ học sau Attribution.** Tách beta, ngành, factor, timing, may mắn khỏi kỹ năng.
6. **Canonical Knowledge không nhận phỏng đoán của AI.** Chỉ nhận thứ đã qua validation.
7. **Firewall Đầu tư ↔ Truyền thông.** Vị thế không bao giờ chảy thẳng vào câu chuyện truyền thông.
8. **Không lưu secret trong GitHub.**

## Kiểm tra repo

```bash
python tools/validate.py
```
