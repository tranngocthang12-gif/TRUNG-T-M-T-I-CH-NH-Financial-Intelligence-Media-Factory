"""B6 của quy trình hồ sơ mã: kiểm luật và khung của hồ sơ (ADR-0019 QĐ-P5, QĐ-P13; ADR-0020).

1. L-02: không cụm từ khuyến nghị nào ở bất kỳ dòng nào. Dùng đúng bộ mẫu của tools/laws_checks.py, thêm vài cụm
   riêng của hồ sơ mã. Kiểm cứng, không xét ngữ cảnh: câu phủ định có cụm cấm cũng bị bắt — đổi cách viết.
2. Khung: đủ mười hai mục theo thứ tự; có "Một trang", "Kết quả 15 điểm soi", "Danh sách CHƯA BIẾT", "Bảng nguồn".
3. Mục 8 để trống cho tới khi Owner sửa L-02 (QĐ-P13).
4. Mục 11 có giả thuyết H0, H1, H2, điều kiện làm giả thuyết sai và ngày xem lại.
5. Bảng 15 điểm soi đủ mười lăm dòng. Danh sách CHƯA BIẾT có ít nhất một dòng.
6. Đầu hồ sơ ghi rõ đây không phải lời khuyên đầu tư và là bản riêng tư.
7. Bảng nguồn khớp nguon.csv: đủ mã, đúng 12 ký tự đầu sha256.

Chạy: python tools/hoso/kiem_luat.py --thu-muc <thư mục mã> --ho-so <tệp .md>
"""
import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools import laws_checks  # noqa: E402
from tools.hoso.chung import KhoTrang, nfc  # noqa: E402
from tools.hoso.kiem_trich_dan import _TAG, doc_dia_chi, loai_nhan, so_can_kiem  # noqa: E402

CAM_THEM = [r"n[êe]n n[ắa]m gi[ữu]", r"n[êe]n gi[ữu]", r"khuy[ếe]n ngh[ịi]", r"[đd]i[ểe]m mua", r"[đd]i[ểe]m b[áa]n",
            r"v[ùu]ng mua", r"v[ùu]ng b[áa]n", r"ch[ốo]t l[ờo]i", r"c[ắa]t l[ỗo]", r"gi[áa] h[ợo]p l[ýy]",
            r"[đd][ịi]nh gi[áa] (?:h[ấa]p d[ẫa]n|r[ẻe]|[đd][ắa]t)", r"\bHOLD\b"]
_CAM = re.compile("|".join(laws_checks.RECOMMEND_PATTERNS + CAM_THEM), re.IGNORECASE)
SAU_MUC_12 = ("Kết quả 15 điểm soi", "Danh sách CHƯA BIẾT", "Bảng nguồn")


def _cac_muc(dong: list) -> list:
    """[(số dòng, tiêu đề, thân)] của các tiêu đề cấp hai."""
    dau = [i for i, d in enumerate(dong) if d.startswith("## ")]
    return [(i + 1, dong[i][3:].strip(), "\n".join(dong[i + 1:j])) for i, j in zip(dau, dau[1:] + [len(dong)])]


