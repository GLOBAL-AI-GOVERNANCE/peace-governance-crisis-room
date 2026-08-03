import fs from 'node:fs';

const html = fs.readFileSync('web/index.html', 'utf8');
const js = fs.readFileSync('web/app.js', 'utf8');
const guard = fs.readFileSync('web/frame-guard.js', 'utf8');
const combined = html + js + guard;
const checks = [
  ['main landmark', /<main\b/],
  ['live region', /aria-live="polite"/],
  ['skip link', /skip-link/],
  ['CSP', /Content-Security-Policy/],
  ['external frame guard', /window\.top !== window\.self/],
  ['commit gate', /Commit decision/],
  ['duplicate commit guard', /if \(committing\) return/],
  ['no telemetry statement', /No login, telemetry/],
  ['AAR download', /Download After-Action Review Record/],
  ['unique AAR filename', /peace-os-crisis-room-aar-/],
  ['confirmation digest', /confirmed_digest/],
  ['native meter', /<meter min="0" max="100"/],
  ['saved session recovery', /Resume saved session/],
  ['compact progress', /Step \${stepNumber} of \${steps.length}/],
  ['corrupt saved-session recovery', /A damaged saved session was removed/],
  ['structured AAR', /Risks missed/],
  ['memory-only storage fallback', /Memory-only session/],
  ['storage exception handling', /setStorageUnavailable/],
  ['clipboard fallback', /Manual copy fallback/],
  ['download failure fallback', /AAR download failed/],
  ['delete confirmation', /Delete saved session\?/],
  ['facilitator banner', /FACILITATOR MODE/],
  ['facilitator guidance', /Facilitator guidance/],
  ['mobile diagnostic cards', /diagnostic-grid/],
  ['decision time terminology', /Simulated decision-time budget/],
  ['skip-link initial focus preserved', /state\?\.screen === 'start'/],
  ['action capacity terminology', /Action-plan capacity/],
  ['plain assessment language', /Teaching clues remain hidden until after commitment/],
  ['simulated decision time language', /Simulated decision-time budget/],
  ['decision fingerprint language', /Decision fingerprint/],
  ['plain audit limitation', /does not independently prove who made the decision or when/],
  ['persistent session context', /aria-label=\"Current session\"/],
  ['post-action focus preservation', /download-aar-button/],
];
const failures = checks.filter(([, expression]) => !expression.test(combined)).map(([name]) => name);
if (failures.length) throw new Error(`Web static checks failed: ${failures.join(', ')}`);
console.log('Web static checks passed.');
