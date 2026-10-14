from __future__ import annotations

import importlib
import json
from datetime import datetime, timedelta, timezone


module = importlib.import_module('mlops_bench_contracts.e2e_flow_gate')
gate = module.evaluate_mlops_release_flow


def _ts(minutes_old=1):
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_old)).isoformat()


def _valid_records():
    if 'stage_flow' == "target_balance":
        return [
            {"dataset_id": "r1", "event_ts": _ts(), "entity_id": "u1", "feature_value": 10.0, "label": 0},
            {"dataset_id": "r2", "event_ts": _ts(), "entity_id": "u2", "feature_value": 11.0, "label": 1},
            {"dataset_id": "r3", "event_ts": _ts(), "entity_id": "u3", "feature_value": 10.5, "label": 0},
        ]
    if 'stage_flow' == "feature_skew":
        return [
            {"entity_id": "u1", "event_ts": _ts(), "offline_value": 10.0, "online_value": 10.01, "feature_version": "v7"},
            {"entity_id": "u2", "event_ts": _ts(), "offline_value": 20.0, "online_value": 20.01, "feature_version": "v7"},
        ]
    if 'stage_flow' == "training_quality":
        return [
            {"run_id": "run-1", "started_at": _ts(), "accuracy": 0.91, "roc_auc": 0.88, "loss": 0.22, "model_uri": "models/a.pkl"},
            {"run_id": "run-2", "started_at": _ts(), "accuracy": 0.86, "roc_auc": 0.82, "loss": 0.25, "model_uri": "models/b.pkl"},
        ]
    if 'stage_flow' == "serving_health":
        return [
            {"request_id": "q1", "timestamp": _ts(), "latency_ms": 45, "prediction": 0, "model_version": "v3", "status_code": 200},
            {"request_id": "q2", "timestamp": _ts(), "latency_ms": 51, "prediction": 1, "model_version": "v3", "status_code": 200},
            {"request_id": "q3", "timestamp": _ts(), "latency_ms": 49, "prediction": 0, "model_version": "v3", "status_code": 200},
        ]
    if 'stage_flow' == "monitoring_drift":
        return [
            {"metric_name": "accuracy", "timestamp": _ts(), "value": 0.91, "segment": "all", "severity": "info"},
            {"metric_name": "latency", "timestamp": _ts(), "value": 72.0, "segment": "api", "severity": "info"},
        ]
    if 'stage_flow' == "release_manifest":
        return [
            {"artifact_id": "model", "artifact_type": "model", "sha256": "a" * 64, "approved": True, "created_at": _ts()},
            {"artifact_id": "data", "artifact_type": "data", "sha256": "b" * 64, "approved": True, "created_at": _ts()},
            {"artifact_id": "config", "artifact_type": "config", "sha256": "c" * 64, "approved": True, "created_at": _ts()},
        ]
    return [
        {"stage": "data_pipeline", "status": "passed", "started_at": _ts(), "artifact_uri": "artifacts/data.json", "quality_score": 0.94},
        {"stage": "feature_engineering", "status": "passed", "started_at": _ts(), "artifact_uri": "artifacts/features.json", "quality_score": 0.93},
        {"stage": "model_training", "status": "passed", "started_at": _ts(), "artifact_uri": "artifacts/model.json", "quality_score": 0.92},
        {"stage": "model_serving", "status": "passed", "started_at": _ts(), "artifact_uri": "artifacts/serving.json", "quality_score": 0.91},
        {"stage": "monitoring_observability", "status": "passed", "started_at": _ts(), "artifact_uri": "artifacts/monitoring.json", "quality_score": 0.9},
        {"stage": "cicd_governance", "status": "passed", "started_at": _ts(), "artifact_uri": "artifacts/release.json", "quality_score": 0.89},
    ]


def _codes(report):
    return {item["code"] for item in report["violations"]}


def test_valid_records_pass_and_write_matching_artifact(tmp_path):
    output = tmp_path / "nested" / "release_decision.json"
    rows = _valid_records()
    report = gate(rows, output_path=output)

    assert report["passed"] is True
    assert report["recommended_action"] == "none"
    assert report["violations"] == []
    assert report["metrics"]["total_records"] == len(rows)
    assert report["metrics"]["quality_pass_rate"] == 1.0
    assert len(report["decision_id"]) >= 16
    assert output.exists()
    saved = json.loads(output.read_text())
    assert saved == report
    assert saved["lineage"]["stage"] == module.STAGE


