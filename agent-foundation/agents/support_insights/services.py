"""Pure(ish) business layer, kept independent of the LLM and LangChain.

In production, replace read_tickets with a Zendesk/Salesforce/DB adapter.
"""
from __future__ import annotations
from collections import Counter
import csv
from datetime import date, timedelta
import json
from pathlib import Path
import uuid

DATA_DIR = Path(__file__).resolve().parent / "data"
CSV_PATH = DATA_DIR / "tickets.csv"


def seed_demo_data(*, today: date | None = None, path: Path = CSV_PATH, force: bool = False) -> Path:
    """Generate synthetic dated tickets. Never silently replace existing data."""
    if path.exists() and not force:
        return path
    today = today or date.today()
    rows = [
        ("T101", 0, "Login", "SSO login fails for enterprise tenant"),
        ("T102", 1, "Login", "Cannot log in after password reset"),
        ("T103", 1, "Billing", "Invoice total seems incorrect"),
        ("T104", 2, "Login", "Login loops to authentication page"),
        ("T105", 2, "Performance", "Dashboard takes 25 seconds to load"),
        ("T106", 3, "Login", "Sign-in unavailable on mobile app"),
        ("T107", 3, "Billing", "Duplicate charge in payment history"),
        ("T108", 4, "Login", "Cannot log in after a session expires"),
        ("T109", 4, "Performance", "Report page is too slow"),
        ("T110", 5, "Billing", "Incorrect plan on invoice"),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["ticket_id", "created_at", "category", "description"])
        writer.writeheader()
        for ticket_id, ago, category, description in rows:
            writer.writerow({"ticket_id": ticket_id,
                             "created_at": (today - timedelta(days=ago)).isoformat(),
                             "category": category, "description": description})
    return path


def read_tickets(days: int, *, today: date | None = None, path: Path = CSV_PATH) -> list[dict[str, str]]:
    if not 1 <= days <= 365:
        raise ValueError("days must be between 1 and 365")
    today = today or date.today()
    if not path.exists():
        raise FileNotFoundError("Missing dataset. Run: python -m foundation.cli seed support_insights")
    first_date = today - timedelta(days=days - 1)
    with path.open(encoding="utf-8", newline="") as f:
        data = list(csv.DictReader(f))
    # Do not count future dated tickets or past tickets outside the window.
    return [t for t in data if first_date <= date.fromisoformat(t["created_at"]) <= today]


def ticket_stats(days: int, *, today: date | None = None, path: Path = CSV_PATH) -> dict:
    rows = read_tickets(days, today=today, path=path)
    counts = Counter(r["category"] for r in rows)
    sorted_counts = dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))
    return {"days": days, "total": len(rows), "by_category": sorted_counts,
            "top_category": next(iter(sorted_counts), None)}


def ticket_examples(category: str, days: int = 7, *, today: date | None = None,
                    path: Path = CSV_PATH, limit: int = 3) -> list[dict[str, str]]:
    if not category.strip() or not 1 <= limit <= 10:
        raise ValueError("Provide nonempty category and limit between 1 and 10")
    rows = read_tickets(days, today=today, path=path)
    return [r for r in rows if r["category"].casefold() == category.casefold()][:limit]


def create_local_draft(title: str, description: str, priority: str,
                       *, directory: Path | None = None) -> dict[str, str]:
    """Local file only. DOES NOT touch Jira or any remote network service."""
    if not title.strip() or not description.strip():
        raise ValueError("Title and description are required")
    if priority not in {"Low", "Medium", "High", "Highest"}:
        raise ValueError("priority must be Low, Medium, High, or Highest")
    directory = directory or DATA_DIR / "drafts"
    directory.mkdir(parents=True, exist_ok=True)
    draft_id = "DRAFT-" + uuid.uuid4().hex[:10].upper()
    payload = {"draft_id": draft_id, "title": title[:160],
               "description": description[:5000], "priority": priority,
               "status": "DRAFT_NOT_SUBMITTED"}
    (directory / f"{draft_id}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"draft_id": draft_id, "status": payload["status"]}
