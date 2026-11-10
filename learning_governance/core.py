"""Universal ML Factory: bounded, read-only Learning Governance primitives.

Original implementation inspired by reviewed, merged governance concepts in
MINH TRI; no dependency on MINH TRI runtime or its domain-specific rules.
No function here writes state, deploys models, verifies external identities,
or claims that the content of a knowledge record is true.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections import deque
from datetime import datetime
from typing import Any, Iterable, Mapping

SCHEMA = "umlf-knowledge/v1"
STATES = frozenset({
    "UNVERIFIED", "EXPERIMENTAL", "CURRENT", "STALE", "RECHECK_REQUIRED",
    "BLOCKED", "SUPERSEDED", "RETIRED",
})
EVIDENCE_CLASSES = frozenset({
    "OFFICIAL_DOCUMENT", "DIRECT_OBSERVATION", "MEASURED", "SECONDARY",
    "INFERENCE", "HYPOTHESIS",
})
REQUIRED = frozenset({
    "schema", "id", "version", "claim", "state", "scope", "producer_id",
    "evidence_refs", "depends_on", "supersedes", "invalidation_triggers",
})
MATERIAL = frozenset({"CRITICAL", "HIGH", "MEDIUM"})
SHA256 = re.compile(r"^[0-9a-f]{64}$")
IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_:.\-/]{0,127}$")
MAX_RECORDS = 2000
MAX_DEPTH = 64


def digest(value: Any) -> str:
    """Digest a canonical JSON representation; a digest is not source authentication."""
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _sha(value: Any) -> bool:
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def _timestamp(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return t.tzinfo is not None and t.utcoffset() is not None
    except ValueError:
        return False


def _key(obj: Any) -> tuple[str, int] | None:
    if not isinstance(obj, dict):
        return None
    ident, version = obj.get("id"), obj.get("version")
    if not isinstance(ident, str) or not IDENT.fullmatch(ident):
        return None
    if type(version) is not int or version < 1:
        return None
    return (ident, version)


def _keys(value: Any, label: str, *, owner: tuple[str, int] | None = None) -> tuple[list[tuple[str, int]], list[str]]:
    if not isinstance(value, list):
        return [], [f"{label} must be a list"]
    out, errors = [], []
    for item in value:
        key = _key(item)
        if key is None:
            errors.append(f"{label} has malformed pinned reference")
        elif owner is not None and key == owner:
            errors.append(f"{label} contains self-reference")
        else:
            out.append(key)
    if len(out) != len(set(out)):
        errors.append(f"{label} contains duplicate pinned references")
    return out, errors


def validate_record(record: Any) -> list[str]:
    """Validate a neutral knowledge contract, not the truth of the claim."""
    if not isinstance(record, dict):
        return ["record must be an object"]
    errors = []
    missing = REQUIRED - set(record)
    if missing:
        errors.append("missing required keys: " + ", ".join(sorted(missing)))
        return errors
    key = _key(record)
    if record.get("schema") != SCHEMA:
        errors.append("unsupported knowledge schema")
    if key is None:
        errors.append("invalid id/version")
    if not _nonempty(record.get("claim")):
        errors.append("claim is blank")
    if not isinstance(record.get("state"), str) or record.get("state") not in STATES:
        errors.append("unsupported lifecycle state")
    if not _nonempty(record.get("producer_id")):
        errors.append("producer identity declaration missing")
    scope = record.get("scope")
    if not isinstance(scope, dict) or any(not _nonempty(scope.get(k)) for k in
                                          ("task_family", "domain", "applicability")):
        errors.append("scope must declare task_family, domain and applicability")
    else:
        if any(k in scope and not _nonempty(scope[k]) for k in ("provider", "provider_version")):
            errors.append("optional provider/version must be nonempty")
        if "provider_version" in scope and "provider" not in scope:
            errors.append("provider_version requires provider")
    evidence = record.get("evidence_refs")
    if not isinstance(evidence, list):
        errors.append("evidence_refs must be a list")
    else:
        seen = set()
        for item in evidence:
            if not isinstance(item, dict):
                errors.append("evidence must be an object")
                continue
            evid = item.get("id")
            if not _nonempty(evid) or evid in seen:
                errors.append("invalid or duplicate evidence id")
            else:
                seen.add(evid)
            if not _sha(item.get("sha256")) or not _nonempty(item.get("source_locator")):
                errors.append("evidence digest or locator missing")
            if not isinstance(item.get("class"), str) or item.get("class") not in EVIDENCE_CLASSES:
                errors.append("evidence class invalid")
            if not _timestamp(item.get("observed_at")):
                errors.append("evidence timestamp missing timezone")
    _, depend_errors = _keys(record.get("depends_on"), "depends_on", owner=key)
    _, supersede_errors = _keys(record.get("supersedes"), "supersedes", owner=key)
    errors.extend(depend_errors + supersede_errors)
    invalidates = record.get("invalidation_triggers")
    if not isinstance(invalidates, list) or any(not _nonempty(v) for v in invalidates):
        errors.append("invalidation_triggers must be a list of nonempty strings")
    elif len(invalidates) != len(set(invalidates)):
        errors.append("duplicate invalidation triggers")
    if record.get("state") == "CURRENT":
        if not evidence:
            errors.append("CURRENT record requires evidence")
        if not _nonempty(record.get("acceptance_ref")):
            errors.append("CURRENT record requires external acceptance reference")
    return sorted(set(errors))


def _index(records: Iterable[dict[str, Any]], *, validate_all: bool = True) -> tuple[dict[tuple[str, int], dict], list[str]]:
    result, errors = {}, []
    try:
        records = list(records)
    except TypeError:
        return {}, ["records must be iterable"]
    if len(records) > MAX_RECORDS:
        return {}, ["knowledge graph exceeds safe bound"]
    for i, record in enumerate(records):
        if validate_all:
            errors.extend(f"row {i}: {e}" for e in validate_record(record))
        key = _key(record)
        if key is None:
            continue
        if key in result:
            errors.append(f"duplicate knowledge key: {key[0]}@{key[1]}")
        else:
            result[key] = record
    return result, sorted(set(errors))


def check_dependency_closure(
    records: Iterable[dict[str, Any]], target: dict[str, Any],
    *, root_states: tuple[str, ...] = ("CURRENT",),
) -> dict[str, Any]:
    """Fail closed on missing, stale, ambiguous, cyclic or superseded pinned facts."""
    index, errors = _index(records, validate_all=False)
    root = _key(target)
    if root is None or root not in index:
        errors.append("missing or invalid root pinned reference")
    if errors:
        return {"allowed": False, "reasons": sorted(set(errors)), "closure": []}

    superseded = set()
    for key, record in index.items():
        if record.get("state") == "CURRENT":
            refs, _ = _keys(record.get("supersedes", []), "supersedes")
            superseded.update(refs)

    visiting, visited = set(), set()

    def walk(key: tuple[str, int], depth: int, is_root: bool) -> None:
        if key in visiting:
            errors.append(f"knowledge dependency cycle at {key[0]}@{key[1]}")
            return
        if key in visited:
            return
        if depth > MAX_DEPTH:
            errors.append("dependency depth exceeds safe bound")
            return
        record = index.get(key)
        if record is None:
            errors.append(f"missing pinned dependency: {key[0]}@{key[1]}")
            return
        errors.extend(f"invalid pinned {key[0]}@{key[1]}: {e}" for e in validate_record(record))
        allowed_states = root_states if is_root else ("CURRENT",)
        if record.get("state") not in allowed_states:
            errors.append(f"stale or unestablished dependency: {key[0]}@{key[1]}")
        if key in superseded:
            errors.append(f"superseded dependency: {key[0]}@{key[1]}")
        visiting.add(key)
        deps, ref_errors = _keys(record.get("depends_on"), "depends_on")
        errors.extend(ref_errors)
        for dep in deps:
            walk(dep, depth + 1, False)
        visiting.remove(key)
        visited.add(key)

    walk(root, 0, True)
    return {"allowed": not errors, "reasons": sorted(set(errors)),
            "closure": [{"id": k[0], "version": k[1]} for k in sorted(visited)]}


def invalidation_impact(
    records: Iterable[dict[str, Any]], changed: Iterable[dict[str, Any]],
    *, event: str | None = None,
) -> dict[str, Any]:
    """Compute minimal transitive invalidation radius; does not edit record states."""
    index, errors = _index(records)
    try:
        changed = list(changed)
    except TypeError:
        changed = []
        errors.append("changed must be iterable")
    roots = [_key(k) for k in changed]
    if not roots or any(k is None or k not in index for k in roots):
        errors.append("changed keys must refer to existing records")
    if event is not None and not _nonempty(event):
        errors.append("event must be nonempty")
    if errors:
        return {"valid": False, "reasons": sorted(set(errors)), "affected": [], "state_changed": False}
    reverse: dict[tuple[str, int], set[tuple[str, int]]] = {}
    for key, rec in index.items():
        deps, _ = _keys(rec["depends_on"], "depends_on")
        for dep in deps:
            reverse.setdefault(dep, set()).add(key)
    queue = deque(k for k in roots if event is None or event in index[k]["invalidation_triggers"])
    affected = set(queue)
    while queue:
        key = queue.popleft()
        for child in reverse.get(key, ()):
            if child not in affected:
                affected.add(child)
                queue.append(child)
    return {"valid": True, "reasons": [],
            "affected": [{"id": k[0], "version": k[1]} for k in sorted(affected)],
            "state_changed": False}


def check_scope(record: Mapping[str, Any], context: Mapping[str, str]) -> list[str]:
    """Scope is exact-match, including provider version; no silent version inheritance."""
    if not isinstance(context, Mapping) or not isinstance(record, Mapping):
        return ["scope/context must be objects"]
    scope = record.get("scope")
    if not isinstance(scope, dict):
        return ["missing knowledge scope"]
    errors = []
    for name in ("task_family", "domain", "provider", "provider_version"):
        if name not in scope:
            continue
        if name in ("task_family", "domain") and scope[name] == "*":
            continue
        if scope[name] != context.get(name):
            errors.append(f"runtime context differs from validated scope: {name}")
    return errors


def inspect_promotion(
    records: Iterable[dict[str, Any]], target: dict[str, Any],
    *, evidence_snapshots: Mapping[str, bytes],
    evaluation: Mapping[str, Any], review: Mapping[str, Any],
    runtime_context: Mapping[str, str],
) -> dict[str, Any]:
    """Inspect EXPERIMENTAL -> CURRENT as a proposal only; never self-promote."""
    records = list(records)
    key = _key(target)
    errors = []
    graph = check_dependency_closure(records, target, root_states=("EXPERIMENTAL",))
    errors.extend(graph["reasons"])
    index, index_errors = _index(records, validate_all=False)
    errors.extend(index_errors)
    if key is not None and key in index:
        try:
            if digest(index[key]) != digest(target):
                errors.append("candidate differs from registered pinned record")
        except (TypeError, ValueError):
            errors.append("candidate or registered record cannot be hashed")
    if key is None:
        errors.append("invalid candidate key")
    if not isinstance(target, dict):
        errors.append("invalid candidate object")
        target = {}
    errors.extend(check_scope(target, runtime_context))
    evidence = target.get("evidence_refs", [])
    if not isinstance(evidence, list) or not evidence:
        errors.append("promotion requires evidence")
        evidence = []
    if not isinstance(evidence_snapshots, Mapping):
        errors.append("evidence snapshot mapping missing")
        evidence_snapshots = {}
    eligible_evidence_classes = {"OFFICIAL_DOCUMENT", "DIRECT_OBSERVATION", "MEASURED"}
    if not any(isinstance(r, dict) and r.get("class") in eligible_evidence_classes for r in evidence):
        errors.append("inference-only evidence cannot promote")
    for item in evidence:
        if not isinstance(item, dict):
            continue
        evidence_id = item.get("id")
        raw = evidence_snapshots.get(evidence_id) if _nonempty(evidence_id) else None
        if not isinstance(raw, bytes) or hashlib.sha256(raw).hexdigest() != item.get("sha256"):
            errors.append("missing or mismatched evidence snapshot: " + str(item.get("id")))
    try:
        candidate_sha = digest(target)
    except (TypeError, ValueError):
        candidate_sha = None
        errors.append("candidate cannot be hashed")
    if not isinstance(evaluation, Mapping):
        evaluation = {}
    required_eval = (
        evaluation.get("candidate_sha256") == candidate_sha
        and _sha(evaluation.get("frozen_packet_sha256"))
        and evaluation.get("preregistered") is True
        and evaluation.get("heldout_test") is True
        and evaluation.get("baseline_present") is True
        and evaluation.get("result") == "PASS"
        and _nonempty(evaluation.get("receipt_ref"))
    )
    if not required_eval:
        errors.append("missing or unbound preregistered held-out evaluation receipt")
    if not isinstance(review, Mapping):
        review = {}
    reviewer = review.get("reviewer_id")
    if (review.get("candidate_sha256") != candidate_sha
            or not _nonempty(reviewer)
            or str(reviewer).strip().casefold() == str(target.get("producer_id", "")).strip().casefold()
            or review.get("verdict") != "NO_MATERIAL_DEFECT"
            or not _nonempty(review.get("receipt_ref"))):
        errors.append("missing exact-target separate-actor critique")
    findings = review.get("findings")
    if not isinstance(findings, list):
        errors.append("review findings must be explicit list")
    else:
        for item in findings:
            if not isinstance(item, Mapping) or item.get("severity") not in MATERIAL | {"LOW"} or item.get("status") not in ("OPEN", "RESOLVED"):
                errors.append("invalid critic finding")
            elif item["severity"] in MATERIAL:
                if item["status"] != "RESOLVED":
                    errors.append("unresolved material critic finding")
                elif not _nonempty(item.get("disposition_ref")):
                    errors.append("resolved material finding missing disposition evidence")
    return {
        "ready_for_external_approval": not errors,
        "reasons": sorted(set(errors)),
        "proposed_transition": "EXPERIMENTAL_TO_CURRENT",
        "state_changed": False,
        "verified": False,
        "critic_independence_proven": False,
        "source_authenticity_proven": False,
        "production_ready": False,
        "approval_required": True,
    }


def compare_parent_candidate(
    frozen_packet: Mapping[str, Any],
    parent: Mapping[str, Any], challenger: Mapping[str, Any],
) -> dict[str, Any]:
    """Return metric-guardrail eligibility, never a model promotion or causal proof."""
    errors, improvements = [], []
    if not isinstance(frozen_packet, Mapping) or frozen_packet.get("frozen") is not True:
        return _candidate_out(["evaluation packet must be frozen"], improvements)
    metrics = frozen_packet.get("metric_specs")
    if (not isinstance(metrics, list) or not metrics or
        not _nonempty(frozen_packet.get("dataset_version")) or
        not _nonempty(frozen_packet.get("task_family"))):
        return _candidate_out(["invalid frozen dataset or metrics contract"], improvements)
    try:
        sha = digest(frozen_packet)
    except (TypeError, ValueError):
        return _candidate_out(["evaluation packet is not canonical JSON"], improvements)
    if not isinstance(parent, Mapping) or not isinstance(challenger, Mapping):
        return _candidate_out(["evaluations must be objects"], improvements)
    if parent.get("packet_sha256") != sha or challenger.get("packet_sha256") != sha:
        errors.append("parent and challenger not bound to the same exact frozen packet")
    if (not _nonempty(parent.get("run_ref")) or not _nonempty(challenger.get("run_ref"))
            or parent.get("run_ref") == challenger.get("run_ref")):
        errors.append("missing or duplicate evaluation run references")
    required_integrity = {"leakage", "security", "reproducibility", "authority", "data_contract"}
    for result in (parent, challenger):
        failures = result.get("critical_failures")
        if not isinstance(failures, dict) or set(failures) != required_integrity or any(type(v) is not int or v < 0 for v in failures.values()):
            errors.append("critical failure counters must be nonnegative integers")
        elif any(failures.values()):
            errors.append("evaluation has leakage, safety, authority or reproducibility failure")
    p_values, c_values = parent.get("metrics"), challenger.get("metrics")
    if not isinstance(p_values, dict) or not isinstance(c_values, dict):
        return _candidate_out(errors + ["missing metric results"], improvements)
    seen = set()
    has_primary = False
    for spec in metrics:
        if not isinstance(spec, dict):
            errors.append("invalid metric spec")
            continue
        name, direction, role = spec.get("name"), spec.get("direction"), spec.get("role")
        delta = spec.get("min_improvement", 0.0)
        if not _nonempty(name) or name in seen or direction not in ("MAX", "MIN") or role not in ("PRIMARY", "GUARDRAIL"):
            errors.append("invalid or duplicate metric definition")
            continue
        seen.add(name)
        if role == "PRIMARY":
            has_primary = True
        if type(delta) not in (int, float) or not math.isfinite(delta) or delta < 0:
            errors.append("minimum improvement must be finite nonnegative")
            continue
        pv, cv = p_values.get(name), c_values.get(name)
        if (type(pv) not in (int, float) or type(cv) not in (int, float)
                or not math.isfinite(pv) or not math.isfinite(cv)):
            errors.append("missing/nonfinite metric result: " + name)
            continue
        advantage = (cv - pv) if direction == "MAX" else (pv - cv)
        if advantage < 0:
            errors.append("metric regression: " + name)
        if role == "PRIMARY" and advantage > delta:
            improvements.append(name)
    if not has_primary:
        errors.append("at least one primary metric is required")
    if set(p_values) != seen or set(c_values) != seen:
        errors.append("evaluations must contain exactly the frozen metrics")
    if not improvements:
        errors.append("no primary metric cleared the preregistered improvement margin")
    return _candidate_out(sorted(set(errors)), improvements)


def _candidate_out(errors: list[str], improvements: list[str]) -> dict[str, Any]:
    return {
        "candidate_eligible_for_external_review": not errors,
        "improved_primary_metrics": sorted(set(improvements)),
        "reasons": sorted(set(errors)),
        "state_changed": False,
        "model_promoted": False,
        "measured_improvement_independently_proven": False,
    }


def _wilson_rate_interval(successes: int, total: int, z: float = 1.6448536269514722) -> tuple[float, float]:
    if total == 0:
        return (0.0, 1.0)
    p = successes / total
    divisor = 1 + z * z / total
    center = (p + z * z / (2 * total)) / divisor
    radius = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / divisor
    return max(0., center - radius), min(1., center + radius)


def canary_truth_digest(cases: Iterable[dict[str, Any]]) -> str:
    """Freeze only ground truth, excluding predicted results to resist post-hoc edits."""
    fields = ("case_id", "expected_defect", "subtle", "historical", "hard_negative",
              "truth_span", "trap_author", "rubric_author", "adjudicator", "human_adjudicated")
    return digest([{k: row.get(k) for k in fields} for row in cases])


def score_critic_canary(
    cases: Iterable[dict[str, Any]], contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Canary assessment with sample-size floors and one-sided Wilson bounds.

    Even a PASS is distribution-scoped. Role names and ground truth are declarations;
    this function cannot authenticate their authors or certify critic independence.
    """
    try:
        rows = list(cases)
    except TypeError:
        rows = []
    errors = []
    if any(not isinstance(row, dict) for row in rows):
        return {"structural_canary_pass": False, "reasons": ["invalid canary record"],
                "counts": {}, "critic_reliability_proven": False,
                "critic_independence_proven": False, "state_changed": False}
    if not isinstance(contract, Mapping):
        contract = {}
    if not 0 < len(rows) <= 500:
        errors.append("canary dataset size out of bounds")
    if contract.get("single_use") is not True or type(contract.get("prior_exposures")) is not int or contract.get("prior_exposures") != 0:
        errors.append("canary must be frozen single-use")
    if not _timestamp(contract.get("preregistered_at")):
        errors.append("missing preregistration timestamp")
    try:
        actual_truth_sha = canary_truth_digest(rows)
    except (TypeError, ValueError, OverflowError):
        actual_truth_sha = None
        errors.append("canary truth is not canonical JSON")
    if contract.get("truth_sha256") != actual_truth_sha or actual_truth_sha is None:
        errors.append("frozen canary truth hash mismatch")
    unique_ids = set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append("invalid canary record")
            continue
        if not _nonempty(row.get("case_id")) or row["case_id"] in unique_ids:
            errors.append("canary duplicate/invalid case id")
        else:
            unique_ids.add(row["case_id"])
        names = [row.get(k) for k in ("trap_author", "rubric_author", "adjudicator")]
        if not all(_nonempty(n) for n in names) or len({str(n).strip().casefold() for n in names}) != 3:
            errors.append("canary ground-truth roles not separated")
        if row.get("human_adjudicated") is not True:
            errors.append("canary truth not adjudicated")
        for k in ("expected_defect", "subtle", "historical", "hard_negative", "predicted_defect"):
            if type(row.get(k)) is not bool:
                errors.append("invalid canary boolean: " + k)
        if row.get("expected_defect") is True and type(row.get("localized_correctly")) is not bool:
            errors.append("missing defect localization evaluation")
    bad = [r for r in rows if r.get("expected_defect") is True]
    clean = [r for r in rows if r.get("expected_defect") is False]
    subtle = [r for r in bad if r.get("subtle") is True]
    floors = {"total": 40, "bad": 20, "clean": 20, "subtle": 10}
    actual = {"total": len(rows), "bad": len(bad), "clean": len(clean), "subtle": len(subtle)}
    for key, floor in floors.items():
        required = contract.get("minimum_" + key)
        if type(required) is not int or required < floor or actual[key] < required:
            errors.append(f"insufficient frozen {key} canary sample")
    if not any(r.get("historical") is True for r in bad):
        errors.append("historical defects missing")
    if not any(r.get("hard_negative") is True for r in clean):
        errors.append("clean hard negatives missing")
    limits = {}
    for name in ("max_false_acceptance_upper95", "max_false_rejection_upper95", "min_subtle_detection_lower95"):
        value = contract.get(name)
        if type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value <= 1:
            errors.append("invalid preregistered threshold: " + name)
        else:
            limits[name] = float(value)
    false_acceptances = sum(r.get("predicted_defect") is False for r in bad)
    false_rejections = sum(r.get("predicted_defect") is True for r in clean)
    subtle_hits = sum(r.get("predicted_defect") is True and r.get("localized_correctly") is True for r in subtle)
    far_lower, far_upper = _wilson_rate_interval(false_acceptances, len(bad))
    frr_lower, frr_upper = _wilson_rate_interval(false_rejections, len(clean))
    subtle_lower, subtle_upper = _wilson_rate_interval(subtle_hits, len(subtle))
    if "max_false_acceptance_upper95" in limits and far_upper > limits["max_false_acceptance_upper95"]:
        errors.append("false-acceptance uncertainty bound exceeds threshold")
    if "max_false_rejection_upper95" in limits and frr_upper > limits["max_false_rejection_upper95"]:
        errors.append("false-rejection uncertainty bound exceeds threshold")
    if "min_subtle_detection_lower95" in limits and subtle_lower < limits["min_subtle_detection_lower95"]:
        errors.append("subtle-error uncertainty bound below threshold")
    return {
        "structural_canary_pass": not errors,
        "reasons": sorted(set(errors)),
        "counts": actual,
        "false_acceptance_upper95": round(far_upper, 4),
        "false_rejection_upper95": round(frr_upper, 4),
        "subtle_detection_lower95": round(subtle_lower, 4),
        "critic_reliability_proven": False,
        "critic_independence_proven": False,
        "state_changed": False,
    }
