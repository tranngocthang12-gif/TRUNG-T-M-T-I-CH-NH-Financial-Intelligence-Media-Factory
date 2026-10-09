import copy
import hashlib
import unittest

from learning_governance import (
    digest, validate_record, check_dependency_closure, invalidation_impact,
    check_scope, inspect_promotion, compare_parent_candidate,
    canary_truth_digest, score_critic_canary,
)

OBSERVED = "2026-10-09T03:00:00+00:00"
SAMPLE = b"offline evidence bytes"


def record(name="A", state="CURRENT", deps=None, **scope_overrides):
    scope = {"task_family": "TABULAR_CLASSIFICATION", "domain": "demo", "applicability": "fixture"}
    scope.update(scope_overrides)
    result = {
        "schema": "umlf-knowledge/v1", "id": name, "version": 1,
        "claim": "A bounded claim about leakage checks.", "state": state,
        "scope": scope, "producer_id": "learner-seat", "evidence_refs": [{
            "id": "EV-" + name, "sha256": hashlib.sha256(SAMPLE).hexdigest(),
            "source_locator": "fixture/" + name, "class": "MEASURED",
            "observed_at": OBSERVED,
        }],
        "depends_on": deps or [], "supersedes": [],
        "invalidation_triggers": ["source_changed"],
    }
    if state == "CURRENT":
        result["acceptance_ref"] = "owner-reviewed/" + name
    return result


def ref(name, version=1):
    return {"id": name, "version": version}


def promotion_receipts(candidate):
    target_sha = digest(candidate)
    evaluation = {
        "candidate_sha256": target_sha, "frozen_packet_sha256": "a" * 64,
        "preregistered": True, "heldout_test": True, "baseline_present": True,
        "result": "PASS", "receipt_ref": "eval/fixture-001",
    }
    review = {
        "candidate_sha256": target_sha,
        "reviewer_id": "separate-critic", "verdict": "NO_MATERIAL_DEFECT",
        "receipt_ref": "review/fixture-001", "findings": [],
    }
    return evaluation, review


def canary_cases():
    cases = []
    for i in range(40):
        bad = i < 20
        cases.append({
            "case_id": f"C{i:03d}", "expected_defect": bad,
            "subtle": bad and i < 10, "historical": bad and i == 0,
            "hard_negative": not bad and i == 20,
            "truth_span": [0, 3] if bad else None,
            "trap_author": "ground-truth-author", "rubric_author": "rubric-editor",
            "adjudicator": "human-adjudicator", "human_adjudicated": True,
            "predicted_defect": bad, "localized_correctly": True if bad else False,
        })
    return cases


def canary_contract(cases):
    return {
        "preregistered_at": OBSERVED, "truth_sha256": canary_truth_digest(cases),
        "single_use": True, "prior_exposures": 0,
        "minimum_total": 40, "minimum_bad": 20, "minimum_clean": 20,
        "minimum_subtle": 10, "max_false_acceptance_upper95": 0.2,
        "max_false_rejection_upper95": 0.2,
        "min_subtle_detection_lower95": 0.7,
    }


def evaluated_task(family="TABULAR_CLASSIFICATION"):
    if family == "TIME_SERIES_FORECASTING":
        specs = [
            {"name": "MAE", "direction": "MIN", "role": "PRIMARY", "min_improvement": 0.2},
            {"name": "latency_ms", "direction": "MIN", "role": "GUARDRAIL"},
        ]
        p_values = {"MAE": 3.0, "latency_ms": 20.0}
        c_values = {"MAE": 2.6, "latency_ms": 19.0}
    else:
        specs = [
            {"name": "PR_AUC", "direction": "MAX", "role": "PRIMARY", "min_improvement": 0.02},
            {"name": "latency_ms", "direction": "MIN", "role": "GUARDRAIL"},
        ]
        p_values = {"PR_AUC": 0.5, "latency_ms": 20.0}
        c_values = {"PR_AUC": 0.53, "latency_ms": 19.0}
    packet = {"frozen": True, "task_family": family, "dataset_version": "dataset-v1",
              "metric_specs": specs, "holdout_frozen": True}
    critical = {"leakage": 0, "security": 0, "reproducibility": 0,
                "authority": 0, "data_contract": 0}
    parent = {"packet_sha256": digest(packet), "run_ref": "run-parent",
              "metrics": p_values, "critical_failures": dict(critical)}
    challenger = {"packet_sha256": digest(packet), "run_ref": "run-challenger",
                  "metrics": c_values, "critical_failures": dict(critical)}
    return packet, parent, challenger


