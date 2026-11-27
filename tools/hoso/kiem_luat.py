"""B6 của quy trình hồ sơ mã: kiểm luật và khung của hồ sơ (ADR-0019 QĐ-P5, QĐ-P13; ADR-0020).

0. Định dạng cho phép (kiem_dinh_dang; sửa theo bản chấm L-09 vòng 4): hồ sơ chỉ được dùng một bộ Markdown hẹp, liệt kê
   ở docstring của kiem_dinh_dang. Dòng nào ngoài bộ là lỗi, bất kể nội dung. Mục đích: mọi cách viết làm chữ hiển thị
   khác chữ máy đọc (dấu nhấn mạnh bằng «_», tiêu đề thụt lề hay gạch chân, thực thể và thẻ HTML, ký tự vô hình, mã chen
   giữa chữ…) bị chặn trước khi cổng giá đọc chữ. Tiêu đề cấp hai phải đúng từng chữ một tên của khung (TIEU_DE_CAP_HAI),
   nên tiêu đề khung không chở được dấu hiệu giá. Dấu định dạng cũng không được đổi con số (_dd_so; sửa theo bản chấm
   L-09 vòng 2 của ADR-0021): chữ đậm và mã phải bọc trọn con số, kể cả dấu âm, ngoặc và dấu %.
   ADR-0022 khép bộ này ở mức ký tự: mỗi ký tự của hồ sơ phải thuộc bảng chữ cho phép (CHU_CHO_PHEP, chữ số 0–9,
   DAU_CHO_PHEP, sáu dấu Markdown | * ` _ [ ], và dấu \\ trong mã); ngoặc vuông chỉ dùng cho nhãn đúng dạng (_dd_nhan);
   không có địa chỉ web hay mã biểu tượng; và các cách viết làm người đọc thấy một con số hay một dấu âm mà máy không đọc
   là lỗi (_dd_cach_viet_so). Mục đích: không còn danh sách cấm để vá dần; mọi cách viết ngoài bộ đã liệt kê bị chặn.
1. L-02: không cụm từ khuyến nghị nào ở bất kỳ dòng nào. Dùng đúng bộ mẫu của tools/laws_checks.py, thêm vài cụm
   riêng của hồ sơ mã. Kiểm cứng, không xét ngữ cảnh: câu phủ định có cụm cấm cũng bị bắt — đổi cách viết.
2. Khung: đủ mười hai mục theo thứ tự; có "Một trang", "Kết quả 15 điểm soi", "Danh sách CHƯA BIẾT", "Bảng nguồn". Mỗi
   tiêu đề cấp hai chỉ được xuất hiện một lần; khi tiêu đề lặp, máy báo lỗi và xét thân của lần xuất hiện đầu tiên. Mọi
   tiêu đề cấp hai đứng theo thứ tự của khung, nên một mục ngoài phạm vi đối chiếu («Cách đọc», «Lịch sử sửa», «Phiếu
   máy») không chen được vào giữa các mục có số liệu.
3. Mục 8 để trống cho tới khi Owner sửa L-02 (QĐ-P13): sau khi bỏ chữ đậm và khoảng trắng thừa, thân mục phải đúng bằng
   câu cố định MUC_8. Thêm bất kỳ chữ, chữ số hay bảng nào là lỗi.
   Khoảng giá trị bị cấm ở MỌI mục, bất kể nhãn (QĐ-P13): hai số nối bằng gạch ngang hoặc "đến/tới" kèm đơn vị tiền
   (đồng, nghìn đồng, VND, đ; trong bảng, đơn vị ghi ở tiêu đề cột cũng tính), và các cụm "khoảng giá", "vùng giá",
   "mức giá", "giá mục tiêu", "giá trị nội tại", "giá trị một/mỗi cổ phiếu" đi với số. Chỉ cho qua khi phần chữ đó nằm
   trong đoạn ĐÃ KIỂM và mọi con số của nó có trên trang đã ghi (giá quá khứ có trong nguồn).
   Giới hạn: máy bắt theo mẫu. Khoảng viết thành hai ô "thấp | cao" không kèm cụm nào ở trên, hay hai câu rời mỗi câu
   một giá, thì máy không bắt; ghế phản biện khác hãng đọc.
   Cổng giá cổ phiếu (ADR-0020 QĐ-H3 dòng 5; sửa theo bản chấm L-09 vòng 2 và vòng 3): quy tắc cho phép, không phải
   danh sách cấm. Đơn vị xét là từng phần chữ của kiem_trich_dan.cac_phan_chu (đoạn theo nhãn; hàng bảng kèm tiêu đề
   cột), ở mọi mục.
   Từ chỉ cổ phiếu (co_tu_co_phieu): «cổ phiếu», «co phieu»; «cổ phần», «co phan», «cp» khi không đứng ngay sau «công
   ty» («cty»); mã của hồ sơ (dòng tiêu đề đầu «HỒ SƠ MÃ <MÃ>») đứng ngay sau một từ có «giá» (giá MAU, giá bán MAU,
   giá trị MAU) hoặc ngay sau «mã».
   Dấu hiệu giá (dau_hieu_gia):
     (a) con số mang đơn vị giá: đồng, nghìn/ngàn đồng, VND/VNĐ, đ; «nghìn», «ngàn», «k» đứng ngay sau số mà không có
         danh từ nào theo sau, hoặc theo sau bởi «mỗi», «một», «trên» hay «/» rồi «cp», «cổ phiếu», «cổ phần»; «/cp»,
         «/cổ phiếu», «một/mỗi cổ phiếu», «một/mỗi cổ phần». Đơn vị ở tiêu đề cột áp cho ô số. Không tính tỷ đồng,
         triệu đồng, nghìn tỷ;
     (b) chữ «giá» (cả cách gõ «gía») đứng thành một từ, và bốn cụm không dấu GIA_KHONG_DAU. Các từ ghép trong
         GIA_KHONG_TINH, và «giá trị» không theo sau bởi một cụm trong GIA_TRI_TINH, chỉ được loại khi phần chữ và ngữ
         cảnh của nó (đoạn, dòng dẫn, tiêu đề) không có từ chỉ cổ phiếu;
     (c) hệ số định giá (P/E, P/B, P/S, EV/EBITDA) hoặc «vốn hóa», trừ các cụm trong VON_HOA_KHONG_TINH;
     (d) nhãn phủ phần chữ là ĐÃ KIỂM và địa chỉ có một nguồn giá thị trường. Quy ước: mã nguồn giá bắt đầu bằng G.
   Thừa hưởng: các phần chữ của cùng một đoạn (hay một mục liệt kê) dùng chung dấu hiệu. Bảng hay mục liệt kê đứng ngay
   sau một khối có dấu hiệu (không khối nào chen giữa; dòng trống không phải khối) thừa hưởng dấu hiệu, chữ và năm của
   khối đó; dãy mục liệt kê, bảng nối tiếp truyền tiếp. Mọi phần chữ dưới một tiêu đề có dấu hiệu, tới tiêu đề kế tiếp
   cùng cấp hoặc cao hơn, thừa hưởng dấu hiệu, chữ và năm của tiêu đề đó; tiêu đề khung cấp hai («## Mục n.» và
   KHUNG_CAP_HAI) và dòng tiêu đề đầu không truyền.
   Con số của phần chữ có dấu hiệu (so_ngu_canh_gia): MỌI cụm chữ số, chỉ trừ mã tài liệu (L-02, QĐ-P13, ADR-0019), mã
   nguồn và mã giả thuyết dạng một chữ hoa với một hai chữ số (D1, G1, H0), địa chỉ trang, URL; «mục 1–12», «điểm soi
   1–15»; số đầu dòng của danh sách đánh số đúng 1, 2, …, n; ô số thứ tự thật (kiem_trich_dan.cot_so_thu_tu); ngày đủ
   ngày tháng năm, «năm yyyy», «tháng 1–12», «quý 1–4» (năm của chúng xét ở luật 4). Chữ trong nhãn tính như chữ của
   phần nó phủ, trừ từ khóa nhãn, địa chỉ và khóa sổ. Các bộ lọc khác của kiem_trich_dan («điểm 30», «bản 45», «25–30
   kỳ», «12 tháng», «25/4», «25:40», backtick…) không áp. Số viết bằng chữ có bậc («ba mươi nghìn», «hai trăm») cũng
   là con số khi phần chữ hay ngữ cảnh của nó có từ chỉ cổ phiếu hoặc từ chỉ tương lai.
   Luật cho phần chữ có dấu hiệu (sai luật nào báo luật đó, kèm số dòng và dấu hiệu):
     1. có con số thì nhãn phủ nó phải là ĐÃ KIỂM, địa chỉ hợp lệ;
     2. có con số và nhãn ĐÃ KIỂM thì mọi con số có trên trang đã ghi (ngày tháng trên trang chỉ còn năm của nó), hoặc
        khớp dòng gốc của sổ đúng nguồn đúng trang (dòng sửa phải đã chứng minh). Số phần trăm và số có phần lẻ kèm
        «lần» là số tính, miễn đối chiếu. Số viết bằng chữ hay không đọc được theo kiểu Việt Nam thì không đối chiếu được;
     3. có từ trong TU_TUONG_LAI (ở phần chữ, đoạn của nó, dòng dẫn hay tiêu đề), cùng con số, hoặc từ chỉ cổ phiếu,
        hoặc dấu hiệu (d): lỗi, bất kể nhãn, kể cả khi không có con số;
     4. nhãn ĐÃ KIỂM: năm ghi trong phần chữ, tiêu đề cột, dòng dẫn hay tiêu đề (đứng riêng, sau chữ «năm», hay trong
        một ngày) không được lớn hơn năm lớn nhất xuất hiện trên các trang đã ghi.
   Dòng tiêu đề '#', hàng tiêu đề bảng và ô mô tả trong bảng của mục "Bảng nguồn" không mang nhãn, nên xét nới: có dấu
   hiệu (của chính nó hay thừa hưởng) và có số mang đơn vị giá hay số khác năm (kể cả số viết bằng chữ khi có từ chỉ cổ
   phiếu hay từ chỉ tương lai) là lỗi; cộng thêm luật 3.
   Giới hạn của cổng giá, nói thẳng. Máy không bắt:
     1. câu nêu giá tương lai mà phần chữ, dòng dẫn và tiêu đề phụ của nó không có dấu hiệu nào (không chữ «giá», không
        đơn vị tiền, không hệ số định giá, không dẫn nguồn G; từ ghép loại trừ không kèm từ chỉ cổ phiếu cũng không phải
        dấu hiệu), ví dụ «Cổ phiếu MAU kỳ tới về 25,40. [GIẢ ĐỊNH]», «Giá bán của MAU kỳ tới là 31,70. [GIẢ ĐỊNH]»;
     2. dấu hiệu ở một đoạn, con số ở một đoạn khác không phải bảng hay danh sách ngay dưới;
     3. ý tương lai viết bằng từ ngoài TU_TUONG_LAI, với số quá khứ có nguồn (hay số phần trăm, số tính kèm «lần») và
        năm không vượt nguồn;
     4. số viết bằng chữ, khi phần chữ không có từ chỉ cổ phiếu và không có từ chỉ tương lai;
     5. chữ không dấu ngoài bốn cụm đã liệt kê (ký tự thay cho chữ số bị bảng chữ của ADR-0022 chặn);
     6. tệp giá không đặt mã G thì dấu hiệu (d) không nhận ra.
   Lớp bắt các việc này là ghế phản biện khác hãng (B7), với câu hỏi bắt buộc ở templates/hoso/LENH_MAU.md.
4. Mục 11 có giả thuyết H0, H1, H2, điều kiện làm giả thuyết sai và ngày xem lại.
5. Bảng 15 điểm soi đủ mười lăm dòng. Danh sách CHƯA BIẾT có ít nhất một dòng.
6. Đầu hồ sơ ghi rõ đây không phải lời khuyên đầu tư và là bản riêng tư.
7. Bảng nguồn khớp nguon.csv: đủ mã, đúng 12 ký tự đầu sha256.
8. Trạng thái kiểm (ADR-0021 QĐ-K3): tiêu đề cấp hai đầu tiên là "Trạng thái kiểm" và chỉ xuất hiện một lần; mỗi tên
   trong TRANG_THAI_KIEM mở đầu đúng một mục liệt kê riêng («- **Phiếu máy:** …», dòng phải bắt đầu bằng «- »; bỏ chữ
   đậm khi so tên). Máy không kiểm nội
   dung bốn dòng; mục này nằm ngoài phạm vi đối chiếu trích dẫn như "Lịch sử sửa".

Chạy: python tools/hoso/kiem_luat.py --thu-muc <thư mục mã> --ho-so <tệp .md>
"""
import argparse
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools import laws_checks  # noqa: E402
from tools.hoso.chung import NHAN, KhoTrang, khop_co_dau, nfc, tim_so  # noqa: E402
from tools.hoso.kiem_so_lieu import doc_so_lieu  # noqa: E402
from tools.hoso.kiem_trich_dan import (_TAG, cac_phan_chu, doc_dia_chi, khop_dong_goc, lam_sach, loai_nhan,  # noqa: E402
                                       so_tho, tren_trang)

