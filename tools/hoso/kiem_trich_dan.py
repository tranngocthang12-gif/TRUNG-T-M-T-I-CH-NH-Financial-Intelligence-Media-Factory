"""B6 của quy trình hồ sơ mã: lần từng con số trong hồ sơ về trang nguồn (ADR-0019 QĐ-P9 lớp 1, ADR-0020).

Hồ sơ là tệp Markdown. Mỗi đoạn kết bằng một nhãn trong ngoặc vuông:
    [ĐÃ KIỂM D1 tr.12]   [ĐÃ KIỂM D1 tr.8–11; D5 tr.3]   [SUY LUẬN, tính từ D1 tr.12]   [GIẢ ĐỊNH]   [CHƯA BIẾT]
Nhãn phủ phần chữ từ nhãn trước (hoặc đầu đoạn) tới nó. Nhãn đứng ở dòng ngay trước một bảng, hoặc đứng đầu dòng
ngay sau bảng, phủ cả bảng.

Mỗi con số trong đoạn ĐÃ KIỂM phải lần ra được theo một trong các đường:
    TRANG   có trên trang đã ghi (cho phép đổi đơn vị 10^3, 10^6, 10^9 và làm tròn tới số chữ số lẻ đã viết)
    SỔ      khớp một dòng của so_lieu.csv thuộc trang đã ghi (kể cả dòng ghế phân tích đã sửa lỗi máy đọc)
    TÍNH    ra được bằng một phép tính đơn giản trên các số khác cùng đoạn, cùng hàng hoặc cùng cột
    NGOẠI LỆ có trong ngoai_le.csv kèm lý do (in ra phiếu máy)
Không theo đường nào: KHÔNG LẦN RA — hồ sơ chưa đạt.

Đoạn SUY LUẬN, GIẢ ĐỊNH, CHƯA BIẾT: máy chỉ đếm; số nào trùng số đã lần ra thì ghi NHẮC LẠI.
Đoạn có số mà không có nhãn: CHƯA GẮN NHÃN — hồ sơ chưa đạt.

Giới hạn, nói thẳng: máy chỉ bắt được con số KHÔNG có trên trang và phép tính KHÔNG khớp. Máy không biết con số có
đúng ô hay không, và không kiểm lập luận. Việc đó thuộc ghế phản biện khác hãng và Owner (QĐ-P9 lớp 2, 3).

Chạy: python tools/hoso/kiem_trich_dan.py --thu-muc <thư mục mã> --ho-so <tệp .md>
"""
import argparse
import itertools
import pathlib
import re
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools.hoso.chung import NHAN, KhoTrang, doc_csv, khop_tap, nfc, nua_don_vi, tim_so  # noqa: E402
from tools.hoso.kiem_so_lieu import doc_so_lieu  # noqa: E402

_TAG = re.compile(r"\[[^\[\]]*(?:" + "|".join(NHAN) + r")[^\[\]]*\]")
_DIA_CHI = re.compile(r"(?<![\w.])([A-Z]\d{1,2})(?!\w)|tr\.\s*(\d+)(?:\s*[–-]\s*(\d+))?")
NGOAI_PHAM_VI = ("Cách đọc", "Bảng nguồn", "Lịch sử sửa", "Phiếu máy")

