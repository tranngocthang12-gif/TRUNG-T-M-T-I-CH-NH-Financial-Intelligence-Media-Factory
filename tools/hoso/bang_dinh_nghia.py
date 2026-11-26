"""Bảng định nghĩa của một hồ sơ mã (ADR-0021 QĐ-K2): lớp mà máy không kiểm được nghĩa.

    python tools/hoso/bang_dinh_nghia.py --thu-muc <thư mục mã> --ho-so <hồ sơ.md> [--ra <tệp .md>]

Phiếu máy kiểm con số có trên trang, phép tính đúng và số SUY LUẬN khớp khóa nhãn gọi tên. Phiếu không biết một công thức
có tính đúng điều câu hồ sơ nói không, cùng một chỉ tiêu ở hai kỳ có cùng phạm vi không, hay dòng gốc có đúng là khoản mục
câu hồ sơ nói tới không. Bảng này gom đúng phần đó cho người đọc: mỗi khóa sổ mà nhãn SUY LUẬN gọi tên, theo thứ tự gặp
trong hồ sơ, kèm giá trị, công thức, các dòng gốc nó dựa vào (nguồn, trang, chuỗi máy đọc) và các dòng hồ sơ dùng nó.

Bảng gửi kèm lệnh đối chiếu số ở bước B7 (templates/hoso/LENH_MAU.md, mẫu C). Bảng nằm trong thư mục mã, riêng tư như
hồ sơ, không vào kho. Không có giờ chạy: cùng đầu vào, cùng công cụ thì ra cùng bảng. Mặc định ghi cạnh hồ sơ:
BANG_DINH_NGHIA_<tên hồ sơ>.md
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools.hoso import kiem_so_lieu, kiem_trich_dan  # noqa: E402
from tools.hoso.chung import KhoTrang, sha256_tep  # noqa: E402
from tools.hoso.phieu_may import _commit, _muc_cua  # noqa: E402

CAU_HOI = (
    "Công thức có tính đúng điều câu hồ sơ ở cột «Dùng ở» nói không?",
    "Cùng một chỉ tiêu ở các kỳ khác nhau (ví dụ cuối năm và cuối quý) có cùng công thức, cùng phạm vi không?",
    "Dòng gốc có đúng là khoản mục câu hồ sơ nói tới không? Mở trang để xem tên dòng in trên báo cáo.",
)


def _hien(v) -> str:
    """Giá trị viết kiểu Việt Nam: dấu chấm ngăn nghìn, dấu phẩy thập phân, tối đa bốn chữ số lẻ."""
    chu = f"{v:,.0f}" if abs(v) >= 1000 else f"{v:,.4f}".rstrip("0").rstrip(".")
    return chu.replace(",", "§").replace(".", ",").replace("§", ".")


def _o(text: str) -> str:
    """Chữ an toàn cho một ô bảng Markdown."""
    return " ".join(str(text).replace("|", "/").split())


def lap_bang(thu_muc, ho_so) -> str:
    ho_so = pathlib.Path(ho_so)
    text = ho_so.read_text(encoding="utf-8")
    kho = KhoTrang(thu_muc)
    sl = kiem_so_lieu.doc_so_lieu(kho)
    theo_khoa = {d["khoa"]: d for d in sl["dong"]}
    td = kiem_trich_dan.kiem(thu_muc, text)
    muc = _muc_cua(text)
    dung = {}
    for x in td["khoa_dung"]:
        for k in x["khoa"]:
            dung.setdefault(k, [])
            for dg in x.get("dong_khoa", {}).get(k) or [x["dong"]]:   # dòng có số khớp khóa; không có thì dòng đầu nhãn
                if dg not in dung[k]:
                    dung[k].append(dg)
    dong = [
        "# BẢNG ĐỊNH NGHĨA — HỒ SƠ MÃ (ADR-0021 QĐ-K2)",
        "",
        f"- Hồ sơ: {ho_so.name}",
        f"- sha256 hồ sơ: {sha256_tep(ho_so)}",
        f"- Công cụ: tools/hoso tại commit {_commit()}",
        f"- Số khóa: {len(dung)}",
        "",
        "Với từng dòng, ghế đối chiếu trả lời KHỚP NGHĨA hoặc LỆCH NGHĨA kèm một câu lý do, theo ba câu hỏi:",
        "",
        *[f"{n}. {c}" for n, c in enumerate(CAU_HOI, 1)],
        "",
        "| # | Khóa | Giá trị | Đơn vị | Công thức | Dòng gốc (nguồn, trang, chuỗi máy đọc) | Dùng ở |",
        "|---|---|---|---|---|---|---|",
    ]
    for n, (k, cac_dong) in enumerate(dung.items(), 1):
        d = theo_khoa.get(k)
        if d is None:
            continue
        goc = []
        for g in kiem_so_lieu.cac_dong_goc(k, theo_khoa):
            sua = f", sổ ghi {g['gia_tri_ghi']} (đã sửa so với máy đọc)" if g.get("sua") else ""
            goc.append(f"{g['khoa']}: {g['nguon']} tr.{g['trang']} «{g['chuoi_goc']}»{sua}")
        cong_thuc = d.get("cong_thuc") or "(dòng gốc)"
        o_dung = "; ".join(f"dòng {x} ({muc.get(x) or 'đầu hồ sơ'})" for x in cac_dong)
        dong.append(f"| {n} | {k} | {_hien(d['gia_tri'])} | {_o(d.get('don_vi', ''))} | {_o(cong_thuc)} | "
                    f"{_o('; '.join(goc))} | {_o(o_dung)} |")
    if td["loi"]:
        dong += ["", f"Lưu ý: phiếu máy của hồ sơ này còn {len(td['loi'])} lỗi trích dẫn; bảng có thể thiếu khóa."]
    return "\n".join(dong) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--thu-muc", required=True)
    ap.add_argument("--ho-so", required=True)
    ap.add_argument("--ra", help="tệp ghi bảng; mặc định BANG_DINH_NGHIA_<tên hồ sơ>.md cạnh hồ sơ")
    a = ap.parse_args(argv)
    bang = lap_bang(a.thu_muc, a.ho_so)
    p = pathlib.Path(a.ho_so)
    ra = pathlib.Path(a.ra) if a.ra else p.with_name(f"BANG_DINH_NGHIA_{p.stem}.md")
    ra.write_text(bang, encoding="utf-8")
    print(bang)
    return 0


if __name__ == "__main__":
    sys.exit(main())
