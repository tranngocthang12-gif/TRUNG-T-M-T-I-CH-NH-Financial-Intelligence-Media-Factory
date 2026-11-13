"""Read-only compatibility bridge for legacy engine and Issue Forecast rows.

Never rewrites a frozen ledger row. The only automatically gradeable Issue rule
in this slice is excess_return_positive. Source-dependent rules remain pending.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from zoneinfo import ZoneInfo

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
PRICE_RULE = "excess_return_positive"
NONPRICE_RULES = {"numeric_range", "event_before_date", "comparison"}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_TICKER = re.compile(r"^[A-Z0-9]{2,8}$")


def valid_benchmark_universe(members: object, ticker: object) -> bool:
    """Validate the prospective, hashed constituent snapshot; never infer it from prices."""
    return (type(members) is list and len(members) >= 2
            and all(type(t) is str and _TICKER.fullmatch(t) for t in members)
            and len(set(members)) == len(members)
            and type(ticker) is str and ticker in members)


def _instant(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("missing timestamp")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.utcoffset() is None:
        raise ValueError("timestamp must include UTC offset")
    return dt.astimezone(timezone.utc)


def normalize_prediction(raw: dict) -> tuple[dict | None, str | None]:
    """Return (legacy-shaped read view, blocked_reason). No side effects."""
    if not isinstance(raw, dict):
        return None, "INVALID_ROW"
    if "issue_number" not in raw:
        rr = raw.get("resolution_rule")
        if (isinstance(rr, dict) and rr.get("type") == PRICE_RULE
                and isinstance(raw.get("id"), str)
                and isinstance(raw.get("created_at"), str)
                and isinstance(raw.get("procedure"), str)
                and "probability" in raw and "base_rate" in raw):
            return raw, None
        return None, "INVALID_LEGACY_ROW"

    try:
        if raw.get("ingest_action") != "opened":
            return None, "UNATTESTED_ISSUE_OPEN_EVENT"
        created = _instant(raw["issue_created_at"])
        updated = _instant(raw["issue_updated_at"])
        received = _instant(raw["registered_at"])
        # The event snapshot must reflect the original open, not a late-edited Issue.
        if updated < created or updated > created + timedelta(seconds=30):
            return None, "ISSUE_CHANGED_AFTER_OPEN"
        if received < created:
            return None, "REGISTERED_BEFORE_CREATED"
        if not _HEX64.fullmatch(raw.get("raw_payload_sha256", "")):
            return None, "MISSING_PAYLOAD_DIGEST"
        n = raw["issue_number"]
        if type(n) is not int or n < 1:
            return None, "INVALID_ISSUE_NUMBER"
        seat = raw["seat"]
        if seat not in {"A", "B"}:
            return None, "INVALID_SEAT"
        p, base = float(raw["p"]), float(raw["base_rate"])
        if not (0.05 <= p <= 0.95 and 0 <= base <= 1):
            return None, "INVALID_PROBABILITY"
        issue_day = created.astimezone(VN_TZ).date()
        registered_day = received.astimezone(VN_TZ).date()
        decision_day = max(issue_day, registered_day)
        due = date.fromisoformat(raw["resolve_at"])
        if due <= decision_day:
            return None, "INVALID_DUE_DATE"
        rule = raw["resolution_rule"]
        if rule in NONPRICE_RULES:
            return None, "SOURCE_RESOLVER_NOT_IMPLEMENTED"
        if rule != PRICE_RULE:
            return None, "UNKNOWN_RESOLUTION_RULE"
        ticker = raw["ticker"]
        horizon = raw["horizon"]
        if not isinstance(ticker, str) or not _TICKER.fullmatch(ticker):
            return None, "INVALID_TICKER"
        if type(horizon) is not int or horizon not in (5, 20):
            return None, "INVALID_HORIZON"
        if not isinstance(raw.get("resolution_source"), str) or len(raw["resolution_source"]) < 5:
            return None, "MISSING_RESOLUTION_SOURCE"
    except (KeyError, ValueError, TypeError, OverflowError):
        return None, "INVALID_ISSUE_ROW"
    return {
        "id": f"I-{n}",
        # Never use market prices prior to the actual ledger registration date.
        "created_at": decision_day.isoformat(),
        "original_issue_created_at": created.isoformat(),
        "registered_at": received.isoformat(),
        "procedure": f"issue_{seat}",
        "probability": p,
        "base_rate": base,
        # Only an intake-time immutable snapshot can define the scoring basket.
        # Older Issue rows without it remain readable but cannot be scored.
        "benchmark_universe": raw.get("benchmark_universe"),
        "question": raw.get("question", ""),
        "resolution_rule": {
            "type": PRICE_RULE,
            "ticker": ticker,
            "horizon": horizon,
            "benchmark": "universe_equal_weight",
            "entry": "close_t+1",
        },
        "resolve_at": due.isoformat(),
        "seat": seat,
        "pair_key": hashlib.sha256(json.dumps({
            "day": decision_day.isoformat(), "question": raw.get("question"),
            "resolution_source": raw["resolution_source"],
            "rule": rule, "ticker": ticker, "horizon": horizon,
            "resolve_at": due.isoformat(),
        }, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
        "evidence_refs": raw.get("library_refs", ""),
        "source_issue_number": n,
    }, None


def prepare_predictions(rows: list[dict]) -> tuple[list[dict], dict[str, int]]:
    """Convert rows without mutating them; report unsupported rows explicitly."""
    accepted, blocked, ids = [], {}, set()
    for raw in rows:
        normalized, reason = normalize_prediction(raw)
        if normalized is not None:
            if normalized["id"] in ids:
                blocked["DUPLICATE_FORECAST_ID"] = blocked.get("DUPLICATE_FORECAST_ID", 0) + 1
                continue
            ids.add(normalized["id"])
            accepted.append(normalized)
        else:
            key = reason or "UNKNOWN_ERROR"
            blocked[key] = blocked.get(key, 0) + 1
    return accepted, blocked
