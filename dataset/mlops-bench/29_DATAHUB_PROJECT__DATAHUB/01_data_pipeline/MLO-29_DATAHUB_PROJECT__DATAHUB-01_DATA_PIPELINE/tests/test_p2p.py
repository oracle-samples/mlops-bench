from __future__ import annotations

import importlib
import json


module = importlib.import_module('mlops_bench_contracts.data_pipeline_gate')


def test_public_metadata_surface_is_stable():
    metadata = module.describe_contract()

    assert callable(module.validate_dataset_contract)
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
    report = module.validate_dataset_contract([], output_path=output)

    assert set(report) == {"passed", "metrics", "violations", "recommended_action", "artifact_path", "decision_id", "lineage"}
    assert output.exists()
    loaded = json.loads(output.read_text())
    assert loaded["artifact_path"] == str(output)
    assert loaded["lineage"]["stage"] == module.STAGE