class KnowledgeContractTests(unittest.TestCase):
    def test_valid_current(self):
        self.assertEqual(validate_record(record()), [])

    def test_valid_experimental(self):
        self.assertEqual(validate_record(record(state="EXPERIMENTAL")), [])

    def test_malformed_state_type_is_blocked_not_exception(self):
        for state in ([], {}, ["CURRENT"]):
            x = record(); x["state"] = state
            self.assertTrue(validate_record(x))
            self.assertFalse(check_dependency_closure([x], ref("A"))["allowed"])

    def test_malformed_evidence_class_is_blocked_not_exception(self):
        x = record(); x["evidence_refs"][0]["class"] = []
        self.assertTrue(validate_record(x))

    def test_missing_current_acceptance_ref(self):
        x = record(); x.pop("acceptance_ref")
        self.assertTrue(any("acceptance" in e for e in validate_record(x)))

    def test_current_requires_evidence(self):
        x = record(); x["evidence_refs"] = []
        self.assertTrue(any("requires evidence" in e for e in validate_record(x)))

    def test_evidence_provenance_hash_required(self):
        x = record(); x["evidence_refs"][0]["sha256"] = "garbage"
        self.assertTrue(any("digest" in e for e in validate_record(x)))

    def test_timestamp_timezone_required(self):
        x = record(); x["evidence_refs"][0]["observed_at"] = "2026-10-09"
        self.assertTrue(any("timezone" in e for e in validate_record(x)))

    def test_provider_version_needs_provider(self):
        self.assertTrue(any("provider_version requires" in e for e in validate_record(record(provider_version="v2"))))

    def test_disallow_self_dependent(self):
        self.assertTrue(any("self-reference" in e for e in validate_record(record(deps=[ref("A")]))))

    def test_unverified_record_not_production_dependency(self):
        x = record(state="UNVERIFIED")
        self.assertFalse(check_dependency_closure([x], ref("A"))["allowed"])

    def test_valid_dependency_closure(self):
        a = record("A")
        b = record("B", deps=[ref("A")])
        self.assertTrue(check_dependency_closure([a, b], ref("B"))["allowed"])

    def test_missing_dependency_fails_closed(self):
        b = record("B", deps=[ref("A")])
        self.assertTrue(any("missing pinned" in e for e in check_dependency_closure([b], ref("B"))["reasons"]))

    def test_exact_version_pinned(self):
        a = record("A"); a["version"] = 2
        b = record("B", deps=[ref("A", 1)])
        self.assertFalse(check_dependency_closure([a, b], ref("B"))["allowed"])

    def test_stale_dependency_blocked(self):
        a = record("A", state="STALE")
        b = record("B", deps=[ref("A")])
        self.assertFalse(check_dependency_closure([a, b], ref("B"))["allowed"])

    def test_dependency_cycle_blocked(self):
        a = record("A", deps=[ref("B")])
        b = record("B", deps=[ref("A")])
        self.assertTrue(any("cycle" in e for e in check_dependency_closure([a, b], ref("A"))["reasons"]))

    def test_duplicate_pinned_versions_rejected(self):
        a = record("A")
        self.assertTrue(any("duplicate" in e for e in check_dependency_closure([a, a], ref("A"))["reasons"]))

    def test_successor_invalidates_superseded_current(self):
        a = record("A")
        b = record("B"); b["supersedes"] = [ref("A")]
        self.assertTrue(any("superseded" in e for e in check_dependency_closure([a, b], ref("A"))["reasons"]))

    def test_unrelated_bad_state_does_not_poison_closure(self):
        a = record("A")
        unrelated = record("X"); unrelated["state"] = "UNEXPECTED"
        self.assertTrue(check_dependency_closure([a, unrelated], ref("A"))["allowed"])

    def test_unrelated_malformed_record_does_not_poison_closure(self):
        a = record("A")
        x = record("X"); x.pop("state")
        self.assertTrue(check_dependency_closure([a, x], ref("A"))["allowed"])

    def test_invalidation_radius_only_related(self):
        a = record("A")
        b = record("B", deps=[ref("A")])
        c = record("C", deps=[ref("B")])
        z = record("Z")
        initial = copy.deepcopy([a, b, c, z])
        result = invalidation_impact(initial, [ref("A")], event="source_changed")
        self.assertTrue(result["valid"])
        self.assertEqual(result["affected"], [ref("A"), ref("B"), ref("C")])
        self.assertEqual(initial, [a, b, c, z])
        self.assertFalse(result["state_changed"])

    def test_nontriggering_event_does_not_force_global_invalidation(self):
        res = invalidation_impact([record()], [ref("A")], event="market_shift")
        self.assertEqual(res["affected"], [])

    def test_context_provider_version_exact(self):
        rec = record(provider="provider-X", provider_version="v1")
        ctx = {"task_family": "TABULAR_CLASSIFICATION", "domain": "demo",
               "provider": "provider-X", "provider_version": "v2"}
        self.assertTrue(check_scope(rec, ctx))
        ctx["provider_version"] = "v1"
        self.assertEqual(check_scope(rec, ctx), [])

    def test_portable_to_image_classification_without_core_change(self):
        rec = record(task_family="IMAGE_CLASSIFICATION", domain="plant_disease")
        self.assertTrue(check_dependency_closure([rec], ref("A"))["allowed"])
        self.assertEqual(check_scope(rec, {"task_family": "IMAGE_CLASSIFICATION", "domain": "plant_disease"}), [])

    def test_portable_to_forecasting_without_core_change(self):
        rec = record(task_family="TIME_SERIES_FORECASTING", domain="demand")
        self.assertTrue(check_dependency_closure([rec], ref("A"))["allowed"])
        self.assertEqual(check_scope(rec, {"task_family": "TIME_SERIES_FORECASTING", "domain": "demand"}), [])