def test_missing_required_field_fails_with_machine_readable_violation(tmp_path):
    rows = _valid_records()
    rows[0].pop('stage')

    report = gate(rows, output_path=tmp_path / "missing.json")
    codes = _codes(report)

    assert report["passed"] is False
    assert "missing_required_field" in codes
    assert report["recommended_action"] in {"investigate_data_quality", "rollback_review"}
    assert report["metrics"]["missing_required_count"] >= 1
    assert all("severity" in item for item in report["violations"])
    assert any("record_id" in item for item in report["violations"])


def test_duplicate_and_stale_records_are_blocked(tmp_path):
    rows = _valid_records()
    rows[1][module.ID_FIELD] = rows[0][module.ID_FIELD]
    rows[1][module.TIMESTAMP_FIELD] = _ts(minutes_old=70)

    report = gate(rows, output_path=tmp_path / "freshness.json")
    codes = _codes(report)

    assert report["passed"] is False
    assert "duplicate_identifier" in codes
    assert "stale_record" in codes
    assert report["metrics"]["duplicate_rate"] > 0
    assert report["metrics"]["freshness_breach_rate"] > 0


def test_null_invalid_timestamp_and_numeric_errors_are_aggregated():
    rows = _valid_records()
    rows[0]['stage'] = None
    rows[0][module.TIMESTAMP_FIELD] = "not-a-timestamp"
    if True:
        rows[0]['quality_score'] = "not-a-number"

    report = gate(rows)
    codes = _codes(report)

    assert report["passed"] is False
    assert "null_required_field" in codes
    assert "invalid_timestamp" in codes
    if True:
        assert "invalid_numeric" in codes
        assert report["metrics"]["invalid_numeric_count"] >= 1
    assert report["metrics"]["invalid_timestamp_count"] >= 1
    assert report["metrics"]["quality_pass_rate"] < 1.0


def test_threshold_override_changes_freshness_without_mutating_defaults():
    before = dict(module.DEFAULT_THRESHOLDS)
    rows = _valid_records()
    rows[0][module.TIMESTAMP_FIELD] = _ts(minutes_old=3)

    report = gate(rows, thresholds={"max_age_minutes": 1})

    assert dict(module.DEFAULT_THRESHOLDS) == before
    assert report["passed"] is False
    assert "stale_record" in _codes(report)
    assert report["lineage"]["thresholds"]["max_age_minutes"] == 1.0


def test_generator_input_and_decision_id_are_deterministic():
    rows = _valid_records()

    report_a = gate((dict(row) for row in rows))
    report_b = gate((dict(row) for row in rows))

    assert report_a["passed"] is True
    assert report_a["decision_id"] == report_b["decision_id"]
    assert report_a["metrics"]["total_records"] == len(rows)


def test_baseline_or_stage_specific_regression_is_detected(tmp_path):
    rows = _valid_records()
    baseline = _valid_records()
    if 'stage_flow' == "feature_skew":
        rows[0]["online_value"] = rows[0]["offline_value"] * 1.5
    elif 'stage_flow' == "training_quality":
        baseline = [dict(rows[0], loss=0.1)]
        rows = [dict(rows[0], loss=0.8, accuracy=0.93, roc_auc=0.9)]
    elif 'stage_flow' == "serving_health":
        rows = [dict(item, latency_ms=999, status_code=503) for item in rows]
    elif 'stage_flow' == "monitoring_drift":
        baseline = [dict(rows[0], value=10.0), dict(rows[1], value=12.0)]
        rows = [dict(rows[0], value=99.0), dict(rows[1], value=100.0)]
    elif 'stage_flow' == "release_manifest":
        rows[0]["sha256"] = "not-a-real-hash"
        rows[1]["approved"] = False
    elif 'stage_flow' == "stage_flow":
        rows = [dict(item) for item in reversed(rows)]
        rows[0]["quality_score"] = 0.2
    else:
        baseline = [dict(rows[0], feature_value=10.0), dict(rows[1], feature_value=11.0)]
        rows = [dict(rows[0], feature_value=99.0), dict(rows[1], feature_value=100.0)]

    report = gate(rows, output_path=tmp_path / "regression.json", baseline=baseline)
    codes = _codes(report)

    assert report["passed"] is False
    assert codes
    assert report["recommended_action"] in {"retrain", "rollback_review", "investigate_data_quality", "block_release"}
    assert json.loads((tmp_path / "regression.json").read_text())["passed"] is False


