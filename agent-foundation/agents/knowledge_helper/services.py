"""Baseline lexical search; replace this module with a vector store adapter later."""
from __future__ import annotations
from pathlib import Path
import re

HANDBOOK = Path(__file__).resolve().parent / "data" / "handbook.md"


def sections(path: Path = HANDBOOK) -> dict[str, str]:
    content = path.read_text(encoding="utf-8")
    result: dict[str, str] = {}
    heading = None
    lines: list[str] = []
    for line in content.splitlines():
        if line.startswith("## "):
            if heading is not None:
                result[heading] = "\n".join(lines).strip()
            heading = line[3:].strip()
            lines = []
        elif heading is not None:
            lines.append(line)
    if heading is not None:
        result[heading] = "\n".join(lines).strip()
    return result


def search(query: str, *, path: Path = HANDBOOK, limit: int = 3) -> list[dict]:
    if not query.strip():
        raise ValueError("Query cannot be empty")
    terms = re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]", query.lower())
    matches = []
    for heading, content in sections(path).items():
        text = (heading + " " + content).lower()
        score = sum(text.count(t) for t in terms)
        if score:
            matches.append({"document": path.name, "section": heading,
                            "snippet": content[:500], "score": score})
    return sorted(matches, key=lambda r: -r["score"])[:limit]


def read_section(section: str, *, path: Path = HANDBOOK) -> dict:
    data = sections(path)
    for heading, body in data.items():
        if heading.casefold() == section.casefold():
            return {"document": path.name, "section": heading, "content": body}
    return {"error": "SECTION_NOT_FOUND", "available_sections": list(data)}
