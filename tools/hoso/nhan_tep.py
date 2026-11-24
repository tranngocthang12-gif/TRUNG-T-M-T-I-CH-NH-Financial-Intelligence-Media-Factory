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

Kết quả: <thư mục mã>/nguon.csv, <thư mục mã>/trang/<ma>/pNNN.txt và <thư mục mã>/trang_sha256.csv.
PDF có lớp chữ thì đọc bằng pdftotext; PDF dạng ảnh thì pdftoppm (300 dpi, xám) rồi tesseract (vie+eng).
Tệp văn bản (.csv .md .txt) được coi là một trang. Thiếu chương trình ngoài thì dừng và báo, không đoán.

trang_sha256.csv ghi sha256 của từng tệp trong trang/<ma>/ lúc máy tạo ra nó (nhan và doc-lai), kèm sha256 của tệp gốc
đã tách ra nó. kiem_ke báo lỗi nếu một tệp trang bị sửa, bị thêm hay bị mất sau đó. Chỗ hợp lệ duy nhất để sửa lỗi máy
đọc là dòng goc trong so_lieu.csv (gia_tri kèm ghi_chu); không sửa tay vào trang/.
Chạy lại nhan thì mọi trang chính pNNN.txt được tách lại từ tệp gốc; bản đọc lại còn đúng dấu vân tay thì được giữ.
Giới hạn: trang_sha256.csv cũng là văn bản. Người sửa cả trang lẫn danh mục thì chỉ bị bắt ở tệp gốc dạng văn bản (máy
tách lại và so); với PDF, cách kiểm là chạy lại nhan trên tệp gốc đã ghim rồi lập lại phiếu.
"""
import argparse
import csv
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools.hoso.chung import doc_csv, sha256_tep  # noqa: E402

COT = ["ma", "tep", "ten", "sha256", "so_trang", "cach_doc", "kieu_so"]
VAN_TAY = "trang_sha256.csv"
COT_VAN_TAY = ["ma", "tep", "sha256", "sha256_goc", "cach"]
_TRANG_CHINH = re.compile(r"^p\d+\.txt$")              # pNNN.txt: trang chính, luôn tách lại được từ tệp gốc
_DOC_LAI = re.compile(r"^p\d+\.dpi\d+psm\d+\.txt$")    # bản đọc lại do doc_lai ghi
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


def doc_van_tay(thu_muc) -> dict:
    """{(mã nguồn, tên tệp trang): dòng} của trang_sha256.csv; {} nếu chưa có tệp."""
    p = pathlib.Path(thu_muc) / VAN_TAY
    return {(d.get("ma", ""), d.get("tep", "")): d for d in doc_csv(p)} if p.is_file() else {}


def _ghi_van_tay(thu_muc, van_tay: dict) -> None:
    with open(pathlib.Path(thu_muc) / VAN_TAY, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COT_VAN_TAY, lineterminator="\n")
        w.writeheader()
        w.writerows({k: van_tay[x].get(k, "") for k in COT_VAN_TAY} for x in sorted(van_tay))


def doc_lai(thu_muc, ma: str, trang: int, dpi: int = 400, psm: int = 4) -> pathlib.Path:
    """Đọc lại một trang ảnh với độ phân giải và cách dàn trang khác; ghi thêm pNNN.dpi<dpi>psm<psm>.txt (không ghi đè
    pNNN.txt) và ghi dấu vân tay của bản đọc lại vào trang_sha256.csv."""
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
    van_tay = doc_van_tay(thu_muc)
    van_tay[(ma, ra.name)] = {"ma": ma, "tep": ra.name, "sha256": sha256_tep(ra), "sha256_goc": sha256_tep(tep),
                              "cach": f"doc_lai dpi{dpi} psm{psm}"}
    _ghi_van_tay(thu_muc, van_tay)
    return ra


def nhan(thu_muc, ma_nguon) -> list:
    thu_muc = pathlib.Path(thu_muc)
    cu, van_tay, dong_ra = doc_van_tay(thu_muc), {}, []
    for d in doc_csv(ma_nguon):
        tep = thu_muc / "goc" / d["tep"]
        if (thu_muc / "goc").resolve() not in tep.resolve().parents:
            raise SystemExit(f"DỪNG: tệp {d['tep']!r} nằm ngoài thư mục goc/")
        if not tep.is_file():
            raise SystemExit(f"DỪNG: không thấy tệp gốc {tep}")
        dich = thu_muc / "trang" / d["ma"]
        sha_goc = sha256_tep(tep)
        if dich.is_dir():                                        # trang chính luôn tách lại từ tệp gốc
            for t in dich.iterdir():
                if t.is_file() and _TRANG_CHINH.match(t.name):
                    t.unlink()
        if tep.suffix.lower() in VAN_BAN:
            dich.mkdir(parents=True, exist_ok=True)
            (dich / "p001.txt").write_text(van_ban_cua_tep(tep), encoding="utf-8")
            n, cach = 1, "van_ban"
        elif tep.suffix.lower() == ".pdf":
            n, cach = _tach_pdf(tep, dich)
        else:
            raise SystemExit(f"DỪNG: chưa hỗ trợ loại tệp {tep.suffix} ({tep.name})")
        for t in sorted(dich.iterdir()):
            sha, cu_t = sha256_tep(t) if t.is_file() else "", cu.get((d["ma"], t.name), {})
            if t.is_file() and _TRANG_CHINH.match(t.name):
                van_tay[(d["ma"], t.name)] = {"ma": d["ma"], "tep": t.name, "sha256": sha, "sha256_goc": sha_goc,
                                              "cach": cach}
            elif (t.is_file() and _DOC_LAI.match(t.name) and cu_t.get("sha256") == sha
                  and cu_t.get("sha256_goc") == sha_goc):
                van_tay[(d["ma"], t.name)] = cu_t                  # bản đọc lại còn nguyên: giữ
            else:
                raise SystemExit(f"DỪNG: trang/{d['ma']}/{t.name} không do nhan_tep tạo ra, đã bị sửa, hoặc đọc từ một "
                                 "bản tệp gốc khác. Xóa nó rồi chạy lại (bản đọc lại thì chạy lại doc-lai).")
        dong_ra.append({"ma": d["ma"], "tep": d["tep"], "ten": d.get("ten", ""), "sha256": sha_goc,
                        "so_trang": n, "cach_doc": cach, "kieu_so": d.get("kieu_so") or "vn"})
    with open(thu_muc / "nguon.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COT, lineterminator="\n")
        w.writeheader()
        w.writerows(dong_ra)
    _ghi_van_tay(thu_muc, van_tay)
    return dong_ra


def kiem_ke(thu_muc) -> list:
    """Danh sách lỗi của danh mục nguồn: mã trùng, tệp gốc mất hoặc đổi nội dung, thiếu trang văn bản; tệp trang bị sửa,
    bị thêm hay bị mất so với trang_sha256.csv, hoặc tách từ bản tệp gốc khác bản đã ghim."""
    thu_muc = pathlib.Path(thu_muc)
    p = thu_muc / "nguon.csv"
    if not p.is_file():
        return ["thiếu nguon.csv"]
    if not (thu_muc / VAN_TAY).is_file():
        return [f"thiếu {VAN_TAY}: chạy lại nhan_tep.py nhan để máy ghi dấu vân tay từng trang"]
    van_tay = doc_van_tay(thu_muc)
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
        loi.extend(_kiem_van_tay(thu_muc, ma, d, tep, van_tay))
    for m in sorted({m for m, _ in van_tay} - da_thay):
        loi.append(f"{VAN_TAY}: có mã nguồn {m!r} không có trong nguon.csv")
    return loi


def _kiem_van_tay(thu_muc, ma: str, d: dict, tep, van_tay: dict) -> list:
    """Lỗi về tệp trong trang/<ma>/ so với trang_sha256.csv."""
    thu_muc_trang = thu_muc / "trang" / ma
    co = {t.name: t for t in thu_muc_trang.iterdir()} if thu_muc_trang.is_dir() else {}
    ghi = {tep_t: v for (m, tep_t), v in van_tay.items() if m == ma}
    loi = [f"{ma}: trang/{ma}/{ten} không có trong {VAN_TAY} (không do nhan_tep tạo ra)"
           for ten in sorted(set(co) - set(ghi))]
    loi += [f"{ma}: trang/{ma}/{ten} có trong {VAN_TAY} mà đã mất" for ten in sorted(set(ghi) - set(co))]
    for ten in sorted(set(co) & set(ghi)):
        if not co[ten].is_file() or sha256_tep(co[ten]) != ghi[ten].get("sha256"):
            loi.append(f"{ma}: trang/{ma}/{ten} đã bị sửa sau khi máy tạo ra (sha256 khác {VAN_TAY}). "
                       "Sửa lỗi máy đọc bằng dòng goc trong so_lieu.csv, không sửa trang")
        elif ghi[ten].get("sha256_goc") != d.get("sha256"):
            loi.append(f"{ma}: trang/{ma}/{ten} được tách từ một bản tệp gốc khác bản đã ghim trong nguon.csv")
    chinh = thu_muc_trang / "p001.txt"                          # tệp gốc dạng văn bản: tách lại và so
    if (tep.is_file() and tep.suffix.lower() in VAN_BAN and sha256_tep(tep) == d.get("sha256") and chinh.is_file()
            and chinh.read_text(encoding="utf-8") != van_ban_cua_tep(tep)):
        loi.append(f"{ma}: trang/{ma}/p001.txt khác văn bản tách lại từ tệp gốc")
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
