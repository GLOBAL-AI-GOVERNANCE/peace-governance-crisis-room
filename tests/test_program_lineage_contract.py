import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LineageContract(unittest.TestCase):
    def test_current_identity(self):
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        publish = (ROOT / 'scripts' / 'publish_to_github.sh').read_text(encoding='utf-8')
        self.assertIn('Peace OS: Crisis Room', readme)
        self.assertIn('Peace OS is the product name. This project is not a computer operating system.', readme)
        self.assertIn('GLOBAL-AI-GOVERNANCE/peace-os-crisis-room', publish)

    def test_lean_public_verification_record(self):
        self.assertTrue((ROOT / 'VERIFICATION.md').is_file())
        self.assertTrue((ROOT / 'docs/audit/v0.2.1-public-scoring-audit-summary.md').is_file())
        for removed in (
            'docs/audit/internal-candidate-corrective-history.md',
            'docs/audit/v0.3.0-rc1-final-publication-hardening.md',
            'docs/audit/v0.3.0-rc1-integrated-vv.md',
            'docs/maintainers/release',
            'SBOM.spdx.json',
        ):
            self.assertFalse((ROOT / removed).exists(), removed)

    def test_historical_identity_is_bounded(self):
        self.assertIn('Peace Governance Crisis Room', (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8'))
        self.assertIn('historical', (ROOT / 'docs/architecture/ADR-001-canonical-identity.md').read_text(encoding='utf-8').lower())

    def test_future_build_names_use_current_identity(self):
        for rel in ('builds/README.md', 'builds/windows/README.md'):
            value = (ROOT / rel).read_text(encoding='utf-8')
            self.assertIn('Peace_OS_Crisis_Room', value)
            stale = 'Peace_' + 'Governance_Crisis_Room'
            self.assertNotIn(stale, value)

    def test_private_material_absent(self):
        manifest = json.loads((ROOT / 'MANIFEST.json').read_text(encoding='utf-8'))
        controlled_paths = [entry['path'] for entry in manifest['files']]
        self.assertFalse(any(path.lower().endswith('.zip') for path in controlled_paths))


if __name__ == '__main__':
    unittest.main()
