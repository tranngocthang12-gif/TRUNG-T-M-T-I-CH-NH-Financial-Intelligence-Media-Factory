"""Hàm dùng chung của bộ công cụ hồ sơ mã (ADR-0020). Chỉ dùng thư viện chuẩn của Python.

Quy ước số: kiểu Việt Nam — dấu chấm tách hàng nghìn, dấu phẩy là phần lẻ, số trong ngoặc đơn là số âm.
Nguồn dùng kiểu Anh (dấu phẩy tách nghìn) phải ghi kieu_so=en trong nguon.csv.
"""
import ast
import csv
import hashlib
import pathlib
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal

NHAN = ("ĐÃ KIỂM", "SUY LUẬN", "GIẢ ĐỊNH", "CHƯA BIẾT")
BAC = (Decimal(1), Decimal(10) ** 3, Decimal(10) ** 6, Decimal(10) ** 9)   # đồng → nghìn → triệu → tỷ


def nfc(text) -> str:
    return unicodedata.normalize("NFC", text or "")


def sha256_tep(duong) -> str:
    h = hashlib.sha256()
    with open(duong, "rb") as f:
        for khoi in iter(lambda: f.read(1 << 20), b""):
            h.update(khoi)
    return h.hexdigest()


def doc_csv(duong) -> list:
    """Đọc CSV có dòng tiêu đề; bỏ dòng trống và dòng bắt đầu bằng '#'."""
    with open(duong, encoding="utf-8-sig", newline="") as f:
        dong = [d for d in f if d.strip() and not d.lstrip().startswith("#")]
    return [{(k or "").strip(): nfc((v or "").strip()) for k, v in d.items()} for d in csv.DictReader(dong)]


# ---------- đọc số ----------
_SO = re.compile(r"""
    (?<![\w.,])
    (?P<mo>[(\[])?
    (?P<dau>[-−–+])?
    (?P<nguyen>\d{1,3}(?:\.\d{3})+|\d+)
    (?:,(?P<le>\d+))?
    (?![\d])(?![.,]\d)
    (?P<dong>[)\]}])?
    (?P<pt>\s?%)?
""", re.X)


@dataclass(frozen=True)
class So:
    raw: str          # chuỗi chữ số đúng như trong văn bản (không kèm ngoặc, dấu, %)
    gia_tri: Decimal  # có dấu
    so_le: int        # số chữ số sau dấu phẩy
    pt: bool          # có ký hiệu % đi kèm
    vi_tri: int       # vị trí trong chuỗi nguồn

    @property
    def tuyet_doi(self) -> Decimal:
        return abs(self.gia_tri)


def tim_so(text: str, kieu: str = "vn") -> list:
    """Mọi con số trong text. kieu='en': đổi chỗ dấu chấm và dấu phẩy trước khi đọc.
    kieu='ca_hai' (tệp lẫn hai kiểu viết): trả cả hai cách đọc — chỉ dùng để dò số, không dùng để đọc một ô."""
    if kieu == "ca_hai":
        return tim_so(text, "vn") + tim_so(text, "en")
    if kieu == "en":
        text = text.translate(str.maketrans({",": ".", ".": ","}))
    ket_qua = []
    for m in _SO.finditer(text):
        nguyen, le = m.group("nguyen"), m.group("le") or ""
        gia_tri = Decimal(nguyen.replace(".", "") + ("." + le if le else ""))
        am = (m.group("dau") in ("-", "−", "–")) or (m.group("mo") is not None and m.group("dong") is not None)
        ket_qua.append(So(raw=nguyen + ("," + le if le else ""), gia_tri=-gia_tri if am else gia_tri,
                          so_le=len(le), pt=m.group("pt") is not None, vi_tri=m.start("nguyen")))
    return ket_qua


def doc_so(chuoi: str) -> Decimal:
    """Đọc đúng một con số kiểu Việt Nam; lỗi nếu chuỗi không phải một con số."""
    ds = tim_so(chuoi.strip())
    if len(ds) != 1:
        raise ValueError(f"không đọc được một con số từ {chuoi!r}")
    return ds[0].gia_tri


def nua_don_vi(so_le: int) -> Decimal:
    """Nửa đơn vị của chữ số cuối: sai số do làm tròn khi viết số với so_le chữ số lẻ."""
    return Decimal(5).scaleb(-(so_le + 1))


def khop_tap(gia_tri: Decimal, so_le: int, tap) -> str:
    """Số (đã làm tròn tới so_le chữ số lẻ) có khớp một giá trị trong tap không, cho phép đổi đơn vị 10^3, 10^6, 10^9.
    Trả '' nếu không khớp; trả mô tả nếu khớp."""
    d, e = abs(gia_tri), nua_don_vi(so_le)
    for bac in BAC:
        for p in tap:
            if bac > 1 and p < bac / 2:
                continue
            if abs(p / bac - d) <= e:
                return "nguyên đơn vị" if bac == 1 else f"chia {int(bac):,}".replace(",", ".")
    return ""


