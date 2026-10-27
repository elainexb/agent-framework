"""Model-visible tool declarations for the knowledge helper."""
import json
from langchain.tools import tool
from .services import search, read_section as lookup_section


@tool
def search_knowledge(query: str) -> str:
    """Search a local reference handbook and return matching sections with document citations."""
    return json.dumps(search(query), ensure_ascii=False)


@tool
def read_section(section: str) -> str:
    """Read a complete handbook section by exact section heading returned by search_knowledge."""
    return json.dumps(lookup_section(section), ensure_ascii=False)
