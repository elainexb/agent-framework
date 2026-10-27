from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from foundation import config, scaffold


class CatalogPageTests(unittest.TestCase):
    def test_page_reload_discovers_new_agent_and_reads_modified_definition(self):
        from foundation.web import catalog_view

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(config.AGENTS_ROOT / "_template", root / "_template",
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            with patch.object(config, "AGENTS_ROOT", root), patch.object(scaffold, "AGENTS_ROOT", root):
                empty = catalog_view(None)
                self.assertEqual(empty["choices"], [])
                self.assertIsNone(empty["report"])
                folder = scaffold.scaffold("page_example")
                first = catalog_view("page_example")
                self.assertEqual(first["choices"], ["page_example"])
                self.assertEqual(first["report"]["name"], "page_example")
                self.assertFalse(first["report"]["can_run"])
                path = folder / "instructions.md"
                path.write_text(path.read_text() + "\nAsk for clarification when evidence is missing.\n")
                modified = catalog_view("page_example")
                self.assertNotEqual(first["report"]["source_version"], modified["report"]["source_version"])
                self.assertEqual(modified["report"]["model"]["status"], "UNKNOWN")
                (folder / "agent.yaml").write_text("model: broken\n")
                broken = catalog_view("page_example")
                self.assertEqual(broken["report"]["configuration"]["status"], "FAIL")
                shutil.rmtree(folder)
                removed = catalog_view("page_example")
                self.assertIsNone(removed["selected"])
                self.assertIsNone(removed["report"])


if __name__ == "__main__":
    unittest.main()
