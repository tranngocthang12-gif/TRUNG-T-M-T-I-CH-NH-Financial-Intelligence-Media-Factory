"""Chuyên gia Claude — Giai đoạn 1: NEWS/EVENT + DEVIL'S ADVOCATE.
Vòng độc lập: Devil's Advocate là lần gọi riêng, trả XÁC SUẤT RIÊNG cho cùng câu hỏi và cũng bị chấm điểm."""
import json, os, random, re, urllib.request
import pandas as pd
from .config import CFG, ROOT, load_json
from . import budget, facts, ledger

V_NEWS, V_DA = "news@v1", "devils_advocate@v1"

SYS_NEWS = """Bạn là chuyên gia NEWS/EVENT của TRUNG TÂM TÀI CHÍNH (thị trường chứng khoán Việt Nam).
Nhiệm vụ: từ tin tức được cung cấp, đưa ra DỰ BÁO XÁC SUẤT kiểm chứng được. Không khuyến nghị mua bán.
Luật bắt buộc:
- Chỉ dùng mã có trong danh sách ứng viên. Chỉ trích evidence_refs bằng đúng id tin được cung cấp.
- Câu hỏi luôn là: mã X có lợi nhuận VƯỢT bình quân universe trong H phiên không (H ∈ {5, 20}).
- probability trong [0.05, 0.95]. Xác suất nền (base_rate) do hệ thống tính sẵn; chỉ lệch khỏi nó khi tin tức thật sự có thông tin mới chưa phản ánh vào giá.
- Nếu tin không đủ thông tin mới, BỎ QUA mã đó. Ít dự báo tốt hơn nhiều dự báo kém.
- Không tự tính toán số liệu; dùng số trong phần context.
Trả về DUY NHẤT JSON: {"predictions":[{"ticker":"","horizon":20,"probability":0.5,"claim":"","evidence_refs":["N-..."],"note":""}]}"""

SYS_DA = """Bạn là DEVIL'S ADVOCATE của TRUNG TÂM TÀI CHÍNH. Bạn KHÔNG thấy lập luận gốc, chỉ thấy claim và bằng chứng.
Với mỗi mục, hãy tìm giả định yếu nhất, giải thích thay thế (beta thị trường, ngành, tin đã phản ánh vào giá, thanh khoản),
rồi đưa ra XÁC SUẤT RIÊNG của bạn cho CÙNG câu hỏi. Bạn cũng bị chấm điểm — phản biện có trách nhiệm, không phản biện cho có.
probability trong [0.05, 0.95]. Trả về DUY NHẤT JSON:
{"reviews":[{"ref":"<id mục>","probability":0.5,"weakest_assumption":"","alternative_explanation":""}]}"""

def _call(system, user, as_of, procedure):
    if os.environ.get("TTC_MOCK_LLM"):
        return _mock(system, user), {"input_tokens": 0, "output_tokens": 0}
    e = CFG["experts"]
    body = {"model": e["model"], "max_tokens": e["max_tokens"], "system": system,
            "messages": [{"role": "user", "content": user}]}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                 headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                                          "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.loads(r.read())
    usage = d.get("usage", {})
    budget.record(as_of, procedure, usage)
    return "".join(b.get("text", "") for b in d.get("content", [])), usage

def _json(text):
    m = re.search(r"\{.*\}", text.replace("```json", "").replace("```", ""), re.S)
    return json.loads(m.group(0)) if m else {}

def _mock(system, user):
    """Giả lập để kiểm thử đường ống (TTC_MOCK_LLM=1). Không dùng khi chạy thật."""
    d = json.loads(user); rnd = random.Random(len(user))
    if system is SYS_NEWS:
        return json.dumps({"predictions": [{"ticker": c["ticker"], "horizon": 20, "probability": round(rnd.uniform(0.3, 0.7), 2),
                                            "claim": f"mock claim {c['ticker']}", "evidence_refs": [c["news"][0]["id"]]}
                                           for c in d["candidates"]]})
    return json.dumps({"reviews": [{"ref": it["ref"], "probability": round(rnd.uniform(0.3, 0.7), 2),
                                    "weakest_assumption": "mock", "alternative_explanation": "mock"} for it in d["items"]]})

def _context(close, t):
    r = close[t].pct_change(fill_method=None)
    mkt = close.pct_change(fill_method=None).mean(axis=1)
    return {"ret_5d": round(float(close[t].iloc[-1] / close[t].iloc[-6] - 1), 4),
            "ret_20d": round(float(close[t].iloc[-1] / close[t].iloc[-21] - 1), 4),
            "excess_20d_vs_universe": round(float((1 + r.iloc[-20:]).prod() - (1 + mkt.iloc[-20:]).prod()), 4),
            "vol_20d": round(float(r.iloc[-20:].std()), 4)}

def run(as_of, close):
    st = budget.status(as_of)
    if not st["allowed"]:
        return {"ran": False, "reasons": st["reasons"]}
    universe = list(close.columns)
    cands = facts.candidates(as_of, universe)
    if not cands:
        return {"ran": True, "note": "không có tin nhắc tới mã trong universe", "recorded": 0}
    knowledge = [load_json(f"knowledge/candidates/{p.name}", {}).get("statement")
                 for p in sorted((ROOT / "knowledge/candidates").glob("*.json"))[:10]] if (ROOT / "knowledge/candidates").exists() else []
    payload = {"as_of": as_of, "knowledge_da_kiem_chung": [k for k in knowledge if k],
               "candidates": [{"ticker": t, "context": _context(close, t),
                               "base_rate_20d": ledger.base_rate(close, t, 20), "base_rate_5d": ledger.base_rate(close, t, 5),
                               "news": [{"id": n["id"], "title": n["title"], "summary": n["summary"][:300]} for n in ns[:4]]}
                              for t, ns in list(cands.items())[:CFG["experts"]["max_predictions_per_day"]]]}
    text, _ = _call(SYS_NEWS, json.dumps(payload, ensure_ascii=False), as_of, V_NEWS)
    preds = [{**p, "procedure": V_NEWS} for p in _json(text).get("predictions", [])][:CFG["experts"]["max_predictions_per_day"]]
    fact_ids = {n["id"] for n in facts.load_news()}
    ok, rej = ledger.record(preds, as_of, universe, fact_ids, close)
    da_ok = []
    if ok and budget.status(as_of)["allowed"]:
        items = [{"ref": p["id"], "question": p["question"], "claim": p["claim"], "evidence": p["evidence_refs"],
                  "context": _context(close, p["resolution_rule"]["ticker"]), "base_rate": p["base_rate"]} for p in ok]
        text, _ = _call(SYS_DA, json.dumps({"items": items}, ensure_ascii=False), as_of, V_DA)
        byid = {p["id"]: p for p in ok}
        da = []
        for rv in _json(text).get("reviews", []):
            src = byid.get(rv.get("ref"))
            if not src: continue
            da.append({"procedure": V_DA, "ticker": src["resolution_rule"]["ticker"], "horizon": src["resolution_rule"]["horizon"],
                       "probability": rv.get("probability"), "claim": f"Phản biện {src['id']}: {rv.get('weakest_assumption','')}",
                       "evidence_refs": src["evidence_refs"], "links": {"challenges": src["id"]},
                       "note": rv.get("alternative_explanation", "")})
        da_ok, _ = ledger.record(da, as_of, universe, fact_ids, close)
    return {"ran": True, "recorded": len(ok), "rejected": len(rej), "devils_advocate": len(da_ok)}