CAM_THEM = [r"n[êe]n n[ắa]m gi[ữu]", r"n[êe]n gi[ữu]", r"khuy[ếe]n ngh[ịi]", r"[đd]i[ểe]m mua", r"[đd]i[ểe]m b[áa]n",
            r"v[ùu]ng mua", r"v[ùu]ng b[áa]n", r"ch[ốo]t l[ờo]i", r"c[ắa]t l[ỗo]", r"gi[áa] h[ợo]p l[ýy]",
            r"[đd][ịi]nh gi[áa] (?:h[ấa]p d[ẫa]n|r[ẻe]|[đd][ắa]t)", r"\bHOLD\b"]
_CAM = re.compile("|".join(laws_checks.RECOMMEND_PATTERNS + CAM_THEM), re.IGNORECASE)
SAU_MUC_12 = ("Kết quả 15 điểm soi", "Danh sách CHƯA BIẾT", "Bảng nguồn")
MUC_8 = "Chưa viết. Theo ADR-0019 QĐ-P13, mục này chỉ viết sau khi Owner sửa L-02."

_SO_TIEN = r"\d+(?:[.,]\d+)*"
_DV_TIEN = r"(?:(?:ngh[ìi]n|ng[àa]n)\s*)?(?:[đd][ồo]ng|vn[đd]|đ)(?!\w)"
_NOI = r"[–—-]|(?<!\w)(?:[đd][ếe]n|t[ớo]i)(?!\w)"            # gạch ngang, "đến", "tới"
_KHOANG_GIA = re.compile(rf"(?<![\w.,])(?P<a>{_SO_TIEN})\s*(?P<dv1>{_DV_TIEN})?\s*(?:{_NOI})"
                         rf"\s*(?P<b>{_SO_TIEN})(?:\s*(?P<dv2>{_DV_TIEN}))?", re.IGNORECASE)
_CUM_GIA = re.compile(r"(?<!\w)(?:kho[ảa]ng\s+gi[áa]|v[ùu]ng\s+gi[áa]|m[ứu]c\s+gi[áa]|gi[áa]\s+m[ụu]c\s+ti[êe]u"
                      r"|gi[áa]\s+tr[ịi]\s+n[ộo]i\s+t[ạa]i"
                      r"|gi[áa]\s+tr[ịi]\s+(?:c[ủu]a\s+)?(?:m[ộo]t|m[ỗo]i)\s+c[ổo]\s+phi[ếe]u)(?!\w)", re.IGNORECASE)
_DV_O = re.compile(r"(?<!\w)" + _DV_TIEN, re.IGNORECASE)
_TY_TRIEU = re.compile(r"(?<!\w)(?:t[ỷy]|tri[ệe]u)\s*$", re.IGNORECASE)

# ---------- cổng giá cổ phiếu: các danh sách là hằng số, có test ----------
GIA_KHONG_TINH = ("giá vốn", "giá thành", "giá bán", "giá mua", "giá gốc", "nguyên giá", "đơn giá", "tỷ giá", "đánh giá",
                  "trị giá", "giá phí")
GIA_TRI_TINH = ("nội tại", "hợp lý", "thị trường", "vốn hóa", "một cổ phiếu", "mỗi cổ phiếu", "một cổ phần", "mỗi cổ phần")
VON_HOA_KHONG_TINH = ("chi phí vốn hóa", "lãi vay vốn hóa", "lãi vay được vốn hóa", "vốn hóa chi phí", "vốn hóa lãi vay")
HE_SO_DINH_GIA = ("P/E", "P/B", "P/S", "EV/EBITDA")
TU_TUONG_LAI = ("dự báo", "dự kiến", "dự phóng", "dự đoán", "kỳ vọng", "ước tính", "mục tiêu", "sẽ", "có thể", "khả năng",
                "tiềm năng", "triển vọng", "tương lai", "sắp tới", "thời gian tới", "kỳ tới", "quý tới", "năm tới",
                "tháng tới", "tuần tới", "phiên tới", "kế tiếp", "hỗ trợ", "kháng cự", "điểm vào", "điểm ra", "xứng đáng",
                "đáng giá", "upside", "downside", "target",
                "kịch bản", "nếu", "giả sử", "giả định", "năm sau", "quý sau", "tháng sau", "tuần sau", "kỳ sau", "sang năm",
                "dự tính", "ước lượng", "ước đạt", "hướng tới", "nhắm", "ngắn hạn", "trung hạn", "dài hạn", "nên", "chờ")
TU_CO_PHIEU = ("cổ phiếu", "cổ phần", "cp", "co phieu", "co phan")
GIA_KHONG_DAU = ("gia co phieu", "gia co phan", "gia cp", "thi gia")
_BIEN_THE = {"hóa": "h(?:óa|oá)", "kỳ": "k[ỳì]", "tỷ": "t[ỷỉ]", "giá": "g(?:iá|ía)"}


def _mau(cum: str) -> str:
    """Biểu thức chính quy của một cụm từ: khoảng trắng co giãn, chấp nhận biến thể hóa/hoá, kỳ/kì, tỷ/tỉ, giá/gía, '/' có
    cách."""
    tu = []
    for w in cum.split():
        tu.append(_BIEN_THE.get(w.lower()) or r"\s*/\s*".join(re.escape(x) for x in w.split("/")))
    return r"\s+".join(tu)


def _cac_cum(cum) -> re.Pattern:
    return re.compile(r"(?<!\w)(?:" + "|".join(_mau(c) for c in sorted(cum, key=len, reverse=True)) + r")(?!\w)",
                      re.IGNORECASE)


_GIA = re.compile(r"(?<!\w)" + _BIEN_THE["giá"] + r"(?!\w)", re.IGNORECASE)
_GIA_KHONG_TINH = _cac_cum(GIA_KHONG_TINH)
_GIA_TRI_KHONG_TINH = re.compile(r"(?<!\w)" + _mau("giá trị") + r"(?!\w)(?!\s+(?:của\s+)?(?:"
                                 + "|".join(_mau(c) for c in GIA_TRI_TINH) + r")(?!\w))", re.IGNORECASE)
_GIA_KHONG_DAU = _cac_cum(GIA_KHONG_DAU)
_VON_HOA = _cac_cum(("vốn hóa",))
_VON_HOA_KHONG_TINH = _cac_cum(VON_HOA_KHONG_TINH)
_HE_SO = re.compile(r"(?<![\w/])(?:" + "|".join(_mau(c) for c in HE_SO_DINH_GIA) + r")(?![\w/])", re.IGNORECASE)
_TUONG_LAI = _cac_cum(TU_TUONG_LAI)
_CO_PHIEU = re.compile(r"(?<!\w)(?<!c[ôo]ng ty )(?<!cty )(?:c[ổo]\s+ph[ầa]n|cp)(?!\w)|(?<!\w)c[ổo]\s+phi[ếe]u(?!\w)",
                       re.IGNORECASE)
_SO_GIA = re.compile(rf"(?<![\w.,]){_SO_TIEN}\s*(?:{_DV_TIEN}|(?:ngh[ìi]n|ng[àa]n|k)(?!\s*\w)"
                     r"|/\s*(?:cp|c[ổo]\s*phi[ếe]u)(?!\w))", re.IGNORECASE)
_SO_MOI_CP = re.compile(rf"(?<![\w.,]){_SO_TIEN}\s*(?:ngh[ìi]n|ng[àa]n|k)\s*(?:(?:m[ỗo]i|m[ộo]t|tr[êe]n)\s+|/\s*)"
                        r"(?:cp|c[ổo]\s*phi[ếe]u|c[ổo]\s*ph[ầa]n)(?!\w)", re.IGNORECASE)
_MOT_CO_PHIEU = re.compile(r"(?<!\w)(?:m[ộo]t|m[ỗo]i)\s+c[ổo]\s+(?:phi[ếe]u|ph[ầa]n)(?!\w)"
                           r"|/\s*(?:cp|c[ổo]\s*phi[ếe]u)(?!\w)", re.IGNORECASE)
_DAU_DONG = re.compile(r"^\s*(?:[-*]\s+)?\d+\.\s")
_LAN = re.compile(r"\)?\s*l[ầa]n(?!\w)", re.IGNORECASE)
_MA_HO_SO = re.compile(r"^#+\s*HỒ SƠ MÃ\s+([A-Z0-9]{2,6})(?!\w)")

