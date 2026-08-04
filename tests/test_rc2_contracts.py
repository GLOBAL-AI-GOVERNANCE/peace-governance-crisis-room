import json
import unittest
from pathlib import Path
from scoring_model_reference import load_scenarios, ideal_decision, total_score, performance_label, Decision, expected_marks
ROOT=Path(__file__).resolve().parents[1]

class RC2Contracts(unittest.TestCase):
    def test_metadata_is_canonical(self):
        metadata=json.loads((ROOT/'core/release/metadata.json').read_text())
        self.assertEqual(metadata['product_version'],'0.3.0-rc2')
        self.assertEqual((ROOT/'VERSION').read_text().strip(),metadata['product_version'])
    def test_ideal_decisions_remain_top_band(self):
        for scenario in load_scenarios().values():
            decision=ideal_decision(scenario)
            self.assertEqual(total_score(scenario,decision),100)
            self.assertEqual(performance_label(scenario,decision),'Strong doctrine alignment')
    def test_weak_actions_cannot_receive_top_band(self):
        for scenario in load_scenarios().values():
            ideal=ideal_decision(scenario)
            weak={key:False for key in scenario['action_scores']}
            weak['protect_civilians']=True
            decision=Decision(ideal.reviewed_count,expected_marks(scenario),ideal.confidence_history,ideal.corroboration_history,ideal.authenticity_history,ideal.release_id,weak,ideal.remaining_minutes,True)
            self.assertLess(total_score(scenario,decision),90)
            self.assertNotEqual(performance_label(scenario,decision),'Strong doctrine alignment')
    def test_family_follow_up_is_consistent(self):
        scenario=load_scenarios()['scenario_02_deepfake_distress_call']
        card=next(c for c in scenario['evidence_cards'] if c['id']=='family_01')
        self.assertTrue(card['expected_marks']['follow_up'])
        self.assertIn('Requires Follow-Up',card['facilitator_indicators'])
        self.assertNotEqual(card['reliability'],'sensitive')

if __name__=='__main__': unittest.main()
