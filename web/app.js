import {
  MARK_NAMES,
  actionCosts,
  actionPlanValid,
  scoreBreakdown,
  totalScore,
  performanceLabel,
  markingDiagnostics,
  canonicalJson,
  sha256Hex,
  computeOutcomeIndicators,
} from './scoring.js';

const PRODUCT_NAME = 'Peace OS: Crisis Room';
const APP_VERSION = '0.3.0-rc1';
const SESSION_SCHEMA = '1.0';
const STORAGE_KEY = 'peace-os-crisis-room-session-v1';

const $ = selector => document.querySelector(selector);
const main = $('#main');
const live = $('#live');
const progress = $('#progress');

const actionLabels = {
  protect_civilians: 'Protect civilian identities and sensitive details',
  request_original_media: 'Request original media and metadata',
  info_integrity_review: 'Trigger an information-integrity review',
  deescalation_channel: 'Activate a de-escalation review channel',
  senior_review: 'Escalate to senior human review',
  humanitarian_check: 'Check humanitarian and safety channels without public overclaiming',
};

const steps = [
  'Start',
  'Briefing',
  'Evidence',
  'Judgment',
  'Release',
  'Actions',
  'Review',
  'Result',
];

const progressMap = {
  resume: 0,
  start: 0,
  boundary: 0,
  briefing: 1,
  evidence: 2,
  card: 2,
  confidence: 3,
  corroboration: 3,
  authenticity: 3,
  release: 4,
  actions: 5,
  review: 6,
  result: 7,
};

let rubric;
let language;
let scenarios = {};
let state;
let savedCandidate = null;
let pendingFocusId = '';
let committing = false;
let storageAvailable = true;
let storageReason = '';
let visibleActionMessage = '';
let copyFallbackText = '';
let deleteReturnScreen = 'start';

const blank = () => ({
  session_schema_version: SESSION_SCHEMA,
  app_version: APP_VERSION,
  screen: 'start',
  mode: '',
  scenario_id: '',
  card_id: '',
  reviewed: [],
  marks: {},
  confidence: '',
  corroboration: '',
  authenticity: '',
  release_id: '',
  actions: Object.fromEntries(Object.keys(actionLabels).map(key => [key, false])),
  remaining_minutes: 30,
  public_pressure: 0,
  timed: { evidence: [], confidence: false, release: false },
  human_confirmation: false,
  confirmed_digest: '',
  committed: false,
  result: null,
});

function setStorageUnavailable(error) {
  storageAvailable = false;
  storageReason = error instanceof Error ? error.message : String(error || 'Browser storage is unavailable.');
}

function detectStorage() {
  try {
    const probe = `${STORAGE_KEY}-probe`;
    localStorage.setItem(probe, '1');
    localStorage.removeItem(probe);
    storageAvailable = true;
    storageReason = '';
  } catch (error) {
    setStorageUnavailable(error);
  }
}

function save() {
  if (!storageAvailable) return false;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    updateDeleteButton();
    return true;
  } catch (error) {
    setStorageUnavailable(error);
    visibleActionMessage = 'Session persistence is unavailable. This session continues in memory, but it cannot be resumed after refresh.';
    updateDeleteButton();
    return false;
  }
}

function clearSaved() {
  if (!storageAvailable) return false;
  try {
    localStorage.removeItem(STORAGE_KEY);
    updateDeleteButton();
    return true;
  } catch (error) {
    setStorageUnavailable(error);
    visibleActionMessage = 'Saved-session deletion could not be completed because browser storage is unavailable.';
    updateDeleteButton();
    return false;
  }
}

function loadSaved() {
  if (!storageAvailable) return null;
  let raw = null;
  try {
    raw = localStorage.getItem(STORAGE_KEY);
  } catch (error) {
    setStorageUnavailable(error);
    return null;
  }
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    try {
      localStorage.removeItem(STORAGE_KEY);
      visibleActionMessage = 'A damaged saved session was removed. Start a new session or choose another scenario.';
    } catch (error) {
      setStorageUnavailable(error);
    }
    return null;
  }
}

function hasSavedSession() {
  if (!storageAvailable) return false;
  try {
    return localStorage.getItem(STORAGE_KEY) !== null;
  } catch (error) {
    setStorageUnavailable(error);
    return false;
  }
}

function updateDeleteButton() {
  const control = $('#delete-session');
  if (!control) return;
  const available = hasSavedSession();
  control.hidden = !available;
  control.disabled = !available;
}

function storageNotice() {
  if (storageAvailable) return '';
  return `<div class="warning" role="status"><strong>Memory-only session:</strong> browser storage is unavailable. Continue normally, then download, copy, or print the AAR before closing this page. Resume and saved-session deletion are unavailable.</div>`;
}

function actionMessage() {
  if (!visibleActionMessage) return '';
  return `<p class="status-message" role="status">${esc(visibleActionMessage)}</p>`;
}

function facilitatorBanner() {
  if (state?.mode !== 'facilitator' || ['start', 'resume', 'delete_confirm'].includes(state.screen)) return '';
  return '<div class="facilitator-banner" role="note"><strong>FACILITATOR MODE</strong>  -  answer-revealing teaching context is visible. Do not use this mode for blind assessment.</div>';
}

