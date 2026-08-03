#!/usr/bin/env python3
"""Copy authoritative core data into the Godot and semantic web clients."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
FILES=[
 'scenarios/scenario_01_viral_collision_video.json',
 'scenarios/scenario_02_deepfake_distress_call.json',
 'scoring/scoring_rubric.json',
 'governance/policy.json',
 'release_language/controlled_language.json',
]
for rel in FILES:
    source=ROOT/'core'/rel
    for base in ('game/data','web/data'):
        target=ROOT/base/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
shutil.copy2(ROOT/'core/scenarios/index.json',ROOT/'web/data/scenarios/index.json')
print('Core data synchronized to game and web clients.')