def khop_co_dau(so: "So", tap_co_dau) -> str:
    """Như khop_tap, có xét dấu. tap_co_dau là tập giá trị CÓ DẤU (KhoTrang.tap_so_co_dau, hoặc giá trị trong sổ).
    Số viết có dấu âm rõ ràng (−, -, hoặc trong ngoặc đơn) chỉ khớp được số âm của tập. Số viết không dấu khớp theo trị
    tuyệt đối, vì văn xuôi thường bỏ dấu ("lỗ 1.193 tỷ")."""
    am = so.gia_tri < 0
    return khop_tap(so.gia_tri, so.so_le, {abs(p) for p in tap_co_dau if p < 0 or not am})


# ---------- trang nguồn ----------
class KhoTrang:
    """Văn bản từng trang của tệp gốc: <thu_muc>/trang/<mã nguồn>/pNNN.txt; danh mục ở <thu_muc>/nguon.csv."""

    def __init__(self, thu_muc):
        self.thu_muc = pathlib.Path(thu_muc)
        self.nguon = {d["ma"]: d for d in doc_csv(self.thu_muc / "nguon.csv")}
        self._van_ban, self._tap = {}, {}

    def cac_trang(self, ma: str) -> list:
        return sorted(int(p.stem[1:]) for p in (self.thu_muc / "trang" / ma).glob("p[0-9]*.txt") if p.stem[1:].isdigit())

    def van_ban(self, ma: str, trang: int) -> str:
        """Văn bản một trang: pNNN.txt, nối thêm mọi bản đọc lại pNNN.<tên>.txt (ví dụ đọc lại ở 400 dpi)."""
        if (ma, trang) not in self._van_ban:
            goc = self.thu_muc / "trang" / ma
            tep = [goc / f"p{trang:03d}.txt"] + sorted(goc.glob(f"p{trang:03d}.*.txt"))
            self._van_ban[(ma, trang)] = "\n".join(nfc(p.read_text(encoding="utf-8")) for p in tep if p.is_file())
        return self._van_ban[(ma, trang)]

    def kieu_so(self, ma: str) -> str:
        return (self.nguon.get(ma, {}).get("kieu_so") or "vn").lower()

    def tap_so(self, ma: str, trang: int) -> frozenset:
        """Tập trị tuyệt đối của mọi con số trên một trang."""
        if (ma, trang) not in self._tap:
            self._tap[(ma, trang)] = frozenset(s.tuyet_doi for s in tim_so(self.van_ban(ma, trang), self.kieu_so(ma)))
        return self._tap[(ma, trang)]

    def tap_so_co_dau(self, ma: str, trang: int) -> frozenset:
        """Tập giá trị CÓ DẤU của mọi con số trên một trang: số trong ngoặc đơn hoặc có dấu trừ là số âm."""
        if (ma, trang, "dau") not in self._tap:
            so = tim_so(self.van_ban(ma, trang), self.kieu_so(ma))
            self._tap[(ma, trang, "dau")] = frozenset(s.gia_tri for s in so)
        return self._tap[(ma, trang, "dau")]


# ---------- biểu thức số học an toàn ----------
_PHEP = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
         ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b}


def tinh_bieu_thuc(bieu_thuc: str, bien: dict) -> Decimal:
    """Tính biểu thức chỉ gồm + - * /, ngoặc, số và tên khóa trong bien. Không gọi hàm, không truy cập thuộc tính."""
    def di(nut):
        if isinstance(nut, ast.Expression):
            return di(nut.body)
        if isinstance(nut, ast.BinOp) and type(nut.op) in _PHEP:
            return _PHEP[type(nut.op)](di(nut.left), di(nut.right))
        if isinstance(nut, ast.UnaryOp) and isinstance(nut.op, (ast.USub, ast.UAdd)):
            return -di(nut.operand) if isinstance(nut.op, ast.USub) else di(nut.operand)
        if isinstance(nut, ast.Constant) and isinstance(nut.value, (int, float)) and not isinstance(nut.value, bool):
            return Decimal(str(nut.value))
        if isinstance(nut, ast.Name):
            if nut.id not in bien:
                raise KeyError(f"khóa {nut.id!r} chưa có trong sổ số liệu")
            return bien[nut.id]
        raise ValueError(f"biểu thức không được phép: {bieu_thuc!r}")
    return di(ast.parse(bieu_thuc.strip(), mode="eval"))
