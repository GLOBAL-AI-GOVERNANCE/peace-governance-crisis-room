from __future__ import annotations
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MARKS=("flagged","sensitive","follow_up","used")

class PolicyDataContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=json.loads((ROOT/'game/data/governance/policy.json').read_text())
        cls.rubric=json.loads((ROOT/'game/data/scoring/scoring_rubric.json').read_text())
        cls.scenarios=[json.loads(p.read_text()) for p in sorted((ROOT/'game/data/scenarios').glob('*.json'))]

    def test_policy_and_rubric_component_weights_match(self):
        self.assertEqual(self.policy['required_score_components'], self.rubric['score_components'])
        self.assertEqual(sum(self.policy['required_score_components'].values()),100)
        self.assertEqual(len(self.policy['required_score_components']),8)

    def test_mandatory_safeguards_are_strict_true(self):
        for key in ('simulation_only','require_human_final_confirmation','require_complete_evidence_review','require_in_memory_audit_chain','require_action_budget','require_final_review_screen'):
            self.assertIs(self.policy[key],True)

    def test_prohibited_capabilities_are_strict_false(self):
        for key in ('allow_live_data','allow_autonomous_release','allow_external_action_execution'):
            self.assertIs(self.policy[key],False)

    def test_every_scenario_has_unique_release_ids_and_bounded_action_plan(self):
        for scenario in self.scenarios:
            ids=[option['id'] for option in scenario['release_options']]
            self.assertEqual(len(ids),len(set(ids)))
            self.assertTrue(all(isinstance(v,int) and v>0 for v in scenario['action_scores'].values()))
            self.assertEqual(set(scenario['action_scores']),set(scenario['action_costs']))
            self.assertEqual(set(scenario['recommended_actions']).issubset(scenario['action_scores']),True)
            selected=scenario['recommended_actions']
            self.assertEqual(sum(scenario['action_scores'][name] for name in selected),15)
            for resource in ('time','authority'):
                self.assertLessEqual(sum(scenario['action_costs'][name][resource] for name in selected),scenario['action_budget'][resource])
                self.assertGreater(sum(scenario['action_costs'][name][resource] for name in scenario['action_scores']),scenario['action_budget'][resource])

    def test_expected_marks_are_discriminative_per_category(self):
        for scenario in self.scenarios:
            for mark in MARKS:
                values=[card['expected_marks'][mark] for card in scenario['evidence_cards']]
                self.assertIn(True,values)
                self.assertIn(False,values)

    def test_learner_data_does_not_publish_answer_labels_as_states(self):
        for scenario in self.scenarios:
            for card in scenario['evidence_cards']:
                self.assertNotIn('states',card)
                self.assertIsInstance(card.get('facilitator_indicators'),list)

if __name__=='__main__': unittest.main()
