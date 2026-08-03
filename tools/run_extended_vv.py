#!/usr/bin/env python3
"""Run extended scoring V&V beyond the default fast validation suite.

This script exhausts every 20-bit evidence-marking pattern in both five-card
scenarios, enumerates every valid confidence/corroboration/authenticity/release/
action-plan state, and samples seeded random marking. It validates the Python
reference model only; it does not execute Godot.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import argparse
import itertools
import json
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from scoring_model_reference import (  # noqa: E402
    AUTHENTICITY_LEVELS,
    CONFIDENCE_LEVELS,
    CORROBORATION_LEVELS,
    MARK_NAMES,
    Decision,
    action_plan_valid,
    ideal_decision,
    load_scenarios,
    marking_score,
    performance_label,
    total_score,
)


def marks_from_mask(scenario, mask: int):
    marks = {}
    bit = 0
    for card in scenario["evidence_cards"]:
        row = {}
        for name in MARK_NAMES:
            row[name] = bool((mask >> bit) & 1)
            bit += 1
        marks[card["id"]] = row
    return marks


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=str(ROOT / "dist" / "extended-vv-results-v0.3.0-rc1.json"),
        help="Path for the JSON evidence record.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = {
        "schema_version": "1.0",
        "version": (ROOT / "VERSION").read_text().strip(),
        "boundary": "Python reference model only; Godot runtime not executed.",
        "scenarios": {},
    }
    rng = random.Random(333)
    for scenario_id, scenario in load_scenarios().items():
        distribution = Counter()
        bit_count = len(scenario["evidence_cards"]) * len(MARK_NAMES)
        for mask in range(1 << bit_count):
            distribution[marking_score(scenario, marks_from_mask(scenario, mask))] += 1
        if distribution[20] != 1:
            raise SystemExit(f"{scenario_id}: expected exactly one perfect marking pattern")

        ideal = ideal_decision(scenario)
        valid_action_states = 0
        state_count = 0
        action_names = list(scenario["action_scores"])
        for bits in itertools.product((False, True), repeat=len(action_names)):
            selected = dict(zip(action_names, bits))
            if not action_plan_valid(scenario, selected):
                continue
            valid_action_states += 1
            for confidence in CONFIDENCE_LEVELS:
                for corroboration in CORROBORATION_LEVELS:
                    for authenticity in AUTHENTICITY_LEVELS:
                        for option in scenario["release_options"]:
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
                            if not 0 <= score <= 100:
                                raise SystemExit(f"{scenario_id}: unbounded score {score}")
                            state_count += 1

        random_scores = []
        random_labels = []
        random_sample_count = 10000
        for _ in range(random_sample_count):
            marks = {
                card["id"]: {name: bool(rng.getrandbits(1)) for name in MARK_NAMES}
                for card in scenario["evidence_cards"]
            }
            decision = Decision(
                reviewed_count=ideal.reviewed_count,
                marks=marks,
                confidence_history=ideal.confidence_history,
                corroboration_history=ideal.corroboration_history,
                authenticity_history=ideal.authenticity_history,
                release_id=ideal.release_id,
                actions=ideal.actions,
                remaining_minutes=ideal.remaining_minutes,
            )
            random_scores.append(total_score(scenario, decision))
            random_labels.append(performance_label(scenario, decision))

        results["scenarios"][scenario_id] = {
            "marking_patterns_exhausted": 1 << bit_count,
            "marking_score_distribution": {str(k): v for k, v in sorted(distribution.items())},
            "perfect_marking_patterns": distribution[20],
            "valid_action_subsets": valid_action_states,
            "epistemic_release_action_states_exhausted": state_count,
            "random_marking_seed": 333,
            "random_marking_samples": len(random_scores),
            "random_total_score_mean": statistics.mean(random_scores),
            "random_total_score_min": min(random_scores),
            "random_total_score_max": max(random_scores),
            "random_total_score_fraction_at_least_90": sum(v >= 90 for v in random_scores) / len(random_scores),
            "random_performance_label_distribution": dict(sorted(Counter(random_labels).items())),
            "random_fraction_labeled_excellent": sum(
                label == "Excellent governance discipline" for label in random_labels
            ) / len(random_labels),
            "ideal_total_score": total_score(scenario, ideal),
        }

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
