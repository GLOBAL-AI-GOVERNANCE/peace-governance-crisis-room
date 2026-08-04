from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLISH = ROOT / 'scripts' / 'publish_to_github.sh'
BUILD = ROOT / 'tools' / 'build_release.py'
MANIFEST_TOOL = ROOT / 'tools' / 'generate_manifest.py'
APP = ROOT / 'web' / 'app.js'
BROWSER_SMOKE = ROOT / 'tests' / 'browser_smoke.py'
HTTP_SMOKE = ROOT / 'tests' / 'http_asset_smoke.py'


class ReleaseOperatorContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.publish = PUBLISH.read_text(encoding='utf-8')
        cls.build = BUILD.read_text(encoding='utf-8')
        cls.manifest_tool = MANIFEST_TOOL.read_text(encoding='utf-8')
        cls.app = APP.read_text(encoding='utf-8')
        cls.browser_smoke = BROWSER_SMOKE.read_text(encoding='utf-8')
        cls.http_smoke = HTTP_SMOKE.read_text(encoding='utf-8')

    def test_publication_script_parses(self) -> None:
        result = subprocess.run(['bash', '-n', str(PUBLISH)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_source_root_is_resolved_before_changing_directories(self) -> None:
        script_dir = self.publish.index('SCRIPT_DIR=')
        source_root = self.publish.index('SOURCE_ROOT=')
        clone_cd = self.publish.index('cd "$WORK/repo"')
        self.assertLess(script_dir, source_root)
        self.assertLess(source_root, clone_cd)
        self.assertNotIn('SOURCE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.."', self.publish)

    def test_dry_run_evidence_is_persistent_and_reviewable(self) -> None:
        for fragment in (
            'KEEP_WORKDIR',
            'PUBLISH_REVIEW_DIR',
            'prepare_integration_overlay.py',
            'integration-review.patch',
            'integration-review.stat.txt',
            'integration-review.name-status.txt',
            'deletions-reviewed.txt',
            'overlay-plan.txt',
            'git diff --cached --check',
            'extended-vv-results-v0.3.0-rc2.json',
            'scan_publication_surface.py',
            'git-history-secret-scan.txt',
        ):
            self.assertIn(fragment, self.publish)

    def test_push_requires_explicit_review_acknowledgment(self) -> None:
        self.assertIn('ACKNOWLEDGE_REVIEW', self.publish)
        self.assertIn('ACKNOWLEDGE_DELETIONS', self.publish)
        self.assertIn('remote review branch already exists', self.publish)


    def test_release_inventories_use_cross_platform_posix_ordering(self) -> None:
        self.assertIn(
            "key=lambda item: item.relative_to(ROOT).as_posix()",
            self.manifest_tool,
        )
        self.assertIn(
            "sorted_include = sorted(include, key=lambda relative: relative.as_posix())",
            self.build,
        )
        self.assertNotIn("for path in sorted(ROOT.rglob('*')):", self.manifest_tool)
        self.assertNotIn("for relative in sorted(include):", self.build)

    def test_release_builder_enforces_clean_git_tree(self) -> None:
        self.assertIn('def ensure_clean_git_tree()', self.build)
        self.assertIn("git_output('status', '--porcelain', '--untracked-files=all')", self.build)
        self.assertIn('working tree is not clean', self.build)

    def test_release_timestamp_is_not_hardcoded(self) -> None:
        self.assertIn('--release-timestamp', self.build)
        self.assertIn('SOURCE_DATE_EPOCH', self.build)
        self.assertIn("git_output('show', '-s', '--format=%cI', 'HEAD')", self.build)
        self.assertNotIn("'release_date': '2026-08-03'", self.build)
        self.assertIn("'release_timestamp_utc': timestamp_utc", self.build)
        self.assertIn("-SBOM.spdx.json", self.build)
        self.assertIn("'spdxVersion': 'SPDX-2.3'", self.build)

    def test_release_sbom_is_file_level(self) -> None:
        self.assertIn('sbom_files = []', self.build)
        self.assertIn("'filesAnalyzed': True", self.build)
        self.assertIn("'relationshipType': 'CONTAINS'", self.build)

    def test_python_interpreter_is_resolved_portably(self) -> None:
        self.assertIn('PYTHON="$(command -v python3 || command -v python || true)"', self.publish)
        self.assertNotIn('for command in gh git python node', self.publish)

    def test_push_requires_patch_or_reviewed_workspace(self) -> None:
        self.assertIn('EXPECTED_PATCH_SHA256', self.publish)
        self.assertIn('REVIEWED_WORKSPACE', self.publish)
        self.assertIn('EXPECTED_SOURCE_ZIP_SHA256', self.publish)
        self.assertIn('EXPECTED_GITHUB_LOGIN', self.publish)
        self.assertIn('--push requires EXPECTED_PATCH_SHA256', self.publish)

    def test_exact_reviewed_workspace_push_is_cryptographically_bound(self) -> None:
        for fragment in (
            "--push requires EXPECTED_GITHUB_LOGIN",
            "--push requires EXPECTED_SOURCE_ZIP_SHA256",
            "--push requires EXPECTED_PATCH_SHA256",
            'PARENT_COMMIT="$(git rev-parse HEAD^)"',
            'git diff --binary "$EXPECTED_BASE_COMMIT" HEAD',
            'reviewed workspace commit does not reproduce the approved patch',
            'reviewed workspace is not clean',
            'recorded local review commit',
        ):
            self.assertIn(fragment, self.publish)

    def test_browser_smoke_timeout_cannot_hang_on_descendant_pipes(self) -> None:
        for fragment in (
            "TemporaryFile(mode='w+'",
            "start_new_session=(os.name != 'nt')",
            'os.killpg(process.pid, signal.SIGKILL)',
            'process.wait(timeout=20)',
        ):
            self.assertIn(fragment, self.browser_smoke)
        self.assertNotIn('subprocess.run(cmd,capture_output=True,text=True,timeout=20)', self.browser_smoke)

    def test_http_asset_smoke_stops_cleanly(self) -> None:
        for fragment in (
            "protocol_version = 'HTTP/1.0'",
            'server.handle_request()',
            "headers={'Connection': 'close'",
            'thread.join(timeout=10)',
            "HTTP asset smoke failed to stop its bounded local server cleanly",
        ):
            self.assertIn(fragment, self.http_smoke)

    def test_branch_upload_does_not_depend_on_optional_browser_runtime(self) -> None:
        self.assertNotIn('$PYTHON" tests/browser_smoke.py', self.publish)
        self.assertIn('complete deployed Pages UAT after merge', self.publish)

    def test_generated_vv_output_cannot_enter_staged_source(self) -> None:
        self.assertIn('--output "$REVIEW_ROOT/extended-vv-results-v0.3.0-rc2.json"', self.publish)
        self.assertIn("generated dist output is staged", self.publish)
        self.assertIn('staged path is not in the reviewed source allowlist', self.publish)

    def test_public_copy_uses_plain_language(self) -> None:
        for fragment in (
            'Teaching clues remain hidden until after commitment',
            'Simulated decision-time budget',
            'Evidence judgment and public posture',
            'Decision fingerprint',
            'Download After-Action Review Record',
            'does not independently prove who made the decision or when',
        ):
            self.assertIn(fragment, self.app)
        for old in (
            'Self-guided cue suppression',
            'event-budget minutes',
            'Epistemic judgment and public posture',
            'Download AAR JSON',
            'It is not nonrepudiation evidence',
        ):
            self.assertNotIn(old, self.app)

    def test_gitignore_has_exactly_one_terminal_newline(self) -> None:
        content = (ROOT / '.gitignore').read_bytes()
        self.assertTrue(content.endswith(b'\n'))
        self.assertFalse(content.endswith(b'\n\n'))

    def test_public_text_files_have_no_trailing_whitespace(self) -> None:
        suffixes = {'.md', '.txt', '.py', '.js', '.mjs', '.gd', '.sh', '.yml', '.yaml', '.json', '.cfg', '.godot', '.cff', '.html', '.css', '.webmanifest'}
        failures = []
        for path in ROOT.rglob('*'):
            if not path.is_file() or any(part in {'.git', 'dist', 'dist-a', 'dist-b', '__pycache__'} for part in path.parts):
                continue
            if path.suffix.lower() not in suffixes and path.name not in {'LICENSE', 'VERSION', '.gitignore'}:
                continue
            try:
                lines = path.read_text(encoding='utf-8').splitlines()
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(lines, start=1):
                if line.endswith((' ', '\t')):
                    failures.append(f'{path.relative_to(ROOT)}:{line_number}')
        self.assertEqual(failures, [])


if __name__ == '__main__':
    unittest.main()
