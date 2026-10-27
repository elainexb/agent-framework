"""Inspect the existing Agent definition without importing business code or models."""
from __future__ import annotations

import ast
import hashlib
import yaml

from .config import PROJECT_ROOT, get_agent_folder, list_agents, parse_spec


def _check(status: str, detail: str) -> dict:
    return {"status": status, "detail": detail}


def inspect_agent(name: str) -> dict:
    folder = get_agent_folder(name)
    result = {
        "name": name,
        "description": "",
        "source_version": None,
        "configuration": _check("UNKNOWN", "尚未检查"),
        "tools": _check("UNKNOWN", "尚未检查"),
        "build": _check("UNKNOWN", "需求、业务能力与质量资源契约需按 build-agent 流程审查"),
        "model": {"status": "UNKNOWN", "provider": None, "name": None,
                  "detail": "未连接模型；权重版本、响应及工具调用尚未验证"},
        "can_run": False,
        "runtime": _check("FAIL", "第1票仅提供配置入口；网页试跑属于后续任务"),
    }
    try:
        contents = {filename: (folder / filename).read_text(encoding="utf-8")
                    for filename in ("agent.yaml", "instructions.md")}
        contents["base_instructions.md"] = (PROJECT_ROOT / "foundation" / "base_instructions.md").read_text(encoding="utf-8")
        for filename in ("tools.py", "services.py"):
            path = folder / filename
            if path.is_file():
                contents[filename] = path.read_text(encoding="utf-8")
        raw = yaml.safe_load(contents["agent.yaml"])
        spec = parse_spec(name, raw, contents["instructions.md"], contents["base_instructions.md"])
        sections = [(raw, {"name", "description", "model", "tools", "runtime", "approval"}, "agent.yaml"),
                    (raw["model"], {"provider", "name", "temperature"}, "model"),
                    (raw.get("runtime", {}), {"max_model_calls", "max_tool_calls", "retry"}, "runtime"),
                    (raw.get("runtime", {}).get("retry", {}), {"attempts", "tools"}, "runtime.retry"),
                    (raw.get("approval", {}), {"tools"}, "approval")]
        for mapping, allowed, section in sections:
            unknown = set(mapping) - allowed
            if unknown:
                raise ValueError(f"{section} 未接通的配置项：{', '.join(sorted(map(str, unknown)))}")
        result["description"] = spec.description
        result["model"].update(provider=spec.provider, name=spec.model)
        result["configuration"] = _check("PASS", "已通过与 load_spec 共用的配置检查")
        digest = hashlib.sha256()
        for filename in ("agent.yaml", "instructions.md", "tools.py", "services.py", "base_instructions.md"):
            if filename in contents:
                digest.update(filename.encode() + b"\0" + contents[filename].encode("utf-8") + b"\0")
        result["source_version"] = digest.hexdigest()
        if ("A new business agent - update this description." in spec.description
                or "Replace this with a *specific* task" in contents["instructions.md"]):
            result["build"] = _check("FAIL", "仍有模板说明，尚未完成搭建")
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        result["configuration"] = _check("FAIL", str(exc))
        return result
    try:
        functions = set()
        if spec.tools:
            if "tools.py" not in contents:
                raise FileNotFoundError("Missing tools.py")
            tree = ast.parse(contents["tools.py"])
            functions = {node.name for node in tree.body
                         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        missing = [entry for entry in spec.tools if entry.rsplit(":", 1)[1] not in functions]
        if missing:
            raise ValueError("工具函数不存在：" + ", ".join(missing))
        result["tools"] = _check("PASS", "工具源码可解析、注册函数存在；未导入、未执行，Schema/权限运行效果未验证")
    except (OSError, SyntaxError, ValueError) as exc:
        result["tools"] = _check("FAIL", str(exc))
    return result


def agent_catalog() -> list[dict]:
    return [inspect_agent(name) for name in list_agents()]
