#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
metadata=json.loads((ROOT/'core/release/metadata.json').read_text())
version=(ROOT/'VERSION').read_text().strip()
if version!=metadata['product_version'] or version!=metadata['application_version']:
    raise SystemExit('Canonical release metadata does not match VERSION')
for rel in ('web/data/release/metadata.json','game/data/release/metadata.json'):
    if (ROOT/rel).read_bytes()!=(ROOT/'core/release/metadata.json').read_bytes():
        raise SystemExit(f'Release metadata parity failed: {rel}')
for rel,key in (
 ('core/governance/policy.json','policy_version'),
 ('core/scoring/scoring_rubric.json','version'),
 ('core/scenarios/index.json','version'),
):
    if json.loads((ROOT/rel).read_text())[key]!=version:
        raise SystemExit(f'{rel} is not aligned to {version}')
for path in sorted((ROOT/'core/scenarios').glob('scenario_*.json')):
    scenario=json.loads(path.read_text())
    if scenario['version']!=metadata['scenario_versions'][scenario['scenario_id']]:
        raise SystemExit(f'{path.name} version mismatch')
print('Canonical release metadata parity passed.')