# Những thứ có chữ số nhưng không phải số liệu: bỏ trước khi tìm số.
_BO = [re.compile(m, re.I) for m in (
    r"`[^`]*`", r"https?://\S+",
    r"[A-Z]\d{1,2}\s+tr\.\s*\d+(?:\s*[–-]\s*\d+)?(?:\s*,\s*tr\.\s*\d+(?:\s*[–-]\s*\d+)?)*", r"\btr\.\s*\d+(?:\s*[–-]\s*\d+)?",
    r"\bngày\s+\d{1,2}\s+tháng\s+\d{1,2}(?:\s+năm\s+\d{4})?", r"\b\d{1,2}/\d{1,2}/\d{4}\b", r"\b\d{1,2}/\d{4}\b",
    r"\b\d{1,2}/\d{1,2}\b", r"\b\d{1,2}:\d{2}\b",
    r"\b[A-ZĐ]{1,4}-[A-Z]?\d+\b",
    r"\b(?:mục|điểm soi|điểm|bản|vòng|quý|tháng|đợt|lớp|bước|ngày|lần thứ)\s+\d{1,2}\b(?![.,/]\d)", r"\bnăm\s+\d{4}\b(?![.,]\d)",
    r"(?<![\d.,])\d{1,4}\s*(?:[–-]\s*\d{1,4}\s*)?(?:tháng|năm|quý|ngày|tuần|phiên|kỳ|trang|tệp|dòng|câu)\b",
)]


def so_can_kiem(text: str) -> list:
    """Các con số là số liệu trong một đoạn chữ. Đã bỏ: ngày tháng, số mục, mã tài liệu, năm, số đếm thời gian
    ("9 tháng", "66 ngày"), và số nguyên dưới 10 không kèm % (máy không kiểm các số này)."""
    for mau in _BO:
        text = mau.sub(" ", text)
    text = re.sub(r"^\s*(?:[-*]\s+)?\d+\.\s", " ", text)
    kq = []
    for s in tim_so(text):
        nguyen = s.raw.replace(".", "")
        if s.so_le == 0 and not s.pt:
            if s.tuyet_doi < 10 or (len(s.raw) == 4 and "." not in s.raw and 1900 <= int(nguyen) <= 2100):
                continue
        kq.append(s)
    return kq


def doc_dia_chi(nhan: str) -> dict:
    """'ĐÃ KIỂM D1 tr.8–11; D5 tr.3, tr.7; G2' → {'D1': {8,9,10,11}, 'D5': {3,7}, 'G2': None}. None = mọi trang."""
    kq, ma = {}, None
    for m in _DIA_CHI.finditer(nhan):
        if m.group(1):
            ma = m.group(1)
            kq.setdefault(ma, None)
        elif ma is not None:
            dau, cuoi = int(m.group(2)), int(m.group(3) or m.group(2))
            kq[ma] = (kq[ma] or set()) | set(range(dau, cuoi + 1))
    return kq


def loai_nhan(nhan: str) -> str:
    vi_tri = [(nhan.find(n), n) for n in NHAN if n in nhan]
    return min(vi_tri)[1] if vi_tri else ""


