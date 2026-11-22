"""Sổ FWD theo phiên (F1b; QĐ-11, QĐ-11a, QĐ-5a của ADR-0016): ba sổ đối chứng FWD-EW, FWD-HOLD, FWD-CASH; sổ bóng FWD-S1,
FWD-S2 chỉ chạy khi có hàm chấm điểm truyền vào (F1c làm phần đó).

Chưa đăng ký — không có dòng `kind: "forward_test"` với `trial_id` bằng mã phép thử trong research/trial_registry.jsonl — thì
`run` chỉ đọc tệp sổ đăng ký rồi trả None: không tạo tệp, không ghi dòng nào.

Đã đăng ký: thư mục paper/fwd/<trial_id>/ gồm state.json và năm tệp CSV chỉ ghi thêm (cột ở COLS):
  - nav.csv: NAV cuối phiên từng sổ; `stale` = mã đang giữ được định giá theo giá gốc gần nhất (STALE_PRICE);
  - trades.csv: BUY, SELL, CASH_DIVIDEND, STOCK_ADJUST (kèm khóa sự kiện `event`, giá trị đã áp `value`, cờ CA_UNVERIFIED,
    CA_LATE), và lệnh không khớp: UNFILLED_LIMIT_UP, UNFILLED_LIMIT_DOWN, STALE_PRICE, UNFILLED_RISK_GATE;
  - decisions.csv: DECIDE (danh mục mục tiêu từng sổ và dữ liệu lúc quyết định, QĐ-11a mục 8), RISK_GATE (đủ đầu vào và kết
    luận của mỗi lần gọi cổng R1a, cùng sha256 các tệp đầu vào), LATE_VOID, D0_LATE, VERIFY_WAIT, WAIT_PRICES,
    DRAWDOWN_BREACH, PIT_REJECTED, SPEC_INVALID, ERROR;
  - periods.csv: mỗi kỳ một dòng (k, phiên quyết định, phiên khớp, SEALED hoặc LATE_VOID);
  - drawdown.csv: sụt giảm từng phiên từng sổ (hàm thuần risk_gate.drawdown_path, chế độ chỉ ghi nhận).

Luật (mục của QĐ-11a trong ngoặc):
  - Đầu vào: data.load_market(as_of, research_input="verified", universe="historical", sessions="calendar"). Nhãn phải là
    "PIT_MODES_ONLY" (Owner xác nhận 22/11/2026, gói 4 đã sửa: F1b dùng nhãn này); khác thì ghi PIT_REJECTED, không xử lý
    phiên nào. "Đủ điều kiện" tại phiên s là `eligible` tại s.
  - Phiên (1): risk_gate.session_axis(ngày của kho giá, lịch, until=as_of), bỏ ngày CHUA_CO_THONG_BAO và ngày ngoài vùng lịch
    mà không thành viên rổ nào có giá (danh sách của load_market). Có giá = dòng giá với khối lượng > 0.
  - Tuần tự từng phiên sau phiên đã xử lý gần nhất (2): xác minh niêm phong quyết định phiên trước → sự kiện quyền cho vị thế
    giữ từ trước phiên → khớp → định giá → đo sụt giảm → quyết định (chỉ ở phiên tái cơ cấu). Mỗi phiên ghi qua nhật ký
    journal.json (các byte sẽ nối vào từng CSV và state.json mới, ghi nguyên tử trước); lần chạy sau thấy nhật ký thì ghi
    nốt phần còn thiếu, nên bị ngắt ở bất kỳ bước ghi nào cũng không có dòng trùng hay dòng dở (finish_journal).
  - Niêm phong lúc khớp (3): lệnh của quyết định phiên t chỉ khớp ở đóng cửa phiên t+1, khi hàm xác minh (mặc định
    `github_run`, API GitHub) cho biết lượt chạy ghi quyết định là `.github/workflows/daily_cycle.yml` trên `main`, sự kiện
    `schedule` hoặc `workflow_dispatch`, kết luận `success`, kết thúc trước hạn (seal_deadline_local, giờ VN) của phiên t+1;
    VÀ lịch sử git của nhánh đang chạy cho thấy commit đưa ĐÚNG dòng DECIDE đó (run_id, danh mục trùng lệnh đang chờ) vào
    decisions.csv mang "run <run_id>" trong thông điệp và có giờ commit nằm trong lượt chạy. Không xác minh được (lỗi API,
    lượt chưa xong, thiếu lịch sử git, kho nông) → VERIFY_WAIT, dừng trước t+1, thử lại lần chạy sau. Lượt không hợp lệ, trễ,
    hay không có bằng chứng commit → LATE_VOID: không sổ nào đổi danh mục theo quyết định đó.
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
`replay(root, spec, until)` dựng lại các sổ từ D0 tới phiên robot đã ghi xong, bằng danh mục mục tiêu đã niêm phong, các
dòng áp sự kiện đã ghi, giá trong kho và luật trên; cổng R1a ở phiên khớp được tính lại từ đầu vào ở dòng RISK_GATE (xem
replay).
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import pathlib
import re
import subprocess
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
JOURNAL = "journal.json"
STATE = "state.json"


class JournalConflict(RuntimeError):
    """Tệp CSV không khớp nhật ký ghi dở: không đoán, không ghi thêm gì (dừng, chờ người xem)."""


class ReplayMismatch(ValueError):
    """Dòng đã ghi của robot không khớp phép tính lại của replay."""


class _Wait(Exception):
    """Chưa đủ bằng chứng để xác minh niêm phong (thiếu lịch sử git, API): VERIFY_WAIT, thử lại lần chạy sau."""


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


def _atomic_write(p, text):
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, p)


def _append_bytes(p, b):
    with open(p, "ab") as f:
        f.write(b)


def _drop_journal(p):
    p.unlink()


def _state_text(st):
    return json.dumps(st, ensure_ascii=False, indent=2, sort_keys=True)


def _commit(d, rows, state=None):
    """Ghi một phiên (hoặc một dòng lẻ) qua nhật ký, để lần chạy bị ngắt giữa chừng không để lại dòng trùng hay dòng dở.
    1. journal.json (ghi nguyên tử) chứa, cho từng CSV, kích thước tệp trước khi ghi và ĐÚNG các byte sẽ nối thêm, cùng
       state.json mới (None: không đổi trạng thái);
    2. nối các byte vào từng CSV; 3. ghi state.json (nguyên tử); 4. xóa journal.json.
    Lần chạy sau thấy journal.json thì finish_journal ghi nốt phần còn thiếu, không ghi lại phần đã có."""
    d.mkdir(parents=True, exist_ok=True)
    parts = {}
    for name in COLS:
        if rows.get(name):
            f = d / name
            off = f.stat().st_size if f.exists() else 0
            parts[name] = {"offset": off, "text": pd.DataFrame(rows[name], columns=COLS[name]).to_csv(
                index=False, header=off == 0, lineterminator="\n")}
    if not parts and state is None:
        return
    j = {"parts": parts, "state": state}
    _atomic_write(d / JOURNAL, json.dumps(j, ensure_ascii=False))
    finish_journal(d, j)


def finish_journal(d, j=None):
    """Hoàn tất nhật ký ghi dở → True; không có nhật ký → False. Mỗi CSV phải có kích thước từ `offset` tới `offset` + số
    byte cần nối, và phần đã có phải trùng đầu của các byte đó (ghi dở); khi đó chỉ nối phần còn thiếu. Khác đi thì
    JournalConflict (không ghi thêm gì)."""
    jp = d / JOURNAL
    if j is None:
        if not jp.exists():
            return False
        j = json.loads(jp.read_text(encoding="utf-8"))
    for name in COLS:
        part = j["parts"].get(name)
        if part is None:
            continue
        f, b, off = d / name, part["text"].encode("utf-8"), int(part["offset"])
        cur = f.stat().st_size if f.exists() else 0
        if not off <= cur <= off + len(b):
            raise JournalConflict(f"{name}: kích thước {cur} byte ngoài khoảng của nhật ký [{off}, {off + len(b)}]")
        if cur > off:
            with open(f, "rb") as fh:
                fh.seek(off)
                if fh.read() != b[:cur - off]:
                    raise JournalConflict(f"{name}: phần đã ghi sau byte {off} khác nội dung của nhật ký")
        if cur < off + len(b):
            _append_bytes(f, b[cur - off:])
    if j["state"] is not None:
        _atomic_write(d / STATE, _state_text(j["state"]))
    _drop_journal(jp)
    return True


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
    if "note" in kw:                                    # một dòng CSV mỗi bản ghi (đối chiếu dòng quyết định với git)
        kw["note"] = " ".join(str(kw["note"]).split())
    return {"date": date, "action": action, **kw}


# ---------- xác minh niêm phong ----------

def github_run(run_id):
    """Hàm xác minh mặc định: lượt chạy "<GITHUB_RUN_ID>.<GITHUB_RUN_ATTEMPT>" theo API GitHub → {started_at, finished_at,
    path, branch, event, conclusion}. Lượt chưa kết thúc hay lỗi mạng: ném lỗi (nơi gọi ghi VERIFY_WAIT)."""
    rid, _, att = str(run_id).partition(".")
    r = risk_gate.github_api(f"actions/runs/{rid}/attempts/{att}" if att else f"actions/runs/{rid}")
    if r.get("status") != "completed":
        raise RuntimeError(f"lượt chạy {run_id} chưa kết thúc (status {r.get('status')!r})")
    return {"started_at": r.get("run_started_at"), "finished_at": r.get("updated_at"), "path": r.get("path"),
            "branch": r.get("head_branch"), "event": r.get("event"), "conclusion": r.get("conclusion")}


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True, encoding="utf-8", timeout=60)


def _decision_line(d, p):
    """Dòng CSV nguyên văn của quyết định đang chờ `p` trong decisions.csv → (dòng, None) hoặc (None, lý do). Phải có đúng
    một dòng DECIDE cùng phiên, cùng kỳ; run_id và danh mục mục tiêu của dòng phải trùng lệnh đang chờ trong state.json."""
    f = d / "decisions.csv"
    lines = f.read_text(encoding="utf-8").splitlines() if f.exists() else []
    if not lines:
        return None, "decisions.csv không có dòng quyết định"
    head, hits = next(csv.reader([lines[0]])), []
    for line in lines[1:]:
        r = dict(zip(head, next(csv.reader([line]))))
        if r.get("action") == "DECIDE" and r.get("date") == p["t"] and r.get("k") == str(p["k"]):
            hits.append((line, r))
    if len(hits) != 1:
        return None, f"decisions.csv có {len(hits)} dòng DECIDE kỳ {p['k']} phiên {p['t']}, cần đúng 1"
    line, r = hits[0]
    if r.get("run_id") != p["run_id"]:
        return None, f"run_id của dòng quyết định ({r.get('run_id')}) khác lệnh đang chờ ({p['run_id']})"
    try:
        tg = json.loads(r.get("targets") or "")
    except ValueError:
        return None, "danh mục mục tiêu của dòng quyết định không đọc được"
    if tg != p["targets"]:
        return None, "danh mục mục tiêu của dòng quyết định khác lệnh đang chờ trong state.json"
    return line, None


def _decision_commit(root, rel, line, run_id):
    """Commit trên lịch sử của HEAD (nhánh main của lượt chạy robot) đã đưa ĐÚNG dòng quyết định `line` vào `rel`, và thông
    điệp của nó mang mã lượt chạy "run <run_id>" (daily_cycle.yml ghi "run ${GITHUB_RUN_ID}.${GITHUB_RUN_ATTEMPT}") →
    ((sha, giờ commit), None) hoặc (None, lý do). Không đọc được lịch sử git hay kho nông → _Wait."""
    r = _git(root, "rev-parse", "--is-shallow-repository")
    if r.returncode != 0:
        raise _Wait("không đọc được lịch sử git của kho")
    if r.stdout.strip() == "true":
        raise _Wait("kho nông (shallow clone): thiếu lịch sử git để xác minh commit của quyết định")
    r = _git(root, "log", "--reverse", "--format=%H", f"-S{line}", "HEAD", "--", rel)
    if r.returncode != 0:
        raise _Wait(f"git log lỗi: {r.stderr.strip()[:200]}")
    sha = None
    for c in r.stdout.split():
        f = _git(root, "show", f"{c}:{rel}")
        if f.returncode == 0 and line in f.stdout.splitlines():
            sha = c
            break
    if sha is None:
        return None, "dòng quyết định không nằm trong commit nào trên lịch sử của nhánh đang chạy"
    msg = _git(root, "show", "-s", "--format=%B", sha).stdout
    if not re.search(rf"\brun {re.escape(str(run_id))}(?![\d.])", msg):
        return None, f"commit {sha[:7]} đưa dòng quyết định vào không mang mã lượt chạy {run_id}"
    return (sha, _aware(_git(root, "show", "-s", "--format=%cI", sha).stdout.strip())), None


def _seal(info, s, local, proof=None, proof_why=None):
    """→ ("SEALED" | "LATE_VOID", lý do). `proof` = (sha, giờ commit) của commit đưa dòng quyết định lên nhánh main, hoặc None
    với lý do `proof_why`. Thông tin lượt chạy thiếu giờ bắt đầu hay kết thúc (hay không phải dict): ném lỗi → VERIFY_WAIT."""
    if not isinstance(info, dict) or not info.get("finished_at") or not info.get("started_at"):
        raise ValueError(f"API không trả giờ bắt đầu và giờ kết thúc của lượt chạy ({info!r})")
    start, fin, dl = _aware(info["started_at"]), _aware(info["finished_at"]), _deadline(s, local)
    bad = []
    if str(info.get("path") or "").split("@")[0] != WORKFLOW:
        bad.append(f"workflow {info.get('path')!r} khác {WORKFLOW}")
    if info.get("branch") != "main":
        bad.append(f"nhánh {info.get('branch')!r} khác main")
    if info.get("event") not in RUN_EVENTS:
        bad.append(f"sự kiện {info.get('event')!r} không thuộc {list(RUN_EVENTS)}")
    if info.get("conclusion") != "success":
        bad.append(f"kết luận {info.get('conclusion')!r} khác success")
    if proof is None:
        bad.append(proof_why or "không có bằng chứng commit của quyết định")
    elif not start <= proof[1] <= fin:
        bad.append(f"commit {proof[0][:7]} lúc {proof[1].isoformat()} nằm ngoài lượt chạy "
                   f"[{start.isoformat()}, {fin.isoformat()}]")
    if bad:
        return "LATE_VOID", "chưa niêm phong: " + "; ".join(bad)
    if fin >= dl:
        return "LATE_VOID", f"lượt chạy kết thúc {fin.isoformat()} không trước hạn {dl.isoformat()}"
    return "SEALED", (f"lượt chạy kết thúc {fin.isoformat()} trước hạn {dl.isoformat()}; commit {proof[0]} lúc "
                      f"{proof[1].isoformat()} đưa dòng quyết định lên nhánh main")


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
        self.vol = vol = s.pivot(index="date", columns="ticker", values="volume").sort_index()
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
        self._inputs = None

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

    def inputs(self):
        """sha256 của các tệp quyết định cửa sổ cách ly và trục phiên của cổng R1a tại lúc chạy: manifest bản gốc sự kiện
        quyền, bảng sự kiện nhập tay và của Yahoo, lịch phiên, rổ theo ngày. Kiểm toán dựng lại đầu vào cổng từ đúng các tệp
        này ở commit của lượt chạy."""
        if self._inputs is None:
            cfg = config.CFG["corporate_actions"]
            files = sorted(self.root.joinpath(*data.EVIDENCE_DIR).glob("EVIDENCE_MANIFEST*.json"))
            files += [self.root / cfg["manual"], self.root / cfg["yahoo_cache"], self.root.joinpath(*risk_gate.CALENDAR),
                      self.root / data.VN30_HISTORY]
            self._inputs = {f.relative_to(self.root).as_posix(): (va.sha256_file(f) if f.is_file() else None)
                            for f in files}
        return self._inputs

    def adv(self, s, tickers):
        """Giá trị giao dịch bình quân tính lại từ giá và khối lượng gốc của kho tới phiên s (như market_snapshot)."""
        lim = config.CFG["paper"].get("risk_limits") or {}
        raw, vol = self.raw.loc[:s], self.vol.loc[:s]
        axis = risk_gate.session_axis(raw.index, self.cal, until=s)
        return risk_gate.adv_values(raw, vol, axis, list(tickers), int(lim.get("adv_sessions", 20)))

    def gate(self, stage, book, s, targets, nav, positions, rows, k=""):
        """risk_gate.check với thị trường tại phiên s; ghi một dòng RISK_GATE vào decisions.csv (`rows`) mang ĐỦ đầu vào của
        hàm thuần check (mục tiêu, NAV, vị thế, giới hạn, thị trường) và dấu vân tay tệp đầu vào → kết quả check."""
        lim = config.CFG["paper"].get("risk_limits")
        market = self.market(s, list(targets) + list(positions))
        g = risk_gate.check(list(targets), {"nav": nav, "positions": dict(positions)}, market, lim)
        rec = {"stage": stage, "targets": list(targets), "nav": nav, "positions": dict(positions), "limits": lim,
               "market": market, "verdict": g["verdict"], "excluded": g["excluded"], "reasons": g["reasons"],
               "inputs": self.inputs()}
        rows.append(_drow(_iso(s), "RISK_GATE", book=book, k=k, note=f"{stage}: {g['verdict']}",
                          targets=json.dumps(rec, ensure_ascii=False, sort_keys=True)))
        return g


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


def _fill(book, bk, order, s, ctx, rows, gate):
    """Khớp lệnh `order` = {"targets", "legs"} của một sổ ở đóng cửa phiên s → lệnh còn chờ (thử lại phiên sau) hoặc None.
    gate(sổ, phiên, mục tiêu, NAV, vị thế) → kết quả risk_gate.check cho lệnh mua (robot: chạy cổng và ghi đầu vào; replay:
    tính lại check từ đầu vào đã ghi, đối chiếu giá và giá trị giao dịch bình quân với kho)."""
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
    if buys:                        # R1a: lệnh mua qua lại cổng ở chính phiên khớp, sau lệnh bán, với mọi vị thế còn lại
        g = gate(book, s, list(targets), _value(bk, lambda x: ctx.price(x, s)), dict(bk["positions"]))
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


def _targets(ctx, st, s, k, books, scorer, rows):
    """Mục tiêu từng sổ ở phiên quyết định s (kỳ k), sau cổng R1a (dòng RISK_GATE vào `rows`) → ({sổ: [mã]}, ghi chú cổng)."""
    elig, members, notes, out = ctx.eligible(s), ctx.members(s), [], {}
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
            g = ctx.gate("decide", b, s, tg, nav, keep, rows, k=k)
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
        err = f"{type(e).__name__}: {e}"
        try:
            finish_journal(d)               # phiên đã vào nhật ký thì ghi nốt trước, để dòng ERROR không chen vào giữa
        except Exception as e2:             # noqa: BLE001 — nhật ký không khớp tệp: không ghi gì thêm
            return {"trial_id": test_id, "processed": [], "stopped": "JOURNAL_CONFLICT",
                    "error": f"{err}; {type(e2).__name__}: {e2}"}
        _commit(d, {"decisions.csv": [_drow(t0, "ERROR", note=err[:300])]})
        return {"trial_id": test_id, "processed": [], "stopped": "ERROR", "error": err}


def _run(spec, d, root, test_id, t0, verify, scorer, now, run_id):
    finish_journal(d)                       # lần chạy trước bị ngắt giữa lúc ghi: ghi nốt phiên đó (JournalConflict: dừng)
    why = spec_problem(spec)
    if why:
        _commit(d, {"decisions.csv": [_drow(t0, "SPEC_INVALID", note=why)]})
        return {"trial_id": test_id, "processed": [], "stopped": "SPEC_INVALID"}
    p_state = d / STATE
    books = [b for b in BOOKS if b in spec["books"] and (b in CONTROL or scorer is not None)]
    st = json.loads(p_state.read_text(encoding="utf-8")) if p_state.exists() else _new_state(test_id, spec, books)
    if st.get("done"):
        return {"trial_id": test_id, "processed": [], "stopped": "DONE"}
    for b in books:
        st["books"].setdefault(b, _new_state(test_id, spec, [b])["books"][b])
    ctx = _Ctx(root, t0)
    if ctx.mk["pit_label"] != PIT_REQUIRED:
        _commit(d, {"decisions.csv": [_drow(t0, "PIT_REJECTED", derivation_id=ctx.mk.get("derivation_id", ""),
                                            note=f"pit_label {ctx.mk['pit_label']!r} khác {PIT_REQUIRED!r}: không xử lý phiên "
                                                 f"nào; " + "; ".join(ctx.mk.get("pit_gaps") or []))]})
        return {"trial_id": test_id, "processed": [], "stopped": "PIT_REJECTED"}
    hashes = {"vn30_history_sha256": va.sha256_file(root / data.VN30_HISTORY),
              "trading_calendar_sha256": va.sha256_file(root.joinpath(*risk_gate.CALENDAR))
              if root.joinpath(*risk_gate.CALENDAR).is_file() else ""}
    hist, done, stopped = _history(d), [], None
    period, n_periods, local = int(spec["period_sessions"]), int(spec["periods"]), spec["seal_deadline_local"]
    rel = "/".join((*DIR, test_id, "decisions.csv"))
    todo = [s for s in ctx.sessions if s >= pd.Timestamp(spec["d0"])
            and (st["last"] is None or s > pd.Timestamp(st["last"]))]
    for s in todo:
        si = _iso(s)
        if not bool(ctx.session_ok.get(s, False)):
            _commit(d, {"decisions.csv": [_drow(si, "WAIT_PRICES", note=f"phiên {si} có trong lịch nhưng kho chưa có giá "
                                                                        "của thành viên rổ nào: dừng trước phiên này, thử lại "
                                                                        "lần chạy sau (QĐ-11a mục 5)")]})
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
                line, why = _decision_line(d, p)
                if line is None:                                 # dòng quyết định không khớp lệnh đang chờ: không niêm phong
                    seal = ("LATE_VOID", "chưa niêm phong: " + why)
                else:
                    try:
                        info = verify(p["run_id"])
                        proof, why = _decision_commit(root, rel, line, p["run_id"])
                        seal = _seal(info, s, local, proof, why)
                    except Exception as e:  # noqa: BLE001 — không xác minh được: dừng trước phiên khớp
                        _commit(d, {"decisions.csv": [_drow(
                            si, "VERIFY_WAIT", k=p["k"], run_id=p["run_id"],
                            note=f"chưa xác minh được lượt chạy {p['run_id']} của quyết định phiên {p['t']}: "
                                 f"{type(e).__name__}: {str(e)[:200]}; dừng trước phiên khớp, thử lại lần chạy sau "
                                 "(QĐ-11a mục 3)")]})
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
                st["open"][b] = _fill(b, st["books"][b], st["open"][b], s, ctx, out["trades.csv"],
                                      lambda book, day, tg, nav, pos: ctx.gate("fill", book, day, tg, nav, pos,
                                                                               out["decisions.csv"]))
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
                    tg, notes = _targets(ctx, st, s, due, books, scorer, out["decisions.csv"])
                    out["decisions.csv"].append(_drow(
                        si, "DECIDE", k=due, run_id=run_id or "", decided_at=now.isoformat(), deadline=dl.isoformat(),
                        derivation_id=ctx.mk["derivation_id"], targets=json.dumps(tg, ensure_ascii=False, sort_keys=True),
                        note="; ".join(notes), **hashes))
                    st["pending"] = {"k": due, "t": si, "run_id": run_id, "targets": tg, "void": None}
                    if due == 0:
                        st["anchor"], st["count"] = si, 0
                    else:
                        st["k"] = due + 1
        st["last"] = si
        st["done"] = finish
        _commit(d, out, st)                 # các CSV và state.json của phiên: qua nhật ký, không trùng khi bị ngắt
        done.append(si)
        if finish:
            stopped = "DONE"
            break
    return {"trial_id": test_id, "processed": done, "stopped": stopped}


# ---------- dựng lại ----------

def replay(root, spec, until):
    """Dựng lại các sổ từ D0 đã đăng ký tới phiên `until`, nhưng không quá phiên cuối robot đã ghi xong (`last` của
    state.json; phiên có nhật ký ghi dở không tính) → bảng (date, book, nav), cùng cách làm tròn với nav.csv. Không ghi tệp.
    Dùng: danh mục mục tiêu đã niêm phong (DECIDE và periods.csv), các dòng áp sự kiện quyền đã ghi, giá trong kho, luật của
    mô-đun. Cổng R1a ở phiên khớp được TÍNH LẠI bằng hàm thuần risk_gate.check từ đầu vào robot đã ghi ở dòng RISK_GATE:
    mục tiêu, NAV và vị thế phải trùng trạng thái replay đang dựng, giá và giá trị giao dịch bình quân phải trùng phép tính lại
    từ kho, kết luận phải trùng; khác thì ReplayMismatch. Riêng cửa sổ cách ly lấy từ dòng đã ghi, kèm sha256 các tệp đầu
    vào (manifest bản gốc, bảng sự kiện, lịch, rổ) để kiểm toán dựng lại ở commit của lượt chạy."""
    root = pathlib.Path(root)
    d = book_dir(root, spec["trial_id"])
    p_state = d / STATE
    last = json.loads(p_state.read_text(encoding="utf-8")).get("last") if p_state.exists() else None
    if last is None:
        return pd.DataFrame(columns=["date", "book", "nav"])
    upto = min(pd.Timestamp(until), pd.Timestamp(last))
    dec = _read(d, "decisions.csv")
    targets = {(int(r.k), r.date): json.loads(r.targets) for r in dec[dec["action"] == "DECIDE"].itertuples(index=False)}
    gates = {}
    for r in dec[dec["action"] == "RISK_GATE"].itertuples(index=False):
        rec = json.loads(r.targets)
        if rec.get("stage") == "fill":
            gates.setdefault((r.date, r.book), []).append(rec)
    fills = {r.fill_session: (int(r.k), r.status, r.decision_session)
             for r in _read(d, "periods.csv").itertuples(index=False)}
    trd = _read(d, "trades.csv")
    ca = trd[trd["side"].isin(CA_SIDES)]
    books = [b for b in BOOKS if any(b in v for v in targets.values())] or [b for b in CONTROL if b in spec["books"]]
    ctx = _Ctx(root, upto)
    cap = float(spec["capital"])
    state = {b: {"cash": cap, "positions": {}} for b in books}
    orders, out, scratch = {}, [], []

    def gate(book, s, tg, nav, pos):
        si = _iso(s)
        recs = gates.get((si, book)) or []
        if not recs:
            raise ReplayMismatch(f"{si} {book}: có lệnh mua nhưng không có dòng RISK_GATE nào của phiên khớp")
        rec = recs.pop(0)
        if rec["targets"] != list(tg) or rec["positions"] != dict(pos) or rec["nav"] != nav:
            raise ReplayMismatch(f"{si} {book}: mục tiêu, vị thế hay NAV ở dòng RISK_GATE khác trạng thái dựng lại")
        m = rec["market"]
        for t, p in (m.get("price") or {}).items():
            if ctx.price(t, s) != p:
                raise ReplayMismatch(f"{si} {book}: giá {t} ở dòng RISK_GATE ({p}) khác giá gốc trong kho ({ctx.price(t, s)})")
        if (m.get("adv_value") or m.get("adv_problem")) and rec.get("limits"):
            adv, _ = ctx.adv(s, list(m.get("adv_value") or {}) + list(m.get("adv_problem") or {}))
            if adv != (m.get("adv_value") or {}):
                raise ReplayMismatch(f"{si} {book}: giá trị giao dịch bình quân ở dòng RISK_GATE khác phép tính lại từ kho")
        g = risk_gate.check(rec["targets"], {"nav": rec["nav"], "positions": rec["positions"]}, m, rec["limits"])
        if g["verdict"] != rec["verdict"] or g["excluded"] != rec["excluded"]:
            raise ReplayMismatch(f"{si} {book}: kết luận cổng ghi ({rec['verdict']}) khác check tính lại ({g['verdict']})")
        return g

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
                orders[b] = _fill(b, state[b], orders[b], s, ctx, scratch, gate)
        for b in books:
            out.append({"date": si, "book": b, "nav": round(_value(state[b], lambda x: ctx.price(x, s)), 0)})
        if fin is not None and fin[0] >= int(spec["periods"]):
            break
    return pd.DataFrame(out, columns=["date", "book", "nav"])
