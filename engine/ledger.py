"""PREDICTION LEDGER — trái tim của v1.0.
Dự báo ghi TRƯỚC khi biết kết quả (append-only, commit vào git). Kết quả ghi ở file riêng.
Auditor, Resolution, Scorecard đều là code tất định — không LLM nào tự chấm mình.

ĐƯỜNG GHI CỦA ENGINE ĐANG ĐÓNG (ADR-0003 quyết định 11; config.yaml ledger.engine_forecasts: closed). Từ v3.0 sổ dự báo là sổ
của các Issue 'Forecast'/'Resolution': mỗi dòng có Issue thật và dấu nhận của robot. Dòng do engine tự ghi (chuyên gia LLM
dự báo giá, engine tự chấm bằng giá) không có bằng chứng nào ngoài tệp về việc ai ghi và ghi lúc nào, nên tools/validate.py
không nhận dòng nào như thế. Khi đóng: record() không ghi, resolve() không chấm, scorecard() không tính dòng engine.
Mã của đường này được giữ (và test bằng thư mục tạm có cổng mở) để mở lại bằng ADR khi có cơ chế xuất xứ."""
import hashlib, json, math, re, sys
import numpy as np, pandas as pd
from .config import CFG, ROOT, REPO, path, save_json

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from tools.laws_checks import line_hash  # noqa: E402  một thuật toán hash chuỗi cho mọi bên ghi Ledger
from tools.ledger_intake import qkey as _qkey, vn_day  # noqa: E402  một định nghĩa "câu hỏi" và "ngày" cho nhận/phân định/chấm

PRED, RES = "ledger/predictions.jsonl", "ledger/resolutions.jsonl"

def _load(rel):
    p = ROOT / rel
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []

