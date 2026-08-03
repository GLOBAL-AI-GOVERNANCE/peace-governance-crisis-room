from __future__ import annotations

import itertools
import random
import unittest

from scoring_model_reference import (
    AUTHENTICITY_LEVELS,
    CONFIDENCE_LEVELS,
    CORROBORATION_LEVELS,
    Decision,
    action_plan_valid,
    actions_score,
    blank_marks,
    expected_marks,
    ideal_decision,
    load_scenarios,
    marking_diagnostics,
    marking_score,
    performance_label,
    total_score,
)


class ScoringContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scenarios = load_scenarios()

    def test_ideal_path_reaches_100_in_each_scenario(self) -> None:
        for scenario in self.scenarios.values():
            self.assertEqual(total_score(scenario, ideal_decision(scenario)), 100)

    def test_all_evidence_is_required(self) -> None:
        for scenario in self.scenarios.values():
            decision = ideal_decision(scenario)
            incomplete = Decision(
                reviewed_count=len(scenario["evidence_cards"]) - 1,
                marks=decision.marks,
                confidence_history=decision.confidence_history,
                corroboration_history=decision.corroboration_history,
                authenticity_history=decision.authenticity_history,
                release_id=decision.release_id,
                actions=decision.actions,
                remaining_minutes=decision.remaining_minutes,
            )
            with self.assertRaises(ValueError):
                total_score(scenario, incomplete)

    def test_human_confirmation_is_required(self) -> None:
        for scenario in self.scenarios.values():
            decision = ideal_decision(scenario)
            unconfirmed = Decision(
                reviewed_count=decision.reviewed_count,
                marks=decision.marks,
                confidence_history=decision.confidence_history,
                corroboration_history=decision.corroboration_history,
                authenticity_history=decision.authenticity_history,
                release_id=decision.release_id,
                actions=decision.actions,
                remaining_minutes=decision.remaining_minutes,
                human_confirmation=False,
            )
            with self.assertRaises(ValueError):
                total_score(scenario, unconfirmed)

    def test_marking_is_chance_corrected(self) -> None:
        for scenario in self.scenarios.values():
            self.assertEqual(marking_score(scenario, expected_marks(scenario)), 20)
            self.assertEqual(marking_score(scenario, blank_marks(scenario, True)), 0)
            self.assertEqual(marking_score(scenario, blank_marks(scenario, False)), 0)

    def test_marking_categories_have_positive_and_negative_examples(self) -> None:
        for scenario in self.scenarios.values():
            diagnostics = marking_diagnostics(scenario, expected_marks(scenario))
            for category in diagnostics.values():
                self.assertGreater(category["tp"] + category["fn"], 0)
                self.assertGreater(category["tn"] + category["fp"], 0)

    def test_credible_label_requires_evidence_floor(self) -> None:
        for scenario in self.scenarios.values():
            ideal = ideal_decision(scenario)
            no_skill = Decision(
                reviewed_count=ideal.reviewed_count,
                marks=blank_marks(scenario, False),
                confidence_history=ideal.confidence_history,
                corroboration_history=ideal.corroboration_history,
                authenticity_history=ideal.authenticity_history,
                release_id=ideal.release_id,
                actions=ideal.actions,
                remaining_minutes=ideal.remaining_minutes,
            )
            self.assertEqual(marking_score(scenario, no_skill.marks), 0)
            self.assertEqual(total_score(scenario, no_skill), 74)
            self.assertEqual(performance_label(scenario, no_skill), "Mixed outcome")

    def test_random_marking_does_not_average_excellent(self) -> None:
        rng = random.Random(333)
        for scenario in self.scenarios.values():
            scores = []
            for _ in range(5000):
                marks = {
                    card["id"]: {
                        name: bool(rng.getrandbits(1))
                        for name in ("flagged", "sensitive", "follow_up", "used")
                    }
                    for card in scenario["evidence_cards"]
                }
                decision = ideal_decision(scenario)
                randomized = Decision(
                    reviewed_count=decision.reviewed_count,
                    marks=marks,
                    confidence_history=decision.confidence_history,
                    corroboration_history=decision.corroboration_history,
                    authenticity_history=decision.authenticity_history,
                    release_id=decision.release_id,
                    actions=decision.actions,
                    remaining_minutes=decision.remaining_minutes,
                )
                scores.append(total_score(scenario, randomized))
            self.assertLess(sum(scores) / len(scores), 86.0)
            self.assertLess(sum(score >= 90 for score in scores) / len(scores), 0.10)

    def test_random_marking_cannot_earn_excellent_without_marking_gate(self) -> None:
        rng = random.Random(777)
        for scenario in self.scenarios.values():
            excellent = 0
            for _ in range(10000):
                marks = {
                    card["id"]: {
                        name: bool(rng.getrandbits(1))
                        for name in ("flagged", "sensitive", "follow_up", "used")
                    }
                    for card in scenario["evidence_cards"]
                }
                ideal = ideal_decision(scenario)
                randomized = Decision(
                    reviewed_count=ideal.reviewed_count,
                    marks=marks,
                    confidence_history=ideal.confidence_history,
                    corroboration_history=ideal.corroboration_history,
                    authenticity_history=ideal.authenticity_history,
                    release_id=ideal.release_id,
                    actions=ideal.actions,
                    remaining_minutes=ideal.remaining_minutes,
                )
                excellent += performance_label(scenario, randomized) == "Excellent governance discipline"
            self.assertLessEqual(excellent, 5)

    def test_displayed_score_and_label_cannot_contradict(self) -> None:
        for scenario in self.scenarios.values():
            ideal = ideal_decision(scenario)
            all_true = {
                card["id"]: {
                    name: True
                    for name in ("flagged", "sensitive", "follow_up", "used")
                }
                for card in scenario["evidence_cards"]
            }
            blind = Decision(
                reviewed_count=ideal.reviewed_count,
                marks=all_true,
                confidence_history=ideal.confidence_history,
                corroboration_history=ideal.corroboration_history,
                authenticity_history=ideal.authenticity_history,
                release_id=ideal.release_id,
                actions=ideal.actions,
                remaining_minutes=ideal.remaining_minutes,
            )
            score = total_score(scenario, blind)
            label = performance_label(scenario, blind)
            self.assertLess(score, 90)
            self.assertNotEqual(label, "Excellent governance discipline")
            self.assertEqual(score >= 90, label == "Excellent governance discipline")

    def test_clean_and_self_corrected_judgements_receive_same_final_score(self) -> None:
        for scenario in self.scenarios.values():
            clean = ideal_decision(scenario)
            corrected = Decision(
                reviewed_count=clean.reviewed_count,
                marks=clean.marks,
                confidence_history=(scenario["unsafe_choices"][0], clean.final_confidence),
                corroboration_history=(scenario["unsafe_corroboration_choices"][0], clean.final_corroboration),
                authenticity_history=(scenario["unsafe_authenticity_choices"][0], clean.final_authenticity),
                release_id=clean.release_id,
                actions=clean.actions,
                remaining_minutes=clean.remaining_minutes,
            )
            self.assertEqual(total_score(scenario, clean), total_score(scenario, corrected))

    def test_select_all_actions_is_invalid(self) -> None:
        for scenario in self.scenarios.values():
            all_actions = {name: True for name in scenario["action_scores"]}
            self.assertFalse(action_plan_valid(scenario, all_actions))
            with self.assertRaises(ValueError):
                actions_score(scenario, all_actions)

    def test_recommended_action_plan_is_valid_and_reaches_maximum(self) -> None:
        for scenario in self.scenarios.values():
            actions = {name: name in scenario["recommended_actions"] for name in scenario["action_scores"]}
            self.assertTrue(action_plan_valid(scenario, actions))
            self.assertEqual(actions_score(scenario, actions), 15)

    def test_action_score_is_monotonic_within_budget(self) -> None:
        for scenario in self.scenarios.values():
            names = list(scenario["action_scores"])
            for bits in itertools.product((False, True), repeat=len(names)):
                current = dict(zip(names, bits))
                if not action_plan_valid(scenario, current):
                    continue
                current_score = actions_score(scenario, current)
                for name in names:
                    if current[name]:
                        continue
                    improved = dict(current)
                    improved[name] = True
                    if action_plan_valid(scenario, improved):
                        self.assertGreaterEqual(actions_score(scenario, improved), current_score)

    def test_exhaustive_epistemic_release_action_space_stays_bounded(self) -> None:
        for scenario in self.scenarios.values():
            ideal = ideal_decision(scenario)
            action_names = list(scenario["action_scores"])
            for confidence in CONFIDENCE_LEVELS:
                for corroboration in CORROBORATION_LEVELS:
                    for authenticity in AUTHENTICITY_LEVELS:
                        for option in scenario["release_options"]:
                            for bits in itertools.product((False, True), repeat=len(action_names)):
                                selected = dict(zip(action_names, bits))
                                if not action_plan_valid(scenario, selected):
                                    continue
                                decision = Decision(
                                    reviewed_count=ideal.reviewed_count,
                                    marks=ideal.marks,
                                    confidence_history=(confidence,),
                                    corroboration_history=(corroboration,),
                                    authenticity_history=(authenticity,),
                                    release_id=option["id"],
                                    actions=selected,
                                    remaining_minutes=14,
                                )
                                score = total_score(scenario, decision)
                                self.assertGreaterEqual(score, 0)
                                self.assertLessEqual(score, 100)

    def test_overclaim_cannot_outscore_safe_release(self) -> None:
        for scenario in self.scenarios.values():
            ideal = ideal_decision(scenario)
            unsafe = Decision(
                reviewed_count=ideal.reviewed_count,
                marks=ideal.marks,
                confidence_history=(scenario["unsafe_choices"][0],),
                corroboration_history=(scenario["unsafe_corroboration_choices"][0],),
                authenticity_history=(scenario["unsafe_authenticity_choices"][0],),
                release_id="overclaim",
                actions=ideal.actions,
                remaining_minutes=ideal.remaining_minutes,
            )
            self.assertLess(total_score(scenario, unsafe), total_score(scenario, ideal))


if __name__ == "__main__":
    unittest.main()
