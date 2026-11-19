"""Dựng bản dẫn xuất 'verified-adjusted' (ADR-0009) RA THƯ MỤC `--out`, không ghi vào kho.

Đọc kho giá gốc, sự kiện quyền (nhập tay và Yahoo) và các EVIDENCE_MANIFEST.json; chạy cổng bằng chứng
(`engine/verified_adjust.py`); ghi: manifest.json (derivation_id, hash đầu vào, nguồn gốc), events_verification.csv,
taint_by_ticker.csv, before_after.md (đối chiếu chuỗi hiện hành với chuỗi kiểm chứng, ADR-0009 điều 5).

Không sửa kho raw, không gọi `data.write_derived`, không gọi mạng.

Chính sách đầu ra (ADR-0009 điều 6, không ghi đè bản dẫn xuất đã xuất):
  - `--out` phải nằm NGOÀI kho: từ chối mọi đường bên trong thư mục mã (REPO) và thư mục dữ liệu (TTC_HOME), kể cả
    `reports/`, và kể cả khi đi vòng qua liên kết tượng trưng;
  - `--out` phải CHƯA tồn tại (tệp, thư mục rỗng hay thư mục đã có bản dẫn xuất đều bị từ chối). Thư mục được tạo nguyên tử
    (`mkdir` không `exist_ok`) và từng tệp được mở ở chế độ tạo-mới (`x`), nên không có đường nào ghi đè tệp đã có.
  Muốn dựng lại thì xuất ra thư mục mới; hai bản cũ/mới được so bằng `derivation_id`, không đè lên nhau.
Từ chối thì thoát mã 2, không tạo gì. Cùng đầu vào và cùng `--created-at` cho ra cùng từng byte. Dùng: python tools/build_verified_derivation.py --out DIR
[--as-of YYYY-MM-DD] [--evidence MANIFEST ...] [--created-at ISO] [--code-commit SHA]"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pandas as pd

from engine import adjust, data, verified_adjust as va
from engine.config import CFG, REPO, ROOT

DEFAULT_EVIDENCE = ["data/evidence/corporate_actions/EVIDENCE_MANIFEST.json"]
HORIZONS = (20, 60, 120, 252)
OUT_FILES = ("manifest.json", "events_verification.csv", "taint_by_ticker.csv", "before_after.md")


def out_is_protected(out: pathlib.Path) -> str | None:
    """Lý do từ chối `--out`, hoặc None nếu được phép. Không tạo, không sửa gì."""
    if out.is_symlink() or out.exists():
        return f"{out} đã tồn tại; không ghi đè bản dẫn xuất (ADR-0009 điều 6). Chọn thư mục mới chưa có."
    res = out.resolve()
    for name, base in (("thư mục dữ liệu TTC_HOME", ROOT.resolve()), ("thư mục mã của kho", REPO.resolve())):
        try:
            rel = res.relative_to(base)
        except ValueError:
            continue
        where = rel.parts[0] if rel.parts else "."
        return f"{res} nằm trong {name} ({where}); bản dẫn xuất chỉ được xuất ra ngoài kho"
    return None


def _create(path: pathlib.Path):
    """Mở tệp ở chế độ tạo-mới: lỗi nếu tệp đã có, không bao giờ ghi đè."""
    return open(path, "x", encoding="utf-8", newline="")


def _horizon_returns(adj, n):
    a = adj.ffill(limit=5)
    return a.iloc[-1] / a.iloc[-1 - n] - 1 if len(a) > n else pd.Series(dtype=float)


def build(out, as_of, evidence, created_at, code_commit):
    s = data.load_store()
    if s.empty:
        raise RuntimeError("kho giá trống")
    as_of = pd.Timestamp(as_of) if as_of else s.date.max()
    s = s[s.date <= as_of]
    raw = s.pivot(index="date", columns="ticker", values="close").sort_index()
    obs = s.pivot(index="date", columns="ticker", values="observed_at").sort_index()
    keep = raw.columns[raw.notna().sum() > 250]
    raw, obs = raw[keep], obs[keep]
    events = adjust.build_events(raw, obs, adjust.load_manual(), adjust.load_yahoo())
    docs = va.load_evidence([ROOT / p if not pathlib.Path(p).is_absolute() else p for p in evidence])
    ev = va.verify_events(events, raw, docs, evidence_root=ROOT, as_of=as_of)
    F_d, _ = adjust.factors(raw.index, raw.columns, events)
    F_v, _ = va.verified_factors(raw.index, raw.columns, ev)
    taint = va.taint_mask(raw.index, raw.columns, ev)
    cov = va.coverage(ev, taint)
    man = va.derivation_manifest(root=ROOT, cfg=CFG, as_of=as_of, docs=docs, ev=ev, code_commit=code_commit, created_at=created_at)
    man["coverage"] = cov
    man["evidence_manifests"] = sorted(pathlib.Path(p).name for p in evidence if (ROOT / p).is_file())

    out.mkdir(parents=True, exist_ok=False)        # nguyên tử: lỗi nếu thư mục xuất hiện giữa lúc kiểm và lúc ghi
    with _create(out / "manifest.json") as f:
        f.write(json.dumps(man, ensure_ascii=False, indent=2, sort_keys=True))
    cols = ["ticker", "ex_date", "type", "source", "source_status", "ratio", "status", "trade_date", "verify_state",
            "verify_reason", "evidence_id", "official_ex_date", "official_trade_date", "session_offset", "in_verified_chain"]
    with _create(out / "events_verification.csv") as f:
        ev[cols].sort_values(["ticker", "ex_date", "type"]).to_csv(f, index=False, date_format="%Y-%m-%d")
    w = taint.iloc[-252:]
    t = pd.DataFrame({"ticker": taint.columns, "tainted_cells_window": w.sum().values, "window_cells": len(w),
                      "tainted_cells_all": taint.sum().values, "all_cells": len(taint)})
    q = ev[ev["taints"]]
    last = {k: str(pd.Timestamp(v).date()) for k, v in q.groupby("ticker")["trade_date"].max().items()}
    cnt = {k: int(v) for k, v in q.groupby("ticker").size().items()}
    t["last_quarantined_event_trade_date"] = [last.get(k, "") for k in t["ticker"]]
    t["quarantined_stock_events"] = [cnt.get(k, 0) for k in t["ticker"]]
    with _create(out / "taint_by_ticker.csv") as f:
        t.sort_values("ticker").to_csv(f, index=False)

    lines = [f"# Đối chiếu trước/sau — chuỗi hiện hành và chuỗi kiểm chứng (as_of {as_of.date()})", "",
             f"derivation_id `{man['derivation_id']}`; mã commit `{code_commit}`; bằng chứng nạp: {len(docs)} bản gốc từ "
             f"{man['evidence_manifests'] or 'không có manifest nào'}.", "",
             "Chuỗi kiểm chứng = giá gốc + sự kiện cổ phiếu đã kiểm. Không điều chỉnh cổ tức tiền mặt. Không suy ngày đúng từ giá.", "",
             "## Bao phủ", "",
             f"- Sự kiện cổ phiếu: {cov['stock_events']}; vào chuỗi kiểm chứng: {cov['in_verified_chain']}; "
             f"sự kiện tiền mặt chưa xét: {cov['cash_events_not_assessed']}.",
             f"- Theo trạng thái: {cov['by_state']}.",
             f"- Ô giá bị cách ly (TAINTED): {cov['tainted_share_all']:.1%} toàn lịch sử; {cov['tainted_share_window']:.1%} trong "
             f"{cov['window_sessions']} phiên gần nhất; {cov['tickers_tainted_in_window']}/{cov['tickers']} mã có ô bị cách ly trong cửa sổ đó.", "",
             "## Số dòng và hệ số", "",
             f"- Chuỗi hiện hành áp {int((events.status == 'APPLIED').sum())} sự kiện (cổ phiếu + tiền mặt); chuỗi kiểm chứng áp "
             f"{int((ev.in_verified_chain & (ev.status == 'APPLIED')).sum())}.",
             f"- Số ngày × mã: {raw.shape[0]} × {raw.shape[1]}; số dòng giá gốc không đổi (module không sửa kho)."]
    diffs = {n: (_horizon_returns(raw * F_v, n) - _horizon_returns(raw * F_d, n)).abs() for n in HORIZONS}
    unv = ev[ev["type"].isin(va.STOCK) & (ev["status"] == "APPLIED") & ~ev["in_verified_chain"]]
    lines += ["", "## Sự kiện cổ phiếu engine đang áp (APPLIED) nhưng chưa vào chuỗi kiểm chứng", ""]
    for r in unv.sort_values(["trade_date", "ticker"]).itertuples():
        lines.append(f"- {r.ticker} ngày áp {pd.Timestamp(r.trade_date).date()} tỷ lệ {r.ratio} ({r.source}, {r.source_status}) → "
                     f"{r.verify_state}")
    if unv.empty:
        lines.append("- Không có.")
    lines += ["", "## Lợi suất tại as_of: chênh giữa hai chuỗi", ""]
    for n, d in diffs.items():
        start = raw.index[-1 - n] if len(raw) > n else raw.index[0]
        by_stock = sorted({r.ticker for r in unv.itertuples() if r.trade_date > start} & set(d[d > 1e-9].index))
        cash_only = sorted(set(d[d > 1e-9].index) - set(by_stock))
        lines.append(f"- {n} phiên: {int((d > 1e-9).sum())}/{len(d)} mã chênh; chênh lớn nhất {float(d.max()) if len(d) else 0.0:.6f}. "
                     f"Có sự kiện cổ phiếu engine đang áp nhưng chưa kiểm trong cửa sổ: {by_stock or 'không'}; "
                     f"chỉ chênh do cổ tức tiền mặt chưa vào chuỗi kiểm chứng: {len(cash_only)} mã.")
    lines += ["", "## Sự kiện có bản gốc ghim", ""]
    have = ev[ev.evidence_id != ""]
    if have.empty:
        lines.append("- Không sự kiện nào khớp bản gốc ghim trong lần dựng này.")
    for r in have.sort_values(["ticker", "ex_date"]).itertuples():
        lines.append(f"- {r.ticker} ex_date engine {pd.Timestamp(r.ex_date).date()} ({r.source}, engine {r.status}) → "
                     f"**{r.verify_state}** — {r.verify_reason}")
    lines += ["", "## Giới hạn", "",
              "- Chưa nối vào vòng học hay `data.sources` (ADR-0009 điều 7). Không phải bản dẫn xuất được công bố.",
              "- Nhãn RETROSPECTIVE: không có vintage, không tuyên bố point-in-time đầy đủ.", ""]
    with _create(out / "before_after.md") as f:
        f.write("\n".join(lines))
    return man


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--as-of")
    ap.add_argument("--evidence", action="append")
    ap.add_argument("--created-at")
    ap.add_argument("--code-commit")
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    why = out_is_protected(out)
    if why:
        print("TỪ CHỐI:", why, file=sys.stderr)
        return 2
    commit = a.code_commit
    if not commit:
        r = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True)
        commit = r.stdout.strip() if r.returncode == 0 else "UNKNOWN"
    created = a.created_at or pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        man = build(out, a.as_of, a.evidence or DEFAULT_EVIDENCE, created, commit)
    except FileExistsError as e:
        print("TỪ CHỐI:", f"{e.filename} đã tồn tại; không ghi đè bản dẫn xuất (ADR-0009 điều 6)", file=sys.stderr)
        return 2
    print(f"{man['derivation_id']}: {man['coverage']['in_verified_chain']} sự kiện vào chuỗi kiểm chứng; "
          f"{man['coverage']['tainted_share_window']:.1%} ô cách ly trong cửa sổ gần nhất; ghi vào {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
