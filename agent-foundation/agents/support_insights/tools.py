"""Tool interface that the model can see. Small wrappers around tested services."""
from __future__ import annotations
import json
from langchain.tools import tool
from .services import ticket_stats, ticket_examples, create_local_draft


@tool
def get_ticket_stats(days: int) -> str:
    """Get exact counts of support tickets grouped by category for the last N days (1..365)."""
    return json.dumps(ticket_stats(days), ensure_ascii=False)


@tool
def get_ticket_examples(category: str, days: int = 7) -> str:
    """Retrieve up to three supporting ticket records for a known category and date window."""
    return json.dumps(ticket_examples(category, days), ensure_ascii=False)


@tool
def create_jira_draft(title: str, description: str, priority: str) -> str:
    """Create a LOCAL Jira-style draft. This does NOT submit to the Jira API. Human approval required."""
    return json.dumps(create_local_draft(title, description, priority), ensure_ascii=False)
