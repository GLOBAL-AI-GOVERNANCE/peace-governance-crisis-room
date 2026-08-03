import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WebCoreContract(unittest.TestCase):
    def test_web_files(self):
        for rel in (
            'web/index.html',
            'web/app.js',
            'web/frame-guard.js',
            'web/scoring.js',
            'web/styles.css',
            'web/manifest.webmanifest',
        ):
            self.assertTrue((ROOT / rel).is_file(), rel)

    def test_two_scenarios(self):
        index = json.loads((ROOT / 'core/scenarios/index.json').read_text(encoding='utf-8'))
        self.assertEqual(len(index['scenarios']), 2)

    def test_local_only_policy(self):
        policy = json.loads((ROOT / 'core/governance/policy.json').read_text(encoding='utf-8'))
        self.assertFalse(policy['allow_live_data'])
        self.assertFalse(policy['allow_telemetry'])
        self.assertFalse(policy['allow_external_ai'])

    def test_five_positive_indicators(self):
        rubric = json.loads((ROOT / 'core/scoring/scoring_rubric.json').read_text(encoding='utf-8'))
        self.assertEqual(len(rubric['public_indicators']), 5)
        self.assertEqual(set(rubric['scenario_state']), {'public_pressure'})


if __name__ == '__main__':
    unittest.main()
