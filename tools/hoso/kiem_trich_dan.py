"""B6 của quy trình hồ sơ mã: lần từng con số trong hồ sơ về trang nguồn (ADR-0019 QĐ-P9 lớp 1, ADR-0020).

Hồ sơ là tệp Markdown. Mỗi đoạn kết bằng một nhãn trong ngoặc vuông:
    [ĐÃ KIỂM D1 tr.12]   [ĐÃ KIỂM D1 tr.8–11; D5 tr.3]   [SUY LUẬN, tính từ D1 tr.12]   [GIẢ ĐỊNH]   [CHƯA BIẾT]
Nhãn phủ phần chữ từ nhãn trước (hoặc đầu đoạn) tới nó. Nhãn đứng ở dòng ngay trước một bảng, hoặc đứng đầu dòng
ngay sau bảng, phủ cả bảng. Giữa nhãn đứng trước và bảng chỉ được có dòng trống: nhãn không phủ bảng qua một tiêu đề.
Ô đầu hàng bảng chỉ là số thứ tự (không phải số liệu) khi tiêu đề cột đầu, bỏ dấu đậm và khoảng trắng thừa, là một trong
TIEU_DE_SO_THU_TU (#, STT, TT, Số TT, Số thứ tự) và các ô của cột đó đúng là 1, 2, …, n theo thứ tự. Thiếu một trong hai
điều thì ô đầu là số liệu như mọi ô khác.

Mỗi trang ghi trong nhãn ĐÃ KIỂM phải có trong thư mục trang/ của nguồn đó; không có thì ĐỊA CHỈ SAI.
Mỗi con số trong đoạn ĐÃ KIỂM phải lần ra được theo một trong các đường:
    TRANG   có trên trang đã ghi (cho phép đổi đơn vị 10^3, 10^6, 10^9 và làm tròn tới số chữ số lẻ đã viết)
    SỔ      khớp một dòng GỐC của so_lieu.csv có đúng nguồn và đúng trang ghi trong nhãn. Dòng sửa (ghế phân tích ghi
            khác máy đọc) chỉ được dùng khi đã được chứng minh (kiem_so_lieu: gần chuỗi máy đọc và có đẳng thức cộng
            trừ trong quan_he.csv). Dòng tính không hợp thức hóa được một địa chỉ trang: số tính đi dưới nhãn
            [SUY LUẬN, sổ số liệu: <khóa>].
    TÍNH    ra được bằng một phép tính đơn giản trên các số đã lần ra khác cùng đoạn, cùng hàng hoặc cùng cột
Không theo đường nào: KHÔNG LẦN RA — hồ sơ chưa đạt. Không có đường ngoại lệ (ADR-0020, sửa theo bản chấm L-09 vòng 2):
con số máy không lần ra thì không mang nhãn ĐÃ KIỂM. Thư mục mã còn tệp ngoai_le.csv thì báo lỗi: tệp không còn dùng.
so_can_kiem bỏ qua số nguyên dưới 10, năm và số trong dấu backtick. Trong đoạn ĐÃ KIỂM, các số đó vẫn phải có trên trang
đã ghi hoặc là dòng gốc của sổ (lượt 4); không thì KHÔNG LẦN RA. Ngày tháng, số mục, mã tài liệu, địa chỉ trang và số
đếm thời gian ("9 tháng", "66 ngày") không được coi là con số và không bị đối chiếu.

Dấu: số viết có dấu âm rõ ràng (−, -, hoặc trong ngoặc đơn) chỉ khớp số âm trên trang hay trong sổ, và không đi đường
TÍNH bằng phép cộng, nhân, chia. Số viết không dấu khớp theo trị tuyệt đối, vì văn xuôi thường bỏ dấu ("lỗ 1.193 tỷ").

Đoạn SUY LUẬN (ADR-0021 QĐ-K1): nhãn gọi tên khóa sổ sau «sổ số liệu:», cách nhau bằng dấu phẩy, tới dấu «;» hoặc hết
nhãn; chữ sau dấu «;» là ghi chú, máy không đọc. «a05 tới a09» là dãy khóa cùng phần chữ, phần số tăng từng một, giữ số
chữ số. Khóa không có trong sổ, hay phần không phải tên khóa trước dấu «;», là lỗi. Mỗi con số trong đoạn phải:
    KHÓA      khớp giá trị của một khóa nhãn gọi tên (làm tròn tới số chữ số đã viết, đổi đơn vị 10^3, 10^6, 10^9); hoặc
    HẰNG SỐ   khớp một hằng số viết trong công thức của một khóa nhãn gọi tên (ví dụ 49 trong «a * 49 / 100»); hoặc
    NHẮC LẠI  khớp một con số ĐÃ KIỂM đã lần ra trong hồ sơ.
Không theo đường nào: KHÔNG GẮN KHÓA — hồ sơ chưa đạt. Đoạn SUY LUẬN không gọi khóa nào thì mọi con số phải là NHẮC LẠI
(QĐ-H4 của ADR-0020: không tính nhẩm). Chiều ngược: phần chữ nhãn phủ (cả bảng, khi nhãn phủ bảng) có ít nhất một chữ số
thì mỗi khóa nhãn gọi tên phải khớp ít nhất một con số trong đó; khóa chỉ dùng làm căn cứ mà không in số thì đặt sau dấu «;».
Ở chiều ngược, máy đọc cả số nhỏ, năm và số đếm thời gian («66 ngày»). Câu dẫn hay câu định tính không có chữ số nào thì
chiều ngược không xét.
Đoạn GIẢ ĐỊNH, CHƯA BIẾT: máy chỉ đếm; số nào trùng số đã lần ra thì ghi NHẮC LẠI.
Đoạn có số mà không có nhãn: CHƯA GẮN NHÃN — hồ sơ chưa đạt, kể cả khi số đó trùng số đã lần ra hay trùng sổ.

Giới hạn, nói thẳng: máy chỉ bắt được con số KHÔNG có trên trang, phép tính KHÔNG khớp, và số SUY LUẬN không khớp khóa
nhãn gọi tên. Máy không biết con số có đúng ô hay không, công thức có đúng nghĩa không, và không kiểm lập luận. Việc đó
thuộc ghế phản biện khác hãng (có bảng định nghĩa, ADR-0021 QĐ-K2) và Owner (QĐ-P9 lớp 2, 3).

Chạy: python tools/hoso/kiem_trich_dan.py --thu-muc <thư mục mã> --ho-so <tệp .md>
"""
import argparse
import ast
import itertools
import pathlib
import re
import sys
from collections import Counter
from decimal import Decimal

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools.hoso.chung import NHAN, KhoTrang, khop_co_dau, nfc, nua_don_vi, tim_so  # noqa: E402
from tools.hoso.kiem_so_lieu import doc_so_lieu  # noqa: E402

