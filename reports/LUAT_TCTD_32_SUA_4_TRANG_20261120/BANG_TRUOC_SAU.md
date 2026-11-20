# Bốn lỗi bản chép Luật 32/2024 — đã xác nhận trên ảnh PDF gốc

Ảnh render từ byte PDF đã ghim, không từ `text.md`. Hai PDF không sửa.

| | |
|---|---|
| PDF A `cb-369-370.pdf` | 1188965 byte, SHA-256 `b613a8f94e1955a776035be2b7cd14dc34a76c568973f8db7367324ebf50581a` |
| PDF B `cb-371-372.pdf` | 741096 byte, SHA-256 `67852f403c7f368989ef47f98a47933d732d3d6b9d2db40cda2a9af84b969c49` |
| `text.md` trước | 406064 byte, SHA-256 `8c69c6a2b0c516e8093a22dc2bdba68a0f62944cd25d5fa83789f0863f95aa5a` — **STALE** |
| `text.md` sau | 406070 byte, SHA-256 `bd639d7951f68b6d41d502cb84a7fca53fe0490706c2aa8b84dd7b2b21961d44` |

Không có `pdf_check`. Không SOURCED. Hồ sơ PR #60 đóng từ hash cũ, phải đóng gói lại trước vòng chấm.

## [p9] — CONFIRMED_TRANSCRIPTION_ERROR

`cb-369-370.pdf` trang 9. Ảnh: `p9_full.png`, vùng chữ: `p9_crop.png`.

PDF in ngoặc kép cong “ ”. Bản chép giữ byte WinAnsi 0x93/0x94 thành ký tự điều khiển U+0093/U+0094 (6 cặp, Điều 5). Đã đổi thành U+201C/U+201D. Không đổi chữ trong ngoặc.

## [p81] — CONFIRMED_TRANSCRIPTION_ERROR

`cb-369-370.pdf` trang 81. Ảnh: `p81_full.png`, `p81_crop.png`.

Một dòng in: `a) Thực hiện dịch vụ thanh toán trong nước bao gồm séc, lệnh chi, ủy nhiệm`. Parser tách vì `ự` lệch baseline 7,5pt so với `Th` (ngưỡng cụm 6pt), không phải xuống dòng của bản in. Đã ghép lại đúng dòng nhìn thấy. Dòng kế tiếp `chi, nhờ thu, ...` vẫn là dòng in riêng.

## [p83] — CONFIRMED_TRANSCRIPTION_ERROR

`cb-369-370.pdf` trang 83. Ảnh: `p83_full.png`, `p83_crop.png`.

Một dòng in kết thúc `kiều hối, vàng, bao thanh`. Parser tách `ố` và `i` (lệch khoảng 8pt, x tiếp nối). Đã ghép thành `kiều hối, vàng, bao thanh`. Dòng sau `toán, phát hành thẻ tín dụng, ...` vẫn xuống dòng như bản in. Câu khác trên cùng trang đã có sẵn `kiều hối` nguyên, không đụng.

## [p134] — CONFIRMED_TRANSCRIPTION_ERROR

`cb-371-372.pdf` trang 41. Ảnh: `p134_full.png`, `p134_crop.png`.

Một dòng in: `Điều 185. Quyền, nghĩa vụ của bên nhận chuyển giao bắt buộc`. Parser tách `ĩ` và `a` (lệch 6,6pt). Đã ghép. Không sửa câu khoản 1 phía dưới, câu đó đã nguyên.

## Lỗi cùng kiểu còn lại

Quét baseline 6pt so với 12pt trên PDF A trang 1–93 và PDF B trang 1–59: không còn chỗ nào khác vừa lệch vừa nối tiếp theo x. Không kết luận đã đối chiếu mắt 152 trang. Chưa ký `pdf_check`.
