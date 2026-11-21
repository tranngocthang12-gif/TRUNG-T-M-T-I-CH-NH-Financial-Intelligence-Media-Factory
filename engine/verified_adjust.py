"""Chuỗi 'verified-adjusted': CỔNG BẰNG CHỨNG cho sự kiện quyền cổ phiếu (ADR-0009 điều 2, 3 và 7).

Module này CHỈ ĐỌC. Nó không sửa `engine/adjust.py`, không sửa kho raw, không ghi đĩa, không gọi mạng.
Chuỗi điều chỉnh hiện hành (`adjust.build_events` / `adjust.factors`) giữ nguyên nghĩa của nó: ở đó `ex_date` là ngày
CHUỖI GIÁ GỐC GÃY trong kho, chưa chắc là ngày giao dịch không hưởng quyền chính thức, và trạng thái `source_status`
(ví dụ CAN_DOI_CHIEU) chỉ được chép sang kết quả, KHÔNG tham gia quyết định APPLIED. Quyết định APPLIED chỉ dựa vào việc
biên độ giá sau điều chỉnh nằm trong sàn. Đó là nguyên nhân một sự kiện chưa đối chiếu vẫn thành APPLIED.

Cổng này dựng một chuỗi RIÊNG. Một sự kiện cổ phiếu chỉ vào chuỗi đó khi đủ cả chín điều kiện:
  1. có bản gốc đã ghim trong manifest (source_id, url, issuer, path, sha256 đều là chuỗi không rỗng), tệp tồn tại, đúng
     sha256 và số byte; bản gốc thuộc lớp STOCK như sự kiện engine (QĐ-2, ADR-0016: chia tách và trả cổ tức bằng cổ phiếu
     cùng một lớp vì engine tính hệ số như nhau). Bản gốc thuộc lớp STOCK khi `event_type` thuộc `adjust.STOCK`, hoặc khi
     `event_type` trống và nguyên văn loại (`event_type_verbatim`, không có thì `source_event_text`) nằm trong bảng ánh xạ
     đóng STOCK_VERBATIM; nguyên văn ngoài bảng thì CÁCH LY LOAI_CHUA_ANH_XA. Nguyên văn trong manifest không bị sửa;
  2. có ngày công bố (`published_at`) hợp lệ: có mặt, không muộn hơn ngày cắt `as_of`, sớm hơn ngày không hưởng quyền;
  3. tỷ lệ in trên văn bản (`official_ratio`) là số hữu hạn dương và trùng tỷ lệ của sự kiện khi làm tròn tới RATIO_DECIMALS
     = 7 chữ số thập phân;
  4. NGÀY GIAO DỊCH mà engine đang áp sự kiện trùng ngày giao dịch của ngày không hưởng quyền chính thức;
  5. không có sự kiện nào khác của cùng bản gốc được engine áp ở ngày khác; "cùng bản gốc" xét theo cả `source_id` lẫn
     sha256 của tệp, nên đổi hay bỏ `source_id` không lách được kiểm tra này;
  6. trạng thái engine nằm trong danh sách cho phép VERIFIABLE = APPLIED hoặc DA_NAM_TRONG_GIA_NGUON (giá gốc đã chứa
     điều chỉnh). Mọi trạng thái khác, kể cả trạng thái engine chưa biết, đều bị cách ly.
  7. GIÁ phải chứng minh đúng một giả thuyết, đo trực tiếp từ `close` (không tin `raw_return`/`adj_return` của bảng sự kiện),
     biên độ theo `adjust.limits`/`bands` (chỉ đọc). Hai giả thuyết tại phiên sự kiện: "giá gốc chưa điều chỉnh" (bước giá gốc
     ngoài biên, bước giá sau khi nhân tỷ lệ trong biên) và "giá gốc đã điều chỉnh" (bước giá gốc trong biên, sau khi nhân tỷ
     lệ ngoài biên). Engine không kiểm đủ: APPLIED chỉ xét bước giá sau khi nhân tỷ lệ; DA_NAM_TRONG_GIA_NGUON chỉ xét nguồn
     yahoo và `observed_at`. Cổng dùng CHUNG một hàm `_price_hypothesis` cho cả hai:
       - APPLIED (chuỗi kiểm chứng sẽ áp hệ số) chỉ nhận khi giá chứng minh "chưa điều chỉnh"; không thì CÁCH LY
         GIA_KHONG_CHUNG_MINH_HE_SO;
       - DA_NAM_TRONG_GIA_NGUON (không áp hệ số) chỉ nhận khi giá chứng minh "đã điều chỉnh"; không thì CÁCH LY
         GIA_CHUA_LIEN_TUC.
     Mơ hồ (cả hai bước giá trong biên) hoặc sai cả hai (cả hai ngoài biên) đều bị cách ly và nhiễm ô.
  8. Với DA_NAM_TRONG_GIA_NGUON: KHÔNG có bước giá gốc ngoài biên nào trong WINDOW_DAYS ngày lịch trước phiên sự kiện; có thì
     CÁCH LY GIA_GAY_TRUOC_NGAY_HUONG_QUYEN (nguồn có thể chỉ điều chỉnh vài phiên liền trước, như TCB/VCB trong kho thật).
  9. Mọi phiên trên trục ngày của panel (`close.index`) trong [phiên sự kiện − WINDOW_DAYS ngày lịch, phiên sự kiện] đều có
     giá của mã; thiếu bất kỳ phiên nào thì CÁCH LY THIEU_GIA_TRUOC_NGAY_HUONG_QUYEN. Kiểm TRƯỚC điều kiện 7 và 8: khi thiếu
     phiên, bước giá đo qua chỗ trống có biên nới theo số phiên (`adjust.bands`), nên một bước gãy có thể lọt qua cả hai.
Không đạt thì CÁCH LY: không đưa vào hệ số của chuỗi kiểm chứng, và mọi ô giá của mã đó TRƯỚC ngày giao dịch của sự kiện bị
đánh dấu TAINTED (không bảo đảm so sánh được qua sự kiện). Cổng KHÔNG đổi ngày hộ và KHÔNG suy ngày đúng từ bước nhảy giá.
Sự kiện tiền mặt chưa có bằng chứng ghim nên chưa được xét; chuỗi kiểm chứng là chuỗi giá gốc cộng các sự kiện cổ phiếu
đã kiểm, KHÔNG điều chỉnh cổ tức tiền mặt.
Module chưa được nối vào vòng học hay `data.sources` (ADR-0009 điều 7)."""
from __future__ import annotations