# những thứ có chữ số mà không phải con số, ở phần chữ có dấu hiệu giá (danh sách đóng; các bộ lọc khác của
# kiem_trich_dan._BO KHÔNG áp ở đây)
_KHONG_PHAI_SO = [re.compile(m, re.IGNORECASE) for m in (
    r"https?://\S+",                                                       # đường dẫn
    r"(?<!\w)[A-Z]\d{1,2}\s+tr\.\s*\d+(?:\s*[–-]\s*\d+)?(?:\s*,\s*tr\.\s*\d+(?:\s*[–-]\s*\d+)?)*",   # địa chỉ trang
    r"(?<!\w)tr\.\s*\d+(?:\s*[–-]\s*\d+)?",
    r"(?<!\w)(?:L|ADR|QĐ|QD)-[A-Z]?\d+(?!\w)",                             # mã tài liệu: L-02, ADR-0019, QĐ-P13
    r"(?<!\w)(?-i:[A-Z]\d{1,2})(?!\w)",                                    # mã nguồn, mã giả thuyết: D1, G1, H0
    r"(?<!\w)mục\s+(?:1[0-2]|[1-9])(?!\d)(?![.,]\d)",                      # mục 1–12
    r"(?<!\w)điểm\s+soi\s+(?:1[0-5]|[1-9])(?!\d)(?![.,]\d)",               # điểm soi 1–15
)]
_NGAY_DU = re.compile(r"(?<![\d/.,])(?P<d1>\d{1,2})/(?P<m1>\d{1,2})/(?P<y1>\d{4})(?![\d/])"
                      r"|(?<![\d.,/-])(?P<y2>\d{4})-(?P<m2>\d{1,2})-(?P<d2>\d{1,2})(?![\d-])"
                      r"|(?<!\w)ngày\s+(?P<d3>\d{1,2})\s+tháng\s+(?P<m3>\d{1,2})\s+năm\s+(?P<y3>\d{4})(?!\d)(?![.,]\d)",
                      re.IGNORECASE)
_NAM_THANG_QUY = re.compile(r"(?<!\w)(?:năm\s+(?P<y>\d{4})|tháng\s+(?:1[0-2]|0?[1-9])(?:\s*/\s*(?P<ym>\d{4}))?"
                            r"|quý\s+[1-4](?:\s*/\s*(?P<yq>\d{4}))?)(?!\d)(?![.,]\d)", re.IGNORECASE)
_CUM_SO = re.compile(r"\d+(?:[.,]\d+)*")
_CHU_SO = "một|hai|ba|bốn|năm|sáu|bảy|tám|chín|mười"
_SO_BANG_CHU = re.compile(rf"(?<!\w)(?:{_CHU_SO})(?:\s+(?:{_CHU_SO}|mươi|mốt|lăm|nhăm|tư|linh|lẻ|trăm|nghìn|ngàn|triệu|tỷ|tỉ"
                          r"|rưỡi|không))*(?!\w)", re.IGNORECASE)
_BAC_CHU = re.compile(r"(?<!\w)(?:mười|mươi|trăm|nghìn|ngàn|triệu|tỷ|tỉ)(?!\w)", re.IGNORECASE)
_DON_VI_THOI_GIAN = re.compile(r"\s*(?:năm|tháng|quý|tuần|ngày|phiên|kỳ|kì|giờ|phút)(?!\w)", re.IGNORECASE)


KHUNG_CAP_HAI = ("Trạng thái kiểm", "Cách đọc", "Một trang", "Kết quả 15 điểm soi", "Danh sách CHƯA BIẾT", "Bảng nguồn",
                 "Lịch sử sửa", "Phiếu máy")
TRANG_THAI_KIEM = ("Phiếu máy:", "Đối chiếu số khác hãng:", "Phản biện khác hãng:", "Owner tự mở ba số:")


def _la_tieu_de_khung(d: str) -> bool:
    """Tiêu đề cấp hai của khung: '## Mục n…' và các tiêu đề cố định của hồ sơ. Các tiêu đề này không truyền dấu hiệu."""
    ten = d[3:].strip() if d.startswith("## ") else None
    return ten is not None and (re.match(r"Mục \d+\.", ten) is not None or any(ten.startswith(x) for x in KHUNG_CAP_HAI))


# ---------- định dạng cho phép (sửa theo bản chấm L-09 vòng 4) ----------
TIEU_DE_CAP_HAI = (
    "Cách đọc", "Một trang",
    "Mục 1. Doanh nghiệp làm gì: tiền đến từ đâu", "Mục 2. Loại doanh nghiệp", "Mục 3. Lợi thế cạnh tranh: bằng chứng số",
    "Mục 4. Ban lãnh đạo và cổ đông", "Mục 5. Sức khỏe tài chính", "Mục 6. Chất lượng lợi nhuận",
    "Mục 7. Tăng trưởng gần đây", "Mục 8. Định giá theo khoảng", "Mục 9. Thị trường chung và chu kỳ",
    "Mục 10. Cung cầu và xu hướng giá (chỉ mô tả, không sinh tín hiệu)",
    "Mục 11. Ba giả thuyết, điều kiện sai, ngày xem lại", "Mục 12. Ca tương tự, thành và bại",
    "Kết quả 15 điểm soi", "Danh sách CHƯA BIẾT (hồ sơ kết thúc ở đây)", "Bảng nguồn (tệp gốc đã ghim)", "Lịch sử sửa",
    "Phiếu máy", "Trạng thái kiểm",
)
_DD_TIEU_DE = re.compile(r"#{1,6} \S")
_DD_MUC = re.compile(r"(?P<thut>(?:  )*)(?:- |\d{1,2}\. )(?P<noi>.*)")
_DD_THUC_THE = re.compile(r"&(?:[A-Za-z][A-Za-z0-9]*|#[0-9]+|#[xX][0-9A-Fa-f]+);")
_DD_THE = re.compile(r"<[A-Za-z!/?]")
_DD_LIEN_KET = re.compile(r"\]\(|\]\[|\]:|!\[|\[\^|^\s*\[[^\]]*\]:")
_DD_KHOA = re.compile(r"(?<![\w])[a-z0-9]+(?:_[a-z0-9]+)+(?!\w)")

# ADR-0022: bảng chữ cho phép. Mỗi ký tự của hồ sơ phải thuộc bảng này; ký tự ngoài bảng là lỗi định dạng, bất kể nghĩa.
# Chữ: 26 chữ Latin hoa và thường, Đ đ, và các nguyên âm tiếng Việt có dấu (dựng sẵn, sau chuẩn hóa NFC). Chữ số: 0–9.
# Dấu: DAU_CHO_PHEP. Sáu dấu Markdown còn hiệu lực, mỗi dấu một luật riêng: | * ` _ [ ]. Trong mã (giữa hai dấu `) thêm \.
_NGUYEN_AM = "aăâeêioôơuưy"
CHU_CHO_PHEP = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzĐđ" + "".join(
    unicodedata.normalize("NFC", v + t) for v in _NGUYEN_AM + _NGUYEN_AM.upper()
    for t in ("", "\u0300", "\u0301", "\u0309", "\u0303", "\u0323")))
DAU_CHO_PHEP = frozenset(" .,;:!?'\"“”‘’«»()/%+=×÷±≈≠≤≥→←…#&-–—−")
DAU_MARKDOWN = frozenset("|*`_[]")
THEM_TRONG_MA = frozenset("\\")
_DD_EMOJI = re.compile(r":[A-Za-z0-9_+\-]+:")                   # «:one:», «:100:» hiện thành hình
_DD_WEB = re.compile(r"://|(?<![\w.])www\.", re.IGNORECASE)      # trình dựng tự biến thành liên kết
_DD_DINH = re.compile(r"(?<![^\W\d_])(?P<chu>[^\W\d_]+)(?P<so>\d+)(?P<sau>[.,]\d|\s?%)?")
_DD_MA_CHO_PHEP = ("VN30", "VN100", "HNX30", "VNX50", "SHA256", "sha256", "CO2", "m2", "m3", "km2")
_DD_KY = re.compile(r"(?:\d{1,2}[TM](?:19|20)\d{2}|(?:Q[1-4]|H[12])[./](?:19|20)\d{2})(?!\d|[.,]\d|\s?%)")
#                                                                kỳ báo cáo: «9T2026», «6M2025», «Q3.2025», «H1/2025»
_DD_GACH_SO = re.compile(r"[-−–](?=\(?\d)")
_DD_GACH_CACH = re.compile(r"[-−–](?=\s+\d)")
_DD_SO_CACH = re.compile(r"(?<![\d.,])\d{1,3}(?: \d{3})+(?![\d.,])")
_DD_SO_CHU = re.compile(r"\d(?:[^\W\d_]+(?=[.,]?\d|\s?%)|[OoIl])")   # chữ kẹp giữa chữ số («5O,5%»), O o I l sau chữ số
_DD_CHU_PT = re.compile(r"[^\W\d_]%")                           # «lO%»: chữ cái trông như chữ số đứng trước dấu %
_DD_NHAY = re.compile(r"\d['’]\d")                              # «1'200»


def _dd_bang_chu(dong: str) -> list:
    """Bảng chữ cho phép (ADR-0022). Trả lỗi của ký tự đầu tiên ngoài bảng (một lỗi mỗi dòng)."""
    trong_ma = False
    for c in dong:
        if c == "`":
            trong_ma = not trong_ma
            continue
        ten = unicodedata.name(c, "không tên")
        if unicodedata.category(c) in ("Cf", "Cc", "Zl", "Zp", "Mn", "Mc", "Me") or (
                unicodedata.category(c) == "Zs" and c != " ") or c == "\u2800" or "FILLER" in ten:
            return [f"ký tự U+{ord(c):04X} ({ten})"]
        if not (c in CHU_CHO_PHEP or "0" <= c <= "9" or c in DAU_CHO_PHEP or c in DAU_MARKDOWN
                or (trong_ma and c in THEM_TRONG_MA)):
            return [f"ký tự «{c}» U+{ord(c):04X} ({ten}) ngoài bảng chữ cho phép (ADR-0022): chữ Latin và chữ Việt, chữ số "
                    "0–9, dấu câu thường dùng; không dùng ~ $ < > \\ ^ @ { } và mọi ký hiệu khác"]
    return []


