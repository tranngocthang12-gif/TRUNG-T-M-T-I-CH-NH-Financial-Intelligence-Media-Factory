"""B4 của quy trình hồ sơ mã: kiểm sổ số liệu trước khi viết hồ sơ.

Ba phép kiểm, sinh ra từ bài học hồ sơ đầu tiên (máy nhận dạng chữ đọc sai một chữ số mà đối chiếu trích dẫn không bắt được):

1. Mỗi dòng gốc của so_lieu.csv có `chuoi_goc` xuất hiện đúng trên trang đã ghi.
2. Mỗi quan hệ trong quan_he.csv đúng: đẳng thức kế toán (doanh thu − giá vốn = lợi nhuận gộp) và hàng so sánh
   mà báo cáo tự in (kỳ này − kỳ trước = cột biến động).
3. Soát bảng: tự dò mọi trang, tìm hàng ba số a, b, c mà a − b lệch c đúng một chữ số — dấu hiệu máy đọc sai.

so_lieu.csv, cột: khoa,nguon,trang,chuoi_goc,gia_tri,don_vi,ghi_chu,cong_thuc
  Dòng gốc : khoa,nguon,trang,chuoi_goc. `gia_tri` để trống nghĩa là bằng chuoi_goc. Chỉ điền `gia_tri` khi ghế phân
             tích kết luận máy đọc sai; khi đó `ghi_chu` bắt buộc nói vì sao (phép trừ nào, đã xem ảnh trang nào).
             chuoi_goc chép không kèm dấu ngoặc thì giá trị dương, dấu do công thức ở quan_he.csv quyết định;
             chép kèm ngoặc đơn thì giá trị âm.
  Dòng tính: khoa,cong_thuc (chỉ + - * / trên các khóa đứng trước). `gia_tri` nếu điền phải khớp kết quả.
quan_he.csv, cột: ten,ve_trai,ve_phai,sai_so  (sai_so tính theo đơn vị của hai vế; số viết kiểu Việt Nam).

Chạy: python tools/hoso/kiem_so_lieu.py --thu-muc <thư mục mã> [--soat-bang]
"""
import argparse
import pathlib
import re
import sys
from decimal import Decimal, InvalidOperation

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools.hoso.chung import KhoTrang, doc_csv, doc_so, nua_don_vi, tim_so, tinh_bieu_thuc  # noqa: E402

_KHOA = re.compile(r"^[a-z][a-z0-9_]*$")


def _co_tren_trang(chuoi_goc: str, van_ban: str) -> bool:
    """chuoi_goc có đứng thành một con số trọn vẹn trên trang không (cho phép khoảng trắng lọt giữa các ký tự)."""
    gon = re.sub(r"\s+", "", chuoi_goc)
    if not gon:
        return False
    mau = r"(?<![\d.,])" + r"\s*".join(re.escape(c) for c in gon) + r"(?!\d)(?![.,]\d)"
    return re.search(mau, van_ban) is not None


