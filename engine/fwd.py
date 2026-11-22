"""Sổ FWD theo phiên (F1b; QĐ-11, QĐ-11a, QĐ-5a của ADR-0016): ba sổ đối chứng FWD-EW, FWD-HOLD, FWD-CASH; sổ bóng FWD-S1,
FWD-S2 chỉ chạy khi có hàm chấm điểm truyền vào (F1c làm phần đó).

Chưa đăng ký — không có dòng `kind: "forward_test"` với `trial_id` bằng mã phép thử trong research/trial_registry.jsonl — thì
`run` chỉ đọc tệp sổ đăng ký rồi trả None: không tạo tệp, không ghi dòng nào.

Đã đăng ký: thư mục paper/fwd/<trial_id>/ gồm state.json và năm tệp CSV chỉ ghi thêm (cột ở COLS):
  - nav.csv: NAV cuối phiên từng sổ; `stale` = mã đang giữ được định giá theo giá gốc gần nhất (STALE_PRICE);
  - trades.csv: BUY, SELL, CASH_DIVIDEND, STOCK_ADJUST (kèm khóa sự kiện `event`, giá trị đã áp `value`, cờ CA_UNVERIFIED,
    CA_LATE), và lệnh không khớp: UNFILLED_LIMIT_UP, UNFILLED_LIMIT_DOWN, STALE_PRICE, UNFILLED_RISK_GATE;
  - decisions.csv: DECIDE (danh mục mục tiêu từng sổ và dữ liệu lúc quyết định, QĐ-11a mục 8), LATE_VOID, D0_LATE,
    VERIFY_WAIT, WAIT_PRICES, DRAWDOWN_BREACH, PIT_REJECTED, SPEC_INVALID, ERROR;
  - periods.csv: mỗi kỳ một dòng (k, phiên quyết định, phiên khớp, SEALED hoặc LATE_VOID);
  - drawdown.csv: sụt giảm từng phiên từng sổ (hàm thuần risk_gate.drawdown_path, chế độ chỉ ghi nhận).

Luật (mục của QĐ-11a trong ngoặc):
  - Đầu vào: data.load_market(as_of, research_input="verified", universe="historical", sessions="calendar"). Nhãn phải là
    "PIT_MODES_ONLY" (Owner xác nhận 22/11/2026, gói 4 đã sửa: F1b dùng nhãn này); khác thì ghi PIT_REJECTED, không xử lý
    phiên nào. "Đủ điều kiện" tại phiên s là `eligible` tại s.
  - Phiên (1): risk_gate.session_axis(ngày của kho giá, lịch, until=as_of), bỏ ngày CHUA_CO_THONG_BAO và ngày ngoài vùng lịch
    mà không thành viên rổ nào có giá (danh sách của load_market). Có giá = dòng giá với khối lượng > 0.
  - Tuần tự từng phiên sau phiên đã xử lý gần nhất (2): xác minh niêm phong quyết định phiên trước → sự kiện quyền cho vị thế
    giữ từ trước phiên → khớp → định giá → đo sụt giảm → quyết định (chỉ ở phiên tái cơ cấu). Mỗi phiên ghi xong mới lưu
    state.json, nên lần chạy dừng giữa chừng không ghi trùng.
  - Niêm phong lúc khớp (3): lệnh của quyết định phiên t chỉ khớp ở đóng cửa phiên t+1, khi hàm xác minh (mặc định
    `github_run`, API GitHub) cho biết lượt chạy ghi quyết định là `.github/workflows/daily_cycle.yml` trên `main`, sự kiện
    `schedule` hoặc `workflow_dispatch`, kết luận `success`, kết thúc trước hạn (seal_deadline_local, giờ VN) của phiên t+1.
    Không xác minh được (lỗi API, lượt chưa xong) → VERIFY_WAIT, dừng trước t+1, thử lại lần chạy sau. Lượt không hợp lệ
    hoặc trễ → LATE_VOID: không sổ nào đổi danh mục theo quyết định đó.
  - Khóa biên độ: paper.locked trên bảng giá đã điều chỉnh của chế độ verified (hệ số va.verified_factors như load_market),
    trên trục phiên, không che theo rổ (mã rời rổ vẫn được xét khi bán); lệnh không khớp thử lại phiên sau.
  - Không quyết định muộn (4): phiên tái cơ cấu (D0 thực tế + period_sessions × k) chỉ ra quyết định khi là phiên mới nhất có
    giá trong kho; không thì LATE_VOID, không quyết định bù. Robot tự từ chối quyết định khi giờ máy chạy đã qua hạn.
  - Thiếu giá (5): mã không có giá ở phiên s → định giá theo giá gốc gần nhất, `stale` trong nav.csv; lệnh của mã đó ghi
    STALE_PRICE và thử lại. Phiên không thành viên nào có giá → WAIT_PRICES, dừng trước phiên đó.
  - Sự kiện quyền (6): bảng sự kiện của engine (adjust.build_events, trạng thái APPLIED), như sổ giấy. Cơ sở là số cổ phiếu
    nắm giữ trước phiên giao dịch không hưởng quyền (dựng từ trades.csv), nên cổ phiếu mua ở đóng cửa phiên đó không hưởng.
    Cổ tức tiền: cơ sở × tiền mỗi cổ phiếu × (1 − thuế cổ tức). Sự kiện cổ phiếu: thêm int(cơ sở × hệ số) − cơ sở cổ phiếu;
    chưa vào chuỗi kiểm chứng → CA_UNVERIFIED. Sự kiện biết muộn (ngày giao dịch không hưởng quyền trước phiên đang xử lý)
    áp ở phiên đang xử lý, ghi CA_LATE.
  - Sụt giảm: chạm drawdown_record → DRAWDOWN_BREACH (một dòng mỗi lần đi vào vùng chạm ngưỡng); không khóa, không bán (QĐ-5a).
  - Kỳ, D0 (9): D0 thực tế là phiên quyết định đầu tiên từ D0 đã đăng ký được niêm phong đúng hạn; D0 trễ (D0_LATE) thì dời
    sang phiên kế. Phép thử có `periods` kỳ: quyết định k = 0…periods; xong phiên khớp của kỳ cuối thì dừng.
  - Ba sổ đối chứng (mục 1, 2 của giao thức): FWD-EW chia đều cho mọi mã đủ điều kiện, tái cơ cấu mỗi kỳ về đúng phần vốn
    mỗi mã; FWD-HOLD mua chia đều tại D0, sau đó chỉ bán mã rời rổ, tiền bán giữ tiền mặt, không mua mã mới; FWD-CASH giữ
    tiền mặt. Mỗi mã mục tiêu nhận min(NAV / số mã, max_weight × NAV) × buy_budget ở phiên khớp; lô `lot_size`; phí, thuế,
    trượt giá theo `costs`. Bán trước, mua sau; mua giới hạn bởi tiền mặt.
  - Cổng R1a (QĐ-5a): risk_gate.check lúc quyết định và lúc khớp lệnh mua, cùng ngữ nghĩa với paper.run (FAIL lúc quyết định
    → mục tiêu = vị thế đang giữ; mã bị loại không mua; FAIL lúc khớp → không mua mã nào; mã bị từ chối không thử lại). Sổ
    FWD không có trạng thái đóng băng dữ liệu: cổng nhận frozen=False.
`replay(root, spec, until)` dựng lại các sổ từ D0 chỉ bằng danh mục mục tiêu đã ghi (DECIDE), periods.csv, các dòng áp sự
kiện đã ghi, giá trong kho và luật trên; riêng cổng R1a ở phiên khớp dùng các dòng UNFILLED_RISK_GATE đã ghi (xem replay).
"""
from __future__ import annotations

