"""Test our HITL driver contract without any downloaded provider or SDK package."""
from types import ModuleType, SimpleNamespace
from unittest.mock import patch
import sys
import unittest
from foundation.runner import run_turn


class FakeCommand:
    def __init__(self, resume):
        self.resume = resume


class FakeGraph:
    def __init__(self):
        self.calls = []

    def invoke(self, data, config, version):
        self.calls.append((data, config, version))
        if len(self.calls) == 1:
            return SimpleNamespace(interrupts=(SimpleNamespace(value={"action_requests": [
                {"name": "create_jira_draft", "args": {"title": "test"}}
            ]}),), value=None)
        return SimpleNamespace(interrupts=(), value={"messages": [SimpleNamespace(
            type="ai", content="Human decision acknowledged", tool_calls=[])]})


class RunnerV2Tests(unittest.TestCase):
    def test_resume_thread_and_reject(self):
        lg = ModuleType("langgraph")
        types = ModuleType("langgraph.types")
        types.Command = FakeCommand
        with patch.dict(sys.modules, {"langgraph": lg, "langgraph.types": types}), patch("builtins.print"):
            fake = FakeGraph()
            result = run_turn(fake, "make draft", thread_id="unit-thread", input_fn=lambda _: "n")
        self.assertEqual(result, "Human decision acknowledged")
        self.assertEqual(len(fake.calls), 2)
        self.assertEqual(fake.calls[0][2], "v2")
        self.assertEqual(fake.calls[0][1], fake.calls[1][1])
        self.assertEqual(fake.calls[1][0].resume["decisions"][0]["type"], "reject")


if __name__ == "__main__":
    unittest.main()
