# ADR-0016: Đường từ dữ liệu tới vốn — quyết định Owner, tiêu chí số của thang vốn, điều kiện dừng

- Ngày: 2026-11-21
- Trạng thái: **PROPOSED — chưa hiệu lực.** Chỉ có hiệu lực khi ghế khác nhà cung cấp chấm (L-09) và Owner gộp (L-10). Owner có thể duyệt từng quyết định QĐ-1…QĐ-8 riêng.
- Người đề xuất: Claude Project TTC (Anthropic), ghế kiến trúc sư trưởng. Chép chữ vào kho: phiên Claude Code (Anthropic), theo LỆNH A1.
- Người chấm: chưa có. Phải là ChatGPT (OpenAI) hoặc Gemini (Google), chấm đúng commit.
- Owner duyệt: chưa.

## Nguồn chữ và phạm vi

- Ba mục "Quyết định", "Thang vốn: tiêu chí số" và "Điều kiện dừng và đảo" chép từ mục 3, 6 và 9 của tài liệu *[TTC] LỆNH CODE — HOÀN THIỆN KIẾN TRÚC TỪ DỮ LIỆU TỚI VỐN*. Tài liệu đó ghi ngày 21/11/2026, cơ sở `main` `20f5d924bbf52c34b68baeaff9df8d022a0af363`.
- Tài liệu nguồn chưa nằm trong kho. Các mã lệnh K0, A1, D1–D5, E1, E2a, E2b, E3, E4, R1, F1 và FWD-001 là tên việc trong gói lệnh của tài liệu đó. ADR này **không** phát lệnh nào: mỗi lệnh chỉ có hiệu lực khi Owner phát cho ghế.
- ADR này không sửa `architecture/ARCHITECTURE.md`, `governance/LAWS.md`, `governance/GATES.md`, `governance/SAFETY_STATE.yaml`, `config.yaml` hay mã.
- Không đổi `deployment_level: 0`. Không bật tiền thật. Không nêu mã nên mua hay bán (L-02). Không nêu số vốn thật (L-03).
- ADR-0015 (PR #68, PROPOSED) có bảng cổng BASELINE-001 và PAPER/RISK. FWD-001 hiện thực hai hàng đó nếu ADR-0015 được duyệt, nhưng ADR này không phụ thuộc vào việc ADR-0015 được duyệt.

## Quyết định (mục 3 của tài liệu nguồn)

| Mã | Quyết định đề xuất |
|---|---|
| QĐ-1 | Theo điều 7 của ADR-0009 (bản vá engine đi PR riêng, có test end-to-end, L-09, Owner gộp), cho phép các PR E1, E2a, E2b, E3, R1, F1, E4 chạm đúng các tệp engine nêu trong từng lệnh. Trừ E3 (đổi mặc định theo QĐ-6), mọi thay đổi nằm sau tham số và mặc định giữ hành vi cũ. `engine/adjust.py` và `data.sources` vẫn không đổi. |
| QĐ-2 | Trong cổng chứng cứ, "chia tách" và "trả cổ tức bằng cổ phiếu" thuộc một lớp STOCK khi so loại. Engine vốn tính hệ số như nhau cho hai loại (`adjust.STOCK`). Nguyên văn loại của bản gốc vẫn lưu. |
| QĐ-3 | Mặt nạ nhiễm theo cửa sổ quanh sự kiện thay cho mặt nạ theo ô. |
| QĐ-4 | Phép thử tiến dùng rổ VN30 đã ghim theo ngày và tải thêm giá BSR, LPB, MCH, TCX, VPL. Nghiên cứu cũ giữ rổ cấu hình và mang nhãn RETROSPECTIVE. |
| QĐ-5 | Tham số FWD-001: 12 kỳ cố định; 3 sổ đối chứng; tối đa 2 sổ bóng chọn bằng quy tắc cơ học (S1 là đặc tả của lần thử có `ic_t` cao nhất trong `research/trials.csv` tại ngày đăng ký; S2 là `signed_sum` trên đủ 13 đặc trưng); giới hạn rủi ro danh nghĩa như lệnh R1. |
| QĐ-6 | Mô hình chỉ lên ACTIVE khi Owner ghi mô hình đó vào `state/MODEL_REGISTRY.yaml` qua PR. |
| QĐ-7 | Tiêu chí số của thang vốn theo mục "Thang vốn: tiêu chí số" bên dưới. |
| QĐ-8 | Người chấm L-09 cho từng PR phải khác nhà cung cấp người viết: PR của Claude do ChatGPT hoặc Gemini chấm; PR của ChatGPT do Gemini hoặc Grok chấm. |

Cổng Owner đang treo từ trước, không đổi: ký `OWNER_MISSION`; `GOVERNOR_POLICY`; nguồn giá chính thức; bảo vệ `main` (P5).

## Thang vốn: tiêu chí số (mục 6 của tài liệu nguồn; đề xuất cho QĐ-7; tên bậc theo `GATES.md`)

| Bước | Điều kiện trong `GATES.md` | Tiêu chí số đề xuất | Hiện trạng |
|---|---|---|---|
| 0 → 1 Mô phỏng | Mô phỏng có baseline | FWD-001 đã đăng ký; 3 sổ đối chứng chạy đủ 1 kỳ; `tools/fwd_audit.py` đạt | Chưa |
| 1 → 2 Backtest | Phí, trượt giá, holdout, walk-forward, chế độ thị trường | Có khoảng lịch sử đủ điều kiện PIT; E4 đã gộp; ít nhất một đặc tả đạt cùng lúc: `ic_t` ≥ ngưỡng L-06 (hiện 3,69), lãi ròng > 0, `fold_pos` ≥ 0,6, `recent_ic` > 0, từ 2 chế độ dương, DSR ≥ 0,95, và đạt trên holdout khóa | 0/222 |
| 2 → 3 Giấy có mô hình | Backtest qua robustness; Owner duyệt | Owner ghi mô hình vào `state/MODEL_REGISTRY.yaml` qua PR | 0 mô hình |
| 3 → 4 Vốn nhỏ | Giấy đạt tiêu chí; Risk Gate; Owner; `live_trading_enabled` | Mô hình ACTIVE đủ 12 kỳ tái cơ cấu; hiệu ròng so với `FWD-EW` dương; IC thực hiện không ở DEGRADING hoặc PAUSED; phí và tỷ lệ không khớp không quá 1,5 lần giả định; sụt giảm trong ngưỡng; 0 vi phạm cổng và 0 sự cố PIT; `OWNER_MISSION` đã ký; giới hạn vốn thật đặt ngoài kho; `main` được bảo vệ; có ADR riêng và ý kiến pháp lý | Chưa |
| 4 → 5, 5 → 6 | Theo `GATES.md` | Ngoài phạm vi lệnh này | — |

- 12 kỳ trùng ngưỡng mẫu tối thiểu đã có trong `engine/attribution.py` (dưới 12 lần tái cơ cấu thì không kết luận về kỹ năng).
- 12 kỳ không chứng minh được lợi thế nhỏ hơn 2,37% mỗi kỳ. Qua bước 3 → 4 nghĩa là hệ thống vận hành đúng và không có dấu hiệu xấu, không phải lợi thế đã được xác nhận.
- Ở bậc 4, Owner tự đặt lệnh trong tài khoản của mình. Hệ thống không gửi lệnh (`autonomous_order_execution: false` giữ nguyên). Vị thế thật không vào kho (L-03).

## Điều kiện dừng và đảo (mục 9 của tài liệu nguồn)

- D0 trượt quá 8 tuần so với 08/01/2027 thì báo Owner. Không nới điều kiện để kịp mốc.
- Sau 12 kỳ, nếu không sổ bóng nào đạt và đợt 2 không có đặc tả qua bậc 2, ghi NO_EDGE cho không gian 13 × 3 trên VN30. Khi đó Owner quyết mở giả thuyết mới bằng ADR, hoặc giữ TTC ở vai nghiên cứu và sổ dự báo.
- Mọi tham số mới của E2a, E2b, F1 gỡ được bằng một PR. Chuỗi `legacy` không bị xóa.
- Lệnh này không đổi mẫu 194 cặp, mốc 31/03/2027 và cột dừng 3 tuần của §8.

## Lý do

Bằng chứng và phép tính đầy đủ nằm ở mục 1–2 của tài liệu nguồn; ADR này không chép lại. Trạng thái trên `main` tại cơ sở nêu trên, kiểm được trong kho:

- `reports/PIT-001_20261121.json`: kết luận NOT_READY, 18 hạng mục.
- `research/trials.csv`: 222/222 lần thử REJECTED.
- `state/MODEL_REGISTRY.yaml`: `models: []`.
- `state/PROJECT_STATE.yaml`: `deployment_level: 0`.
- `engine/knowledge.rank_active` tự đặt ACTIVE theo `ic_t` backtest. QĐ-6 đổi điểm này.

## Điều kiện hoàn tác (đo được, có hạn)

1. **D0 trượt.** Nếu tới 05/03/2027 (8 tuần sau 08/01/2027) chưa có D0, báo Owner (như mục "Điều kiện dừng và đảo"). Owner chọn giữ, đổi QĐ-5 hoặc hoàn tác ADR này bằng một ADR mới. Không nới tiêu chí số để kịp mốc.
2. **Sau 12 kỳ FWD-001.** Nếu không sổ bóng nào đạt và không đặc tả nào qua bậc 2, ghi NO_EDGE. Tiêu chí số của thang vốn (QĐ-7) giữ nguyên; Owner quyết mở giả thuyết mới bằng ADR riêng hay dừng ở vai nghiên cứu.
3. **Hoàn tác kỹ thuật.**
   - Mỗi tham số mới do QĐ-1 cho phép (E2a, E2b, F1) gỡ được bằng một PR.
   - Chuỗi `legacy` và sổ giấy hiện có không bị xóa.
   - Hoàn tác QĐ-6 bằng ADR mới.
   - Hoàn tác không xóa sổ thử, kết quả âm hay dữ liệu đã ghi.
4. **Xung đột.** Nếu một quyết định ở đây xung đột với ADR đã ACCEPTED hoặc với L-01…L-10, phần triển khai liên quan dừng. ADR này không ghi đè ADR cũ.

## Ảnh hưởng tới ARCHITECTURE.md

Không sửa trong PR này (LỆNH A1 cấm). Nếu ADR được ACCEPTED, một PR riêng thêm một dòng trỏ tới ADR này ở §4.3 và §8. Không viết bản kiến trúc mới (L-07).