# ---------- tách hồ sơ thành đoạn ----------
def tach_doan(text: str) -> list:
    """Trả danh sách, mỗi phần tử là MỘT con số kèm ngữ cảnh:
    {'dong': số dòng, 'chu': chữ của đoạn, 'nhan': nhãn đầy đủ hoặc '', 'so': So, 'hang': [...], 'cot': [...]}.
    'hang' là chỉ số của các con số khác cùng đoạn (hoặc cùng hàng của bảng); 'cot' là các con số cùng cột của bảng."""
    dong = nfc(text).splitlines()
    trong_pham_vi, khoi, hien = False, [], None
    for i, d in enumerate(dong, 1):                              # gom dòng thành khối: bảng, hoặc đoạn/mục liệt kê
        if d.startswith("## "):
            ten = d[3:].strip()
            trong_pham_vi = not any(ten.startswith(x) for x in NGOAI_PHAM_VI)
            hien = None
            continue
        if not trong_pham_vi or d.startswith("#") or not d.strip() or set(d.strip()) <= set("-*_"):
            hien = None
            continue
        la_bang = d.lstrip().startswith("|")
        la_muc = re.match(r"\s*(?:[-*]|\d+\.)\s", d) is not None
        if hien and hien["bang"] == la_bang and not (la_muc and not la_bang):
            hien["dong_chu"].append(d)
        else:
            hien = {"bang": la_bang, "dong": i, "dong_chu": [d]}
            khoi.append(hien)
    for j, k in enumerate(khoi):                                 # nhãn của bảng: dòng ngay sau, hoặc dòng ngay trước
        if not k["bang"]:
            continue
        k["nhan"] = ""
        if j + 1 < len(khoi) and not khoi[j + 1]["bang"]:
            m = _TAG.match(khoi[j + 1]["dong_chu"][0].lstrip())
            if m:
                k["nhan"] = m.group(0)
                khoi[j + 1]["bo_dau"] = len(khoi[j + 1]["dong_chu"][0]) - len(khoi[j + 1]["dong_chu"][0].lstrip()) + m.end()
        if not k["nhan"] and j and not khoi[j - 1]["bang"]:
            truoc = " ".join(khoi[j - 1]["dong_chu"]).rstrip()
            cac = list(_TAG.finditer(truoc))
            if cac and cac[-1].end() == len(truoc):
                k["nhan"] = cac[-1].group(0)
    doan = []
    for k in khoi:
        if k["bang"]:
            hang = [[c.strip() for c in d.strip().strip("|").split("|")] for d in k["dong_chu"]]
            hang = [(k["dong"] + n, h) for n, h in enumerate(hang) if not all(set(c) <= set("-: ") for c in h)]
            o_bang = []                                          # (hàng, cột, chỉ số trong doan); hàng đầu là tiêu đề cột
            for n, (so_dong, h) in enumerate(hang[1:]):
                rieng = _TAG.search(" | ".join(h))               # nhãn nằm trong một ô thì phủ riêng hàng đó
                for c, o in enumerate(h):
                    if c == 0 and re.fullmatch(r"\**\d{1,2}\**", o):  # cột đầu chỉ là số thứ tự
                        continue
                    for s in so_can_kiem(_TAG.sub(" ", o)):
                        o_bang.append((n, c, len(doan)))
                        doan.append({"dong": so_dong, "chu": " | ".join(h), "so": s,
                                     "nhan": rieng.group(0) if rieng else k["nhan"]})
            for n, c, i in o_bang:
                doan[i]["hang"] = [j for n2, _, j in o_bang if n2 == n and j != i]
                doan[i]["cot"] = [j for n2, c2, j in o_bang if c2 == c and n2 != n]
            continue
        chu = " ".join(k["dong_chu"])[k.get("bo_dau", 0):]
        dau = 0
        for m in list(_TAG.finditer(chu)) + [None]:
            phan = chu[dau:m.start()] if m else chu[dau:]
            cung = list(range(len(doan), len(doan) + len(so_can_kiem(phan))))
            for i, s in zip(cung, so_can_kiem(phan)):
                doan.append({"dong": k["dong"], "chu": phan.strip(), "nhan": m.group(0) if m else "", "so": s,
                             "hang": [j for j in cung if j != i], "cot": []})
            if m:
                dau = m.end()
    return doan


# ---------- phép tính đơn giản ----------
def _khoang(s):
    e, v = float(nua_don_vi(s.so_le)), float(s.tuyet_doi)
    return (max(v - e, 0.0), v + e)


_HAI = {"a − b": lambda a, b: abs(a - b), "a + b": lambda a, b: a + b, "a ÷ b": lambda a, b: a / b,
        "a ÷ b × 100": lambda a, b: a / b * 100, "(a ÷ b − 1) × 100": lambda a, b: abs(a / b - 1) * 100,
        "a × b ÷ 100": lambda a, b: a * b / 100}
_BA = {"a + b + c": lambda a, b, c: a + b + c, "a + b − c": lambda a, b, c: abs(a + b - c),
       "a − b − c": lambda a, b, c: abs(a - b - c)}
_COT = ("a − b", "a + b", "(a ÷ b − 1) × 100", "a ÷ b × 100")


def _ra_duoc(d, ham, bo) -> bool:
    thap, cao = _khoang(d)
    try:
        gia = [ham(*goc) for goc in itertools.product(*[_khoang(x) for x in bo])]
    except ZeroDivisionError:
        return False
    return min(gia) <= cao and max(gia) >= thap