import json
import math
import os
import pathlib
from datetime import datetime, timedelta, timezone

import pandas as pd

from . import adjust, config, data, paper, risk_gate
from . import verified_adjust as va

TEST_ID = "FWD-001"
CONTROL = ("FWD-EW", "FWD-HOLD", "FWD-CASH")
SHADOW = ("FWD-S1", "FWD-S2")
BOOKS = CONTROL + SHADOW
SHADOW_SIZE = 5
SPEC_KEYS = ("trial_id", "d0", "books", "capital", "period_sessions", "periods", "max_weight", "buy_budget",
             "drawdown_record", "seal_deadline_local", "s1", "s2", "train_input", "score_input", "protocol_sha256",
             "adr_commit")
REGISTRY = ("research", "trial_registry.jsonl")
DIR = ("paper", "fwd")
WORKFLOW = ".github/workflows/daily_cycle.yml"
RUN_EVENTS = ("schedule", "workflow_dispatch")
VN = timezone(timedelta(hours=7))
MARKET = {"research_input": "verified", "universe": "historical", "sessions": "calendar"}
PIT_REQUIRED = data.PIT_MODES_ONLY
COLS = {
    "nav.csv": ["date", "book", "nav", "cash", "n_positions", "stale"],
    "trades.csv": ["date", "book", "asset", "side", "quantity", "price", "fees", "event", "value", "flags"],
    "decisions.csv": ["date", "action", "book", "k", "run_id", "decided_at", "deadline", "vn30_history_sha256",
                      "trading_calendar_sha256", "derivation_id", "targets", "note"],
    "periods.csv": ["k", "decision_session", "fill_session", "status", "note"],
    "drawdown.csv": ["date", "book", "nav", "peak", "drawdown", "verified"],
}
CA_SIDES = ("CASH_DIVIDEND", "STOCK_ADJUST")


# ---------- đăng ký, đặc tả ----------

def load_registration(root, test_id):
    """Dòng `kind: "forward_test"` đầu tiên có `trial_id` bằng `test_id` trong research/trial_registry.jsonl, hoặc None (không
    có tệp, không có dòng). Chỉ đọc. Dòng không phải JSON bị bỏ qua (tính toàn vẹn của sổ đăng ký do L-06 kiểm)."""
    p = pathlib.Path(root).joinpath(*REGISTRY)
    if not p.is_file():
        return None
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if isinstance(r, dict) and r.get("kind") == "forward_test" and r.get("trial_id") == test_id:
            return r
    return None


