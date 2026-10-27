"""CLI-only synchronous driver, including explicit user approval on tool side effects."""
from __future__ import annotations
from typing import Any, Callable


def _show_approval(interrupts, input_fn: Callable[[str], str]) -> dict:
    decisions = []
    for item in interrupts:
        payload = item.value
        if not isinstance(payload, dict) or "action_requests" not in payload:
            raise RuntimeError("Unknown interrupt format; manual review required")
        for action in payload["action_requests"]:
            print("\n[Requires human review]")
            print("  Tool:", action.get("name"))
            print("  Args:", action.get("args"))
            approved = input_fn("Approve this action? [y/N]: ").strip().lower() == "y"
            decisions.append({"type": "approve"} if approved else
                             {"type": "reject", "message": "Human reviewer declined this action."})
    return {"decisions": decisions}


def run_turn(graph, message: str, *, thread_id: str, trace: bool = False,
             input_fn: Callable[[str], str] = input) -> str:
    from langgraph.types import Command

    config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config=config, version="v2",
    )
    while result.interrupts:
        decisions = _show_approval(result.interrupts, input_fn)
        result = graph.invoke(Command(resume=decisions), config=config, version="v2")

    messages = result.value.get("messages", [])
    if trace:
        print("\n--- TRACE (tool names only; inputs/outputs omitted) ---")
        for msg in messages:
            for call in getattr(msg, "tool_calls", []) or []:
                print("  tool_call:", call.get("name"))
            if getattr(msg, "type", None) == "tool":
                print("  tool_result:", getattr(msg, "name", "unknown"))
        print("--- END TRACE ---\n")
    if not messages:
        return "[No final messages returned]"
    latest = messages[-1]
    if getattr(latest, "type", None) != "ai":
        return "[Agent stopped without a final assistant answer; inspect trace/limits.]"
    content = latest.content
    if isinstance(content, str):
        return content
    # Some model providers return content blocks rather than plain strings.
    if isinstance(content, list):
        return "\n".join(str(c.get("text", "")) if isinstance(c, dict) else str(c)
                         for c in content).strip()
    return str(content)
