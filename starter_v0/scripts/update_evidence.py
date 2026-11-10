"""Rebuild submission evidence from saved live runs; never call a provider/API.

The newest valid run is chosen, not the highest-scoring run. Provider validity
and tool execution health are deliberately separate because run_eval scores
tool selection/arguments even when an external tool returns an error object.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
AUTHOR = "Đinh Phúc Diên (AI-assisted implementation)"
VERSIONS = ("v0", "v1", "v2", "v3")
FIELDS = [
    "version", "author", "changed_artifact", "artifact_version", "prompt_hash",
    "tools_hash", "reason", "hypothesis", "metric_before", "metric_after", "run_file",
]
CHANGES = {
    "v0": {
        "changed_artifact": "baseline (original starter prompt/tools)",
        "reason": "Đo starter trước tối ưu; chọn lần chạy hợp lệ mới nhất, không chọn điểm cao nhất.",
        "hypothesis": "Ghi nhận lỗi routing, args, thiếu thông tin và xác nhận gửi của starter.",
    },
    "v1": {
        "changed_artifact": "artifacts/system_prompt.md; artifacts/tools.yaml (register 4 CP3 tools)",
        "reason": "Viết lại phạm vi research, clarify dữ liệu thiếu, preview/xác nhận trước gửi và trust boundary; đồng thời đăng ký deduplicate, investigate, compare_research, citation_audit.",
        "hypothesis": "Quy tắc phạm vi/clarify/xác nhận rõ hơn giúp giảm gọi tool sai và đoán dữ liệu; thay đổi tool set đồng thời nên không quy toàn bộ mức tăng cho prompt.",
    },
    "v2": {
        "changed_artifact": "artifacts/tools.yaml",
        "reason": "Giữ prompt v1; viết lại mô tả khi dùng/không dùng và schema args (handle, news/timeframe, Top, send confirmation) cho các tool.",
        "hypothesis": "Mô tả routing và quy ước args cụ thể giúp model chọn tool đúng và truyền tham số đúng hơn.",
    },
    "v3": {
        "changed_artifact": "artifacts/system_prompt.md",
        "reason": "Thêm thứ tự phân loại request: gửi/xác nhận, thiếu định danh, chọn tool hẹp nhất, rồi tổng hợp; giữ tools v2.",
        "hypothesis": "Ưu tiên clarify cho tweet thiếu người/chủ đề và boundary gửi giúp giảm hai lỗi còn lại; không giả định đạt 100%.",
    },
    "v4": {
        "changed_artifact": "artifacts/system_prompt.md",
        "reason": "Giữ tools v3; bổ sung quy tắc batch các góc nhìn/tiêu chí vào một workbench call và truyền timeframe=all khi không giới hạn thời gian.",
        "hypothesis": "Gộp công việc trong một call và ghi rõ timeframe giúp giảm call investigate trùng và thiếu giá trị mặc định trong eval nhóm; chỉ ghi metric khi có run thật.",
    },
}


def relative(path: Path, root: Path = ROOT) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invalid_reasons(run: dict[str, Any]) -> list[str]:
    """Reject incomplete/provider-failed runs without treating tool errors as routing failures."""
    summary = run.get("summary", {})
    results = run.get("results", [])
    if not isinstance(summary, dict) or not isinstance(results, list):
        return ["invalid_summary_or_results"]
    total = summary.get("total_cases")
    reasons = []
    if type(total) is not int or total <= 0:
        reasons.append("missing_or_empty_total_cases")
    if summary.get("measured_cases") != total:
        reasons.append("measured_cases_does_not_equal_total_cases")
    if summary.get("provider_error_cases") != 0:
        reasons.append("provider_error_cases_nonzero_or_missing")
    if len(results) != total:
        reasons.append("results_length_does_not_equal_total_cases")
    if any(not isinstance(item, dict) or not isinstance(item.get("result"), dict) for item in results):
        reasons.append("invalid_case_result")
        return reasons
    if any(item["result"].get("failure_type") == "provider_error" for item in results):
        reasons.append("case_contains_provider_error")
    passed = sum(item["result"].get("passed") is True for item in results)
    if summary.get("passed_cases") != passed:
        reasons.append("passed_cases_disagrees_with_case_results")
    if type(total) is int and total > 0 and summary.get("case_accuracy") != round(passed / total, 4):
        reasons.append("case_accuracy_disagrees_with_case_results")
    for field in ("prompt_hash", "tools_hash"):
        if not isinstance(run.get(field), str) or not re.fullmatch(r"[0-9a-f]{64}", run[field]):
            reasons.append(f"missing_or_invalid_{field}")
    return reasons


def tool_health(run: dict[str, Any]) -> dict[str, Any]:
    errors = []
    by_tool: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    error_case_ids = set()
    partial_case_ids = set()
    calls = 0
    partial_calls = 0
    nested_errors = 0
    for case in run.get("results", []):
        for call in case.get("tool_results", []):
            calls += 1
            result = call.get("result")
            if not isinstance(result, dict):
                continue
            nested = result.get("search_errors", [])
            nested_count = len(nested) if isinstance(nested, list) else 0
            nested_errors += nested_count
            is_partial = result.get("status") == "partial"
            if is_partial:
                partial_calls += 1
                partial_case_ids.add(case["id"])
            if not (result.get("error") or result.get("status") == "error"):
                continue
            name = str(call.get("tool", "unknown"))
            by_tool[name] += 1
            error_case_ids.add(case["id"])
            # Store categories/status, never copy URLs/messages that might contain credentials.
            match = re.search(r"\b([45][0-9]{2})\b", str(result.get("message", "")))
            status = match[1] if match else None
            if status:
                statuses[status] += 1
            errors.append({
                "case_id": case["id"], "tool": name,
                "error_type": str(result.get("error", "status_error"))[:160],
                "http_status": int(status) if status else None,
                "nested_search_errors": nested_count,
            })
    return {
        "executed_tool_calls": calls, "tool_error_calls": len(errors),
        "tool_error_case_count": len(error_case_ids), "tool_error_case_ids": sorted(error_case_ids),
        "partial_tool_calls": partial_calls, "partial_case_ids": sorted(partial_case_ids),
        "nested_search_error_count": nested_errors, "errors_by_tool": dict(by_tool),
        "http_status_counts": dict(statuses), "error_details": errors,
        "note": "Routing/argument scores do not measure external tool success. Tool errors are reported separately and do not invalidate a fully measured provider run.",
    }


def git_original_tools(root: Path) -> dict[str, Any]:
    repo = root.parent
    prefix = ["git", "-c", f"safe.directory={repo}", "-C", str(repo)]
    try:
        content = subprocess.run(prefix + ["show", "HEAD:starter_v0/artifacts/tools.yaml"],
                                 capture_output=True, check=True, timeout=10).stdout
        commit = subprocess.run(prefix + ["rev-parse", "HEAD"], capture_output=True,
                                text=True, check=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return {"available": False, "note": "Original tools file was not reconstructed; the hash stored in each run remains authoritative."}
    return {"available": True, "git_object": "HEAD:starter_v0/artifacts/tools.yaml", "commit": commit,
            "sha256": hashlib.sha256(content).hexdigest(),
            "note": "Hash read directly from the existing Git object; no original tools snapshot was fabricated."}


def snapshot_provenance(root: Path, run: dict[str, Any], original_tools: dict[str, Any]) -> dict[str, Any]:
    version = run["version"]
    prompt = root / "artifacts" / "versions" / ("system_prompt_v0.md" if version == "v0" else f"{version}/system_prompt.md")
    tools = root / "artifacts" / "versions" / version / "tools.yaml"
    result: dict[str, Any] = {"run_hashes_are_authoritative": True}
    for label, path, expected in (("prompt", prompt, run["prompt_hash"]), ("tools", tools, run["tools_hash"])):
        if version == "v0" and label == "tools":
            result[label] = {"snapshot_file": None, "recorded_hash": expected,
                             "git_original_hash": original_tools.get("sha256"),
                             "matches_git_original": original_tools.get("sha256") == expected if original_tools.get("available") else None}
            continue
        actual = sha256(path) if path.is_file() else None
        result[label] = {"snapshot_file": relative(path, root), "recorded_hash": expected,
                         "snapshot_hash": actual, "matches_snapshot": actual == expected if actual else None}
    return result


def select_runs(root: Path, runs_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates = []
    excluded = []
    for path in sorted(runs_dir.glob("*.json")):
        try:
            run = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            excluded.append({"run_file": relative(path, root), "reasons": [type(exc).__name__]})
            continue
        if (not isinstance(run, dict) or not isinstance(run.get("version"), str)
                or not re.fullmatch(r"v[0-9]+", run["version"])
                or run.get("suite") not in {"base", "group"}):
            continue
        reasons = invalid_reasons(run)
        if reasons:
            excluded.append({"run_file": relative(path, root), "reasons": reasons,
                             "version": run.get("version"), "suite": run.get("suite"), "summary": run.get("summary")})
        else:
            candidates.append({"path": path, "run": run})
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for candidate in sorted(candidates, key=lambda item: (item["run"].get("generated_at", ""), item["path"].name)):
        latest[(candidate["run"]["version"], candidate["run"]["suite"])] = candidate
    selected_paths = {item["path"] for item in latest.values()}
    for candidate in candidates:
        if candidate["path"] not in selected_paths:
            excluded.append({"run_file": relative(candidate["path"], root),
                             "reasons": ["superseded_by_newer_valid_run_same_version_and_suite"],
                             "version": candidate["run"]["version"], "suite": candidate["run"]["suite"],
                             "summary": candidate["run"]["summary"]})
    ordered = sorted(latest.values(), key=lambda item: (0 if item["run"]["suite"] == "base" else 1, int(item["run"]["version"][1:])))
    return ordered, sorted(excluded, key=lambda item: item["run_file"])


def percentage(value: Any) -> str:
    return "—" if value is None else f"{value:.2%}"


def build_evidence(root: Path = ROOT, runs_dir: Path | None = None) -> dict[str, Any]:
    selected, excluded = select_runs(root, runs_dir or root / "runs")
    original_tools = git_original_tools(root)
    entries = []
    rows = []
    prior_accuracy: dict[str, Any] = {"base": "", "group": ""}
    for candidate in selected:
        path, run = candidate["path"], candidate["run"]
        version, suite = run["version"], run["suite"]
        summary = run["summary"]
        failure_cases = [{"case_id": case["id"],
                          "failure_type": case["result"].get("failure_type"),
                          "observed_mismatch": case["result"].get("observed_mismatch"),
                          "failures": case["result"].get("failures", [])}
                         for case in run["results"] if not case["result"].get("passed")]
        entry = {"version": version, "suite": suite, "run_file": relative(path, root),
                 "run_id": run.get("run_id"), "generated_at": run.get("generated_at"),
                 "provider": run.get("provider"), "model": run.get("model"),
                 "artifact_version": run.get("artifact_version"), "prompt_hash": run["prompt_hash"],
                 "tools_hash": run["tools_hash"], "summary": summary, "failure_cases": failure_cases,
                 "tool_health": tool_health(run), "snapshot_provenance": snapshot_provenance(root, run, original_tools)}
        entries.append(entry)
        change = CHANGES.get(version, {
            "changed_artifact": "See recorded hashes and matching version snapshots",
            "reason": "Run có thật; chưa mô tả thay đổi thủ công cho version này.",
            "hypothesis": "Chưa ghi giả thuyết; không suy diễn từ điểm đo được.",
        }) if suite == "base" else {
            "changed_artifact": "data/eval_group.json (evaluation only; version artifacts unchanged)",
            "reason": "Chạy 10 case nhóm (5 single turn + 5 multi turn) kiểm tra bốn tool mới, args và boundary.",
            "hypothesis": "Bộ case riêng đo khả năng routing/args trên yêu cầu mới; không suy ra model đã tổng hợp nội dung chính xác.",
        }
        rows.append({"version": version, "author": AUTHOR, **change,
                     "artifact_version": run.get("artifact_version", ""), "prompt_hash": run["prompt_hash"],
                     "tools_hash": run["tools_hash"], "metric_before": prior_accuracy[suite],
                     "metric_after": summary["case_accuracy"], "run_file": relative(path, root)})
        prior_accuracy[suite] = summary["case_accuracy"]

    selected_keys = {(entry["version"], entry["suite"]) for entry in entries}
    pending = [f"{version}/base" for version in VERSIONS if (version, "base") not in selected_keys]
    if not any(entry["suite"] == "group" for entry in entries):
        pending.append("group")
    evidence = {
        "generated_at": datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).isoformat(timespec="seconds"),
        "selection_policy": "Latest valid run per version and suite, ordered by recorded generated_at then filename; not highest accuracy. Invalid provider runs and superseded valid runs remain on disk and are listed as excluded.",
        "validity_rule": "total_cases > 0; measured_cases == total_cases; provider_error_cases == 0; per-case results/counts/accuracy agree; full SHA-256 prompt/tools hashes exist.",
        "metric_scope": "run_eval measures routing and argument matching. Its passed_cases do not imply successful APIs, factual accuracy, or a complete conversation.",
        "change_log_note": "Change descriptions/hypotheses are documented retrospectively from actual snapshots and saved runs, not pre-registered experiments. v1 also changed the tool set; improvement cannot be attributed to the prompt alone.",
        "author": AUTHOR, "original_tools_provenance": original_tools,
        "eval_base_sha256": sha256(root / "data" / "eval_base.json") if (root / "data" / "eval_base.json").is_file() else None,
        "selected_runs": entries, "excluded_runs": excluded, "pending_runs": pending,
    }
    artifacts, analysis = root / "artifacts", root / "analysis"
    artifacts.mkdir(exist_ok=True)
    analysis.mkdir(exist_ok=True)
    with (artifacts / "version_log.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (analysis / "summary.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    markdown = ["# So sánh các run thực tế", "", f"Cập nhật: {evidence['generated_at']} (GMT+7).", "",
                "Chọn lần chạy **hợp lệ mới nhất** cho từng version/suite, không chọn điểm cao nhất. "
                "Run hợp lệ có đủ case được đo và không có provider error. Điểm chỉ đo routing/args; "
                "lỗi API của tool được đếm riêng bên dưới.", "",
                "| Version/suite | Pass | Routing | Args | Multi-turn | Tool errors (calls/cases) | Run gốc |",
                "|---|---:|---:|---:|---:|---:|---|"]
    for entry in entries:
        summary, health = entry["summary"], entry["tool_health"]
        link = f"[{Path(entry['run_file']).name}](../{entry['run_file']})"
        markdown.append(f"| {entry['version']}/{entry['suite']} | {summary['passed_cases']}/{summary['total_cases']} ({percentage(summary['case_accuracy'])}) | {percentage(summary.get('tool_routing_accuracy'))} | {percentage(summary.get('argument_accuracy'))} | {percentage(summary.get('multiturn_accuracy'))} | {health['tool_error_calls']}/{health['tool_error_case_count']} | {link} |")
    markdown += ["", "## Thay đổi có bằng chứng", "", evidence["change_log_note"], ""]
    for entry in entries:
        if entry["suite"] == "base":
            markdown += [f"- **{entry['version']}**: {CHANGES.get(entry['version'], {}).get('reason', 'Xem hash và snapshot; chưa mô tả thay đổi thủ công.')}" ]
    markdown += ["", "## Lỗi còn lại và tình trạng API tool", ""]
    for entry in entries:
        health = entry["tool_health"]
        markdown.append(f"- **{entry['version']}/{entry['suite']}**: {len(entry['failure_cases'])} case routing/args chưa đạt; {health['tool_error_calls']} tool call trả lỗi, {health['partial_tool_calls']} call trả kết quả partial. HTTP status: {json.dumps(health['http_status_counts'], ensure_ascii=False)}.")
        for case in entry["failure_cases"]:
            markdown.append(f"  - `{case['case_id']}`: {case['observed_mismatch']} — {'; '.join(case['failures'])}.")
    markdown += ["", "Tool errors không bị `run_eval.py` tính là failure nếu model chọn đúng tool/args. "
                 "Đặc biệt, RapidAPI trả HTTP 403 ở các run base; các điểm routing cao không chứng minh timeline/social_search đã lấy được dữ liệu.",
                 "", "## Hash và snapshot", "", "Hash dưới đây lấy nguyên từ JSON run, không thay bằng hash file hiện tại.", ""]
    for entry in entries:
        provenance = entry["snapshot_provenance"]
        markdown += [f"- **{entry['version']}/{entry['suite']}**: `{entry['artifact_version']}`",
                     f"  - prompt SHA-256: `{entry['prompt_hash']}`; snapshot khớp: `{provenance['prompt']['matches_snapshot']}`.",
                     f"  - tools SHA-256: `{entry['tools_hash']}`; " + (f"Git original khớp: `{provenance['tools'].get('matches_git_original')}`. Không tạo lại file tools v0." if entry["version"] == "v0" else f"snapshot khớp: `{provenance['tools']['matches_snapshot']}`.")]
    markdown += ["", "## Run không dùng để tính tiến bộ", ""]
    for entry in excluded:
        markdown.append(f"- [{Path(entry['run_file']).name}](../{entry['run_file']}): {', '.join(entry['reasons'])}.")
    if pending:
        markdown += ["", f"Chưa có run hợp lệ: {', '.join(pending)}."]
    markdown += ["", "Chi tiết số liệu và từng lỗi tool: [summary.json](summary.json). "
                 "Log phiên bản: [version_log.csv](../artifacts/version_log.csv).", ""]
    (analysis / "run_comparison.md").write_text("\n".join(markdown), encoding="utf-8")
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "runs")
    args = parser.parse_args()
    evidence = build_evidence(runs_dir=args.runs_dir)
    print(json.dumps({"selected": [{"version": item["version"], "suite": item["suite"],
                                    "case_accuracy": item["summary"]["case_accuracy"],
                                    "tool_error_calls": item["tool_health"]["tool_error_calls"],
                                    "run_file": item["run_file"]} for item in evidence["selected_runs"]],
                      "excluded_count": len(evidence["excluded_runs"]), "pending": evidence["pending_runs"],
                      "written": ["artifacts/version_log.csv", "analysis/summary.json", "analysis/run_comparison.md"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
