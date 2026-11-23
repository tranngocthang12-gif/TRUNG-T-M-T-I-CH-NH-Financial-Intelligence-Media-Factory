"""B7 của quy trình hồ sơ mã: gài một lỗi cố ý vào bản gửi phản biện (ADR-0019 QĐ-P9).

    python tools/hoso/gai_loi.py tao  --thu-muc <thư mục mã> --ho-so <hồ sơ.md> --tim "6,89%" --thay "8,69%" [--ngu-canh "…"]
    python tools/hoso/gai_loi.py kiem --ho-so <hồ sơ.md> --niem-phong <…_LOI_GAI.md>

`tao` ghi hai tệp cạnh hồ sơ: <tên>_BAN_PHAN_BIEN.md (gửi ghế phản biện và ghế đối chiếu số) và <tên>_LOI_GAI.md (niêm
phong, KHÔNG gửi ghế nào). Hồ sơ gốc không bị sửa: đó là bản Owner đọc.

Bản phản biện mang một "mã nhận tệp" ở đầu. Ghế nào trả lời mà không chép lại được mã này là chưa đọc tệp (bài học hồ sơ
đầu tiên: ghế phản biện trả lời từ tài liệu trên mạng vì Owner quên đính tệp).

Bài học hồ sơ đầu tiên: lỗi gài phải nằm ở chỗ mà phép đối chiếu số bắt được. Vì vậy `tao` chỉ nhận lỗi gài nếu máy đối
chiếu (kiem_trich_dan) báo thêm ĐÚNG MỘT con số không lần ra ở bản phản biện so với bản gốc. Không đạt thì từ chối.

`kiem` xác nhận bản Owner không còn dòng đã gài (QĐ-P9: lỗi thử được gỡ trước khi giao Owner).
"""
import argparse
import hashlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools.hoso import kiem_trich_dan  # noqa: E402
from tools.hoso.chung import nfc, sha256_tep  # noqa: E402

HAU_TO = " — BẢN PHẢN BIỆN"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tao(thu_muc, ho_so, tim: str, thay: str, ngu_canh: str = "") -> tuple:
    ho_so = pathlib.Path(ho_so)
    goc = ho_so.read_text(encoding="utf-8")
    dong = goc.split("\n")
    tim, thay, ngu_canh = nfc(tim), nfc(thay), nfc(ngu_canh)
    ung_vien = [i for i, d in enumerate(dong) if tim in nfc(d) and ngu_canh in nfc(d)]
    if len(ung_vien) != 1 or nfc(dong[ung_vien[0]]).count(tim) != 1:
        raise SystemExit(f"TỪ CHỐI: «{tim}» phải xuất hiện đúng một lần trên đúng một dòng (đang có {len(ung_vien)} dòng). "
                         "Thêm --ngu-canh để chỉ rõ dòng.")
    i = ung_vien[0]
    dong_gai = nfc(dong[i]).replace(tim, thay)
    moi = dong[:i] + [dong_gai] + dong[i + 1:]
    if not moi[0].startswith("# ") or i == 0:
        raise SystemExit("TỪ CHỐI: dòng đầu hồ sơ phải là tiêu đề '# …' và lỗi gài không được nằm ở dòng đó.")
    loi_goc = set(kiem_trich_dan.kiem(thu_muc, goc)["loi"])      # so khi số dòng hai bản còn trùng nhau
    them = [x for x in kiem_trich_dan.kiem(thu_muc, "\n".join(moi))["loi"] if x not in loi_goc]
    if len(them) != 1 or not them[0].startswith(f"dòng {i + 1}:") or "không có trên trang" not in them[0]:
        raise SystemExit("TỪ CHỐI: máy đối chiếu không báo thêm đúng một con số không lần ra ở dòng đã gài "
                         f"(báo thêm {len(them)}). Lỗi gài này nằm ngoài tầm phép đối chiếu số; chọn con số khác "
                         "trong một đoạn ĐÃ KIỂM có ghi trang.")
    ma_nhan = _sha("\n".join(moi))[:8].upper()
    moi[0] += HAU_TO
    moi.insert(1, f"\n- **Mã nhận tệp: {ma_nhan}.** Ghế phản biện và ghế đối chiếu số chép lại mã này ở dòng đầu bản trả lời.")
    ban_pb = "\n".join(moi)
    dong_pb = ban_pb.split("\n").index(dong_gai) + 1
    duong_pb = ho_so.with_name(ho_so.stem + "_BAN_PHAN_BIEN.md")
    duong_np = ho_so.with_name(ho_so.stem + "_LOI_GAI.md")
    duong_pb.write_text(ban_pb, encoding="utf-8")
    sha_owner, sha_pb = sha256_tep(ho_so), sha256_tep(duong_pb)
    duong_np.write_text("\n".join([
        f"# LỖI GÀI CỐ Ý — {ho_so.name} (niêm phong)",
        "",
        "KHÔNG gửi tệp này cho ghế phản biện hay ghế đối chiếu số. Chỉ Owner và ghế phân tích đọc.",
        "",
        f"- ban_owner: {ho_so.name}",
        f"- sha256_ban_owner: {sha_owner}",
        f"- ban_phan_bien: {duong_pb.name}",
        f"- sha256_ban_phan_bien: {sha_pb}",
        f"- ma_nhan_tep: {ma_nhan}",
        f"- dong_trong_ban_owner: {i + 1}",
        f"- dong_trong_ban_phan_bien: {dong_pb}",
        f"- dung: {tim}",
        f"- da_gai: {thay}",
        f"- dong_da_gai: {dong_gai}",
        f"- may_bao: {them[0]}",
        "",
        "## Kết quả (ghế phân tích điền sau khi nhận bản phản biện)",
        "",
        "| Ghế | Hãng | Có nhận được tệp không | Có bắt được lỗi gài không | Ngày |",
        "|---|---|---|---|---|",
        "| | | | | |",
        "",
    ]), encoding="utf-8")
    return duong_pb, duong_np