def _append(rel, rows):
    with open(path(rel), "a", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")

def _append_chained(rel, rows):
    """Ghi nối tiếp vào Ledger có hash chuỗi prev_hash/hash, cùng luật với tools/ledger_intake.py
    (tools/laws_checks.check_ledger_chain kiểm mọi dòng)."""
    old = _load(rel)
    prev = old[-1].get("hash", "GENESIS") if old else "GENESIS"
    out = []
    for r in rows:
        r = {**_finite(r), "prev_hash": prev}
        r["hash"] = line_hash(r)
        prev = r["hash"]
        out.append(r)
    with open(path(rel), "a", encoding="utf-8") as f:
        for r in out: f.write(json.dumps(r, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")

def _finite(x):
    """NaN/±vô cực không phải JSON chuẩn (laws_checks.check_ledger_chain từ chối): đổi thành null trước khi ghi sổ."""
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    if isinstance(x, dict):
        return {k: _finite(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_finite(v) for v in x]
    return x

def is_issue_row(p):
    """Dòng ghi từ GitHub Issue 'Forecast' (tools/ledger_intake.py). Không chấm bằng giá ở đây."""
    return "issue_number" in p

GATE_REASON = "config.yaml: ledger.engine_forecasts = closed — đường ghi dự báo của engine đang đóng (ADR-0003 quyết định 11)"
ENGINE_KEYS = {"id", "created_at", "procedure", "claim", "question", "resolution_rule", "probability", "base_rate",
               "evidence_refs", "links", "note"}
ENGINE_RULE = {"type": "excess_return_positive", "benchmark": "universe_equal_weight", "entry": "close_t+1"}
_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")

def forecasts_open():
    """Đường ghi dự báo của engine chỉ mở khi config.yaml ghi ĐÚNG ledger.engine_forecasts: open. Không khai = đóng.
    (tools/validate.py của bản này chỉ chấp nhận 'closed' trong kho thật; 'open' chỉ dùng trong thư mục tạm của test.)"""
    return (CFG.get("ledger") or {}).get("engine_forecasts") == "open"

def _num(x):
    return not isinstance(x, bool) and isinstance(x, (int, float)) and math.isfinite(x)

def _engine_id(row):
    body = {k: v for k, v in row.items() if k not in ("prev_hash", "hash")}
    body["id"] = None
    return "P-" + hashlib.sha1(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]

def engine_row_error(p):
    """Hợp đồng ĐẦY ĐỦ của một dòng dự báo do engine ghi (đúng những gì _engine_row() tạo ra). Trả về lỗi hoặc None.
    resolve() và scorecard() chỉ đụng tới dòng qua được hàm này — một dòng thiếu horizon, created_at hay probability bị bỏ
    qua chứ không làm vòng học vỡ (KeyError)."""
    if not isinstance(p, dict) or is_issue_row(p) or "seat" in p:
        return "không phải dòng của engine"
    if set(p) - {"prev_hash", "hash"} != ENGINE_KEYS:
        return "tập trường không đúng hợp đồng dòng engine"
    rr = p["resolution_rule"]
    if not isinstance(rr, dict) or set(rr) != set(ENGINE_RULE) | {"ticker", "horizon"} or any(rr[k] != v for k, v in ENGINE_RULE.items()):
        return "resolution_rule không đúng hợp đồng"
    if not isinstance(rr["ticker"], str) or not re.fullmatch(r"[A-Za-z0-9._-]{1,15}", rr["ticker"]):
        return "ticker không hợp lệ"
    if isinstance(rr["horizon"], bool) or not isinstance(rr["horizon"], int) or rr["horizon"] not in CFG["ledger"]["horizons"]:
        return "horizon không thuộc config.yaml ledger.horizons"
    if not isinstance(p["created_at"], str) or not _DATE_RE.fullmatch(p["created_at"]):
        return "created_at không phải ngày YYYY-MM-DD"
    try:
        pd.Timestamp(p["created_at"])
    except ValueError:
        return "created_at không phải ngày YYYY-MM-DD"
    L = CFG["ledger"]
    if not _num(p["probability"]) or not (L["min_p"] <= p["probability"] <= L["max_p"]):
        return "probability không phải số trong khoảng cho phép"
    if not _num(p["base_rate"]) or not (0.0 <= p["base_rate"] <= 1.0):
        return "base_rate không phải số trong [0, 1]"
    if not all(isinstance(p[k], str) and p[k].strip() for k in ("procedure", "claim", "question")) or not isinstance(p["note"], str):
        return "procedure/claim/question/note không phải chuỗi hợp lệ"
    if not isinstance(p["evidence_refs"], list) or not isinstance(p["links"], dict):
        return "evidence_refs/links sai kiểu"
    if p["id"] != _engine_id(p):
        return "id không khớp nội dung dòng"
    return None

def is_engine_row(p):
    """Dòng do engine/experts ghi, đúng hợp đồng đầy đủ → chấm tự động bằng giá. Khi đường ghi của engine đóng thì không
    dòng nào được coi là dòng engine: không chấm, không tính điểm (sổ hợp lệ khi đó cũng không có dòng nào như thế)."""
    return forecasts_open() and engine_row_error(p) is None

def _engine_row(p, as_of, base):
    """Dựng một dòng dự báo của engine từ dự báo đã qua audit(). Mã = sha1 của nội dung dòng."""
    h = int(p["horizon"])
    row = {"id": None, "created_at": as_of, "procedure": p["procedure"], "claim": p["claim"],
           "question": f"{p['ticker']} vượt bình quân universe trong {h} phiên, vào lệnh tại close phiên kế tiếp sau {as_of}",
           "resolution_rule": {"type": "excess_return_positive", "ticker": p["ticker"], "horizon": h,
                               "benchmark": "universe_equal_weight", "entry": "close_t+1"},
           "probability": round(float(p["probability"]), 3), "base_rate": round(float(base), 3),
           "evidence_refs": p.get("evidence_refs", []), "links": p.get("links", {}), "note": p.get("note", "")}
    row["id"] = _engine_id(row)
    return row

def base_rate(close, ticker, h):
    """Tỷ lệ lịch sử mã này vượt bình quân universe trong h phiên (do code tính)."""
    fwd = close.shift(-h) / close - 1
    ex = fwd.sub(fwd.mean(axis=1), axis=0)[ticker].dropna()
    return float(np.clip((ex > 0).mean(), 0.05, 0.95)) if len(ex) > 50 else 0.5

# ---------------- AUDITOR (code) ----------------
def audit(p, universe, fact_ids, as_of):
    L = CFG["ledger"]; errs = []
    if p.get("ticker") not in universe: errs.append("mã không thuộc universe")
    if p.get("horizon") not in L["horizons"]: errs.append(f"horizon phải thuộc {L['horizons']}")
    try:
        pr = float(p.get("probability"))
        if not (L["min_p"] <= pr <= L["max_p"]): errs.append(f"xác suất ngoài [{L['min_p']}, {L['max_p']}]")
    except (TypeError, ValueError): errs.append("xác suất không phải số")
    refs = p.get("evidence_refs") or []
    if p.get("requires_evidence", True):
        if not refs: errs.append("không có evidence_refs")
        missing = [r for r in refs if r not in fact_ids]
        if missing: errs.append(f"nguồn không tồn tại trong Fact Layer: {missing}")
    if not str(p.get("claim", "")).strip(): errs.append("thiếu claim")
    return errs

def record(preds, as_of, universe, fact_ids, close):
    """Kiểm toán rồi ghi. Trả về (đã ghi, bị loại). Đường ghi đóng → không ghi gì vào sổ, mọi dự báo bị loại."""
    if not forecasts_open():
        return [], [{**p, "audit_errors": [GATE_REASON]} for p in preds]
    ok, rejected = [], []
    for p in preds:
        errs = audit(p, universe, fact_ids, as_of)
        if errs:
            rejected.append({**p, "audit_errors": errs}); continue
        row = _finite(_engine_row(p, as_of, base_rate(close, p["ticker"], int(p["horizon"]))))
        bad = engine_row_error(row)                      # engine không ghi dòng mà chính nó sẽ không đọc lại được
        if bad:
            rejected.append({**p, "audit_errors": [f"dòng không đúng hợp đồng: {bad}"]}); continue
        ok.append(row)
    _append_chained(PRED, ok)
    if rejected:
        _append("ledger/rejected.jsonl", [{**r, "rejected_at": as_of} for r in rejected])
    return ok, rejected

# ---------------- RESOLUTION (code) ----------------
def resolve(close, as_of, bad=None):
    """Chấm bằng GIÁ ĐIỀU CHỈNH. Mã có ô lỗi dữ liệu trong cửa sổ chấm → VOID (không tính điểm);
    mã khác có lỗi trong cửa sổ bị loại khỏi bình quân universe. Đường ghi của engine đóng → không chấm, không ghi gì."""
    if not forecasts_open():
        return []
    done = {r.get("prediction_id") for r in _load(RES)}
    idx = close.index
    new = []
    for p in _load(PRED):
        if not is_engine_row(p): continue                # dự báo từ Issue (phân định theo nguồn, không bằng giá) và dòng sai hợp đồng
        if p["id"] in done: continue
        rr = p["resolution_rule"]; h = rr["horizon"]
        c = pd.Timestamp(p["created_at"])
        pos = idx.searchsorted(c, side="right")          # phiên kế tiếp = điểm vào lệnh
        if pos + h >= len(idx): continue                 # chưa đến hạn
        t0, t1 = idx[pos], idx[pos + h]
        ret = close.loc[t1] / close.loc[t0] - 1
        if bad is not None:
            dirty = bad.loc[(bad.index > t0) & (bad.index <= t1)].any()
            if bool(dirty.get(rr["ticker"], False)):
                new.append({"prediction_id": p["id"], "resolved_at": as_of, "entry_date": str(t0.date()),
                            "exit_date": str(t1.date()), "excess_return": None, "outcome": None,
                            "void": "lỗi dữ liệu giá trong cửa sổ chấm"})
                continue
            ret = ret[~dirty.reindex(ret.index).fillna(False).astype(bool)]
        if pd.isna(ret.get(rr["ticker"])): continue
        excess = float(ret[rr["ticker"]] - ret.mean())
        new.append({"prediction_id": p["id"], "resolved_at": as_of, "entry_date": str(t0.date()),
                    "exit_date": str(t1.date()), "excess_return": round(excess, 5), "outcome": int(excess > 0)})
    _append_chained(RES, new)
    return new

# ---------------- SCORECARD (code) ----------------
TARGET_DISAGREEMENTS = 194        # ARCHITECTURE v3.0 §4.2: phát hiện A đúng 60% so với 50%, độ mạnh 80%, α 0,05

MIN_PAIRS_FOR_RATE_WARNING = 60   # governance/CONTROL_B_PROMPT.md: "dưới 10% sau 60 câu" thì mở ADR đổi nhóm B

def _calibration(ps, os_):
    out = {}
    for k in range(10):
        lo, hi = k / 10, (k + 1) / 10
        idx = [i for i, p in enumerate(ps) if lo <= p < hi or (k == 9 and p == 1.0)]
        if idx:
            out[f"{lo:.1f}-{hi:.1f}"] = {"n": len(idx), "mean_p": round(float(np.mean([ps[i] for i in idx])), 3),
                                              "hit_rate": round(float(np.mean([os_[i] for i in idx])), 3)}
    return out

def _binom_two_sided(k, n):
    """p hai phía của kiểm định nhị thức với p0 = 0,5 (khớp cỡ mẫu 194 ở §4.2, vốn tính cho kiểm định hai phía):
    p = 2·P(X ≥ max(k, n−k)), chặn ≤ 1."""
    if not n:
        return 1.0
    m = max(k, n - k)
    return float(min(1.0, 2 * sum(math.comb(n, j) for j in range(m, n + 1)) / 2 ** n))

def _valid_issue_row(p):
    """Dòng Issue đủ để chấm: có id, seat A/B, p là số trong (0, 1). Dòng hỏng không được làm vỡ vòng học."""
    try:
        return bool(p.get("id")) and str(p.get("seat")) in ("A", "B") and 0.0 < float(p["p"]) < 1.0
    except (KeyError, TypeError, ValueError):
        return False

def _same_day(a, b):
    try:
        return vn_day(a["issue_created_at"]) == vn_day(b["issue_created_at"])
    except (KeyError, TypeError, ValueError):
        return False

def issue_summary(all_rows, R):
    """Chấm dự báo từ Issue theo ARCHITECTURE v3.0 §4.1 bước 5 và ADR-0003.
    Theo ghế: n, đã phân định, VOID, chờ; Brier, Brier của xác suất nền, hiệu chuẩn.
    Cặp A–B: cùng câu hỏi (question + resolve_at), ghi cùng ngày (giờ VN, §4.2). Bất đồng = hai ghế ở hai phía 0,5.
    Chỉ chấm ĐÚNG/SAI cặp mà cả A và B đã phân định cùng một sự thật.

    Kiểm định CHỐT MẪU — mẫu được xác định khi mở Issue dự báo, không phải lúc phân định (ADR-0003 quyết định 3, ADR-0004):
    - Mẫu chốt = đúng 194 cặp bất đồng ĐẦU TIÊN theo SỐ ISSUE HOÀN TẤT CẶP (số Issue lớn hơn trong hai dự báo A, B của cặp;
      không phải vị trí dòng trong ledger/predictions.jsonl). Cặp nào vào mẫu đã cố định từ trước khi có bất kỳ kết quả
      nào: hủy một câu hỏi, để một câu hỏi không phân định, hay phân định câu này trước câu kia đều không đổi được thành
      phần của mẫu.
    - Phạm vi phép thử (ADR-0002): câu hỏi có luật event_before_date KHÔNG vào phép thử A–B — ghế A được tìm web, ghế B
      thì không, nên với loại câu hỏi mà sự kiện có thể đã xảy ra trước khi hỏi, bất đồng không đo thư viện mà đo việc
      tìm web. Các cặp đó vẫn là cặp, vẫn vào tỷ lệ bất đồng và Brier theo ghế; số của chúng báo riêng.
    - Chỉ ra phán quyết khi CẢ 194 cặp đó đã đóng (phân định YES/NO, hoặc VOID). Còn cặp chưa đóng → "CHƯA ĐỦ MẪU".
    - VOID là một quyền chọn của người phân định (bỏ câu hỏi), nên mỗi cặp VOID trong mẫu được tính theo hướng BẤT LỢI cho
      kết luận đang xét: xét "A hơn B" thì coi A sai ở mọi cặp VOID; xét "B hơn A" thì coi A đúng ở mọi cặp VOID. Hủy một
      câu hỏi vì thế không bao giờ làm kết luận nào dễ đạt hơn.
    - Kiểm định nhị thức hai phía với p0 = 0,5 trên n = 194 (khớp cỡ mẫu §4.2); không xem lại trên mẫu lớn dần.
    Số và tỷ lệ VOID được báo riêng theo ghế, theo cặp và theo cặp bất đồng (khóa "void"). Brier theo ghế chỉ tính dự báo
    đã có kết quả YES/NO; vì hủy có chọn lọc làm đẹp được con số đó, khóa "void" in thêm cho mỗi ghế brier_void_worst:
    Brier trên mọi dự báo đã đóng, trong đó mỗi dự báo VOID tính như thể kết quả ngược với phía nó đứng (ADR-0004).
    Phán quyết A–B chỉ dựa vào phép kiểm định chốt mẫu ở trên."""
    R = [r for r in R if r.get("resolution_issue") is not None]   # dự báo Issue chỉ nhận kết quả từ Issue 'Resolution'
    done = {r.get("prediction_id") for r in R}
    outcome = {r.get("prediction_id"): int(r["outcome"]) for r in R if r.get("outcome") in (0, 1)}
    void_ids = {r.get("prediction_id") for r in R if r.get("outcome") is None}
    raw = [p for p in all_rows if is_issue_row(p)]
    issue = [p for p in raw if _valid_issue_row(p)]
    by_seat, scores = {}, {}
    for p in issue:
        d = by_seat.setdefault(str(p["seat"]), {"n": 0, "resolved": 0, "void": 0, "pending": 0})
        d["n"] += 1
        if p["id"] in outcome: d["resolved"] += 1
        elif p["id"] in void_ids: d["void"] += 1
        elif p["id"] not in done: d["pending"] += 1
    for s in sorted(by_seat):
        rows = [p for p in issue if str(p["seat"]) == s and p["id"] in outcome]
        if not rows:
            continue
        ps = [float(p["p"]) for p in rows]; os_ = [outcome[p["id"]] for p in rows]
        bs = []
        for p in rows:
            try: bs.append(min(1.0, max(0.0, float(p.get("base_rate", 0.5)))))
            except (TypeError, ValueError): bs.append(0.5)
        scores[s] = {"n": len(rows), "brier": round(float(np.mean([(a - b) ** 2 for a, b in zip(ps, os_)])), 4),
                     "brier_base_rate": round(float(np.mean([(a - b) ** 2 for a, b in zip(bs, os_)])), 4),
                     "brier_coin": round(float(np.mean([(0.5 - b) ** 2 for b in os_])), 4),
                     "mean_p": round(float(np.mean(ps)), 3), "hit_rate": round(float(np.mean(os_)), 3),
                     "calibration": _calibration(ps, os_)}
    by_q = {}
    for p in sorted(issue, key=lambda r: r.get("issue_number", 0)):
        by_q.setdefault(_qkey(p), {"A": [], "B": []})[str(p["seat"])].append(p)
    pairs, unpaired, not_same_day = [], 0, 0
    for g in by_q.values():
        for a, b in zip(g["A"], g["B"]):
            if _same_day(a, b): pairs.append((a, b))
            else: not_same_day += 1
        unpaired += abs(len(g["A"]) - len(g["B"]))
    dis_all = [(a, b) for a, b in pairs if (float(a["p"]) - 0.5) * (float(b["p"]) - 0.5) < 0]
    out_of_scope = lambda ab: ab[0].get("resolution_rule") == "event_before_date"   # ADR-0002: ngoài phạm vi phép thử A–B
    dis = [ab for ab in dis_all if not out_of_scope(ab)]
    is_void = lambda ab: ab[0]["id"] in void_ids or ab[1]["id"] in void_ids      # một VOID hủy cả câu hỏi
    both = [(a, b) for a, b in dis if a["id"] in outcome and b["id"] in outcome]
    inconsistent = sum(1 for a, b in dis_all if a["id"] in outcome and b["id"] in outcome and outcome[a["id"]] != outcome[b["id"]])
    resolved_ids = {a["id"] for a, b in both if outcome[a["id"]] == outcome[b["id"]]}
    is_res = lambda ab: ab[0]["id"] in resolved_ids and not is_void(ab)           # cả hai đã phân định cùng một sự thật
    def right(a): return (float(a["p"]) > 0.5) == (outcome[a["id"]] == 1)
    dis_res, dis_void = [ab for ab in dis if is_res(ab)], [ab for ab in dis if is_void(ab)]
    n_all, a_all = len(dis_res), sum(1 for a, _ in dis_res if right(a))
    # MẪU CHỐT: 194 cặp bất đồng đầu tiên theo số Issue hoàn tất cặp — cố định trước khi có kết quả; phân định sau không đổi được.
    recorded = lambda ab: max(ab[0].get("issue_number", 0), ab[1].get("issue_number", 0))
    fixed = sorted(dis, key=recorded)[:TARGET_DISAGREEMENTS]
    n = len(fixed)
    v = sum(1 for ab in fixed if is_void(ab))
    r = sum(1 for ab in fixed if is_res(ab))
    k = sum(1 for ab in fixed if is_res(ab) and right(ab[0]))
    full = n == TARGET_DISAGREEMENTS and r + v == n                              # đủ 194 cặp VÀ cả 194 cặp đã đóng
    p_a = _binom_two_sided(k, n) if full else None                               # xét "A hơn B": mọi cặp VOID coi như A sai
    p_b = _binom_two_sided(k + v, n) if full else None                           # xét "B hơn A": mọi cặp VOID coi như A đúng
    verdict = ((f"CHƯA ĐỦ MẪU ({r + v}/{TARGET_DISAGREEMENTS} cặp bất đồng đầu tiên đã phân định hoặc VOID; đã ghi {n} cặp)")
               if not full else
               "A HƠN B CÓ Ý NGHĨA" if p_a < 0.05 and k > n / 2 else
               "B HƠN A CÓ Ý NGHĨA" if p_b < 0.05 and k + v < n / 2 else "CHƯA THẤY KHÁC BIỆT A–B")
    ab = {"pairs": len(pairs), "unpaired": unpaired, "not_same_day": not_same_day, "disagreements": len(dis),
          "disagreements_out_of_scope": len(dis_all) - len(dis),
          "disagreement_rate": round(len(dis_all) / len(pairs), 3) if pairs else None,
          "disagreements_resolved": n_all, "disagreements_void": len(dis_void), "inconsistent_outcomes": inconsistent,
          "a_correct": a_all, "a_accuracy": round(a_all / n_all, 3) if n_all else None,
          "target_disagreements": TARGET_DISAGREEMENTS,
          "fixed_sample": {"n": n, "resolved": r, "void": v, "open": n - r - v, "a_correct": k,
                           "p_value_void_as_a_wrong": round(p_a, 4) if p_a is not None else None,
                           "p_value_void_as_a_right": round(p_b, 4) if p_b is not None else None},
          "verdict": verdict}
    if v:
        ab["void_rule"] = (f"{v} cặp bất đồng trong mẫu chốt bị VOID: tính A sai khi xét 'A hơn B', tính A đúng khi xét 'B hơn A' "
                           "(ADR-0003 quyết định 3)")
    if inconsistent:
        ab["warning_inconsistent"] = f"{inconsistent} cặp có hai outcome khác nhau cho cùng câu hỏi — kiểm ledger/resolutions.jsonl"
    if len(pairs) >= MIN_PAIRS_FOR_RATE_WARNING and len(dis_all) / len(pairs) < 0.10:
        ab["warning"] = "tỷ lệ bất đồng < 10% sau 60 cặp: mở ADR đổi nhóm B sang nhà cung cấp khác (CONTROL_B_PROMPT, ARCHITECTURE §9)"
    rate = lambda x, y: round(x / y, 3) if y else None
    pairs_void, pairs_closed = sum(1 for ab_ in pairs if is_void(ab_)), sum(1 for a, b in pairs if a["id"] in done and b["id"] in done)
    def worst(s):
        """Brier của ghế trên mọi dự báo đã đóng; dự báo VOID tính như kết quả ngược phía nó đứng (p = 0,5 → 0,25)."""
        e = [(float(p["p"]) - outcome[p["id"]]) ** 2 if p["id"] in outcome else max(float(p["p"]), 1 - float(p["p"])) ** 2
             for p in issue if str(p["seat"]) == s and (p["id"] in outcome or p["id"] in void_ids)]
        return round(float(np.mean(e)), 4) if e else None
    void = {"by_seat": {s: {"void": d["void"], "closed": d["void"] + d["resolved"], "rate": rate(d["void"], d["void"] + d["resolved"]),
                            "brier_void_worst": worst(s)}
                        for s, d in sorted(by_seat.items())},
            "pairs": {"void": pairs_void, "closed": pairs_closed, "rate": rate(pairs_void, pairs_closed)},
            "disagreements": {"void": len(dis_void), "closed": n_all + len(dis_void),
                              "rate": rate(len(dis_void), n_all + len(dis_void))}}
    out = {"total": len(raw), "by_seat": by_seat, "scores": scores, "ab": ab, "void": void}
    if len(raw) != len(issue):
        out["malformed"] = len(raw) - len(issue)
    return out

def scorecard(as_of):
    all_rows = _load(PRED)
    P = {p["id"]: p for p in all_rows if is_engine_row(p)}
    R = _load(RES)
    rows = [{**P[r["prediction_id"]], **r} for r in R if r.get("prediction_id") in P and r.get("outcome") is not None]
    void = sum(1 for r in R if r.get("prediction_id") in P and r.get("outcome") is None)
    out = {"as_of": as_of, "total_predictions": len(all_rows), "resolved": len(rows), "void_data_error": void,
           "issue_forecasts": issue_summary(all_rows, R), "procedures": {}}
    if rows:
        df = pd.DataFrame(rows)
        for proc, g in df.groupby("procedure"):
            p, o, b = g.probability.astype(float), g.outcome.astype(float), g.base_rate.astype(float)
            brier = float(((p - o) ** 2).mean())
            baselines = {"base_rate": float(((b - o) ** 2).mean()), "coin_0.5": float(((0.5 - o) ** 2).mean())}
            best = min(baselines, key=baselines.get)          # phải thắng baseline MẠNH NHẤT
            brier_base = baselines[best]
            bss = 1 - brier / brier_base if brier_base > 0 else 0.0
            buckets = {}
            for lo in np.arange(0.0, 1.0, 0.1):
                m = (p >= lo) & (p < lo + 0.1)
                if m.sum(): buckets[f"{lo:.1f}-{lo+0.1:.1f}"] = {"n": int(m.sum()), "mean_p": round(float(p[m].mean()), 3),
                                                                "hit_rate": round(float(o[m].mean()), 3)}
            n = len(g)
            verdict = ("CHƯA ĐỦ MẪU" if n < CFG["ledger"]["min_n_for_verdict"] else
                       "HƠN BASELINE" if bss > 0 else "KHÔNG HƠN BASELINE")
            out["procedures"][proc] = {"n": n, "brier": round(brier, 4), "brier_base_rate": round(brier_base, 4),
                                       "brier_skill": round(bss, 4), "best_baseline": best, "hit_rate": round(float(o.mean()), 3),
                                       "mean_p": round(float(p.mean()), 3), "calibration": buckets, "verdict": verdict}
    save_json("reports/scorecard.json", out)
    return out