def spec_problem(spec):
    """Lý do đặc tả không dùng được, hoặc None."""
    miss = [k for k in SPEC_KEYS if k not in spec]
    if miss:
        return f"đặc tả thiếu khóa {miss}"
    books = spec["books"]
    if (not isinstance(books, list) or len(set(books)) != len(books) or not set(CONTROL) <= set(books)
            or not set(books) <= set(BOOKS)):
        return f"books phải gồm {list(CONTROL)} và chỉ các sổ {list(BOOKS)}, có {books!r}"

    def real(v):
        return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
    if not (real(spec["capital"]) and spec["capital"] > 0):
        return f"capital không hợp lệ ({spec['capital']!r})"
    for k in ("max_weight", "buy_budget"):
        if not (real(spec[k]) and 0 < spec[k] <= 1):
            return f"{k} phải trong (0, 1], có {spec[k]!r}"
    if not (real(spec["drawdown_record"]) and 0 < spec["drawdown_record"] < 1):
        return f"drawdown_record phải trong (0, 1), có {spec['drawdown_record']!r}"
    for k in ("period_sessions", "periods"):
        if not (isinstance(spec[k], int) and not isinstance(spec[k], bool) and spec[k] >= 1):
            return f"{k} phải là số nguyên ≥ 1, có {spec[k]!r}"
    try:
        if _iso(spec["d0"]) != str(spec["d0"]):
            raise ValueError
        _deadline("2000-01-03", spec["seal_deadline_local"])
    except (ValueError, TypeError):
        return f"d0 ({spec['d0']!r}) phải là YYYY-MM-DD và seal_deadline_local ({spec['seal_deadline_local']!r}) là HH:MM"
    return None


# ---------- tiện ích ----------

def _iso(d):
    return str(pd.Timestamp(d).date())


def book_dir(root, trial_id):
    return pathlib.Path(root).joinpath(*DIR, trial_id)


def _append(d, name, rows):
    if not rows:
        return
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    pd.DataFrame(rows, columns=COLS[name]).to_csv(p, mode="a", header=not p.exists(), index=False)


def _read(d, name):
    p = d / name
    return pd.read_csv(p, dtype=str, keep_default_na=False) if p.exists() else pd.DataFrame(columns=COLS[name])


def _deadline(day, local):
    """Hạn niêm phong của phiên `day`: giờ `local` ("HH:MM") giờ Việt Nam."""
    hh, mm = str(local).split(":")
    if len(hh) != 2 or len(mm) != 2:
        raise ValueError(local)
    d = pd.Timestamp(day)
    return datetime(d.year, d.month, d.day, int(hh), int(mm), tzinfo=VN)


def _next_session(day, cal):
    """Phiên kế sau `day` theo lịch HOSE (ngày lịch phủ), ngoài vùng lịch theo thứ Hai–thứ Sáu."""
    d = pd.Timestamp(day)
    for i in range(1, 60):
        x = d + pd.Timedelta(days=i)
        flag = cal.get(_iso(x)) if cal else None
        if flag == 1 or (flag is None and x.weekday() < 5):
            return x
    raise ValueError(f"không tìm được phiên kế sau {_iso(d)}")


def _aware(x):
    if isinstance(x, datetime):
        return x if x.tzinfo is not None else x.replace(tzinfo=timezone.utc)
    t = pd.Timestamp(x)
    return (t if t.tzinfo is not None else t.tz_localize("UTC")).to_pydatetime()


def _drow(date, action, **kw):
    return {"date": date, "action": action, **kw}


# ---------- xác minh niêm phong ----------

def github_run(run_id):
    """Hàm xác minh mặc định: lượt chạy "<GITHUB_RUN_ID>.<GITHUB_RUN_ATTEMPT>" theo API GitHub → {finished_at, path, branch,
    event, conclusion}. Lượt chưa kết thúc hay lỗi mạng: ném lỗi (nơi gọi ghi VERIFY_WAIT)."""
    rid, _, att = str(run_id).partition(".")
    r = risk_gate.github_api(f"actions/runs/{rid}/attempts/{att}" if att else f"actions/runs/{rid}")
    if r.get("status") != "completed":
        raise RuntimeError(f"lượt chạy {run_id} chưa kết thúc (status {r.get('status')!r})")
    return {"finished_at": r.get("updated_at"), "path": r.get("path"), "branch": r.get("head_branch"),
            "event": r.get("event"), "conclusion": r.get("conclusion")}


def _seal(info, s, local):
    """→ ("SEALED" | "LATE_VOID", lý do). Thông tin thiếu giờ kết thúc (hay không phải dict): ném lỗi → VERIFY_WAIT."""
    if not isinstance(info, dict) or not info.get("finished_at"):
        raise ValueError(f"API không trả giờ kết thúc của lượt chạy ({info!r})")
    fin, dl = _aware(info["finished_at"]), _deadline(s, local)
    bad = []
    if str(info.get("path") or "").split("@")[0] != WORKFLOW:
        bad.append(f"workflow {info.get('path')!r} khác {WORKFLOW}")
    if info.get("branch") != "main":
        bad.append(f"nhánh {info.get('branch')!r} khác main")
    if info.get("event") not in RUN_EVENTS:
        bad.append(f"sự kiện {info.get('event')!r} không thuộc {list(RUN_EVENTS)}")
    if info.get("conclusion") != "success":
        bad.append(f"kết luận {info.get('conclusion')!r} khác success")
    if bad:
        return "LATE_VOID", "lượt chạy không hợp lệ: " + "; ".join(bad)
    if fin >= dl:
        return "LATE_VOID", f"lượt chạy kết thúc {fin.isoformat()} không trước hạn {dl.isoformat()}"
    return "SEALED", f"lượt chạy kết thúc {fin.isoformat()} trước hạn {dl.isoformat()}"


# ---------- dữ liệu thị trường của một lần chạy ----------