import hashlib
import json
import pathlib
import unicodedata
from decimal import ROUND_HALF_UP, Decimal

import numpy as np
import pandas as pd

from . import adjust

STOCK = adjust.STOCK
IMPACT = ("APPLIED", "KHONG_KHOP", "DA_NAM_TRONG_GIA_NGUON", "LOI_TY_LE")   # trạng thái engine cho thấy có chỗ gãy dữ liệu thật
NO_DATA = ("KHONG_CO_MA", "CHUA_DEN_HAN", "NGOAI_DU_LIEU")                   # không có cửa sổ giá để so
VERIFIABLE = ("APPLIED", "DA_NAM_TRONG_GIA_NGUON")                           # danh sách cho phép: chỉ hai trạng thái này được kiểm
DOC_REQUIRED = ("source_id", "url", "issuer", "path", "sha256")
WINDOW_DAYS = 45          # bản gốc phải có ngày không hưởng quyền cách ngày engine không quá ngần này ngày lịch
# Tỷ lệ so ở 7 chữ số thập phân: đó là độ chính xác của data/derived/yahoo_actions.csv (ví dụ CTG 2025: Yahoo 1.4463658,
# văn bản 1,4463658403). So chặt hơn thì một sự kiện đúng bị loại chỉ vì nguồn làm tròn; so lỏng hơn thì tỷ lệ sai lọt qua.
RATIO_DECIMALS = 7
# QĐ-2 (ADR-0016): bảng ánh xạ ĐÓNG từ nguyên văn loại sự kiện trên bản gốc sang lớp STOCK. Chỉ gồm nguyên văn "trả cổ tức
# bằng cổ phiếu" đã gặp trong manifest. Không có: cổ tức tiền, phát hành quyền mua, phát hành tăng vốn từ nguồn vốn chủ sở
# hữu (cổ phiếu thưởng), loại gộp cổ tức và tăng vốn. Những nguyên văn đó ra LOAI_CHUA_ANH_XA. Đổi bảng phải qua PR và L-09.
# So sau khi chuẩn hóa: Unicode NFC, chữ thường (casefold), gộp khoảng trắng.
STOCK_VERBATIM = frozenset({
    "trả cổ tức bằng cổ phiếu",
    "chi trả cổ tức bằng cổ phiếu",
    "phát hành cổ phiếu để trả cổ tức",
})
VERBATIM_FIELDS = ("event_type_verbatim", "source_event_text")