def doc_so_lieu(kho: KhoTrang) -> dict:
    """Trả {'bien': khóa→giá trị, 'dong': các dòng đã đọc, 'loi': [...], 'da_sua': [...]}."""
    kq = {"bien": {}, "dong": [], "loi": [], "da_sua": []}
    p = kho.thu_muc / "so_lieu.csv"
    if not p.is_file():
        kq["loi"].append("thiếu so_lieu.csv")
        return kq
    for d in doc_csv(p):
        khoa = d.get("khoa", "")
        noi = f"so_lieu.csv, khóa {khoa!r}"
        if not _KHOA.match(khoa) or khoa in kq["bien"]:
            kq["loi"].append(f"{noi}: khóa phải là chữ thường, số, gạch dưới, bắt đầu bằng chữ, và không trùng")
            continue
        try:
            if d.get("cong_thuc"):
                if d.get("nguon") or d.get("trang") or d.get("chuoi_goc"):
                    kq["loi"].append(f"{noi}: dòng tính không được có nguon, trang, chuoi_goc")
                    continue
                gia_tri = tinh_bieu_thuc(d["cong_thuc"], kq["bien"])
                if d.get("gia_tri"):
                    ghi = tim_so(d["gia_tri"])
                    if len(ghi) != 1 or abs(abs(ghi[0].gia_tri) - abs(gia_tri)) > nua_don_vi(ghi[0].so_le):
                        kq["loi"].append(f"{noi}: gia_tri ghi {d['gia_tri']} nhưng công thức ra {gia_tri:f}")
                        continue
                loai = "tinh"
            else:
                ma, trang = d.get("nguon", ""), int(d.get("trang") or 0)
                if ma not in kho.nguon or trang not in kho.cac_trang(ma):
                    kq["loi"].append(f"{noi}: không có nguồn {ma!r} trang {trang}")
                    continue
                chuoi = d.get("chuoi_goc", "")
                if not _co_tren_trang(chuoi, kho.van_ban(ma, trang)):
                    kq["loi"].append(f"{noi}: không thấy {chuoi!r} trên {ma} tr.{trang}")
                    continue
                kieu = kho.kieu_so(ma)
                if kieu == "ca_hai":                             # tệp lẫn hai kiểu: đoán theo chính chuỗi
                    kieu = "en" if re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?|\d+\.\d{1,2}", chuoi.strip()) else "vn"
                goc = tim_so(chuoi, kieu)
                may_doc = goc[0].gia_tri if len(goc) == 1 and len(goc[0].raw) >= len(re.sub(r"[^\d.,]", "", chuoi)) else None
                if not d.get("gia_tri"):
                    if may_doc is None:
                        kq["loi"].append(f"{noi}: chuoi_goc không đọc được thành một con số — điền gia_tri và ghi_chu")
                        continue
                    gia_tri = may_doc
                else:
                    gia_tri = doc_so(d["gia_tri"])
                    if gia_tri != may_doc:
                        if not d.get("ghi_chu"):
                            kq["loi"].append(f"{noi}: gia_tri khác chuoi_goc mà không có ghi_chu giải thích")
                            continue
                        kq["da_sua"].append(f"{khoa}: máy đọc {chuoi}, ghế phân tích ghi {d['gia_tri']} "
                                            f"({ma} tr.{trang}) — {d['ghi_chu']}")
                loai = "goc"
        except (ValueError, KeyError, InvalidOperation, ZeroDivisionError, SyntaxError) as e:
            kq["loi"].append(f"{noi}: {e}")
            continue
        kq["bien"][khoa] = gia_tri
        kq["dong"].append({"khoa": khoa, "loai": loai, "gia_tri": gia_tri, "nguon": d.get("nguon", ""),
                           "trang": int(d.get("trang") or 0), "chuoi_goc": re.sub(r"\s+", "", d.get("chuoi_goc", "")),
                           "ghi_chu": d.get("ghi_chu", "")})
    return kq


def kiem_quan_he(kho: KhoTrang, bien: dict) -> dict:
    kq = {"dat": 0, "loi": [], "ten_dat": []}
    p = kho.thu_muc / "quan_he.csv"
    if not p.is_file():
        kq["loi"].append("thiếu quan_he.csv (cần ít nhất các đẳng thức kế toán của báo cáo mới nhất)")
        return kq
    for d in doc_csv(p):
        noi = f"quan_he.csv, «{d.get('ten', '')}»"
        try:
            trai, phai = tinh_bieu_thuc(d["ve_trai"], bien), tinh_bieu_thuc(d["ve_phai"], bien)
            sai_so = abs(doc_so(d.get("sai_so") or "0"))
        except (ValueError, KeyError, InvalidOperation, ZeroDivisionError, SyntaxError) as e:
            kq["loi"].append(f"{noi}: {e}")
            continue
        if abs(trai - phai) <= sai_so:
            kq["dat"] += 1
            kq["ten_dat"].append(d.get("ten", ""))
        else:
            kq["loi"].append(f"{noi}: vế trái {trai:f} khác vế phải {phai:f} (lệch {trai - phai:f}, cho phép {sai_so:f})")
    return kq


# ---------- soát bảng: tìm chữ số máy đọc sai ----------
def _sua_mot_chu_so(raw: str):
    """Mọi biến thể của raw khi đổi đúng một chữ số (không đổi chữ số đầu thành 0)."""
    for i, c in enumerate(raw):
        if c.isdigit():
            for m in "0123456789":
                if m != c and not (i == 0 and m == "0"):
                    yield raw[:i] + m + raw[i + 1:]


