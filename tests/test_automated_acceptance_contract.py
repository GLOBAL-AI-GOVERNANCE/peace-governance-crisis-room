from pathlib import Path
import json
import subprocess
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'tools' / 'run_automated_acceptance.py'
BROWSER = ROOT / 'tests' / 'deployed_browser_uat.mjs'


class AutomatedAcceptanceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = TOOL.read_text(encoding='utf-8')
        cls.browser = BROWSER.read_text(encoding='utf-8')

    def test_acceptance_does_not_redefine_human_uat(self) -> None:
        self.assertIn('automated_acceptance_validation', self.text)
        self.assertIn('human_uat_status', self.text)
        self.assertNotIn('UAT means', self.text)
        self.assertIn('not human user acceptance testing', self.text)

    def test_acceptance_checks_source_assets_and_browser_journeys(self) -> None:
        for fragment in (
            'tools/validate_repository.py',
            'tools/generate_manifest.py',
            'Avoid',
            'duplicate local-server checks',
            'deployment_asset_checks',
            'unexpected_external_references',
            'tests/deployed_browser_uat.mjs',
            'expected-commit',
        ):
            self.assertIn(fragment, self.text)

    def test_browser_harness_covers_required_journeys_and_failures(self) -> None:
        for fragment in (
            'scenario_01_viral_collision_video',
            'scenario_02_deepfake_distress_call',
            "'practice'",
            "'assessment'",
            "'facilitator'",
            'confirmation_invalidated_after_change',
            'clipboard_denial_fallback',
            'download_invocation',
            'download_denial_fallback',
            'print_invocation',
            'resume_committed_result',
            'delete_saved_session',
            'corrupted_session_recovery',
            'const widths = [320, 360, 375, 390, 414]',
            'mobile_width_matrix',
            'zoom_200_no_global_overflow',
            'storage_denied_memory_only',
            'skip_link_first_tab',
            'unexpected_network_requests',
        ):
            self.assertIn(fragment, self.browser)

    def test_browser_harness_is_dependency_free_and_requires_node_22(self) -> None:
        self.assertIn('Node.js 22 or newer is required', self.browser)
        self.assertIn('new WebSocket', self.browser)
        self.assertNotIn("from 'playwright'", self.browser)
        self.assertNotIn("from 'puppeteer'", self.browser)
        self.assertIn('existsSync', self.browser)
        self.assertIn('Timed out waiting for DevTools response', self.browser)
        self.assertNotIn("spawnSync(candidate, ['--version']", self.browser)

    def test_source_only_automated_acceptance_executes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_json = Path(directory) / 'acceptance.json'
            output_md = Path(directory) / 'acceptance.md'
            result = subprocess.run(
                [
                    sys.executable, str(TOOL),
                    '--skip-source-checks',
                    '--output-json', str(output_json),
                    '--output-md', str(output_md),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=180,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            record = json.loads(output_json.read_text(encoding='utf-8'))
            self.assertEqual(record['status'], 'PASS')
            self.assertEqual(record['human_uat_status'], 'PENDING_FOR_STABLE')
            self.assertIn('Automated Acceptance Validation', output_md.read_text(encoding='utf-8'))

    def test_node_browser_harness_parses(self) -> None:
        result = subprocess.run(['node', '--check', str(BROWSER)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_subprocess_output_capture_cannot_hang_on_inherited_pipes(self) -> None:
        for fragment in (
            "TemporaryFile(mode='w+'",
            'stdout=stdout_file',
            'stderr=stderr_file',
            'timeout=300',
            "'timed_out': timed_out",
        ):
            self.assertIn(fragment, self.text)
        self.assertNotIn('capture_output=True', self.text)


if __name__ == '__main__':
    unittest.main()