OK = "DA_KIEM_CHUNG"
NA_NODATA = "KHONG_ANH_HUONG"
NA_CASH = "KHONG_XET_TIEN_MAT"
Q = "CACH_LY_"
STATES = (OK, NA_NODATA, NA_CASH, Q + "THIEU_BANG_CHUNG", Q + "BANG_CHUNG_HONG", Q + "THIEU_NGAY_CONG_BO",
          Q + "CONG_BO_SAU_NGAY_CAT", Q + "CONG_BO_SAU_NGAY_HUONG_QUYEN", Q + "TY_LE_LECH", Q + "LECH_NGAY",
          Q + "XUNG_DOT_NGAY", Q + "GIA_KHONG_KHOP_TY_LE", Q + "LOAI_SU_KIEN_LECH",
          Q + "TRANG_THAI_ENGINE_KHONG_HOP_LE", Q + "GIA_CHUA_LIEN_TUC", Q + "GIA_KHONG_CHUNG_MINH_HE_SO",
          Q + "GIA_GAY_TRUOC_NGAY_HUONG_QUYEN", Q + "THIEU_GIA_TRUOC_NGAY_HUONG_QUYEN", Q + "LOAI_CHUA_ANH_XA")
# trạng thái engine → giả thuyết giá phải được chứng minh; trạng thái cách ly khi không chứng minh được
EXPECTED_HYPOTHESIS = {"APPLIED": "CAN_HE_SO", "DA_NAM_TRONG_GIA_NGUON": "DA_DIEU_CHINH"}
HYPOTHESIS_FAIL_STATE = {"CAN_HE_SO": Q + "GIA_KHONG_CHUNG_MINH_HE_SO", "DA_DIEU_CHINH": Q + "GIA_CHUA_LIEN_TUC"}

NEW_COLS = ["verify_state", "verify_reason", "evidence_id", "official_ex_date", "official_trade_date",
            "session_offset", "in_verified_chain", "taints"]


def _ts(x):
    if x is None:
        return pd.NaT
    try:
        v = pd.to_datetime(x, errors="coerce")
    except Exception:                       # noqa: BLE001
        return pd.NaT
    return v if isinstance(v, pd.Timestamp) else pd.NaT


def sha256_file(p) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def load_evidence(manifest_paths) -> list[dict]:
    """Đọc các EVIDENCE_MANIFEST.json (lược đồ `source_documents[]`, ADR-0009 điều 2). Không có tệp thì trả về danh sách rỗng."""
    docs = []
    for mp in manifest_paths or []:
        p = pathlib.Path(mp)
        if not p.is_file():
            continue
        j = json.loads(p.read_text(encoding="utf-8"))
        for d in j.get("source_documents", []):
            docs.append({**d, "_manifest": p.name})
    return docs


def _positive_number(x):
    """Số hữu hạn dương (không nhận bool, chuỗi, None, NaN, vô cực, 0, số âm)."""
    if isinstance(x, bool) or not isinstance(x, (int, float, np.integer, np.floating)):
        return None
    v = float(x)
    return v if np.isfinite(v) and v > 0 else None


def _doc_problem(d, base):
    for k in DOC_REQUIRED:
        v = d.get(k)
        if not isinstance(v, str) or not v.strip():
            return f"mục manifest thiếu trường {k} (phải là chuỗi không rỗng)"
    p = pathlib.Path(base) / d["path"]
    if not p.is_file():
        return "tệp bản gốc không tồn tại tại đường dẫn đã ghi"
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != d["sha256"]:
        return "sha256 của tệp không khớp manifest"
    if d.get("bytes") is not None and len(b) != int(d["bytes"]):
        return "số byte của tệp không khớp manifest"
    return None


def _norm_text(x) -> str:
    return " ".join(unicodedata.normalize("NFC", x).casefold().split()) if isinstance(x, str) else ""


