#!/usr/bin/env node
/**
 * Dependency-free deployed browser journey validation for Peace OS: Crisis Room.
 *
 * Requires Node.js 22+ and a locally installed Chromium-family browser.
 * The script drives the deployed GitHub Pages client through Chrome DevTools
 * Protocol and writes machine-readable and human-readable evidence.
 */
import { spawn, spawnSync } from 'node:child_process';
import { existsSync, mkdtempSync, rmSync, writeFileSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { basename, dirname, join, resolve } from 'node:path';
import process from 'node:process';
import { URL } from 'node:url';

const sleep = ms => new Promise(resolvePromise => setTimeout(resolvePromise, ms));
const now = () => new Date().toISOString();

function fail(message) {
  throw new Error(message);
}

function parseArgs(argv) {
  const options = { outputJson: 'deployed-browser-uat.json', outputMd: 'deployed-browser-uat.md' };
  for (let index = 2; index < argv.length; index += 1) {
    const key = argv[index];
    const value = argv[index + 1];
    if (key === '--base-url') options.baseUrl = value;
    else if (key === '--expected-commit') options.expectedCommit = value;
    else if (key === '--output-json') options.outputJson = value;
    else if (key === '--output-md') options.outputMd = value;
    else if (key === '--browser') options.browser = value;
    else fail(`Unknown argument: ${key}`);
    index += 1;
  }
  if (!options.baseUrl) fail('--base-url is required');
  if (!options.expectedCommit || !/^[0-9a-f]{40}$/i.test(options.expectedCommit)) {
    fail('--expected-commit must be a full 40-character Git commit SHA');
  }
  options.baseUrl = options.baseUrl.replace(/\/+$/, '') + '/';
  return options;
}

function commandPath(command) {
  const locator = process.platform === 'win32' ? 'where' : 'which';
  const result = spawnSync(locator, [command], { encoding: 'utf8' });
  if (result.status !== 0) return '';
  return result.stdout.split(/\r?\n/).map(value => value.trim()).find(Boolean) || '';
}

function browserCandidates(explicit = '') {
  const env = process.env;
  const values = [
    explicit,
    env.PEACE_OS_BROWSER,
    env.CHROME_PATH,
    env.EDGE_PATH,
  ];
  if (process.platform === 'win32') {
    for (const base of [env.PROGRAMFILES, env['PROGRAMFILES(X86)'], env.LOCALAPPDATA]) {
      if (!base) continue;
      values.push(
        join(base, 'Google', 'Chrome', 'Application', 'chrome.exe'),
        join(base, 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
        join(base, 'Chromium', 'Application', 'chrome.exe'),
      );
    }
    values.push('chrome.exe', 'msedge.exe', 'chromium.exe');
  } else if (process.platform === 'darwin') {
    values.push(
      '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
      '/Applications/Chromium.app/Contents/MacOS/Chromium',
      'google-chrome', 'microsoft-edge', 'chromium',
    );
  } else {
    values.push('google-chrome', 'google-chrome-stable', 'microsoft-edge', 'microsoft-edge-stable', 'chromium', 'chromium-browser');
  }
  return [...new Set(values.filter(Boolean))];
}

function findBrowser(explicit = '') {
  for (const candidate of browserCandidates(explicit)) {
    const path = candidate.includes('/') || candidate.includes('\\')
      ? candidate
      : commandPath(candidate);
    if (!path || !existsSync(path)) continue;
    return { path, version: basename(path) };
  }
  fail('No supported Chrome, Edge, or Chromium executable was found. Set PEACE_OS_BROWSER to its full path.');
}

async function launchBrowser(browserPath) {
  const profile = mkdtempSync(join(tmpdir(), 'peace-os-browser-uat-'));
  const args = [
    '--headless=new',
    '--remote-debugging-port=0',
    `--user-data-dir=${profile}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-background-networking',
    '--disable-component-update',
    '--disable-sync',
    '--disable-extensions',
    '--disable-features=Translate,OptimizationHints,MediaRouter',
    '--metrics-recording-only',
    '--mute-audio',
    '--hide-scrollbars',
    '--disable-gpu',
    '--window-size=1440,1200',
    'about:blank',
  ];
  if (process.platform !== 'win32' && typeof process.getuid === 'function' && process.getuid() === 0) args.unshift('--no-sandbox');
  const child = spawn(browserPath, args, { stdio: ['ignore', 'ignore', 'pipe'], windowsHide: true });
  let stderr = '';
  let debuggerUrl = '';
  child.stderr.setEncoding('utf8');
  child.stderr.on('data', chunk => {
    stderr += chunk;
    const match = stderr.match(/DevTools listening on (ws:\/\/[^\s]+)/);
    if (match) debuggerUrl = match[1];
  });
  const deadline = Date.now() + 30000;
  while (!debuggerUrl && Date.now() < deadline) {
    if (child.exitCode !== null) fail(`Browser exited before DevTools was ready: ${stderr.slice(-2000)}`);
    await sleep(100);
  }
  if (!debuggerUrl) {
    child.kill('SIGKILL');
    fail(`Timed out waiting for browser DevTools endpoint: ${stderr.slice(-2000)}`);
  }
  let version = basename(browserPath);
  try {
    const endpoint = new URL(debuggerUrl);
    const response = await fetch(`http://${endpoint.hostname}:${endpoint.port}/json/version`, { signal: AbortSignal.timeout(5000) });
    if (response.ok) {
      const details = await response.json();
      version = details.Browser || version;
    }
  } catch {
    // Version text is diagnostic only; the live DevTools endpoint is the functional gate.
  }
  return {
    child,
    version,
    profile,
    debuggerUrl,
    async close() {
      if (child.exitCode === null) child.kill('SIGTERM');
      await Promise.race([new Promise(resolvePromise => child.once('exit', resolvePromise)), sleep(3000)]);
      if (child.exitCode === null) {
        child.kill('SIGKILL');
        await Promise.race([new Promise(resolvePromise => child.once('exit', resolvePromise)), sleep(3000)]);
      }
      rmSync(profile, { recursive: true, force: true });
    },
  };
}

class CDPClient {
  constructor(url) {
    this.url = url;
    this.nextId = 1;
    this.pending = new Map();
    this.listeners = new Map();
  }

  async connect() {
    this.ws = new WebSocket(this.url);
    await new Promise((resolvePromise, reject) => {
      const timer = setTimeout(() => reject(new Error('Timed out connecting to DevTools page socket')), 15000);
      this.ws.addEventListener('open', () => { clearTimeout(timer); resolvePromise(); }, { once: true });
      this.ws.addEventListener('error', event => { clearTimeout(timer); reject(event.error || new Error('DevTools WebSocket error')); }, { once: true });
    });
    this.ws.addEventListener('message', event => {
      const message = JSON.parse(String(event.data));
      if (message.id) {
        const pending = this.pending.get(message.id);
        if (!pending) return;
        this.pending.delete(message.id);
        if (message.error) pending.reject(new Error(`${message.error.message} (${message.error.code})`));
        else pending.resolve(message.result || {});
        return;
      }
      const callbacks = this.listeners.get(message.method) || [];
      for (const callback of callbacks) callback(message.params || {});
    });
    this.ws.addEventListener('close', () => {
      for (const pending of this.pending.values()) pending.reject(new Error('DevTools WebSocket closed'));
      this.pending.clear();
    });
  }

  on(method, callback) {
    const callbacks = this.listeners.get(method) || [];
    callbacks.push(callback);
    this.listeners.set(method, callbacks);
  }

  send(method, params = {}, timeoutMs = 15000) {
    const id = this.nextId++;
    return new Promise((resolvePromise, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`Timed out waiting for DevTools response: ${method}`));
      }, timeoutMs);
      this.pending.set(id, {
        resolve: value => { clearTimeout(timer); resolvePromise(value); },
        reject: error => { clearTimeout(timer); reject(error); },
      });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async evaluate(expression) {
    const result = await this.send('Runtime.evaluate', {
      expression,
      awaitPromise: true,
      returnByValue: true,
      userGesture: true,
    });
    if (result.exceptionDetails) {
      const description = result.exceptionDetails.exception?.description || result.exceptionDetails.text || 'Runtime evaluation failed';
      throw new Error(description);
    }
    return result.result?.value;
  }

  close() {
    if (this.ws && this.ws.readyState < 2) this.ws.close();
  }
}

async function createPage(debuggerUrl) {
  const endpoint = new URL(debuggerUrl);
  const httpOrigin = `http://${endpoint.hostname}:${endpoint.port}`;
  const response = await fetch(`${httpOrigin}/json/new?${encodeURIComponent('about:blank')}`, { method: 'PUT', signal: AbortSignal.timeout(10000) });
  if (!response.ok) fail(`Unable to create browser page: HTTP ${response.status}`);
  const target = await response.json();
  const client = new CDPClient(target.webSocketDebuggerUrl);
  await client.connect();
  return client;
}

async function waitFor(client, expression, description, timeoutMs = 20000) {
  const deadline = Date.now() + timeoutMs;
  let last = false;
  while (Date.now() < deadline) {
    try {
      last = await client.evaluate(expression);
      if (last) return last;
    } catch {
      // The app may be between renders. Poll until the bounded timeout.
    }
    await sleep(100);
  }
  fail(`Timed out waiting for ${description}; last value: ${JSON.stringify(last)}`);
}

const js = value => JSON.stringify(value);

async function click(client, selector) {
  await client.evaluate(`(() => { const element = document.querySelector(${js(selector)}); if (!element) throw new Error('Missing element: ' + ${js(selector)}); if (element.disabled) throw new Error('Disabled element: ' + ${js(selector)}); element.click(); return true; })()`);
  await sleep(75);
}

async function setChecked(client, selector, desired = true) {
  await client.evaluate(`(() => { const element = document.querySelector(${js(selector)}); if (!element) throw new Error('Missing element: ' + ${js(selector)}); if (Boolean(element.checked) !== ${desired ? 'true' : 'false'}) element.click(); return Boolean(element.checked); })()`);
  await sleep(75);
}

async function waitHeading(client, text) {
  await waitFor(client, `document.querySelector('#screen-heading')?.textContent?.includes(${js(text)})`, `heading containing ${text}`);
}

async function navigate(client, url) {
  await client.send('Page.navigate', { url });
  await waitFor(client, `document.readyState === 'complete' && Boolean(document.querySelector('#screen-heading'))`, `Peace OS application at ${url}`, 30000);
}

async function loadJson(baseUrl, relative) {
  const response = await fetch(new URL(relative, baseUrl), { headers: { 'User-Agent': 'Peace-OS-Deployed-Browser-UAT/1.0' } });
  if (!response.ok) fail(`Unable to fetch ${relative}: HTTP ${response.status}`);
  return response.json();
}

async function completeScenario(client, baseUrl, scenario, mode, { testInvalidation = false } = {}) {
  await navigate(client, `${baseUrl}?uat=${Date.now()}`);
  await client.evaluate('localStorage.clear(); true');
  await navigate(client, `${baseUrl}?uat=${Date.now()}-clean`);
  await waitHeading(client, 'Start a fictional session');
  const initiallyChecked = await client.evaluate(`document.querySelectorAll('input[type="radio"]:checked').length`);
  if (initiallyChecked !== 0) fail(`Expected neutral start; found ${initiallyChecked} selected radio controls`);

  await setChecked(client, `#mode-${mode}`);
  await setChecked(client, `#scenario-${scenario.scenario_id}`);
  await click(client, '[data-action="continue-start"]');
  await waitHeading(client, 'Policy boundary');
  await click(client, '[data-action="continue-boundary"]');
  await waitHeading(client, scenario.title);
  await click(client, '[data-action="open-evidence"]');
  await waitHeading(client, 'Evidence inbox');

  let assessmentMetadataHidden = true;
  let facilitatorPanels = 0;
  for (const [index, card] of scenario.evidence_cards.entries()) {
    await click(client, `#open-card-${card.id}`);
    await waitHeading(client, card.title);
    if (mode === 'assessment' && index === 0) {
      assessmentMetadataHidden = !(await client.evaluate(`document.body.textContent.includes('Practice metadata:')`));
    }
    if (mode === 'facilitator') {
      facilitatorPanels += Number(await client.evaluate(`document.querySelectorAll('.facilitator-panel').length`));
    }
    for (const [mark, expected] of Object.entries(card.expected_marks)) {
      await setChecked(client, `#mark-${card.id}-${mark}`, Boolean(expected));
    }
    await click(client, '[data-action="back-evidence"]');
    await waitHeading(client, 'Evidence inbox');
  }
  await click(client, '[data-action="continue-evidence"]');
  await waitHeading(client, 'Confidence');
  await setChecked(client, `input[name="confidence"][value=${js(scenario.correct_confidence_range[0])}]`);
  await click(client, '[data-action="continue-confidence"]');
  await waitHeading(client, 'Corroboration');
  await setChecked(client, `input[name="corroboration"][value=${js(scenario.correct_corroboration_range[0])}]`);
  await click(client, '[data-action="continue-corroboration"]');
  await waitHeading(client, 'Authenticity');
  await setChecked(client, `input[name="authenticity"][value=${js(scenario.correct_authenticity_range[0])}]`);
  await click(client, '[data-action="continue-authenticity"]');
  await waitHeading(client, 'Public release posture');
  const bestRelease = scenario.release_options.find(option => Number(option.doctrine_score) === 15);
  if (!bestRelease) fail(`Scenario ${scenario.scenario_id} has no 15-point release option`);
  await setChecked(client, `#release-${bestRelease.id}`);
  await click(client, '[data-action="continue-release"]');
  await waitHeading(client, 'Governance action plan');
  for (const action of scenario.recommended_actions) await setChecked(client, `#action-${action}`);
  await click(client, '[data-action="continue-actions"]');
  await waitHeading(client, 'Final human review');
  await setChecked(client, '#human-confirm');
  await waitFor(client, `!document.querySelector('#commit-button')?.disabled`, 'enabled commit button');

  let confirmationInvalidated = null;
  if (testInvalidation) {
    await click(client, '[data-action="back-actions"]');
    await waitHeading(client, 'Governance action plan');
    const firstAction = scenario.recommended_actions[0];
    await setChecked(client, `#action-${firstAction}`, false);
    await click(client, '[data-action="continue-actions"]');
    await waitHeading(client, 'Final human review');
    confirmationInvalidated = !(await client.evaluate(`document.querySelector('#human-confirm').checked`));
    if (!confirmationInvalidated) fail('Human confirmation was not invalidated after a material action change');
    await click(client, '[data-action="back-actions"]');
    await setChecked(client, `#action-${firstAction}`, true);
    await click(client, '[data-action="continue-actions"]');
    await setChecked(client, '#human-confirm');
    await waitFor(client, `!document.querySelector('#commit-button')?.disabled`, 're-enabled commit button');
  }

  await click(client, '#commit-button');
  await waitHeading(client, 'After-action review');
  const result = await client.evaluate(`(() => ({
    text: document.querySelector('#main').innerText,
    score: Number((document.querySelector('#main').innerText.match(/Score:\\s*(\\d+)\\/100/) || [])[1]),
    label: (document.querySelector('#main').innerText.match(/Bounded label:\\s*([^\\n]+)/) || [])[1] || '',
    digest: document.querySelector('.decision-digest code')?.textContent || ''
  }))()`);
  if (result.score !== 100) fail(`${scenario.scenario_id}/${mode} expected score 100, received ${result.score}`);
  if (!result.label.includes('Strong doctrine alignment')) fail(`${scenario.scenario_id}/${mode} expected Excellent label, received ${result.label}`);

  return {
    scenario_id: scenario.scenario_id,
    mode,
    score: result.score,
    label: result.label.trim(),
    assessment_metadata_hidden: mode === 'assessment' ? assessmentMetadataHidden : null,
    facilitator_panels_visible: mode === 'facilitator' ? facilitatorPanels > 0 : null,
    confirmation_invalidated_after_change: confirmationInvalidated,
  };
}

async function exerciseResultControls(client) {
  const checks = {};
  await client.evaluate(`Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async text => { window.__copied = text; } } }); true`);
  await click(client, '#copy-summary-button');
  checks.clipboard_success = Boolean(await client.evaluate(`window.__copied && document.body.textContent.includes('Summary copied to the clipboard.')`));

  await client.evaluate(`Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async () => { throw new Error('denied'); } } }); true`);
  await click(client, '#copy-summary-button');
  checks.clipboard_denial_fallback = Boolean(await client.evaluate(`document.querySelector('#copy-fallback') && document.body.textContent.includes('Clipboard access was denied')`));

  await client.evaluate(`window.__downloadName = ''; window.__originalAnchorClick = HTMLAnchorElement.prototype.click; HTMLAnchorElement.prototype.click = function(){ window.__downloadName = this.download || ''; }; true`);
  await click(client, '#download-aar-button');
  checks.download_invocation = Boolean(await client.evaluate(`window.__downloadName.startsWith('peace-os-crisis-room-aar-') && window.__downloadName.endsWith('.json')`));

  await client.evaluate(`URL.createObjectURL = () => { throw new Error('download denied'); }; true`);
  await click(client, '#download-aar-button');
  checks.download_denial_fallback = Boolean(await client.evaluate(`document.body.textContent.includes('AAR download failed')`));

  await client.evaluate(`window.__printed = false; window.print = () => { window.__printed = true; }; true`);
  await click(client, '#print-aar-button');
  checks.print_invocation = Boolean(await client.evaluate(`window.__printed === true`));

  return checks;
}

async function exerciseResumeDeleteAndCorruption(client, baseUrl) {
  const result = {};
  await navigate(client, `${baseUrl}?uat=resume-${Date.now()}`);
  await waitHeading(client, 'Saved session found');
  await click(client, '[data-action="resume-saved"]');
  await waitHeading(client, 'After-action review');
  result.resume_committed_result = true;
  await click(client, '#delete-session');
  await waitHeading(client, 'Delete saved session?');
  await click(client, '[data-action="confirm-delete"]');
  await waitHeading(client, 'Start a fictional session');
  result.delete_saved_session = !(await client.evaluate(`localStorage.getItem('peace-os-crisis-room-session-v1')`));

  await client.evaluate(`localStorage.setItem('peace-os-crisis-room-session-v1', '{broken-json'); true`);
  await navigate(client, `${baseUrl}?uat=corrupt-${Date.now()}`);
  await waitHeading(client, 'Start a fictional session');
  result.corrupted_session_recovery = Boolean(await client.evaluate(`document.body.textContent.includes('A damaged saved session was removed') && !localStorage.getItem('peace-os-crisis-room-session-v1')`));
  return result;
}

async function exerciseMobileAndKeyboard(client, baseUrl) {
  const result = {};
  const widths = [320, 360, 375, 390, 414];
  let mobilePass = true;
  for (const width of widths) {
    await client.send('Emulation.setDeviceMetricsOverride', { width, height: 900, deviceScaleFactor: 1, mobile: true });
    await navigate(client, `${baseUrl}?uat=mobile-${width}-${Date.now()}`);
    const fits = Boolean(await client.evaluate(`document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1`));
    result[`mobile_${width}_no_global_overflow`] = fits;
    mobilePass = mobilePass && fits;
  }
  result.mobile_width_matrix = mobilePass;

  await client.send('Emulation.setDeviceMetricsOverride', { width: 720, height: 900, deviceScaleFactor: 2, mobile: false });
  await navigate(client, `${baseUrl}?uat=zoom-${Date.now()}`);
  result.zoom_200_no_global_overflow = Boolean(await client.evaluate(`document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1`));
  await client.send('Emulation.clearDeviceMetricsOverride');

  await navigate(client, `${baseUrl}?uat=keyboard-${Date.now()}`);
  await client.evaluate(`document.body.focus(); true`);
  await client.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 });
  await client.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 });
  result.skip_link_first_tab = Boolean(await client.evaluate(`document.activeElement?.classList.contains('skip-link')`));

  await client.send('Page.addScriptToEvaluateOnNewDocument', { source: `
    for (const name of ['getItem','setItem','removeItem','clear']) {
      Object.defineProperty(Storage.prototype, name, { configurable: true, value(){ throw new DOMException('blocked','SecurityError'); } });
    }
  ` });
  await navigate(client, `${baseUrl}?uat=storage-blocked-${Date.now()}`);
  result.storage_denied_memory_only = Boolean(await client.evaluate(`document.body.textContent.includes('Memory-only session')`));
  return result;
}