class PromotionTests(unittest.TestCase):
    def setUp(self):
        self.rec = record(state="EXPERIMENTAL")
        self.e, self.c = promotion_receipts(self.rec)
        self.snapshots = {"EV-A": SAMPLE}
        self.context = {"task_family": "TABULAR_CLASSIFICATION", "domain": "demo"}

    def check(self, rec=None, records=None, evidence=None, evaluation=None, review=None, context=None):
        return inspect_promotion(
            records if records is not None else [self.rec],
            rec if rec is not None else self.rec,
            evidence_snapshots=evidence if evidence is not None else self.snapshots,
            evaluation=evaluation if evaluation is not None else self.e,
            review=review if review is not None else self.c,
            runtime_context=context if context is not None else self.context,
        )

    def test_eligible_only_for_external_approval(self):
        verdict = self.check()
        self.assertTrue(verdict["ready_for_external_approval"], verdict)
        for k in ("state_changed", "verified", "critic_independence_proven", "source_authenticity_proven", "production_ready"):
            self.assertFalse(verdict[k])
        self.assertEqual(self.rec["state"], "EXPERIMENTAL")

    def test_cannot_promote_unverified_directly(self):
        x = copy.deepcopy(self.rec); x["state"] = "UNVERIFIED"
        self.assertFalse(self.check(rec=x, records=[x])["ready_for_external_approval"])

    def test_unchanged_source_hash_not_authenticity_proof(self):
        self.assertFalse(self.check()["source_authenticity_proven"])

    def test_missing_source_bytes_blocks(self):
        self.assertTrue(any("missing or mismatched" in e for e in self.check(evidence={})["reasons"]))

    def test_source_digest_mismatch_blocks(self):
        self.assertFalse(self.check(evidence={"EV-A": b"tampered"})["ready_for_external_approval"])

    def test_same_critic_learner_blocked(self):
        review = dict(self.c, reviewer_id="LEARNER-SEAT")
        self.assertFalse(self.check(review=review)["ready_for_external_approval"])

    def test_critic_target_mismatch_blocked(self):
        review = dict(self.c, candidate_sha256="0" * 64)
        self.assertFalse(self.check(review=review)["ready_for_external_approval"])

    def test_unresolved_medium_finding_blocks(self):
        review = dict(self.c, findings=[{"severity": "MEDIUM", "status": "OPEN"}])
        self.assertFalse(self.check(review=review)["ready_for_external_approval"])

    def test_resolved_finding_requires_disposition(self):
        review = dict(self.c, findings=[{"severity": "HIGH", "status": "RESOLVED"}])
        self.assertFalse(self.check(review=review)["ready_for_external_approval"])
        review["findings"][0]["disposition_ref"] = "review/disposition-1"
        self.assertTrue(self.check(review=review)["ready_for_external_approval"])

    def test_no_baseline_or_holdout_blocks(self):
        e = dict(self.e, baseline_present=False)
        self.assertFalse(self.check(evaluation=e)["ready_for_external_approval"])
        e = dict(self.e, heldout_test=False)
        self.assertFalse(self.check(evaluation=e)["ready_for_external_approval"])

    def test_unregistered_candidate_tampering_blocks(self):
        changed = copy.deepcopy(self.rec); changed["claim"] = "silently changed"
        self.assertFalse(self.check(rec=changed)["ready_for_external_approval"])

    def test_inference_only_does_not_promote(self):
        x = copy.deepcopy(self.rec); x["evidence_refs"][0]["class"] = "INFERENCE"
        e, r = promotion_receipts(x)
        out = self.check(rec=x, records=[x], evaluation=e, review=r)
        self.assertFalse(out["ready_for_external_approval"])

    def test_wrong_scope_blocks(self):
        ctx = dict(self.context, domain="other")
        self.assertFalse(self.check(context=ctx)["ready_for_external_approval"])