def _dd_nhan(dong: str) -> list:
    """Ngoặc vuông chỉ dùng cho nhãn, và nhãn đúng dạng (ADR-0022). Đọc trên chữ hiển thị (bỏ ** và `; trong mã không có
    ngoặc vuông, nên mọi ngoặc vuông của dòng đều nằm ngoài mã). Máy xếp nhãn theo loại đứng đầu (loai_nhan), nên:
      - nhãn mở đầu ngay bằng một trong bốn loại: ĐÃ KIỂM, SUY LUẬN, GIẢ ĐỊNH, CHƯA BIẾT;
      - «sổ số liệu» chỉ đứng trong nhãn SUY LUẬN (ở nhãn khác máy không đọc khóa);
      - nhãn GIẢ ĐỊNH, CHƯA BIẾT không nhắc loại nào khác: máy không kiểm số của hai loại này, nên «[GIẢ ĐỊNH, SUY LUẬN,
        sổ số liệu: …]» hay «[CHƯA BIẾT; ĐÃ KIỂM D1 tr.3]» cho người đọc tưởng số đã được kiểm. Nhãn ĐÃ KIỂM, SUY LUẬN
        được nhắc loại khác trong ghi chú («[ĐÃ KIỂM D1 tr.1. Biên lợi nhuận gộp là SUY LUẬN, tính từ hai dòng trên]»): máy
        kiểm số theo loại đứng đầu, là loại chặt hơn."""
    hien = dong.replace("**", "").replace("`", "")
    loi = []
    con = _TAG.sub(" ", hien)
    if "[" in con or "]" in con:
        loi.append("ngoặc vuông «[ ]» ngoài nhãn (ngoặc vuông chỉ dùng cho nhãn ĐÃ KIỂM, SUY LUẬN, GIẢ ĐỊNH, CHƯA BIẾT; "
                   "liên kết, chú thích chân trang, ô đánh dấu đều dùng ngoặc vuông)")
    for m in _TAG.finditer(hien):
        noi, nhan = m.group(0)[1:-1], m.group(0)[:60]
        if "|" in noi:
            loi.append(f"nhãn «{nhan}» chứa dấu «|» (trong bảng, dấu này tách ô và cắt đôi nhãn)")
        elif not noi.startswith(NHAN):
            loi.append(f"nhãn «{nhan}» phải mở đầu ngay bằng loại nhãn: ĐÃ KIỂM, SUY LUẬN, GIẢ ĐỊNH hay CHƯA BIẾT")
        elif "sổ số liệu" in noi.casefold() and not noi.startswith("SUY LUẬN"):
            loi.append(f"nhãn «{nhan}»: «sổ số liệu» chỉ đứng trong nhãn SUY LUẬN")
        elif noi.startswith(("GIẢ ĐỊNH", "CHƯA BIẾT")) and sum(noi.count(x) for x in NHAN) > 1:
            loi.append(f"nhãn «{nhan}»: nhãn GIẢ ĐỊNH, CHƯA BIẾT không nhắc loại nhãn khác (máy không kiểm số của hai loại "
                       "này); tách phần chữ ra hai nhãn")
    return loi


def _dd_cach_viet_so(dong: str, cac_doan: list, dau_muc) -> list:
    """Cách viết làm người đọc thấy một con số (hay một dấu âm) mà máy không đọc (ADR-0022). Xét chữ ngoài mã và ngoài
    nhãn, sau khi bỏ dấu **. dau_muc: vị trí ký hiệu «- » của mục liệt kê (None nếu dòng không phải mục liệt kê «- »)."""
    g = _TAG.sub(lambda m: " " * len(m.group(0)), "\x00".join(cac_doan[0::2]).replace("**", ""))
    loi = []
    for m in _DD_DINH.finditer(g):                               # chữ cái dính liền trước chữ số: máy coi là mã
        dau, cuoi = m.start(), m.end("so")
        while dau and (g[dau - 1].isalnum() or g[dau - 1] == "_"):
            dau -= 1
        while cuoi < len(g) and (g[cuoi].isalnum() or g[cuoi] == "_"):
            cuoi += 1
        tu, chu = g[dau:cuoi], m.group("chu")
        ky = _DD_KY.match(g, dau)
        if ky and ky.end() >= m.end():
            continue                                             # kỳ báo cáo: «9T2026», «Q3.2025»
        if not m.group("sau") and (re.fullmatch(r"[0-9a-fA-F]{7,64}", tu) or tu in _DD_MA_CHO_PHEP or (
                re.fullmatch(r"[A-Z]", chu) and len(m.group("so")) <= 2 and g[m.start() - 1:m.start()] != "/")):
            continue                                             # mã băm, mã nhận tệp, tên chỉ số, mã nguồn (D1, H0, Q3)
        loi.append(f"con số dính liền sau chữ cái («{tu}{m.group('sau') or ''}»): máy coi cả cụm là một mã và không đọc "
                   "con số; thêm dấu cách giữa chữ và số")
        break
    for m in _DD_GACH_SO.finditer(g):                            # dấu gạch sát trước chữ số
        truoc = g[:m.start()]
        if g[m.end()] == "(":
            loi.append("dấu trừ đứng trước ngoặc («-(36,4%)»): máy không đọc dấu này; viết «-36,4%» hay «(36,4)»")
            break
        c = truoc[-1:]
        if c in (".", ","):
            loi.append("dấu trừ dính sau dấu chấm hay dấu phẩy («20,0%,-36,4%»): máy đọc số không dấu; thêm dấu cách")
            break
        if c.isalpha():
            chu = re.search(r"[^\W\d_]+$", truoc).group(0)
            sau = re.match(r"\d+([.,]\d|\s?%)?", g[m.end():])
            if not (chu.upper() == chu and not sau.group(1)):   # mã viết hoa nối số nguyên: L-02, ADR-0019, PR-120
                loi.append(f"dấu trừ dính sau chữ cái («{chu}{m.group(0)}…»): máy đọc số không dấu; thêm dấu cách trước "
                           "dấu trừ")
                break
    for m in _DD_GACH_CACH.finditer(g):                          # dấu gạch đứng cách con số
        if m.start() == dau_muc:
            continue                                             # ký hiệu mục liệt kê «- »
        c = g[:m.start()].rstrip()[-1:]
        if not (c.isdigit() or c == "%"):                        # sau một con số là khoảng: «2020 - 2025»
            loi.append("dấu trừ đứng cách con số («giảm - 36,4%»): máy đọc số không dấu; viết dấu trừ sát con số "
                       "(«-36,4%») hay dùng chữ («giảm 36,4%»)")
            break
    for m in _DD_SO_CHU.finditer(g):                             # chữ cái dính sau chữ số mà người đọc có thể đọc thành số
        dau, cuoi = m.start(), m.end()
        while dau and (g[dau - 1].isalnum() or g[dau - 1] == "_"):
            dau -= 1
        while cuoi < len(g) and (g[cuoi].isalnum() or g[cuoi] == "_"):
            cuoi += 1
        ky = _DD_KY.match(g, dau)
        if not (re.fullmatch(r"[0-9a-fA-F]{7,64}", g[dau:cuoi]) or (ky and ky.end() >= cuoi)):
            loi.append(f"chữ cái dính sau chữ số («{g[dau:cuoi]}»): chữ như O, l, I trông như chữ số, và chữ kẹp giữa hai "
                       "con số làm máy đọc khác người đọc; viết tách chữ và số")
            break
    if _DD_CHU_PT.search(g) or _DD_NHAY.search(g):
        loi.append("dấu % đứng sát sau chữ cái, hay dấu nháy giữa hai chữ số («1'200»): người đọc thấy một con số mà máy "
                   "không đọc; viết con số bằng chữ số 0–9 theo kiểu Việt Nam")
    m = _DD_SO_CACH.search(g)
    if m:
        loi.append(f"số tách hàng nghìn bằng dấu cách («{m.group(0)}»): máy đọc thành nhiều số; viết «"
                   + m.group(0).replace(" ", ".") + "»")
    return loi


def _dd_noi_dong(doan: str, trong_ma: bool) -> list:
    """Lỗi định dạng trong một đoạn chữ của một dòng (trong hay ngoài dấu `)."""
    loi = []
    if trong_ma:                                                 # trong mã: «_» chỉ nằm giữa hai chữ (tên tệp)
        if any(c == "_" and not (0 < i < len(doan) - 1 and doan[i - 1].isalnum() and doan[i + 1].isalnum())
               for i, c in enumerate(doan)):
            loi.append("dấu _ trong mã không nằm giữa hai chữ")
        if any(c in doan for c in "|[]"):                          # ADR-0022: bảng tách ô ở «|» kể cả trong mã
            loi.append("trong mã không dùng «|», «[», «]»")
    elif "_" in _TAG.sub(lambda m: _DD_KHOA.sub("", m.group(0)), doan):   # ngoài mã: «_» chỉ trong khóa sổ trong nhãn
        loi.append("dấu _ ngoài khóa sổ trong nhãn (dấu nhấn mạnh hay chữ nối)")
    if "\\" in doan and not trong_ma:
        loi.append("dấu \\ (ký tự thoát)")
    if "*" in doan.replace("**", "") or "***" in doan:
        loi.append("dấu * lẻ (chỉ dùng ** để in đậm)")
    elif trong_ma and "*" in doan:
        loi.append("dấu ** trong mã (trong mã, ** hiện nguyên văn chứ không in đậm)")
    if "~~" in doan:
        loi.append("dấu ~~")
    if _DD_THUC_THE.search(doan):
        loi.append("thực thể HTML (&…;)")
    if _DD_THE.search(doan):
        loi.append("thẻ HTML hay chú thích HTML (<…)")
    if not trong_ma and _DD_LIEN_KET.search(doan):
        loi.append("liên kết, ảnh, định nghĩa liên kết hay chú thích chân trang")
    if not trong_ma:
        for m in _DD_EMOJI.finditer(doan):                       # ADR-0022: mã biểu tượng; giờ «10:30:45» thì được
            if not (m.group(0)[1:-1].isdigit() and doan[m.start() - 1:m.start()].isdigit()):
                loi.append(f"mã biểu tượng «{m.group(0)}» (trình dựng hiện thành hình)")
                break
    return loi


_GACH_LA = "\u02d7\u207b\u208b\u2796"                           # dấu trừ biến thể không thuộc nhóm gạch ngang (Pd)
_VI_TRI_DAU = re.compile(r"(?<![\w.,])(.)(?=\d)")                # ký tự đứng ở vị trí dấu của một con số (như chung._SO)


