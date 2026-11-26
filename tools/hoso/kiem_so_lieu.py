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
  Dòng sửa : dòng gốc có `gia_tri` khác giá trị máy đọc từ chuoi_goc (kể cả khi chuoi_goc không đọc được thành một
             con số). Lời ghi chú không đủ: dòng sửa chỉ được nhận khi máy kiểm được cả hai điều (ADR-0020 QĐ-H4):
             (i)  gần chuỗi máy đọc: bỏ dấu chấm, dấu phẩy, khoảng trắng, ngoặc và dấu trừ ở cả chuoi_goc và gia_tri,
                  khoảng cách sửa (thêm, bớt, thay một ký tự) giữa hai dãy còn lại không quá KHOANG_CACH_TOI_DA;
             (ii) có đẳng thức chứng minh trong quan_he.csv: đẳng thức đúng; hai vế chỉ gồm tên khóa nối bằng cộng,
                  trừ và ngoặc (không hằng số, không nhân chia); mọi khóa là dòng gốc; hệ số gộp của khóa đang xét
                  khác 0; sai_so không quá SAI_SO_CHUNG_MINH đơn vị ở chữ số cuối của gia_tri; mọi khóa khác là dòng
                  gốc chép đúng máy đọc hoặc dòng sửa đã được chứng minh trước (lặp tới khi không thêm được; không
                  chứng minh vòng).
             Thiếu một trong hai: CHỜ CHỨNG MINH, là lỗi; đối chiếu trích dẫn không dùng dòng đó cho số ĐÃ KIỂM.
  Dòng tính: khoa,cong_thuc (chỉ + - * / trên các khóa đứng trước). `gia_tri` nếu điền phải khớp kết quả.
quan_he.csv, cột: ten,ve_trai,ve_phai,sai_so  (sai_so tính theo đơn vị của hai vế; số viết kiểu Việt Nam). Quan hệ có
  hằng số hay nhân chia (ví dụ cột phần trăm) vẫn được kiểm đúng sai, chỉ không tính là chứng minh cho dòng sửa.

