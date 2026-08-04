#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
policy=json.loads((ROOT/'core/governance/policy.json').read_text())
actions={'protect_civilians','request_original_media','info_integrity_review','deescalation_channel','senior_review','humanitarian_check'}
indicator_map={'flagged':'Flagged','sensitive':'Sensitive','follow_up':'Requires Follow-Up'}
failures=[]
for path in sorted((ROOT/'core/scenarios').glob('scenario_*.json')):
    scenario=json.loads(path.read_text())
    ids=[c['id'] for c in scenario['evidence_cards']]
    if len(ids)!=len(set(ids)): failures.append(f'{path.name}: duplicate evidence IDs')
    if not set(scenario.get('critical_safeguards',[])).issubset(actions): failures.append(f'{path.name}: invalid safeguard')
    if set(scenario['action_scores'])!=actions or set(scenario['action_costs'])!=actions: failures.append(f'{path.name}: action registry mismatch')
    if scenario['time_step_minutes']<=0: failures.append(f'{path.name}: invalid time step')
    for value in scenario['correct_authenticity_range']+scenario['unsafe_authenticity_choices']:
        if value not in policy['allowed_authenticity_levels']: failures.append(f'{path.name}: authenticity vocabulary {value}')
    for card in scenario['evidence_cards']:
        indicators=set(card.get('facilitator_indicators',[]))
        for mark,label in indicator_map.items():
            if bool(card['expected_marks'][mark]) != (label in indicators):
                failures.append(f"{path.name}/{card['id']}: {mark} contradicts facilitator indicator")
        if card.get('reliability')=='sensitive': failures.append(f"{path.name}/{card['id']}: sensitivity used as reliability")
if failures: raise SystemExit('Scenario consistency failed:\n- '+'\n- '.join(failures))
print('Scenario consistency passed for controlled vocabularies, evidence guidance, actions, safeguards, and time semantics.')
