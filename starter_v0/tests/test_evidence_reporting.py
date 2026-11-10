"""Evidence selection must not hide failed runs or cherry-pick high scores."""
from __future__ import annotations

import json

from scripts.update_evidence import invalid_reasons, select_runs, snapshot_provenance, tool_health


def synthetic_run(version="v0", timestamp="2026-11-10T10:00:00", passed=True):
    """Synthetic in-memory test fixture; never written into the project's runs/."""
    return {
        "version": version, "suite": "base", "generated_at": timestamp,
        "prompt_hash": "a" * 64, "tools_hash": "b" * 64,
        "summary": {"total_cases": 1, "measured_cases": 1, "provider_error_cases": 0,
                    "passed_cases": int(passed), "case_accuracy": float(passed)},
        "results": [{"id": "test-only", "result": {"passed": passed, "failure_type": None}, "tool_results": []}],
    }


def test_latest_valid_lower_score_wins_while_newer_provider_failure_is_excluded(tmp_path):
    runs = tmp_path / "runs"
    runs.mkdir()
    old = synthetic_run()
    latest_valid = synthetic_run(timestamp="2026-11-10T11:00:00", passed=False)
    provider_failure = synthetic_run(timestamp="2026-11-10T12:00:00", passed=False)
    provider_failure["summary"].update(measured_cases=0, provider_error_cases=1)
    provider_failure["results"][0]["result"]["failure_type"] = "provider_error"
    for filename, payload in [("old.json", old), ("latest_valid.json", latest_valid), ("failed_provider.json", provider_failure)]:
        (runs / filename).write_text(json.dumps(payload), encoding="utf-8")
    selected, excluded = select_runs(tmp_path, runs)
    assert [item["path"].name for item in selected] == ["latest_valid.json"]
    assert {item["run_file"] for item in excluded} == {"runs/old.json", "runs/failed_provider.json"}
    assert "provider_error_cases_nonzero_or_missing" in next(item for item in excluded if "failed_provider" in item["run_file"])["reasons"]


def test_api_tool_failure_does_not_invalidate_a_fully_measured_routing_run():
    run = synthetic_run()
    run["results"][0]["tool_results"] = [{
        "tool": "timeline", "result": {"error": "HTTPError", "message": "403 Client Error: Forbidden"},
    }]
    assert invalid_reasons(run) == []
    health = tool_health(run)
    assert health["tool_error_calls"] == health["tool_error_case_count"] == 1
    assert health["errors_by_tool"] == {"timeline": 1}
    assert health["http_status_counts"] == {"403": 1}


def test_version_selection_supports_future_versions_in_numeric_order(tmp_path):
    runs = tmp_path / "runs"
    runs.mkdir()
    for version in ["v10", "v2", "v4"]:
        (runs / f"{version}.json").write_text(json.dumps(synthetic_run(version=version)), encoding="utf-8")
    selected, excluded = select_runs(tmp_path, runs)
    assert [item["run"]["version"] for item in selected] == ["v2", "v4", "v10"]
    assert excluded == []


def test_snapshot_provenance_keeps_recorded_hash_when_file_does_not_match(tmp_path):
    directory = tmp_path / "artifacts" / "versions" / "v2"
    directory.mkdir(parents=True)
    (directory / "system_prompt.md").write_text("changed after run", encoding="utf-8")
    (directory / "tools.yaml").write_text("changed tools", encoding="utf-8")
    provenance = snapshot_provenance(tmp_path, synthetic_run(version="v2"), {"available": False})
    assert provenance["prompt"]["recorded_hash"] == "a" * 64
    assert provenance["prompt"]["matches_snapshot"] is False
    assert provenance["tools"]["recorded_hash"] == "b" * 64
    assert provenance["tools"]["matches_snapshot"] is False
