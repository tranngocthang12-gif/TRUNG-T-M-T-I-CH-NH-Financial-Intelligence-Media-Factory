# ADR-0016: Đường từ dữ liệu tới vốn — quyết định Owner, tiêu chí số của thang vốn, điều kiện dừng

- Ngày: 2026-11-21
- Trạng thái: **ACCEPTED 21/11/2026, hiệu lực khi Owner gộp PR này** (PR #75, cập nhật trạng thái theo lệnh Owner ngày 21/11/2026). Văn bản đã gộp vào `main` (PR #73). Chỉ quyết định được ghi ACCEPTED trong bảng "Trạng thái từng quyết định" mới có hiệu lực.
- Người đề xuất: Claude Project TTC (Anthropic), ghế kiến trúc sư trưởng. Chép chữ vào kho: phiên Claude Code (Anthropic).
- Người chấm: ChatGPT (OpenAI), `GỘP ĐƯỢC` trên commit `cee8e98d7ff92c724260c79e7c6526f115219702` ([bình luận L-09, PR #73](https://github.com/tranngocthang12-gif/TRUNG-T-M-T-I-CH-NH-Financial-Intelligence-Media-Factory/pull/73#issuecomment-7061811768)).
- Owner duyệt: văn bản gộp ngày 21/11/2026 (giờ Việt Nam), PR #73, merge `b75250184b553560a0ea31c909766a1f11f1a6f3`. Hiệu lực từng quyết định theo bảng "Trạng thái từng quyết định".

## Nguồn chữ và phạm vi

- **ADR này chính là văn bản quyết định.** Owner duyệt chữ trong ADR này, không duyệt tài liệu nào nằm ngoài kho. Không câu nào ở đây lấy tài liệu ngoài kho làm căn cứ.
- Mọi số đo và trạng thái nêu trong ADR là tại `main` `20f5d924bbf52c34b68baeaff9df8d022a0af363`, dữ liệu tới phiên 20/11/2026.
- Các mã việc D1–D5, E1, E2a, E2b, E3, E4, R1, F1 và FWD-001 chỉ là tên gọi. ADR này **không** phát lệnh nào: mỗi việc chỉ có hiệu lực khi Owner phát cho một ghế. Phạm vi tệp của mỗi việc do lệnh đó ghi và do PR thực hiện liệt kê; L-09 và Owner gộp kiểm phạm vi đó.
- ADR này không sửa `architecture/ARCHITECTURE.md`, `governance/LAWS.md`, `governance/GATES.md`, `governance/SAFETY_STATE.yaml`, `config.yaml` hay mã.
- Không đổi `deployment_level: 0`. Không bật tiền thật. Không nêu mã nên mua hay bán (L-02). Không nêu số vốn thật (L-03).
- ADR-0015 (PR #68, PROPOSED) có bảng cổng BASELINE-001 và PAPER/RISK. FWD-001 hiện thực hai hàng đó nếu ADR-0015 được duyệt, nhưng ADR này không phụ thuộc vào việc ADR-0015 được duyệt.

## Quyết định

| Mã | Quyết định đề xuất |
|---|---|
| QĐ-1 | Theo điều 7 của ADR-0009 (bản vá engine đi PR riêng, có test end-to-end, L-09, Owner gộp), cho phép các PR E1, E2a, E2b, E3, R1, F1, E4 chạm đúng các tệp engine nêu trong từng lệnh. Trừ E3 (đổi mặc định theo QĐ-6), mọi thay đổi nằm sau tham số và mặc định giữ hành vi cũ. `engine/adjust.py` và `data.sources` vẫn không đổi. |
| QĐ-2 | Trong cổng chứng cứ, "chia tách" và "trả cổ tức bằng cổ phiếu" thuộc một lớp STOCK khi so loại. Engine vốn tính hệ số như nhau cho hai loại (`adjust.STOCK`). Nguyên văn loại của bản gốc vẫn lưu. Lệnh E1 phải có test từ chối cổ tức tiền mặt, phát hành quyền mua, và mọi nguyên văn ngoài bảng ánh xạ (ra `CACH_LY_LOAI_CHUA_ANH_XA`). Tỷ lệ vẫn phải khớp. Nguyên văn loại sự kiện trong manifest không bị sửa. Đổi bảng ánh xạ phải qua PR và L-09. |
| QĐ-2a | Lớp STOCK gồm thêm: phát hành cổ phiếu để tăng vốn từ nguồn vốn chủ sở hữu (cổ phiếu thưởng); câu gộp cổ tức bằng cổ phiếu với phát hành tăng vốn từ nguồn vốn chủ sở hữu. Lớp STOCK không gồm: phát hành quyền mua, ESOP, chào bán riêng lẻ. Bảng ánh xạ chỉ thêm đúng các nguyên văn của hai loại này đang có trong hai manifest. Mỗi câu mới có một test đạt; giữ các test từ chối quyền mua và cổ tức tiền. |
| QĐ-3 | Mặt nạ nhiễm theo cửa sổ quanh sự kiện thay cho mặt nạ theo ô. |
| QĐ-4 | Phép thử tiến dùng rổ VN30 đã ghim theo ngày và tải thêm giá BSR, LPB, MCH, TCX, VPL. Nghiên cứu cũ giữ rổ cấu hình và mang nhãn RETROSPECTIVE. |
| QĐ-5 | Tham số FWD-001: 12 kỳ cố định; 3 sổ đối chứng; tối đa 2 sổ bóng chọn bằng quy tắc cơ học (S1 là đặc tả của lần thử có `ic_t` cao nhất trong `research/trials.csv` tại ngày đăng ký; S2 là `signed_sum` trên đủ 13 đặc trưng); giới hạn rủi ro danh nghĩa như lệnh R1. |
| QĐ-6 | Mô hình chỉ lên ACTIVE khi Owner ghi mô hình đó vào `state/MODEL_REGISTRY.yaml` qua PR. |
| QĐ-7 | Tiêu chí số của thang vốn theo mục "Thang vốn: tiêu chí số" bên dưới. |
| QĐ-8 | Người chấm L-09 cho từng PR phải khác nhà cung cấp người viết: PR của Claude do ChatGPT hoặc Gemini chấm; PR của ChatGPT do Gemini hoặc Grok chấm. |
| QĐ-9 | Ngày HOSE đăng tin được ghi vào `published_at` kể cả khi trùng ngày ký văn bản, khi máy kiểm được ngày đó từ metadata HOSE đã ghim trong kho (`tools/publication_proof.py`): tệp tin JSON và tệp danh sách đính kèm khớp sha256, id tin khớp `source_id`, `published_at` bằng đúng `data.postedDate` đổi theo UTC, đính kèm trỏ đúng PDF, ngày đăng không sớm hơn ngày ký, và ngày của (ngày đăng + 7 giờ) sớm hơn ngày không hưởng quyền. Ngày gõ tay, hoặc suy từ ngày ký, tên tệp hay ngày hưởng quyền, vẫn bị từ chối. |
| QĐ-5a | Trong FWD-001, cổng R1a áp cho mọi sổ. Ngưỡng sụt giảm NAV 15% ở các sổ FWD chỉ để ghi nhận (`DRAWDOWN_BREACH`); không khóa và không bán. Ngắt thật (khóa, bán hết, chỉ Owner gỡ) do R1b hiện thực, áp cho sổ giấy chính (sổ của mô hình Owner duyệt ACTIVE) và mọi sổ gắn vốn thật. R1b phải gộp trước khi đăng ký FWD-001. Quyết định này thay phần "ngưỡng sụt giảm" của QĐ-5 đối với các sổ FWD. |
| QĐ-10 | Robot vòng học chạy mỗi phiên HOSE (thứ Hai đến thứ Sáu, bỏ ngày nghỉ theo `data/trading_calendar.csv`) cho các bước: tải giá, định giá sổ giấy, cổng rủi ro, ghi quyết định của sổ. Bước nghiên cứu (đăng ký và chạy lần thử L-06, thăng hạng và theo dõi suy giảm mô hình) vẫn chỉ chạy thứ Sáu, 6 lần thử mỗi tuần; chạy tay tối đa 1 lần thử. Không gian 13 × 3 và ngưỡng theo số lần thử không đổi. Đây vẫn là robot và các đường ghi mà ADR-0013 đã ghi nhận; không thêm đường ghi `main` mới. |
| QĐ-11 | Phép thử FWD-001 chạy theo mục "Giao thức FWD-001" của ADR này. Dòng đăng ký L-06 của FWD-001 phải chép đúng các tham số đó. |
| QĐ-11a | Làm rõ giao thức FWD-001 trước khi đăng ký, theo mục "Làm rõ giao thức FWD-001 (QĐ-11a)" của ADR này. Không đổi tham số nào của QĐ-11. Dòng đăng ký L-06 của FWD-001 ghi sha256 của cả hai mục "Giao thức FWD-001 (QĐ-11)" và "Làm rõ giao thức FWD-001 (QĐ-11a)". |

Cổng Owner đang treo từ trước, không đổi: ký `OWNER_MISSION`; `GOVERNOR_POLICY`; nguồn giá chính thức; bảo vệ `main` (P5).

## Trạng thái từng quyết định

| QĐ | Trạng thái | Owner | Ngày |
|---|---|---|---|
| QĐ-1 | ACCEPTED | Owner | 21/11/2026 |
| QĐ-2 | ACCEPTED | Owner | 21/11/2026 |
| QĐ-2a | ACCEPTED | Owner | 21/11/2026 |
| QĐ-3 | ACCEPTED | Owner | 21/11/2026 |
| QĐ-4 | ACCEPTED | Owner | 21/11/2026 |
| QĐ-5 | ACCEPTED | Owner | 21/11/2026 |
| QĐ-6 | ACCEPTED | Owner | 21/11/2026 |
| QĐ-7 | ACCEPTED | Owner | 21/11/2026 |
| QĐ-8 | ACCEPTED | Owner | 21/11/2026 |
| QĐ-9 | ACCEPTED | Owner | 22/11/2026 |
| QĐ-5a | ACCEPTED | Owner | 22/11/2026 |
| QĐ-10 | ACCEPTED | Owner | 22/11/2026 |
| QĐ-11 | ACCEPTED | Owner | 22/11/2026 |
| QĐ-11a | ACCEPTED | Owner | 22/11/2026 |

Quy tắc:

- Gộp ADR này không tự duyệt quyết định nào.
- Chỉ quyết định được Owner ghi `ACCEPTED` kèm ngày trong bảng này mới có hiệu lực.
- `DEFERRED`, `REJECTED` hoặc ô trống là chưa có hiệu lực.
- Mỗi PR engine theo QĐ-1 và mỗi bước thang vốn theo QĐ-7 vẫn phải qua L-09 và Owner gộp riêng.

## Thang vốn: tiêu chí số (đề xuất cho QĐ-7; tên bậc theo `GATES.md`)

| Bước | Điều kiện trong `GATES.md` | Tiêu chí số đề xuất | Hiện trạng |
|---|---|---|---|
| 0 → 1 Mô phỏng | Mô phỏng có baseline | FWD-001 đã đăng ký; 3 sổ đối chứng chạy đủ 1 kỳ; `tools/fwd_audit.py` đạt | Chưa |
| 1 → 2 Backtest | Phí, trượt giá, holdout, walk-forward, chế độ thị trường | Có khoảng lịch sử đủ điều kiện PIT; E4 đã gộp; ít nhất một đặc tả đạt cùng lúc: `ic_t` ≥ ngưỡng L-06 (hiện 3,69), lãi ròng > 0, `fold_pos` ≥ 0,6, `recent_ic` > 0, từ 2 chế độ dương, DSR ≥ 0,95, và đạt trên holdout khóa | 0/222 |
| 2 → 3 Giấy có mô hình | Backtest qua robustness; Owner duyệt | Owner ghi mô hình vào `state/MODEL_REGISTRY.yaml` qua PR | 0 mô hình |
| 3 → 4 Vốn nhỏ | Giấy đạt tiêu chí; Risk Gate; Owner; `live_trading_enabled` | Mô hình ACTIVE đủ 12 kỳ tái cơ cấu; hiệu ròng so với `FWD-EW` dương; IC thực hiện không ở DEGRADING hoặc PAUSED; phí và tỷ lệ không khớp không quá 1,5 lần giả định; sụt giảm trong ngưỡng; 0 vi phạm cổng và 0 sự cố PIT; `OWNER_MISSION` đã ký; giới hạn vốn thật đặt ngoài kho; `main` được bảo vệ; có ADR riêng và ý kiến pháp lý | Chưa |
| 4 → 5, 5 → 6 | Theo `GATES.md` | Ngoài phạm vi ADR này | — |

- 12 kỳ trùng ngưỡng mẫu tối thiểu đã có trong `engine/attribution.py` (dưới 12 lần tái cơ cấu thì không kết luận về kỹ năng).
- Minh họa độ mạnh thống kê của 12 kỳ, **hoàn toàn giả định, không phải số đo của TTC**:
  - Giả định độ lệch chuẩn mỗi kỳ của lợi suất danh mục trừ bình quân rổ là σ = 3%.
  - Công thức: Δ = (z0,975 + z0,80) × σ / √n = 2,80 × 3% / √12 ≈ 2,42%, với n = 12 kỳ.
  - Đọc là: với σ giả định đó, 12 kỳ chỉ phát hiện được mức vượt trội từ khoảng 2,42% mỗi kỳ trở lên; lợi thế nhỏ hơn thì 12 kỳ không chứng minh được.
  - Giả định thống kê: các kỳ độc lập; kiểm định hai phía 5%; độ mạnh 80%; không hiệu chỉnh nhiều phép thử.
  - Con số này chỉ minh họa. Nó không phải tiêu chí, không phải bằng chứng, và không được dùng để mở cổng vốn.
- Qua bước 3 → 4 nghĩa là hệ thống vận hành đúng và không có dấu hiệu xấu, không phải lợi thế đã được xác nhận.
- Ở bậc 4, Owner tự đặt lệnh trong tài khoản của mình. Hệ thống không gửi lệnh (`autonomous_order_execution: false` giữ nguyên). Vị thế thật không vào kho (L-03).

## Giao thức FWD-001 (QĐ-11)

1. **Năm sổ, mỗi sổ 10 tỷ đồng danh nghĩa.** Đây là tham số thí nghiệm, không phải vốn thật (L-03). Mức 10 tỷ để phần dư do làm tròn lô 100 cổ phiếu không quá khoảng 7% mỗi vị thế ở sổ chia đều.
   - `FWD-EW`: chia đều cho mọi thành viên đủ điều kiện tại phiên quyết định; tái cơ cấu mỗi kỳ.
   - `FWD-HOLD`: mua chia đều tại D0 rồi giữ. Chỉ bán mã rời rổ; tiền bán giữ ở tiền mặt. Không mua mã mới vào rổ.
   - `FWD-CASH`: giữ tiền mặt.
   - `FWD-S1`, `FWD-S2`: sổ bóng theo QĐ-5. Mỗi kỳ chọn 5 mã điểm cao nhất trong các thành viên đủ điều kiện.
   - "Đủ điều kiện" tại một phiên: là thành viên rổ VN30 đã ghim tại phiên đó, có giá, và không nằm trong cửa sổ cách ly của QĐ-3.
2. **Chia vốn.** Mỗi mã mục tiêu nhận min(NAV / số mã mục tiêu, 20% NAV) × 0,995. Phần còn lại giữ tiền mặt. Sổ bóng có ít hơn 5 mã đủ điều kiện vẫn mua, không vượt giới hạn tỷ trọng.
3. **Dữ liệu và khớp lệnh.**
   - Định giá, chọn mã và khớp lệnh dùng chuỗi đã kiểm, rổ theo ngày và lịch phiên (`research_input="verified"`, `universe="historical"`, `sessions="calendar"`).
   - Quyết định ở đóng cửa phiên t, khớp ở đóng cửa phiên t+1.
   - Phí, thuế, trượt giá, lô, khóa trần và khóa sàn như sổ giấy hiện có. Cổ tức tiền mặt ghi vào tiền mặt như sổ giấy hiện có.
   - Sổ bóng huấn luyện trên chuỗi đã kiểm có mặt nạ cửa sổ, rổ theo cấu hình, chỉ dùng dữ liệu tới phiên t. Phần huấn luyện này mang nhãn RETROSPECTIVE.
4. **Kỳ.** D0 là phiên quyết định đầu tiên. Mỗi kỳ 20 phiên HOSE theo lịch đã ghim. Lợi suất kỳ k của một sổ là NAV tại đóng cửa phiên khớp của kỳ k+1 chia NAV tại đóng cửa phiên khớp của kỳ k, trừ 1. Phép thử gồm đúng 12 kỳ.
5. **Niêm phong.**
   - Quyết định của phiên tái cơ cấu t phải nằm trong một commit trên `main` do lượt chạy GitHub Actions của robot ghi, và lượt chạy đó phải kết thúc trước 09:00 giờ Việt Nam của phiên kế, theo giờ của API GitHub. `tools/fwd_audit.py` đối chiếu.
   - Trễ: ở phiên đó không sổ nào đổi danh mục, ghi `LATE_VOID`. Kỳ đó vẫn được tính với danh mục đang giữ; không tái cơ cấu bù.
   - D0 trễ thì D0 dời sang phiên kế.
   - Có hơn 2 kỳ `LATE_VOID` trong 12 kỳ thì phán quyết là INCONCLUSIVE.
6. **Thước đo chính.** d_k = lợi suất ròng kỳ k của sổ bóng trừ lợi suất ròng kỳ k của `FWD-EW`, với k = 1…12.
7. **Phán quyết.** Ra một lần, sau kỳ 12.
   - Với mỗi sổ bóng: kiểm định t một mẫu, hai phía, cho trung bình của d (11 bậc tự do). Hiệu chỉnh Holm trên 2 giá trị p ở mức 5%.
   - PASS: giả thuyết trung bình bằng 0 bị bác bỏ và trung bình của d lớn hơn 0.
   - Mọi trường hợp khác: KHÔNG ĐẠT.
   - Không sổ bóng nào PASS thì FWD-001 ghi NO_EDGE, như mục "Điều kiện dừng và đảo".
   - Báo cáo kèm, không dùng để phán quyết: kiểm định dấu; so với `FWD-HOLD` và `FWD-CASH`; số lần `DRAWDOWN_BREACH`.
   - 12 kỳ là mẫu nhỏ. Nếu độ lệch chuẩn của d là 3% mỗi kỳ (giả định, chưa đo), mức vượt trội trung bình phải khoảng 2,2% mỗi kỳ thì khả năng PASS mới đạt 50%, và khoảng 3% mỗi kỳ thì mới đạt 80%. PASS không phải điều kiện đủ để lên bậc vốn.
8. **Không đổi luật giữa chừng.** Sổ nằm công khai trên `main` nên kết quả từng kỳ ai cũng xem được. Không tham số nào của mục này được đổi sau khi đăng ký. Muốn đổi thì đăng ký phép thử mới với D0 mới.
9. **Đăng ký.** Dòng `kind: "forward_test"` trong `research/trial_registry.jsonl` ghi mã `FWD-001`, D0, năm sổ, đặc tả của S1 và S2, và sha256 của mục này tại commit Owner gộp.

## Làm rõ giao thức FWD-001 (QĐ-11a)

1. **Phiên.** Phiên của FWD-001 là ngày mà `data/trading_calendar.csv` ghi `is_session=1` với nguồn là một thông báo HOSE hoặc `HOSE_DEFAULT`. Ngày ghi `CHUA_CO_THONG_BAO` và ngày nằm ngoài vùng lịch phủ chỉ là phiên khi kho giá có giá của ít nhất một thành viên rổ ở ngày đó. Có giá nghĩa là có dòng giá với khối lượng lớn hơn 0; dòng khối lượng 0 coi như không có giá.
2. **Xử lý tuần tự.** Robot xử lý lần lượt từng phiên kể từ phiên đã xử lý gần nhất, theo thứ tự: áp sự kiện quyền cho vị thế đang giữ từ trước phiên, khớp lệnh chờ ở đóng cửa phiên, định giá, đo sụt giảm, rồi (chỉ ở phiên tái cơ cấu) ra quyết định. Cổ phiếu mua ở đóng cửa phiên s không hưởng sự kiện có ngày giao dịch không hưởng quyền là s.
3. **Niêm phong lúc khớp.** Lệnh của quyết định phiên t chỉ khớp ở đóng cửa phiên t+1, sau khi robot xác minh qua API GitHub rằng lượt chạy ghi quyết định đó đã kết thúc trước 09:00 giờ Việt Nam của phiên t+1. Không xác minh được thì robot dừng trước phiên t+1 và thử lại ở lần chạy sau; không khớp ở phiên khác. Xác minh được là trễ thì ghi `LATE_VOID` theo mục 5 của giao thức.
4. **Không quyết định muộn.** Quyết định cho phiên tái cơ cấu t chỉ được ra trong lượt chạy mà t là phiên mới nhất có giá trong kho. Lượt đó không ghi được quyết định lên `main` (lỗi, không chạy, quá hạn) thì phiên t là `LATE_VOID`.
5. **Thiếu giá.** Mã không có giá gốc ở một phiên được coi là không giao dịch ở phiên đó: định giá theo giá gốc gần nhất và ghi `STALE_PRICE`; lệnh của mã đó không khớp và thử lại ở phiên sau, như khóa biên độ. Phiên có trong lịch mà kho chưa có giá của thành viên nào thì robot dừng trước phiên đó và thử lại ở lần chạy sau. Có giá nghĩa là có dòng giá với khối lượng lớn hơn 0; dòng khối lượng 0 coi như không có giá.
6. **Sự kiện quyền với vị thế đang giữ.** Định giá ở phiên s dùng giá đóng cửa gốc của phiên s. Số cổ phiếu và tiền mặt là sau khi áp các sự kiện có ngày giao dịch không hưởng quyền ≤ s, như sổ giấy hiện có:
   - cổ tức tiền mặt: cộng tiền theo bảng sự kiện của engine (trạng thái APPLIED), sau thuế cổ tức;
   - sự kiện cổ phiếu: nhân số cổ phiếu theo hệ số trong bảng sự kiện; sự kiện chưa vào chuỗi kiểm chứng tại phiên xử lý thì ghi thêm `CA_UNVERIFIED`;
   - sự kiện robot biết muộn (ngày không hưởng quyền đã qua) được áp ở phiên đang xử lý và ghi `CA_LATE`.
   Mỗi lần áp ghi một dòng vào sổ giao dịch của sổ FWD.
7. **Phán quyết chờ bằng chứng.** Phán quyết chỉ ra khi mọi sự kiện cổ phiếu đã áp vào vị thế của năm sổ trong 12 kỳ đều đã vào chuỗi kiểm chứng. Hệ số đã kiểm khác hệ số đã áp thì kiểm toán dựng lại các sổ từ D0 theo hệ số đã kiểm, với cùng danh mục mục tiêu đã niêm phong. Sau 60 phiên kể từ mốc NAV thứ 13 mà còn sự kiện chưa kiểm thì phán quyết là INCONCLUSIVE.
8. **Dữ liệu tại lúc quyết định.** Quyết định dùng dữ liệu có trên `main` lúc lượt chạy đó chạy. Mỗi dòng quyết định ghi: mã lượt chạy GitHub Actions; sha256 của `data/vn30_history.csv` và `data/trading_calendar.csv`; `derivation_id`; danh mục mục tiêu của từng sổ. Cập nhật rổ hay lịch được ghi sau phiên quyết định thì không áp ngược.
9. **Dời D0.** D0 thực tế là phiên đầu tiên, kể từ D0 đã đăng ký, có quyết định được niêm phong đúng hạn. Mọi mốc kỳ tính từ D0 thực tế.
10. **Kiểm toán độc lập với sổ.** `tools/fwd_audit.py` dựng lại năm sổ từ D0 theo danh mục mục tiêu đã niêm phong, các dòng áp sự kiện quyền đã ghi, giá trong kho và luật của giao thức; lệch với NAV robot đã ghi thì báo lỗi. Trước kỳ 12, kiểm toán chỉ báo tính toàn vẹn và lợi suất từng kỳ; không tính thống kê t hay giá trị p.

## Điều kiện dừng và đảo

- D0 trượt quá 8 tuần so với 08/01/2027 thì báo Owner. Không nới điều kiện để kịp mốc.
- Sau 12 kỳ, nếu không sổ bóng nào đạt và đợt 2 không có đặc tả qua bậc 2, ghi NO_EDGE cho không gian 13 × 3 trên VN30. Khi đó Owner quyết mở giả thuyết mới bằng ADR, hoặc giữ TTC ở vai nghiên cứu và sổ dự báo.
- Mọi tham số mới của E2a, E2b, F1 gỡ được bằng một PR. Chuỗi `legacy` không bị xóa.
- ADR này không đổi mẫu 194 cặp, mốc 31/03/2027 và cột dừng 3 tuần của §8.

## Lý do

Trạng thái trên `main` `20f5d92`, kiểm được trong kho:

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

Không sửa trong PR này. Nếu ADR được ACCEPTED, một PR riêng thêm một dòng trỏ tới ADR này ở §4.3 và §8. Không viết bản kiến trúc mới (L-07).