def _dd_so(dong: str, cac_doan: list) -> list:
    """Dấu định dạng không được đổi con số (sửa theo bản chấm L-09 vòng 2 của ADR-0021, lỗi chặn 1). cac_doan: dong cắt
    theo dấu `, phần tử lẻ là mã. Bốn luật:
      - mã «`…`» không có dấu cách sát mép trong (trình dựng bỏ dấu cách đó, «-` 36,4 `» hiện thành «-36,4»);
      - dấu ** đủ cặp trên một dòng, chữ đậm không trống và không có dấu cách sát mép trong;
      - đọc số trên chữ hiển thị (bỏ dấu ** và dấu `) phải ra đúng các con số như khi thay mỗi dấu đó bằng một dấu cách:
        dấu định dạng không tách dấu âm, ngoặc, phần lẻ hay dấu % khỏi con số, không cắt đôi con số, không dán con số
        vào chữ;
      - ký tự gạch ngang mà máy không đọc là dấu âm (gạch dài «—», gạch nối không ngắt U+2011, dấu trừ nhỏ…) không được
        dính liền trước chữ số ở vị trí của dấu âm."""
    loi = []
    if any(d != d.strip() for d in cac_doan[1::2]):
        loi.append("mã «`…`» có dấu cách sát mép trong")
    dam = "\x00".join(cac_doan[0::2]).split("**")               # chữ ngoài mã; mỗi đoạn mã giữ chỗ bằng một ký tự
    if len(dam) % 2 == 0:
        loi.append("dấu ** không đủ cặp trên một dòng")
    elif any(not d or d != d.strip() for d in dam[1::2]):
        loi.append("chữ đậm «**…**» trống hay có dấu cách sát mép trong")

    def doc(t):
        return [(x.raw, x.gia_tri, x.pt) for x in tim_so(" ".join(t.split()))]
    hien = dong.replace("**", "").replace("`", "")
    if doc(hien) != doc(dong.replace("**", " ").replace("`", " ")):
        loi.append("dấu ** hay ` chen vào con số (tách dấu âm, ngoặc, phần lẻ hay dấu % khỏi con số, cắt đôi con số, hay "
                   "dán con số vào chữ): đặt trọn con số vào trong hoặc ra ngoài dấu định dạng")
    for m in _VI_TRI_DAU.finditer(hien):
        c = m.group(1)
        if c not in "-−–" and (unicodedata.category(c) == "Pd" or c in _GACH_LA):
            loi.append(f"ký tự U+{ord(c):04X} ({unicodedata.name(c, 'không tên')}) dính liền trước chữ số trông như dấu âm "
                       "nhưng máy không đọc là dấu âm: dùng «-» hay «−», hoặc thêm dấu cách")
            break
    return loi


def _dd_bang(bang: list) -> list:
    """Bảng phải là bảng thật của trình dựng (sửa cùng loại với lỗi chặn 2 của bản chấm L-09 vòng 2, ADR-0021). bang:
    [(số dòng, dòng)] của một dãy dòng liền nhau bắt đầu bằng «|». Dòng thứ hai phải là dòng kẻ «|---|» có đủ số ô của
    hàng tiêu đề; thiếu thì trình dựng hiện cả dãy thành đoạn chữ, trong khi máy vẫn đọc là bảng. Mỗi hàng phải có đúng số
    ô của hàng tiêu đề: trình dựng bỏ ô thừa, trong khi máy đọc mọi ô. Trả [(số dòng, lỗi)]."""
    def o(d):
        d = d.strip()
        return [c.strip() for c in d[1:-1 if d.endswith("|") and len(d) > 1 else None].split("|")]
    n = len(o(bang[0][1]))
    if len(bang) < 2 or len(o(bang[1][1])) != n or not all(re.fullmatch(r":?-+:?", c) for c in o(bang[1][1])):
        return [(bang[0][0], "bảng thiếu dòng kẻ «|---|» ngay dưới hàng tiêu đề, hay dòng kẻ không đủ số ô của hàng tiêu đề "
                             "(trình dựng hiện thành đoạn chữ, không thành bảng)")]
    return [(so, f"hàng bảng có {len(o(d))} ô, hàng tiêu đề có {n} ô (trình dựng bỏ ô thừa; ô thiếu thì thêm ô trống)")
            for so, d in bang[2:] if len(o(d)) != n]


def kiem_dinh_dang(text: str) -> list:
    """Hồ sơ chỉ được dùng một bộ Markdown hẹp. Dòng nào ngoài bộ này là lỗi, bất kể nội dung (danh sách cho phép, không
    phải danh sách cấm). Bộ cho phép:
      - dòng trống; dòng chữ bắt đầu sát lề, không bắt đầu bằng «>», «<», «=», «```», «~~~», «* », «+ », «1) »;
      - tiêu đề «# …» tới «###### …» sát lề, có một dấu cách sau dấu #; «# » chỉ ở dòng đầu; tiêu đề cấp hai đúng từng
        chữ một tên trong TIEU_DE_CAP_HAI;
      - hàng bảng bắt đầu sát lề bằng «|»; dòng nào có «|» thì phải là hàng bảng; bảng có dòng kẻ «|---|» ngay dưới
        hàng tiêu đề và mọi hàng đủ đúng số ô của hàng tiêu đề (_dd_bang);
      - mục liệt kê «- » hay «1. », thụt 0, 2, 4… dấu cách; nội dung mục không bắt đầu bằng «#», «>», «|», «<» hay «`»;
      - đường kẻ «---» đúng ba dấu, đứng sau một dòng trống;
      - trong dòng: chữ đậm «**…**»; mã «`…`» với số dấu ` chẵn, không dính liền chữ ở mặt ngoài; dấu «_» ngoài mã chỉ
        trong khóa sổ dạng chữ thường không dấu «a_b_1» nằm trong một nhãn, trong mã chỉ khi nằm giữa hai chữ (tên tệp);
      - dấu định dạng không đổi con số (_dd_so): chữ đậm và mã mở, đóng trên cùng một dòng, không có dấu cách sát mép
        trong, bọc trọn con số (cả dấu âm, ngoặc, dấu %); trong mã không có dấu *;
      - ADR-0022: mọi ký tự thuộc bảng chữ cho phép (_dd_bang_chu); ngoặc vuông chỉ dùng cho nhãn đúng dạng, trong mã
        không có «|», «[», «]» (_dd_nhan); không có «://», «www.», mã biểu tượng «:x:»; cách viết số và dấu âm theo
        _dd_cach_viet_so.
    Không cho phép: dấu cách khác dấu cách thường (tab, dấu cách cứng…); ký tự định dạng vô hình (rộng 0, gạch nối mềm,
    đổi chiều), ký tự trống thuộc nhóm chữ hay ký hiệu (các ký tự «FILLER» của Hangul, ô Braille trống U+2800: dính liền
    trước một con số thì con số thành mã, máy không đọc) và dấu kết hợp đứng riêng sau chuẩn hóa NFC (chữ Việt chuẩn luôn
    là chữ dựng sẵn); dấu «_» hay «*» để
    nhấn mạnh; «~» (kể cả một dấu), «$», «<», «>», «^», «@», «{», «}»; dấu \\ ngoài mã; thực thể và thẻ HTML; liên kết,
    định nghĩa liên kết, ảnh, chú thích chân trang, ô đánh dấu; trích dẫn «>»; khối mã
    (```, ~~~ hay thụt lề); tiêu đề gạch chân (=== hay --- ngay dưới một dòng chữ); dòng thụt lề mà không phải mục liệt
    kê."""
    loi, truoc, bang = [], "", []
    cac_dong = nfc(text).split("\n")
    for so, dong in enumerate(cac_dong + [""], 1):               # dòng trống thêm ở cuối để khép bảng cuối tệp
        if dong.startswith("|"):
            bang.append((so, dong))
        elif bang:
            loi.extend(f"dòng {d}: định dạng ngoài bộ cho phép — {b}" for d, b in _dd_bang(bang))
            bang = []
        if so > len(cac_dong):
            break
        bao = _dd_bang_chu(dong)                                 # ADR-0022: bảng chữ cho phép
        if _DD_WEB.search(dong):
            bao.append("địa chỉ web («://», «www.»): trình dựng biến thành liên kết, máy bỏ qua chữ số trong đó")
        than, dau_muc = dong, None
        if not dong.strip():
            pass
        elif dong.startswith("#"):
            if not _DD_TIEU_DE.match(dong):
                bao.append("tiêu đề phải là 1–6 dấu # sát lề rồi một dấu cách")
            elif dong.startswith("# ") and so != 1:
                bao.append("tiêu đề cấp một chỉ ở dòng đầu")
            elif dong.startswith("## ") and dong[3:].strip() not in TIEU_DE_CAP_HAI:
                bao.append("tiêu đề cấp hai phải đúng từng chữ một tên của khung (TIEU_DE_CAP_HAI)")
        elif dong.startswith("|"):
            pass
        elif re.fullmatch(r"=+\s*", dong) or (re.fullmatch(r"-+\s*", dong) and (truoc.strip() or dong.strip() != "---")):
            bao.append("tiêu đề gạch chân hay đường kẻ sai (chỉ cho «---» sau một dòng trống)")
        else:
            m = _DD_MUC.fullmatch(dong)
            if m:
                than = m.group("noi")
                dau_muc = len(m.group("thut")) if dong[len(m.group("thut"))] == "-" else None
                if than[:1] in ("#", ">", "|", "<", "`") or not than.strip():
                    bao.append("nội dung mục liệt kê không được là tiêu đề, trích dẫn, bảng, HTML, mã hay trống")
            elif dong[:1].isspace():
                bao.append("dòng thụt lề mà không phải mục liệt kê (khối mã, đoạn nối, tiêu đề thụt)")
            elif dong[:1] in (">", "<", "=") or dong.startswith(("```", "~~~")) or re.match(r"[*+] |\d{1,9}\) ", dong):
                bao.append(f"dòng bắt đầu bằng «{dong[:3]}» (trích dẫn, HTML, khối mã hay ký hiệu liệt kê khác «- », «1. »)")
            elif "|" in dong:
                bao.append("dấu | ngoài hàng bảng")
        if dong.count("`") % 2:
            bao.append("số dấu ` lẻ")
        elif "``" in dong or any((a > 0 and dong[a - 1].isalnum()) or (b + 1 < len(dong) and dong[b + 1].isalnum())
                                 for a, b in zip(*[iter([i for i, c in enumerate(dong) if c == "`"])] * 2)):
            bao.append("mã «`…`» dính liền chữ ở mặt ngoài, hay dùng hai dấu ` liền nhau")
        else:
            cac_doan = dong.split("`")
            for k, doan in enumerate(cac_doan):
                bao.extend(_dd_noi_dong(doan, trong_ma=k % 2 == 1))
            bao.extend(_dd_so(dong, cac_doan))
            bao.extend(_dd_nhan(dong))                           # ADR-0022: ngoặc vuông chỉ cho nhãn đúng dạng
            bao.extend(_dd_cach_viet_so(dong, cac_doan, dau_muc))   # ADR-0022: số người đọc thấy mà máy không đọc
        for b in dict.fromkeys(bao):
            loi.append(f"dòng {so}: định dạng ngoài bộ cho phép — {b}")
        truoc = dong
    return loi


def chu_trong_nhan(nhan: str) -> str:
    """Chữ tự do trong một nhãn: bỏ từ khóa nhãn, khóa sổ (có dấu gạch dưới); địa chỉ nguồn được so_ngu_canh_gia bỏ sau.
    '[GIẢ ĐỊNH: 31,70 nghìn đồng]' → ': 31,70 nghìn đồng'."""
    t = nfc(nhan).strip().strip("[]")
    for n in NHAN:
        t = t.replace(n, " ")
    return re.sub(r"(?<!\w)\w*_\w*", " ", t)


def _chuan(chu: str) -> str:
    """Bỏ nhãn, dấu backtick và dấu đậm; gộp khoảng trắng."""
    return " ".join(_TAG.sub(" ", nfc(chu)).replace("`", " ").replace("*", "").split())