_TAG = re.compile(r"\[[^\[\]]*(?:" + "|".join(NHAN) + r")[^\[\]]*\]")
_DIA_CHI = re.compile(r"(?<![\w.])([A-Z]\d{1,2})(?!\w)|tr\.\s*(\d+)(?:\s*[–-]\s*(\d+))?")
NGOAI_PHAM_VI = ("Trạng thái kiểm", "Cách đọc", "Bảng nguồn", "Lịch sử sửa", "Phiếu máy")
_KHOA_NHAN = re.compile(r"sổ số liệu\s*:\s*([^;\]]*)")
_KHOA_TEN = re.compile(r"[a-z][a-z0-9_]*")
_KHOA_DAY = re.compile(r"([a-z][a-z0-9_]*?)(\d+)\s+tới\s+([a-z][a-z0-9_]*?)(\d+)")
TIEU_DE_SO_THU_TU = ("#", "STT", "TT", "Số TT", "Số thứ tự")

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


_DAU_DONG = re.compile(r"^\s*(?:[-*]\s+)?\d+\.\s")


def lam_sach(text: str) -> str:
    """Bỏ dấu backtick, ngày tháng, số mục, mã tài liệu, địa chỉ trang và số đếm thời gian (thay bằng khoảng trắng)."""
    text = text.replace("`", " ")
    for mau in _BO:
        text = mau.sub(" ", text)
    return text


