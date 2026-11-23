"""B3 của quy trình hồ sơ mã: nhận tệp gốc, ghim sha256, tách văn bản từng trang.

Chạy trong thư mục làm việc RIÊNG TƯ của một mã (không nằm trong kho công khai):
    python tools/hoso/nhan_tep.py nhan --thu-muc <thư mục mã> --ma-nguon <ma_nguon.csv>
    python tools/hoso/nhan_tep.py kiem --thu-muc <thư mục mã>
    python tools/hoso/nhan_tep.py doc-lai --thu-muc <thư mục mã> --ma D7 --trang 16 [--dpi 400 --psm 4]

ma_nguon.csv do ghế phân tích viết, cột: ma,tep,ten,kieu_so
  ma      mã nguồn dùng trong hồ sơ (D1, D2, E1, G1 …)
  tep     đường dẫn tương đối trong <thư mục mã>/goc/
  ten     tên dễ đọc của tài liệu
  kieu_so vn (mặc định), en, hoặc ca_hai nếu tệp lẫn hai kiểu viết số

Kết quả: <thư mục mã>/nguon.csv và <thư mục mã>/trang/<ma>/pNNN.txt.
PDF có lớp chữ thì đọc bằng pdftotext; PDF dạng ảnh thì pdftoppm (300 dpi, xám) rồi tesseract (vie+eng).
Tệp văn bản (.csv .md .txt) được coi là một trang. Thiếu chương trình ngoài thì dừng và báo, không đoán.
"""
import argparse
import csv
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools.hoso.chung import doc_csv, sha256_tep  # noqa: E402

COT = ["ma", "tep", "ten", "sha256", "so_trang", "cach_doc", "kieu_so"]
NGUONG_CHU = 200      # dưới ngần này ký tự mỗi trang (trung bình) thì coi PDF là ảnh
VAN_BAN = {".csv", ".md", ".txt"}


def _chay(lenh: list) -> str:
    if shutil.which(lenh[0]) is None:
        raise SystemExit(f"DỪNG: thiếu chương trình {lenh[0]!r} trên máy này. Không tách được trang, không đoán số.")
    return subprocess.run(lenh, check=True, capture_output=True, text=True).stdout


def _so_trang_pdf(tep) -> int:
    for dong in _chay(["pdfinfo", str(tep)]).splitlines():
        if dong.startswith("Pages:"):
            return int(dong.split()[1])
    raise SystemExit(f"DỪNG: không đọc được số trang của {tep}")


def _tach_pdf(tep, thu_muc_trang) -> tuple:
    n = _so_trang_pdf(tep)
    chu = [_chay(["pdftotext", "-layout", "-f", str(i), "-l", str(i), str(tep), "-"]) for i in range(1, n + 1)]
    cach = "chu"
    if sum(len(t.strip()) for t in chu) < NGUONG_CHU * n:
        cach, chu = "ocr", []
        with tempfile.TemporaryDirectory() as tam:
            for i in range(1, n + 1):
                goc = pathlib.Path(tam) / f"p{i:03d}"
                _chay(["pdftoppm", "-r", "300", "-gray", "-png", "-singlefile", "-f", str(i), "-l", str(i),
                       str(tep), str(goc)])
                chu.append(_chay(["tesseract", f"{goc}.png", "-", "-l", "vie+eng", "--psm", "6",
                                  "-c", "preserve_interword_spaces=1"]))
    thu_muc_trang.mkdir(parents=True, exist_ok=True)
    for i, t in enumerate(chu, 1):
        (thu_muc_trang / f"p{i:03d}.txt").write_text(t, encoding="utf-8")
    return n, cach


def van_ban_cua_tep(tep) -> str:
    """Nội dung tệp văn bản. Tệp .csv được đổi dấu phẩy ngăn cột thành dấu tab, để dấu phẩy không lẫn với số."""
    chu = pathlib.Path(tep).read_text(encoding="utf-8-sig")
    if pathlib.Path(tep).suffix.lower() != ".csv":
        return chu
    return "\n".join("\t".join(hang) for hang in csv.reader(chu.splitlines())) + "\n"


def doc_lai(thu_muc, ma: str, trang: int, dpi: int = 400, psm: int = 4) -> pathlib.Path:
    """Đọc lại một trang ảnh với độ phân giải và cách dàn trang khác; ghi thêm pNNN.dpi<dpi>psm<psm>.txt, không ghi đè."""
    thu_muc = pathlib.Path(thu_muc)
    d = {x["ma"]: x for x in doc_csv(thu_muc / "nguon.csv")}[ma]
    tep = thu_muc / "goc" / d["tep"]
    with tempfile.TemporaryDirectory() as tam:
        goc = pathlib.Path(tam) / "p"
        _chay(["pdftoppm", "-r", str(dpi), "-gray", "-png", "-singlefile", "-f", str(trang), "-l", str(trang),
               str(tep), str(goc)])
        chu = _chay(["tesseract", f"{goc}.png", "-", "-l", "vie+eng", "--psm", str(psm),
                     "-c", "preserve_interword_spaces=1"])
    ra = thu_muc / "trang" / ma / f"p{trang:03d}.dpi{dpi}psm{psm}.txt"
    ra.write_text(chu, encoding="utf-8")
    return ra