function savedStateValid(candidate) {
  return Boolean(
    candidate &&
    typeof candidate === 'object' &&
    candidate.session_schema_version === SESSION_SCHEMA &&
    candidate.app_version === APP_VERSION &&
    typeof candidate.screen === 'string' &&
    Array.isArray(candidate.reviewed) &&
    candidate.marks && typeof candidate.marks === 'object' &&
    candidate.actions && typeof candidate.actions === 'object'
  );
}

function announce(text) {
  live.textContent = '';
  setTimeout(() => { live.textContent = text; }, 20);
}

function esc(value = '') {
  return String(value).replace(/[&<>"']/g, character => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[character]));
}

function button(label, action, secondary = false, disabled = false, id = '') {
  return `<button type="button" data-action="${esc(action)}" class="${secondary ? 'secondary' : ''}" ${disabled ? 'disabled' : ''} ${id ? `id="${esc(id)}"` : ''}>${esc(label)}</button>`;
}

function renderProgress() {
  const current = progressMap[state.screen] ?? 0;
  const stepNumber = current + 1;
  progress.innerHTML = `
    <div class="progress-summary">
      <span>Step ${stepNumber} of ${steps.length}</span>
      <strong>${esc(steps[current])}</strong>
    </div>
    <progress max="${steps.length}" value="${stepNumber}" aria-label="Step ${stepNumber} of ${steps.length}: ${esc(steps[current])}">${stepNumber} of ${steps.length}</progress>`;
}

function focusAfterRender() {
  const requested = pendingFocusId ? document.getElementById(pendingFocusId) : null;
  pendingFocusId = '';
  if (!requested && state?.screen === 'start') return;
  const target = requested || document.getElementById('screen-heading') || main;
  requestAnimationFrame(() => target?.focus());
}

function scenario() {
  return scenarios[state.scenario_id];
}

function consumeTime(kind, id = '') {
  const currentScenario = scenario();
  if (!currentScenario) return;
  if (kind === 'evidence') {
    if (state.timed.evidence.includes(id)) return;
    state.timed.evidence.push(id);
  } else {
    if (state.timed[kind]) return;
    state.timed[kind] = true;
  }
  state.remaining_minutes = Math.max(0, state.remaining_minutes - 2);
  state.public_pressure = Math.min(100, state.public_pressure + 3);
}

function invalidate(reason) {
  if (state.human_confirmation || state.confirmed_digest) {
    state.human_confirmation = false;
    state.confirmed_digest = '';
    announce(`Confirmation invalidated: ${reason}`);
  }
}

function setState(patch, reason = '', focusId = '') {
  if (reason) invalidate(reason);
  Object.assign(state, patch);
  pendingFocusId = focusId;
  save();
  render();
}

async function decisionDigest() {
  return sha256Hex(canonicalJson(decisionInput()));
}

function decisionInput() {
  return {
    scenario_id: state.scenario_id,
    reviewed: [...state.reviewed].sort(),
    marks: state.marks,
    confidence: state.confidence,
    corroboration: state.corroboration,
    authenticity: state.authenticity,
    release_id: state.release_id,
    actions: state.actions,
    remaining_minutes: state.remaining_minutes,
  };
}

function decisionForScore() {
  return {
    ...decisionInput(),
    reviewed_count: state.reviewed.length,
    human_confirmation: state.human_confirmation,
  };
}


function sessionContext() {
  if (!state?.scenario_id || ['start', 'resume'].includes(state.screen)) return '';
  const currentScenario = scenarios[state.scenario_id];
  const mode = state.mode ? state.mode[0].toUpperCase() + state.mode.slice(1) : 'Not selected';
  return `<div class="session-context" aria-label="Current session"><span><strong>Scenario:</strong> ${esc(currentScenario?.title || state.scenario_id)}</span><span><strong>Mode:</strong> ${esc(mode)}</span></div>`;
}

function panel(title, body) {
  main.innerHTML = `<section class="panel" aria-labelledby="screen-heading">${facilitatorBanner()}${storageNotice()}${actionMessage()}${sessionContext()}<h2 id="screen-heading" tabindex="-1">${esc(title)}</h2>${body}</section>`;
  visibleActionMessage = '';
  renderProgress();
  wire();
  updateDeleteButton();
  focusAfterRender();
}

function render() {
  if (!state) state = blank();
  const screens = {
    resume,
    start,
    boundary,
    briefing,
    evidence,
    card,
    confidence: () => categorical(
      'Confidence',
      'confidence',
      ['Confirmed', 'Likely', 'Possible', 'Unverified'],
      'How strongly does the available evidence support the claim?'
    ),
    corroboration: () => categorical(
      'Corroboration',
      'corroboration',
      ['Corroborated', 'Partially corroborated', 'Contradictory', 'Uncorroborated'],
      'Do independent sources support the claim?'
    ),
    authenticity: () => categorical(
      'Authenticity',
      'authenticity',
      ['No manipulation indicators', 'Manipulation suspected', 'Authenticity unclear', 'Not applicable'],
      'Is the item genuine, altered, synthetic, or unresolved?'
    ),
    release,
    actions,
    review,
    result,
    delete_confirm: deleteConfirm,
  };
  return (screens[state.screen] || start)();
}

function resume() {
  const title = savedCandidate?.scenario_id && scenarios[savedCandidate.scenario_id]
    ? scenarios[savedCandidate.scenario_id].title
    : 'Saved session';
  panel('Saved session found', `
    <p>A compatible local session exists for <strong>${esc(title)}</strong>.</p>
    <p>Choose deliberately. Starting new or deleting removes the stored session from this browser.</p>
    <div class="actions">
      ${button('Resume saved session', 'resume-saved')}
      ${button('Start new session', 'start-new', true)}
      ${button('Delete saved session', 'delete-saved', true)}
    </div>`);
}

function start() {
  const scenarioChoices = Object.values(scenarios).map(item => `
    <label class="choice" for="scenario-${esc(item.scenario_id)}">
      <input id="scenario-${esc(item.scenario_id)}" data-focus-key="scenario-${esc(item.scenario_id)}" type="radio" name="scenario" value="${esc(item.scenario_id)}" ${state.scenario_id === item.scenario_id ? 'checked' : ''}>
      <span><strong>${esc(item.title)}</strong><br>${esc(item.briefing)}</span>
    </label>`).join('');
  const modes = ['practice', 'assessment', 'facilitator'].map(mode => {
    const explanation = mode === 'assessment'
      ? 'Teaching clues remain hidden until after commitment; this mode is not secure or proctored.'
      : mode === 'facilitator'
        ? 'Answer-revealing teaching information appears after entry.'
        : 'Guided learning with explanations after commitment.';
    return `
      <label class="choice" for="mode-${mode}">
        <input id="mode-${mode}" data-focus-key="mode-${mode}" type="radio" name="mode" value="${mode}" ${state.mode === mode ? 'checked' : ''}>
        <span><strong>${mode[0].toUpperCase() + mode.slice(1)}</strong><br>${esc(explanation)}</span>
      </label>`;
  }).join('');
  panel('Start a fictional session', `
    <p>No answer is preselected. Choose a mode and scenario before starting.</p>
    <fieldset><legend>Experience mode</legend>${modes}</fieldset>
    <fieldset><legend>Scenario</legend>${scenarioChoices}</fieldset>
    <div class="actions">${button('Continue to policy boundary', 'continue-start', false, !state.mode || !state.scenario_id)}</div>`);
}

function boundary() {
  panel('Policy boundary', `
    <ul>
      <li>Fictional and educational only.</li>
      <li>No live data, login, telemetry, cloud storage, external AI, autonomous release, or external action.</li>
      <li>Outputs are authored learning-model results, not forecasts, intelligence, attribution, or legal conclusions.</li>
      <li>AI may advise. AI may not decide.</li>
    </ul>
    <div class="actions">${button('Back', 'back-start', true)}${button('Acknowledge and continue', 'continue-boundary')}</div>`);
}

function facilitatorNotes(currentScenario, context = 'briefing') {
  if (state.mode !== 'facilitator') return '';
  const notes = currentScenario.facilitator_notes || [];
  const lead = context === 'result'
    ? 'Use these prompts after commitment to compare the participant decision with the authored learning model.'
    : 'Use these notes to guide observation and later discussion. Avoid answering for the participant.';
  return `<aside class="facilitator-panel" aria-labelledby="facilitator-guidance"><h3 id="facilitator-guidance">Facilitator guidance</h3><p>${esc(lead)}</p><ul>${notes.map(note => `<li>${esc(note)}</li>`).join('')}</ul></aside>`;
}

function facilitatorCardContext(evidenceCard) {
  if (state.mode !== 'facilitator') return '';
  const indicators = evidenceCard.facilitator_indicators || [];
  const expected = Object.entries(evidenceCard.expected_marks || {}).filter(([, value]) => value).map(([key]) => key.replaceAll('_', ' '));
  return `<aside class="facilitator-panel" aria-labelledby="facilitator-card"><h3 id="facilitator-card">Facilitator evidence context</h3><p><strong>Teaching indicators:</strong> ${esc(indicators.join('; ') || 'None authored.')}</p><p><strong>Expected positive marks:</strong> ${esc(expected.join(', ') || 'None.')}</p></aside>`;
}

function facilitatorActionContext(currentScenario) {
  if (state.mode !== 'facilitator') return '';
  return `<aside class="facilitator-panel" aria-labelledby="facilitator-actions"><h3 id="facilitator-actions">Facilitator action rationale</h3><ul>${Object.keys(actionLabels).map(key => `<li>${esc(actionLabels[key])}: authored doctrine score ${esc(currentScenario.action_scores?.[key] ?? 0)}</li>`).join('')}</ul></aside>`;
}

function briefing() {
  const currentScenario = scenario();
  panel(currentScenario.title, `
    <h3>Your role</h3><p>Act as the human governance reviewer for a fictional information crisis.</p>
    <h3>What happened</h3><p>${esc(currentScenario.briefing)}</p>
    <h3>What is unknown</h3><p>Source integrity, corroboration, authenticity, civilian exposure, and causal attribution remain unresolved.</p>
    <h3>Decision required</h3><p>Review all evidence, form a bounded judgment, select a public posture and feasible actions, then explicitly confirm the package.</p>
    <p class="status">Simulated decision-time budget: ${currentScenario.decision_clock_minutes} minutes. This is not a live countdown. First-time evidence review and selected judgment events use the budget.</p>
    ${facilitatorNotes(currentScenario)}
    <div class="actions">${button('Back', 'back-boundary', true)}${button('Open evidence inbox', 'open-evidence')}</div>`);
}

function evidence() {
  const currentScenario = scenario();
  const complete = state.reviewed.length === currentScenario.evidence_cards.length;
  const cards = currentScenario.evidence_cards.map(item => `
    <article class="card ${state.reviewed.includes(item.id) ? 'reviewed' : 'unreviewed'}">
      <h3>${esc(item.title)}</h3>
      <p>${state.reviewed.includes(item.id) ? 'Reviewed' : 'Unread'}</p>
      ${button('Review evidence', `card:${item.id}`, true, false, `open-card-${item.id}`)}
    </article>`).join('');
  panel('Evidence inbox', `
    <p class="status">Reviewed ${state.reviewed.length} of ${currentScenario.evidence_cards.length}. Simulated decision-time budget remaining: ${state.remaining_minutes} minutes. Public pressure: ${state.public_pressure}/100. Complete review is required before analysis.</p>
    <div class="grid">${cards}</div>
    <div class="actions">${button('Back to briefing', 'back-briefing', true)}${button('Continue to confidence', 'continue-evidence', false, !complete)}</div>`);
}

function card() {
  const currentScenario = scenario();
  const evidenceCard = currentScenario.evidence_cards.find(item => item.id === state.card_id);
  const marks = state.marks[evidenceCard.id] || Object.fromEntries(MARK_NAMES.map(key => [key, false]));
  const metadata = state.mode === 'assessment'
    ? ''
    : `<p><strong>Practice metadata:</strong> ${esc(evidenceCard.tags.join(', '))}. Source status: ${esc(evidenceCard.reliability)}.</p>`;
  const controls = [
    ['flagged', 'Flag for contradiction or manipulation risk'],
    ['sensitive', 'Sensitive civilian or identity concern'],
    ['follow_up', 'Follow-up required'],
    ['used', 'Use in final assessment'],
  ].map(([key, label]) => {
    const id = `mark-${evidenceCard.id}-${key}`;
    return `
      <label class="choice" for="${id}">
        <input id="${id}" data-mark="${key}" type="checkbox" ${marks[key] ? 'checked' : ''}>
        <span>${esc(label)}</span>
      </label>`;
  }).join('');
  panel(evidenceCard.title, `
    <p>${esc(evidenceCard.description)}</p>${metadata}${facilitatorCardContext(evidenceCard)}
    <fieldset><legend>Your evidence markings</legend>${controls}</fieldset>
    <div class="actions">${button('Return to evidence inbox', 'back-evidence', true)}</div>`);
}

function categorical(title, key, values, definition) {
  const backAction = key === 'confidence' ? 'back-evidence' : key === 'corroboration' ? 'back-confidence' : 'back-corroboration';
  const controls = values.map((value, index) => {
    const id = `${key}-${index}`;
    return `
      <label class="choice" for="${id}">
        <input id="${id}" type="radio" name="${key}" value="${esc(value)}" ${state[key] === value ? 'checked' : ''}>
        <span>${esc(value)}</span>
      </label>`;
  }).join('');
  panel(title, `
    <p>${esc(definition)}</p>
    <fieldset><legend>Select one</legend>${controls}</fieldset>
    <div class="actions">${button('Back', backAction, true)}${button('Continue', `continue-${key}`, false, !state[key])}</div>`);
}

function release() {
  const currentScenario = scenario();
  const controls = currentScenario.release_options.map(option => {
    const id = `release-${option.id}`;
    return `
      <label class="choice" for="${id}">
        <input id="${id}" type="radio" name="release" value="${esc(option.id)}" ${state.release_id === option.id ? 'checked' : ''}>
        <span>${esc(option.label)}</span>
      </label>`;
  }).join('');
  panel('Public release posture', `
    <p>Choose the public posture. No score, verdict, or safer answer is shown before commitment.</p>
    <fieldset><legend>Release choice</legend>${controls}</fieldset>
    <div class="actions">${button('Back', 'back-authenticity', true)}${button('Continue', 'continue-release', false, !state.release_id)}</div>`);
}

function actions() {
  const currentScenario = scenario();
  const cost = actionCosts(currentScenario, state.actions);
  const valid = actionPlanValid(currentScenario, state.actions);
  const controls = Object.keys(actionLabels).map(key => {
    const itemCost = currentScenario.action_costs[key];
    const id = `action-${key}`;
    return `
      <label class="choice" for="${id}">
        <input id="${id}" type="checkbox" data-action-choice="${key}" ${state.actions[key] ? 'checked' : ''}>
        <span><strong>${esc(actionLabels[key])}</strong><br>Action-plan capacity cost: time ${itemCost.time}; authority ${itemCost.authority}</span>
      </label>`;
  }).join('');
  panel('Governance action plan', `
    <p>Select a feasible plan. Scores and doctrine points remain hidden before commitment.</p>
    <p class="status ${valid ? '' : 'error'}">Action-plan capacity: time ${cost.time}/${currentScenario.action_budget.time}; authority ${cost.authority}/${currentScenario.action_budget.authority}. ${valid ? 'Within budget.' : 'Plan exceeds budget.'}</p>
    ${facilitatorActionContext(currentScenario)}
    <fieldset><legend>Actions</legend>${controls}</fieldset>
    <div class="actions">${button('Back', 'back-release', true)}${button('Continue to final review', 'continue-actions', false, !valid)}</div>`);
}

function review() {
  const currentScenario = scenario();
  const releaseChoice = currentScenario.release_options.find(option => option.id === state.release_id);
  const chosen = Object.entries(state.actions).filter(([, selected]) => selected).map(([key]) => actionLabels[key]);
  panel('Final human review', `
    <p>Review the current package. Any later material change invalidates confirmation.</p>
    <dl>
      <dt>Evidence</dt><dd>${state.reviewed.length}/${currentScenario.evidence_cards.length} reviewed</dd>
      <dt>Confidence</dt><dd>${esc(state.confidence)}</dd>
      <dt>Corroboration</dt><dd>${esc(state.corroboration)}</dd>
      <dt>Authenticity</dt><dd>${esc(state.authenticity)}</dd>
      <dt>Release posture</dt><dd>${esc(releaseChoice?.label || '')}</dd>
      <dt>Actions</dt><dd>${chosen.length ? chosen.map(esc).join('; ') : 'None selected'}</dd>
    </dl>
    <label class="choice" for="human-confirm">
      <input id="human-confirm" type="checkbox" ${state.human_confirmation ? 'checked' : ''}>
      <span><strong>I confirm this exact fictional decision package after review.</strong></span>
    </label>
    <p class="status">${state.human_confirmation ? `Confirmed digest: ${esc(state.confirmed_digest.slice(0, 16))}…` : 'Decision incomplete: human confirmation required.'}</p>
    <div class="actions">${button('Back to actions', 'back-actions', true)}${button('Commit decision', 'commit', false, !state.human_confirmation || committing, 'commit-button')}</div>`);
}

function indicator(label, value, description) {
  const rounded = Math.round(Number(value));
  return `
    <div class="indicator">
      <div class="indicator-row"><strong>${esc(label)}</strong><span>${rounded}/100</span></div>
      <meter min="0" max="100" value="${rounded}" aria-label="${esc(label)}: ${rounded} out of 100. ${esc(description)}">${rounded} out of 100</meter>
      <p>${esc(description)}</p>
    </div>`;
}

function diagnosticCards(diagnostics) {
  const names = {
    flagged: 'Contradiction or manipulation risk',
    sensitive: 'Civilian or identity sensitivity',
    follow_up: 'Follow-up requirement',
    used: 'Use in final assessment',
  };
  return Object.entries(diagnostics).map(([key, values]) => `
    <article class="diagnostic-card">
      <h4>${esc(names[key] || key)}</h4>
      <dl class="metric-list">
        <div><dt>Correctly identified</dt><dd>${values.tp}</dd></div>
        <div><dt>Risks missed</dt><dd>${values.fn}</dd></div>
        <div><dt>Unsupported markings</dt><dd>${values.fp}</dd></div>
      </dl>
      <details class="technical-details">
        <summary>Technical metrics</summary>
        <dl class="metric-list">
          <div><dt>Precision</dt><dd>${Math.round(values.precision * 100)}%</dd></div>
          <div><dt>Recall</dt><dd>${Math.round(values.recall * 100)}%</dd></div>
          <div><dt>Specificity</dt><dd>${Math.round(values.specificity * 100)}%</dd></div>
        </dl>
      </details>
    </article>`).join('');
}

function whatWentWell(resultRecord) {
  const items = ['All evidence cards were reviewed before scoring.'];
  if (resultRecord.breakdown.evidence_marking >= 18) items.push('Evidence markings showed strong discrimination between supported and unsupported risks.');
  else if (resultRecord.breakdown.evidence_marking >= 10) items.push('Evidence markings met the minimum credible-analysis floor.');
  if (resultRecord.breakdown.release === 15) items.push('The selected public posture disclosed uncertainty without premature attribution.');
  if (resultRecord.breakdown.actions >= 12) items.push('The governance plan used the available time and authority effectively.');
  return items.map(item => `<li>${esc(item)}</li>`).join('');
}

function recommendedCorrection(resultRecord, currentScenario) {
  if (resultRecord.label === 'Excellent governance discipline') {
    return 'Preserve the reasoning trace, identify the remaining uncertainties, and compare the decision with an independent reviewer.';
  }
  const actionsList = currentScenario.recommended_actions.map(key => actionLabels[key]).join('; ');
  return `Revisit evidence markings before increasing certainty. Compare the release posture with the scenario's controlled-language options and consider this bounded action set: ${actionsList}.`;
}

function result() {
  const record = state.result;
  const currentScenario = scenario();
  const cost = actionCosts(currentScenario, record.decision.actions);
  const releaseChoice = currentScenario.release_options.find(option => option.id === record.decision.release_id);
  const selectedActions = Object.entries(record.decision.actions).filter(([, selected]) => selected).map(([key]) => actionLabels[key]);
  const componentRows = Object.entries(record.breakdown).map(([key, value]) => `<div><dt>${esc(key.replaceAll('_', ' '))}</dt><dd>${value}</dd></div>`).join('');

  panel('After-action review', `
    <p class="success">Decision committed. Results were not available before commitment.</p>
    <p><strong>Score:</strong> ${record.score}/100<br><strong>Bounded label:</strong> ${esc(record.label)}</p>

    <h3>What went well</h3>
    <ul>${whatWentWell(record)}</ul>

    <h3>Evidence analysis</h3>
    <p>The result distinguishes supported findings, missed risks, and unsupported markings. These are authored learning metrics, not professional certification results.</p>
    <details class="technical-details">
      <summary>View evidence diagnostics</summary>
      <div class="diagnostic-grid">${diagnosticCards(record.diagnostics)}</div>
    </details>

    <h3>Evidence judgment and public posture</h3>
    <dl>
      <dt>Confidence</dt><dd>${esc(record.decision.confidence)}</dd>
      <dt>Corroboration</dt><dd>${esc(record.decision.corroboration)}</dd>
      <dt>Authenticity</dt><dd>${esc(record.decision.authenticity)}</dd>
      <dt>Public release posture</dt><dd>${esc(releaseChoice?.label || '')}</dd>
    </dl>

    <h3>Civilian protection and information integrity</h3>
    <div class="indicator-list">
      ${indicator('Evidence Integrity', record.indicators.evidence_integrity, 'Higher indicates better preservation of evidence quality and uncertainty boundaries.')}
      ${indicator('Escalation Control', record.indicators.escalation_control, 'Higher indicates stronger de-escalation and reduced avoidable escalation risk.')}
      ${indicator('Civilian Protection', record.indicators.civilian_protection, 'Higher indicates stronger protection of civilians and sensitive identities.')}
      ${indicator('Institutional Credibility', record.indicators.institutional_credibility, 'Higher indicates stronger alignment between claims, authority, and evidence.')}
      ${indicator('Decision Timeliness', record.indicators.decision_timeliness, 'Higher indicates more time remained when the bounded decision was committed.')}
    </div>
    <p><strong>Scenario state:</strong> Public Pressure ${record.indicators.public_pressure}/100. This is context, not a performance score.</p>

    <h3>Action plan</h3>
    <p>${selectedActions.length ? selectedActions.map(esc).join('; ') : 'No actions selected.'}</p>
    <p>Action-plan capacity used: time ${cost.time}/${currentScenario.action_budget.time}; authority ${cost.authority}/${currentScenario.action_budget.authority}.</p>

    <h3>Recommended correction</h3>
    <p>${esc(recommendedCorrection(record, currentScenario))}</p>

    <details class="technical-details">
      <summary>Score breakdown</summary>
      <dl class="metric-list score-breakdown">${componentRows}</dl>
    </details>

    ${facilitatorNotes(currentScenario, 'result')}

    <p class="identity-note">This is a fictional learning result, not an operational, legal, attribution, certification, or emergency-response decision.</p>
    <details class="technical-details">
      <summary>Technical decision record</summary>
      <p><strong>Decision fingerprint</strong> (technical digest): <code>${esc(record.digest)}</code></p>
      <p>This fingerprint uniquely represents the choices in this committed decision package.</p>
      <p>The record is local, unsigned, and not independently anchored. It does not independently prove who made the decision or when.</p>
    </details>

    ${copyFallbackText ? `<div class="fallback-copy"><label for="copy-fallback"><strong>Manual copy fallback</strong></label><textarea id="copy-fallback" rows="4" readonly>${esc(copyFallbackText)}</textarea></div>` : ''}
    <div class="actions">
      ${button('Download After-Action Review Record', 'download-aar', false, false, 'download-aar-button')}
      ${button('Copy summary', 'copy-summary', true, false, 'copy-summary-button')}
      ${button('Print AAR', 'print', true, false, 'print-aar-button')}
      ${button('Start another session', 'restart', true, false, 'restart-button')}
    </div>`);
}

async function commit(buttonElement) {
  if (committing) return;
  committing = true;
  if (buttonElement) buttonElement.disabled = true;
  announce('Committing the confirmed decision package.');
  try {
    const digest = await decisionDigest();
    if (!state.human_confirmation || digest !== state.confirmed_digest) {
      state.human_confirmation = false;
      state.confirmed_digest = '';
      save();
      announce('Decision changed after confirmation. Review and confirm again.');
      render();
      return;
    }
    const decision = decisionForScore();
    const breakdown = scoreBreakdown(scenario(), decision);
    const score = totalScore(scenario(), decision, rubric);
    const label = performanceLabel(scenario(), decision, rubric);
    const diagnostics = markingDiagnostics(scenario(), state.marks);
    const indicators = computeOutcomeIndicators(scenario(), decision);
    indicators.public_pressure = state.public_pressure;
    state.committed = true;
    state.result = {
      schema_version: '1.0',
      product: PRODUCT_NAME,
      version: APP_VERSION,
      scenario_id: state.scenario_id,
      mode: state.mode,
      committed_at_utc: new Date().toISOString(),
      score,
      label,
      breakdown,
      diagnostics,
      indicators,
      digest,
      decision: decisionInput(),
      limitations: [
        'Fictional authored model',
        'Local unsigned record',
        'Not operational, legal, attribution, certification, or professional validation',
      ],
    };
    state.screen = 'result';
    save();
    announce(`Decision committed. Score ${score}. ${label}.`);
    render();
  } finally {
    committing = false;
  }
}

function summaryText() {
  return `${PRODUCT_NAME}: ${state.result.score}/100 | ${state.result.label} | ${state.result.digest}`;
}

async function copySummary() {
  const text = summaryText();
  try {
    if (!navigator.clipboard?.writeText) throw new Error('Clipboard API is unavailable.');
    await navigator.clipboard.writeText(text);
    copyFallbackText = '';
    visibleActionMessage = 'Summary copied to the clipboard.';
    pendingFocusId = 'copy-summary-button';
    announce(visibleActionMessage);
    render();
  } catch (error) {
    copyFallbackText = text;
    visibleActionMessage = 'Clipboard access was denied or unavailable. Use the manual copy field below, download the JSON, or print the AAR.';
    pendingFocusId = 'copy-fallback';
    announce(visibleActionMessage);
    render();
    requestAnimationFrame(() => $('#copy-fallback')?.select());
  }
}

function download() {
  let objectUrl = '';
  try {
    if (!state.result) throw new Error('No committed AAR is available.');
    if (!URL?.createObjectURL) throw new Error('Browser download support is unavailable.');
    const timestamp = (state.result.committed_at_utc || new Date().toISOString()).replace(/[:.]/g, '-');
    const digestPrefix = state.result.digest.slice(0, 12);
    const filename = `peace-os-crisis-room-aar-${state.scenario_id}-${timestamp}-${digestPrefix}.json`;
    const blob = new Blob([`${JSON.stringify(state.result, null, 2)}\n`], { type: 'application/json' });
    const anchor = document.createElement('a');
    objectUrl = URL.createObjectURL(blob);
    anchor.href = objectUrl;
    anchor.download = filename;
    anchor.hidden = true;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    visibleActionMessage = `AAR download prepared as ${filename}.`;
    pendingFocusId = 'download-aar-button';
    announce(visibleActionMessage);
    render();
  } catch (error) {
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    visibleActionMessage = 'AAR download failed. Use Copy summary or Print AAR as a fallback.';
    pendingFocusId = 'download-aar-button';
    announce(visibleActionMessage);
    render();
  }
}

function startFreshSession() {
  clearSaved();
  savedCandidate = null;
  state = blank();
  copyFallbackText = '';
  pendingFocusId = 'screen-heading';
  render();
}

function requestDeleteSavedSession(returnScreen = state.screen) {
  deleteReturnScreen = returnScreen || 'start';
  state.screen = 'delete_confirm';
  pendingFocusId = 'screen-heading';
  render();
}

function deleteConfirm() {
  panel('Delete saved session?', `
    <p>This deletes only the session stored by this browser. It does not delete AAR files already downloaded to the device.</p>
    <div class="actions">
      ${button('Cancel', 'cancel-delete', true)}
      ${button('Delete saved session', 'confirm-delete')}
    </div>`);
}

function wire() {
  main.querySelectorAll('[data-action]').forEach(element => element.addEventListener('click', async () => {
    const action = element.dataset.action;
    if (action === 'resume-saved') {
      state = savedCandidate;
      savedCandidate = null;
      save();
      announce('Saved session resumed.');
      return render();
    }
    if (action === 'start-new') {
      startFreshSession();
      announce('New session started.');
      return;
    }
    if (action === 'delete-saved') return requestDeleteSavedSession('resume');
    if (action === 'cancel-delete') {
      state.screen = deleteReturnScreen;
      pendingFocusId = 'screen-heading';
      return render();
    }
    if (action === 'confirm-delete') {
      clearSaved();
      savedCandidate = null;
      state = blank();
      announce('Saved session deleted. Downloaded AAR files were not changed.');
      return render();
    }
    if (action === 'continue-start') return setState({ screen: 'boundary' });
    if (action === 'back-start') return setState({ screen: 'start' });
    if (action === 'continue-boundary') return setState({ screen: 'briefing' });
    if (action === 'back-boundary') return setState({ screen: 'boundary' });
    if (action === 'open-evidence') return setState({ screen: 'evidence' });
    if (action === 'back-evidence') return setState({ screen: 'evidence' }, '', `open-card-${state.card_id}`);
    if (action === 'back-briefing') return setState({ screen: 'briefing' });
    if (action.startsWith('card:')) {
      const id = action.split(':')[1];
      if (!state.reviewed.includes(id)) {
        state.reviewed.push(id);
        consumeTime('evidence', id);
      }
      state.card_id = id;
      state.screen = 'card';
      invalidate('evidence review changed');
      save();
      return render();
    }
    if (action === 'continue-evidence' || action === 'back-confidence') return setState({ screen: 'confidence' });
    if (action === 'continue-confidence' || action === 'back-corroboration') return setState({ screen: 'corroboration' });
    if (action === 'continue-corroboration' || action === 'back-authenticity') return setState({ screen: 'authenticity' });
    if (action === 'continue-authenticity' || action === 'back-release') return setState({ screen: 'release' });
    if (action === 'continue-release' || action === 'back-actions') return setState({ screen: 'actions' });
    if (action === 'continue-actions') return setState({ screen: 'review' });
    if (action === 'commit') return commit(element);
    if (action === 'download-aar') return download();
    if (action === 'copy-summary') return copySummary();
    if (action === 'print') return window.print();
    if (action === 'restart') return startFreshSession();
  }));

  main.querySelectorAll('input[name="mode"]').forEach(input => input.addEventListener('change', event => {
    setState({ mode: event.target.value }, 'mode changed', event.target.id);
  }));

  main.querySelectorAll('input[name="scenario"]').forEach(input => input.addEventListener('change', event => {
    const selectedMode = document.querySelector('input[name="mode"]:checked')?.value || state.mode || '';
    state = blank();
    state.mode = selectedMode;
    state.scenario_id = event.target.value;
    state.remaining_minutes = scenarios[event.target.value].decision_clock_minutes;
    state.public_pressure = scenarios[event.target.value].starting_meters.public_pressure;
    pendingFocusId = event.target.id;
    save();
    render();
  }));

  main.querySelectorAll('[data-mark]').forEach(input => input.addEventListener('change', event => {
    const id = state.card_id;
    state.marks[id] ??= Object.fromEntries(MARK_NAMES.map(key => [key, false]));
    state.marks[id][event.target.dataset.mark] = event.target.checked;
    invalidate('evidence marking changed');
    pendingFocusId = event.target.id;
    save();
    render();
  }));

  for (const key of ['confidence', 'corroboration', 'authenticity']) {
    main.querySelectorAll(`input[name="${key}"]`).forEach(input => input.addEventListener('change', event => {
      if (key === 'confidence' && !state.confidence) consumeTime('confidence');
      setState({ [key]: event.target.value }, `${key} changed`, event.target.id);
    }));
  }

  main.querySelectorAll('input[name="release"]').forEach(input => input.addEventListener('change', event => {
    if (!state.release_id) consumeTime('release');
    setState({ release_id: event.target.value }, 'release posture changed', event.target.id);
  }));

  main.querySelectorAll('[data-action-choice]').forEach(input => input.addEventListener('change', event => {
    state.actions[event.target.dataset.actionChoice] = event.target.checked;
    invalidate('governance action changed');
    pendingFocusId = event.target.id;
    save();
    render();
  }));

  $('#human-confirm')?.addEventListener('change', async event => {
    state.human_confirmation = event.target.checked;
    state.confirmed_digest = event.target.checked ? await decisionDigest() : '';
    pendingFocusId = 'human-confirm';
    save();
    render();
  });
}

async function init() {
  detectStorage();
  const index = await fetch('./data/scenarios/index.json').then(response => response.json());
  for (const item of index.scenarios) {
    scenarios[item.id] = await fetch(`./data/scenarios/${item.file}`).then(response => response.json());
  }
  rubric = await fetch('./data/scoring/scoring_rubric.json').then(response => response.json());
  language = await fetch('./data/release_language/controlled_language.json').then(response => response.json());

  const saved = loadSaved();
  if (savedStateValid(saved) && (!saved.scenario_id || scenarios[saved.scenario_id])) {
    savedCandidate = saved;
    state = blank();
    state.screen = 'resume';
  } else {
    if (saved) clearSaved();
    state = blank();
  }
  render();
  updateDeleteButton();
  if (!storageAvailable) announce('Browser storage is unavailable. The session will continue in memory only.');

  if (new URLSearchParams(location.search).has('selftest')) {
    document.documentElement.dataset.selftest = Object.keys(scenarios).length === 2 && rubric.credible_gate ? 'pass' : 'fail';
  }
}

$('#delete-session').addEventListener('click', () => requestDeleteSavedSession(state.screen));

init().catch(error => {
  main.innerHTML = `<section class="panel"><h2>Unable to load simulation</h2><p class="error">${esc(error.message)}</p></section>`;
  console.error(error);
});
