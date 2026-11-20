# Bằng chứng sự kiện quyền cổ phiếu 11/2025–11/2026 — 19/11/2026

Chỉ số liệu đọc từ thông báo HOSE đã ghim sha256 trong `data/evidence/corporate_actions/EVIDENCE_MANIFEST_2026H2.json`, và từ `engine.adjust.build_events` chạy trên kho giá chỉ-đọc cùng `data/corporate_actions.csv` và `data/derived/yahoo_actions.csv`. Không ghi kho. Không lấy ngày hay tỷ lệ từ báo chí. Không khuyến nghị sửa engine.

Ngày ký là ngày in trên văn bản (`signed_date`). Ngày đó không phải ngày HOSE đăng. Cả 17 văn bản chưa có metadata tin HOSE được ghim và kiểm nội dung trong kho này, nên `published_at` để trống và `published_at_status` là CHƯA XÁC MINH.

VPB (hose-2497757): văn bản in ngày ký 16/09/2026. Ghi nhận trước nói tin HOSE 2497757 đăng 17/09/2026. Không chọn ngày nào làm ngày công bố.

VIB (hose-2490400): văn bản in ngày ký 18/08/2026. Ghi nhận trước nói tin HOSE 2490400 đăng 19/08/2026. Không chọn ngày nào làm ngày công bố.

Nguyên văn loại sự kiện giữ ở `event_type_verbatim`. Trường `event_type` (trường cổng verified-adjusted đọc) để trống, trạng thái CHƯA XÁC MINH. Không ánh xạ sang `stock_split` hay `stock_dividend`. Có PDF, hoặc ngày và hệ số trùng nhau, không đưa sự kiện vào chuỗi kiểm chứng. Cột «Loại engine» dưới đây là nhãn yahoo mà engine đang đọc, không phải loại đã xác minh của văn bản.

Đối chiếu engine dưới đây là kết quả vừa đọc từ `engine.adjust.build_events`, không phải danh sách hệ số trong lệnh Owner. Bản trước so với danh sách đó nên ghi sai số engine. Bảng này chỉ dùng số vừa đọc.

Hệ số văn bản = (cổ cũ + cổ mới) / cổ cũ. Hai phần cổ phiếu được nhận không phải trả tiền trên cùng gốc thì cộng, không nhân. Quyền mua phải trả tiền và cổ tức bằng tiền không đưa vào hệ số. Lệch phiên = vị trí ngày engine trừ vị trí ngày trên văn bản, trên các phiên của mã đó trong kho.

`APPLIED`: engine đang áp hệ số lên giá gốc. `DA_NAM_TRONG_GIA_NGUON`: engine kết luận giá yahoo đã chứa điều chỉnh, không áp lại. Cả hai đều không phải đã kiểm chứng.

