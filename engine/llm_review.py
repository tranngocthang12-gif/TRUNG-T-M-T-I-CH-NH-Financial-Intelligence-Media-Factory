"""Tầng LLM phản biện (tùy chọn): Claude đóng vai Devil's Advocate cho mỗi phát hiện mới được thăng hạng.
Chỉ chạy khi có biến môi trường ANTHROPIC_API_KEY. Không bao giờ ra quyết định thay số liệu."""
import json, os, urllib.request
from .config import CFG, path

PROMPT = ("Bạn là Devil's Advocate của TRUNG TÂM TÀI CHÍNH. Dưới đây là một phát hiện định lượng vừa vượt kiểm định "
          "walk-forward trên cổ phiếu Việt Nam. Hãy: (1) nêu giả định yếu nhất, (2) giải thích thay thế khả dĩ "
          "(beta, ngành, thanh khoản, hiệu ứng quy mô, sai sót dữ liệu), (3) dấu hiệu overfit, (4) regime nào có thể "
          "làm nó sai, (5) một phép kiểm tra cụ thể để bác bỏ. Không khuyến nghị mua bán. Trả lời tiếng Việt, ngắn gọn.")

def review(mid, candidate, metrics):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key or not CFG["llm_review"]["enabled"]:
        return None
    body = {"model": CFG["llm_review"]["model"], "max_tokens": 1200, "system": PROMPT,
            "messages": [{"role": "user", "content": json.dumps({"candidate": candidate, "metrics": metrics},
                                                                ensure_ascii=False, default=str)}]}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                 headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                                          "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            text = "".join(b.get("text", "") for b in json.loads(r.read())["content"])
    except Exception as e:
        text = f"(Không gọi được LLM: {e})"
    path(f"research/reviews/{mid}.md").write_text(f"# Phản biện {mid}\n\n{text}\n", encoding="utf-8")
    return text