def so_tho(text: str) -> list:
    """Mọi con số trong một đoạn chữ, chỉ bỏ ngày tháng, số mục, mã tài liệu, địa chỉ trang và số đếm thời gian. KHÔNG bỏ
    số nguyên nhỏ, năm hay số trong dấu backtick. Dùng cho phép kiểm phải chặt hơn đối chiếu trích dẫn (khoảng giá)."""
    return tim_so(lam_sach(text))


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


def doc_khoa(nhan: str, trong_so) -> tuple:
    """Khóa sổ mà nhãn gọi tên (ADR-0021 QĐ-K1): phần sau «sổ số liệu:» tới dấu «;» hoặc hết nhãn, cách nhau bằng dấu
    phẩy. «a05 tới a09» là dãy khóa cùng phần chữ, phần số tăng từng một, giữ số chữ số. trong_so: tập khóa của sổ.
    Trả (danh sách khóa theo thứ tự, không trùng; danh sách lỗi)."""
    m = _KHOA_NHAN.search(nhan)
    if not m:
        return [], []
    khoa, loi = [], []
    for phan in m.group(1).split(","):
        phan = " ".join(phan.split()).rstrip(".")
        day = _KHOA_DAY.fullmatch(phan)
        if day:
            p1, s1, p2, s2 = day.groups()
            if p1 != p2 or len(s1) != len(s2) or int(s1) > int(s2):
                loi.append(f"dãy «{phan}» không hợp lệ: hai đầu phải cùng phần chữ, cùng số chữ số, đầu không lớn hơn cuối")
                continue
            ds = [f"{p1}{n:0{len(s1)}d}" for n in range(int(s1), int(s2) + 1)]
        elif _KHOA_TEN.fullmatch(phan):
            ds = [phan]
        else:
            loi.append(f"«{phan}» không phải tên khóa sổ (chữ thường, số, gạch dưới); ghi chú đặt sau dấu «;»")
            continue
        for k in ds:
            if k not in trong_so:
                loi.append(f"khóa {k} không có trong sổ số liệu")
            elif k not in khoa:
                khoa.append(k)
    return khoa, loi


def hang_so_cong_thuc(cong_thuc: str) -> list:
    """Các hằng số viết trong công thức của một dòng tính (ví dụ 49 và 100 trong «a * 49 / 100»)."""
    try:
        cay = ast.parse(cong_thuc.strip(), mode="eval") if cong_thuc and cong_thuc.strip() else None
    except SyntaxError:
        return []
    return [Decimal(str(n.value)) for n in ast.walk(cay) if isinstance(n, ast.Constant)
            and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)] if cay else []


def _gon_so(v) -> str:
    """Giá trị của một khóa sổ, viết gọn để in lỗi."""
    return f"{v:.0f}" if abs(v) >= 1000 else f"{v:.4f}".rstrip("0").rstrip(".")


def so_hien(text: str) -> list:
    """Mọi con số hiện trong một phần chữ, kể cả số nhỏ, năm và số đếm thời gian («66 ngày»); chỉ bỏ địa chỉ trang, mã tài
    liệu, ngày tháng, số mục, URL và mã trong backtick. Dùng cho chiều ngược của QĐ-K1: khóa nhãn gọi tên có hiện số không."""
    for mau in _BO[:-1]:                                         # mẫu cuối của _BO là số đếm thời gian: giữ lại
        text = mau.sub(" ", text)
    return tim_so(text)


# ---------- tách hồ sơ thành đoạn ----------
def _gom_khoi(dong: list) -> list:
    """Gom các dòng trong phạm vi kiểm thành khối: bảng, hoặc đoạn/mục liệt kê; gắn nhãn cho bảng.
    Mỗi khối: {'bang', 'dong' (số dòng đầu), 'dong_chu', 'nhan' (bảng), 'bo_dau' (đoạn mở đầu bằng nhãn của bảng trước)}."""
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
        giua = dong[khoi[j - 1]["dong"] - 1 + len(khoi[j - 1]["dong_chu"]):k["dong"] - 1] if j else []
        if not k["nhan"] and j and not khoi[j - 1]["bang"] and not any(d.strip() for d in giua):   # không qua tiêu đề
            truoc = " ".join(khoi[j - 1]["dong_chu"]).rstrip()
            cac = list(_TAG.finditer(truoc))
            if cac and cac[-1].end() == len(truoc):
                k["nhan"] = cac[-1].group(0)
    return khoi