def ma_ho_so(text: str) -> str:
    """Mã của hồ sơ, đọc ở dòng tiêu đề đầu tiên «# HỒ SƠ MÃ <MÃ>» ('' nếu không có)."""
    for d in nfc(text).splitlines():
        if d.startswith("#"):
            m = _MA_HO_SO.match(d)
            return m.group(1) if m else ""
    return ""


def co_tu_co_phieu(chu: str, ma: str = "") -> bool:
    """Phần chữ có từ chỉ cổ phiếu: «cổ phiếu»; «cổ phần», «cp» khi không đứng ngay sau «công ty»; «co phieu», «co phan»;
    mã của hồ sơ ngay sau một từ chứa «giá» (giá MAU, giá bán MAU, giá trị MAU) hoặc ngay sau «mã»."""
    chu = _chuan(chu)
    if _CO_PHIEU.search(chu):
        return True
    return bool(ma) and re.search(r"(?i:(?<!\w)g(?:iá|ía|ia)(?:\s+\w+)?|(?<!\w)m[ãa])\s+" + re.escape(ma) + r"(?!\w)",
                                  chu) is not None


def nguon_gia(nhan: str) -> list:
    """Các mã nguồn giá thị trường (quy ước: mã bắt đầu bằng G) trong địa chỉ của một nhãn ĐÃ KIỂM."""
    return sorted(m for m in doc_dia_chi(nhan) if m.startswith("G")) if loai_nhan(nhan) == "ĐÃ KIỂM" else []


def dau_hieu_gia(chu: str, co_phieu=None, nhan: str = "") -> list:
    """Các dấu hiệu ngữ cảnh giá cổ phiếu có trong một đoạn chữ (đã gắn đơn vị của tiêu đề cột nếu là hàng bảng).
    co_phieu: phần chữ (kể cả ngữ cảnh của nó) có từ chỉ cổ phiếu không; None thì chỉ xét chính đoạn chữ, không xét mã.
    nhan: nhãn phủ phần chữ, cho dấu hiệu (d)."""
    chu = _chuan(chu)
    co_phieu = co_tu_co_phieu(chu) if co_phieu is None else co_phieu
    dh = []
    if _SO_GIA.search(chu) or _MOT_CO_PHIEU.search(chu) or _SO_MOI_CP.search(chu):
        dh.append("(a) đơn vị giá")
    con = chu if co_phieu else _GIA_TRI_KHONG_TINH.sub(" ", _GIA_KHONG_TINH.sub(" ", chu))
    if _GIA.search(con) or _GIA_KHONG_DAU.search(chu):
        dh.append("(b) chữ «giá»")
    if _HE_SO.search(chu) or _VON_HOA.search(_VON_HOA_KHONG_TINH.sub(" ", chu)):
        dh.append("(c) hệ số định giá hoặc vốn hóa")
    if nguon_gia(nhan):
        dh.append(f"(d) nhãn ĐÃ KIỂM dẫn nguồn giá {', '.join(nguon_gia(nhan))}")
    return dh


def _la_nam(s) -> bool:
    return s.so_le == 0 and not s.pt and "." not in s.raw and len(s.raw) == 4 and 1900 <= int(s.raw) <= 2100


def _so_cua(chu: str, la_ti_le: bool = False) -> list:
    """[(So, là số tính được phép)] của một đoạn chữ, sau các bộ lọc của kiem_trich_dan (cách xét nới của tiêu đề)."""
    sach = lam_sach(chu)
    return [(s, la_ti_le or s.pt or bool(_LAN.match(sach[s.vi_tri + len(s.raw):]))) for s in tim_so(sach)]


def so_ngu_canh_gia(chu: str, bo_so_dau: bool = True, cot_pt: bool = False, cot_lan: bool = False) -> tuple:
    """Con số của một phần chữ có dấu hiệu giá: MỌI cụm chữ số, trừ danh sách đóng _KHONG_PHAI_SO, số đầu dòng liệt kê
    (khi bo_so_dau, tức danh sách đánh số đúng 1, 2, …, n) và ngày tháng (ngày đủ, «năm yyyy», «tháng 1–12», «quý 1–4»).
    Trả (so, nam): so = [(chuỗi, So hoặc None nếu không đọc được theo kiểu Việt Nam, là số tính được miễn đối chiếu)];
    nam = các năm (trong ngày tháng, sau «năm», hoặc đứng riêng). Số tính được miễn: số phần trăm, số có phần lẻ kèm «lần»
    (cot_pt, cot_lan: tiêu đề cột ghi % hay «lần»)."""
    t = _chuan(chu)
    if bo_so_dau:
        t = _DAU_DONG.sub(" ", t, count=1)
    for mau in _KHONG_PHAI_SO:
        t = mau.sub(" ", t)
    nam = []

    def ngay(m):
        d, th, y = (int(m.group(f"{k}{i}")) for i in (1, 2, 3) if m.group(f"y{i}") for k in "dmy")
        if 1 <= d <= 31 and 1 <= th <= 12 and 1900 <= y <= 2100:
            nam.append(y)
            return " "
        return m.group(0)

    def nam_thang_quy(m):
        y = m.group("y") or m.group("ym") or m.group("yq")
        if y and not 1900 <= int(y) <= 2100:
            return m.group(0)
        if y:
            nam.append(int(y))
        return " "
    t = _NAM_THANG_QUY.sub(nam_thang_quy, _NGAY_DU.sub(ngay, t))
    doc = {s.vi_tri: s for s in tim_so(t)}
    so = []
    for m in _CUM_SO.finditer(t):
        s = doc.get(m.start())
        if s is None or len(s.raw) != len(m.group(0)):
            so.append((m.group(0), None, False))
            continue
        sau = t[m.end():]
        tinh = s.pt or cot_pt or (s.so_le > 0 and (cot_lan or bool(_LAN.match(sau))))
        so.append((m.group(0), s, tinh))
        if _la_nam(s):
            nam.append(int(s.raw))
    return so, nam


def so_bang_chu(chu: str) -> list:
    """Số viết bằng chữ ('ba mươi nghìn', 'hai trăm'): cụm từ số bắt đầu bằng một chữ số và có ít nhất một bậc (mười,
    mươi, trăm, nghìn, ngàn, triệu, tỷ), không đứng trước đơn vị thời gian. [(cụm, là phần trăm)]."""
    kq = []
    t = _chuan(chu)
    for m in _SO_BANG_CHU.finditer(t):
        cum, sau = m.group(0), t[m.end():]
        tu = cum.split()
        if len(tu) > 1 and tu[-1].lower() == "năm" and re.match(r"\s+\w", sau):   # «mười năm qua»: «năm» là thời gian
            cum, sau = " ".join(tu[:-1]), " năm" + sau
        if not _BAC_CHU.search(cum) or _DON_VI_THOI_GIAN.match(sau):
            continue
        kq.append((cum, bool(re.match(r"\s*phần\s+trăm(?!\w)", sau, re.IGNORECASE))))
    return kq


def _tap_so_khong_ngay(kho, ma: str, trang: int, nho: dict) -> frozenset:
    """Tập giá trị có dấu của các con số trên trang, sau khi thay mỗi ngày tháng bằng năm của nó (ngày và tháng trong một
    ngày không phải giá; năm thì vẫn đối chiếu được)."""
    if (ma, trang) not in nho:
        chu = re.sub(r"(?<!\d)\d{1,2}/\d{1,2}/(\d{4})(?!\d)|(?<!\d)(\d{4})-\d{1,2}-\d{1,2}(?!\d)",
                     lambda m: f" {m.group(1) or m.group(2)} ", kho.van_ban(ma, trang))
        nho[(ma, trang)] = frozenset(s.gia_tri for s in tim_so(chu, kho.kieu_so(ma)))
    return nho[(ma, trang)]


def _cac_trang(kho, dia_chi: dict) -> list:
    return [(ma, t) for ma, trang in dia_chi.items() if ma in kho.nguon
            for t in (sorted(set(trang) & set(kho.cac_trang(ma))) if trang is not None else kho.cac_trang(ma))]


def _dia_chi_hop_le(kho, nhan: str) -> dict:
    """Địa chỉ của nhãn ĐÃ KIỂM nếu hợp lệ (mã có trong nguon.csv, trang có trong kho); {} nếu không."""
    dia_chi = doc_dia_chi(nhan) if loai_nhan(nhan) == "ĐÃ KIỂM" else {}
    if kho is None or not dia_chi or any(m not in kho.nguon for m in dia_chi) or any(
            t not in kho.cac_trang(m) for m, tr in dia_chi.items() if tr is not None for t in tr):
        return {}
    return dia_chi


