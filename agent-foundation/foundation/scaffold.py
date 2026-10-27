"""Create a new agent from the reusable template, without changing the runtime."""
from __future__ import annotations
from pathlib import Path
import shutil
from .config import AGENTS_ROOT, get_agent_folder


def scaffold(name: str) -> Path:
    dest = get_agent_folder(name)
    if dest.exists():
        raise FileExistsError(f"Agent already exists: {name}; refusing overwrite")
    template = AGENTS_ROOT / "_template"
    if not template.is_dir():
        raise FileNotFoundError("Agent template is missing")
    shutil.copytree(template, dest)
    try:
        for path in dest.rglob("*"):
            if path.is_file() and path.suffix in {".md", ".yaml", ".py", ".json"}:
                s = path.read_text(encoding="utf-8").replace("__AGENT_NAME__", name)
                path.write_text(s, encoding="utf-8")
    except Exception:
        shutil.rmtree(dest)
        raise
    return dest