class CandidateEvaluationTests(unittest.TestCase):
    def test_bounded_tabular_improvement(self):
        p, a, b = evaluated_task()
        verdict = compare_parent_candidate(p, a, b)
        self.assertTrue(verdict["candidate_eligible_for_external_review"], verdict)
        self.assertFalse(verdict["model_promoted"])
        self.assertFalse(verdict["measured_improvement_independently_proven"])

    def test_bounded_forecasting_improvement(self):
        p, a, b = evaluated_task("TIME_SERIES_FORECASTING")
        self.assertTrue(compare_parent_candidate(p, a, b)["candidate_eligible_for_external_review"])

    def test_same_frozen_packet_required(self):
        p, a, b = evaluated_task()
        b["packet_sha256"] = "b" * 64
        self.assertFalse(compare_parent_candidate(p, a, b)["candidate_eligible_for_external_review"])

    def test_no_regression_in_latency_cost_guardrail(self):
        p, a, b = evaluated_task()
        b["metrics"]["latency_ms"] = 21.0
        self.assertFalse(compare_parent_candidate(p, a, b)["candidate_eligible_for_external_review"])

    def test_leakage_failure_blocks(self):
        p, a, b = evaluated_task()
        b["critical_failures"]["leakage"] = 1
        self.assertFalse(compare_parent_candidate(p, a, b)["candidate_eligible_for_external_review"])

    def test_missing_integrity_gate_blocks(self):
        p, a, b = evaluated_task()
        b["critical_failures"].pop("authority")
        self.assertFalse(compare_parent_candidate(p, a, b)["candidate_eligible_for_external_review"])

    def test_parent_without_distinct_run_receipt_blocks(self):
        p, a, b = evaluated_task()
        b["run_ref"] = a["run_ref"]
        self.assertFalse(compare_parent_candidate(p, a, b)["candidate_eligible_for_external_review"])

    def test_no_improvement_fails(self):
        p, a, b = evaluated_task()
        b["metrics"]["PR_AUC"] = 0.51
        self.assertFalse(compare_parent_candidate(p, a, b)["candidate_eligible_for_external_review"])

    def test_metric_name_not_frozen_fails(self):
        p, a, b = evaluated_task()
        b["metrics"]["new_metric"] = 1.0
        self.assertFalse(compare_parent_candidate(p, a, b)["candidate_eligible_for_external_review"])

    def test_nan_metric_fails(self):
        p, a, b = evaluated_task()
        b["metrics"]["PR_AUC"] = float("nan")
        self.assertFalse(compare_parent_candidate(p, a, b)["candidate_eligible_for_external_review"])

    def test_modified_metric_spec_fails(self):
        p, a, b = evaluated_task()
        p["metric_specs"][0]["min_improvement"] = 0.0
        self.assertFalse(compare_parent_candidate(p, a, b)["candidate_eligible_for_external_review"])

    def test_never_promotes_even_when_eligible(self):
        p, a, b = evaluated_task()
        self.assertFalse(compare_parent_candidate(p, a, b)["state_changed"])


