"""Inspect the app's configured architecture and its recorded execution events.

This module renders observations only. Opening the panel never invokes a model
or tool, and a diagram node is not evidence that the corresponding step ran.
"""
from __future__ import annotations

from collections import Counter
import html
from typing import Any

import streamlit as st

from tools import to_openai_tools
from ui.components import metric, section
from ui.runtime import redact


_STATUS_CLASS = {"observed", "ok", "error", "blocked", "waiting", "not_executed", "info"}


def architecture_html() -> str:
    """Return a self-contained, interactive architecture map with static text."""
    return r'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>
    *{box-sizing:border-box}body{margin:0;color:#e8eefb;background:#0b1425;font:13px 'Segoe UI',sans-serif}button{font:inherit}.frame{border:1px solid #2a3d58;border-radius:17px;overflow:hidden;background:radial-gradient(ellipse at 70% 5%,#1b2e4b,transparent 65%),#0c1627}.bar{display:flex;justify-content:space-between;gap:12px;padding:17px 20px;border-bottom:1px solid #293b54;font-size:10px;letter-spacing:.14em;color:#91a7c4}.bar b{color:#66e4cf;font-weight:500}.map{padding:23px 20px 8px}.row{display:grid;grid-template-columns:1fr 24px 1.35fr 24px 1fr;align-items:stretch;gap:7px}.row.bottom{grid-template-columns:1fr 24px 1.35fr 24px 1fr;margin-top:11px}.node{display:block;text-align:left;background:#14223a;border:1px solid #344a67;border-radius:12px;padding:15px;color:#c8d7eb;min-height:112px;cursor:pointer;transition:border-color .15s,background .15s}.node:hover,.node:focus-visible{border-color:#66e4cf;outline:0}.node.active{background:#163330;border-color:#66e4cf;box-shadow:0 0 0 1px #66e4cf22}.node small{display:block;color:#8fa4c1;font-size:9px;letter-spacing:.1em;margin-bottom:9px}.node b{display:block;font-weight:600;font-size:14px;color:#f0f5ff;margin-bottom:7px}.node span{font-size:10px;line-height:1.6;display:block;color:#9eb1cd}.arrow{align-self:center;color:#66e4cf;font-size:20px;text-align:center}.join{display:flex;justify-content:space-between;padding:8px 7px 0;color:#7e96b9;font-size:10px}.join .loop{color:#a79bff}.branches{display:flex;flex-wrap:wrap;gap:7px;margin:17px 0 12px}.branches span{font-size:10px;padding:6px 9px;border-radius:6px;border:1px solid #334560;color:#a9bad1}.branches .locked{color:#f4be83;border-color:#705235}.details{border-top:1px solid #2b3e58;padding:17px 20px 20px;min-height:124px;background:#0c1728}.details b{font-size:13px;color:#66e4cf}.details p{font-size:11px;line-height:1.8;color:#acbfd9;margin:7px 0 9px;white-space:pre-line}.details code{font-size:10px;color:#a79bff;overflow-wrap:anywhere}.direct{border-top:1px dashed #32465f;padding:13px 20px;color:#9db2ce;font-size:10px;line-height:1.8}.direct b{color:#c9e993}.hint{color:#8299ba;font-size:10px;margin:13px 0 3px}@media(max-width:640px){.bar{font-size:8px}.map{padding:15px 10px 8px}.row,.row.bottom{grid-template-columns:1fr 14px 1.15fr 14px 1fr;gap:3px}.node{padding:10px 7px;min-height:119px}.node b{font-size:11px}.node span{font-size:9px}.node small{font-size:8px}.arrow{font-size:16px}.details{padding:14px}.join{font-size:8px}.direct{padding:11px}}
    </style></head><body><div class="frame"><div class="bar"><span>AGENT ORCHESTRATION / ARCHITECTURE</span><b>CHỌN NODE ĐỂ XEM</b></div><div class="map"><div class="row"><button class="node active" data-node="input"><small>01 / ENTRY</small><b>User request</b><span>Chat + lịch sử riêng<br>theo phiên trình duyệt</span></button><span class="arrow">→</span><button class="node" data-node="context"><small>02 / ASSEMBLY</small><b>Prompt + context</b><span>System prompt · policy<br>history · tool schema</span></button><span class="arrow">→</span><button class="node" data-node="model"><small>03 / INFERENCE</small><b>Selected model</b><span>Text + danh sách tool calls<br>temperature = 0</span></button></div><div class="join"><span>↑ Lượt mới tiếp nối lịch sử phiên</span><span>↓ Model đề xuất tool + args</span></div><div class="row bottom"><button class="node" data-node="output"><small>06 / EXIT</small><b>Answer / pause</b><span>Trả lời · hỏi bổ sung<br>bị chặn · lỗi · chạm giới hạn</span></button><span class="arrow">←</span><button class="node" data-node="feedback"><small>05 / FEEDBACK</small><b>Tool results → context</b><span>Kết quả thật được che secrets<br>quay lại model nếu còn vòng</span></button><span class="arrow">←</span><button class="node" data-node="dispatch"><small>04 / EXECUTION</small><b>Guard → registry</b><span>send bị chặn tại UI<br>tool tự kiểm tra input</span></button></div><div class="join"><span>Không có tool call → trả lời ngay</span><span class="loop">05 ↻ 03 · tối đa 4 vòng / 8 tool calls</span></div><div class="branches"><span>clarify.awaiting_user → chờ người dùng</span><span class="locked">send → blocked · không gửi</span><span>tool error → giữ lỗi trong trace</span></div><div class="hint">Sơ đồ kiến trúc. Các node đã chạy thực tế được liệt kê riêng ở phần “Lượt thực thi” bên dưới.</div></div><div class="details" aria-live="polite"><b id="detail-title"></b><p id="detail-text"></p><code id="detail-source"></code></div><div class="direct"><b>RESEARCH DESK / ĐƯỜNG TRỰC TIẾP</b><br>Form → execute_tool → research_board → Tavily → gộp URL / nhóm domain / graph → UI + transcript. Đường này không gọi model và không dùng system prompt để chọn tool.</div></div><script>
    const descriptions={input:{title:'01 · Nhận yêu cầu từ chat',text:'Chỉ bắt đầu gọi API khi người dùng gửi yêu cầu. Mỗi browser session có context, board và transcript riêng. Câu mẫu chỉ điền ô nhập, chưa thực thi.',source:'app.py → chat_panel() → run_turn()'},context:{title:'02 · Ghép đúng thứ tự đầu vào',text:'messages = system prompt của lab → deployment policy của UI → lịch sử phiên → user request mới. Tool schema được gửi riêng trong tham số tools. Runtime giữ các system messages và giới hạn context gửi model trong 64.000 ký tự.',source:'artifacts/system_prompt.md + app.py: PUBLIC_POLICY + artifacts/tools.yaml → ui/runtime.py: _provider_context()'},model:{title:'03 · Gọi provider thật',text:'Provider được chọn nhận messages, tools, model và temperature=0. Model trả text cùng tool calls đã được provider chuẩn hóa. UI chỉ hiển thị request / response / tool events quan sát được; không suy đoán suy nghĩ nội bộ của model.',source:'ui/runtime.py: run_turn() → Selected provider.complete() → client.chat.completions.create()'},dispatch:{title:'04 · Chặn hành động và chạy tool',text:'Runtime chặn send trước khi truy cập registry, kể cả confirmed=true. Những tool còn lại được tra trong TOOL_FUNCTIONS. Runtime kiểm tra name và args dạng object; từng implementation kiểm tra input của chính nó và trả kết quả hoặc error dict.',source:'ui/runtime.py: execute_tool() → tools/__init__.py: TOOL_FUNCTIONS → tools/<tool>/tool.py'},feedback:{title:'05 · Đưa kết quả về context',text:'Tool calls được ghi thành assistant text với TOOL_CALLS_JSON. Kết quả được thêm thành user message với TOOL_RESULTS_JSON, sau khi che secrets; payload lớn có thể được rút gọn cho model. Đây là cơ chế text của starter, không phải message role=tool. Nếu chưa pause / blocked / chạm giới hạn, vòng tiếp theo mới gửi context này cho model.',source:'ui/runtime.py: _model_event() → _provider_context() → provider.complete()'},output:{title:'06 · Kết thúc hoặc tạm dừng',text:'Không có tool call: trả lời. clarify.awaiting_user: chờ lượt bổ sung. send: blocked. Provider lỗi: dừng và hiện lỗi. Giới hạn 4 vòng hoặc 8 tool calls: dừng, không tự nhận đã hoàn tất. App lưu trace theo phiên và hỗ trợ tải transcript.',source:'ui/runtime.py: finish() → app.py: remember() → transcripts/*.transcript.json'}};
    function choose(key){const d=descriptions[key];document.getElementById('detail-title').textContent=d.title;document.getElementById('detail-text').textContent=d.text;document.getElementById('detail-source').textContent=d.source;document.querySelectorAll('[data-node]').forEach(el=>el.classList.toggle('active',el.dataset.node===key));}document.querySelectorAll('[data-node]').forEach(el=>el.addEventListener('click',()=>choose(el.dataset.node)));choose('input');
    </script></body></html>'''


def _event_stage(event: dict[str, Any], number: int) -> dict[str, str]:
    result = event.get("result")
    state = "ok"
    detail = "Implementation đã trả kết quả."
    if isinstance(result, dict):
        if result.get("status") == "blocked":
            state, detail = "blocked", "Guard chặn thực thi; không gửi/đăng."
        elif result.get("awaiting_user"):
            state, detail = "waiting", "Tool yêu cầu bổ sung/xác nhận; runtime dừng chờ người dùng."
        elif result.get("error"):
            state, detail = "error", "Tool trả lỗi: " + str(result["error"])
        elif result.get("status") in {"partial", "skipped"}:
            state, detail = "waiting", "Kết quả " + str(result["status"]) + "; cần kiểm tra dữ liệu thiếu."
        elif result.get("status"):
            detail = "Trạng thái tool: " + str(result["status"])
    return {"label": f'Tool {number:02d} · {event.get("tool", "unknown")}', "detail": detail, "status": state}


def trace_stages(turn: dict[str, Any]) -> list[dict[str, str]]:
    """Derive a timeline without treating proposed calls as executed calls."""
    stages = [{"label": "User input", "detail": str(turn.get("user", "")), "status": "observed"}]
    events = [event for event in turn.get("tool_events", []) if isinstance(event, dict)]
    if turn.get("interaction") == "explicit_board_form":
        stages.append({"label": "Research desk · bypass model", "detail": "Form gọi tool trực tiếp. Không có model request; system prompt không tham gia routing.", "status": "info"})
        stages.extend(_event_stage(event, index) for index, event in enumerate(events, 1))
    else:
        rounds = [record for record in turn.get("rounds", []) if isinstance(record, dict)]
        requests = [request for request in turn.get("model_requests", []) if isinstance(request, dict)]
        round_map = {record.get("round"): record for record in rounds}
        request_map = {request.get("round"): request for request in requests}
        numbers = sorted({n for n in (*round_map, *request_map) if isinstance(n, int)})
        event_count = 0
        for number in numbers:
            request, record = request_map.get(number), round_map.get(number)
            if request:
                messages = request.get("messages", [])
                roles = Counter(str(message.get("role", "unknown")) for message in messages if isinstance(message, dict))
                stages.append({"label": f"Context · round {number}", "detail": f'{len(messages)} messages đưa vào model adapter · ' + ", ".join(f"{role}: {count}" for role, count in roles.items()), "status": "observed"})
            if request and request.get("status") == "provider_error":
                stages.append({"label": f"Model · round {number}", "detail": "Lượt gọi adapter thất bại. Chưa đủ dữ liệu xác định HTTP đã gửi; không có response hoàn chỉnh để suy ra tool call.", "status": "error"})
                continue
            calls = record.get("tool_calls", []) if record else []
            if record or request:
                stages.append({"label": f"Model · round {number}", "detail": f'Response có {len(calls)} tool call đề xuất.' if record else "Có request được ghi; chưa có round response trong bản ghi.", "status": "observed"})
            results = [event for event in (record or {}).get("tool_results", []) if isinstance(event, dict)]
            for event in results:
                event_count += 1
                stages.append(_event_stage(event, event_count))
            for call in calls[len(results):]:
                stages.append({"label": "Chưa chạy · " + str(call.get("name", "unknown") if isinstance(call, dict) else "unknown"), "detail": "Model đề xuất nhưng không có tool result tương ứng trong round. Không tính là tool đã thực thi.", "status": "not_executed"})
            if results:
                next_request = any(n > number for n in request_map if isinstance(n, int))
                stages.append({"label": "TOOL_RESULTS_JSON → context", "detail": "Kết quả được thêm vào lịch sử; request tiếp theo đã được ghi." if next_request else "Kết quả được thêm vào lịch sử. Chưa có request tiếp theo được ghi để khẳng định model đã đọc kết quả.", "status": "observed"})
        if not numbers and events:
            stages.append({"label": "Legacy trace", "detail": "Có tool events nhưng không có bản ghi từng model round; không suy ra payload hay số request.", "status": "info"})
            stages.extend(_event_stage(event, index) for index, event in enumerate(events, 1))
    status = str(turn.get("status", "unknown"))
    endings = {
        "answered": ("Answer", "Model đã trả lời; vẫn cần kiểm tra lỗi từng tool.", "ok"),
        "waiting_for_user": ("Pause · chờ người dùng", "Lượt tiếp theo bổ sung dữ liệu/xác nhận vào lịch sử phiên.", "waiting"),
        "blocked": ("Blocked", "Runtime chặn hành động; không có gửi/đăng.", "blocked"),
        "provider_error": ("Provider error", "Lượt chưa có câu trả lời hoàn chỉnh.", "error"),
        "configuration_error": ("Configuration error", "Runtime không tiếp tục khi giới hạn cấu hình không hợp lệ.", "error"),
        "max_tool_calls": ("Stop · giới hạn tool calls", "Những call chưa chạy không được tính thành công.", "waiting"),
        "max_tool_rounds": ("Stop · giới hạn rounds", "Dừng trước khi có kết luận hoàn chỉnh.", "waiting"),
        "tool_error": ("Tool error", "Form trực tiếp nhận lỗi từ tool.", "error"),
    }
    label, detail, state = endings.get(status, ("Kết thúc · " + status, "Trạng thái được lưu trong transcript của lượt này.", "observed"))
    stages.append({"label": label, "detail": detail, "status": state})
    return stages


def trace_html(stages: list[dict[str, Any]]) -> str:
    """Build escaped timeline cards; dynamic data never enters executable HTML."""
    cards = []
    for index, stage in enumerate(stages, 1):
        state = str(stage.get("status", "info"))
        css_state = state if state in _STATUS_CLASS else "info"
        cards.append(f'<div class="pipe-step {css_state}"><span class="pipe-index">{index:02d}</span><div><b>{html.escape(str(stage.get("label", "")))}</b><p>{html.escape(str(stage.get("detail", "")))}</p></div><small>{html.escape(state)}</small></div>')
    return '<div class="pipe-timeline">' + "".join(cards) + '</div>'


_TRACE_STYLES = """<style>
.pipe-timeline{margin:12px 0 22px;display:grid;gap:8px}.pipe-step{display:flex;align-items:flex-start;gap:13px;background:#101e32;border:1px solid #2c405b;border-radius:11px;padding:13px 15px;position:relative}.pipe-index{font:500 14px monospace;color:#66e4cf;padding-top:1px}.pipe-step b{font-size:12px;font-weight:600;color:#dfebfa}.pipe-step p{font-size:11px;color:#92aac8;line-height:1.7;margin:5px 0 0;white-space:pre-wrap;overflow-wrap:anywhere}.pipe-step small{margin-left:auto;font-size:9px;color:#91a8c8;white-space:nowrap;padding:3px 7px;border:1px solid #334b68;border-radius:5px}.pipe-step.error,.pipe-step.blocked{border-left:3px solid #f0ad79}.pipe-step.waiting,.pipe-step.not_executed{border-left:3px solid #a79bff}.pipe-step.ok{border-left:3px solid #66e4cf}.pipe-step.info{border-left:3px solid #79b5ff}.pipe-step.not_executed{opacity:.75}.pipe-step.error small,.pipe-step.blocked small{color:#f0bc91}.pipe-step.waiting small{color:#bcafff}@media(max-width:640px){.pipe-step{padding:11px;gap:8px}.pipe-step small{font-size:8px}.pipe-step b{font-size:11px}}
</style>"""


def show_pipeline(*, session: dict[str, Any], prompt: str, policy: str,
                  declarations: list[dict[str, Any]], artifact: dict[str, Any], model: str) -> None:
    """Render configured flow, inspectable lab prompts and actual turn payloads."""
    section("PIPELINE EXPLORER", "Từ câu hỏi đến câu trả lời", "Chạm từng node để hiểu luồng chạy. Chọn một lượt để đối chiếu request, system prompt, tool calls và kết quả thật.")
    st.iframe(architecture_html(), height=800, alt="Interactive agent architecture: user, system prompt, policy, model, tool dispatch, result feedback and answer")
    st.caption("Sơ đồ giải thích kiến trúc; timeline phía dưới là dữ liệu thực thi sau khi lượt kết thúc. Đây là quan sát request/tool events, không phải suy nghĩ nội bộ của model.")
    st.code("Selected provider.complete() → client.chat.completions.create()", language="text")
    config_tab, turns_tab = st.tabs(["Cấu hình & system prompt", "Lượt thực thi"])
    with config_tab:
        st.info("Cấu hình hiện tại của server. Snapshot ở từng lượt ghi đầu vào đã che dữ liệu nhạy cảm của lần gọi adapter; lịch sử cũ có thể dùng cấu hình khác.")
        cards = [metric("Provider / model", "Groq", model), metric("Prompt hash", str(artifact.get("prompt_hash", ""))[:12], "artifacts/system_prompt.md", "violet"), metric("Tools hash", str(artifact.get("tools_hash", ""))[:12], f"{len(declarations)} tool declarations", "blue"), metric("Execution budget", "4 / 8", "4 rounds · 8 tool calls / lượt", "lime")]
        st.markdown('<div class="metrics">' + "".join(cards) + '</div>', unsafe_allow_html=True)
        st.code("messages[0]   system   ← artifacts/system_prompt.md\nmessages[1]   system   ← PUBLIC_POLICY của app\nmessages[2:-1] history ← các lượt trước trong browser session\nmessages[-1]  user     ← yêu cầu vừa gửi\n\ntools         schemas ← artifacts/tools.yaml → to_openai_tools()\nmodel         Groq    ← NEXUS_MODEL hoặc GROQ_MODEL\ntemperature          = 0.0", language="text")
        with st.expander("System prompt hiện tại · artifacts/system_prompt.md"):
            st.caption("Prompt ứng dụng của bài lab, hiển thị trực tiếp từ file cấu hình của nhóm.")
            st.code(redact(prompt), language="markdown")
        with st.expander("Deployment policy hiện tại · public UI"):
            st.code(redact(policy), language="text")
        with st.expander("Tool schema hiện tại · artifacts/tools.yaml"):
            st.caption("Schema là tham số tools gửi provider, không được nối vào system prompt. Việc tool được khai báo không có nghĩa tool đã chạy.")
            st.json(redact(to_openai_tools(declarations)), expanded=False)
        with st.expander("Code route & giới hạn context"):
            st.code("app.py: chat_panel()\n  → ui/runtime.py: run_turn()\n    → _provider_context(): giữ system + recent messages, tối đa 64.000 ký tự\n    → Selected provider.complete()\n      → client.chat.completions.create(): native function schema\n      → response chuẩn hóa thành text + ToolCall\n    → execute_tool(): send guard → TOOL_FUNCTIONS[name](**args)\n    → tools/<tool>/tool.py\n    → _model_event(): tối đa 24.000 ký tự / tool event cho model\n    → TOOL_RESULTS_JSON (role=user) → vòng model tiếp theo nếu tiếp tục\n  → remember(): giữ context tối đa 70 messages, lưu transcript + render UI\n\nResearch desk: form → execute_tool(research_board) → UI, không gọi model.", language="text")
            st.caption("Trace/transcript giữ kết quả tool đã che dữ liệu nhạy cảm; payload cho model có thể được rút gọn khi quá lớn. Không hiển thị giá trị biến môi trường hay API key.")
            st.json({"artifact_version": artifact.get("artifact_version"), "prompt_hash": artifact.get("prompt_hash"), "tools_hash": artifact.get("tools_hash"), "model": model, "session_turns_limit": 30}, expanded=False)
    with turns_tab:
        turns = session.get("transcript", {}).get("turns", [])
        if not turns:
            st.info("Chưa có lượt thực thi trong phiên này. Gửi một yêu cầu ở Agent chat hoặc chạy Research desk để xem đường đi thực tế.")
            return
        previous_count = st.session_state.get("pipeline_seen_turn_count", 0)
        previous_selection = st.session_state.get("pipeline_turn_index")
        if previous_count != len(turns) or not isinstance(previous_selection, int) or not 0 <= previous_selection < len(turns):
            st.session_state["pipeline_turn_index"] = len(turns) - 1
        st.session_state["pipeline_seen_turn_count"] = len(turns)
        selected = st.selectbox("Lượt cần quan sát", list(range(len(turns))),
                                format_func=lambda index: f'#{turns[index].get("turn_index", index + 1):02d} · {turns[index].get("status", "unknown")} · {str(turns[index].get("user", ""))[:80]}', key="pipeline_turn_index")
        turn = redact(turns[selected])
        st.markdown(_TRACE_STYLES + trace_html(trace_stages(turn)), unsafe_allow_html=True)
        if turn.get("interaction") == "explicit_board_form":
            st.caption("Direct form: 0 model requests. Board.workflow bên trong tool mô tả các bước tìm/gộp/nhóm nguồn; không phải vòng orchestration của agent.")
        elif not turn.get("model_requests"):
            st.warning("Lượt này không có snapshot payload model. Chỉ hiển thị các rounds/tool events đã được ghi; không tái tạo prompt lịch sử từ cấu hình hiện tại.")
        for request in turn.get("model_requests", []):
            number = request.get("round", "?")
            with st.expander(f"Payload gọi model adapter · round {number}", expanded=request.get("status") == "provider_error"):
                st.caption("Snapshot đầu vào adapter đã giới hạn context và che dữ liệu nhạy cảm; không phải HTTP JSON nguyên bản. Với lỗi provider, bản ghi không chứng minh HTTP đã được gửi. Role/order bên dưới được ghi ngay trước khi gọi adapter.")
                st.json(request, expanded=False)
                for index, message in enumerate(request.get("messages", [])):
                    if isinstance(message, dict):
                        st.caption(f'messages[{index}] · role={message.get("role", "unknown")} · {len(str(message.get("content", "")))} ký tự')
                        st.code(str(message.get("content", "")), language="text")
        if turn.get("request_config"):
            with st.expander("Cấu hình request đã ghi · schema & giới hạn"):
                st.json(turn["request_config"], expanded=False)
        with st.expander("Round responses · tool calls đề xuất và results"):
            st.json({"rounds": turn.get("rounds", []), "tool_events": turn.get("tool_events", []), "error": turn.get("error")}, expanded=False)
        st.caption(f'Trạng thái cuối: {turn.get("status", "unknown")} · thời gian: {turn.get("duration_seconds", "—")}s · transcript được quản lý theo phiên, có thể tải ở sidebar.')
