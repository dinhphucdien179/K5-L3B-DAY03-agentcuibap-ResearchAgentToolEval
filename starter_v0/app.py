"""Streamlit workbench for the real Research Agent (no API calls on page load).

Run: conda run -n AI20k python -m streamlit run app.py
"""
from __future__ import annotations

import html
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import streamlit as st

from chat import execute_tool_call, now_iso, run_model_tool_loop, trim_history, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from providers.base import ToolCall
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).resolve().parent
PROMPT_PATH = ROOT / "artifacts" / "system_prompt.md"
TOOLS_PATH = ROOT / "artifacts" / "tools.yaml"
PROVIDERS = ("openrouter", "openai", "gemini", "anthropic", "ollama")
PROVIDER_KEYS = {
    "openrouter": "OPENROUTER_API_KEY", "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY", "anthropic": "ANTHROPIC_API_KEY",
}
PROVIDER_LABELS = {
    "openrouter": "OpenRouter", "openai": "OpenAI", "gemini": "Google Gemini",
    "anthropic": "Anthropic", "ollama": "Ollama · local",
}
SAMPLE_PROMPTS = (
    ("Nghiên cứu đa góc nhìn", "Nghiên cứu RAG trong doanh nghiệp theo 3 góc: hiệu quả thực tế, chi phí triển khai và rủi ro bảo mật. Dẫn nguồn cho từng phần và chỉ rõ chỗ thiếu bằng chứng."),
    ("So sánh có bằng chứng", "So sánh PostgreSQL và MongoDB cho hệ thống phân tích dữ liệu theo hai tiêu chí: khả năng truy vấn và vận hành. Thu thập nguồn cho từng ô so sánh; không tự chấm điểm nếu thiếu bằng chứng."),
    ("Kiểm tra trích dẫn", 'Kiểm tra cấu trúc trích dẫn của bản nháp sau bằng danh mục nguồn, báo ID thiếu và đoạn chưa dẫn nguồn, không đánh giá tính đúng sai.\nBản nháp:\nRAG kết hợp truy xuất và sinh văn bản [S1].\n\nKhẳng định này chưa có tài liệu dẫn chứng [S9].\nNguồn: [{"id":"S1","url":"https://arxiv.org/abs/2005.11401"}]'),
    ("Làm sạch danh sách nguồn", 'Loại nguồn trùng URL, giữ bản xuất hiện đầu tiên từ danh sách này: [{"title":"RAG paper","url":"https://arxiv.org/abs/2005.11401"},{"title":"RAG paper có tracking","url":"https://arxiv.org/abs/2005.11401?utm_source=demo"},{"title":"Transformer paper","url":"https://arxiv.org/abs/1706.03762"}]'),
)

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
:root {color-scheme: dark;}
.stApp {background:#080f1d; color:#e6edf7;}
html, body, [class*="css"], [data-testid="stAppViewContainer"] {font-family:'Be Vietnam Pro',system-ui,sans-serif;}
.block-container {max-width:1120px; padding-top:2.3rem; padding-bottom:5rem;}
[data-testid="stHeader"] {background:rgba(8,15,29,.94);}
[data-testid="stSidebar"] {background:#0e1729; border-right:1px solid #22304a;}
[data-testid="stSidebar"] .block-container {padding-top:1.5rem;}
h1,h2,h3,p,label {color:inherit;}
.ra-eyebrow {font-size:.72rem;font-weight:700;letter-spacing:.16em;color:#73e5c0;margin-bottom:16px;}
.ra-hero {padding:30px 32px 28px;background:radial-gradient(ellipse at 100% 0%,#193b52 0,transparent 54%),#101c31;border:1px solid #283b57;border-radius:20px;margin-bottom:20px;}
.ra-hero h1 {font-size:clamp(1.9rem,4.5vw,3rem);line-height:1.2;font-weight:800;letter-spacing:-.05em;margin:0 0 14px;padding:0;color:#f3f7ff;}
.ra-hero p {font-size:.96rem;line-height:1.85;color:#aebed4;max-width:700px;margin:0;}
.ra-pill {display:inline-block;font-size:.68rem;border-radius:30px;border:1px solid #345166;background:#142e3c;color:#8be5ca;padding:5px 10px;margin-top:20px;}
.ra-card {min-height:136px;background:#111d30;border:1px solid #26354f;border-radius:13px;padding:18px;margin-bottom:16px;}
.ra-card h3 {font-size:.92rem;color:#f2f6fc;margin:0 0 8px;padding:0;font-weight:600;}
.ra-card p {font-size:.78rem;color:#a4b6ce;line-height:1.7;margin:0;}
.ra-dot {display:inline-block;width:7px;height:7px;background:#7ee1ba;border-radius:50%;margin-right:8px;}
.ra-source {border:1px solid #293b55;border-radius:12px;padding:15px 17px;background:#0f1b2c;margin:8px 0;}
.ra-source a {font-weight:600;color:#9acbff;text-decoration:none;font-size:.88rem;}
.ra-source small {display:block;color:#7f99b9;margin-top:7px;font-size:.72rem;}
.ra-source p {color:#adbed5;font-size:.78rem;line-height:1.6;margin:9px 0 0;}
.ra-brand {font-size:1rem;font-weight:800;letter-spacing:-.04em;color:#f4f7fc;margin:0 0 4px;}
.ra-footer {color:#7389a7;font-size:.71rem;line-height:1.7;}
[data-testid="stChatMessage"] {border:1px solid #26344c;border-radius:14px;background:#111d2f;}
[data-testid="stChatInput"] {border:1px solid #365570;border-radius:14px;background:#122137;}
[data-testid="stBottomBlockContainer"] {background:#080f1d;}
button[kind="primary"] {background:#74dfba!important;color:#092a26!important;border:none!important;font-weight:700;}
button[kind="secondary"] {border:1px solid #33455f!important;background:#142136!important;color:#dde8f7!important;}
[data-testid="stExpander"] {border-color:#2a3b53;background:#0e192b;border-radius:12px;}
[data-testid="stCaptionContainer"] {color:#8fa5c1;}
@media(max-width:640px){.ra-hero{padding:23px 21px}.block-container{padding-top:1.4rem}.ra-card{min-height:auto}}
</style>
"""


def redact(value: Any) -> Any:
    """Keep configured credentials out of errors, traces, and downloadable logs."""
    secrets = [v for k, v in os.environ.items()
               if v and len(v) >= 8 and (k.endswith("_KEY") or k.endswith("_TOKEN"))]

    def clean(item: Any) -> Any:
        if isinstance(item, str):
            for secret in secrets:
                item = item.replace(secret, "[REDACTED]")
            return item
        if isinstance(item, dict):
            return {k: "[REDACTED]" if str(k).lower() in {"api_key", "token", "authorization"}
                    else clean(v) for k, v in item.items()}
        if isinstance(item, (list, tuple)):
            return [clean(v) for v in item]
        return item

    return clean(value)


def extract_sources(events: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Find cited source records in different tools' nested output formats."""
    sources: dict[str, dict[str, str]] = {}
    evidence_by_id: dict[str, str] = {}

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            url = value.get("url") or value.get("source_url")
            if isinstance(url, str):
                try:
                    parsed = urlsplit(url)
                    valid = parsed.scheme in {"http", "https"} and bool(parsed.hostname) and not parsed.username
                except ValueError:
                    valid = False
                if valid and url not in sources:
                    excerpt = value.get("summary") or value.get("abstract") or value.get("content") or ""
                    excerpts = value.get("excerpts")
                    if (not excerpt and isinstance(excerpts, list) and excerpts
                            and isinstance(excerpts[0], dict)):
                        excerpt = excerpts[0].get("text", "")
                    if not excerpt:
                        excerpt = evidence_by_id.get(str(value.get("id", "")), "")
                    sources[url] = {"url": url, "title": str(value.get("title") or parsed.hostname),
                                    "domain": parsed.hostname or "", "excerpt": str(excerpt)[:320],
                                    "id": str(value.get("id", ""))}
            for nested in value.values():
                if isinstance(nested, (dict, list)):
                    visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    for event in events:
        result = event.get("result", {})
        # Comparison tools keep snippets in matrix cells and URLs in a catalog.
        # Join within one event: S1 in another tool call may mean another source.
        evidence_by_id = {}
        if isinstance(result, dict):
            for cell in result.get("cells", []):
                if not isinstance(cell, dict):
                    continue
                for evidence in cell.get("evidence", []):
                    if isinstance(evidence, dict) and isinstance(evidence.get("excerpt"), str):
                        source_id = str(evidence.get("source_id", ""))
                        if source_id and source_id not in evidence_by_id:
                            evidence_by_id[source_id] = evidence["excerpt"]
        visit(result)
    return list(sources.values())


def tool_issues(events: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for event in events:
        result = event.get("result", {})
        if not isinstance(result, dict):
            continue
        name = event.get("tool", "tool")
        if result.get("error"):
            issues.append(f"{name}: {result['error']}" + (f" — {result['message']}" if result.get("message") else ""))
        elif result.get("status") == "partial" or result.get("search_errors"):
            coverage = (f" ({result['covered_cells']}/{result['total_cells']} ô có nguồn)"
                        if "covered_cells" in result and "total_cells" in result else "")
            issues.append(f"{name}: chỉ thu được một phần dữ liệu{coverage}. Xem các nguồn còn thiếu trong trace.")
        elif result.get("status") == "review_needed":
            issues.append(f"{name}: cần rà soát {len(result.get('unresolved_citations', []))} trích dẫn chưa khớp, "
                          f"{len(result.get('uncited_blocks', []))} đoạn thiếu trích dẫn hợp lệ và "
                          f"{len(result.get('catalog_issues', []))} lỗi danh mục nguồn. "
                          "Đây là kiểm tra cấu trúc tham chiếu, chưa xác minh tính đúng sai.")
    return redact(issues)


def pending_send(result: dict[str, Any]) -> str | None:
    """The UI confirms the exact tool payload rather than a model-written claim."""
    pending = result.get("pending_send")
    if isinstance(pending, dict) and isinstance(pending.get("text"), str):
        return pending["text"]
    for event in result.get("tool_events", []):
        output = event.get("result", {})
        if (event.get("tool") == "send" and isinstance(output, dict)
                and output.get("status") in {"needs_confirmation", "confirmation_required"}):
            text = event.get("args", {}).get("text")
            if isinstance(text, str) and text.strip():
                return text
    return None


def init_session() -> None:
    if "research_transcript" not in st.session_state:
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        st.session_state.research_transcript = {
            "transcript_id": f"ui_{timestamp}", "created_at": now_iso(),
            "updated_at": now_iso(), "interface": "streamlit", "turns": [],
        }


def persist() -> None:
    transcript = st.session_state.research_transcript
    path = ROOT / "transcripts" / f"{transcript['transcript_id']}.transcript.json"
    try:
        write_transcript(path, redact(transcript))
        st.session_state.transcript_saved = True
    except OSError as exc:
        st.session_state.transcript_saved = False
        st.warning(f"Chưa ghi được transcript lên đĩa: {redact(str(exc))}. Bạn vẫn có thể tải JSON từ thanh bên.")


def clear_pending_send(status: str) -> None:
    """Invalidate approvals when a draft is cancelled or the conversation moves on."""
    text = st.session_state.pop("telegram_pending", None)
    origin = st.session_state.pop("telegram_pending_turn", None)
    if not text:
        return
    for turn in reversed(st.session_state.research_transcript["turns"]):
        if turn.get("turn_index") == origin:
            turn["send_confirmation"] = {"status": status, "decided_at": now_iso(), "source": "ui"}
            break


def render_sources(events: list[dict[str, Any]]) -> None:
    sources = extract_sources(events)
    if not sources:
        return
    with st.expander(f"Nguồn tham khảo · {len(sources)}", expanded=True):
        for source in sources[:12]:
            title, url, domain, excerpt = (html.escape(str(redact(source[k])), quote=True)
                                           for k in ("title", "url", "domain", "excerpt"))
            if source.get("id"):
                title = f"[{html.escape(source['id'])}] {title}"
            st.markdown(f'<div class="ra-source"><a href="{url}" target="_blank" rel="noopener noreferrer">↗ {title}</a>'
                        f'<small>{domain}</small>' + (f'<p>{excerpt}</p>' if excerpt else '') + '</div>',
                        unsafe_allow_html=True)
        if len(sources) > 12:
            st.caption("Hiển thị 12 nguồn đầu tiên. Toàn bộ nguồn nằm trong transcript.")


def render_turn(turn: dict[str, Any]) -> None:
    with st.chat_message("user", avatar="👤"):
        st.markdown(redact(turn["user"]))
    with st.chat_message("assistant", avatar="🔎"):
        if turn.get("status") == "provider_error":
            st.error(redact(turn.get("error", "Lỗi provider. Kiểm tra kết nối, model và cấu hình API.")))
        else:
            st.markdown(redact(turn.get("assistant_text") or "Agent chưa trả về nội dung."))
        if turn.get("status") == "waiting_for_user":
            st.info("Agent đang chờ bạn bổ sung thông tin. Trả lời ở ô chat bên dưới.")
        elif turn.get("status") == "max_tool_rounds":
            st.warning("Đã đến giới hạn số vòng gọi tool. Hãy thu hẹp yêu cầu hoặc tăng giới hạn ở thanh bên.")
        events = turn.get("tool_events", [])
        for issue in tool_issues(events):
            st.warning(f"Tool báo lỗi / thiếu dữ liệu · {issue}")
        render_sources(events)
        if events or turn.get("rounds"):
            with st.expander(f"Theo dõi agent · {len(events)} lần gọi tool", expanded=False):
                for index, event in enumerate(events, 1):
                    st.markdown(f"**{index}. `{event.get('tool', 'tool')}`**")
                    st.json(redact({"arguments": event.get("args", {}), "result": event.get("result", {})}), expanded=False)
                if not events:
                    st.caption("Agent trả lời trực tiếp, không gọi tool ở lượt này.")
        st.caption(f"{PROVIDER_LABELS.get(turn.get('provider'), turn.get('provider', ''))} · "
                   f"{turn.get('model', '')} · {len(events)} tool · {turn.get('status', '')}")


def run_turn(user_text: str, provider_name: str, model: str, version: str, max_rounds: int) -> None:
    clear_pending_send("superseded_by_new_message")
    transcript = st.session_state.research_transcript
    history = []
    for turn in transcript["turns"]:
        if turn.get("status") != "provider_error":
            history.extend([{"role": "user", "content": turn["user"]},
                            {"role": "assistant", "content": turn.get("assistant_text", "")}])
    turn = {"turn_index": len(transcript["turns"]) + 1, "started_at": now_iso(),
            "user": user_text, "provider": provider_name, "model": model, "status": "started",
            "rounds": [], "tool_events": []}
    try:
        artifact = artifact_version_dict(build_artifact_version(version or "workbench", PROMPT_PATH, TOOLS_PATH))
        transcript.update({**artifact, "provider": provider_name, "model": model,
                           "system_prompt": str(PROMPT_PATH), "tools": str(TOOLS_PATH),
                           "history_window": 8, "max_tool_rounds": max_rounds})
        turn.update(artifact)
        result = run_model_tool_loop(
            provider=make_provider(provider_name),
            messages=[{"role": "system", "content": PROMPT_PATH.read_text(encoding="utf-8")},
                      *trim_history(history, 8), {"role": "user", "content": user_text}],
            tools=to_openai_tools(load_tool_declarations(TOOLS_PATH)), model=model or None,
            max_tool_rounds=max_rounds,
        )
        turn.update(result)
        text = pending_send(result)
        if text:
            st.session_state.telegram_pending = text
            st.session_state.telegram_pending_turn = turn["turn_index"]
    except Exception as exc:
        turn.update(status="provider_error", error=redact(f"{type(exc).__name__}: {exc}"))
    turn["ended_at"] = now_iso()
    transcript["turns"].append(redact(turn))
    persist()


def render_confirmation() -> None:
    text = st.session_state.get("telegram_pending")
    if not text:
        return
    transcript = st.session_state.research_transcript
    turns = transcript["turns"]
    if not turns or st.session_state.get("telegram_pending_turn") != turns[-1].get("turn_index"):
        clear_pending_send("superseded_by_new_message")
        persist()
        return
    with st.container(border=True):
        st.markdown("**Xác nhận gửi Telegram**")
        st.caption("Kiểm tra nội dung nguyên văn dưới đây. Chỉ nút xác nhận mới thực hiện gửi.")
        st.code(redact(text), language=None, wrap_lines=True)
        contains_secret = redact(text) != text
        if contains_secret:
            st.error("Bản nháp chứa thông tin bí mật đã được che. Hãy hủy và tạo lại nội dung trước khi gửi.")
        approve, cancel = st.columns(2)
        if approve.button("Xác nhận gửi Telegram", type="primary", use_container_width=True, disabled=contains_secret):
            # Consume this approval before the side effect; a rerun cannot reuse it.
            clear_pending_send("approved")
            with st.spinner("Đang gửi nội dung đã xác nhận…"):
                event = execute_tool_call(ToolCall(name="send", args={"text": text, "confirmed": True}),
                                          confirmed_send_text=text)
            result = event.get("result", {})
            succeeded = result.get("status") == "sent"
            transcript["turns"].append({
                "turn_index": len(transcript["turns"]) + 1, "started_at": now_iso(), "ended_at": now_iso(),
                "user": f"Xác nhận gửi Telegram đúng nội dung sau:\n{text}",
                "assistant_text": "Đã gửi Telegram." if succeeded else "Gửi Telegram chưa thành công. Xem lỗi tool bên dưới.",
                "provider": "ui", "model": "explicit-user-confirmation", "status": "answered",
                "rounds": [], "tool_events": [event], "confirmation_source": "ui_button",
            })
            persist()
            st.rerun()
        if cancel.button("Hủy gửi", use_container_width=True):
            clear_pending_send("cancelled")
            persist()
            st.rerun()


def main() -> None:
    st.set_page_config(page_title="Research Studio · agentcuibap", page_icon="✳", layout="wide")
    load_lab_env(ROOT)
    st.markdown(STYLE, unsafe_allow_html=True)
    init_session()
    declarations = load_tool_declarations(TOOLS_PATH)

    with st.sidebar:
        st.markdown('<div class="ra-brand">✳ Research Studio</div><div class="ra-footer">agentcuibap · Research Agent</div>', unsafe_allow_html=True)
        st.divider()
        st.caption("KẾT NỐI MÔ HÌNH")
        default = next((name for name in PROVIDERS if os.getenv(PROVIDER_KEYS.get(name, ""))), "openai")
        provider = st.selectbox("Provider", PROVIDERS, index=PROVIDERS.index(default), format_func=lambda name: PROVIDER_LABELS[name])
        default_model = getattr(make_provider(provider), "default_model", "")
        model = st.text_input("Model", value=default_model, key=f"model_{provider}", help="Tên model do provider hỗ trợ. Có thể thay trước mỗi lượt chat.").strip()
        configured = provider == "ollama" or bool(os.getenv(PROVIDER_KEYS.get(provider, "")))
        if configured:
            st.success("Đã có cấu hình · sẵn sàng kiểm tra khi chat", icon="✅")
        else:
            st.warning(f"Chưa có {PROVIDER_KEYS.get(provider, 'API key')} trong .env")
        st.caption("Trang chỉ đọc trạng thái cấu hình, không hiển thị API key.")
        with st.expander("Tùy chỉnh phiên"):
            version = st.text_input("Nhãn artifact", value="v6", help="Hash prompt và tools được ghi tự động trong transcript.")
            max_rounds = st.slider("Số vòng gọi tool tối đa", min_value=1, max_value=10, value=6)
        st.divider()
        st.caption("KHO CÔNG CỤ")
        st.markdown(f"**{len(declarations)} tools** · nghiên cứu & tổng hợp")
        for label, key in (("Tìm kiếm · Tavily", "TAVILY_API_KEY"), ("Đọc web · Firecrawl", "FIRECRAWL_API_KEY"),
                           ("Mạng xã hội · RapidAPI", "RAPIDAPI_KEY")):
            st.caption(f"{'●' if os.getenv(key) else '○'} {label}")
        with st.expander("Danh sách tool"):
            st.code(" · ".join(item["name"] for item in declarations), language=None, wrap_lines=True)
        st.divider()
        transcript = st.session_state.research_transcript
        st.caption(f"PHIÊN HIỆN TẠI · {len(transcript['turns'])} LƯỢT")
        st.download_button("↓ Tải transcript JSON", json.dumps(redact(transcript), ensure_ascii=False, indent=2, default=str),
                           file_name=f"{transcript['transcript_id']}.transcript.json", mime="application/json", use_container_width=True)
        if st.button("＋ Cuộc trò chuyện mới", use_container_width=True):
            clear_pending_send("cancelled_by_new_session")
            if transcript["turns"]:
                persist()
            for key in ("research_transcript", "telegram_pending", "telegram_pending_turn", "transcript_saved", "queued_prompt"):
                st.session_state.pop(key, None)
            st.rerun()
        if st.session_state.get("transcript_saved"):
            st.caption("✓ Transcript được lưu sau mỗi lượt trong transcripts/.")
        st.markdown('<p class="ra-footer">Mỗi câu trả lời có trace và nguồn gốc dữ liệu. Nội dung web là dữ liệu chưa được xác minh; mở nguồn trước khi dùng cho quyết định quan trọng.</p>', unsafe_allow_html=True)

    st.markdown('<div class="ra-hero"><div class="ra-eyebrow">RESEARCH WORKSPACE / 01</div>'
                '<h1>Từ câu hỏi.<br>Đến bằng chứng.</h1>'
                '<p>Tìm nguồn, đọc tài liệu và nghiên cứu đa góc nhìn trong một cuộc trò chuyện. '
                'Theo dõi từng lần gọi tool và kiểm tra nguồn ngay bên dưới câu trả lời.</p>'
                '<span class="ra-pill"><span class="ra-dot"></span>Live tools · Có nguồn · Có transcript</span></div>', unsafe_allow_html=True)

    if not transcript["turns"]:
        cards = (("01 / Khám phá", "Nghiên cứu theo nhiều góc nhìn, giữ bằng chứng và nhận diện phần còn thiếu."),
                 ("02 / Kiểm chứng", "Đọc trang gốc, tìm paper khoa học và đối chiếu các nguồn liên quan."),
                 ("03 / Chia sẻ", "Tạo digest có dẫn nguồn. Duyệt nguyên văn trước khi gửi qua Telegram."))
        for column, (title, body) in zip(st.columns(3), cards):
            with column:
                st.markdown(f'<div class="ra-card"><h3>{title}</h3><p>{body}</p></div>', unsafe_allow_html=True)
        st.markdown("**Bắt đầu với một câu hỏi**")
        for start in range(0, len(SAMPLE_PROMPTS), 2):
            for column, (label, prompt) in zip(st.columns(2), SAMPLE_PROMPTS[start:start + 2]):
                if column.button(label + " ↗", use_container_width=True, disabled=not configured):
                    st.session_state.queued_prompt = prompt
                    st.rerun()
        st.caption("Bạn cũng có thể gửi yêu cầu chưa đầy đủ để agent hỏi thêm thông tin.")

    for turn in transcript["turns"]:
        render_turn(turn)
    prompt = st.chat_input("Bạn muốn nghiên cứu điều gì?", disabled=not configured)
    prompt = prompt or st.session_state.pop("queued_prompt", None)
    if prompt and prompt.strip():
        with st.chat_message("user", avatar="👤"):
            st.markdown(redact(prompt))
        with st.status("Agent đang nghiên cứu…", expanded=True):
            st.write("Đang chọn tool, thu thập dữ liệu và chuẩn bị câu trả lời có nguồn.")
            run_turn(prompt.strip(), provider, model, version, max_rounds)
        st.rerun()
    else:
        render_confirmation()


if __name__ == "__main__":
    main()