def _doc_class(d):
    """(lớp, mô tả) của bản gốc: "STOCK", "OTHER" (event_type khác lớp STOCK) hoặc "UNMAPPED" (event_type trống và
    nguyên văn loại không có trong STOCK_VERBATIM). Chỉ đọc, không sửa bản gốc."""
    et = d.get("event_type")
    if et in STOCK:
        return "STOCK", f"event_type {et}"
    if isinstance(et, str) and et.strip():
        return "OTHER", f"event_type {et}"
    for f in VERBATIM_FIELDS:
        v = d.get(f)
        if isinstance(v, str) and v.strip():
            if _norm_text(v) in STOCK_VERBATIM:
                return "STOCK", f"{f} '{v}' thuộc bảng ánh xạ STOCK"
            return "UNMAPPED", f"{f} '{v}' không có trong bảng ánh xạ đóng STOCK_VERBATIM"
    return "UNMAPPED", "event_type trống và không có nguyên văn loại sự kiện"


def _ratio_key(x) -> Decimal:
    return Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-RATIO_DECIMALS), rounding=ROUND_HALF_UP)


def _match(ticker, ex_date, typ, docs):
    """Bản gốc của cùng mã có ngày không hưởng quyền gần ngày của sự kiện nhất, trong WINDOW_DAYS ngày lịch.

    Nhận bản gốc lớp STOCK và bản gốc có `event_type` trống (xếp lớp bằng nguyên văn ở `_judge`); bản gốc có `event_type`
    thuộc loại khác (ví dụ cổ tức tiền) không được ghép. Cùng khoảng cách thì ưu tiên bản lớp STOCK, rồi bản cùng loại.
    Bản gốc chưa ánh xạ vẫn được ghép để `_judge` CÁCH LY với lý do rõ ràng và để nó tham gia kiểm tra trùng ngày."""
    best = None
    for d in docs:
        et = d.get("event_type")
        if d.get("ticker") != ticker or (et not in STOCK and isinstance(et, str) and et.strip()):
            continue
        od = _ts(d.get("official_ex_date"))
        if pd.isna(od) or pd.isna(ex_date):
            continue
        key = (abs((od - ex_date).days), _doc_class(d)[0] != "STOCK", et != typ)
        if key[0] <= WINDOW_DAYS and (best is None or key < best[0]):
            best = (key, d)
    return best[1] if best else None


def _price_hypothesis(r, close, td):
    """(giả thuyết, mô tả) mà giá gốc tại phiên td chứng minh, đo trực tiếp từ `close` (không dùng cột của bảng sự kiện).

    Giả thuyết: "CAN_HE_SO" (bước giá gốc ngoài biên, nhân tỷ lệ thì trong biên: giá gốc chưa điều chỉnh, cần hệ số),
    "DA_DIEU_CHINH" (bước giá gốc trong biên, nhân tỷ lệ thì ngoài biên: nguồn đã điều chỉnh), "MO_HO" (cả hai trong biên),
    "SAI_CA_HAI" (cả hai ngoài biên), hoặc None khi không đo được."""
    s = close[r["ticker"]].dropna()
    before = s[s.index < td]
    if before.empty or td not in s.index:
        return None, "không có phiên giá liền trước để đo bước giá"
    p0, p1 = float(before.iloc[-1]), float(s.loc[td])
    if not (np.isfinite(p0) and np.isfinite(p1) and p0 > 0 and p1 > 0):
        return None, "giá gốc quanh phiên sự kiện không hợp lệ"
    _, K = adjust.obs_returns(close[[r["ticker"]]])
    k = K.at[td, r["ticker"]]
    L = adjust.limits(close.index, [r["ticker"]]).at[td, r["ticker"]]
    up, dn = adjust.bands(L, k if pd.notna(k) else 1.0)
    raw = p1 / p0 - 1
    adj = (1 + raw) * float(r["ratio"]) - 1
    raw_in, adj_in = -dn <= raw <= up, -dn <= adj <= up
    desc = (f"tại {td.date()}: bước giá gốc {raw:+.2%} ({'trong' if raw_in else 'ngoài'} biên), sau điều chỉnh tỷ lệ "
            f"{float(r['ratio'])} {adj:+.2%} ({'trong' if adj_in else 'ngoài'} biên); biên −{dn:.2%}/+{up:.2%}")
    if raw_in and adj_in:
        return "MO_HO", desc + "; giá không phân biệt được nguồn đã hay chưa điều chỉnh"
    if not raw_in and not adj_in:
        return "SAI_CA_HAI", desc + "; không giả thuyết nào giải thích được bước giá"
    return ("CAN_HE_SO" if adj_in else "DA_DIEU_CHINH"), desc


