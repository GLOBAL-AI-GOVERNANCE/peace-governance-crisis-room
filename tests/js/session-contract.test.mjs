import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { assessSavedSession, createSession, validateSession } from '../../web/session.js';
const metadata = JSON.parse(fs.readFileSync(new URL('../../core/release/metadata.json', import.meta.url)));
const scenarios = Object.fromEntries(['scenario_01_viral_collision_video','scenario_02_deepfake_distress_call'].map(id => [id, JSON.parse(fs.readFileSync(new URL(`../../core/scenarios/${id}.json`, import.meta.url)))]));
const actions = ['protect_civilians','request_original_media','info_integrity_review','deescalation_channel','senior_review','humanitarian_check'];
const fixture = name => JSON.parse(fs.readFileSync(new URL(`../fixtures/session/${name}`, import.meta.url)));

test('new session validates', () => {
  const session = createSession(metadata, actions);
  assert.equal(validateSession(session, scenarios, metadata, actions).status, 'valid');
});
test('supported uncommitted RC1 session migrates and requires reconfirmation', () => {
  const result = assessSavedSession(fixture('rc1_uncommitted.json'), scenarios, metadata, actions);
  assert.equal(result.status, 'migrated');
  assert.equal(result.state.session_schema_version, '2.0');
  assert.equal(result.state.human_confirmation, false);
});
test('future session is retained but rejected', () => {
  assert.equal(assessSavedSession(fixture('future_version.json'), scenarios, metadata, actions).status, 'incompatible');
});
test('parseable corrupt session cannot reach scoring', () => {
  assert.equal(assessSavedSession(fixture('corrupt_reviewed.json'), scenarios, metadata, actions).status, 'invalid');
});