| Sự kiện | Bản gốc | Ngày ký | Ngày công bố | Ngày engine | Lệch phiên | Hệ số văn bản so với hệ số engine | Loại engine | Ghi chú |
|---|---|---|---|---|---|---|---|---|
| TPB 2026-10-02 | hose-2500573 | 2026-09-28 | CHƯA XÁC MINH | 2026-10-02 | lệch 0 | 1,15 = 1,15 | yahoo stock_split APPLIED | Thông báo 1958/TB-SGDHCM. Đăng ký cuối cùng 05/10/2026. Nguyên văn: trả cổ tức bằng cổ phiếu, 15%. Cùng văn bản có cổ tức tiền 5% (500 đồng), thanh toán 14/10/2026, không tính vào hệ số. |
| HDB 2026-10-09 | hose-2501920 | 2026-10-02 | CHƯA XÁC MINH | 2026-10-09 | lệch 0 | 1,3 = 1,3 | yahoo stock_split APPLIED | Thông báo 1993/TB-SGDHCM. Đăng ký cuối cùng 12/10/2026. Nguyên văn gồm cổ tức bằng cổ phiếu và phát hành tăng vốn. Cổ tức 100:25 và tăng vốn 100:5 trên cùng gốc, cộng thành 1,3. |
| TCB 2026-10-29 | hose-2507504 | 2026-10-23 | CHƯA XÁC MINH | 2026-10-29 | lệch 0 | 1,5 = 1,5 | yahoo stock_split APPLIED | Thông báo 2100/TB-SGDHCM. Đăng ký cuối cùng 30/10/2026. Nguyên văn: phát hành cổ phiếu để trả cổ tức, 50%. |
| VIC 2025-12-05 | hose-2421566 | 2025-12-01 | CHƯA XÁC MINH | 2025-12-05 | lệch 0 | 2 = 2 | yahoo stock_split DA_NAM_TRONG_GIA_NGUON | Thông báo 2245/TB-SGDHCM. Đăng ký cuối cùng 08/12/2025. Nguyên văn: phát hành tăng vốn từ nguồn vốn chủ sở hữu, cổ phiếu phổ thông 1:1. Cổ phiếu ưu đãi không thuộc đối tượng. |
| POW 2025-12-10 | hose-2422161 | 2025-12-04 | CHƯA XÁC MINH | 2025-12-10 | lệch 0 | 1,19 = 1,19 | yahoo stock_split DA_NAM_TRONG_GIA_NGUON | Thông báo 2280/TB-SGDHCM. Đăng ký cuối cùng 11/12/2025. Cổ tức cổ phiếu 100:4 và tăng vốn 100:15 trên cùng gốc. Quyền mua 100:12 giá 10.000 đồng không cộng vào hệ số. |
| CTG 2025-12-17 | hose-2423183 | 2025-12-10 | CHƯA XÁC MINH | 2025-12-17 | lệch 0 | 1,4463658403 khác 1,4463658 | yahoo stock_split DA_NAM_TRONG_GIA_NGUON | Thông báo 2304/TB-SGDHCM. Đăng ký cuối cùng 18/12/2025. Nguyên văn: phát hành cổ phiếu để trả cổ tức. Tỷ lệ in 100:44,63658403. Số engine đọc được là 1,4463658, không trùng số trên văn bản. |
| HDB 2025-12-18 | hose-2423661 | 2025-12-12 | CHƯA XÁC MINH | 2025-12-18 | lệch 0 | 1,2969 = 1,2969 | yahoo stock_split DA_NAM_TRONG_GIA_NGUON | Thông báo 2316/TB-SGDHCM. Đăng ký cuối cùng 19/12/2025. Khác sự kiện tháng 10/2026. Cổ tức năm 2024 100:25 và tăng vốn 100:4,69 trên cùng gốc. |
| HPG 2026-05-25 | hose-2462408 | 2026-05-14 | CHƯA XÁC MINH | 2026-05-25 | lệch 0 | 1,1 = 1,1 | yahoo stock_split DA_NAM_TRONG_GIA_NGUON | Thông báo 1121/TB-SGDHCM, ngày ký 14/05/2026. Tên tệp ghi 20260515; không lấy ngày tên tệp làm ngày công bố. Đăng ký cuối cùng 26/05/2026. Nguyên văn: trả cổ tức bằng cổ phiếu, 10%. |
| SSB 2026-05-28 | hose-2464953 | 2026-05-25 | CHƯA XÁC MINH | 2026-05-28 | lệch 0 | 1,205202 = 1,205202 | yahoo stock_split DA_NAM_TRONG_GIA_NGUON | Thông báo 1245/TB-SGDHCM. Đăng ký cuối cùng 29/05/2026. Tỷ lệ in 100:20,5202. |
| ACB 2026-06-15 | hose-2468381 | 2026-06-05 | CHƯA XÁC MINH | 2026-06-15 | lệch 0 | 1,13 = 1,13 | yahoo stock_split DA_NAM_TRONG_GIA_NGUON | Thông báo 1323/TB-SGDHCM. Đăng ký cuối cùng 16/06/2026. Nguyên văn: trả cổ tức bằng cổ phiếu, 100:13. Cùng văn bản có cổ tức tiền 7% (700 đồng), thanh toán 23/06/2026, không tính vào hệ số. |
| VJC 2026-06-16 | hose-2469251 | 2026-06-09 | CHƯA XÁC MINH | 2026-06-16 | lệch 0 | 1,3 = 1,3 | yahoo stock_split DA_NAM_TRONG_GIA_NGUON | Thông báo 1340/TB-SGDHCM. Đăng ký cuối cùng 17/06/2026. Nguyên văn: trả cổ tức bằng cổ phiếu năm 2025, tỷ lệ 100:30. |
| VHM 2026-08-06 | hose-2482208 | 2026-07-23 | CHƯA XÁC MINH | 2026-08-06 | lệch 0 | 2 = 2 | yahoo stock_split DA_NAM_TRONG_GIA_NGUON | Thông báo 1592/TB-SGDHCM. Đăng ký cuối cùng 07/08/2026. Nguyên văn: chi trả cổ tức năm 2025 bằng cổ phiếu, tỷ lệ 1:1. |
| MBB 2026-08-11 | hose-2486778 | 2026-08-05 | CHƯA XÁC MINH | 2026-08-11 | lệch 0 | 1,15 = 1,15 | yahoo stock_split DA_NAM_TRONG_GIA_NGUON | Thông báo 1656/TB-SGDHCM. Đăng ký cuối cùng 12/08/2026. Nguyên văn: trả cổ tức bằng cổ phiếu, 15%. Quyền mua 10:1 giá 10.000 đồng không cộng vào hệ số. |
| SSI 2026-08-17 | hose-2485374 | 2026-07-30 | CHƯA XÁC MINH | 2026-08-17 | lệch 0 | 1,2 = 1,2 | yahoo stock_split DA_NAM_TRONG_GIA_NGUON | Thông báo 1634/TB-SGDHCM. Đăng ký cuối cùng 18/08/2026. Nguyên văn phần cổ phiếu: phát hành tăng vốn từ nguồn vốn chủ sở hữu, tỷ lệ 5:1, không phải cổ tức bằng cổ phiếu. Cùng văn bản có cổ tức tiền 10% (1.000 đồng), thanh toán 14/09/2026, không tính vào hệ số. |
| BID 2026-08-17 | hose-2487984 | 2026-08-11 | CHƯA XÁC MINH | 2026-08-17 | lệch 0 | 1,068433 = 1,068433 | yahoo stock_split DA_NAM_TRONG_GIA_NGUON | Thông báo 1686/TB-SGDHCM. Đăng ký cuối cùng 18/08/2026. Nguyên văn: phát hành tăng vốn từ nguồn vốn chủ sở hữu, tỷ lệ 100:6,8433. |
| VIB 2026-09-10 | hose-2490400 | 2026-08-18 | CHƯA XÁC MINH | 2026-09-10 | lệch 0 | 1,095 = 1,095 | yahoo stock_split DA_NAM_TRONG_GIA_NGUON | Thông báo 1733/TB-SGDHCM. Đăng ký cuối cùng 11/09/2026. Nguyên văn: phát hành tăng vốn từ nguồn vốn chủ sở hữu, 9,5%, không phải cổ tức bằng cổ phiếu. |
| VPB 2026-09-24 | hose-2497757 | 2026-09-16 | CHƯA XÁC MINH | 2026-09-24 | lệch 0 | 1,2604104 = 1,2604104 | yahoo stock_split DA_NAM_TRONG_GIA_NGUON | Thông báo 1903/TB-SGDHCM. Đăng ký cuối cùng 25/09/2026. Nguyên văn: chi trả cổ tức bằng cổ phiếu. Tỷ lệ in 26,04104% (10.000.000 nhận 2.604.104). Số engine đọc được trùng 1,2604104. Ngày ký 16/09/2026 và lời ghi tin đăng 17/09/2026 đều không được dùng làm ngày công bố. |