class CriticCanaryTests(unittest.TestCase):
    def test_good_synthetic_set_passes_structurally_only(self):
        rows = canary_cases(); contract = canary_contract(rows)
        out = score_critic_canary(rows, contract)
        self.assertTrue(out["structural_canary_pass"], out)
        self.assertFalse(out["critic_reliability_proven"])
        self.assertFalse(out["critic_independence_proven"])

    def test_two_item_dataset_cannot_pass(self):
        rows = canary_cases()[:2]; contract = canary_contract(rows)
        self.assertFalse(score_critic_canary(rows, contract)["structural_canary_pass"])

    def test_truth_changed_after_freeze_rejected(self):
        rows = canary_cases(); contract = canary_contract(rows)
        rows[0]["expected_defect"] = False
        self.assertFalse(score_critic_canary(rows, contract)["structural_canary_pass"])

    def test_reused_critic_set_blocked(self):
        rows = canary_cases(); contract = canary_contract(rows)
        contract["prior_exposures"] = 1
        self.assertFalse(score_critic_canary(rows, contract)["structural_canary_pass"])

    def test_unpreregistered_set_blocked(self):
        rows = canary_cases(); contract = canary_contract(rows)
        contract["preregistered_at"] = "2026-10-09"
        self.assertFalse(score_critic_canary(rows, contract)["structural_canary_pass"])

    def test_same_truth_roles_blocked(self):
        rows = canary_cases(); rows[0]["rubric_author"] = rows[0]["trap_author"]
        contract = canary_contract(rows)
        self.assertFalse(score_critic_canary(rows, contract)["structural_canary_pass"])

    def test_canary_role_spoofing_case_insensitive_blocked(self):
        rows = canary_cases()
        rows[0]["rubric_author"] = "  GROUND-TRUTH-AUTHOR  "
        contract = canary_contract(rows)
        self.assertFalse(score_critic_canary(rows, contract)["structural_canary_pass"])

    def test_false_acceptance_exceeds_bound(self):
        rows = canary_cases()
        for r in rows[:5]: r["predicted_defect"] = False
        contract = canary_contract(rows)
        self.assertFalse(score_critic_canary(rows, contract)["structural_canary_pass"])

    def test_false_rejection_exceeds_bound(self):
        rows = canary_cases()
        for r in rows[20:26]: r["predicted_defect"] = True
        contract = canary_contract(rows)
        self.assertFalse(score_critic_canary(rows, contract)["structural_canary_pass"])

    def test_subtle_error_localization_required(self):
        rows = canary_cases()
        for r in rows[:6]: r["localized_correctly"] = False
        contract = canary_contract(rows)
        self.assertFalse(score_critic_canary(rows, contract)["structural_canary_pass"])

    def test_historical_defect_required(self):
        rows = canary_cases()
        rows[0]["historical"] = False
        contract = canary_contract(rows)
        self.assertFalse(score_critic_canary(rows, contract)["structural_canary_pass"])

    def test_nonserializable_truth_fails_closed(self):
        rows = canary_cases(); contract = canary_contract(rows)
        rows[0]["case_id"] = {"not JSON"}
        self.assertFalse(score_critic_canary(rows, contract)["structural_canary_pass"])

    def test_malformed_records_fail_closed(self):
        self.assertFalse(score_critic_canary([None], {})["structural_canary_pass"])


if __name__ == "__main__":
    unittest.main()
