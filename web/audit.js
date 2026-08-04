import { canonicalJson, sha256Hex } from './scoring.js';

export const AUDIT_EVENT_TYPES = Object.freeze([
  'session_started',
  'session_migrated',
  'scenario_selected',
  'mode_selected',
  'evidence_reviewed',
  'judgment_recorded',
  'release_posture_selected',
  'action_selected',
  'confirmation_created',
  'confirmation_invalidated',
  'decision_committed',
  'aar_generated',
  'session_deleted',
]);

export function recordAuditEvent(events, eventType, data = {}, occurredAt = new Date().toISOString()) {
  if (!Array.isArray(events)) throw new TypeError('Audit-event target must be an array.');
  if (!AUDIT_EVENT_TYPES.includes(eventType)) throw new Error(`Unsupported audit event: ${eventType}`);
  const event = {
    sequence: events.length + 1,
    event_type: eventType,
    occurred_at: occurredAt,
    data: structuredClone(data),
  };
  events.push(event);
  return event;
}

export async function hashAuditEvents(events, schemaVersion = '1.0') {
  let previousHash = '0'.repeat(64);
  const result = [];
  for (const raw of events) {
    const payload = {
      schema_version: schemaVersion,
      sequence: raw.sequence,
      event_type: raw.event_type,
      occurred_at: raw.occurred_at,
      data: raw.data ?? {},
      previous_hash: previousHash,
    };
    const eventHash = await sha256Hex(canonicalJson(payload));
    result.push({ ...payload, event_hash: eventHash });
    previousHash = eventHash;
  }
  return result;
}

export async function verifyAuditChain(events) {
  if (!Array.isArray(events) || events.length === 0) return false;
  let previousHash = '0'.repeat(64);
  for (let index = 0; index < events.length; index += 1) {
    const event = events[index];
    if (event.sequence !== index + 1 || event.previous_hash !== previousHash) return false;
    const payload = {
      schema_version: event.schema_version,
      sequence: event.sequence,
      event_type: event.event_type,
      occurred_at: event.occurred_at,
      data: event.data ?? {},
      previous_hash: event.previous_hash,
    };
    const expected = await sha256Hex(canonicalJson(payload));
    if (event.event_hash !== expected) return false;
    previousHash = event.event_hash;
  }
  return true;
}