class _Ctx:
    """Dữ liệu CHỈ ĐỌC tới as_of: đầu vào verified/historical/calendar, giá và khối lượng GỐC của kho, danh sách phiên."""

    def __init__(self, root, as_of):
        self.root = pathlib.Path(root)
        if self.root.resolve() != pathlib.Path(config.ROOT).resolve():
            raise ValueError(f"root {self.root} khác config.ROOT {config.ROOT}: data.load_market đọc config.ROOT")
        t0 = pd.Timestamp(as_of)
        self.mk = data.load_market(_iso(t0), **MARKET)
        s = data.load_store(root=self.root)
        s = s[s.date <= t0]
        self.raw = s.pivot(index="date", columns="ticker", values="close").sort_index()
        vol = s.pivot(index="date", columns="ticker", values="volume").sort_index()
        self.cal = risk_gate.load_calendar(self.root)
        axis = risk_gate.session_axis(list(self.raw.index) if len(self.raw) else [t0], self.cal, until=t0)
        q = self.mk["quality"]["sessions"]
        off = {pd.Timestamp(d) for d in list(q["non_session_unannounced"]) + list(q["non_session_zero_volume"])}
        self.sessions = [d for d in axis if d not in off and d <= t0]
        idx = pd.DatetimeIndex(self.sessions)
        has = (self.raw > 0) & (vol > 0)                               # có giá: dòng giá với khối lượng > 0
        self.ok = has.reindex(index=idx, fill_value=False).fillna(False).astype(bool)
        self.last = self.raw.where(has).ffill().reindex(idx, method="ffill")   # giá gốc gần nhất ≤ phiên
        m = self.mk["members"].reindex(index=idx, columns=self.ok.columns, fill_value=False).fillna(False).astype(bool)
        self.session_ok = (self.ok & m).any(axis=1)
        priced = self.session_ok[self.session_ok]
        self.newest = priced.index[-1] if len(priced) else None
        self.events = self.mk.get("event_checks")
        # Bảng giá đã điều chỉnh của chế độ verified (cùng hệ số va.verified_factors với load_market) trên trục phiên, KHÔNG che
        # theo rổ: mã rời rổ vẫn cần biết khóa sàn khi bán.
        r = self.raw.reindex(idx)
        ev = self.events
        if ev is not None and len(ev):
            F, _ = va.verified_factors(idx, r.columns, ev[ev["ticker"].isin(r.columns)])
            r = r * F
        self.adj = r.ffill(limit=5)
        self._snap = {}

    def priced(self, t, s):
        return t in self.ok.columns and bool(self.ok.at[s, t])

    def price(self, t, s):
        v = self.last.at[s, t] if t in self.last.columns else float("nan")
        return float(v) if pd.notna(v) else None

    def eligible(self, s):
        e = self.mk.get("eligible")
        return [] if e is None or s not in e.index else sorted(c for c in e.columns if bool(e.at[s, c]))

    def members(self, s):
        m = self.mk["members"]
        return set() if s not in m.index else {c for c in m.columns if bool(m.at[s, c])}

    def locks(self, s):
        return paper.locked(self.adj, s)

    def market(self, s, tickers):
        key = (s, tuple(sorted(set(tickers))))
        if key not in self._snap:
            lim = config.CFG["paper"].get("risk_limits")
            snap = risk_gate.market_snapshot(s, list(key[1]), lim, root=self.root, frozen=False)
            snap["price"] = {t: p for t in key[1] if (p := self.price(t, s)) is not None}
            self._snap[key] = snap
        return self._snap[key]


# ---------- luật một sổ (dùng chung cho run và replay) ----------

def _value(bk, price):
    return bk["cash"] + sum(sh * price(t) for t, sh in bk["positions"].items())


def _apply_ca_row(bk, order, row):
    """Áp một dòng CASH_DIVIDEND / STOCK_ADJUST đã ghi lên sổ (và lệnh đang chờ của mã đó)."""
    if row["side"] == "CASH_DIVIDEND":
        bk["cash"] += float(row["value"])
        return
    t, n = row["asset"], bk["positions"].get(row["asset"], 0) + int(row["quantity"])
    if n:
        bk["positions"][t] = n
    else:
        bk["positions"].pop(t, None)
    if order and order["legs"].get(t, 0) > 0:
        order["legs"][t] = int(order["legs"][t] * float(row["value"]))


