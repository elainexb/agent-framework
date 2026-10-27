import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from foundation import config, scaffold
from foundation.cli import main


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(config.AGENTS_ROOT / "_template", self.root / "_template",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for module in (config, scaffold):
            patcher = patch.object(module, "AGENTS_ROOT", self.root)
            patcher.start()
            self.addCleanup(patcher.stop)

    def inspect(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["inspect", "catalog_example"])
        return code, json.loads(output.getvalue())

    def test_new_and_modified_agent_share_inspection_without_overwriting(self):
        folder = scaffold.scaffold("catalog_example")
        code, draft = self.inspect()
        self.assertEqual(code, 0)
        self.assertEqual(draft["configuration"]["status"], "PASS")
        self.assertEqual(draft["build"]["status"], "FAIL")
        self.assertEqual(draft["model"]["status"], "UNKNOWN")
        with self.assertRaises(FileExistsError):
            scaffold.scaffold("catalog_example")
        original_tools = (folder / "tools.py").read_bytes()
        (folder / "instructions.md").write_text(
            "Answer reference questions using sample_lookup. Cite returned evidence; "
            "ask for clarification if evidence is missing.\n")
        yaml_path = folder / "agent.yaml"
        yaml_path.write_text(yaml_path.read_text().replace(
            "A new business agent - update this description.", "Reference lookup example."))
        code, modified = self.inspect()
        self.assertEqual(code, 0)
        self.assertEqual(modified["build"]["status"], "UNKNOWN")
        self.assertEqual(modified["model"]["status"], "UNKNOWN")
        self.assertFalse(modified["can_run"])
        self.assertNotEqual(draft["source_version"], modified["source_version"])
        self.assertEqual(modified["model"]["name"], "qwen3:4b")
        self.assertEqual((folder / "tools.py").read_bytes(), original_tools)

    def test_unintegrated_capability_is_reported_instead_of_silently_ignored(self):
        folder = scaffold.scaffold("catalog_example")
        with (folder / "agent.yaml").open("a") as stream:
            stream.write("memory:\n  enabled: true\n")
        code, report = self.inspect()
        self.assertEqual(code, 2)
        self.assertEqual(report["configuration"]["status"], "FAIL")
        self.assertIn("memory", report["configuration"]["detail"])
        self.assertFalse(report["can_run"])

    def test_missing_tool_and_invalid_config_are_failures_without_importing_tools(self):
        folder = scaffold.scaffold("catalog_example")
        marker = self.root / "unexpected-import"
        (folder / "tools.py").write_text(
            f"from pathlib import Path\nPath({str(marker)!r}).touch()\n"
            "def another_tool(query: str):\n    return query\n")
        code, missing = self.inspect()
        self.assertEqual(code, 2)
        self.assertEqual(missing["tools"]["status"], "FAIL")
        self.assertIn("sample_lookup", missing["tools"]["detail"])
        self.assertFalse(marker.exists())
        (folder / "agent.yaml").write_text("name: catalog_example\nmodel: [invalid]\n")
        code, invalid = self.inspect()
        self.assertEqual(code, 2)
        self.assertEqual(invalid["configuration"]["status"], "FAIL")
        self.assertFalse(marker.exists())

    def test_inspection_uses_one_validated_snapshot_when_config_changes_during_read(self):
        folder = scaffold.scaffold("catalog_example")
        _, original = self.inspect()
        config_path = folder / "agent.yaml"
        read_text = Path.read_text
        changed = False

        def read_then_save(path, *args, **kwargs):
            nonlocal changed
            value = read_text(path, *args, **kwargs)
            if path == config_path and not changed:
                changed = True
                config_path.write_text("name: catalog_example\n")
            return value

        with patch.object(Path, "read_text", read_then_save):
            code, snapshot = self.inspect()
        self.assertEqual(code, 0)
        self.assertEqual(snapshot["model"]["name"], "qwen3:4b")
        self.assertEqual(snapshot["source_version"], original["source_version"])
        code, next_reload = self.inspect()
        self.assertEqual(code, 2)
        self.assertEqual(next_reload["configuration"]["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
