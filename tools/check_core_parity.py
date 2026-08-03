#!/usr/bin/env python3
"""Fail if generated game/web data diverges from the authoritative core."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES=[
 'scenarios/scenario_01_viral_collision_video.json',
 'scenarios/scenario_02_deepfake_distress_call.json',
 'scoring/scoring_rubric.json',
 'governance/policy.json',
 'release_language/controlled_language.json',
]
failures=[]
for rel in FILES:
    canonical=(ROOT/'core'/rel).read_bytes()
    for base in ('game/data','web/data'):
        p=ROOT/base/rel
        if not p.is_file() or p.read_bytes()!=canonical:
            failures.append(f'{base}/{rel}')
index=ROOT/'core/scenarios/index.json'
web_index=ROOT/'web/data/scenarios/index.json'
if not web_index.is_file() or web_index.read_bytes()!=index.read_bytes(): failures.append('web/data/scenarios/index.json')
if failures: raise SystemExit('Core/client parity failed: '+', '.join(failures)+'. Run tools/sync_core_data.py')
print('Core/client parity passed.')