Chạy: python tools/hoso/kiem_so_lieu.py --thu-muc <thư mục mã> [--soat-bang]
"""
import argparse
import ast
import pathlib
import re
import sys
from decimal import Decimal, InvalidOperation

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools.hoso.chung import KhoTrang, doc_csv, doc_so, nua_don_vi, tim_so, tinh_bieu_thuc  # noqa: E402

_KHOA = re.compile(r"^[a-z][a-z0-9_]*$")
KHOANG_CACH_TOI_DA = 2        # ký tự, giữa dãy chữ số của chuoi_goc và của gia_tri
SAI_SO_CHUNG_MINH = 2         # đơn vị ở chữ số cuối của gia_tri


def day_so(chuoi: str) -> str:
    """Bỏ dấu chấm, dấu phẩy, khoảng trắng, dấu ngoặc và dấu trừ."""
    return re.sub(r"[.,\s()\[\]\-−–]", "", chuoi or "")


def khoang_cach(a: str, b: str) -> int:
    """Khoảng cách sửa (thêm, bớt, thay một ký tự) giữa hai chuỗi."""
    truoc = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        hien = [i]
        for j, y in enumerate(b, 1):
            hien.append(min(truoc[j] + 1, hien[j - 1] + 1, truoc[j - 1] + (x != y)))
        truoc = hien
    return truoc[-1]


def he_so_cong_tru(bieu_thuc: str):
    """{khóa: hệ số} nếu biểu thức chỉ gồm tên khóa nối bằng cộng, trừ và ngoặc (cho phép dấu đứng trước); None nếu có
    hằng số, nhân, chia hay thứ khác."""
    try:
        cay = ast.parse((bieu_thuc or "").strip(), mode="eval").body
    except SyntaxError:
        return None
    hs = {}

    def di(nut, dau):
        if isinstance(nut, ast.Name):
            hs[nut.id] = hs.get(nut.id, 0) + dau
            return True
        if isinstance(nut, ast.BinOp) and isinstance(nut.op, (ast.Add, ast.Sub)):
            return di(nut.left, dau) and di(nut.right, dau if isinstance(nut.op, ast.Add) else -dau)
        if isinstance(nut, ast.UnaryOp) and isinstance(nut.op, (ast.UAdd, ast.USub)):
            return di(nut.operand, dau if isinstance(nut.op, ast.UAdd) else -dau)
        return False
    return hs if di(cay, 1) else None


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
        khoa, sua = d.get("khoa", ""), False
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
                        sua = True
                loai = "goc"
        except (ValueError, KeyError, InvalidOperation, ZeroDivisionError, SyntaxError) as e:
            kq["loi"].append(f"{noi}: {e}")
            continue
        kq["bien"][khoa] = gia_tri
        kq["dong"].append({"khoa": khoa, "loai": loai, "gia_tri": gia_tri, "nguon": d.get("nguon", ""),
                           "trang": int(d.get("trang") or 0), "chuoi_goc": re.sub(r"\s+", "", d.get("chuoi_goc", "")),
                           "ghi_chu": d.get("ghi_chu", ""), "sua": sua, "gia_tri_ghi": d.get("gia_tri", ""),
                           "chung_minh": "", "cong_thuc": d.get("cong_thuc", ""), "don_vi": d.get("don_vi", "")})
    _chung_minh(kho, kq)
    return kq


def cac_dong_goc(khoa: str, theo_khoa: dict) -> list:
    """Các dòng GỐC mà một khóa dựa vào, lần qua công thức của các dòng tính, theo thứ tự gặp, không trùng.
    theo_khoa: khóa → dòng (như doc_so_lieu trả trong 'dong'). Khóa gốc trả chính nó. (ADR-0021 QĐ-K2, QĐ-K4.)"""
    kq, da_qua = [], set()

    def di(k):
        if k in da_qua or k not in theo_khoa:
            return
        da_qua.add(k)
        d = theo_khoa[k]
        if d["loai"] == "goc":
            kq.append(d)
            return
        for nut in ast.walk(ast.parse(d.get("cong_thuc", "").strip() or "0", mode="eval")):
            if isinstance(nut, ast.Name):
                di(nut.id)
    di(khoa)
    return kq


def _chung_minh(kho: KhoTrang, kq: dict) -> None:
    """Xét từng dòng sửa theo hai điều (i), (ii) ở đầu tệp. Ghi tên đẳng thức chứng minh vào dòng['chung_minh']; dòng
    thiếu điều nào thì thêm lỗi CHỜ CHỨNG MINH. Ghi kq['da_sua'] cho mọi dòng sửa."""
    sua = {d["khoa"]: d for d in kq["dong"] if d["sua"]}
    if not sua:
        return
    goc = {d["khoa"] for d in kq["dong"] if d["loai"] == "goc"}
    goc_dung = {d["khoa"] for d in kq["dong"] if d["loai"] == "goc" and not d["sua"]}
    p = kho.thu_muc / "quan_he.csv"
    quan_he = []                                             # (tên, {khóa: hệ số của vế trái − vế phải}, sai_so)
    for r in (doc_csv(p) if p.is_file() else []):
        trai, phai = he_so_cong_tru(r.get("ve_trai", "")), he_so_cong_tru(r.get("ve_phai", ""))
        if trai is None or phai is None or not (set(trai) | set(phai)) <= goc:
            continue
        try:
            lech = abs(tinh_bieu_thuc(r["ve_trai"], kq["bien"]) - tinh_bieu_thuc(r["ve_phai"], kq["bien"]))
            sai_so = abs(doc_so(r.get("sai_so") or "0"))
        except (ValueError, KeyError, InvalidOperation, ZeroDivisionError, SyntaxError):
            continue
        if lech <= sai_so:
            hs = dict(trai)
            for k, v in phai.items():
                hs[k] = hs.get(k, 0) - v
            quan_he.append((r.get("ten", ""), hs, sai_so))
    kc = {k: khoang_cach(day_so(d["chuoi_goc"]), day_so(d["gia_tri_ghi"])) for k, d in sua.items()}
    gan = {k for k in sua if kc[k] <= KHOANG_CACH_TOI_DA}

    def chung_minh_duoc(k, da):
        don_vi = Decimal(1).scaleb(-tim_so(sua[k]["gia_tri_ghi"])[0].so_le)
        for ten, hs, sai_so in quan_he:
            if hs.get(k, 0) != 0 and sai_so <= SAI_SO_CHUNG_MINH * don_vi and all(
                    o in goc_dung or o in da for o in hs if o != k):
                return ten
        return ""
    da = {}
    doi = True
    while doi:                                               # lặp tới khi không thêm được dòng nào
        doi = False
        for k in sorted(gan - set(da)):
            ten = chung_minh_duoc(k, da)
            if ten:
                da[k], doi = ten, True
    for k, d in sua.items():
        d["chung_minh"] = da.get(k, "")
        dong = (f"{k}: máy đọc {d['chuoi_goc']}, ghế phân tích ghi {d['gia_tri_ghi']} ({d['nguon']} tr.{d['trang']}) — "
                f"{d['ghi_chu']}")
        if k in da:
            kq["da_sua"].append(f"{dong}; chứng minh bằng đẳng thức «{da[k]}»")
            continue
        kq["da_sua"].append(f"{dong}; CHỜ CHỨNG MINH")
        thieu = []
        if k not in gan:
            thieu.append(f"cách chuỗi máy đọc {kc[k]} ký tự (quá {KHOANG_CACH_TOI_DA})")
        if not chung_minh_duoc(k, da):
            thieu.append("chưa có đẳng thức chứng minh trong quan_he.csv (đúng; chỉ tên khóa nối bằng cộng, trừ, ngoặc; "
                         f"mọi khóa là dòng gốc; hệ số của {k} khác 0; sai_so không quá {SAI_SO_CHUNG_MINH} đơn vị ở chữ "
                         "số cuối; mọi khóa khác là dòng gốc chép đúng máy đọc hoặc dòng sửa đã chứng minh)")
        kq["loi"].append(f"so_lieu.csv, khóa {k!r}: CHỜ CHỨNG MINH — dòng sửa so với máy đọc chưa được nhận: "
                         + "; ".join(thieu))


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