def _hang_bang(k: dict) -> list:
    """[(số dòng, ô)] của một khối bảng, bỏ dòng kẻ; phần tử đầu là hàng tiêu đề cột."""
    hang = [[c.strip() for c in d.strip().strip("|").split("|")] for d in k["dong_chu"]]
    return [(k["dong"] + n, h) for n, h in enumerate(hang) if not all(set(c) <= set("-: ") for c in h)]


def cot_so_thu_tu(hang: list) -> bool:
    """Cột đầu của bảng (hang như _hang_bang trả về) là số thứ tự thật: tiêu đề là một trong TIEU_DE_SO_THU_TU và các ô của
    cột đó đúng là 1, 2, …, n theo thứ tự."""
    if len(hang) < 2 or not hang[0][1]:
        return False
    tieu_de = " ".join(hang[0][1][0].replace("*", "").split()).lower()
    if tieu_de not in {x.lower() for x in TIEU_DE_SO_THU_TU}:
        return False
    return [(h[0] if h else "").replace("*", "").strip() for _, h in hang[1:]] == [str(i) for i in range(1, len(hang))]


def tach_doan(text: str) -> list:
    """Trả danh sách, mỗi phần tử là MỘT con số kèm ngữ cảnh:
    {'dong': số dòng, 'chu': chữ của đoạn, 'nhan': nhãn đầy đủ hoặc '', 'so': So, 'hang': [...], 'cot': [...]}.
    'hang' là chỉ số của các con số khác cùng đoạn (hoặc cùng hàng của bảng); 'cot' là các con số cùng cột của bảng."""
    doan = []
    for k in _gom_khoi(nfc(text).splitlines()):
        if k["bang"]:
            hang = _hang_bang(k)
            stt = cot_so_thu_tu(hang)
            o_bang = []                                          # (hàng, cột, chỉ số trong doan); hàng đầu là tiêu đề cột
            for n, (so_dong, h) in enumerate(hang[1:]):
                rieng = _TAG.search(" | ".join(h))               # nhãn nằm trong một ô thì phủ riêng hàng đó
                for c, o in enumerate(h):
                    if c == 0 and stt:                           # cột đầu là số thứ tự thật
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


