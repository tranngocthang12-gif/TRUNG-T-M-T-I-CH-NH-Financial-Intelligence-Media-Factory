"""B6 của quy trình hồ sơ mã: kiểm luật và khung của hồ sơ (ADR-0019 QĐ-P5, QĐ-P13; ADR-0020).

1. L-02: không cụm từ khuyến nghị nào ở bất kỳ dòng nào. Dùng đúng bộ mẫu của tools/laws_checks.py, thêm vài cụm
   riêng của hồ sơ mã. Kiểm cứng, không xét ngữ cảnh: câu phủ định có cụm cấm cũng bị bắt — đổi cách viết.
2. Khung: đủ mười hai mục theo thứ tự; có "Một trang", "Kết quả 15 điểm soi", "Danh sách CHƯA BIẾT", "Bảng nguồn".
3. Mục 8 để trống cho tới khi Owner sửa L-02 (QĐ-P13): sau khi bỏ chữ đậm và khoảng trắng thừa, thân mục phải đúng bằng
   câu cố định MUC_8. Thêm bất kỳ chữ, chữ số hay bảng nào là lỗi.
   Khoảng giá trị bị cấm ở MỌI mục, bất kể nhãn (QĐ-P13): hai số nối bằng gạch ngang hoặc "đến/tới" kèm đơn vị tiền
   (đồng, nghìn đồng, VND, đ; trong bảng, đơn vị ghi ở tiêu đề cột cũng tính), và các cụm "khoảng giá", "vùng giá",
   "mức giá", "giá mục tiêu", "giá trị nội tại", "giá trị một/mỗi cổ phiếu" đi với số. Chỉ cho qua khi phần chữ đó nằm
   trong đoạn ĐÃ KIỂM và mọi con số của nó có trên trang đã ghi (giá quá khứ có trong nguồn).
   Giới hạn: máy bắt theo mẫu. Khoảng viết thành hai ô "thấp | cao" không kèm cụm nào ở trên, hay hai câu rời mỗi câu
   một giá, thì máy không bắt; ghế phản biện khác hãng đọc.
   Cổng giá cổ phiếu (ADR-0020 QĐ-H3 dòng 5, sửa theo bản chấm L-09 vòng 2): quy tắc cho phép, không phải danh sách cấm.
   Đơn vị xét là từng phần chữ của kiem_trich_dan.cac_phan_chu (đoạn theo nhãn; hàng bảng kèm tiêu đề cột), ở mọi mục.
   Số thứ tự ở ô đầu hàng bảng và số đầu dòng liệt kê không tính là con số. Dòng tiêu đề '#', hàng tiêu đề bảng (chữ và
   đơn vị của nó cũng áp cho từng hàng dữ liệu) và ô mô tả trong bảng của mục "Bảng nguồn" xét theo cách nới, vì chúng
   không mang nhãn: bỏ qua năm đứng riêng; có dấu hiệu giá và có số khác năm, hoặc có số mang đơn vị giá, là lỗi. Phần chữ ở ngữ cảnh giá cổ phiếu khi
   có ít nhất một con số (như kiem_trich_dan.so_tho: cả số nguyên nhỏ, cả số trong backtick) và có một trong ba dấu hiệu:
     (a) con số mang đơn vị giá: đồng, nghìn/ngàn đồng, VND/VNĐ, đ; "nghìn", "ngàn", "k" đứng ngay sau số mà không có
         danh từ đơn vị nào theo sau; "/cp", "/cổ phiếu", "một/mỗi cổ phiếu", "một/mỗi cổ phần". Đơn vị ở tiêu đề cột
         áp cho ô số. Không tính tỷ đồng, triệu đồng, nghìn tỷ;
     (b) chữ "giá" đứng thành một từ, trừ các từ ghép trong GIA_KHONG_TINH, và trừ "giá trị" khi không theo sau bởi một
         cụm trong GIA_TRI_TINH;
     (c) hệ số định giá (P/E, P/B, P/S, EV/EBITDA) hoặc "vốn hóa", trừ các cụm trong VON_HOA_KHONG_TINH.
   Phần chữ ở ngữ cảnh giá phải đủ ba điều, thiếu một là lỗi: (1) nhãn phủ nó là ĐÃ KIỂM, địa chỉ hợp lệ; (2) mọi con số
   có trên trang đã ghi hoặc khớp một dòng gốc của sổ đúng nguồn đúng trang (dòng sửa phải đã chứng minh); riêng số phần
   trăm và số kèm "lần" được là số tính (mục 4 của phiếu vẫn lần chúng); (3) không có từ nào trong TU_TUONG_LAI.
   Giới hạn của cổng giá, nói thẳng: máy không bắt câu nêu giá tương lai mà không có chữ "giá", không đơn vị tiền, không
   hệ số định giá (ví dụ "Cổ phiếu MAU kỳ tới về 25,40"), và câu đặt số quá khứ có nguồn vào ý tương lai bằng từ ngoài
   TU_TUONG_LAI. Lớp bắt phần này là ghế phản biện khác hãng (B7), với câu hỏi bắt buộc ở templates/hoso/LENH_MAU.md.
4. Mục 11 có giả thuyết H0, H1, H2, điều kiện làm giả thuyết sai và ngày xem lại.
5. Bảng 15 điểm soi đủ mười lăm dòng. Danh sách CHƯA BIẾT có ít nhất một dòng.
6. Đầu hồ sơ ghi rõ đây không phải lời khuyên đầu tư và là bản riêng tư.
7. Bảng nguồn khớp nguon.csv: đủ mã, đúng 12 ký tự đầu sha256.

Chạy: python tools/hoso/kiem_luat.py --thu-muc <thư mục mã> --ho-so <tệp .md>
"""
import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools import laws_checks  # noqa: E402
from tools.hoso.chung import KhoTrang, nfc, tim_so  # noqa: E402
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
                "đáng giá", "upside", "downside", "target")