def _price_problem(r, close, td):
    """(trạng thái cách ly, lý do) nếu giá không chứng minh đúng giả thuyết mà trạng thái engine đòi hỏi, hoặc None."""
    want = EXPECTED_HYPOTHESIS[r["status"]]
    got, desc = _price_hypothesis(r, close, td)
    if got == want:
        return None
    lead = {"CAN_HE_SO": "engine áp hệ số (APPLIED) nhưng giá không chứng minh giá gốc cần hệ số",
            "DA_DIEU_CHINH": "engine báo giá nguồn đã chứa điều chỉnh nhưng giá không chứng minh điều đó"}[want]
    tail = {"CAN_HE_SO": "; giá gốc còn bước gãy", "SAI_CA_HAI": "; giá gốc còn bước gãy",
            "DA_DIEU_CHINH": "; giá gốc liên tục, áp hệ số sẽ tạo bước gãy"}.get(got, "")
    return HYPOTHESIS_FAIL_STATE[want], f"{lead} — {desc}{tail}"


def _judge(r, d, close, base, as_of):
    """(state, reason, official_trade_date, offset) cho một sự kiện cổ phiếu đã khớp bản gốc d."""
    bad = _doc_problem(d, base)
    if bad:
        return Q + "BANG_CHUNG_HONG", bad, pd.NaT, np.nan
    cls, cdesc = _doc_class(d)
    if cls == "UNMAPPED":
        return Q + "LOAI_CHUA_ANH_XA", f"{cdesc}; không xếp được bản gốc vào lớp STOCK (QĐ-2)", pd.NaT, np.nan
    if cls != "STOCK" or r["type"] not in STOCK:
        return (Q + "LOAI_SU_KIEN_LECH", f"bản gốc ({cdesc}) và sự kiện engine ({r['type']}) không cùng lớp STOCK",
                pd.NaT, np.nan)
    pub, off = _ts(d.get("published_at")), _ts(d.get("official_ex_date"))
    if pd.isna(pub):
        return Q + "THIEU_NGAY_CONG_BO", "bản gốc không có published_at; không lấy ngày hưởng quyền thay ngày công bố", pd.NaT, np.nan
    if pub > as_of:
        return Q + "CONG_BO_SAU_NGAY_CAT", f"công bố {pub.date()} sau ngày cắt {as_of.date()}", pd.NaT, np.nan
    if pub >= off:
        return Q + "CONG_BO_SAU_NGAY_HUONG_QUYEN", f"công bố {pub.date()} không sớm hơn ngày không hưởng quyền {off.date()}", pd.NaT, np.nan
    ro, rv = d.get("official_ratio"), r["ratio"]
    fo, fv = _positive_number(ro), _positive_number(rv)
    if fo is None or fv is None:
        return Q + "TY_LE_LECH", f"tỷ lệ không hợp lệ (văn bản {ro!r}, sự kiện {rv!r}); phải là số hữu hạn dương", pd.NaT, np.nan
    if _ratio_key(fo) != _ratio_key(fv):
        return (Q + "TY_LE_LECH", f"tỷ lệ in trên văn bản {ro} khác tỷ lệ sự kiện {rv} ở {RATIO_DECIMALS} chữ số thập phân "
                f"({_ratio_key(fo)} và {_ratio_key(fv)})", pd.NaT, np.nan)
    sess = close[r["ticker"]].dropna().index
    pos = int(sess.searchsorted(off))
    if pos >= len(sess):
        return Q + "LECH_NGAY", f"ngày không hưởng quyền chính thức {off.date()} nằm sau dữ liệu giá hiện có", pd.NaT, np.nan
    otd, td = sess[pos], r["trade_date"]
    if td != otd:
        offset = int(sess.get_loc(td)) - pos if td in sess else np.nan
        return (Q + "LECH_NGAY",
                f"engine áp ngày {td.date()}, ngày không hưởng quyền chính thức {off.date()} (phiên {otd.date()}); "
                f"lệch {offset:+d} phiên" if offset == offset else f"engine áp ngày {td.date()} khác phiên {otd.date()}",
                otd, offset)
    if r["status"] == "KHONG_KHOP":
        return Q + "GIA_KHONG_KHOP_TY_LE", "ngày và tỷ lệ khớp bản gốc nhưng bước giá không giải thích được bằng tỷ lệ", otd, 0.0
    if r["status"] not in VERIFIABLE:
        return (Q + "TRANG_THAI_ENGINE_KHONG_HOP_LE", f"trạng thái engine {r['status']} không nằm trong danh sách cho phép "
                f"{', '.join(VERIFIABLE)}", otd, 0.0)
    gap = _missing_sessions(r, close, td)
    if gap:
        return Q + "THIEU_GIA_TRUOC_NGAY_HUONG_QUYEN", gap, otd, 0.0
    bad_price = _price_problem(r, close, td)
    if bad_price:
        return bad_price[0], bad_price[1], otd, 0.0
    if r["status"] == "DA_NAM_TRONG_GIA_NGUON":
        pre = _pre_event_break(r, close, td)
        if pre:
            return Q + "GIA_GAY_TRUOC_NGAY_HUONG_QUYEN", pre, otd, 0.0
    return OK, "bản gốc ghim hợp lệ, ngày công bố hợp lệ, tỷ lệ và ngày áp dụng khớp", otd, 0.0