def cac_phan_chu(text: str) -> list:
    """MỌI phần chữ của hồ sơ, kèm nhãn phủ nó: [{'dong', 'chu', 'nhan', 'o', 'tieu_de', 'loai', 'muc', 'khoi', 'kieu_khoi',
    'cap', 'stt'}]. Phần nằm trong phạm vi đối chiếu trích dẫn được gắn nhãn đúng như tach_doan. Hàng tiêu đề của bảng, chữ
    nằm trong chính nhãn, tiêu đề mục và các mục ngoài phạm vi có nhãn ''. Với hàng dữ liệu của bảng: 'o' là các ô (đã bỏ
    nhãn), 'tieu_de' là các ô tiêu đề cột, 'stt' cho biết cột đầu có phải số thứ tự thật (cot_so_thu_tu).
    'loai': hang_bang, tieu_de_bang, doan, nhan (chữ nằm trong chính nhãn), tieu_de (dòng '#'), ngoai (mục ngoài phạm vi
    đối chiếu). 'muc': tiêu đề cấp hai đang chứa phần chữ ('' nếu trước tiêu đề đầu tiên).
    'khoi': số thứ tự của khối chứa phần chữ, theo thứ tự trong hồ sơ; 'kieu_khoi': bang, muc (một mục liệt kê), doan,
    tieu_de; 'cap': số dấu '#' của dòng tiêu đề (0 nếu không phải tiêu đề). Dòng trống không phải khối.
    Dùng cho phép kiểm phải phủ toàn hồ sơ (khoảng giá, cổng giá; QĐ-P13)."""
    dong = nfc(text).splitlines()
    muc_cua, muc = {}, ""
    for i, d in enumerate(dong, 1):
        if d.startswith("## "):
            muc = d[3:].strip()
        muc_cua[i] = muc
    kq, phu = [], set()
    la_muc = re.compile(r"\s*(?:[-*]|\d+\.)\s")

    def them(so_dong, chu, nhan, loai, khoi, kieu, o=(), tieu_de=(), stt=False):
        kq.append({"dong": so_dong, "chu": chu, "nhan": nhan, "o": list(o), "tieu_de": list(tieu_de), "loai": loai,
                   "muc": muc_cua.get(so_dong, ""), "khoi": khoi, "kieu_khoi": kieu, "cap": 0, "stt": stt})
        return kq[-1]
    for k in _gom_khoi(dong):
        phu.update(range(k["dong"], k["dong"] + len(k["dong_chu"])))
        if k["bang"]:
            hang = _hang_bang(k)
            stt = cot_so_thu_tu(hang)
            tieu_de = [_TAG.sub(" ", o) for o in hang[0][1]] if hang else []
            for n, (so_dong, h) in enumerate(hang):
                o = [_TAG.sub(" ", c) for c in h]
                rieng = _TAG.search(" | ".join(h))
                if n == 0:
                    them(so_dong, " | ".join(o), "", "tieu_de_bang", k["dong"], "bang")
                else:
                    them(so_dong, " | ".join(o), rieng.group(0) if rieng else k["nhan"], "hang_bang", k["dong"], "bang", o,
                         tieu_de, stt)
                for m in _TAG.finditer(" | ".join(h)):
                    them(so_dong, m.group(0), "", "nhan", k["dong"], "bang")
            continue
        kieu = "muc" if la_muc.match(k["dong_chu"][0]) else "doan"
        chu = " ".join(k["dong_chu"])
        bo = k.get("bo_dau", 0)
        if bo:
            them(k["dong"], chu[:bo], "", "nhan", k["dong"], kieu)
        chu, dau = chu[bo:], 0
        for m in list(_TAG.finditer(chu)) + [None]:
            them(k["dong"], chu[dau:m.start()] if m else chu[dau:], m.group(0) if m else "", "doan", k["dong"], kieu)
            if m:
                them(k["dong"], m.group(0), "", "nhan", k["dong"], kieu)
                dau = m.end()
    nhom, bang_dau = None, None                                  # các dòng còn lại: tiêu đề, mục ngoài phạm vi
    for i, d in enumerate(dong, 1):
        if i in phu or not d.strip():
            nhom, bang_dau = None, None
        elif d.startswith("#"):
            p = them(i, d, "", "tieu_de", i, "tieu_de")
            p["cap"] = len(d) - len(d.lstrip("#"))
            nhom, bang_dau = None, None
        elif d.lstrip().startswith("|"):                         # dòng bảng ngoài phạm vi: mỗi dòng một phần, chung khối
            bang_dau = bang_dau or i
            them(i, d, "", "ngoai", bang_dau, "bang")
            nhom = None
        elif nhom is None or la_muc.match(d):
            nhom = them(i, d, "", "ngoai", i, "muc" if la_muc.match(d) else "doan")
            bang_dau = None
        else:
            nhom["chu"] += " " + d
    thu_tu = {k: n for n, k in enumerate(sorted({p["khoi"] for p in kq}))}
    for p in kq:
        p["khoi"] = thu_tu[p["khoi"]]
    return sorted(kq, key=lambda x: x["dong"])


def khop_dong_goc(so_lieu: list, so, dia_chi: dict) -> bool:
    """Con số khớp một dòng GỐC của sổ có đúng nguồn, đúng trang trong địa chỉ (giữ dấu). Dòng sửa chỉ được dùng khi đã
    được chứng minh; dòng tính không bao giờ."""
    for d in so_lieu:
        if d["loai"] != "goc" or (d.get("sua") and not d.get("chung_minh")) or d["nguon"] not in dia_chi:
            continue
        if dia_chi[d["nguon"]] is not None and d["trang"] not in dia_chi[d["nguon"]]:
            continue
        if khop_co_dau(so, [d["gia_tri"]]):
            return True
    return False