_BIEN_THE = {"hóa": "h(?:óa|oá)", "kỳ": "k[ỳì]", "tỷ": "t[ỷỉ]"}


def _mau(cum: str) -> str:
    """Biểu thức chính quy của một cụm từ: khoảng trắng co giãn, chấp nhận biến thể hóa/hoá, kỳ/kì, tỷ/tỉ, '/' có cách."""
    tu = []
    for w in cum.split():
        tu.append(_BIEN_THE.get(w.lower()) or r"\s*/\s*".join(re.escape(x) for x in w.split("/")))
    return r"\s+".join(tu)


def _cac_cum(cum) -> re.Pattern:
    return re.compile(r"(?<!\w)(?:" + "|".join(_mau(c) for c in sorted(cum, key=len, reverse=True)) + r")(?!\w)",
                      re.IGNORECASE)


_GIA = re.compile(r"(?<!\w)giá(?!\w)", re.IGNORECASE)
_GIA_KHONG_TINH = _cac_cum(GIA_KHONG_TINH)
_GIA_TRI_KHONG_TINH = re.compile(r"(?<!\w)giá\s+trị(?!\w)(?!\s+(?:của\s+)?(?:" + "|".join(_mau(c) for c in GIA_TRI_TINH)
                                 + r")(?!\w))", re.IGNORECASE)
_VON_HOA = _cac_cum(("vốn hóa",))
_VON_HOA_KHONG_TINH = _cac_cum(VON_HOA_KHONG_TINH)
_HE_SO = re.compile(r"(?<![\w/])(?:" + "|".join(_mau(c) for c in HE_SO_DINH_GIA) + r")(?![\w/])", re.IGNORECASE)
_TUONG_LAI = _cac_cum(TU_TUONG_LAI)
_SO_GIA = re.compile(rf"(?<![\w.,]){_SO_TIEN}\s*(?:{_DV_TIEN}|(?:ngh[ìi]n|ng[àa]n|k)(?!\s*\w)"
                     r"|/\s*(?:cp|c[ổo]\s*phi[ếe]u)(?!\w))", re.IGNORECASE)
_MOT_CO_PHIEU = re.compile(r"(?<!\w)(?:m[ộo]t|m[ỗo]i)\s+c[ổo]\s+(?:phi[ếe]u|ph[ầa]n)(?!\w)"
                           r"|/\s*(?:cp|c[ổo]\s*phi[ếe]u)(?!\w)", re.IGNORECASE)
_DAU_DONG = re.compile(r"^\s*(?:[-*]\s+)?\d+\.\s")
_LAN = re.compile(r"\)?\s*l[ầa]n(?!\w)", re.IGNORECASE)


def dau_hieu_gia(chu: str) -> list:
    """Các dấu hiệu ngữ cảnh giá cổ phiếu có trong một đoạn chữ (đã gắn đơn vị của tiêu đề cột nếu là hàng bảng)."""
    chu = nfc(chu).replace("`", "").replace("*", "")
    dh = []
    if _SO_GIA.search(chu) or _MOT_CO_PHIEU.search(chu):
        dh.append("(a) đơn vị giá")
    if _GIA.search(_GIA_TRI_KHONG_TINH.sub(" ", _GIA_KHONG_TINH.sub(" ", chu))):
        dh.append("(b) chữ «giá»")
    if _HE_SO.search(chu) or _VON_HOA.search(_VON_HOA_KHONG_TINH.sub(" ", chu)):
        dh.append("(c) hệ số định giá hoặc vốn hóa")
    return dh


def _la_nam(s) -> bool:
    return s.so_le == 0 and not s.pt and "." not in s.raw and len(s.raw) == 4 and 1900 <= int(s.raw) <= 2100


def _so_cua(chu: str, la_ti_le: bool = False) -> list:
    """[(So, là số tính được phép)] của một đoạn chữ: số phần trăm và số kèm 'lần' là số tính được phép."""
    sach = lam_sach(chu)
    return [(s, la_ti_le or s.pt or bool(_LAN.match(sach[s.vi_tri + len(s.raw):]))) for s in tim_so(sach)]


