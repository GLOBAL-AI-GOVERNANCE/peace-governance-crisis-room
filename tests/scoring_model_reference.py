"""Reference model for Peace OS: Crisis Room v0.3.0-rc2.

This model mirrors the data-driven source scoring contract. It does not execute
Godot and must not be represented as runtime validation.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import json

ROOT = Path(__file__).resolve().parents[1]
SCENARIO_DIR = ROOT / "core" / "scenarios"
RUBRIC_PATH = ROOT / "core" / "scoring" / "scoring_rubric.json"

MARK_NAMES = ("flagged", "sensitive", "follow_up", "used")
CONFIDENCE_LEVELS = ("Confirmed", "Likely", "Possible", "Unverified")
CORROBORATION_LEVELS = (
    "Corroborated",
    "Partially corroborated",
    "Contradictory",
    "Uncorroborated",
)
AUTHENTICITY_LEVELS = (
    "No manipulation indicators",
    "Manipulation suspected",
    "Authenticity unclear",
    "Not applicable",
)
COMPONENT_MAX = {
    "evidence_review": 10,
    "evidence_marking": 20,
    "confidence": 15,
    "corroboration": 10,
    "authenticity": 10,
    "release": 15,
    "actions": 15,
    "timeliness": 5,
}


def load_scenarios() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(SCENARIO_DIR.glob("*.json")):
        scenario = json.loads(path.read_text(encoding="utf-8"))
        if "scenario_id" not in scenario:
            continue
        result[scenario["scenario_id"]] = scenario
    return result


def load_scoring_rubric() -> dict[str, Any]:
    return json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))


def expected_marks(scenario: Mapping[str, Any]) -> dict[str, dict[str, bool]]:
    return {
        card["id"]: {name: bool(card["expected_marks"][name]) for name in MARK_NAMES}
        for card in scenario["evidence_cards"]
    }


def blank_marks(scenario: Mapping[str, Any], value: bool = False) -> dict[str, dict[str, bool]]:
    return {
        card["id"]: {name: value for name in MARK_NAMES}
        for card in scenario["evidence_cards"]
    }


def round_half_away_from_zero(value: float) -> int:
    # All scoring values are non-negative, so floor(x + 0.5) matches GDScript.
    return int(value + 0.5)


def marking_diagnostics(
    scenario: Mapping[str, Any], marks: Mapping[str, Mapping[str, bool]]
) -> dict[str, dict[str, float | int]]:
    """Return category-balanced confusion metrics.

    Each category is scored by Youden's J / informedness:
    sensitivity + specificity - 1. Chance, all-positive, and all-negative
    strategies have expected skill 0. Perfect classification has skill 1.
    """
    diagnostics: dict[str, dict[str, float | int]] = {}
    for name in MARK_NAMES:
        tp = tn = fp = fn = 0
        for card in scenario["evidence_cards"]:
            card_id = card["id"]
            expected = bool(card["expected_marks"][name])
            actual = bool(marks.get(card_id, {}).get(name, False))
            if expected and actual:
                tp += 1
            elif expected and not actual:
                fn += 1
            elif not expected and actual:
                fp += 1
            else:
                tn += 1
        positives = tp + fn
        negatives = tn + fp
        if positives == 0 or negatives == 0:
            raise ValueError(f"Mark category {name!r} must contain positive and negative examples")
        recall = tp / positives
        specificity = tn / negatives
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        skill = max(0.0, recall + specificity - 1.0)
        diagnostics[name] = {
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "specificity": specificity,
            "chance_corrected_skill": skill,
        }
    return diagnostics


def marking_score(scenario: Mapping[str, Any], marks: Mapping[str, Mapping[str, bool]]) -> int:
    diagnostics = marking_diagnostics(scenario, marks)
    mean_skill = sum(float(v["chance_corrected_skill"]) for v in diagnostics.values()) / len(
        diagnostics
    )
    return round_half_away_from_zero(20 * mean_skill)


def evidence_review_score(scenario: Mapping[str, Any], reviewed_count: int) -> int:
    total = len(scenario["evidence_cards"])
    return round_half_away_from_zero(10 * reviewed_count / total) if total else 0


def categorical_score(
    choice: str,
    correct: list[str] | tuple[str, ...],
    unsafe: list[str] | tuple[str, ...],
    maximum: int,
) -> int:
    if choice in correct:
        return maximum
    if choice in unsafe:
        return 0
    return maximum // 2


def confidence_score(scenario: Mapping[str, Any], choice: str) -> int:
    return categorical_score(choice, scenario["correct_confidence_range"], scenario["unsafe_choices"], 15)


def corroboration_score(scenario: Mapping[str, Any], choice: str) -> int:
    return categorical_score(
        choice,
        scenario["correct_corroboration_range"],
        scenario["unsafe_corroboration_choices"],
        10,
    )


def authenticity_score(scenario: Mapping[str, Any], choice: str) -> int:
    return categorical_score(
        choice,
        scenario["correct_authenticity_range"],
        scenario["unsafe_authenticity_choices"],
        10,
    )


def release_score(scenario: Mapping[str, Any], release_id: str) -> int:
    for option in scenario["release_options"]:
        if option["id"] == release_id:
            return max(0, min(15, int(option["doctrine_score"])))
    return 0


def action_costs(scenario: Mapping[str, Any], actions: Mapping[str, bool]) -> dict[str, int]:
    result = {"time": 0, "authority": 0}
    configured = scenario["action_costs"]
    for name, selected in actions.items():
        if selected and name in configured:
            result["time"] += int(configured[name]["time"])
            result["authority"] += int(configured[name]["authority"])
    return result


def action_plan_valid(scenario: Mapping[str, Any], actions: Mapping[str, bool]) -> bool:
    costs = action_costs(scenario, actions)
    budget = scenario["action_budget"]
    return costs["time"] <= int(budget["time"]) and costs["authority"] <= int(budget["authority"])


def actions_score(scenario: Mapping[str, Any], actions: Mapping[str, bool]) -> int:
    if not action_plan_valid(scenario, actions):
        raise ValueError("Action plan exceeds time or authority budget")
    points = sum(
        int(points)
        for name, points in scenario["action_scores"].items()
        if bool(actions.get(name, False))
    )
    return max(0, min(15, points))


def timeliness_score(remaining_minutes: int) -> int:
    if remaining_minutes >= 10:
        return 5
    if remaining_minutes >= 5:
        return 4
    if remaining_minutes > 0:
        return 2
    return 0


@dataclass(frozen=True)
class Decision:
    reviewed_count: int
    marks: Mapping[str, Mapping[str, bool]]
    confidence_history: tuple[str, ...]
    corroboration_history: tuple[str, ...]
    authenticity_history: tuple[str, ...]
    release_id: str
    actions: Mapping[str, bool]
    remaining_minutes: int
    human_confirmation: bool = True

    @property
    def final_confidence(self) -> str:
        return self.confidence_history[-1] if self.confidence_history else ""

    @property
    def final_corroboration(self) -> str:
        return self.corroboration_history[-1] if self.corroboration_history else ""

    @property
    def final_authenticity(self) -> str:
        return self.authenticity_history[-1] if self.authenticity_history else ""


def score_breakdown(scenario: Mapping[str, Any], decision: Decision) -> dict[str, int]:
    if not decision.human_confirmation:
        raise ValueError("Human final confirmation is required")
    if decision.reviewed_count < len(scenario["evidence_cards"]):
        raise ValueError("Complete evidence review is required")
    if not action_plan_valid(scenario, decision.actions):
        raise ValueError("Action plan exceeds time or authority budget")
    result = {
        "evidence_review": evidence_review_score(scenario, decision.reviewed_count),
        "evidence_marking": marking_score(scenario, decision.marks),
        "confidence": confidence_score(scenario, decision.final_confidence),
        "corroboration": corroboration_score(scenario, decision.final_corroboration),
        "authenticity": authenticity_score(scenario, decision.final_authenticity),
        "release": release_score(scenario, decision.release_id),
        "actions": actions_score(scenario, decision.actions),
        "timeliness": timeliness_score(decision.remaining_minutes),
    }
    assert set(result) == set(COMPONENT_MAX)
    for key, value in result.items():
        assert 0 <= value <= COMPONENT_MAX[key]
    return result


def raw_total_score(scenario: Mapping[str, Any], decision: Decision) -> int:
    """Return the additive component total before the evidence-quality ceiling."""
    return sum(score_breakdown(scenario, decision).values())


def total_score(scenario: Mapping[str, Any], decision: Decision) -> int:
    """Return the displayed score, aligned with the consequence classification.

    Credible and Excellent labels require evidence-analysis floors. Downstream
    choices cannot fully compensate for weak evidence discrimination.
    """
    raw = raw_total_score(scenario, decision)
    if raw >= 75 and not credible_gate_passes(scenario, decision):
        return 74
    if raw >= 90 and not excellent_gate_passes(scenario, decision):
        return 89
    return raw


def credible_gate_passes(scenario: Mapping[str, Any], decision: Decision) -> bool:
    rubric = load_scoring_rubric()
    minimum = int(rubric.get("credible_gate", {}).get("minimum_evidence_marking", 10))
    return score_breakdown(scenario, decision)["evidence_marking"] >= minimum


def excellent_gate_passes(scenario: Mapping[str, Any], decision: Decision) -> bool:
    rubric = load_scoring_rubric()
    minimum = int(rubric.get("excellent_gate", {}).get("minimum_evidence_marking", 18))
    breakdown = score_breakdown(scenario, decision)
    return (
        breakdown["evidence_marking"] >= minimum
        and decision.final_confidence in scenario["correct_confidence_range"]
        and decision.final_corroboration in scenario["correct_corroboration_range"]
        and decision.final_authenticity in scenario["correct_authenticity_range"]
        and release_score(scenario, decision.release_id) == 15
        and action_plan_valid(scenario, decision.actions)
    )


def performance_label(scenario: Mapping[str, Any], decision: Decision) -> str:
    score = total_score(scenario, decision)
    if score >= 90 and excellent_gate_passes(scenario, decision):
        return "Excellent governance discipline"
    if score >= 75:
        return "Credible crisis handling"
    if score >= 60:
        return "Mixed outcome"
    return "Governance failure risk"


def ideal_decision(scenario: Mapping[str, Any]) -> Decision:
    actions = {name: name in scenario["recommended_actions"] for name in scenario["action_scores"]}
    safe_release = next(
        option["id"] for option in scenario["release_options"] if option["doctrine_score"] == 15
    )
    return Decision(
        reviewed_count=len(scenario["evidence_cards"]),
        marks=expected_marks(scenario),
        confidence_history=(scenario["correct_confidence_range"][0],),
        corroboration_history=(scenario["correct_corroboration_range"][0],),
        authenticity_history=(scenario["correct_authenticity_range"][0],),
        release_id=safe_release,
        actions=actions,
        remaining_minutes=14,
    )