def _la_nam(s) -> bool:
    return "." not in s.raw and len(s.raw) == 4 and 1900 <= int(s.raw) <= 2100


def soat_dong(dong: str, kieu: str = "vn") -> list:
    """Trong một dòng văn bản, xét từng bộ ba số nguyên liền nhau (a, b, c) từ bốn chữ số trở lên, không tính năm.
    Trả danh sách ('khop', a, b, c, []) hoặc ('nghi', a, b, c, [gợi ý sửa]); bộ ba không liên quan thì bỏ qua.
    'khop' là a − b = c hoặc a + b = c (lệch tối đa 2 do làm tròn)."""
    so = [s for s in tim_so(dong, kieu)
          if s.so_le == 0 and not s.pt and len(s.raw.replace(".", "")) >= 4 and not _la_nam(s)]
    kq = []

    def khop(x, y, z):
        return abs(abs(x - y) - abs(z)) <= 2 or abs(abs(x + y) - abs(z)) <= 2

    def hieu(x, y, z):
        return abs(abs(x - y) - abs(z)) <= 2
    for i in range(len(so) - 2):
        a, b, c = so[i:i + 3]
        if khop(a.gia_tri, b.gia_tri, c.gia_tri):
            kq.append(("khop", a.raw, b.raw, c.raw, []))
            continue
        goi_y = []
        for ten, s in (("a", a), ("b", b), ("c", c)):
            for moi in _sua_mot_chu_so(s.raw):
                v = Decimal(moi.replace(".", "")).copy_sign(s.gia_tri)
                bo = {"a": (v, b.gia_tri, c.gia_tri), "b": (a.gia_tri, v, c.gia_tri),
                      "c": (a.gia_tri, b.gia_tri, v)}[ten]
                if hieu(*bo):
                    goi_y.append(f"{s.raw} → {moi}")
        if goi_y:
            kq.append(("nghi", a.raw, b.raw, c.raw, goi_y))
    return kq


def soat_bang(kho: KhoTrang) -> dict:
    """Dò mọi trang của mọi nguồn. Trả {'khop': số hàng khớp, 'nghi': [{'ma','trang','so': (a,b,c),'mo_ta'}]}."""
    kq = {"khop": 0, "nghi": []}
    for ma in sorted(kho.nguon):
        for trang in kho.cac_trang(ma):
            for dong in kho.van_ban(ma, trang).splitlines():
                for loai, a, b, c, goi_y in soat_dong(dong, "en" if kho.kieu_so(ma) == "en" else "vn"):
                    if loai == "khop":
                        kq["khop"] += 1
                    else:
                        kq["nghi"].append({"ma": ma, "trang": trang, "so": (a, b, c),
                                           "mo_ta": f"{ma} tr.{trang}: {a} − {b} không ra {c}; sửa một chữ số thì khớp: "
                                                    + " hoặc ".join(dict.fromkeys(goi_y))})
    return kq


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--thu-muc", required=True)
    ap.add_argument("--soat-bang", action="store_true", help="chỉ dò hàng so sánh nghi đọc sai rồi thoát")
    a = ap.parse_args(argv)
    kho = KhoTrang(a.thu_muc)
    if a.soat_bang:
        sb = soat_bang(kho)
        print(f"Hàng so sánh khớp phép trừ: {sb['khop']}. Hàng nghi máy đọc sai: {len(sb['nghi'])}.")
        for n in sb["nghi"]:
            print("NGHI:", n["mo_ta"])
        return 0
    sl = doc_so_lieu(kho)
    qh = kiem_quan_he(kho, sl["bien"])
    for dong in sl["loi"] + qh["loi"]:
        print("LỖI:", dong)
    for dong in sl["da_sua"]:
        print("ĐÃ SỬA SO VỚI MÁY ĐỌC:", dong)
    print(f"Sổ số liệu: {len(sl['dong'])} dòng đọc được, {len(sl['loi'])} lỗi. "
          f"Quan hệ: {qh['dat']} đạt, {len(qh['loi'])} lỗi.")
    return 1 if sl["loi"] or qh["loi"] else 0


if __name__ == "__main__":
    sys.exit(main())