def _legs(book, k, targets, bk, nav, price, spec):
    """Lệnh của quyết định kỳ k đã niêm phong, tính ở phiên khớp → {mã: số cổ phiếu muốn giữ}, chỉ mã cần đổi."""
    c, lot = config.CFG["costs"], int(config.CFG["lot_size"])
    pos = bk["positions"]
    if book == "FWD-CASH":
        want = {}
    elif book == "FWD-HOLD" and k > 0:                  # chỉ bán mã rời rổ; không mua mới, không tái cân bằng
        want = {t: (sh if t in targets else 0) for t, sh in pos.items()}
    else:
        want = {t: 0 for t in pos if t not in targets}
        if targets:
            alloc = min(nav / len(targets), float(spec["max_weight"]) * nav) * float(spec["buy_budget"])
            for t in targets:
                if price(t) is None:                    # chưa từng có giá: không đặt lệnh
                    continue
                unit = price(t) * (1 + c["slippage"]) * (1 + c["buy_fee"])
                want[t] = int(alloc // unit) // lot * lot
    return {t: w for t, w in want.items() if w != pos.get(t, 0)}


def _fill(book, bk, order, s, ctx, rows, refused_by_gate=None):
    """Khớp lệnh `order` = {"targets", "legs"} của một sổ ở đóng cửa phiên s → lệnh còn chờ (thử lại phiên sau) hoặc None.
    refused_by_gate(sổ, phiên) → tập mã cổng R1a đã từ chối mua (replay đọc từ dòng UNFILLED_RISK_GATE đã ghi); None: chạy
    cổng (robot)."""
    c, lot = config.CFG["costs"], int(config.CFG["lot_size"])
    si, legs, targets = _iso(s), order["legs"], order["targets"]
    up, down = ctx.locks(s)
    still = {}

    def trade(t, side, qty=0, price=0.0, fees=0.0):
        rows.append({"date": si, "book": book, "asset": t, "side": side, "quantity": int(qty), "price": round(price, 2),
                     "fees": round(fees, 0), "event": "", "value": "", "flags": ""})
    for t in sorted(legs):                                          # bán trước
        held, want = bk["positions"].get(t, 0), legs[t]
        if want >= held:
            continue
        qty = held if want == 0 else (held - want) // lot * lot
        if qty <= 0:
            continue
        if not ctx.priced(t, s):
            trade(t, "STALE_PRICE", price=ctx.price(t, s) or 0.0)
            still[t] = want
            continue
        if t in down:
            trade(t, "UNFILLED_LIMIT_DOWN", price=ctx.price(t, s))
            still[t] = want
            continue
        p0 = ctx.price(t, s)
        p = p0 * (1 - c["slippage"])
        bk["cash"] += qty * p * (1 - c["sell_fee"] - c["sell_tax"])
        left = held - qty
        if left:
            bk["positions"][t] = left
        else:
            bk["positions"].pop(t)
        trade(t, "SELL", qty, p, qty * p0 * c["slippage"] + qty * p * (c["sell_fee"] + c["sell_tax"]))
    buys = [t for t in sorted(legs) if (legs[t] - bk["positions"].get(t, 0)) // lot * lot > 0]
    refused = set()
    if buys and refused_by_gate is not None:
        refused = set(buys) & set(refused_by_gate(book, si))
    elif buys:                      # R1a: lệnh mua qua lại cổng ở chính phiên khớp, sau lệnh bán, với mọi vị thế còn lại
        nav = _value(bk, lambda x: ctx.price(x, s))
        g = risk_gate.check(list(targets), {"nav": nav, "positions": dict(bk["positions"])},
                            ctx.market(s, list(targets) + list(bk["positions"])), config.CFG["paper"].get("risk_limits"))
        refused = set(buys) if g["verdict"] == "FAIL" else set(g["excluded"]) & set(buys)
    for t in buys:                  # mã bị cổng từ chối: không mua, không thử lại
        if t in refused:
            trade(t, "UNFILLED_RISK_GATE", price=ctx.price(t, s) or 0.0)
    buys = [t for t in buys if t not in refused]
    for t in buys:
        if not ctx.priced(t, s):
            trade(t, "STALE_PRICE", price=ctx.price(t, s) or 0.0)
            still[t] = legs[t]
            continue
        if t in up:
            trade(t, "UNFILLED_LIMIT_UP", price=ctx.price(t, s))
            still[t] = legs[t]
            continue
        p0 = ctx.price(t, s)
        unit = p0 * (1 + c["slippage"]) * (1 + c["buy_fee"])
        qty = min((legs[t] - bk["positions"].get(t, 0)) // lot * lot, int(bk["cash"] // unit) // lot * lot)
        if qty <= 0:
            continue
        bk["cash"] -= qty * unit
        bk["positions"][t] = bk["positions"].get(t, 0) + qty
        trade(t, "BUY", qty, p0 * (1 + c["slippage"]), qty * p0 * (c["slippage"] + c["buy_fee"]))
    return {"targets": list(targets), "legs": still} if still else None


# ---------- robot ----------

def _new_state(test_id, spec, books):
    cap = float(spec["capital"])
    return {"trial_id": test_id, "last": None, "anchor": None, "d0": None, "count": 0, "k": 0, "pending": None,
            "open": {}, "seen": [], "done": False,
            "books": {b: {"cash": cap, "positions": {}, "peak": cap, "peak_date": None, "in_breach": False}
                      for b in books}}


def _history(d):
    """{sổ: {mã: [(phiên, thay đổi số cổ phiếu)]}} từ trades.csv: cơ sở của sự kiện quyền."""
    h = {}
    t = _read(d, "trades.csv")
    for r in t.itertuples(index=False):
        _record(h, {"date": r.date, "book": r.book, "asset": r.asset, "side": r.side, "quantity": r.quantity})
    return h


def _record(h, row):
    sign = {"BUY": 1, "SELL": -1, "STOCK_ADJUST": 1}.get(row["side"])
    if sign:
        h.setdefault(row["book"], {}).setdefault(row["asset"], []).append((row["date"], sign * int(row["quantity"])))


def _held_before(h, book, t, day):
    return sum(q for d, q in h.get(book, {}).get(t, []) if d < day)


def _corporate_actions(st, ctx, s, books, hist, out):
    """Sự kiện quyền APPLIED có ngày giao dịch không hưởng quyền ≤ s, chưa xét lần nào (QĐ-11a mục 6)."""
    ev = ctx.events
    if ev is None or not len(ev):
        return
    si, seen = _iso(s), set(st["seen"])
    tax = float(config.CFG["costs"].get("dividend_tax", 0.0))
    cand = ev[(ev["status"] == "APPLIED") & ev["trade_date"].notna()]
    cand = cand[pd.to_datetime(cand["trade_date"]) <= s].sort_values(["trade_date", "ticker", "type"], kind="stable")
    for e in cand.itertuples(index=False):
        key = f"{e.ticker}|{_iso(e.ex_date)}|{e.type}"
        if key in seen:
            continue
        seen.add(key)
        te, stock = _iso(e.trade_date), e.type in adjust.STOCK
        flags = (["CA_LATE"] if te < si else []) + (["CA_UNVERIFIED"] if stock and not bool(e.in_verified_chain) else [])
        for b in books:
            base = _held_before(hist, b, e.ticker, te)
            if base <= 0:
                continue
            if stock:
                row = {"side": "STOCK_ADJUST", "quantity": int(base * float(e.ratio)) - base, "price": float(e.ratio),
                       "value": float(e.ratio)}
            else:
                row = {"side": "CASH_DIVIDEND", "quantity": base, "price": float(e.cash_per_share),
                       "value": round(base * float(e.cash_per_share) * (1 - tax), 2)}
            row.update(date=si, book=b, asset=e.ticker, fees=0, event=key, flags=";".join(flags))
            _apply_ca_row(st["books"][b], st["open"].get(b), row)
            _record(hist, row)
            out["trades.csv"].append(row)
    st["seen"] = sorted(seen)


def _targets(ctx, st, s, k, books, scorer):
    """Mục tiêu từng sổ ở phiên quyết định s (kỳ k), sau cổng R1a → ({sổ: [mã]}, ghi chú cổng)."""
    elig, members, notes, out = ctx.eligible(s), ctx.members(s), [], {}
    lim = config.CFG["paper"].get("risk_limits")
    for b in books:
        bk = st["books"][b]
        held = {t: sh for t, sh in bk["positions"].items() if sh}
        if b == "FWD-CASH":
            tg = []
        elif b == "FWD-EW" or (b == "FWD-HOLD" and k == 0):
            tg = list(elig)
        elif b == "FWD-HOLD":
            tg = sorted(t for t in held if t in members)
        else:
            tg = list(dict.fromkeys(t for t in scorer(b, _iso(s), list(elig)) if t in elig))[:SHADOW_SIZE]
        if tg:                      # R1a lúc quyết định: FAIL → giữ nguyên vị thế; mã bị loại không mua
            nav = _value(bk, lambda x: ctx.price(x, s))
            keep = {t: sh for t, sh in held.items() if t in tg}
            g = risk_gate.check(tg, {"nav": nav, "positions": keep}, ctx.market(s, tg + list(held)), lim)
            if g["verdict"] == "FAIL" or g["excluded"]:
                tg = sorted(held) if g["verdict"] == "FAIL" else [t for t in tg if t not in g["excluded"] or t in held]
                notes.append(f"{b}: cổng rủi ro {g['verdict']}: " + "; ".join(g["reasons"]))
        out[b] = sorted(tg)
    return out, notes


def run(as_of, root=None, test_id=TEST_ID, verify=None, scorer=None, now=None, run_id=None):
    """Xử lý sổ FWD của `test_id` tới phiên as_of. Chưa đăng ký → None, không đọc thêm, không ghi gì.
    verify(run_id) → thông tin lượt chạy (mặc định github_run); scorer(sổ, phiên, mã đủ điều kiện) → mã xếp theo điểm giảm dần
    (None: không chạy sổ bóng); now: giờ máy chạy (mặc định đồng hồ máy); run_id mặc định GITHUB_RUN_ID.GITHUB_RUN_ATTEMPT."""
    root = pathlib.Path(root) if root is not None else pathlib.Path(config.ROOT)
    spec = load_registration(root, test_id)
    if spec is None:
        return None
    d, t0 = book_dir(root, test_id), _iso(as_of)
    try:
        return _run(spec, d, root, test_id, t0, verify or github_run, scorer,
                    _aware(now) if now is not None else datetime.now(timezone.utc),
                    run_id if run_id is not None else (f"{os.environ['GITHUB_RUN_ID']}."
                                                       f"{os.environ.get('GITHUB_RUN_ATTEMPT') or '1'}"
                                                       if os.environ.get("GITHUB_RUN_ID") else None))
    except Exception as e:                  # noqa: BLE001 — ghi lỗi vào sổ; phiên dở dang không được lưu
        _append(d, "decisions.csv", [_drow(t0, "ERROR", note=f"{type(e).__name__}: {str(e)[:300]}")])
        return {"trial_id": test_id, "processed": [], "stopped": "ERROR", "error": f"{type(e).__name__}: {e}"}


def _run(spec, d, root, test_id, t0, verify, scorer, now, run_id):
    why = spec_problem(spec)
    if why:
        _append(d, "decisions.csv", [_drow(t0, "SPEC_INVALID", note=why)])
        return {"trial_id": test_id, "processed": [], "stopped": "SPEC_INVALID"}
    p_state = d / "state.json"
    books = [b for b in BOOKS if b in spec["books"] and (b in CONTROL or scorer is not None)]
    st = json.loads(p_state.read_text(encoding="utf-8")) if p_state.exists() else _new_state(test_id, spec, books)
    if st.get("done"):
        return {"trial_id": test_id, "processed": [], "stopped": "DONE"}
    for b in books:
        st["books"].setdefault(b, _new_state(test_id, spec, [b])["books"][b])
    ctx = _Ctx(root, t0)
    if ctx.mk["pit_label"] != PIT_REQUIRED:
        _append(d, "decisions.csv", [_drow(t0, "PIT_REJECTED", derivation_id=ctx.mk.get("derivation_id", ""),
                                           note=f"pit_label {ctx.mk['pit_label']!r} khác {PIT_REQUIRED!r}: không xử lý phiên "
                                                f"nào; " + "; ".join(ctx.mk.get("pit_gaps") or []))])
        return {"trial_id": test_id, "processed": [], "stopped": "PIT_REJECTED"}
    hashes = {"vn30_history_sha256": va.sha256_file(root / data.VN30_HISTORY),
              "trading_calendar_sha256": va.sha256_file(root.joinpath(*risk_gate.CALENDAR))
              if root.joinpath(*risk_gate.CALENDAR).is_file() else ""}
    hist, done, stopped = _history(d), [], None
    period, n_periods, local = int(spec["period_sessions"]), int(spec["periods"]), spec["seal_deadline_local"]
    todo = [s for s in ctx.sessions if s >= pd.Timestamp(spec["d0"])
            and (st["last"] is None or s > pd.Timestamp(st["last"]))]
    for s in todo:
        si = _iso(s)
        if not bool(ctx.session_ok.get(s, False)):
            _append(d, "decisions.csv", [_drow(si, "WAIT_PRICES", note=f"phiên {si} có trong lịch nhưng kho chưa có giá của "
                                                                       "thành viên rổ nào: dừng trước phiên này, thử lại lần "
                                                                       "chạy sau (QĐ-11a mục 5)")])
            stopped = "WAIT_PRICES"
            break
        out = {name: [] for name in COLS}
        p, seal = st["pending"], None
        if p is not None:
            if p.get("void"):
                seal = ("LATE_VOID", p["void"])
            elif not p.get("run_id"):
                seal = ("LATE_VOID", "quyết định không có mã lượt chạy GitHub Actions: không niêm phong được")
            else:
                try:
                    seal = _seal(verify(p["run_id"]), s, local)
                except Exception as e:      # noqa: BLE001 — không xác minh được: dừng trước phiên khớp
                    _append(d, "decisions.csv", [_drow(si, "VERIFY_WAIT", k=p["k"], run_id=p["run_id"],
                                                       note=f"chưa xác minh được lượt chạy {p['run_id']} của quyết định "
                                                            f"phiên {p['t']}: {type(e).__name__}: {str(e)[:200]}; dừng "
                                                            "trước phiên khớp, thử lại lần chạy sau (QĐ-11a mục 3)")])
                    stopped = "VERIFY_WAIT"
                    break
        _corporate_actions(st, ctx, s, books, hist, out)                         # 1. sự kiện quyền
        finish = False
        if seal is not None:                                                     # 2. niêm phong
            k, t = p["k"], p["t"]
            if seal[0] == "SEALED":
                out["periods.csv"].append({"k": k, "decision_session": t, "fill_session": si, "status": "SEALED",
                                           "note": seal[1]})
                if k == 0:
                    st["d0"], st["k"] = t, 1
                for b in books:
                    bk = st["books"][b]
                    price = (lambda x: ctx.price(x, s))
                    legs = _legs(b, k, p["targets"].get(b, []), bk, _value(bk, price), price, spec)
                    st["open"][b] = {"targets": list(p["targets"].get(b, [])), "legs": legs} if legs else None
            elif k == 0:
                out["decisions.csv"].append(_drow(si, "D0_LATE", k=0, run_id=p.get("run_id") or "",
                                                  note=f"quyết định D0 phiên {t}: {seal[1]}; D0 dời sang phiên kế"))
                st["anchor"], st["count"] = None, 0
            else:
                out["periods.csv"].append({"k": k, "decision_session": t, "fill_session": si, "status": "LATE_VOID",
                                           "note": seal[1]})
            st["pending"] = None
            finish = k >= n_periods
        for b in books:                                                          # khớp (và thử lại lệnh còn chờ)
            if st["open"].get(b):
                st["open"][b] = _fill(b, st["books"][b], st["open"][b], s, ctx, out["trades.csv"])
        for r in out["trades.csv"]:
            if r["side"] in ("BUY", "SELL"):
                _record(hist, r)
        for b in books:                                                          # 3. định giá, 4. sụt giảm
            bk = st["books"][b]
            nav = _value(bk, lambda x: ctx.price(x, s))
            out["nav.csv"].append({"date": si, "book": b, "nav": round(nav, 0), "cash": round(bk["cash"], 0),
                                   "n_positions": len(bk["positions"]),
                                   "stale": ";".join(sorted(t for t in bk["positions"] if not ctx.priced(t, s)))})
            res = risk_gate.drawdown_path([(s, nav)], float(bk["peak"]), float(spec["drawdown_record"]), bk["peak_date"])
            r = res["rows"][0]
            out["drawdown.csv"].append({"date": si, "book": b, "nav": round(nav, 0), "peak": round(r["peak"], 0),
                                        "drawdown": round(r["drawdown"], 6), "verified": r["verified"]})
            bk["peak"] = res["peak"]
            bk["peak_date"] = _iso(res["peak_date"]) if res["peak_date"] is not None else None
            if res["breach"] is not None and not bk["in_breach"]:
                out["decisions.csv"].append(_drow(si, "DRAWDOWN_BREACH", book=b, note=(
                    f"sụt giảm {r['drawdown']:.2%} ≥ {float(spec['drawdown_record']):.0%} từ đỉnh {r['peak']:,.0f} "
                    f"({bk['peak_date']}): chỉ ghi nhận, không khóa, không bán (QĐ-5a)")))
            bk["in_breach"] = res["breach"] is not None
        if st["anchor"] is not None and si > st["anchor"]:
            st["count"] += 1
        if not finish:                                                           # 5. quyết định
            due = 0 if st["anchor"] is None else (
                st["k"] if st["d0"] is not None and st["k"] <= n_periods and st["count"] == period * st["k"] else None)
            if due is not None:
                dl = _deadline(_next_session(s, ctx.cal), local)
                if ctx.newest is None or s != ctx.newest:
                    late = (f"phiên {si} không phải phiên mới nhất có giá trong kho "
                            f"({_iso(ctx.newest) if ctx.newest is not None else 'không có'}): không quyết định muộn, "
                            "không quyết định bù (QĐ-11a mục 4)")
                elif now >= dl:
                    late = f"giờ máy chạy {now.isoformat()} đã qua hạn {dl.isoformat()}: robot tự từ chối quyết định"
                else:
                    late = None
                if late is not None and due == 0:
                    out["decisions.csv"].append(_drow(si, "D0_LATE", k=0, run_id=run_id or "", decided_at=now.isoformat(),
                                                      deadline=dl.isoformat(), note=late + "; D0 dời sang phiên kế"))
                elif late is not None:
                    out["decisions.csv"].append(_drow(si, "LATE_VOID", k=due, run_id=run_id or "",
                                                      decided_at=now.isoformat(), deadline=dl.isoformat(), note=late))
                    st["pending"], st["k"] = {"k": due, "t": si, "run_id": None, "targets": {}, "void": late}, due + 1
                else:
                    tg, notes = _targets(ctx, st, s, due, books, scorer)
                    out["decisions.csv"].append(_drow(
                        si, "DECIDE", k=due, run_id=run_id or "", decided_at=now.isoformat(), deadline=dl.isoformat(),
                        derivation_id=ctx.mk["derivation_id"], targets=json.dumps(tg, ensure_ascii=False, sort_keys=True),
                        note="; ".join(notes), **hashes))
                    st["pending"] = {"k": due, "t": si, "run_id": run_id, "targets": tg, "void": None}
                    if due == 0:
                        st["anchor"], st["count"] = si, 0
                    else:
                        st["k"] = due + 1
        for name in COLS:
            _append(d, name, out[name])
        st["last"] = si
        st["done"] = finish
        d.mkdir(parents=True, exist_ok=True)
        p_state.write_text(json.dumps(st, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        done.append(si)
        if finish:
            stopped = "DONE"
            break
    return {"trial_id": test_id, "processed": done, "stopped": stopped}


# ---------- dựng lại ----------

def replay(root, spec, until):
    """Dựng lại các sổ từ D0 đã đăng ký tới phiên `until` chỉ bằng danh mục mục tiêu đã ghi (DECIDE), periods.csv, các dòng
    áp sự kiện quyền đã ghi (CASH_DIVIDEND, STOCK_ADJUST), giá trong kho và luật của mô-đun → bảng (date, book, nav), cùng
    cách làm tròn với nav.csv. Không ghi tệp nào.
    Cổng R1a ở phiên khớp KHÔNG tính lại: kết quả cổng phụ thuộc bảng sự kiện và bản gốc tại lúc robot chạy (sự kiện biết muộn,
    bản gốc ghim sau làm đổi cửa sổ cách ly), nên replay dùng các dòng UNFILLED_RISK_GATE robot đã ghi. Mọi phần khác (lệnh,
    khóa biên độ, thiếu giá, giới hạn tiền mặt, phí, định giá) tính lại từ giá trong kho."""
    root = pathlib.Path(root)
    d = book_dir(root, spec["trial_id"])
    dec = _read(d, "decisions.csv")
    dec = dec[dec["action"] == "DECIDE"]
    targets = {(int(r.k), r.date): json.loads(r.targets) for r in dec.itertuples(index=False)}
    fills = {r.fill_session: (int(r.k), r.status, r.decision_session)
             for r in _read(d, "periods.csv").itertuples(index=False)}
    trd = _read(d, "trades.csv")
    ca = trd[trd["side"].isin(CA_SIDES)]
    gate = {}
    for r in trd[trd["side"] == "UNFILLED_RISK_GATE"].itertuples(index=False):
        gate.setdefault((r.book, r.date), set()).add(r.asset)
    books = [b for b in BOOKS if any(b in v for v in targets.values())] or [b for b in CONTROL if b in spec["books"]]
    ctx = _Ctx(root, until)
    cap = float(spec["capital"])
    state = {b: {"cash": cap, "positions": {}} for b in books}
    orders, out, scratch = {}, [], []
    for s in ctx.sessions:
        if s < pd.Timestamp(spec["d0"]):
            continue
        if not bool(ctx.session_ok.get(s, False)):
            break
        si = _iso(s)
        for r in ca[ca["date"] == si].itertuples(index=False):
            if r.book in state:
                _apply_ca_row(state[r.book], orders.get(r.book), {"side": r.side, "asset": r.asset,
                                                                  "quantity": r.quantity, "value": r.value})
        fin = fills.get(si)
        if fin is not None and fin[1] == "SEALED":
            k = fin[0]
            for b in books:
                price = (lambda x: ctx.price(x, s))
                tg = targets[(k, fin[2])].get(b, [])
                legs = _legs(b, k, tg, state[b], _value(state[b], price), price, spec)
                orders[b] = {"targets": list(tg), "legs": legs} if legs else None
        for b in books:
            if orders.get(b):
                orders[b] = _fill(b, state[b], orders[b], s, ctx, scratch,
                                  refused_by_gate=lambda book, day: gate.get((book, day), set()))
        for b in books:
            out.append({"date": si, "book": b, "nav": round(_value(state[b], lambda x: ctx.price(x, s)), 0)})
        if fin is not None and fin[0] >= int(spec["periods"]):
            break
    return pd.DataFrame(out, columns=["date", "book", "nav"])
