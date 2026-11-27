"""Phiếu máy của một hồ sơ mã (ADR-0020 QĐ-H3): chạy mọi phép kiểm và in một phiếu chạy lại được.

    python tools/hoso/phieu_may.py --thu-muc <thư mục mã> --ho-so <hồ sơ.md>

Phiếu ghi sha256 của hồ sơ, nên sửa hồ sơ một chữ là phiếu cũ hết giá trị. Phiếu không có giờ chạy: cùng đầu vào,
cùng công cụ thì ra cùng phiếu — ai có thư mục mã cũng tự chạy lại để kiểm được.

Hồ sơ chỉ được gọi là "hồ sơ mã của dự án" khi phiếu kết luận ĐẠT. Phiếu ĐẠT nghĩa là: tệp gốc đúng bản đã ghim, văn
bản trang đúng bản máy tách ra, số trong sổ khớp trang và khớp phép tính, mỗi dòng sửa so với máy đọc được một đẳng thức
cộng trừ chứng minh (phiếu in tên đẳng thức), mỗi con số ĐÃ KIỂM lần ra được (không có ngoại lệ), hồ sơ đúng khung,
không phạm L-02, và giá cổ phiếu chỉ được nêu dưới dạng số quá khứ có nguồn.
Phiếu ĐẠT KHÔNG có nghĩa là lập luận đúng: việc đó thuộc ghế phản biện khác hãng và Owner.

Cuối phiếu có mục «Owner tự mở ba số» (ADR-0021 QĐ-K4): máy chọn ba con số theo sha256 của hồ sơ, nên cùng một hồ sơ luôn
ra cùng ba số và ghế phân tích không chọn trực tiếp; sửa hồ sơ một chữ thì ba số đổi theo. Mục này không ảnh hưởng kết luận
ĐẠT hay CHƯA ĐẠT.

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
    muc("2. Sổ số liệu", loi_so, f"{len(sl['dong'])} dòng, {qh['dat']} quan hệ đúng, "
        f"{sum(1 for d in sl['dong'] if d['sua'])} dòng sửa so với máy đọc",
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
    thu_tu = ("TRANG", "SỔ", "TÍNH", "KHÓA", "HẰNG SỐ", "NHẮC LẠI", "MÁY KHÔNG KIỂM", "KHÔNG LẦN RA", "KHÔNG GẮN KHÓA",
              "CHƯA GẮN NHÃN", "ĐỊA CHỈ SAI")
    muc("4. Trích dẫn", td["loi"], ", ".join(f"{k} {dem.get(k, 0)}" for k in thu_tu) + "; không có đường ngoại lệ")

    muc("5. Luật và khung", kiem_luat.kiem(text, thu_muc),
        "L-02, cổng giá cổ phiếu, khoảng giá ở mọi mục, trạng thái kiểm, mười hai mục, mục 8 đúng câu cố định, giả thuyết, "
        "bảng nguồn")
    dong.extend(["", *ba_so(text, td, sl, sha256_tep(ho_so))])
    return _dong_goi(ho_so, dong, tong_loi == 0), tong_loi == 0


def _muc_cua(text: str) -> dict:
    """Số dòng → tiêu đề cấp hai đang chứa dòng đó."""
    muc, kq = "", {}
    for i, d in enumerate(text.splitlines(), 1):
        if d.startswith("## "):
            muc = d[3:].strip()
        kq[i] = muc
    return kq


def ba_so(text: str, td: dict, sl: dict, sha: str) -> list:
    """Ba con số Owner tự mở (ADR-0021 QĐ-K4, sửa cách chọn ở QĐ-P9 của ADR-0019). Máy chọn theo sha256 của hồ sơ:
    1) một số ĐÃ KIỂM ở «Một trang» (không có thì ở bất kỳ mục nào);
    2) một dòng máy đọc sai đã được sửa và chứng minh (không có thì một số ĐÃ KIỂM khác);
    3) một dòng gốc sau một khóa SUY LUẬN ở «Một trang» (không có thì sau bất kỳ khóa SUY LUẬN nào; vẫn không có thì một
       số ĐÃ KIỂM khác)."""
    muc = _muc_cua(text)
    hat = int(sha, 16)

    def chon(ds):
        nonlocal hat
        if not ds:
            return None
        x = ds[hat % len(ds)]
        hat //= len(ds)
        return x

    da_kiem = td.get("lan_ra", [])
    mot_trang = [x for x in da_kiem if muc.get(x["dong"]) == "Một trang"]
    kq = ["OWNER TỰ MỞ BA SỐ (ADR-0021 QĐ-K4; máy chọn theo sha256 hồ sơ, không ảnh hưởng kết luận):"]
    so1 = chon(mot_trang or da_kiem)
    con_lai = [x for x in da_kiem if so1 is None or x["raw"] != so1["raw"]]
    if so1:
        kq.append(f"1. Số ĐÃ KIỂM «{so1['raw']}» ở dòng {so1['dong']} ({muc.get(so1['dong']) or 'đầu hồ sơ'}). "
                  f"Mở đúng nguồn và trang trong nhãn {so1['nhan']}; tìm con số và tên khoản mục.")
    else:
        kq.append("1. Hồ sơ không có số ĐÃ KIỂM nào lần ra được.")
    sua = chon([d for d in sl.get("dong", []) if d.get("sua") and d.get("chung_minh")])
    if sua:
        kq.append(f"2. Dòng máy đọc sai đã sửa: khóa {sua['khoa']} — máy đọc «{sua['chuoi_goc']}», sổ ghi «{sua['gia_tri_ghi']}». "
                  f"Mở {sua['nguon']} tr.{sua['trang']}, xem ảnh trang in số nào.")
    else:
        so2 = chon(con_lai)
        con_lai = [x for x in con_lai if x["raw"] != so2["raw"]] if so2 else con_lai
        kq.append(f"2. Không có dòng sửa; thêm một số ĐÃ KIỂM: «{so2['raw']}» ở dòng {so2['dong']}, nhãn {so2['nhan']}."
                  if so2 else "2. Không có dòng sửa và không còn số ĐÃ KIỂM nào khác.")
    theo_khoa = {d["khoa"]: d for d in sl.get("dong", [])}
    khoa_mt = [k for x in td.get("khoa_dung", []) if muc.get(x["dong"]) == "Một trang" for k in x["khoa"]]
    khoa_all = [k for x in td.get("khoa_dung", []) for k in x["khoa"]]
    goc = []
    for k in (khoa_mt or khoa_all):
        for d in kiem_so_lieu.cac_dong_goc(k, theo_khoa):
            if all(d is not g for g, _ in goc):
                goc.append((d, k))
    pick = chon(goc)
    if pick:
        d, k = pick
        kq.append(f"3. Dòng gốc khóa {d['khoa']} (dùng cho khóa {k}): sổ ghi «{d['chuoi_goc']}». Mở {d['nguon']} "
                  f"tr.{d['trang']}; xem dòng này có đúng là khoản mục mà câu trong hồ sơ nói tới không.")
    else:
        so3 = chon(con_lai)
        kq.append(f"3. Không có khóa SUY LUẬN; thêm một số ĐÃ KIỂM: «{so3['raw']}» ở dòng {so3['dong']}, nhãn {so3['nhan']}."
                  if so3 else "3. Không có khóa SUY LUẬN và không còn số ĐÃ KIỂM nào khác.")
    return kq


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