def nhan(thu_muc, ma_nguon) -> list:
    thu_muc = pathlib.Path(thu_muc)
    dong_ra = []
    for d in doc_csv(ma_nguon):
        tep = thu_muc / "goc" / d["tep"]
        if (thu_muc / "goc").resolve() not in tep.resolve().parents:
            raise SystemExit(f"DỪNG: tệp {d['tep']!r} nằm ngoài thư mục goc/")
        if not tep.is_file():
            raise SystemExit(f"DỪNG: không thấy tệp gốc {tep}")
        dich = thu_muc / "trang" / d["ma"]
        if tep.suffix.lower() in VAN_BAN:
            dich.mkdir(parents=True, exist_ok=True)
            (dich / "p001.txt").write_text(van_ban_cua_tep(tep), encoding="utf-8")
            n, cach = 1, "van_ban"
        elif tep.suffix.lower() == ".pdf":
            n, cach = _tach_pdf(tep, dich)
        else:
            raise SystemExit(f"DỪNG: chưa hỗ trợ loại tệp {tep.suffix} ({tep.name})")
        dong_ra.append({"ma": d["ma"], "tep": d["tep"], "ten": d.get("ten", ""), "sha256": sha256_tep(tep),
                        "so_trang": n, "cach_doc": cach, "kieu_so": d.get("kieu_so") or "vn"})
    with open(thu_muc / "nguon.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COT, lineterminator="\n")
        w.writeheader()
        w.writerows(dong_ra)
    return dong_ra


def kiem_ke(thu_muc) -> list:
    """Danh sách lỗi của danh mục nguồn: mã trùng, tệp gốc mất hoặc đổi nội dung, thiếu trang văn bản."""
    thu_muc = pathlib.Path(thu_muc)
    p = thu_muc / "nguon.csv"
    if not p.is_file():
        return ["thiếu nguon.csv"]
    loi, da_thay = [], set()
    for d in doc_csv(p):
        ma = d.get("ma", "")
        if not ma or ma in da_thay:
            loi.append(f"mã nguồn trống hoặc trùng: {ma!r}")
            continue
        da_thay.add(ma)
        tep = thu_muc / "goc" / d.get("tep", "")
        if not tep.is_file():
            loi.append(f"{ma}: không thấy tệp gốc goc/{d.get('tep', '')}")
        elif sha256_tep(tep) != d.get("sha256", ""):
            loi.append(f"{ma}: sha256 của tệp gốc không khớp nguon.csv (tệp đã bị đổi)")
        try:
            n = int(d.get("so_trang", "0"))
        except ValueError:
            n = 0
        co = len([t for t in (thu_muc / "trang" / ma).glob("p*.txt") if t.stem[1:].isdigit()])
        if n < 1 or co != n:
            loi.append(f"{ma}: nguon.csv ghi {d.get('so_trang', '')} trang, thư mục trang/ có {co}")
    return loi


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("viec", choices=["nhan", "kiem", "doc-lai"])
    ap.add_argument("--thu-muc", required=True)
    ap.add_argument("--ma-nguon")
    ap.add_argument("--ma")
    ap.add_argument("--trang", type=int)
    ap.add_argument("--dpi", type=int, default=400)
    ap.add_argument("--psm", type=int, default=4)
    a = ap.parse_args(argv)
    if a.viec == "doc-lai":
        if not a.ma or not a.trang:
            ap.error("doc-lai cần --ma và --trang")
        print("Đã ghi", doc_lai(a.thu_muc, a.ma, a.trang, a.dpi, a.psm))
        return 0
    if a.viec == "nhan":
        if not a.ma_nguon:
            ap.error("nhan cần --ma-nguon")
        for d in nhan(a.thu_muc, a.ma_nguon):
            print(f"{d['ma']}: {d['so_trang']} trang, đọc bằng {d['cach_doc']}, sha256 {d['sha256'][:12]}")
    loi = kiem_ke(a.thu_muc)
    for dong in loi:
        print("LỖI:", dong)
    print("Danh mục nguồn:", "ĐẠT" if not loi else f"CHƯA ĐẠT ({len(loi)} lỗi)")
    return 1 if loi else 0


if __name__ == "__main__":
    sys.exit(main())