def kiem_cong_gia(text: str, kho=None) -> list:
    """Cổng giá cổ phiếu (xem đầu tệp). kho=None: không có trang để đối chiếu, nên không phần chữ nào có số ở ngữ cảnh giá
    qua."""
    so_lieu = doc_so_lieu(kho)["dong"] if kho is not None and (kho.thu_muc / "so_lieu.csv").is_file() else []
    ma = ma_ho_so(text)
    dau_tien = next((i for i, d in enumerate(nfc(text).splitlines(), 1) if d.startswith("#")), 0)
    phan = [p for p in cac_phan_chu(text) if p["loai"] != "nhan"]   # chữ của nhãn xét cùng phần nó phủ
    nho = {}
    for p in phan:                                               # chữ để tìm dấu hiệu, chữ để tìm từ, chữ trong nhãn
        p["_bn"] = p["muc"].startswith("Bảng nguồn") and p["chu"].lstrip().startswith("|")
        p["_nhan_chu"] = " ".join(chu_trong_nhan(x) for x in [p["nhan"]] + _TAG.findall(p["chu"]) if x)
        if p["_bn"]:
            o = [c.strip() for c in p["chu"].strip().strip("|").split("|")]
            if len(o) >= 4 and re.fullmatch(r"[A-Z]\d{1,2}", o[0]) and o[-2].isdigit() and re.fullmatch(
                    r"[0-9a-f]{12}", o[-1]):
                p["_dh_chu"] = " | ".join(o[1:-2])               # hàng nguồn đúng định dạng: chỉ xét ô mô tả
            else:
                p["_dh_chu"] = p["chu"]
            p["_van"] = _chuan(p["_dh_chu"])
        elif p["loai"] == "hang_bang":                           # chữ gồm cả tiêu đề cột; đơn vị ở tiêu đề áp cho ô số
            dv = [_don_vi_gia(x) for x in p["tieu_de"]]
            p["_dh_chu"] = " | ".join(p["tieu_de"]) + " || " + " | ".join(
                c + (" " + dv[j] if j < len(dv) and dv[j] and re.search(r"\d", c) and not _DV_O.search(c) else "")
                for j, c in enumerate(p["o"])) + " || " + p["_nhan_chu"]
            p["_van"] = _chuan(" | ".join(p["tieu_de"]) + " || " + " | ".join(p["o"]) + " || " + p["_nhan_chu"])
        else:
            p["_dh_chu"] = p["chu"] + " " + p["_nhan_chu"]
            p["_van"] = _chuan(p["_dh_chu"])
    phan = [p for p in phan if re.search(r"\w", p["_van"])]     # phần rỗng (sau nhãn cuối đoạn) không xét
    khoi = {}
    for p in phan:
        khoi.setdefault(p["khoi"], []).append(p)
    kieu = {b: ds[0]["kieu_khoi"] for b, ds in khoi.items()}
    so_dau, chuoi = {}, []                                       # danh sách đánh số đúng 1, 2, …, n: bỏ số đầu dòng
    for b in sorted(khoi) + [None]:
        if b is not None and kieu[b] == "muc":
            m = _DAU_DONG.match(khoi[b][0]["chu"])
            if m:
                chuoi.append((b, int(re.search(r"\d+", m.group(0)).group(0))))
            continue
        hop_le = [n for _, n in chuoi] == list(range(1, len(chuoi) + 1))
        so_dau.update({x: hop_le for x, _ in chuoi})
        chuoi = []
    tren, ngan = {}, []                                          # tiêu đề đang phủ từng phần chữ (trừ tiêu đề khung)
    for p in sorted(phan, key=lambda x: x["dong"]):
        if p["loai"] == "tieu_de":
            while ngan and ngan[-1]["cap"] >= p["cap"]:
                ngan.pop()
            tren[id(p)] = list(ngan)
            if p["dong"] != dau_tien and not _la_tieu_de_khung(p["chu"]):
                ngan.append(p)
        else:
            tren[id(p)] = list(ngan)
    dan, dh_khoi, loi = {}, {}, []                               # dan: (chữ, năm, dấu hiệu) của dòng dẫn mà khối thừa hưởng
    for b in sorted(khoi):
        ds = khoi[b]
        truoc = b - 1
        if kieu[b] in ("bang", "muc") and truoc in khoi and kieu[truoc] != "tieu_de" and not ds[0]["_bn"]:
            cu = dan.get(truoc, ([], [], []))
            dan[b] = ([p["_van"] for p in khoi[truoc]] + cu[0],
                      [y for p in khoi[truoc] for y in so_ngu_canh_gia(p["_van"], False)[1]] + cu[1],
                      [(x, f"ở dòng dẫn {khoi[truoc][0]['dong']}") for x, nguon in dh_khoi[truoc] if not nguon]
                      + [(x, nguon) for x, nguon in dh_khoi[truoc] if nguon.startswith("ở dòng dẫn")])
        lead = dan.get(b, ([], [], []))
        chung = kieu[b] in ("doan", "muc")                       # các phần của một đoạn (mục liệt kê) dùng chung dấu hiệu
        for p in ds:
            p["_ngu_canh"] = " ".join(([q["_van"] for q in ds] if chung else [p["_van"]]) + lead[0]
                                      + [h["_van"] for h in tren[id(p)]])
            p["_cp"] = co_tu_co_phieu(p["_ngu_canh"], ma)
            p["_dh"] = dau_hieu_gia(p["_dh_chu"], p["_cp"], p["nhan"])
        for p in ds:
            dh = [(x, "") for x in p["_dh"]]
            if chung:
                dh += [(x, "ở phần chữ khác cùng đoạn") for q in ds if q is not p for x in q["_dh"]]
            dh += lead[2]
            dh += [(x, f"ở tiêu đề dòng {h['dong']}") for h in tren[id(p)] for x, nguon in h["_dh_tat_ca"]]
            gon = {}
            for x, nguon in dh:
                gon.setdefault(x, nguon)
            p["_dh_tat_ca"] = list(gon.items())
        gop = {}                                                 # dấu hiệu của cả khối: của chính khối thì nguồn ''
        for p in ds:
            for x, nguon in p["_dh_tat_ca"]:
                nguon = "" if nguon in ("", "ở phần chữ khác cùng đoạn") else nguon
                if x not in gop or not nguon:
                    gop[x] = nguon
        dh_khoi[b] = list(gop.items())
        for p in ds:
            if p["_dh_tat_ca"]:                                 # số thứ tự chỉ bỏ ở đúng đầu mục liệt kê (ADR-0022)
                dau_muc = p["stt_dau"] or (p["loai"] == "ngoai" and p is ds[0])
                loi.extend(_kiem_phan(p, kho, so_lieu, so_dau.get(b, False) and dau_muc, lead, tren[id(p)], nho))
    return loi


def _kiem_phan(p, kho, so_lieu, bo_so_dau, dan, tren, nho) -> list:
    """Bốn quy tắc cho một phần chữ có dấu hiệu giá (của chính nó hay thừa hưởng)."""
    dh = "; ".join(f"{x} {nguon}".strip() for x, nguon in p["_dh_tat_ca"])
    tl = sorted({m.group(0).lower() for m in _TUONG_LAI.finditer(p["_ngu_canh"])})
    la_d = any(x.startswith("(d)") for x, _ in p["_dh_tat_ca"])
    if p["loai"] in ("tieu_de", "tieu_de_bang") or p["_bn"]:    # không mang nhãn: xét nới, bỏ qua năm đứng riêng
        dau = f"dòng {p['dong']}: tiêu đề hay bảng nguồn ở ngữ cảnh giá cổ phiếu (dấu hiệu: {dh})"
        chu = nfc(p["_dh_chu"]).replace("`", "").replace("*", "")
        so = [s.raw for s, _ in _so_cua(_TAG.sub(" ", chu)) if not _la_nam(s)]
        so += [x for x, _ in so_bang_chu(chu)] if (p["_cp"] or tl) else []
        kq = []
        if _SO_GIA.search(chu) or _SO_MOI_CP.search(chu) or so:
            kq.append(f"{dau} — quy tắc nới: chỗ này không mang nhãn ĐÃ KIỂM, nên không được nêu giá cổ phiếu, hệ số định "
                      "giá hay vốn hóa kèm số (ADR-0020 QĐ-H3)")
        if tl and (so or p["_cp"]):
            kq.append(f"{dau} — quy tắc 3: từ chỉ tương lai {', '.join(f'«{x}»' for x in tl)} đi cùng "
                      + ("con số" if so else "từ chỉ cổ phiếu") + ", lỗi bất kể nhãn (ADR-0020 QĐ-H3)")
        return kq
    if p["loai"] == "hang_bang":
        o, td = list(p["o"]), list(p["tieu_de"])
        if p["stt"] and o:
            o[0] = ""
        so, nam = [], []
        for j, c in enumerate(o):
            tde = td[j] if j < len(td) else ""
            x, y = so_ngu_canh_gia(c, False, "%" in tde, bool(re.search(r"(?<!\w)l[ầa]n(?!\w)", tde, re.IGNORECASE)))
            so, nam = so + x, nam + y
        nam += [y for c in td for y in so_ngu_canh_gia(c, False)[1]]
        rieng = " | ".join(o)
    else:
        so, nam = so_ngu_canh_gia(p["chu"], bo_so_dau)
        rieng = p["chu"]
    x, y = so_ngu_canh_gia(p["_nhan_chu"], False)                # chữ trong nhãn (ngoài từ khóa, địa chỉ, khóa sổ)
    so, nam, rieng = so + x, nam + y + dan[1] + [y for h in tren for y in so_ngu_canh_gia(h["_van"], False)[1]], \
        rieng + " " + p["_nhan_chu"]
    chu_so = so_bang_chu(rieng) if (p["_cp"] or tl) else []
    cac_so = [x for x, _, _ in so] + [x for x, _ in chu_so]
    nhan = p["nhan"]
    dia_chi = _dia_chi_hop_le(kho, nhan)
    dau = f"dòng {p['dong']}: ngữ cảnh giá cổ phiếu (dấu hiệu: {dh})"
    duoi = (". Giá cổ phiếu, hệ số định giá và vốn hóa chỉ được nêu dưới dạng số quá khứ có nguồn trong đoạn ĐÃ KIỂM, "
            "không kèm từ chỉ tương lai (ADR-0020 QĐ-H3)")
    kq = []
    if cac_so and loai_nhan(nhan) != "ĐÃ KIỂM":
        kq.append(f"{dau} — quy tắc 1: có con số ({', '.join(cac_so)}) mà nhãn {nhan or '(không có)'} không phải ĐÃ KIỂM"
                  + duoi)
    elif cac_so and not dia_chi:
        kq.append(f"{dau} — quy tắc 1: có con số ({', '.join(cac_so)}) mà địa chỉ của nhãn {nhan} không hợp lệ hoặc không "
                  "có trang để đối chiếu" + duoi)
    elif cac_so:
        def co(s):
            return any(khop_co_dau(s, _tap_so_khong_ngay(kho, m, t, nho)) for m, t in _cac_trang(kho, dia_chi)) or \
                khop_dong_goc(so_lieu, s, dia_chi)
        thieu = [x for x, s, tinh in so if not tinh and (s is None or not co(s))] + [x for x, pt in chu_so if not pt]
        if thieu:
            kq.append(f"{dau} — quy tắc 2: số không có trên trang đã ghi hay dòng gốc của sổ (ngày tháng trên trang không "
                      f"tính; số viết bằng chữ hay không đọc được theo kiểu Việt Nam thì không đối chiếu được): "
                      f"{', '.join(thieu)}" + duoi)
    if tl and (cac_so or p["_cp"] or la_d):
        kem = "con số" if cac_so else ("từ chỉ cổ phiếu" if p["_cp"] else "nhãn dẫn nguồn giá")
        kq.append(f"{dau} — quy tắc 3: từ chỉ tương lai {', '.join(f'«{x}»' for x in tl)} đi cùng {kem}, lỗi bất kể nhãn"
                  + duoi)
    if loai_nhan(nhan) == "ĐÃ KIỂM" and nam:
        if not dia_chi:
            if not cac_so:
                kq.append(f"{dau} — quy tắc 4: có năm ({', '.join(map(str, sorted(set(nam))))}) mà địa chỉ của nhãn {nhan} "
                          "không hợp lệ, không xét được năm của nguồn" + duoi)
        else:
            co_nam = [int(s.raw) for m, t in _cac_trang(kho, dia_chi)
                      for s in tim_so(kho.van_ban(m, t), kho.kieu_so(m)) if _la_nam(s)]
            vuot = sorted({y for y in nam if not co_nam or y > max(co_nam)})
            if vuot:
                kq.append(f"{dau} — quy tắc 4: năm {', '.join(map(str, vuot))} vượt năm lớn nhất trên trang đã ghi ("
                          + (str(max(co_nam)) if co_nam else "trang không có năm nào") + ")" + duoi)
    return kq


def _cac_muc(dong: list) -> list:
    """[(số dòng, tiêu đề, thân)] của các tiêu đề cấp hai."""
    dau = [i for i, d in enumerate(dong) if d.startswith("## ")]
    return [(i + 1, dong[i][3:].strip(), "\n".join(dong[i + 1:j])) for i, j in zip(dau, dau[1:] + [len(dong)])]