def tinh_duoc(d, hang: list, cot: list = ()) -> str:
    """Số d có ra được từ phép tính đơn giản trên các số cùng hàng (hai hoặc ba số) hay cùng cột (hai số, hoặc tổng cột)?"""
    for ten, ham in _HAI.items():
        for a, b in itertools.permutations(hang, 2):
            if _ra_duoc(d, ham, (a, b)):
                return f"{ten} với a={a.raw}, b={b.raw}"
    if len(hang) <= 12:
        for ten, ham in _BA.items():
            for a, b, c in itertools.permutations(hang, 3):
                if _ra_duoc(d, ham, (a, b, c)):
                    return f"{ten} với a={a.raw}, b={b.raw}, c={c.raw}"
    for ten in _COT:
        for a, b in itertools.permutations(cot, 2):
            if _ra_duoc(d, _HAI[ten], (a, b)):
                return f"cùng cột: {ten} với a={a.raw}, b={b.raw}"
    if 2 <= len(cot) <= 40:
        tong = abs(sum(float(x.gia_tri) for x in cot))
        sai_so = sum(float(nua_don_vi(x.so_le)) for x in cot) + float(nua_don_vi(d.so_le))
        if abs(tong - float(d.tuyet_doi)) <= sai_so:
            return "cùng cột: tổng các ô còn lại"
    return ""


