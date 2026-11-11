"""Offline CP4 dataset checks; these validate cases, not model performance."""
from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from tools import TOOL_FUNCTIONS, load_tool_declarations


ROOT = Path(__file__).resolve().parents[1]
GROUP = json.loads((ROOT / "data/eval_group.json").read_text(encoding="utf-8"))
CASES = GROUP["cases"]
DECLARED = {tool["name"]: tool for tool in load_tool_declarations(ROOT / "artifacts/tools.yaml")}
FAILURE_TYPES = {
    "wrong_tool", "wrong_arg_value", "wrong_boundary",
    "unnecessary_tool", "out_of_scope", "missing_info",
}


def _normalized(text: str) -> str:
    return " ".join(text.split()).casefold()


def _segments(case):
    return [case["query"]] if "query" in case else [turn["content"] for turn in case["turns"]]


def _assert_value_matches_schema(value, schema) -> None:
    kind = schema.get("type")
    if kind == "string":
        assert isinstance(value, str)
        assert len(value) >= schema.get("minLength", 0)
        assert len(value) <= schema.get("maxLength", float("inf"))
    elif kind == "integer":
        assert type(value) is int
        assert value >= schema.get("minimum", float("-inf"))
        assert value <= schema.get("maximum", float("inf"))
    elif kind == "boolean":
        assert type(value) is bool
    elif kind == "array":
        assert isinstance(value, list)
        assert len(value) <= schema.get("maxItems", float("inf"))
        for item in value:
            _assert_value_matches_schema(item, schema["items"])
    elif kind == "object":
        assert isinstance(value, dict)
    if "enum" in schema:
        assert value in schema["enum"]


def test_group_has_five_single_and_five_multi_turn_cases() -> None:
    assert GROUP["dataset_role"] == "group"
    assert len(CASES) == 10
    assert len({case["id"] for case in CASES}) == 10
    assert sum("query" in case for case in CASES) == 5
    assert sum("turns" in case for case in CASES) == 5
    for case in CASES:
        assert ("query" in case) != ("turns" in case)
        assert case["phase"] == "B"
        assert case["suite"] == "group"
        assert case["failure_type"] in FAILURE_TYPES
        assert all(isinstance(text, str) and text.strip() for text in _segments(case))
        if "turns" in case:
            assert len(case["turns"]) >= 2
            assert all(turn["role"] in {"user", "assistant"} for turn in case["turns"])
            assert case["turns"][-1]["role"] == "user"


def test_group_is_original_and_routes_new_tool_in_both_conversation_formats() -> None:
    fixed_cases = []
    for filename in ["eval_base.json", "eval_research_extension.json"]:
        fixed_cases.extend(json.loads((ROOT / "data" / filename).read_text(encoding="utf-8"))["cases"])
    fixed_segments = {_normalized(text) for case in fixed_cases for text in _segments(case)}
    group_inputs = [_normalized("\n".join(_segments(case))) for case in CASES]
    assert len(set(group_inputs)) == 10
    assert not any(_normalized(text) in fixed_segments for case in CASES for text in _segments(case))
    board_cases = [case for case in CASES if any(
        call["name"] == "research_board" for call in case["expect"].get("tool_calls", [])
    )]
    assert any("query" in case for case in board_cases)
    assert any("turns" in case for case in board_cases)
    assert any("compare_queries" in call.get("args", {}) for case in board_cases for call in case["expect"]["tool_calls"])


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_group_case_contract_expected_args_and_failure_provenance(case) -> None:
    metadata = case["metadata"]
    assert isinstance(metadata["what_it_tests"], str) and len(metadata["what_it_tests"].strip()) >= 20
    assert isinstance(metadata["origin_failure"], str) and metadata["origin_failure"].strip()
    assert metadata["origin_cases"]
    run_path = (ROOT / metadata["from_run"]).resolve()
    assert run_path.is_relative_to(ROOT / "runs")
    origin = json.loads(run_path.read_text(encoding="utf-8"))
    failed_ids = {item["id"] for item in origin["results"] if not item["result"]["passed"]}
    assert set(metadata["origin_cases"]) <= failed_ids

    expect = case["expect"]
    assert (expect.get("no_tool") is True) != bool(expect.get("tool_calls"))
    if expect.get("no_tool"):
        assert expect.get("behavior", "answer_without_tool") in {"answer_without_tool", "refuse"}
        return
    for call in expect["tool_calls"]:
        name = call["name"]
        assert name in DECLARED and name in TOOL_FUNCTIONS
        assert isinstance(call.get("args", {}), dict)
        properties = DECLARED[name]["parameters"]["properties"]
        signature = inspect.signature(TOOL_FUNCTIONS[name])
        for key, value in call.get("args", {}).items():
            assert key in properties and key in signature.parameters
            _assert_value_matches_schema(value, properties[key])
        if name == "research_board":
            args = call["args"]
            queries = [args["query"], *args.get("compare_queries", [])]
            assert len({_normalized(query) for query in queries}) == len(queries)