def test_stage_specific_guardrails_are_not_collapsed_to_schema_only():
    rows = _valid_records()
    baseline = _valid_records()
    expected_codes = set()
    if 'stage_flow' == "target_balance":
        for row in rows:
            row["label"] = 1
        expected_codes.add("single_class_target")
    elif 'stage_flow' == "feature_skew":
        rows[1]["feature_version"] = "v8"
        expected_codes.add("mixed_feature_versions")
    elif 'stage_flow' == "training_quality":
        rows = [dict(rows[0], accuracy=0.01, roc_auc=0.01, loss=0.2)]
        expected_codes.update({"accuracy_below_threshold", "roc_auc_below_threshold"})
    elif 'stage_flow' == "serving_health":
        for row in rows:
            row["prediction"] = "same-class"
        expected_codes.add("single_class_predictions")
    elif 'stage_flow' == "monitoring_drift":
        for row in rows:
            row["severity"] = "critical"
        expected_codes.add("alert_rate_breach")
    elif 'stage_flow' == "release_manifest":
        rows = [row for row in rows if row["artifact_type"] != "config"]
        expected_codes.add("missing_artifact_type")
    else:
        rows[2]["status"] = "failed"
        rows = rows[:4]
        expected_codes.update({"stage_failed", "missing_stage"})

    report = gate(rows, baseline=baseline)

    assert report["passed"] is False
    assert expected_codes <= _codes(report)


def test_public_contract_metadata_and_summary_are_consistent():
    metadata = module.describe_contract()
    summary = module.summarize_records(_valid_records())

    assert metadata["stage"] == module.STAGE
    assert metadata["required_fields"] == list(module.REQUIRED_FIELDS)
    assert summary["total_records"] == len(_valid_records())
    assert summary["required_fields"] == list(module.REQUIRED_FIELDS)

def test_missing_required_fields_across_multiple_rows_are_aggregated():
    rows = _valid_records()
    rows[0].pop('stage', None)
    rows[1].pop('status', None)

    report = gate(rows)
    missing = [item for item in report["violations"] if item.get("code") == "missing_required_field"]
    fields = {item.get("field") for item in missing}

    assert report["passed"] is False
    assert report["metrics"]["missing_required_count"] >= 2
    assert {'stage', 'status'} <= fields


def test_blank_required_values_across_rows_are_aggregated():
    rows = _valid_records()
    rows[0]['stage'] = ""
    rows[1]['status'] = ""

    report = gate(rows)
    nulls = [item for item in report["violations"] if item.get("code") == "null_required_field"]
    fields = {item.get("field") for item in nulls}

    assert report["passed"] is False
    assert report["metrics"]["null_required_count"] >= 2
    assert {'stage', 'status'} <= fields


def test_failure_artifact_roundtrip_matches_returned_report(tmp_path):
    rows = _valid_records()
    rows[0].pop('stage', None)
    output = tmp_path / "audit" / "contract_report.json"

    report = gate(rows, output_path=output)

    assert report["passed"] is False
    assert output.exists()
    assert json.loads(output.read_text()) == report
    assert report["artifact_path"] == str(output)


def test_multiple_invalid_timestamps_preserve_record_ids():
    rows = _valid_records()
    rows[0][module.TIMESTAMP_FIELD] = "not-a-timestamp"
    rows[1][module.TIMESTAMP_FIELD] = "also-not-a-timestamp"
    expected_ids = {str(rows[0][module.ID_FIELD]), str(rows[1][module.ID_FIELD])}

    report = gate(rows)
    timestamp_violations = [item for item in report["violations"] if item.get("code") == "invalid_timestamp"]

    assert report["passed"] is False
    assert expected_ids <= {str(item.get("record_id")) for item in timestamp_violations}
    assert report["metrics"]["invalid_timestamp_count"] >= 2


def test_relaxed_freshness_threshold_allows_old_but_valid_rows():
    rows = _valid_records()
    for row in rows:
        row[module.TIMESTAMP_FIELD] = _ts(minutes_old=45)

    report = gate(rows, thresholds={"max_age_minutes": 50})

    assert report["passed"] is True
    assert "stale_record" not in _codes(report)
    assert report["lineage"]["thresholds"]["max_age_minutes"] == float(50)


def test_decision_id_is_stable_when_record_key_order_changes():
    rows = _valid_records()
    reordered = [
        {key: row[key] for key in reversed(list(row.keys()))}
        for row in rows
    ]

    report_a = gate(rows)
    report_b = gate(reordered)

    assert report_a["passed"] is True
    assert report_a["decision_id"] == report_b["decision_id"]


def test_duplicate_count_reports_only_repeat_identifiers():
    rows = _valid_records()
    rows[1]['stage'] = rows[0]['stage']

    report = gate(rows)

    assert report["passed"] is False
    assert "duplicate_identifier" in _codes(report)
    assert report["metrics"]["duplicate_count"] == 1


