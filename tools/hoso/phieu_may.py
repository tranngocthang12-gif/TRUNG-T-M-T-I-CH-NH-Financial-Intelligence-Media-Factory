"""Phiếu máy của một hồ sơ mã (ADR-0020 QĐ-H3): chạy mọi phép kiểm và in một phiếu chạy lại được.

    python tools/hoso/phieu_may.py --thu-muc <thư mục mã> --ho-so <hồ sơ.md>

Phiếu ghi sha256 của hồ sơ, nên sửa hồ sơ một chữ là phiếu cũ hết giá trị. Phiếu không có giờ chạy: cùng đầu vào,
cùng công cụ thì ra cùng phiếu — ai có thư mục mã cũng tự chạy lại để kiểm được.

Hồ sơ chỉ được gọi là "hồ sơ mã của dự án" khi phiếu kết luận ĐẠT. Phiếu ĐẠT nghĩa là: tệp gốc đúng bản đã ghim, văn
bản trang đúng bản máy tách ra, số trong sổ khớp trang và khớp phép tính, mỗi con số ĐÃ KIỂM lần ra được, hồ sơ đúng
khung và không phạm L-02.
Phiếu ĐẠT KHÔNG có nghĩa là lập luận đúng: việc đó thuộc ghế phản biện khác hãng và Owner. Số NGOẠI LỆ chỉ được máy kiểm
địa chỉ (nguồn, trang), không kiểm con số có trên trang: ghế phản biện đối chiếu từng số với trang gốc.

Mã thoát: 0 nếu ĐẠT, 1 nếu CHƯA ĐẠT. Phiếu được ghi cạnh hồ sơ: PHIEU_MAY_<tên hồ sơ>.txt
"""
import argparse
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools.hoso import kiem_luat, kiem_so_lieu, kiem_trich_dan, nhan_tep  # noqa: E402
from tools.hoso.chung import KhoTrang, sha256_tep  # noqa: E402

BA_BAO_CAO = ("cdkt", "kqkd", "lctt")     # quan_he.csv phải có ít nhất một đẳng thức đúng cho mỗi báo cáo
GIOI_HAN_IN = 200


def _commit() -> str:
    try:
        goc = pathlib.Path(__file__).resolve().parents[2]
        return subprocess.run(["git", "-C", str(goc), "rev-parse", "--short", "HEAD"], check=True,
                              capture_output=True, text=True).stdout.strip() or "không rõ"
    except (OSError, subprocess.CalledProcessError):
        return "không rõ"