def tren_trang(kho: KhoTrang, so, dia_chi: dict) -> bool:
    """Con số có trên một trang thuộc địa chỉ đã ghi không (giữ dấu, xem khop_co_dau). Trang không có trong kho bị bỏ qua."""
    return any(khop_co_dau(so, kho.tap_so_co_dau(ma, t)) for ma, trang in dia_chi.items() if ma in kho.nguon
               for t in (sorted(set(trang) & set(kho.cac_trang(ma))) if trang is not None else kho.cac_trang(ma)))


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
_KHONG_AM = {"a + b", "a ÷ b", "a ÷ b × 100", "a × b ÷ 100", "a + b + c"}   # cộng, nhân, chia trị tuyệt đối: không ra số âm


def _ra_duoc(d, ham, bo) -> bool:
    thap, cao = _khoang(d)
    try:
        gia = [ham(*goc) for goc in itertools.product(*[_khoang(x) for x in bo])]
    except ZeroDivisionError:
        return False
    return min(gia) <= cao and max(gia) >= thap


def tinh_duoc(d, hang: list, cot: list = ()) -> str:
    """Số d có ra được từ phép tính đơn giản trên các số cùng hàng (hai hoặc ba số) hay cùng cột (hai số, hoặc tổng cột)?
    Số d viết có dấu âm rõ ràng không ra được bằng phép cộng, nhân, chia; tổng cột phải âm đúng dấu."""
    am = d.gia_tri < 0
    for ten, ham in _HAI.items():
        if am and ten in _KHONG_AM:
            continue
        for a, b in itertools.permutations(hang, 2):
            if _ra_duoc(d, ham, (a, b)):
                return f"{ten} với a={a.raw}, b={b.raw}"
    if len(hang) <= 12:
        for ten, ham in _BA.items():
            if am and ten in _KHONG_AM:
                continue
            for a, b, c in itertools.permutations(hang, 3):
                if _ra_duoc(d, ham, (a, b, c)):
                    return f"{ten} với a={a.raw}, b={b.raw}, c={c.raw}"
    for ten in _COT:
        if am and ten in _KHONG_AM:
            continue
        for a, b in itertools.permutations(cot, 2):
            if _ra_duoc(d, _HAI[ten], (a, b)):
                return f"cùng cột: {ten} với a={a.raw}, b={b.raw}"
    if 2 <= len(cot) <= 40:
        tong = sum(float(x.gia_tri) for x in cot)
        sai_so = sum(float(nua_don_vi(x.so_le)) for x in cot) + float(nua_don_vi(d.so_le))
        if abs((tong if am else abs(tong)) - (float(d.gia_tri) if am else float(d.tuyet_doi))) <= sai_so:
            return "cùng cột: tổng các ô còn lại"
    return ""


