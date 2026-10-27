"""Mechanical CLI contract and honest scope reporting, not full governance acceptance.

Original whole-requirement gap probes are frozen in evidence/test_document_contract-v1.py.
The overall semantic/acceptance gap stays open in behavior-cases.json.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


GUARD = Path(__file__).resolve().parents[1] / 'md-governance-20261026/trial/doc_guard.py'


class DocumentContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.index = self.root / 'CODEX_START_HERE.md'
        self.index.write_text(
            '# 入口\n\n<!-- doc-governance:v1 -->\n\n'
            '| Topic | Category | Source |\n|---|---|---|\n'
            '| task | 工作 | [任务](task.md) |\n', encoding='utf-8')
        self.task = self.root / 'task.md'
        self.task.write_text('# 当前任务\n\n## 已确认约束\n\n'
                             '历史材料只在追溯或恢复时读取。\n', encoding='utf-8')

    def check(self):
        result = subprocess.run(
            [sys.executable, '-B', str(GUARD), 'check', '--root', str(self.root)],
            text=True, capture_output=True, timeout=10)
        self.assertIn(result.returncode, (0, 1), result.stderr + result.stdout)
        return result.returncode, json.loads(result.stdout)

    def test_C01_valid_indexed_document_is_accepted_without_semantic_certification(self):
        code, report = self.check()
        self.assertEqual(code, 0)
        self.assertEqual(report['mechanical_status'], 'PASS')
        self.assertTrue(report['semantic_status'].startswith('UNKNOWN'))

    def test_C02_new_unindexed_document_is_rejected(self):
        (self.root / 'new.md').write_text('# 新说明\n', encoding='utf-8')
        code, report = self.check()
        self.assertEqual(code, 1)
        self.assertIn('UNINDEXED', {x['code'] for x in report['findings']})

    def test_C03_declared_source_change_requires_recheck(self):
        source = self.root / 'settings.py'
        source.write_text('LIMIT = 10\n', encoding='utf-8')
        reviewed = hashlib.sha256(source.read_bytes()).hexdigest()
        with self.index.open('a', encoding='utf-8') as handle:
            handle.write('\n| Topic | Dependency | Reviewed SHA256 |\n|---|---|---|\n'
                         f'| task | settings.py | {reviewed} |\n')
        self.assertEqual(self.check()[0], 0)
        source.write_text('LIMIT = 20\n', encoding='utf-8')
        code, report = self.check()
        self.assertEqual(code, 1)
        self.assertIn('DEPENDENCY_CHANGED', {x['code'] for x in report['findings']})

    def test_M04_paraphrased_duplicate_is_not_certified_by_mechanical_pass(self):
        # Constructed fault based on the user's single-authority requirement.
        (self.root / 'guide.md').write_text(
            '# 使用指南\n\n只有需要回溯原因或者恢复现场，才打开历史资料。\n', encoding='utf-8')
        with self.index.open('a', encoding='utf-8') as handle:
            handle.write('| guide | 操作 | [指南](guide.md) |\n')
        code, report = self.check()
        self.assertEqual(code, 0)
        self.assertEqual(report['mechanical_status'], 'PASS')
        self.assertEqual(report['semantic_status'], 'UNKNOWN')

    def test_M05_appended_contradiction_is_not_certified_by_mechanical_pass(self):
        with self.task.open('a', encoding='utf-8') as handle:
            handle.write('\n## 本轮补充\n\n每次开始任务，都必须先读取全部历史材料。\n')
        code, report = self.check()
        self.assertEqual(code, 0)
        self.assertEqual(report['mechanical_status'], 'PASS')
        self.assertEqual(report['semantic_status'], 'UNKNOWN')

    def test_M06_code_fact_cache_is_not_certified_by_mechanical_pass(self):
        (self.root / 'settings.py').write_text('LIMIT = 10\n', encoding='utf-8')
        with self.task.open('a', encoding='utf-8') as handle:
            handle.write('\n## 配置副本\n\nsettings.py中LIMIT的当前默认值为10。\n')
        code, report = self.check()
        self.assertEqual(code, 0)
        self.assertEqual(report['mechanical_status'], 'PASS')
        self.assertEqual(report['semantic_status'], 'UNKNOWN')


if __name__ == '__main__':
    print('MECHANICAL SCOPE ONLY: semantic governance and actual acceptance are not certified.', flush=True)
    unittest.main(verbosity=2)