def _gon(text: str) -> str:
    """Bỏ chữ đậm và khoảng trắng thừa."""
    return " ".join(re.sub(r"\*\*|__", "", text).split())


def _don_vi_gia(o: str) -> str:
    """Đơn vị tiền theo giá cổ phiếu ghi trong ô (thường là tiêu đề cột): đồng, nghìn đồng, VND, đ. Trả '' nếu không có,
    hoặc nếu đó là tỷ đồng, triệu đồng."""
    return next((m.group(0) for m in _DV_O.finditer(o) if not _TY_TRIEU.search(o[:m.start()])), "")


def kiem_khoang_gia(text: str, kho=None) -> list:
    """Khoảng giá trị và giá mục tiêu ở mọi mục, bất kể nhãn (QĐ-P13). kho=None: không có trang để đối chiếu, nên không
    phần nào được cho qua."""
    loi = []
    for p in cac_phan_chu(text):
        if p["o"]:                                               # hàng bảng: đơn vị ở tiêu đề cột áp cho ô số
            dv = [_don_vi_gia(x) for x in p["tieu_de"]]
            o = [x + (" " + dv[j] if j < len(dv) and dv[j] and re.search(r"\d", x) and not _DV_O.search(x) else "")
                 for j, x in enumerate(p["o"])]
            chu, kem = " | ".join(o), " | ".join(p["tieu_de"])
        else:
            chu, kem = p["chu"], ""
        chu, kem = chu.replace("`", "").replace("*", ""), kem.replace("`", "").replace("*", "")
        dia_chi = doc_dia_chi(p["nhan"]) if loai_nhan(p["nhan"]) == "ĐÃ KIỂM" and kho is not None else {}
        dia_chi = dia_chi if dia_chi and all(ma in kho.nguon for ma in dia_chi) else {}

        def tren(cac_so) -> bool:
            return bool(dia_chi) and bool(cac_so) and all(tren_trang(kho, s, dia_chi) for s in cac_so)
        vi_tri = 0
        while True:
            m = _KHOANG_GIA.search(chu, vi_tri)
            if m is None:
                break
            vi_tri = m.end() if (m.group("dv1") or m.group("dv2")) else m.start("b")
            if not (m.group("dv1") or m.group("dv2")):
                continue
            hai_dau = tim_so(m.group("a")) + tim_so(m.group("b"))
            if len(hai_dau) != 2 or not tren(hai_dau):
                loi.append(f"dòng {p['dong']}: khoảng giá «{m.group(0).strip()}» — QĐ-P13 cấm khoảng giá trị ở mọi mục, "
                           "bất kể nhãn (chỉ cho qua giá quá khứ trong đoạn ĐÃ KIỂM có cả hai đầu trên trang đã ghi)")
        cum = _CUM_GIA.search(chu) or _CUM_GIA.search(kem)
        cac_so = so_tho(chu)
        if cum and cac_so and not tren(cac_so):
            loi.append(f"dòng {p['dong']}: «{cum.group(0)}» đi với số — QĐ-P13 cấm khoảng giá trị và giá mục tiêu ở mọi mục "
                       "(chỉ cho qua đoạn ĐÃ KIỂM có mọi con số trên trang đã ghi)")
    return loi


def kiem(ho_so_text: str, thu_muc=None) -> list:
    text = nfc(ho_so_text)
    dong = text.splitlines()
    loi = kiem_dinh_dang(text)                                   # 0. định dạng cho phép
    for i, d in enumerate(dong, 1):                              # 1. L-02
        m = _CAM.search(d)
        if m:
            loi.append(f"dòng {i}: cụm từ L-02 cấm: «{m.group(0)}»")
    muc = _cac_muc(dong)
    ten = [t for _, t, _ in muc]
    so_muc = [int(m.group(1)) for t in ten for m in [re.match(r"Mục (\d+)\.", t)] if m]
    if so_muc != list(range(1, 13)):                             # 2. khung
        loi.append(f"khung: cần đúng mười hai tiêu đề '## Mục 1.' tới '## Mục 12.' theo thứ tự; đang có {so_muc}")
    vi_tri = {x: next((n for n, t in enumerate(ten) if t.startswith(x)), None) for x in ("Một trang", "Mục 1.") + SAU_MUC_12}
    if None in vi_tri.values():
        loi.append("khung: thiếu tiêu đề " + ", ".join(f"'## {x}'" for x, v in vi_tri.items() if v is None))
    elif not (vi_tri["Một trang"] < vi_tri["Mục 1."] and vi_tri["Kết quả 15 điểm soi"] < vi_tri["Danh sách CHƯA BIẾT"]
              < vi_tri["Bảng nguồn"]):
        loi.append("khung: thứ tự phải là Một trang, Mục 1–12, Kết quả 15 điểm soi, Danh sách CHƯA BIẾT, Bảng nguồn")
    trung = [t for t in dict.fromkeys(ten) if ten.count(t) > 1]
    if trung:                                                    # sửa theo bản chấm L-09 vòng 2 của ADR-0021, lỗi chặn 4
        loi.append("khung: tiêu đề cấp hai xuất hiện hơn một lần: " + ", ".join(f"'## {t}'" for t in trung)
                   + "; mỗi tiêu đề của khung chỉ được có một lần")
    thu_tu = ("Trạng thái kiểm",) + tuple(t for t in TIEU_DE_CAP_HAI if t != "Trạng thái kiểm")
    biet = [t for t in dict.fromkeys(ten) if t in thu_tu]
    if biet != sorted(biet, key=thu_tu.index):                   # mục ngoài phạm vi đối chiếu không chen được vào giữa
        loi.append("khung: tiêu đề cấp hai không theo thứ tự của khung: Trạng thái kiểm, Cách đọc, Một trang, Mục 1 tới "
                   "Mục 12, Kết quả 15 điểm soi, Danh sách CHƯA BIẾT, Bảng nguồn, Lịch sử sửa, Phiếu máy")
    than = {}
    for _, t, b in muc:
        than.setdefault(t, b)                                    # tiêu đề lặp: xét thân của lần xuất hiện đầu tiên

    def than_cua(dau_ten):
        return next((b for t, b in than.items() if t.startswith(dau_ten)), "")
    if not ten or ten[0] != "Trạng thái kiểm":                  # 8. trạng thái kiểm (ADR-0021 QĐ-K3)
        loi.append("khung: tiêu đề cấp hai đầu tiên phải là '## Trạng thái kiểm' (ADR-0021 QĐ-K3)")
    else:
        dong_tt = [_gon(d) for d in than_cua("Trạng thái kiểm").splitlines() if re.match(r"\s*- ", d)]   # mục liệt kê thật
        sai_tt = [x for x in TRANG_THAI_KIEM if sum(1 for d in dong_tt if d.startswith("- " + x)) != 1]
        if sai_tt:                                               # vòng sửa 1 theo bản chấm L-09, lỗi chặn 5
            loi.append("Trạng thái kiểm: cần đúng một mục liệt kê riêng mở đầu bằng mỗi tên sau, thiếu hoặc trùng: "
                       + ", ".join(f"«- {x}»" for x in sai_tt))
    if _gon(than_cua("Mục 8.")) != MUC_8:                        # 3. mục 8 trống; khoảng giá ở mọi mục
        loi.append(f"Mục 8: thân mục chỉ được là đúng câu «{MUC_8}» (bỏ chữ đậm và khoảng trắng thừa); không thêm chữ, "
                   "số hay bảng nào (QĐ-P13, L-02 chưa sửa)")
    kho = KhoTrang(thu_muc) if thu_muc is not None else None
    loi.extend(kiem_khoang_gia(text, kho))
    loi.extend(kiem_cong_gia(text, kho))
    muc11 = than_cua("Mục 11.")                                  # 4. giả thuyết
    thieu = [x for x in ("H0", "H1", "H2") if x not in muc11]
    if thieu or not re.search(r"điều kiện", muc11, re.I) or not re.search(r"ngày xem lại", muc11, re.I):
        loi.append("Mục 11: cần đủ H0, H1, H2, 'điều kiện' làm giả thuyết sai và 'ngày xem lại'"
                   + (f"; thiếu {', '.join(thieu)}" if thieu else ""))
    diem = {int(m.group(1)) for m in re.finditer(r"^\|\s*\**(\d{1,2})\**\s*\|", than_cua("Kết quả 15 điểm soi"), re.M)}
    if not set(range(1, 16)) <= diem:                            # 5. điểm soi, CHƯA BIẾT
        loi.append(f"Kết quả 15 điểm soi: thiếu dòng {sorted(set(range(1, 16)) - diem)}")
    if not re.search(r"^\s*(?:[-*]|\d+\.)\s+\S", than_cua("Danh sách CHƯA BIẾT"), re.M):
        loi.append("Danh sách CHƯA BIẾT: cần ít nhất một dòng")
    dau = "\n".join(dong[:muc[0][0] - 1]) if muc else text       # 6. đầu hồ sơ
    if "không phải lời khuyên đầu tư" not in dau or "riêng tư" not in dau:
        loi.append("đầu hồ sơ: phải ghi 'không phải lời khuyên đầu tư' và 'riêng tư' trước tiêu đề đầu tiên")
    if kho is not None:                                          # 7. bảng nguồn
        bang = dict(re.findall(r"^\|\s*([A-Z]\d{1,2})\s*\|.*\|\s*([0-9a-f]{12})\s*\|\s*$", than_cua("Bảng nguồn"), re.M))
        for ma, dau_sha in sorted(bang.items()):
            if ma not in kho.nguon:
                loi.append(f"Bảng nguồn: mã {ma} không có trong nguon.csv")
            elif not kho.nguon[ma].get("sha256", "").startswith(dau_sha):
                loi.append(f"Bảng nguồn: sha256 của {ma} ghi {dau_sha}, nguon.csv là {kho.nguon[ma].get('sha256', '')[:12]}")
        da_dung = {ma for m in _TAG.finditer(text) if loai_nhan(m.group(0)) == "ĐÃ KIỂM" for ma in doc_dia_chi(m.group(0))}
        for ma in sorted(da_dung - set(bang)):
            loi.append(f"Bảng nguồn: mã {ma} được dùng trong nhãn nhưng không có dòng (hoặc thiếu sha256) trong bảng")
    return loi


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--thu-muc")
    ap.add_argument("--ho-so", required=True)
    a = ap.parse_args(argv)
    loi = kiem(pathlib.Path(a.ho_so).read_text(encoding="utf-8"), a.thu_muc)
    for d in loi:
        print("LỖI:", d)
    print("Luật và khung:", "ĐẠT" if not loi else f"CHƯA ĐẠT ({len(loi)} lỗi)")
    return 1 if loi else 0


if __name__ == "__main__":
    sys.exit(main())