def lap_phieu(thu_muc, ho_so) -> tuple:
    """Trả (văn bản phiếu, đạt hay không)."""
    ho_so = pathlib.Path(ho_so)
    text = ho_so.read_text(encoding="utf-8")
    dong, tong_loi = [], 0

    def muc(ten, loi, tom_tat, phu=()):
        nonlocal tong_loi
        tong_loi += len(loi)
        dong.append(f"{ten}: {'ĐẠT' if not loi else f'CHƯA ĐẠT ({len(loi)} lỗi)'} — {tom_tat}")
        dong.extend(f"   LỖI: {x}" for x in loi[:GIOI_HAN_IN])
        if len(loi) > GIOI_HAN_IN:
            dong.append(f"   … còn {len(loi) - GIOI_HAN_IN} lỗi nữa")
        dong.extend(f"   {x}" for x in phu)

    loi_nguon = nhan_tep.kiem_ke(thu_muc)
    if loi_nguon:                                                # không có nguồn đáng tin thì không kiểm tiếp
        muc("1. Danh mục nguồn", loi_nguon, "tệp gốc không đúng bản đã ghim")
        return _dong_goi(ho_so, dong, False), False
    kho = KhoTrang(thu_muc)
    muc("1. Danh mục nguồn", [], f"{len(kho.nguon)} tệp, sha256 khớp, đủ trang, văn bản trang khớp dấu vân tay đã ghi")

    sl = kiem_so_lieu.doc_so_lieu(kho)
    qh = kiem_so_lieu.kiem_quan_he(kho, sl["bien"])
    thieu = [b for b in BA_BAO_CAO if not any(t.lower().startswith(b) for t in qh["ten_dat"])]
    loi_so = sl["loi"] + qh["loi"] + [f"quan_he.csv chưa có đẳng thức đúng nào tên bắt đầu bằng '{b}'" for b in thieu]
    muc("2. Sổ số liệu", loi_so, f"{len(sl['dong'])} dòng, {qh['dat']} quan hệ đúng",
        [f"ĐÃ SỬA SO VỚI MÁY ĐỌC: {x}" for x in sl["da_sua"]])

    td = kiem_trich_dan.kiem(thu_muc, text)
    sb = kiem_so_lieu.soat_bang(kho)
    da_ghi_chu = {(d["nguon"], d["trang"], d["chuoi_goc"]) for d in sl["dong"] if d["loai"] == "goc" and d["ghi_chu"]}
    trang_dung = set(td["trang_da_dung"])
    chua_xu_ly, ngoai = [], 0
    for n in sb["nghi"]:
        if (n["ma"], n["trang"]) not in trang_dung:
            ngoai += 1
        elif not any((n["ma"], n["trang"], so) in da_ghi_chu for so in n["so"]):
            chua_xu_ly.append(n["mo_ta"] + " — chưa có dòng nào trong so_lieu.csv kèm ghi_chu kết luận về hàng này")
    muc("3. Soát bảng", chua_xu_ly, f"{sb['khop']} hàng so sánh khớp phép tính; {len(sb['nghi'])} hàng nghi máy đọc sai, "
        f"trong đó {ngoai} hàng ở trang hồ sơ không dùng")

    dem = td["dem"]
    thu_tu = ("TRANG", "SỔ", "TÍNH", "NGOẠI LỆ", "NHẮC LẠI", "MÁY KHÔNG KIỂM", "KHÔNG LẦN RA", "CHƯA GẮN NHÃN", "ĐỊA CHỈ SAI")
    muc("4. Trích dẫn", td["loi"], ", ".join(f"{k} {dem.get(k, 0)}" for k in thu_tu),
        [f"NGOẠI LỆ: {x}" for x in td["ngoai_le"]] + [td["ti_le_ngoai_le"]
         + " (máy chỉ kiểm nguồn và trang của ngoại lệ; ghế phản biện đối chiếu từng số với trang gốc)"] + td["canh_bao"])

    muc("5. Luật và khung", kiem_luat.kiem(text, thu_muc),
        "L-02, khoảng giá ở mọi mục, mười hai mục, mục 8 đúng câu cố định, giả thuyết, bảng nguồn")
    return _dong_goi(ho_so, dong, tong_loi == 0), tong_loi == 0


def _dong_goi(ho_so, dong, dat) -> str:
    return "\n".join([
        "PHIẾU MÁY — HỒ SƠ MÃ (ADR-0020)",
        f"Hồ sơ  : {ho_so.name}",
        f"sha256 : {sha256_tep(ho_so)}",
        f"Công cụ: tools/hoso tại commit {_commit()}",
        "",
        *dong,
        "",
        f"KẾT LUẬN: {'ĐẠT' if dat else 'CHƯA ĐẠT'}",
        "Phiếu ĐẠT nghĩa là con số lần ra được và hồ sơ đúng khung. Phiếu không xét lập luận đúng hay sai.",
        "",
    ])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--thu-muc", required=True)
    ap.add_argument("--ho-so", required=True)
    ap.add_argument("--khong-ghi", action="store_true", help="chỉ in ra màn hình, không ghi tệp phiếu")
    a = ap.parse_args(argv)
    phieu, dat = lap_phieu(a.thu_muc, a.ho_so)
    print(phieu)
    if not a.khong_ghi:
        p = pathlib.Path(a.ho_so)
        p.with_name(f"PHIEU_MAY_{p.stem}.txt").write_text(phieu, encoding="utf-8")
    return 0 if dat else 1


if __name__ == "__main__":
    sys.exit(main())
