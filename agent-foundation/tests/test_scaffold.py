import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
import unittest

from foundation import scaffold as scaffold_module


class ScaffoldTests(unittest.TestCase):
    def test_scaffold_generates_replacements_and_no_overwrite(self):
        source_template = Path(scaffold_module.__file__).resolve().parents[1] / "agents" / "_template"
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            shutil.copytree(source_template, base / "_template", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            with patch.object(scaffold_module, "AGENTS_ROOT", base), patch.object(
                scaffold_module, "get_agent_folder", lambda name: base / name
            ):
                folder = scaffold_module.scaffold("my_new_agent")
                self.assertIn("my_new_agent", (folder / "agent.yaml").read_text())
                self.assertNotIn("__AGENT_NAME__", (folder / "tools.py").read_text())
                with self.assertRaises(FileExistsError):
                    scaffold_module.scaffold("my_new_agent")


if __name__ == "__main__":
    unittest.main()