def _missing_sessions(r, close, td):
    """Lý do cách ly nếu mã thiếu giá ở một phiên bất kỳ của trục ngày panel trong [td − WINDOW_DAYS ngày lịch, td], hoặc None.

    Trục ngày là `close.index` (mọi ngày có ít nhất một mã có giá). Không lấp chỗ trống, không suy giá; chỉ từ chối chứng nhận."""
    win = close.index[(close.index >= td - pd.Timedelta(days=WINDOW_DAYS)) & (close.index <= td)]
    miss = win[close.loc[win, r["ticker"]].isna().to_numpy()]
    if not len(miss):
        return None
    return (f"thiếu giá {len(miss)}/{len(win)} phiên trên trục ngày của panel trong [{win[0].date()}, {td.date()}] "
            f"(phiên thiếu đầu {miss[0].date()}, cuối {miss[-1].date()}); không đo được bước giá quanh sự kiện")


def _pre_event_break(r, close, td):
    """Lý do cách ly nếu giá gốc có bước ngoài biên trong WINDOW_DAYS ngày lịch TRƯỚC phiên sự kiện, hoặc None.

    DA_NAM_TRONG_GIA_NGUON khẳng định MỌI giá trước ngày không hưởng quyền đã được nguồn điều chỉnh. Bước giá liên tục tại
    phiên sự kiện chưa chứng minh điều đó: nguồn có thể chỉ chia lại vài phiên liền trước (kho thật: TCB 2024-06-11..19 và
    VCB 2025-03-03..11, 7 phiên trước ngày không hưởng quyền HOSE — reports/PRICE_INTEGRITY_B1_20261121.md). Khi đó chuỗi
    còn bước gãy ngoài biên vài phiên trước sự kiện. Cổng không suy ngày hay hệ số từ bước đó; chỉ từ chối chứng nhận."""
    t = r["ticker"]
    ret, K = adjust.obs_returns(close[[t]])
    L = adjust.limits(close.index, [t])
    s = close[t].dropna()
    win = s.index[(s.index >= td - pd.Timedelta(days=WINDOW_DAYS)) & (s.index < td)]
    for d in win:
        x = ret.at[d, t]
        if pd.isna(x):
            continue
        k = K.at[d, t]
        up, dn = adjust.bands(L.at[d, t], k if pd.notna(k) else 1.0)
        if -dn <= x <= up:
            continue
        adj = (1 + x) * float(r["ratio"]) - 1
        n = int(((s.index >= d) & (s.index < td)).sum())
        hint = ("nhân tỷ lệ thì trong biên: dấu hiệu nguồn chỉ điều chỉnh một phần" if -dn <= adj <= up
                else "nhân tỷ lệ vẫn ngoài biên")
        return (f"engine báo giá nguồn đã chứa điều chỉnh, nhưng giá gốc có bước {x:+.2%} ngoài biên −{dn:.2%}/+{up:.2%} tại "
                f"{d.date()}, {n} phiên trước phiên sự kiện {td.date()} ({hint}); chưa chứng minh mọi giá trước sự kiện đã được "
                "nguồn điều chỉnh")
    return None


