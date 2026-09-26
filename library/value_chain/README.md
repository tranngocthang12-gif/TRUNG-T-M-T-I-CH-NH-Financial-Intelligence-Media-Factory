# THƯ VIỆN: CHUỖI GIÁ TRỊ HAI ĐẦU

## Đầu ra — người tiêu dùng & cạnh tranh đầu cuối
| Tín hiệu | Phản ánh | Ngành nhạy |
|---|---|---|
| Sức mua, doanh số bán lẻ | Doanh thu sắp tới | Bán lẻ điện máy, trang sức, dược |
| Chiến tranh giá, khuyến mãi dày đặc | Biên lợi nhuận sắp bị bóp | Bán lẻ, đồ uống, sữa, viễn thông |
| Khách chuyển sang đối thủ/thương hiệu mới | Mất thị phần trước khi BCTC lộ | Tiêu dùng, F&B |
| Chuyển kênh (cửa hàng → online, livestream) | Mô hình cũ bị đe dọa | Bán lẻ truyền thống |
| Tăng giá mà khách vẫn mua | Sức mạnh định giá — lợi thế cạnh tranh thật | Thương hiệu mạnh |
| Đơn hàng xuất khẩu | Doanh thu xuất khẩu | Dệt may, thủy sản, gỗ |

## Đầu vào — nguyên liệu
| Nguyên liệu | Ngành chịu ảnh hưởng |
|---|---|
| Quặng sắt, than cốc | Thép |
| Giá khí | Phân đạm, điện |
| Ngô, đậu tương | Thức ăn chăn nuôi, chăn nuôi |
| Bông, xơ sợi | Dệt may |
| Hạt nhựa, dầu thô | Nhựa, bao bì, hàng không, vận tải |
| Đường, sữa bột nhập khẩu | Sữa, bánh kẹo, đồ uống |
| Cước vận tải biển | Xuất nhập khẩu, cảng |

## Mẫu bản đồ chuỗi giá trị cho mỗi Dossier (`library/dossiers/<MÃ>/value_chain.yaml`)
```yaml
ticker: <MÃ>
inputs:                       # đầu vào
  - name: <nguyên liệu>
    cost_share: <% giá vốn>   # nguồn: thuyết minh BCTC
    direction: cost           # cost = tăng giá là bất lợi; revenue = tăng giá là có lợi
    lag_quarters: <độ trễ>
    hedged: <có/không/không rõ>
outputs:                      # đầu ra
  - market: <thị trường>
    revenue_share: <% doanh thu>
    competitors: [<đối thủ>]
    pricing_power: <cao/trung bình/thấp + bằng chứng>
sources: [<nguồn>]
status: DRAFT
```

## Trạng thái
Mọi ghi chú bắt đầu ở DRAFT; tỷ trọng phải trích từ BCTC/thuyết minh mới lên CITED.
