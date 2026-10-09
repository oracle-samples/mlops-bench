from __future__ import annotations

import importlib
import json


module = importlib.import_module('mlops_bench_contracts.monitoring_gate')


def test_public_metadata_surface_is_stable():
    metadata = module.describe_contract()

    assert callable(module.evaluate_observability_window)
    assert metadata["stage"] == module.STAGE
    assert metadata["required_fields"] == list(module.REQUIRED_FIELDS)
    assert "thresholds" in metadata
    assert "decision_id" in metadata["report_fields"]


def test_summarize_records_shape_is_preserved():
    rows = [{module.ID_FIELD: "a"}, {module.ID_FIELD: "b"}]

    summary = module.summarize_records(rows)

    assert summary["total_records"] == 2
    assert summary["entity_count"] == 2
    assert summary["required_fields"] == list(module.REQUIRED_FIELDS)


def test_empty_call_writes_report_schema(tmp_path):
    output = tmp_path / "empty.json"
    report = module.evaluate_observability_window([], output_path=output)

    assert set(report) == {"passed", "metrics", "violations", "recommended_action", "artifact_path", "decision_id", "lineage"}
    assert output.exists()
    loaded = json.loads(output.read_text())
    assert loaded["artifact_path"] == str(output)
    assert loaded["lineage"]["stage"] == module.STAGE


def test_threshold_override_does_not_mutate_defaults():
    before = dict(module.DEFAULT_THRESHOLDS)
    report = module.evaluate_observability_window([], thresholds={"max_drift_ratio": 0.99})
    after = dict(module.DEFAULT_THRESHOLDS)

    assert before == after
    assert report["metrics"]["total_records"] == 0


def test_describe_contract_returns_copies_not_live_defaults():
    metadata = module.describe_contract()
    metadata["thresholds"]["max_drift_ratio"] = 12345
    metadata["required_fields"].append("mutated")

    assert module.DEFAULT_THRESHOLDS.get("max_drift_ratio") != 12345
    assert "mutated" not in module.REQUIRED_FIELDS
