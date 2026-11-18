# Kho lưu kiến trúc đã thay thế (ARCHIVE)

Bản có hiệu lực duy nhất: `architecture/ARCHITECTURE.md` (v3.0, 22/10/2026). Mọi tệp dưới đây là lịch sử: giữ để tra cứu, **không còn hiệu lực**, không xóa (luật INVALIDATED không xóa). `tools/validate.py` từ chối tệp `ARCHITECTURE_v*.md` không có trong bảng này (L-07).

| Tệp | Phiên bản | Ngày | Trạng thái | Phần còn sống trong v3.0 |
|---|---|---|---|---|
| ARCHITECTURE_v0.1.md | v0.1 | 26/09/2026 | SUPERSEDED | 32 mục được bao bởi §2–§6 |
| ARCHITECTURE_v0.2.md | v0.2 | 26/09/2026 | SUPERSEDED | Engine định lượng = đối chứng âm (§4.3) |
| ARCHITECTURE_v1.0.md | v1.0 | 26/09/2026 | SUPERSEDED | Ledger, Scorecard, nhóm B, walking skeleton (§4) |
| ARCHITECTURE_v2.0.md | v2.0 | 26/09/2026 | SUPERSEDED | Thư viện 4 tầng, Học viện, KNOWLEDGE_NOTE (§5) |
| ARCHITECTURE_v2.1.md | v2.1 | 26/09/2026 | SUPERSEDED | Địa chính trị/chính sách ở mức bản đồ phơi nhiễm (§5); làn nhanh, influence, blind-spot hoãn tới G4 |
| ARCHITECTURE_v2.2.md | v2.2 | 26/09/2026 | SUPERSEDED | Tinh hoa, thước đo A–B (§1, §4.2) |

`tools/validate.py` chỉ từ chối tệp `ARCHITECTURE_v*.md` thiếu dòng ở bảng trên (L-07). Các đường dẫn dưới đây không phải bản kiến trúc thứ hai, nhưng cũng không có hiệu lực vận hành. Giữ để tra, không xóa. `BOOT.md` không bảo AI đọc chúng như lệnh hiện hành (ADR-0010).

| Đường dẫn | Vì sao còn | Trạng thái |
|---|---|---|
| `orchestrator/ORCHESTRATOR.md`, `orchestrator/AUTO_MODE.md` | `validate.py` vẫn đòi tệp ORCHESTRATOR tồn tại, để không mất lịch sử | Không vận hành. ARCHITECTURE §2: không có Orchestrator trong 6 tháng đầu |
| `media/MEDIA_OS.md` | Đồ v1.0 | Hoãn. §6: chỉ xét sau luật sư và ≥ 194 bất đồng đã chấm |
| `architecture/engines/` (5 tệp) | Ghi chú engine cũ; ADR-0008 trỏ `data_evidence.md` như chỗ thiên lệch từng được ghi | Không sửa được v3.0. Engine đang chạy là `engine/` |
| `experts/investment/` (10 vai), `experts/media/` | Vai nhập từ bản cũ | Không phải ghế. Ghế hiện hành nằm ở ARCHITECTURE §3 |
