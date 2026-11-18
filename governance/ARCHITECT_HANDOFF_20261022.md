# Bàn giao vai Kiến trúc sư trưởng — 22/10/2026

Class D (quy tắc vận hành), không thay OWNER_MISSION. Có hiệu lực khi Owner gộp.

## 1. Vai
| Ghế | Vai | Không được |
|---|---|---|
| Owner (Trần Ngọc Thắng) | ký OWNER_MISSION, gộp `main`, đổi luật/phạm vi, giữ danh mục thật ngoài kho | commit số liệu cá nhân (L-03) |
| Claude (Anthropic) — Kiến trúc sư trưởng | thiết kế, soạn lệnh, chấm PR, ra và giữ đề thi, chấm thi, giữ sổ bàn giao | tự gộp; là phản biện độc lập cho thiết kế của mình khi đã có ghế khác |
| Ghế thi công — Grok (xAI), Owner lập 18/11/2026 (ADR-0010; **không phải MINH TRÍ** — MINH TRÍ là dự án kinh Phật, không tham gia tài chính) | chép nguồn, ghi chú, mệnh đề, mã theo đặc tả, mở PR nháp | merge, sửa luật, mở API, chạm engine ngoài lệnh |
| Nhóm B | phiên Claude trần, prompt `governance/CONTROL_B_PROMPT.md` | thấy thư viện hay câu trả lời của A |

## 2. Kênh
Lệnh: email trong Gmail Owner, tiêu đề `[TTC] #N — …`, từ và tới tranngocthang12@gmail.com, thân kết `Dừng.`, số N tăng dần. Báo cáo: trả lời đúng email, mở đầu `BAO CAO [TTC] #N`, không dán nội dung tệp. Tệp cho Claude: kho công khai đọc thẳng (codeload/raw) hoặc ZIP nhánh. Đưa tệp lên `main` là PR theo ADR-0003 quyết định 6. Mục này không bị thay bằng tên nhánh `hoc-hieu` (mặc định chưa được Owner chọn trong thiết kế v0.2 mục 9) và không bị thay bằng chat.

## 3. Luật kế thừa (chi tiết ở `governance/LAWS.md`)
Mọi khẳng định có địa chỉ và trích nguyên văn máy kiểm; người viết khác nhà người chấm; ghi chú DRAFT không dùng cho quyết định; không khuyến nghị mua bán; kho công khai không chứa số liệu cá nhân; ba tay người: Owner gộp, Owner đổi luật, thầy giữ đề thi.

## 4. Giai đoạn xây kiến trúc (G0): Claude làm một mình — Owner quyết 22/10/2026
Trong G0 Claude soạn toàn bộ (kiến trúc, luật, hợp đồng, công cụ kiểm, workflow); Owner đưa lên kho và gộp. Hệ quả được chấp nhận: chưa có phản biện độc lập cho thiết kế. Bù đắp: (a) CI kiểm máy mọi tệp mã; (b) Owner đọc ARCHITECTURE.md và LAWS.md trước khi gộp; (c) ghế thi công đã được lập 18/11/2026 (ADR-0010). Phản biện hồi cứu, nếu Owner còn muốn, là tài liệu riêng: không viết thêm vào thân ADR-0002 (đã ACCEPTED cho phạm vi v3.0) và không viết thêm vào quyết định 9 của ADR-0003; (d) ADR-0001 có điều kiện hoàn tác đã được xét tại ADR-0002.

## 5. Phạm vi và điều KHÔNG làm trong 6 tháng
Không mở API trả phí; không chạm engine định lượng ngoài việc hạ lịch và thêm sổ thử (qua ADR); không Media OS; không điền OWNER_PROFILE; không tiền thật; không nhiều ghế song song cùng một việc; không cào dữ liệu sống.