def verify_events(events, close, docs, *, evidence_root, as_of) -> pd.DataFrame:
    """Gắn trạng thái kiểm chứng cho từng sự kiện của `adjust.build_events`. Không đổi các cột gốc."""
    as_of = pd.Timestamp(as_of)
    recs, matched = [], []
    for r in events.to_dict("records"):
        r.update(verify_state=None, verify_reason="", evidence_id="", official_ex_date=pd.NaT,
                 official_trade_date=pd.NaT, session_offset=np.nan)
        d = None
        if r["type"] not in STOCK:
            r["verify_state"], r["verify_reason"] = NA_CASH, "sự kiện tiền mặt: chưa có bằng chứng ghim, không vào chuỗi kiểm chứng"
        elif r["status"] in NO_DATA:
            r["verify_state"], r["verify_reason"] = NA_NODATA, f"trạng thái engine {r['status']}: không có cửa sổ giá để so"
        else:
            d = _match(r["ticker"], r["ex_date"], r["type"], docs)
            if d is None:
                r["verify_state"], r["verify_reason"] = Q + "THIEU_BANG_CHUNG", "không có bản gốc ghim cho sự kiện này trong manifest"
            else:
                r["evidence_id"], r["official_ex_date"] = d.get("source_id", ""), _ts(d.get("official_ex_date"))
                r["verify_state"], r["verify_reason"], r["official_trade_date"], r["session_offset"] = \
                    _judge(r, d, close, evidence_root, as_of)
        recs.append(r)
        matched.append(d)
    # một bản gốc mà engine áp ở hơn một ngày: không bên nào được coi là đã kiểm. Khóa nhận dạng bản gốc gồm source_id
    # (nếu có) VÀ sha256 nội dung khai báo, nên một bản gốc thiếu source_id, hoặc cùng tệp khai hai source_id, vẫn bị bắt.
    def _keys(d):
        if d is None:
            return []
        return [("sid", v.strip()) if k == "source_id" else ("sha", v.strip().lower())
                for k in ("source_id", "sha256") if isinstance((v := d.get(k)), str) and v.strip()]

    by_doc: dict[tuple, set] = {}
    for r, d in zip(recs, matched):
        if pd.notna(r["trade_date"]):
            for k in _keys(d):
                by_doc.setdefault(k, set()).add(r["trade_date"])
    for r, d in zip(recs, matched):
        dates = set().union(*[by_doc.get(k, set()) for k in _keys(d)]) if d is not None else set()
        # Bước gãy trước sự kiện mà chính một ngày engine khác của cùng bản gốc gây ra thì chẩn đoán đúng là xung đột ngày.
        if r["verify_state"] in (OK, Q + "GIA_GAY_TRUOC_NGAY_HUONG_QUYEN") and len(dates) > 1:
            r["verify_state"] = Q + "XUNG_DOT_NGAY"
            r["verify_reason"] = ("cùng bản gốc nhưng engine áp ở nhiều ngày: "
                                  + ", ".join(sorted(str(x.date()) for x in dates)))
    out = pd.DataFrame(recs, columns=list(events.columns) + [c for c in NEW_COLS if c not in ("in_verified_chain", "taints")])
    # Phòng thủ hai lớp: vào chuỗi kiểm chứng chỉ khi trạng thái kiểm là OK VÀ trạng thái engine nằm trong danh sách cho phép.
    out["in_verified_chain"] = (out["verify_state"] == OK) & out["status"].isin(VERIFIABLE)
    # Đóng khi nghi ngờ: mọi sự kiện bị cách ly có ngày giao dịch đều nhiễm ô trước nó, trừ khi engine báo không có cửa sổ giá.
    # (Trạng thái engine chưa biết cũng nhiễm.)
    out["taints"] = (out["verify_state"].str.startswith(Q) & ~out["status"].isin(NO_DATA)
                     & out["trade_date"].notna())
    return out


def verified_factors(index, columns, ev):
    """Hệ số giá/chia tách của chuỗi kiểm chứng: cùng công thức `adjust.factors`, nhưng chỉ sự kiện đã kiểm và APPLIED."""
    e = ev.copy()
    e["status"] = np.where(e["in_verified_chain"] & (e["status"] == "APPLIED"), "APPLIED", "KHONG_VAO_CHUOI_KIEM_CHUNG")
    return adjust.factors(index, columns, e)


def taint_mask(index, columns, ev) -> pd.DataFrame:
    """True ở ô (ngày, mã) nằm TRƯỚC ngày giao dịch của một sự kiện bị cách ly có chỗ gãy dữ liệu thật."""
    m = pd.DataFrame(False, index=index, columns=columns)
    for r in ev[ev["taints"]].itertuples(index=False):
        if r.ticker in m.columns:
            m.loc[m.index < r.trade_date, r.ticker] = True
    return m


