"""Execute tools with a confirmation boundary enforced outside the model."""
from __future__ import annotations

from typing import Any

from providers.base import ToolCall
from tools import TOOL_FUNCTIONS


def execute_tool_call(call: ToolCall, *, confirmed_send_text: str | None = None) -> dict[str, Any]:
    func = TOOL_FUNCTIONS.get(call.name)
    if not func:
        return {"tool": call.name, "args": call.args,
                "result": {"error": "unknown_tool", "message": f"No local implementation for {call.name}"}}
    # A model-supplied boolean is not proof of user consent. The UI/CLI supplies
    # the exact approved text independently, and approval only covers that text.
    if call.name == "send" and (
        not isinstance(confirmed_send_text, str) or not confirmed_send_text.strip()
        or call.args.get("text") != confirmed_send_text or call.args.get("confirmed") is not True
    ):
        return {"tool": call.name, "args": call.args, "result": {
            "status": "needs_confirmation", "awaiting_user": True,
            "question": "Bạn xác nhận gửi nguyên văn nội dung này lên Telegram của nhóm chứ?\n\n"
                        + str(call.args.get("text", "")),
            "pending_send": {"text": call.args.get("text", "")},
        }}
    try:
        result = func(**call.args)
    except Exception as exc:
        result = {"error": type(exc).__name__, "message": str(exc)}
    return {"tool": call.name, "args": call.args, "result": result}
