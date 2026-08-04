import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { recordAuditEvent, hashAuditEvents, verifyAuditChain } from '../../web/audit.js';
import { assertAarRecord } from '../../web/aar.js';

const metadata = JSON.parse(fs.readFileSync(new URL('../../core/release/metadata.json', import.meta.url)));

test('local audit events hash-link and mutation fails verification', async () => {
  const raw = [];
  recordAuditEvent(raw, 'session_started', { application_version: '0.3.0-rc2' }, '2026-08-04T00:00:00Z');
  recordAuditEvent(raw, 'scenario_selected', { scenario_id: 'scenario_01_viral_collision_video' }, '2026-08-04T00:01:00Z');
  const chain = await hashAuditEvents(raw, '1.0');
  assert.equal(await verifyAuditChain(chain), true);
  chain[1].data.scenario_id = 'tampered';
  assert.equal(await verifyAuditChain(chain), false);
});

test('golden RC2 AAR satisfies browser contract', () => {
  const record = JSON.parse(fs.readFileSync(new URL('../fixtures/aar_golden_rc2.json', import.meta.url)));
  assert.equal(assertAarRecord(record, metadata), true);
});
