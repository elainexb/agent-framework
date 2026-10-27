"""Small, transparent end-to-end evaluation scaffold. NOT a full eval platform."""
from __future__ import annotations
import json
from pathlib import Path
import uuid

from .config import AgentSpec


def load_cases(spec: AgentSpec) -> list[dict]:
    path = spec.folder / "eval_cases.json"
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        raise ValueError(f"{path}: expected a JSON list")
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("input"), str):
            raise ValueError(f"{path}: every case requires a string input")
        if not isinstance(case.get("expected_tools", []), list):
            raise ValueError(f"{path}: expected_tools must be a list")
    return cases


def score_case(case: dict, messages: list) -> dict:
    invoked = [call.get("name") for msg in messages
               for call in (getattr(msg, "tool_calls", None) or [])]
    final = messages[-1].content if messages else ""
    if not isinstance(final, str):
        final = str(final)
    required = case.get("expected_tools", [])
    keywords = case.get("answer_contains_any", [])
    tool_pass = all(name in invoked for name in required)
    answer_pass = bool(final.strip()) and (not keywords or any(k.casefold() in final.casefold() for k in keywords))
    return {"id": case.get("id", "unnamed"), "passed": tool_pass and answer_pass,
            "tool_pass": tool_pass, "answer_pass": answer_pass,
            "observed_tools": invoked, "expected_tools": required}


def live_evaluate(spec: AgentSpec) -> list[dict]:
    """Calls an actual LLM; may incur API usage or local compute. No approvals automated."""
    from .builder import build_agent
    graph = build_agent(spec)
    results = []
    for case in load_cases(spec):
        config = {"configurable": {"thread_id": "eval-" + uuid.uuid4().hex}}
        res = graph.invoke({"messages": [{"role": "user", "content": case["input"]}]},
                           config=config, version="v2")
        if res.interrupts:
            # Never silently authorize a write in evaluation.
            results.append({"id": case.get("id"), "passed": False,
                            "error": "HITL interrupt: evaluation refuses to auto-approve"})
        else:
            results.append(score_case(case, res.value.get("messages", [])))
    return results