function markdown(record) {
  const rows = [];
  for (const journey of record.journeys) rows.push(`| ${journey.scenario_id} | ${journey.mode} | ${journey.status} | ${journey.detail} |`);
  for (const [name, value] of Object.entries(record.control_checks)) rows.push(`| control | ${name} | ${value ? 'PASS' : 'FAIL'} | |`);
  return [
    '# Peace OS Deployed Browser Journey Validation',
    '',
    `**URL:** \`${record.base_url}\`  `,
    `**Expected commit:** \`${record.expected_commit}\`  `,
    `**Browser:** \`${record.browser.version}\`  `,
    `**Platform:** \`${record.platform}\`  `,
    `**Generated:** \`${record.generated_at_utc}\`  `,
    `**Overall status:** **${record.status}**`,
    '',
    '| Type | Scenario / check | Status | Detail |',
    '|---|---|---|---|',
    ...rows,
    '',
    '## Evidence boundary',
    '',
    '- This is automated deployed-browser journey validation, not human user acceptance testing.',
    '- Human screen-reader, physical-device, learning, professional, Godot, Windows, certification, and operational validation remain separate evidence streams.',
    '',
  ].join('\n');
}

async function main() {
  const options = parseArgs(process.argv);
  const nodeMajor = Number(process.versions.node.split('.')[0]);
  if (nodeMajor < 22) fail(`Node.js 22 or newer is required; found ${process.versions.node}`);
  const browser = findBrowser(options.browser);
  const runtime = await launchBrowser(browser.path);
  browser.version = runtime.version;
  const client = await createPage(runtime.debuggerUrl);
  const errors = [];
  const requests = [];
  client.on('Runtime.exceptionThrown', params => errors.push(params.exceptionDetails?.exception?.description || params.exceptionDetails?.text || 'Runtime exception'));
  client.on('Log.entryAdded', params => { if (['error', 'warning'].includes(params.entry?.level)) errors.push(`${params.entry.level}: ${params.entry.text}`); });
  client.on('Network.requestWillBeSent', params => requests.push(params.request?.url || ''));
  await client.send('Page.enable');
  await client.send('Runtime.enable');
  await client.send('Network.enable');
  await client.send('Log.enable');

  const record = {
    schema_version: '1.0',
    acceptance_class: 'automated_deployed_browser_journey_validation',
    base_url: options.baseUrl,
    expected_commit: options.expectedCommit,
    generated_at_utc: now(),
    platform: `${process.platform} ${process.arch}`,
    node: process.versions.node,
    browser,
    journeys: [],
    control_checks: {},
    console_errors: [],
    unexpected_network_requests: [],
    status: 'FAIL',
  };

  let fatalError = null;
  try {
    const index = await loadJson(options.baseUrl, 'data/scenarios/index.json');
    const scenarios = {};
    for (const item of index.scenarios) scenarios[item.id] = await loadJson(options.baseUrl, `data/scenarios/${item.file}`);

    for (const [scenarioId, mode, invalidation] of [
      ['scenario_01_viral_collision_video', 'practice', true],
      ['scenario_02_deepfake_distress_call', 'assessment', false],
      ['scenario_01_viral_collision_video', 'facilitator', false],
    ]) {
      try {
        const detail = await completeScenario(client, options.baseUrl, scenarios[scenarioId], mode, { testInvalidation: invalidation });
        record.journeys.push({ scenario_id: scenarioId, mode, status: 'PASS', detail: JSON.stringify(detail) });
      } catch (error) {
        record.journeys.push({ scenario_id: scenarioId, mode, status: 'FAIL', detail: error.message });
        throw error;
      }
    }

    record.control_checks = {
      ...(await exerciseResultControls(client)),
      ...(await exerciseResumeDeleteAndCorruption(client, options.baseUrl)),
      ...(await exerciseMobileAndKeyboard(client, options.baseUrl)),
    };

    const allowedOrigin = new URL(options.baseUrl).origin;
    record.unexpected_network_requests = [...new Set(requests.filter(url => {
      if (!url || url.startsWith('data:') || url.startsWith('blob:') || url.startsWith('devtools:')) return false;
      try { return new URL(url).origin !== allowedOrigin; } catch { return true; }
    }))];
    record.console_errors = errors.filter(message => !message.includes('favicon'));
    const controlsPass = Object.values(record.control_checks).every(Boolean);
    const journeysPass = record.journeys.every(item => item.status === 'PASS');
    record.status = controlsPass && journeysPass && record.console_errors.length === 0 && record.unexpected_network_requests.length === 0 ? 'PASS' : 'FAIL';
  } catch (error) {
    fatalError = error;
    record.fatal_error = error instanceof Error ? error.message : String(error);
    record.status = 'FAIL';
  } finally {
    client.close();
    await runtime.close();
  }

  mkdirSync(dirname(resolve(options.outputJson)), { recursive: true });
  mkdirSync(dirname(resolve(options.outputMd)), { recursive: true });
  writeFileSync(options.outputJson, `${JSON.stringify(record, null, 2)}\n`, 'utf8');
  writeFileSync(options.outputMd, markdown(record), 'utf8');
  if (fatalError) fail(`Deployed browser journey validation failed: ${record.fatal_error}; see ${options.outputJson}`);
  if (record.status !== 'PASS') fail(`Deployed browser journey validation failed; see ${options.outputJson}`);
  console.log(`PASS: deployed browser journey validation completed with ${basename(options.outputJson)}`);
}

main().then(() => {
  process.exit(0);
}).catch(error => {
  console.error(`STOP: ${error.message}`);
  process.exit(1);
});