def kiem(ho_so, niem_phong) -> list:
    """Lỗi nếu bản Owner còn dòng đã gài, hoặc tệp niêm phong không đọc được."""
    goc = nfc(pathlib.Path(ho_so).read_text(encoding="utf-8"))
    np_ = nfc(pathlib.Path(niem_phong).read_text(encoding="utf-8"))
    truong = dict(d[2:].split(": ", 1) for d in np_.splitlines() if d.startswith("- ") and ": " in d)
    if "dong_da_gai" not in truong or "da_gai" not in truong:
        return ["tệp niêm phong thiếu dong_da_gai hoặc da_gai"]
    loi = []
    if truong["dong_da_gai"] in goc.split("\n"):
        loi.append(f"bản Owner còn dòng đã gài (giá trị {truong['da_gai']}): chưa gỡ lỗi thử")
    if goc.split("\n", 1)[0].endswith(HAU_TO):
        loi.append("tệp đang kiểm là bản phản biện, không phải bản Owner")
    return loi


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("viec", choices=["tao", "kiem"])
    ap.add_argument("--thu-muc")
    ap.add_argument("--ho-so", required=True)
    ap.add_argument("--tim")
    ap.add_argument("--thay")
    ap.add_argument("--ngu-canh", default="")
    ap.add_argument("--niem-phong")
    a = ap.parse_args(argv)
    if a.viec == "tao":
        if not (a.thu_muc and a.tim and a.thay):
            ap.error("tao cần --thu-muc, --tim, --thay")
        pb, np_ = tao(a.thu_muc, a.ho_so, a.tim, a.thay, a.ngu_canh)
        print(f"Đã ghi {pb.name} (gửi phản biện) và {np_.name} (niêm phong, không gửi).")
        return 0
    if not a.niem_phong:
        ap.error("kiem cần --niem-phong")
    loi = kiem(a.ho_so, a.niem_phong)
    for d in loi:
        print("LỖI:", d)
    print("Bản Owner không còn lỗi gài:", "ĐẠT" if not loi else "CHƯA ĐẠT")
    return 1 if loi else 0


if __name__ == "__main__":
    sys.exit(main())
