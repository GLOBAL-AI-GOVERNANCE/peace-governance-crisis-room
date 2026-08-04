import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WebAccessibilityContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / 'web/index.html').read_text(encoding='utf-8')
        cls.css = (ROOT / 'web/styles.css').read_text(encoding='utf-8')
        cls.js = (ROOT / 'web/app.js').read_text(encoding='utf-8')
        cls.guard = (ROOT / 'web/frame-guard.js').read_text(encoding='utf-8')
        cls.startup = (ROOT / 'web/startup-guard.js').read_text(encoding='utf-8')
        cls.session = (ROOT / 'web/session.js').read_text(encoding='utf-8')

    def test_semantic_landmarks_and_live_region(self):
        for fragment in ('<header', '<nav', '<main', '<footer', 'aria-live="polite"', 'Skip to simulation'):
            self.assertIn(fragment, self.html)

    def test_local_only_delivery(self):
        combined = self.html + self.js
        for forbidden in ('google-analytics', 'googletagmanager', 'segment.io', 'mixpanel', 'fetch("http', "fetch('http"):
            self.assertNotIn(forbidden, combined)
        self.assertIn('No application account, application telemetry, backend, external AI, live operational feed', self.html)

    def test_commit_before_results(self):
        self.assertIn("result,", self.js)
        self.assertIn("action === 'commit'", self.js)
        self.assertIn('Results were not available before commitment.', self.js)

    def test_no_preselected_decision(self):
        for fragment in ("confidence: ''", "corroboration: ''", "authenticity: ''", "release_id: ''"):
            self.assertIn(fragment, self.js + self.session)

    def test_responsive_and_reduced_motion(self):
        self.assertIn('@media (max-width: 42rem)', self.css)
        self.assertIn('@media (prefers-reduced-motion: reduce)', self.css)
        self.assertNotIn('min-width: 900px', self.css)

    def test_focus_continuity_and_controls(self):
        self.assertIn(':focus-visible', self.css)
        self.assertIn('pendingFocusId', self.js)
        self.assertIn('focusAfterRender', self.js)
        self.assertIn('fieldset', self.js)
        self.assertIn('type="radio"', self.js)
        self.assertIn('type="checkbox"', self.js)

    def test_progress_map_covers_detail_and_review(self):
        self.assertIn('card: 2', self.js)
        self.assertIn('review: 6', self.js)

    def test_native_meter_and_structured_aar(self):
        self.assertIn('<meter min="0" max="100"', self.js)
        self.assertIn('Risks missed', self.js)
        self.assertIn('Unsupported markings', self.js)
        self.assertNotIn('<pre>${esc(JSON.stringify', self.js)

    def test_saved_session_recovery(self):
        for phrase in ('Resume saved session', 'Start new session', 'Delete saved session', 'assessSavedSession'):
            self.assertIn(phrase, self.js + self.html)

    def test_commit_guard_and_unique_download(self):
        self.assertIn('if (committing) return;', self.js)
        self.assertIn('peace-os-crisis-room-aar-', self.js)
        self.assertIn('digestPrefix', self.js)

    def test_frame_guard_is_external_and_documented(self):
        self.assertIn('frame-guard.js', self.html)
        self.assertIn('window.top !== window.self', self.guard)
        self.assertNotIn("frame-ancestors 'none'", self.html)

    def test_focus_indicator_meets_non_text_contrast(self):
        import re

        def relative_luminance(hex_color):
            value = hex_color.lstrip('#')
            channels = [int(value[index:index + 2], 16) / 255 for index in (0, 2, 4)]
            converted = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
            return 0.2126 * converted[0] + 0.7152 * converted[1] + 0.0722 * converted[2]

        def contrast(first, second):
            high, low = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
            return (high + 0.05) / (low + 0.05)

        focus = re.search(r'--focus:\s*(#[0-9a-fA-F]{6})', self.css).group(1)
        self.assertGreaterEqual(contrast(focus, '#ffffff'), 3.0)
        self.assertGreaterEqual(contrast(focus, '#f7f5f0'), 3.0)

    def test_current_session_context_and_action_focus_preservation(self):
        self.assertIn('function sessionContext()', self.js)
        self.assertIn('aria-label="Current session"', self.js)
        for control_id in ('download-aar-button', 'copy-summary-button', 'print-aar-button', 'restart-button'):
            self.assertIn(control_id, self.js)

    def test_visible_maturity_transparency_and_failure_guidance(self):
        self.assertIn('v0.3.0-rc2', self.html)
        self.assertIn('<noscript>', self.html)
        self.assertIn('Project transparency', self.html)
        for fragment in ('VERIFICATION.md', 'PUBLIC_RELEASE_GATE.md', 'security/policy', 'issues/new/choose'):
            self.assertIn(fragment, self.html + self.startup)

    def test_print_expands_complete_aar(self):
        self.assertIn("window.addEventListener('beforeprint'", self.js)
        self.assertIn("window.addEventListener('afterprint'", self.js)

    def test_webcrypto_and_canonical_aar_contract(self):
        self.assertIn('webCryptoAvailable', self.js)
        self.assertIn('buildAarRecord', self.js)
        self.assertIn('assertAarRecord', self.js)


if __name__ == '__main__':
    unittest.main()