# ---------- kiểm ----------
def kiem(thu_muc, ho_so_text: str) -> dict:
    kho = KhoTrang(thu_muc)
    so = doc_so_lieu(kho) if (kho.thu_muc / "so_lieu.csv").is_file() else {"bien": {}, "dong": []}
    so_lieu, bien = so["dong"], so["bien"]
    hang_so = {d["khoa"]: hang_so_cong_thuc(d.get("cong_thuc", "")) for d in so_lieu}
    doan = tach_doan(ho_so_text)
    kq = {"dem": Counter(), "loi": [], "khong_kiem": [], "so_con_so": len(doan), "lan_ra": [], "khoa_dung": []}
    if (kho.thu_muc / "ngoai_le.csv").is_file():
        kq["loi"].append("ngoai_le.csv: tệp không còn được dùng — ADR-0020 (sửa theo bản chấm L-09 vòng 2) bỏ hẳn ngoại lệ; "
                         "con số máy không lần ra thì không mang nhãn ĐÃ KIỂM. Xóa tệp này")

    def trong_so(s, dia_chi) -> bool:
        """Đoạn ĐÃ KIỂM: chỉ dòng gốc có đúng nguồn, đúng trang của nhãn, dòng sửa phải đã chứng minh. (Từ ADR-0021, đoạn
        SUY LUẬN không còn khớp «mọi dòng của sổ»: số phải khớp đúng khóa nhãn gọi tên.)"""
        return khop_dong_goc(so_lieu, s, dia_chi)

    loai = [""] * len(doan)
    cho = []                                                     # con số ĐÃ KIỂM chưa neo được vào trang hay sổ
    for i, d in enumerate(doan):                                 # lượt 1: neo con số ĐÃ KIỂM vào trang hoặc sổ
        if loai_nhan(d["nhan"]) != "ĐÃ KIỂM":
            continue
        s = d["so"]
        dia_chi = doc_dia_chi(d["nhan"])
        la = [ma for ma in dia_chi if ma not in kho.nguon]
        khong_co = [f"{ma} tr.{t}" for ma, trang in dia_chi.items() if ma in kho.nguon and trang is not None
                    for t in sorted(trang) if t not in kho.cac_trang(ma)]
        if not dia_chi or la or khong_co:
            loai[i] = "ĐỊA CHỈ SAI"
            kq["loi"].append(f"dòng {d['dong']}: {s.raw} — nhãn {d['nhan']} " + (
                "thiếu mã nguồn" if not dia_chi else f"dùng mã nguồn không có trong nguon.csv: {', '.join(la)}" if la
                else f"ghi trang không có trong thư mục trang/: {', '.join(khong_co)}"))
        elif tren_trang(kho, s, dia_chi):
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
        loai[i] = "KHÔNG LẦN RA"
        kq["loi"].append(f"dòng {d['dong']}: {s.raw}{'%' if s.pt else ''} — không có trên trang đã ghi, không có trong sổ, "
                         f"không tính ra được từ các số đã lần ra cùng đoạn {d['nhan']}")
    da_lan_ra = {(doan[i]["so"].tuyet_doi, doan[i]["so"].so_le) for i, x in enumerate(loai)
                 if x in ("TRANG", "SỔ", "TÍNH")}
    gia_tri_lan_ra = {doan[i]["so"].gia_tri for i, x in enumerate(loai) if x in ("TRANG", "SỔ", "TÍNH")}
    kq["lan_ra"] = [{"dong": d["dong"], "raw": d["so"].raw + ("%" if d["so"].pt else ""), "loai": loai[i],
                     "nhan": d["nhan"]} for i, d in enumerate(doan) if loai[i] in ("TRANG", "SỔ")]
    for i, d in enumerate(doan):                                 # lượt 3: đoạn không phải ĐÃ KIỂM
        if loai[i]:
            continue
        s, loai_n = d["so"], loai_nhan(d["nhan"])
        if not loai_n:
            loai[i] = "CHƯA GẮN NHÃN"
            kq["loi"].append(f"dòng {d['dong']}: {s.raw}{'%' if s.pt else ''} — đoạn có số mà không có nhãn")
        elif loai_n == "SUY LUẬN":                               # ADR-0021 QĐ-K1: số SUY LUẬN gắn đúng khóa nhãn gọi tên
            khoa = doc_khoa(d["nhan"], bien)[0]
            if any(khop_co_dau(s, [bien[k]]) for k in khoa):
                loai[i] = "KHÓA"
            elif any(khop_co_dau(s, hang_so.get(k, ())) for k in khoa):
                loai[i] = "HẰNG SỐ"
            elif khop_co_dau(s, gia_tri_lan_ra):
                loai[i] = "NHẮC LẠI"
            else:
                loai[i] = "KHÔNG GẮN KHÓA"
                kq["loi"].append(
                    f"dòng {d['dong']}: {s.raw}{'%' if s.pt else ''} — đoạn SUY LUẬN: số không khớp khóa nào nhãn gọi tên"
                    f" ({', '.join(khoa) if khoa else 'nhãn không gọi khóa nào'}), không phải hằng số trong công thức của"
                    f" các khóa đó, không trùng số ĐÃ KIỂM nào đã lần ra {d['nhan']}")
        elif (s.tuyet_doi, s.so_le) in da_lan_ra:
            loai[i] = "NHẮC LẠI"
        else:
            loai[i] = "MÁY KHÔNG KIỂM"
            kq["khong_kiem"].append(f"dòng {d['dong']}: {s.raw}{'%' if s.pt else ''} [{loai_n}]")
    kq["dem"].update(loai)
    nhom = {}                                                    # ADR-0021 QĐ-K1, chiều ngược: khóa gọi tên phải hiện số
    for p in cac_phan_chu(ho_so_text):
        if p["loai"] in ("doan", "hang_bang") and loai_nhan(p["nhan"]) == "SUY LUẬN" and "sổ số liệu" in p["nhan"]:
            nhom.setdefault((p["khoi"], p["nhan"]), []).append(p)
    for (_, nhan), cac_phan in nhom.items():
        dong_dau = cac_phan[0]["dong"]
        khoa, loi_khoa = doc_khoa(nhan, bien)
        kq["loi"].extend(f"dòng {dong_dau}: nhãn {nhan}: {x}" for x in loi_khoa)
        kq["khoa_dung"].append({"dong": dong_dau, "nhan": nhan, "khoa": khoa})
        hien = [s for p in cac_phan for s in so_hien(" | ".join(p["o"]) if p["loai"] == "hang_bang" else p["chu"])]
        if not hien:                                             # câu dẫn hay câu định tính không có chữ số: không xét
            continue
        for k in khoa:
            if not any(khop_co_dau(s, [bien[k]]) for s in hien):
                kq["loi"].append(f"dòng {dong_dau}: nhãn gọi khóa {k} (sổ: {_gon_so(bien[k])}) nhưng phần chữ nhãn phủ không có "
                                 f"con số nào khớp khóa này; khóa chỉ dùng làm căn cứ thì đặt sau dấu «;» {nhan}")
    for p in cac_phan_chu(ho_so_text):                           # lượt 4: số so_can_kiem bỏ qua, trong đoạn ĐÃ KIỂM
        if p["loai"] not in ("doan", "hang_bang") or loai_nhan(p["nhan"]) != "ĐÃ KIỂM":
            continue
        o = list(p["o"]) if p["loai"] == "hang_bang" else [_DAU_DONG.sub(" ", p["chu"])]
        if p["loai"] == "hang_bang" and o and p["stt"]:
            o[0] = ""
        dia_chi = doc_dia_chi(p["nhan"])
        dung = bool(dia_chi) and all(ma in kho.nguon for ma in dia_chi) and all(
            t in kho.cac_trang(ma) for ma, tr in dia_chi.items() if tr is not None for t in tr)
        for c in o:
            con = Counter((s.raw, s.gia_tri, s.pt) for s in so_can_kiem(c))
            for s in so_tho(c):
                if con[(s.raw, s.gia_tri, s.pt)] > 0:
                    con[(s.raw, s.gia_tri, s.pt)] -= 1
                    continue
                if dung and (tren_trang(kho, s, dia_chi) or khop_dong_goc(so_lieu, s, dia_chi)):
                    kq["dem"]["TRANG"] += 1
                    continue
                kq["dem"]["KHÔNG LẦN RA"] += 1
                kq["loi"].append(f"dòng {p['dong']}: {s.raw}{'%' if s.pt else ''} — số nhỏ, năm hay số trong backtick "
                                 f"ở đoạn ĐÃ KIỂM không có trên trang đã ghi hay dòng gốc của sổ {p['nhan']}")
    kq["trang_da_dung"] = sorted({(ma, t) for d in doan if loai_nhan(d["nhan"]) == "ĐÃ KIỂM"
                                  for ma, trang in doc_dia_chi(d["nhan"]).items() if ma in kho.nguon
                                  for t in (trang if trang is not None else kho.cac_trang(ma))})
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
    if a.chi_tiet:
        for dong in kq["khong_kiem"]:
            print("MÁY KHÔNG KIỂM:", dong)
    print("Con số theo đường lần ra:", ", ".join(f"{k} {v}" for k, v in sorted(kq["dem"].items())))
    return 1 if kq["loi"] else 0


if __name__ == "__main__":
    sys.exit(main())