# ---------- kiểm ----------
def kiem(thu_muc, ho_so_text: str) -> dict:
    kho = KhoTrang(thu_muc)
    so_lieu = doc_so_lieu(kho)["dong"] if (kho.thu_muc / "so_lieu.csv").is_file() else []
    p = kho.thu_muc / "ngoai_le.csv"
    ngoai_le = doc_csv(p) if p.is_file() else []
    da_dung = set()
    doan = tach_doan(ho_so_text)
    kq = {"dem": Counter(), "loi": [], "ngoai_le": [], "khong_kiem": [], "so_con_so": len(doan)}

    def trong_so(s, dia_chi=None) -> bool:
        for d in so_lieu:
            if dia_chi is not None and d["loai"] == "goc":
                if d["nguon"] not in dia_chi or (dia_chi[d["nguon"]] is not None and d["trang"] not in dia_chi[d["nguon"]]):
                    continue
            if khop_tap(s.gia_tri, s.so_le, [abs(d["gia_tri"])]):
                return True
        return False

    def la_ngoai_le(s, chu) -> bool:
        for n, e in enumerate(ngoai_le):
            if e.get("so") == s.raw and e.get("ngu_canh") and e["ngu_canh"] in chu and e.get("ly_do"):
                if n not in da_dung:
                    da_dung.add(n)
                    kq["ngoai_le"].append(f"{s.raw} («{e['ngu_canh']}»): {e['ly_do']}")
                return True
        return False

    loai = [""] * len(doan)
    cho = []                                                     # con số ĐÃ KIỂM chưa neo được vào trang hay sổ
    for i, d in enumerate(doan):                                 # lượt 1: neo con số ĐÃ KIỂM vào trang hoặc sổ
        if loai_nhan(d["nhan"]) != "ĐÃ KIỂM":
            continue
        s = d["so"]
        dia_chi = doc_dia_chi(d["nhan"])
        la = [ma for ma in dia_chi if ma not in kho.nguon]
        if not dia_chi or la:
            loai[i] = "ĐỊA CHỈ SAI"
            kq["loi"].append(f"dòng {d['dong']}: {s.raw} — nhãn {d['nhan']} " + (
                "thiếu mã nguồn" if not dia_chi else f"dùng mã nguồn không có trong nguon.csv: {', '.join(la)}"))
        elif any(khop_tap(s.gia_tri, s.so_le, kho.tap_so(ma, t)) for ma, trang in dia_chi.items()
                 for t in (trang if trang is not None else kho.cac_trang(ma))):
            loai[i] = "TRANG"
        elif trong_so(s, dia_chi):
            loai[i] = "SỔ"
        else:
            cho.append(i)
    doi = True
    while doi:                                                   # lượt 2: tính từ các số ĐÃ lần ra (không cho tính vòng)
        doi = False
        for i in list(cho):
            d = doan[i]
            xong = ("TRANG", "SỔ", "TÍNH")
            if tinh_duoc(d["so"], [doan[j]["so"] for j in d["hang"] if loai[j] in xong],
                         [doan[j]["so"] for j in d["cot"] if loai[j] in xong]):
                loai[i], doi = "TÍNH", True
                cho.remove(i)
    for i in cho:
        d, s = doan[i], doan[i]["so"]
        if la_ngoai_le(s, d["chu"]):
            loai[i] = "NGOẠI LỆ"
        else:
            loai[i] = "KHÔNG LẦN RA"
            kq["loi"].append(f"dòng {d['dong']}: {s.raw}{'%' if s.pt else ''} — không có trên trang đã ghi, không có trong sổ, "
                             f"không tính ra được từ các số đã lần ra cùng đoạn {d['nhan']}")
    da_lan_ra = {(doan[i]["so"].tuyet_doi, doan[i]["so"].so_le) for i, x in enumerate(loai)
                 if x in ("TRANG", "SỔ", "TÍNH", "NGOẠI LỆ")}
    for i, d in enumerate(doan):                                 # lượt 3: đoạn không phải ĐÃ KIỂM
        if loai[i]:
            continue
        s, loai_n = d["so"], loai_nhan(d["nhan"])
        if (s.tuyet_doi, s.so_le) in da_lan_ra:
            loai[i] = "NHẮC LẠI"
        elif trong_so(s):
            loai[i] = "SỔ"
        elif loai_n:
            loai[i] = "MÁY KHÔNG KIỂM"
            kq["khong_kiem"].append(f"dòng {d['dong']}: {s.raw}{'%' if s.pt else ''} [{loai_n}]")
        elif la_ngoai_le(s, d["chu"]):
            loai[i] = "NGOẠI LỆ"
        else:
            loai[i] = "CHƯA GẮN NHÃN"
            kq["loi"].append(f"dòng {d['dong']}: {s.raw}{'%' if s.pt else ''} — đoạn có số mà không có nhãn")
    kq["dem"].update(loai)
    kq["trang_da_dung"] = sorted({(ma, t) for d in doan if loai_nhan(d["nhan"]) == "ĐÃ KIỂM"
                                  for ma, trang in doc_dia_chi(d["nhan"]).items() if ma in kho.nguon
                                  for t in (trang if trang is not None else kho.cac_trang(ma))})
    for n, e in enumerate(ngoai_le):
        if n not in da_dung:
            kq["loi"].append(f"ngoai_le.csv: dòng cho số {e.get('so', '')!r} không còn dùng tới (hoặc thiếu ngu_canh, ly_do) — xóa đi")
    return kq


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--thu-muc", required=True)
    ap.add_argument("--ho-so", required=True)
    ap.add_argument("--chi-tiet", action="store_true", help="in cả các số máy không kiểm")
    a = ap.parse_args(argv)
    kq = kiem(a.thu_muc, pathlib.Path(a.ho_so).read_text(encoding="utf-8"))
    for dong in kq["loi"]:
        print("LỖI:", dong)
    for dong in kq["ngoai_le"]:
        print("NGOẠI LỆ:", dong)
    if a.chi_tiet:
        for dong in kq["khong_kiem"]:
            print("MÁY KHÔNG KIỂM:", dong)
    print("Con số theo đường lần ra:", ", ".join(f"{k} {v}" for k, v in sorted(kq["dem"].items())))
    return 1 if kq["loi"] else 0


if __name__ == "__main__":
    sys.exit(main())
