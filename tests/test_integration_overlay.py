from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'tools' / 'prepare_integration_overlay.py'


class IntegrationOverlayTests(unittest.TestCase):
    def test_plan_and_apply_without_rsync(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / 'source'
            target = base / 'target'
            source.mkdir()
            target.mkdir()
            (target / '.git').mkdir()
            (target / '.git' / 'config').write_text('preserve', encoding='utf-8')
            (source / 'same.txt').write_text('same\n', encoding='utf-8')
            (target / 'same.txt').write_text('same\n', encoding='utf-8')
            (source / 'modify.txt').write_text('new\n', encoding='utf-8')
            (target / 'modify.txt').write_text('old\n', encoding='utf-8')
            (source / 'add.txt').write_text('add\n', encoding='utf-8')
            (target / 'delete.txt').write_text('delete\n', encoding='utf-8')
            (source / 'dist-a').mkdir()
            (source / 'dist-a' / 'ignored.txt').write_text('ignored\n', encoding='utf-8')
            plan = base / 'plan.txt'
            deletions = base / 'deletions.txt'

            command = [
                'python3', str(TOOL), '--source', str(source), '--target', str(target),
                '--plan', str(plan), '--deletions', str(deletions), '--apply',
            ]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            text = plan.read_text(encoding='utf-8')
            self.assertIn('SAME\tsame.txt', text)
            self.assertIn('MODIFY\tmodify.txt', text)
            self.assertIn('ADD\tadd.txt', text)
            self.assertIn('DELETE\tdelete.txt', text)
            self.assertEqual(deletions.read_text(encoding='utf-8'), 'delete.txt\n')
            self.assertEqual((target / 'modify.txt').read_text(encoding='utf-8'), 'new\n')
            self.assertEqual((target / 'add.txt').read_text(encoding='utf-8'), 'add\n')
            self.assertFalse((target / 'delete.txt').exists())
            self.assertFalse((target / 'dist-a').exists())
            self.assertEqual((target / '.git' / 'config').read_text(encoding='utf-8'), 'preserve')

    def test_refuses_same_source_and_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = subprocess.run(
                [
                    'python3', str(TOOL), '--source', str(root), '--target', str(root),
                    '--plan', str(root / 'plan.txt'), '--deletions', str(root / 'deletions.txt'),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('source and target must be different', result.stderr + result.stdout)


if __name__ == '__main__':
    unittest.main()
