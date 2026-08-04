import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Rc2DeploymentContractTests(unittest.TestCase):
    def setUp(self):
        self.workflow = (ROOT / '.github/workflows/pages.yml').read_text(encoding='utf-8')
        self.uat = (ROOT / 'tests/deployed_browser_uat.mjs').read_text(encoding='utf-8')

    def test_pages_runs_uat_after_exact_deploy(self):
        self.assertIn('deployed-browser-uat:', self.workflow)
        self.assertLess(self.workflow.index('\n  deploy:'), self.workflow.index('\n  deployed-browser-uat:'))
        self.assertIn('needs: deploy', self.workflow)
        self.assertIn('EXPECTED_COMMIT: ${{ github.sha }}', self.workflow)
        self.assertIn('web/deployment.json', self.workflow)
        self.assertIn('tools/verify_deployed_uat.py', self.workflow)
        self.assertIn('actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02', self.workflow)

    def test_deployed_uat_binds_metadata_and_checks_output(self):
        for marker in (
            'waitForDeploymentMetadata(options.baseUrl, options.expectedCommit)',
            "metadata?.commit === expectedCommit.toLowerCase()",
            'downloaded_aar_contract',
            'print_sections_complete',
            'unexpected_network_requests',
            'console_errors',
        ):
            self.assertIn(marker, self.uat)

    def test_browser_profile_cleanup_is_process_group_aware_and_bounded(self):
        for marker in (
            "const detached = process.platform !== 'win32';",
            'const processGroupId = detached ? child.pid : null;',
            'process.kill(-processGroupId, 0)',
            'process.kill(-processGroupId, signal)',
            "signalBrowserTree('SIGTERM')",
            "signalBrowserTree('SIGKILL')",
            'await waitForBrowserTreeExit(3000)',
            'maxRetries: 10',
            'retryDelay: 250',
            "['ENOTEMPTY', 'EBUSY', 'EPERM'].includes(code)",
            'Browser profile cleanup deferred after verified browser shutdown',
        ):
            self.assertIn(marker, self.uat)
    def test_deployed_uat_score_expectation_matches_timed_browser_journey(self):
        for marker in (
            'function expectedBrowserJourneyScore(scenario)',
            'const timedEvents = scenario.evidence_cards.length + 2;',
            'return 95 + timeliness;',
            'const expectedScore = expectedBrowserJourneyScore(scenario);',
            'expected browser-journey score',
        ):
            self.assertIn(marker, self.uat)
        self.assertNotIn('expected score 100', self.uat)

    def test_deployed_uat_verifier_fails_closed(self):
        commit = 'a' * 40
        record = {
            'status': 'PASS',
            'expected_commit': commit,
            'base_url': 'https://example.test/site/',
            'deployment_metadata': {
                'repository': 'GLOBAL-AI-GOVERNANCE/peace-os-crisis-room',
                'commit': commit,
            },
            'console_errors': [],
            'unexpected_network_requests': [],
            'journeys': [{'status': 'PASS'}],
            'control_checks': {'contract': True},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'uat.json'
            path.write_text(json.dumps(record), encoding='utf-8')
            command = [
                sys.executable, str(ROOT / 'tools/verify_deployed_uat.py'),
                '--input', str(path), '--expected-commit', commit,
                '--expected-url', 'https://example.test/site/',
            ]
            self.assertEqual(subprocess.run(command, cwd=ROOT, capture_output=True).returncode, 0)
            record['console_errors'] = ['boom']
            path.write_text(json.dumps(record), encoding='utf-8')
            self.assertNotEqual(subprocess.run(command, cwd=ROOT, capture_output=True).returncode, 0)


if __name__ == '__main__':
    unittest.main()
