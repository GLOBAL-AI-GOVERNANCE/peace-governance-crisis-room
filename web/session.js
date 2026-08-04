export const CONFIDENCE_LEVELS = Object.freeze(['Confirmed', 'Likely', 'Possible', 'Unverified']);
export const CORROBORATION_LEVELS = Object.freeze(['Corroborated', 'Partially corroborated', 'Contradictory', 'Uncorroborated']);
export const AUTHENTICITY_LEVELS = Object.freeze(['No indicators identified', 'Manipulation suspected', 'Authenticity unclear', 'Not applicable']);
export const SCREENS = Object.freeze(['resume','start','boundary','briefing','evidence','card','confidence','corroboration','authenticity','release','actions','review','result','delete_confirm']);
export const MODES = Object.freeze(['practice','assessment','facilitator']);
const MARKS = Object.freeze(['flagged','sensitive','follow_up','used']);
const HASH = /^[0-9a-f]{64}$/;

function id() {
  if (globalThis.crypto?.randomUUID) return crypto.randomUUID();
  return `local-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function createSession(metadata, actionIds) {
  return {
    session_schema_version: metadata.session_schema_version,
    app_version: metadata.application_version,
    session_id: id(),
    started_at: new Date().toISOString(),
    screen: 'start',
    mode: '',
    scenario_id: '',
    scenario_version: '',
    card_id: '',
    reviewed: [],
    marks: {},
    confidence: '',
    corroboration: '',
    authenticity: '',
    release_id: '',
    actions: Object.fromEntries(actionIds.map(key => [key, false])),
    remaining_minutes: 30,
    public_pressure: 0,
    timed: { evidence: [], confidence: false, release: false },
    human_confirmation: false,
    confirmed_digest: '',
    committed: false,
    result: null,
    audit_events: [],
  };
}

function fail(message) { return { status: 'invalid', message }; }
function unique(values) { return Array.isArray(values) && new Set(values).size === values.length; }
function exactKeys(object, keys) { return object && typeof object === 'object' && !Array.isArray(object) && Object.keys(object).sort().join('|') === [...keys].sort().join('|'); }

export function validateSession(candidate, scenarios, metadata, actionIds) {
  if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) return fail('Saved session is not an object.');
  if (candidate.session_schema_version !== metadata.session_schema_version || candidate.app_version !== metadata.application_version) return fail('Saved session version is incompatible.');
  if (typeof candidate.session_id !== 'string' || candidate.session_id.length < 8 || !Number.isFinite(Date.parse(candidate.started_at))) return fail('Saved session identity or start time is invalid.');
  if (!SCREENS.includes(candidate.screen)) return fail('Saved session screen is invalid.');
  if (candidate.mode !== '' && !MODES.includes(candidate.mode)) return fail('Saved session mode is invalid.');
  if (!Array.isArray(candidate.audit_events) || candidate.audit_events.some((event, index) => event?.sequence !== index + 1 || typeof event.event_type !== 'string')) return fail('Saved audit events are invalid.');

  const scenario = candidate.scenario_id ? scenarios[candidate.scenario_id] : null;
  if (candidate.scenario_id && !scenario) return fail('Saved scenario does not exist.');
  if (scenario && candidate.scenario_version !== scenario.version) return fail('Saved scenario version is incompatible.');
  if (!scenario && candidate.scenario_version !== '') return fail('Saved scenario version is inconsistent.');
  if (!scenario && !['start','resume','delete_confirm'].includes(candidate.screen)) return fail('Saved screen requires a selected scenario.');

  const evidenceIds = scenario ? scenario.evidence_cards.map(card => card.id) : [];
  const evidenceSet = new Set(evidenceIds);
  if (!unique(candidate.reviewed) || candidate.reviewed.some(value => !evidenceSet.has(value))) return fail('Saved reviewed-evidence IDs are invalid or duplicated.');
  if (candidate.card_id && !evidenceSet.has(candidate.card_id)) return fail('Saved evidence-card ID is invalid.');
  if (!candidate.marks || typeof candidate.marks !== 'object' || Array.isArray(candidate.marks)) return fail('Saved marks are invalid.');
  for (const [evidenceId, marks] of Object.entries(candidate.marks)) {
    if (!evidenceSet.has(evidenceId) || !exactKeys(marks, MARKS) || Object.values(marks).some(value => typeof value !== 'boolean')) return fail('Saved evidence markings are invalid.');
  }

  const allowed = [
    [candidate.confidence, CONFIDENCE_LEVELS, 'confidence'],
    [candidate.corroboration, CORROBORATION_LEVELS, 'corroboration'],
    [candidate.authenticity, AUTHENTICITY_LEVELS, 'authenticity'],
  ];
  for (const [value, vocabulary, name] of allowed) if (value !== '' && !vocabulary.includes(value)) return fail(`Saved ${name} value is invalid.`);
  if (candidate.release_id && (!scenario || !scenario.release_options.some(option => option.id === candidate.release_id))) return fail('Saved release posture is invalid.');

  if (!exactKeys(candidate.actions, actionIds) || Object.values(candidate.actions).some(value => typeof value !== 'boolean')) return fail('Saved action selection is invalid.');
  if (scenario) {
    const costs = { time: 0, authority: 0 };
    for (const [name, selected] of Object.entries(candidate.actions)) {
      if (selected) {
        costs.time += Number(scenario.action_costs[name]?.time ?? 0);
        costs.authority += Number(scenario.action_costs[name]?.authority ?? 0);
      }
    }
    if (costs.time > Number(scenario.action_budget.time) || costs.authority > Number(scenario.action_budget.authority)) return fail('Saved action selection exceeds scenario capacity.');
  }
  const maximumMinutes = scenario?.decision_clock_minutes ?? 30;
  if (!Number.isInteger(candidate.remaining_minutes) || candidate.remaining_minutes < 0 || candidate.remaining_minutes > maximumMinutes) return fail('Saved time is outside scenario bounds.');
  if (!Number.isInteger(candidate.public_pressure) || candidate.public_pressure < 0 || candidate.public_pressure > 100) return fail('Saved public pressure is outside bounds.');
  if (!candidate.timed || !unique(candidate.timed.evidence) || candidate.timed.evidence.some(value => !evidenceSet.has(value)) || typeof candidate.timed.confidence !== 'boolean' || typeof candidate.timed.release !== 'boolean') return fail('Saved timing state is invalid.');

  if (typeof candidate.human_confirmation !== 'boolean' || typeof candidate.confirmed_digest !== 'string' || typeof candidate.committed !== 'boolean') return fail('Saved confirmation state is invalid.');
  if (candidate.human_confirmation !== Boolean(candidate.confirmed_digest)) return fail('Saved confirmation and digest are inconsistent.');
  if (candidate.confirmed_digest && !HASH.test(candidate.confirmed_digest)) return fail('Saved confirmation digest is invalid.');
  if (candidate.committed !== Boolean(candidate.result) || (candidate.screen === 'result') !== candidate.committed) return fail('Saved result state is inconsistent.');
  if (candidate.committed && (!candidate.human_confirmation || candidate.result?.decision_digest !== candidate.confirmed_digest)) return fail('Saved committed result is not bound to the confirmed digest.');
  return { status: 'valid', state: structuredClone(candidate), message: 'Saved session is compatible.' };
}

function migrateRc1(candidate, scenarios, metadata, actionIds) {
  if (candidate.session_schema_version !== '1.0' || candidate.app_version !== '0.3.0-rc1') return null;
  if (candidate.committed || candidate.result) return null;
  const migrated = createSession(metadata, actionIds);
  const scenario = candidate.scenario_id ? scenarios[candidate.scenario_id] : null;
  Object.assign(migrated, candidate, {
    session_schema_version: metadata.session_schema_version,
    app_version: metadata.application_version,
    session_id: typeof candidate.session_id === 'string' ? candidate.session_id : migrated.session_id,
    started_at: Number.isFinite(Date.parse(candidate.started_at)) ? candidate.started_at : migrated.started_at,
    scenario_version: scenario?.version ?? '',
    audit_events: [],
    human_confirmation: false,
    confirmed_digest: '',
    committed: false,
    result: null,
  });
  const checked = validateSession(migrated, scenarios, metadata, actionIds);
  if (checked.status !== 'valid') return null;
  return checked.state;
}

export function assessSavedSession(candidate, scenarios, metadata, actionIds) {
  if (!candidate || typeof candidate !== 'object') return { status: 'invalid', message: 'The saved session is damaged or unreadable. It was not deleted.' };
  if (candidate.session_schema_version === metadata.session_schema_version && candidate.app_version === metadata.application_version) return validateSession(candidate, scenarios, metadata, actionIds);
  const migrated = migrateRc1(candidate, scenarios, metadata, actionIds);
  if (migrated) return { status: 'migrated', state: migrated, message: 'A compatible uncommitted RC1 session was migrated to RC2. Review every decision before confirmation.' };
  return { status: 'incompatible', message: 'This saved session uses an unsupported version. It was retained but will not be reused. Delete it explicitly or start a new session.' };
}
