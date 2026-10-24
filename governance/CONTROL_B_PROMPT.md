# Prompt chuẩn cho Nhóm đối chứng B (v1.0, 22/10/2026)

Đổi prompt này phải qua ADR; hash của khối prompt ghi vào mỗi dự báo B (`model_cutoff`, `prompt_hash`).

Cách dùng: Owner mở một phiên Claude **mới**, không trong Project nào, không đính tệp, không bật tìm kiếm; dán nguyên khối dưới rồi dán câu hỏi; ghi xác suất trả về vào Issue "Forecast" với seat = B.

```text
Bạn trả lời một câu hỏi dự báo có luật phân định rõ. Chỉ dùng kiến thức sẵn có của bạn; không tìm kiếm, không giả định có tài liệu nào được cung cấp. Trả lời đúng ba dòng:
1) p = <xác suất từ 0.05 đến 0.95> rằng mệnh đề đúng theo luật phân định;
2) base_rate = <xác suất nền bạn ước lượng và vì sao, một câu>;
3) model_cutoff = <tháng/năm cắt dữ liệu của bạn theo bạn biết>.
Không giải thích thêm. Không khuyến nghị mua bán.
```

Luật: cùng ngày, cùng câu hỏi với A; B không bao giờ thấy thư viện hay trả lời của A; nếu tỷ lệ bất đồng A–B dưới 10% sau 60 câu, mở ADR đổi B sang mô hình nhà cung cấp khác.
