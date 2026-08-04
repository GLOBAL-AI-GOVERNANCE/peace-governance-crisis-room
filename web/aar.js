import { actionCosts } from './scoring.js';

export function buildAarRecord({ metadata, policy, scenario, state, decision, breakdown, score, label, diagnostics, indicators, digest, auditEvents, auditValid, committedAt }) {
  const record = {
    schema_version: metadata.aar_schema_version,
    record_id: `aar-${state.session_id}-${digest.slice(0, 12)}`,
    product_name: metadata.product_name,
    product_version: metadata.product_version,
    application_version: metadata.application_version,
    policy_version: metadata.policy_version,
    scoring_version: metadata.scoring_version,
    scenario_id: scenario.scenario_id,
    scenario_version: scenario.version,
    mode: state.mode,
    session_id: state.session_id,
    started_at: state.started_at,
    committed_at: committedAt,
    decision_record: decision,
    score,
    score_breakdown: breakdown,
    performance_label: label,
    governance_indicators: indicators,
    evidence_diagnostics: diagnostics,
    decision_digest: digest,
    confirmed_digest: state.confirmed_digest,
    digest_algorithm: metadata.digest_algorithm,
    canonicalization_version: metadata.canonicalization_version,
    human_final_confirmation: state.human_confirmation,
    audit_events: auditEvents,
    audit_chain_valid: auditValid,
    audit_limit: policy.audit_limit,
    action_budget: scenario.action_budget,
    action_costs: actionCosts(scenario, decision.actions),
    limitations: [
      'Fictional authored learning model',
      'Local unsigned record',
      'Not identity-authenticated or independently timestamped',
      'Not externally anchored and not proof of real-world activity',
      'Not operational, legal, attribution, certification, or professional validation',
    ],
  };
  assertAarRecord(record, metadata);
  return record;
}

export function assertAarRecord(record, metadata) {
  const required = [
    'schema_version','record_id','product_name','product_version','application_version',
    'policy_version','scoring_version','scenario_id','scenario_version','mode',
    'session_id','started_at','committed_at','decision_record','score','score_breakdown',
    'performance_label','governance_indicators','evidence_diagnostics','confirmed_digest',
    'decision_digest','digest_algorithm','canonicalization_version',
    'human_final_confirmation','audit_events','audit_chain_valid','audit_limit',
    'action_budget','action_costs','limitations',
  ];
  for (const key of required) if (!(key in record)) throw new Error(`AAR record is missing ${key}.`);
  if (record.schema_version !== metadata.aar_schema_version) throw new Error('AAR schema version mismatch.');
  if (record.product_version !== metadata.product_version || record.policy_version !== metadata.policy_version || record.scoring_version !== metadata.scoring_version) throw new Error('AAR metadata versions do not match the release contract.');
  if (!['practice','assessment','facilitator'].includes(record.mode)) throw new Error('AAR mode is invalid.');
  if (!/^[0-9a-f]{64}$/.test(record.decision_digest) || record.decision_digest !== record.confirmed_digest) throw new Error('AAR decision digest is invalid or unconfirmed.');
  if (!record.human_final_confirmation || !record.audit_chain_valid || !Array.isArray(record.audit_events) || record.audit_events.length === 0) throw new Error('AAR confirmation or audit contract is incomplete.');
  if (!Array.isArray(record.limitations) || record.limitations.length < 4) throw new Error('AAR limitations are incomplete.');
  return true;
}