def test_invalid_numeric_values_across_multiple_rows_are_aggregated():
    rows = _valid_records()
    rows[0]['quality_score'] = "bad-number"
    rows[1]['quality_score'] = "also-bad"

    report = gate(rows)
    numeric_violations = [item for item in report["violations"] if item.get("code") == "invalid_numeric"]

    assert report["passed"] is False
    assert len(numeric_violations) >= 2
    assert report["metrics"]["invalid_numeric_count"] >= 2


def test_reversed_complete_stage_sequence_is_rejected():
    rows = [dict(row) for row in reversed(_valid_records())]

    report = gate(rows)

    assert report["passed"] is False
    assert "stage_order_invalid" in _codes(report)


def test_low_quality_stage_blocks_otherwise_complete_release_flow():
    rows = _valid_records()
    rows[0]["quality_score"] = 0.1

    report = gate(rows)

    assert report["passed"] is False
    assert "stage_quality_below_threshold" in _codes(report)

def test_summary_materializes_single_pass_iterable_and_counts_unique_entities():
    rows = _valid_records()
    expected_ids = {str(row[module.ID_FIELD]) for row in rows if row.get(module.ID_FIELD) not in (None, "")}
    summary = module.summarize_records((dict(row) for row in rows))

    assert summary["total_records"] == len(rows)
    assert summary["entity_count"] == len(expected_ids)
    assert summary["required_fields"] == list(module.REQUIRED_FIELDS)


def test_datetime_objects_are_accepted_for_timestamp_field():
    rows = _valid_records()
    rows[0][module.TIMESTAMP_FIELD] = datetime.now(timezone.utc) - timedelta(minutes=1)

    report = gate(rows)

    assert report["passed"] is True
    assert "invalid_timestamp" not in _codes(report)
    assert "stale_record" not in _codes(report)


def test_stage_status_is_case_sensitive_release_signal():
    rows = _valid_records()
    rows[0]["status"] = "PASSED"

    report = gate(rows)

    assert report["passed"] is False
    assert "stage_failed" in _codes(report)

def test_duplicate_stage_is_data_quality_violation():
    rows = _valid_records()
    rows[1][module.ID_FIELD] = rows[0][module.ID_FIELD]

    report = gate(rows)

    assert report["passed"] is False
    assert "duplicate_identifier" in _codes(report)
    assert report["metrics"]["duplicate_count"] == 1


def test_missing_stage_violation_names_all_missing_stages():
    rows = _valid_records()[:3]

    report = gate(rows)
    missing = [item for item in report["violations"] if item.get("code") == "missing_stage"]

    assert report["passed"] is False
    assert missing
    assert "model_serving" in missing[0]["message"]
    assert "monitoring_observability" in missing[0]["message"]
    assert "cicd_governance" in missing[0]["message"]


def test_failed_stage_record_id_is_stage_name():
    rows = _valid_records()
    rows[2]["status"] = "failed"

    report = gate(rows)
    failures = [item for item in report["violations"] if item.get("code") == "stage_failed"]

    assert report["passed"] is False
    assert any(item.get("record_id") == rows[2]["stage"] for item in failures)


def test_threshold_override_allows_low_quality_stage():
    rows = _valid_records()
    rows[0]["quality_score"] = 0.5

    report = gate(rows, thresholds={"min_quality_score": 0.4})

    assert report["passed"] is True
    assert "stage_quality_below_threshold" not in _codes(report)


def test_unknown_stage_does_not_satisfy_required_release_order():
    rows = _valid_records()
    rows[-1]["stage"] = "shadow_stage"

    report = gate(rows)

    assert report["passed"] is False
    assert "missing_stage" in _codes(report)


def test_lineage_reports_required_stage_fields():
    rows = _valid_records()
    report = gate(rows)

    assert report["passed"] is True
    assert report["lineage"]["required_fields"] == list(module.REQUIRED_FIELDS)
    assert report["lineage"]["record_count"] == len(rows)

def test_v11_reversed_complete_stage_sequence_is_rejected():
    rows = [dict(row) for row in reversed(_valid_records())]

    report = gate(rows)

    assert report["passed"] is False
    assert "stage_order_invalid" in _codes(report)


def test_v11_low_quality_stage_blocks_even_with_all_stages_present():
    rows = _valid_records()
    rows[0]["quality_score"] = 0.1

    report = gate(rows)

    assert report["passed"] is False
    assert "stage_quality_below_threshold" in _codes(report)


def test_v11_uppercase_passed_status_is_not_release_success():
    rows = _valid_records()
    rows[0]["status"] = "PASSED"

    report = gate(rows)

    assert report["passed"] is False
    assert "stage_failed" in _codes(report)


