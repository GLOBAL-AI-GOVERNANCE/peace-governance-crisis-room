#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from scoring_model_reference import load_scenarios, expected_marks, blank_marks, Decision, score_breakdown, total_score, performance_label
ROOT=Path(__file__).resolve().parents[1]
vectors=[]
for sid,s in load_scenarios().items():
    actions={n:n in s['recommended_actions'] for n in s['action_scores']}
    safe=next(o['id'] for o in s['release_options'] if o['doctrine_score']==15)
    cases=[('ideal',expected_marks(s),s['correct_confidence_range'][0],s['correct_corroboration_range'][0],s['correct_authenticity_range'][0],safe),('blind',blank_marks(s),s['correct_confidence_range'][0],s['correct_corroboration_range'][0],s['correct_authenticity_range'][0],safe),('overclaim',expected_marks(s),s['unsafe_choices'][0],s['unsafe_corroboration_choices'][0],s['unsafe_authenticity_choices'][0],'overclaim')]
    for name,marks,c,co,a,r in cases:
        d=Decision(len(s['evidence_cards']),marks,(c,),(co,),(a,),r,actions,14,True)
        vectors.append({'id':f'{sid}-{name}','scenario_file':sid+'.json','decision':{'reviewed_count':d.reviewed_count,'marks':marks,'confidence':c,'corroboration':co,'authenticity':a,'release_id':r,'actions':actions,'remaining_minutes':14,'human_confirmation':True},'expected':{'breakdown':score_breakdown(s,d),'score':total_score(s,d),'label':performance_label(s,d)}})
out={'schema_version':'1.0','generated_by':'tests/generate_golden_vectors.py','vectors':vectors}
path=ROOT/'tests/fixtures/scoring_golden_vectors.json'
path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(path)
