from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

from agents.support_insights.services import seed_demo_data, ticket_stats, ticket_examples, create_local_draft
from agents.knowledge_helper.services import search, read_section


class ServiceTests(unittest.TestCase):
    def test_support_stats_are_exact(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "tickets.csv"
            today = date(2026, 10, 24)
            seed_demo_data(today=today, path=path)
            r = ticket_stats(7, today=today, path=path)
            self.assertEqual(r["total"], 10)
            self.assertEqual(r["by_category"], {"Login": 5, "Billing": 3, "Performance": 2})
            self.assertEqual(r["top_category"], "Login")
            self.assertEqual(len(ticket_examples("Login", 7, today=today, path=path)), 3)

    def test_bad_window_rejected(self):
        with self.assertRaises(ValueError):
            ticket_stats(0)

    def test_draft_not_submitted(self):
        with tempfile.TemporaryDirectory() as d:
            result = create_local_draft("Fix login", "Evidence: T101", "High", directory=Path(d))
            self.assertEqual(result["status"], "DRAFT_NOT_SUBMITTED")
            file = Path(d) / (result["draft_id"] + ".json")
            self.assertTrue(file.exists())
            self.assertEqual(json.loads(file.read_text())["priority"], "High")

    def test_knowledge_search_citation(self):
        rows = search("P0 outage")
        self.assertTrue(rows)
        self.assertEqual(rows[0]["document"], "handbook.md")
        self.assertEqual(rows[0]["section"], "Severity")
        self.assertIn("incident commander", read_section("Severity")["content"])


if __name__ == "__main__":
    unittest.main()