def kiem_cong_gia(text: str, kho=None) -> list:
    """Cổng giá cổ phiếu (xem đầu tệp). kho=None: không có trang để đối chiếu, nên không phần chữ nào ở ngữ cảnh giá qua."""
    so_lieu = doc_so_lieu(kho)["dong"] if kho is not None and (kho.thu_muc / "so_lieu.csv").is_file() else []
    loi = []
    for p in cac_phan_chu(text):
        bang_nguon = p["muc"].startswith("Bảng nguồn") and p["chu"].lstrip().startswith("|")
        if p["loai"] in ("tieu_de", "tieu_de_bang") or bang_nguon:   # không mang nhãn: xét nới, bỏ qua năm đứng riêng
            chu = p["chu"]
            o = [c.strip() for c in chu.strip().strip("|").split("|")]
            if bang_nguon and len(o) >= 4 and re.fullmatch(r"[A-Z]\d{1,2}", o[0]) and o[-2].isdigit() and re.fullmatch(
                    r"[0-9a-f]{12}", o[-1]):
                chu = " | ".join(o[1:-2])                        # hàng nguồn đúng định dạng: chỉ xét ô mô tả
            dh = dau_hieu_gia(chu)
            if dh and (_SO_GIA.search(nfc(chu).replace("`", "").replace("*", "")) or any(
                    not _la_nam(s) for s, _ in _so_cua(chu))):
                loi.append(f"dòng {p['dong']}: tiêu đề hay bảng nguồn ở ngữ cảnh giá cổ phiếu ({'; '.join(dh)}) — chỗ này "
                           "không mang nhãn ĐÃ KIỂM, nên không được nêu giá cổ phiếu, hệ số định giá hay vốn hóa kèm số "
                           "(ADR-0020 QĐ-H3)")
            continue
        if p["o"]:                                               # hàng bảng: số lấy từ các ô, chữ gồm cả tiêu đề cột
            o, td = list(p["o"]), list(p["tieu_de"])
            if o and re.fullmatch(r"\**\d{1,2}\**", o[0].strip()):
                o[0] = ""
            dv = [_don_vi_gia(x) for x in td]
            cac_so = [x for j, c in enumerate(o) for x in _so_cua(
                c, j < len(td) and bool(re.search(r"%|(?<!\w)l[ầa]n(?!\w)", td[j], re.IGNORECASE)))]
            chu = " | ".join(td) + " || " + " | ".join(
                c + (" " + dv[j] if j < len(dv) and dv[j] and re.search(r"\d", c) and not _DV_O.search(c) else "")
                for j, c in enumerate(o))
        else:
            chu = _DAU_DONG.sub(" ", p["chu"])
            cac_so = _so_cua(chu)
        if not cac_so:
            continue
        dh = dau_hieu_gia(chu)
        if not dh:
            continue
        ly_do = []
        dia_chi = doc_dia_chi(p["nhan"]) if loai_nhan(p["nhan"]) == "ĐÃ KIỂM" else {}
        if loai_nhan(p["nhan"]) != "ĐÃ KIỂM":
            ly_do.append(f"nhãn {p['nhan'] or '(không có)'} không phải ĐÃ KIỂM")
        elif kho is None or not dia_chi or any(m not in kho.nguon for m in dia_chi) or any(
                t not in kho.cac_trang(m) for m, tr in dia_chi.items() if tr is not None for t in tr):
            ly_do.append(f"địa chỉ của nhãn {p['nhan']} không hợp lệ hoặc không có trang để đối chiếu")
        else:
            thieu = [s.raw for s, tinh in cac_so if not tinh and not tren_trang(kho, s, dia_chi)
                     and not khop_dong_goc(so_lieu, s, dia_chi)]
            if thieu:
                ly_do.append("số không có trên trang đã ghi hay dòng gốc của sổ: " + ", ".join(thieu))
        tl = sorted({m.group(0).lower() for m in _TUONG_LAI.finditer(nfc(chu))})
        if tl:
            ly_do.append("có từ chỉ tương lai hay tín hiệu: " + ", ".join(f"«{x}»" for x in tl))
        if ly_do:
            loi.append(f"dòng {p['dong']}: ngữ cảnh giá cổ phiếu ({'; '.join(dh)}) — " + "; ".join(ly_do)
                       + ". Giá cổ phiếu, hệ số định giá và vốn hóa chỉ được nêu dưới dạng số quá khứ có nguồn trong đoạn "
                       "ĐÃ KIỂM, không kèm từ chỉ tương lai (ADR-0020 QĐ-H3)")
    return loi


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
    loi = []
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
    than = {t: b for _, t, b in muc}

    def than_cua(dau_ten):
        return next((b for t, b in than.items() if t.startswith(dau_ten)), "")
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