def kiem(ho_so_text: str, thu_muc=None) -> list:
    text = nfc(ho_so_text)
    dong = text.splitlines()
    loi = []
    for i, d in enumerate(dong, 1):                              # 1. L-02
        m = _CAM.search(d)
        if m:
            loi.append(f"dòng {i}: cụm từ L-02 cấm: «{m.group(0)}»")
    muc = _cac_muc(dong)
    ten = [t for _, t, _ in muc]
    so_muc = [int(m.group(1)) for t in ten for m in [re.match(r"Mục (\d+)\.", t)] if m]
    if so_muc != list(range(1, 13)):                             # 2. khung
        loi.append(f"khung: cần đúng mười hai tiêu đề '## Mục 1.' tới '## Mục 12.' theo thứ tự; đang có {so_muc}")
    vi_tri = {x: next((n for n, t in enumerate(ten) if t.startswith(x)), None) for x in ("Một trang", "Mục 1.") + SAU_MUC_12}
    if None in vi_tri.values():
        loi.append("khung: thiếu tiêu đề " + ", ".join(f"'## {x}'" for x, v in vi_tri.items() if v is None))
    elif not (vi_tri["Một trang"] < vi_tri["Mục 1."] and vi_tri["Kết quả 15 điểm soi"] < vi_tri["Danh sách CHƯA BIẾT"]
              < vi_tri["Bảng nguồn"]):
        loi.append("khung: thứ tự phải là Một trang, Mục 1–12, Kết quả 15 điểm soi, Danh sách CHƯA BIẾT, Bảng nguồn")
    than = {t: b for _, t, b in muc}

    def than_cua(dau_ten):
        return next((b for t, b in than.items() if t.startswith(dau_ten)), "")
    muc8 = than_cua("Mục 8.")                                    # 3. mục 8 trống
    if not ("Chưa viết" in muc8 and "QĐ-P13" in muc8) or so_can_kiem(muc8) or "|" in muc8:
        loi.append("Mục 8: phải để trống, chỉ ghi 'Chưa viết' và dẫn QĐ-P13; không số liệu, không bảng (L-02 chưa sửa)")
    muc11 = than_cua("Mục 11.")                                  # 4. giả thuyết
    thieu = [x for x in ("H0", "H1", "H2") if x not in muc11]
    if thieu or not re.search(r"điều kiện", muc11, re.I) or not re.search(r"ngày xem lại", muc11, re.I):
        loi.append("Mục 11: cần đủ H0, H1, H2, 'điều kiện' làm giả thuyết sai và 'ngày xem lại'"
                   + (f"; thiếu {', '.join(thieu)}" if thieu else ""))
    diem = {int(m.group(1)) for m in re.finditer(r"^\|\s*\**(\d{1,2})\**\s*\|", than_cua("Kết quả 15 điểm soi"), re.M)}
    if not set(range(1, 16)) <= diem:                            # 5. điểm soi, CHƯA BIẾT
        loi.append(f"Kết quả 15 điểm soi: thiếu dòng {sorted(set(range(1, 16)) - diem)}")
    if not re.search(r"^\s*(?:[-*]|\d+\.)\s+\S", than_cua("Danh sách CHƯA BIẾT"), re.M):
        loi.append("Danh sách CHƯA BIẾT: cần ít nhất một dòng")
    dau = "\n".join(dong[:muc[0][0] - 1]) if muc else text       # 6. đầu hồ sơ
    if "không phải lời khuyên đầu tư" not in dau or "riêng tư" not in dau:
        loi.append("đầu hồ sơ: phải ghi 'không phải lời khuyên đầu tư' và 'riêng tư' trước tiêu đề đầu tiên")
    if thu_muc is not None:                                      # 7. bảng nguồn
        kho = KhoTrang(thu_muc)
        bang = dict(re.findall(r"^\|\s*([A-Z]\d{1,2})\s*\|.*\|\s*([0-9a-f]{12})\s*\|\s*$", than_cua("Bảng nguồn"), re.M))
        for ma, dau_sha in sorted(bang.items()):
            if ma not in kho.nguon:
                loi.append(f"Bảng nguồn: mã {ma} không có trong nguon.csv")
            elif not kho.nguon[ma].get("sha256", "").startswith(dau_sha):
                loi.append(f"Bảng nguồn: sha256 của {ma} ghi {dau_sha}, nguon.csv là {kho.nguon[ma].get('sha256', '')[:12]}")
        da_dung = {ma for m in _TAG.finditer(text) if loai_nhan(m.group(0)) == "ĐÃ KIỂM" for ma in doc_dia_chi(m.group(0))}
        for ma in sorted(da_dung - set(bang)):
            loi.append(f"Bảng nguồn: mã {ma} được dùng trong nhãn nhưng không có dòng (hoặc thiếu sha256) trong bảng")
    return loi


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--thu-muc")
    ap.add_argument("--ho-so", required=True)
    a = ap.parse_args(argv)
    loi = kiem(pathlib.Path(a.ho_so).read_text(encoding="utf-8"), a.thu_muc)
    for d in loi:
        print("LỖI:", d)
    print("Luật và khung:", "ĐẠT" if not loi else f"CHƯA ĐẠT ({len(loi)} lỗi)")
    return 1 if loi else 0


if __name__ == "__main__":
    sys.exit(main())
