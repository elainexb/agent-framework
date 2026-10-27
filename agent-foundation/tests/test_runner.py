from types import SimpleNamespace
from unittest.mock import patch
import sys
import types
import unittest

from foundation.runner import _show_approval


class RunnerTests(unittest.TestCase):
    def test_explicit_human_approval_and_reject(self):
        interruption = [SimpleNamespace(value={"action_requests": [
            {"name": "write_external_data", "args": {"value": "demo"}}
        ]})]
        with patch("builtins.print"):
            self.assertEqual(_show_approval(interruption, lambda _: "n"),
                             {"decisions": [{"type": "reject", "message": "Human reviewer declined this action."}]})
            self.assertEqual(_show_approval(interruption, lambda _: "y"),
                             {"decisions": [{"type": "approve"}]})


if __name__ == "__main__":
    unittest.main()
