"""Expose deliberately small functions with typed parameters and precise docstrings."""
import json
from langchain.tools import tool
from .services import sample_lookup as lookup_service


@tool
def sample_lookup(query: str) -> str:
    """Look up business facts for a text query (placeholder; replace implementation)."""
    return json.dumps(lookup_service(query), ensure_ascii=False)
