"""Sinh tất định reports/CORPORATE_ACTION_EVIDENCE_2026H2_20261119.md từ manifest 2026H2 và engine. Chỉ đọc kho.

Nguồn số: `data/evidence/corporate_actions/EVIDENCE_MANIFEST_2026H2.json` (bản gốc HOSE đã ghim) và
`engine.adjust.build_events` chạy trên kho giá chỉ-đọc với `data/corporate_actions.csv`, `data/derived/yahoo_actions.csv`
(cùng nguồn với `engine_rows()` của tests/test_corporate_action_evidence_2026h2.py). Không gọi mạng. Không ghi tệp nào
ngoài báo cáo. Không có dấu thời gian trong báo cáo, nên cùng dữ liệu thì cùng từng byte.

Dùng: python tools/corporate_action_evidence_2026h2.py            ghi báo cáo
      python tools/corporate_action_evidence_2026h2.py --check    so báo cáo trên đĩa với đầu ra; khác thì thoát 1
      python tools/corporate_action_evidence_2026h2.py --out P    ghi ra đường dẫn khác
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MANIFEST = ROOT / "data" / "evidence" / "corporate_actions" / "EVIDENCE_MANIFEST_2026H2.json"
REPORT = ROOT / "reports" / "CORPORATE_ACTION_EVIDENCE_2026H2_20261119.md"
TOOL = "tools/corporate_action_evidence_2026h2.py"


def fmt(value) -> str:
    """Số thập phân ngắn, dấu phẩy, đúng giá trị float đã đọc (cùng cách viết với test)."""
    text = format(float(value), ".12f").rstrip("0").rstrip(".")
    return text.replace(".", ",")


def ratio_cell(official, engine) -> str:
    left, right = fmt(official), fmt(engine)
    return f"{left} = {right}" if abs(float(official) - float(engine)) <= 1e-12 else f"{left} khác {right}"


def docs(path=MANIFEST) -> list[dict]:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))["source_documents"]


def engine_rows(documents) -> dict:
    """{(mã, ngày không hưởng quyền trên văn bản): dòng cổ phiếu của engine hoặc None}. Chỉ đọc kho."""
    import pandas as pd

    from engine import adjust, data

    store = data.load_store()
    raw = store.pivot(index="date", columns="ticker", values="close").sort_index()
    observed = store.pivot(index="date", columns="ticker", values="observed_at").sort_index()
    events = adjust.build_events(raw, observed, adjust.load_manual(), adjust.load_yahoo())
    stock = events[events["type"].isin(adjust.STOCK)]
    out = {}
    for d in documents:
        key = (d["ticker"], d["official_ex_date"])
        hit = stock[(stock.ticker == key[0]) & (stock.ex_date == pd.Timestamp(key[1]))]
        if len(hit) != 1:
            out[key] = None
            continue
        row = hit.iloc[0]
        sessions = raw[key[0]].dropna().index
        pos = int(sessions.searchsorted(pd.Timestamp(key[1])))
        out[key] = {"type": str(row.type), "ratio": float(row.ratio), "status": str(row.status),
                    "source": str(row.source), "trade_date": str(row.trade_date.date()),
                    "offset": int(sessions.get_loc(row.trade_date)) - pos}
    return out


def _posted(doc, root=ROOT):
    """ISO 8601 (không múi giờ) của data.postedDate trong JSON tin HOSE đã ghim cạnh bản gốc, hoặc None."""
    nid = doc["source_id"].split("-", 1)[1]
    p = pathlib.Path(root) / pathlib.Path(doc["path"]).parent / f"hose_news_{nid}.json"
    if not p.is_file():
        return None
    sec = json.loads(p.read_bytes()).get("data", {}).get("postedDate")
    if not isinstance(sec, int):
        return None
    return dt.datetime.fromtimestamp(sec, dt.timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")


def unverified_reason(doc, root=ROOT) -> str:
    posted = _posted(doc, root)
    if posted and posted[:10] == doc["signed_date"]:
        return f"HOSE đăng {posted} theo data.postedDate, cùng ngày ký; luật D1 không điền"
    if posted:
        return f"HOSE đăng {posted} theo data.postedDate nhưng manifest chưa ghi; xem published_at_note"
    return "chưa ghim metadata tin HOSE"


def _cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def render(documents=None, rows=None, root=ROOT) -> str:
    documents = docs() if documents is None else documents
    rows = engine_rows(documents) if rows is None else rows
    n = len(documents)
    pub = [d for d in documents if d.get("published_at")]
    unpub = [d for d in documents if not d.get("published_at")]
    reasons: dict[str, list[str]] = {}
    for d in unpub:
        r = unverified_reason(d, root)
        key = "HOSE đăng cùng ngày ký" if "cùng ngày ký" in r else r
        reasons.setdefault(key, []).append(f"{d['ticker']} {d['source_id']}")
    lines = [
        f"> Tệp do `{TOOL}` sinh tất định từ manifest và engine; không sửa tay. Tên tệp giữ ngày lập ban đầu (19/11/2026); "
        "nội dung là số liệu tại lần sinh gần nhất. Kiểm bằng `--check`.",
        "",
        "# Bằng chứng sự kiện quyền cổ phiếu 11/2025–11/2026",
        "",
        "Chỉ số liệu đọc từ thông báo HOSE đã ghim sha256 trong `data/evidence/corporate_actions/EVIDENCE_MANIFEST_2026H2.json`, "
        "và từ `engine.adjust.build_events` chạy trên kho giá chỉ-đọc cùng `data/corporate_actions.csv` và "
        "`data/derived/yahoo_actions.csv`. Không ghi kho. Không lấy ngày hay tỷ lệ từ báo chí. Không khuyến nghị sửa engine.",
        "",
        f"Ngày ký là ngày in trên văn bản (`signed_date`), không phải ngày HOSE đăng. Trong {n} văn bản, {len(pub)} văn bản có "
        "ngày công bố (`published_at`, trạng thái DA_XAC_MINH) lấy từ `data.postedDate` của tin HOSE đã ghim cạnh bản gốc, viết "
        f"ISO 8601 không gắn múi giờ vì JSON không ghi múi giờ. {len(unpub)} văn bản CHƯA XÁC MINH"
        + ("." if not unpub else ": " + "; ".join(f"{k} ({', '.join(v)})" for k, v in reasons.items()) + "."),
        "",
        "Nguyên văn loại sự kiện giữ ở `event_type_verbatim`. Trường `event_type` để trống; lớp của văn bản do bảng đóng "
        "`STOCK_VERBATIM` trong `engine.verified_adjust` quyết định (ADR-0016 QĐ-2, QĐ-2a). Cột «Loại engine» là nguồn, nhãn "
        "loại và trạng thái mà engine đang đọc, không phải loại đã xác minh của văn bản.",
        "",
        "Hệ số văn bản = (cổ cũ + cổ mới) / cổ cũ. Hai phần cổ phiếu được nhận không phải trả tiền trên cùng gốc thì cộng, "
        "không nhân. Quyền mua phải trả tiền và cổ tức bằng tiền không đưa vào hệ số. «khác» là so đúng giá trị số đã đọc; cổng "
        "verified-adjusted so ở 7 chữ số thập phân. Lệch phiên = vị trí ngày engine trừ vị trí ngày trên văn bản, trên các phiên "
        "của mã đó trong kho.",
        "",
        "`APPLIED`: engine đang áp hệ số lên giá gốc. `DA_NAM_TRONG_GIA_NGUON`: engine kết luận giá yahoo đã chứa điều chỉnh, "
        "không áp lại. Cả hai đều không phải đã kiểm chứng.",
        "",
        "| Sự kiện | Bản gốc | Ngày ký | Ngày công bố | Ngày engine | Lệch phiên | Hệ số văn bản so với hệ số engine | Loại engine | Ghi chú |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for d in documents:
        key = (d["ticker"], d["official_ex_date"])
        info = rows.get(key)
        published = d["published_at"] if d.get("published_at") else f"CHƯA XÁC MINH ({unverified_reason(d, root)})"
        if info is None:
            engine = ["không có dòng cổ phiếu", "—", fmt(d["official_ratio"]) + " (engine không có)", "—"]
        else:
            engine = [info["trade_date"], f"lệch {info['offset']}", ratio_cell(d["official_ratio"], info["ratio"]),
                      f"{info['source']} {info['type']} {info['status']}"]
        cells = [f"{key[0]} {key[1]}", d["source_id"], d["signed_date"], published] + engine + [d.get("note") or ""]
        lines.append("| " + " | ".join(_cell(c) for c in cells) + " |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPORT))
    ap.add_argument("--check", action="store_true", help="chỉ so với tệp trên đĩa; khác thì thoát 1, không ghi")
    a = ap.parse_args(argv)
    text = render()
    out = pathlib.Path(a.out)
    if a.check:
        same = out.is_file() and out.read_text(encoding="utf-8") == text
        print("KHỚP" if same else f"KHÁC: {out} không bằng đầu ra của {TOOL}")
        return 0 if same else 1
    out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
