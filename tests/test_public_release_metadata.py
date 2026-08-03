import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PublicReleaseMetadataTests(unittest.TestCase):
    def test_citation_has_required_author(self):
        text=(ROOT/'CITATION.cff').read_text(encoding='utf-8')
        self.assertIn('authors:', text)
        self.assertIn('- name: "Global AI Governance contributors"', text)

    def test_release_sbom_has_single_source_of_truth(self):
        self.assertFalse((ROOT/'SBOM.spdx.json').exists())
        build=(ROOT/'tools/build_release.py').read_text(encoding='utf-8')
        self.assertIn("-SBOM.spdx.json", build)
        self.assertIn("'spdxVersion': 'SPDX-2.3'", build)

    def test_current_verification_matrix_is_linked(self):
        readme=(ROOT/'README.md').read_text(encoding='utf-8')
        self.assertIn('[Verification status](VERIFICATION.md)', readme)
        self.assertIn('Deployed GitHub Pages browser validation', (ROOT/'VERIFICATION.md').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