def coverage(ev, taint, window=252) -> dict:
    stock = ev[ev["type"].isin(STOCK)]
    w = taint.iloc[-window:] if len(taint) else taint
    return {"stock_events": int(len(stock)), "cash_events_not_assessed": int((ev["verify_state"] == NA_CASH).sum()),
            "by_state": {k: int(v) for k, v in stock["verify_state"].value_counts().sort_index().items()},
            "in_verified_chain": int(ev["in_verified_chain"].sum()),
            "tickers": int(taint.shape[1]), "tickers_tainted_in_window": int(w.any().sum()) if w.size else 0,
            "tainted_share_all": round(float(taint.values.mean()), 4) if taint.size else 0.0,
            "tainted_share_window": round(float(w.values.mean()), 4) if w.size else 0.0, "window_sessions": int(window)}


def _files_hash(root, rels):
    h = hashlib.sha256()
    for rel in rels:
        h.update(f"{rel}:{sha256_file(pathlib.Path(root) / rel)}\n".encode())
    return h.hexdigest()


DIGEST_COLS = ["ticker", "ex_date", "type", "ratio", "source", "source_status", "status", "trade_date", "verify_state",
               "verify_reason", "evidence_id", "official_ex_date", "official_trade_date", "session_offset",
               "in_verified_chain", "taints"]


def _canon(x):
    """Dạng JSON chuẩn, xác định của metadata văn bản (số numpy → số Python; giá trị lạ → chuỗi có kiểu)."""
    if isinstance(x, dict):
        return {str(k): _canon(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, (list, tuple)):
        return [_canon(v) for v in x]
    if isinstance(x, (bool, str)) or x is None:
        return x
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        v = float(x)
        return v if np.isfinite(v) else f"float:{v}"
    return f"{type(x).__name__}:{x}"


def derivation_manifest(*, root, cfg, as_of, docs, ev, code_commit, created_at=None) -> dict:
    """Manifest dẫn xuất theo ADR-0009 điều 2. `derivation_id` chỉ phụ thuộc đầu vào, không phụ thuộc `created_at`."""
    root = pathlib.Path(root)
    raw_rels = [p for p in [cfg["data"]["store"]] if (root / p).is_file()]
    d = root / cfg["data"]["store_dir"]
    raw_rels += sorted(str(p.relative_to(root)) for p in d.glob("*.csv")) if d.is_dir() else []
    ce = [cfg["corporate_actions"]["manual"], cfg["corporate_actions"]["yahoo_cache"]]
    ce = [p for p in ce if (root / p).is_file()]
    cfg_p = root / "config.yaml"
    # Toàn bộ metadata của từng văn bản (loại, ngày chính thức, tỷ lệ, path, mã, khóa chứng từ và mọi trường khác) được
    # ghi vào manifest để kiểm toán VÀ vào khóa derivation_id. Không chọn lọc trường: trường nào đổi thì định danh đổi.
    srcs = [_canon({k: v for k, v in d_.items() if not str(k).startswith("_")}) for d_ in docs]
    srcs.sort(key=lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False))
    core = ev[[c for c in DIGEST_COLS if c in ev.columns]].copy()
    for c in ("ex_date", "trade_date", "official_ex_date", "official_trade_date"):
        if c in core.columns:
            core[c] = pd.to_datetime(core[c], errors="coerce").dt.strftime("%Y-%m-%d")
    digest = hashlib.sha256(core.to_csv(index=False).encode()).hexdigest()
    m = {"derivation_id": "", "created_at": created_at, "as_of": str(pd.Timestamp(as_of).date()),
         "raw_snapshot_hash": _files_hash(root, raw_rels), "raw_snapshot_files": raw_rels, "code_commit": code_commit,
         "config_hash": sha256_file(cfg_p) if cfg_p.is_file() else "", "corporate_events_hash": _files_hash(root, ce),
         "source_documents": srcs, "events_verification_digest": digest,
         "validity_scope": "RETROSPECTIVE — dựng lại từ bản gốc đã ghim; không có vintage; không phải point-in-time đầy đủ (ADR-0009 điều 4)",
         "chain": "verified-adjusted: giá gốc + sự kiện cổ phiếu đã kiểm; KHÔNG điều chỉnh cổ tức tiền mặt", "supersedes": None}
    key = {k: m[k] for k in ("as_of", "raw_snapshot_hash", "code_commit", "config_hash", "corporate_events_hash",
                              "source_documents", "events_verification_digest")}
    m["derivation_id"] = "VA-" + hashlib.sha256(json.dumps(key, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    return m
