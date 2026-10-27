import unittest
from foundation.config import load_spec, list_agents, valid_name
from foundation.evaluation import load_cases, score_case


class ConfigTests(unittest.TestCase):
    def test_agent_specs_load(self):
        self.assertEqual(set(list_agents()), {"support_insights", "knowledge_helper"})
        support = load_spec("support_insights")
        self.assertEqual(support.approval_tools, ("create_jira_draft",))
        self.assertIn("get_ticket_stats", " ".join(support.tools))
        self.assertIn("Never reveal secrets", support.instructions)
        self.assertEqual(len(load_cases(support)), 1)

    def test_name_rejects_traversal(self):
        for name in ("../bad", "Bad", "foo-bar", "_template", "hello/world", ""):
            self.assertFalse(valid_name(name))

    def test_eval_score(self):
        class FakeMessage:
            def __init__(self, calls, content):
                self.tool_calls = [{"name": name} for name in calls]
                self.content = content
        result = score_case({"expected_tools": ["lookup"], "answer_contains_any": ["success"]},
                            [FakeMessage(["lookup"], ""), FakeMessage([], "SUCCESS")])
        self.assertTrue(result["passed"])
        result2 = score_case({"expected_tools": ["lookup"], "answer_contains_any": ["success"]},
                             [FakeMessage([], "success")])
        self.assertFalse(result2["passed"])


if __name__ == "__main__":
    unittest.main()
