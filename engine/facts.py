"""Fact Layer (Giai đoạn 1: tin tức). Mỗi tin có id = hash(link), nguồn, thời điểm lấy. Trạng thái RAW cho tới khi được đối chiếu."""
import hashlib, json, re, urllib.request, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
import pandas as pd
from .config import CFG, ROOT, path

NEWS = "fact/news.jsonl"

def load_news():
    p = ROOT / NEWS
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

def _clean(t): return re.sub(r"<[^>]+>", " ", t or "").strip()

def ingest_news(as_of):
    seen = {n["id"] for n in load_news()}
    now = pd.Timestamp.now(tz="UTC").isoformat()
    new, errors = [], []
    for url in CFG["news"]["feeds"]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ttc-engine"})
            root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
        except Exception as e:
            errors.append(f"{url}: {str(e)[:120]}"); continue
        for it in root.iter("item"):
            link = (it.findtext("link") or "").strip()
            if not link: continue
            nid = "N-" + hashlib.sha1(link.encode()).hexdigest()[:12]
            if nid in seen: continue
            pub = it.findtext("pubDate")
            try: pub = parsedate_to_datetime(pub).isoformat()
            except Exception: pub = None
            new.append({"id": nid, "source": url, "link": link, "title": _clean(it.findtext("title")),
                        "summary": _clean(it.findtext("description"))[:600], "published_at": pub,
                        "retrieved_at": now, "status": "RAW"})
            seen.add(nid)
    if new:
        with open(path(NEWS), "a", encoding="utf-8") as f:
            for n in new: f.write(json.dumps(n, ensure_ascii=False) + "\n")
    return {"new_items": len(new), "errors": errors}

def candidates(as_of, universe, days=2):
    """Tin trong `days` ngày gần nhất có nhắc tới mã thuộc universe (so khớp bằng code, không bằng LLM)."""
    cut = pd.Timestamp(as_of) - pd.Timedelta(days=days)
    out = {}
    for n in load_news():
        ts = pd.Timestamp(n["retrieved_at"]).tz_localize(None) if n.get("retrieved_at") else None
        if ts is None or ts < cut or ts > pd.Timestamp(as_of) + pd.Timedelta(days=1): continue
        text = f"{n['title']} {n['summary']}"
        for t in universe:
            if re.search(rf"\b{t}\b", text):
                out.setdefault(t, []).append(n)
    return out
