import fs from 'node:fs';
const html = fs.readFileSync('web/index.html', 'utf8');
const js = fs.readFileSync('web/app.js', 'utf8');
const guard = fs.readFileSync('web/frame-guard.js', 'utf8');
const startup = fs.readFileSync('web/startup-guard.js', 'utf8');
const combined = html + js + guard + startup;
const checks = [
  ['main landmark', /<main\b/], ['live region', /aria-live="polite"/], ['skip link', /skip-link/],
  ['CSP', /Content-Security-Policy/], ['external frame guard', /window\.top !== window\.self/],
  ['commit gate', /Commit decision/], ['duplicate commit guard', /if \(committing\) return/],
  ['precise local data statement', /No application account, application telemetry, backend, external AI, live operational feed/],
  ['visible RC2 status', /v0\.3\.0-rc2/], ['AAR download', /Download After-Action Review Record/],
  ['unique AAR filename', /peace-os-crisis-room-aar-/], ['confirmation digest', /confirmed_digest/],
  ['native meter', /<meter min="0" max="100"/], ['saved session recovery', /Resume saved session/],
  ['compact progress', /Step \$\{stepNumber\} of \$\{steps\.length\}/],
  ['corrupt session retained', /saved session is damaged or unreadable/],
  ['strict session assessment', /assessSavedSession/], ['structured AAR', /Risks missed/],
  ['memory-only storage fallback', /Memory-only session/], ['storage exception handling', /setStorageUnavailable/],
  ['clipboard fallback', /Manual copy fallback/], ['download failure fallback', /AAR download failed/],
  ['delete confirmation', /Delete saved session\?/], ['facilitator banner', /FACILITATOR MODE/],
  ['facilitator guidance', /Facilitator guidance/], ['mobile diagnostic cards', /diagnostic-grid/],
  ['data-driven time', /currentScenario\.time_step_minutes/], ['persistent session context', /aria-label="Current session"/],
  ['WebCrypto detection', /webCryptoAvailable/], ['canonical AAR builder', /buildAarRecord/],
  ['bounded audit events', /hashAuditEvents/], ['print completeness', /beforeprint/],
  ['noscript guidance', /<noscript>/], ['startup failure guidance', /Unable to start the simulation/],
  ['repository link', /Project transparency/], ['verification link', /VERIFICATION\.md/],
  ['release link', /releases\/tag\/v0\.3\.0-rc2/], ['security link', /security\/policy/],
  ['issue link', /issues\/new\/choose/], ['post-action focus', /download-aar-button/],
];
const failures = checks.filter(([, expression]) => !expression.test(combined)).map(([name]) => name);
if (failures.length) throw new Error(`Web static checks failed: ${failures.join(', ')}`);
console.log('Web static checks passed.');
