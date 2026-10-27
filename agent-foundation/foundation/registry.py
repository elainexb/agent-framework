"""Explicit tool allowlist. Only trusted code listed in agent.yaml is imported."""
from __future__ import annotations
from importlib import import_module
from typing import Any
from .config import AgentSpec


def load_tools(spec: AgentSpec) -> list[Any]:
    tools: list[Any] = []
    names: set[str] = set()
    for entry in spec.tools:
        module_name, func_name = entry.split(":", 1)
        candidate = getattr(import_module(module_name), func_name)
        # LangChain @tool objects expose .invoke, .name, and .description.
        if not callable(getattr(candidate, "invoke", None)) or not getattr(candidate, "name", None):
            raise TypeError(f"{entry} must be decorated with langchain @tool")
        if candidate.name in names:
            raise ValueError(f"Duplicate registered tool name: {candidate.name}")
        names.add(candidate.name)
        tools.append(candidate)
    return tools