def test_v11_missing_multiple_stages_are_named():
    rows = _valid_records()[:2]

    report = gate(rows)
    missing = [item for item in report["violations"] if item.get("code") == "missing_stage"]

    assert report["passed"] is False
    assert missing
    assert "model_training" in missing[0]["message"]
    assert "cicd_governance" in missing[0]["message"]


def test_v11_duplicate_stage_and_failed_stage_are_both_reported():
    rows = _valid_records()
    rows[1][module.ID_FIELD] = rows[0][module.ID_FIELD]
    rows[2]["status"] = "failed"

    report = gate(rows)

    assert report["passed"] is False
    assert {"duplicate_identifier", "stage_failed"} <= _codes(report)
    assert report["metrics"]["duplicate_count"] == 1


def test_v11_blank_artifact_uri_is_null_required_field():
    rows = _valid_records()
    rows[0]["artifact_uri"] = ""

    report = gate(rows)
    nulls = [item for item in report["violations"] if item.get("code") == "null_required_field"]

    assert report["passed"] is False
    assert any(item.get("field") == "artifact_uri" for item in nulls)


def test_v11_relaxed_quality_still_requires_ordered_stages():
    rows = [dict(row) for row in reversed(_valid_records())]
    rows[0]["quality_score"] = 0.1

    report = gate(rows, thresholds={"min_quality_score": 0.0})

    assert report["passed"] is False
    assert "stage_quality_below_threshold" not in _codes(report)
    assert "stage_order_invalid" in _codes(report)


def test_v11_output_artifact_roundtrips_failed_flow_report(tmp_path):
    rows = _valid_records()
    rows[0]["status"] = "failed"
    output = tmp_path / "flow" / "decision.json"

    report = gate(rows, output_path=output)

    assert report["passed"] is False
    assert output.exists()
    assert json.loads(output.read_text()) == report
    assert report["artifact_path"] == str(output)


def test_v11_datetime_started_at_is_accepted_for_all_stages():
    rows = _valid_records()
    for row in rows:
        row[module.TIMESTAMP_FIELD] = datetime.now(timezone.utc) - timedelta(minutes=1)

    report = gate(rows)

    assert report["passed"] is True
    assert "invalid_timestamp" not in _codes(report)


def test_v11_flow_summary_counts_unique_stage_names():
    rows = _valid_records()
    rows[1][module.ID_FIELD] = rows[0][module.ID_FIELD]

    summary = module.summarize_records(rows)

    assert summary["total_records"] == len(rows)
    assert summary["entity_count"] == len({str(row[module.ID_FIELD]) for row in rows})

def test_v12_flow_all_failures_keep_distinct_violation_codes():
    rows = _valid_records()
    rows[1][module.ID_FIELD] = rows[0][module.ID_FIELD]
    rows[2]["status"] = "failed"
    rows[-1]["stage"] = "shadow_stage"
    rows[0]["quality_score"] = 0.1

    report = gate(rows)

    assert report["passed"] is False
    assert {"duplicate_identifier", "stage_failed", "missing_stage", "stage_quality_below_threshold"} <= _codes(report)


def test_v12_flow_duplicate_count_survives_missing_stage_failure():
    rows = _valid_records()[:4]
    rows[1][module.ID_FIELD] = rows[0][module.ID_FIELD]

    report = gate(rows)

    assert report["passed"] is False
    assert report["metrics"]["duplicate_count"] == 1
    assert {"duplicate_identifier", "missing_stage"} <= _codes(report)


def test_v12_flow_threshold_zero_blocks_nominal_quality():
    rows = _valid_records()

    report = gate(rows, thresholds={"min_quality_score": 1.0})

    assert report["passed"] is False
    assert "stage_quality_below_threshold" in _codes(report)


def test_v12_flow_unknown_stage_does_not_replace_required_stage():
    rows = _valid_records()
    rows[-1]["stage"] = "shadow_stage"

    report = gate(rows)

    assert report["passed"] is False
    assert "missing_stage" in _codes(report)


def test_v12_flow_failed_stage_record_id_is_stage_name():
    rows = _valid_records()
    rows[2]["status"] = "failed"

    report = gate(rows)
    failures = [item for item in report["violations"] if item.get("code") == "stage_failed"]

    assert report["passed"] is False
    assert any(item.get("record_id") == rows[2]["stage"] for item in failures)


def test_v12_flow_failed_report_recommended_action_is_not_none():
    rows = _valid_records()
    rows[0]["status"] = "failed"

    report = gate(rows)

    assert report["passed"] is False
    assert report["recommended_action"] in {"retrain", "rollback_review", "investigate_data_quality", "block_release"}

