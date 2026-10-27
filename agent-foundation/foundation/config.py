"""Load and validate an agent's declarative specification (no LLM imports)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENTS_ROOT = PROJECT_ROOT / "agents"
_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class AgentSpec:
    name: str
    description: str
    folder: Path
    instructions: str
    tools: tuple[str, ...]
    provider: str
    model: str
    temperature: float
    max_model_calls: int
    max_tool_calls: int
    retry_tools: tuple[str, ...]
    retry_attempts: int
    approval_tools: tuple[str, ...]


def valid_name(name: str) -> bool:
    return bool(_NAME.fullmatch(name)) and name != "_template"


def get_agent_folder(name: str) -> Path:
    if not valid_name(name):
        raise ValueError("Agent name must be lowercase snake_case (e.g. my_agent).")
    return AGENTS_ROOT / name


def list_agents() -> list[str]:
    if not AGENTS_ROOT.exists():
        return []
    return sorted(p.name for p in AGENTS_ROOT.iterdir()
                  if p.is_dir() and valid_name(p.name) and (p / "agent.yaml").is_file())


def _mapping(obj: Any, where: str) -> dict[str, Any]:
    if not isinstance(obj, dict):
        raise ValueError(f"{where} must be a YAML mapping")
    return obj


def _integer(obj: Any, where: str, minimum: int = 0) -> int:
    if type(obj) is not int or obj < minimum:
        raise ValueError(f"{where} must be an integer >= {minimum}")
    return obj


def _strings(obj: Any, where: str) -> tuple[str, ...]:
    if not isinstance(obj, list) or any(not isinstance(x, str) or not x.strip() for x in obj):
        raise ValueError(f"{where} must be a list of nonempty strings")
    return tuple(obj)


def load_spec(name: str) -> AgentSpec:
    folder = get_agent_folder(name)
    path = folder / "agent.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Missing agent configuration: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    instructions_path = folder / "instructions.md"
    if not instructions_path.is_file():
        raise FileNotFoundError(f"Missing instructions: {instructions_path}")
    own = instructions_path.read_text(encoding="utf-8")
    base = (PROJECT_ROOT / "foundation" / "base_instructions.md").read_text(encoding="utf-8")
    return parse_spec(name, raw, own, base)


def parse_spec(name: str, raw: Any, own: str, base: str) -> AgentSpec:
    """Validate captured definition content using the same rules as load_spec."""
    folder = get_agent_folder(name)
    raw = _mapping(raw, "agent.yaml")
    if raw.get("name") != name:
        raise ValueError(f"agent.yaml name must equal folder name: {name}")
    model = _mapping(raw.get("model"), "model")
    runtime = _mapping(raw.get("runtime", {}), "runtime")
    approval = _mapping(raw.get("approval", {}), "approval")
    retry = _mapping(runtime.get("retry", {}), "runtime.retry")
    provider = model.get("provider")
    if provider not in {"ollama", "openai"}:
        raise ValueError("model.provider must be 'ollama' or 'openai'")
    model_id = model.get("name")
    if not isinstance(model_id, str) or not model_id.strip():
        raise ValueError("model.name must be a nonempty string")
    try:
        temperature = float(model.get("temperature", 0.0))
    except (TypeError, ValueError) as exc:
        raise ValueError("model.temperature must be numeric") from exc
    if not 0 <= temperature <= 2:
        raise ValueError("model.temperature must be between 0 and 2")
    tools = _strings(raw.get("tools", []), "tools")
    if len(set(tools)) != len(tools):
        raise ValueError("Duplicate tool entry")
    for entry in tools:
        if not re.fullmatch(r"agents\.[a-z][a-z0-9_]*\.tools:[a-zA-Z_]\w*", entry):
            raise ValueError(f"Invalid tool entry: {entry}")
        if entry.split(".")[1] != name:
            raise ValueError(f"Tools must be in the agent's own module: {entry}")
    approval_tools = _strings(approval.get("tools", []), "approval.tools")
    retry_tools = _strings(retry.get("tools", []), "runtime.retry.tools")
    tool_names = {entry.rsplit(":", 1)[1] for entry in tools}
    if not set(approval_tools).issubset(tool_names):
        raise ValueError("approval.tools must reference registered tool function names")
    if not set(retry_tools).issubset(tool_names):
        raise ValueError("runtime.retry.tools must reference registered tool function names")
    if not own.strip():
        raise ValueError("instructions.md may not be empty")
    return AgentSpec(
        name=name,
        description=str(raw.get("description", "")),
        folder=folder,
        instructions=base.strip() + "\n\n" + own.strip(),
        tools=tools,
        provider=provider,
        model=model_id,
        temperature=temperature,
        max_model_calls=_integer(runtime.get("max_model_calls", 8), "runtime.max_model_calls", 1),
        max_tool_calls=_integer(runtime.get("max_tool_calls", 12), "runtime.max_tool_calls", 1),
        retry_tools=retry_tools,
        retry_attempts=_integer(retry.get("attempts", 0), "runtime.retry.attempts"),
        approval_tools=approval_tools,
    )
