import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIO_DIR = ROOT / "game" / "data" / "scenarios"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
RELEASE_LANGUAGE_PATH = ROOT / "game" / "data" / "release_language" / "controlled_language.json"

required_keys = {
    "scenario_id", "version", "title", "briefing", "decision_clock_minutes",
    "time_step_minutes", "starting_meters", "evidence_cards",
    "correct_confidence_range", "unsafe_choices",
    "correct_corroboration_range", "unsafe_corroboration_choices",
    "correct_authenticity_range", "unsafe_authenticity_choices",
    "release_options", "minimum_evidence_cards_required_before_scoring",
    "learning_objectives", "facilitator_notes", "debrief_prompts",
    "recommended_language_keys", "action_scores", "action_costs",
    "action_budget", "recommended_actions", "critical_safeguards",
}
required_meters = {
    "truth_integrity", "escalation_risk", "civilian_safety",
    "institutional_credibility", "decision_timeliness", "public_pressure"
}
actions = {
    "protect_civilians", "request_original_media", "info_integrity_review",
    "deescalation_channel", "senior_review", "humanitarian_check"
}
marks = {"flagged", "sensitive", "follow_up", "used"}
approved_confidence = {"Confirmed", "Likely", "Possible", "Unverified"}
approved_corroboration = {"Corroborated", "Partially corroborated", "Contradictory", "Uncorroborated"}
approved_authenticity = {"No indicators identified", "Manipulation suspected", "Authenticity unclear", "Not applicable"}
allowed_states = {"Unread", "Reviewed", "Flagged", "Sensitive", "Contradictory", "Requires Follow-Up", "Partial"}

release_language = json.loads(RELEASE_LANGUAGE_PATH.read_text(encoding="utf-8"))
scenario_paths = sorted(SCENARIO_DIR.glob("*.json"))
if len(scenario_paths) < 2:
    raise SystemExit("At least two scenarios are required")

for path in scenario_paths:
    scenario = json.loads(path.read_text(encoding="utf-8"))
    missing = required_keys - set(scenario)
    if missing:
        raise SystemExit(f"{path.name}: missing keys {sorted(missing)}")
    if scenario["version"] != VERSION:
        raise SystemExit(f"{path.name}: version {scenario['version']} does not match {VERSION}")
    if set(scenario["starting_meters"]) != required_meters:
        raise SystemExit(f"{path.name}: meter set mismatch")
    if set(scenario["action_scores"]) != actions or set(scenario['action_costs']) != actions:
        raise SystemExit(f"{path.name}: action configuration must cover six actions")
    if not set(scenario["recommended_actions"]).issubset(actions):
        raise SystemExit(f"{path.name}: recommended actions must be configured")
    if not set(scenario["critical_safeguards"]).issubset(actions):
        raise SystemExit(f"{path.name}: critical safeguards must be configured")
    if type(scenario["time_step_minutes"]) is not int or scenario["time_step_minutes"] < 1:
        raise SystemExit(f"{path.name}: invalid time step")
    if sum(scenario['action_scores'][name] for name in scenario['recommended_actions']) != 15:
        raise SystemExit(f"{path.name}: recommended plan must reach 15 action points")
    for resource in ('time','authority'):
        budget=scenario['action_budget'].get(resource)
        if type(budget) is not int or budget < 1:
            raise SystemExit(f"{path.name}: invalid {resource} budget")
        ideal=sum(scenario['action_costs'][name][resource] for name in scenario['recommended_actions'])
        all_cost=sum(scenario['action_costs'][name][resource] for name in actions)
        if ideal > budget or all_cost <= budget:
            raise SystemExit(f"{path.name}: {resource} budget must admit ideal plan and reject select-all")
    if scenario["minimum_evidence_cards_required_before_scoring"] != len(scenario["evidence_cards"]):
        raise SystemExit(f"{path.name}: complete evidence review must be required")
    for level in scenario["correct_confidence_range"] + scenario["unsafe_choices"]:
        if level not in approved_confidence:
            raise SystemExit(f"{path.name}: invalid confidence level {level}")
    for level in scenario['correct_corroboration_range'] + scenario['unsafe_corroboration_choices']:
        if level not in approved_corroboration:
            raise SystemExit(f"{path.name}: invalid corroboration level {level}")
    for level in scenario['correct_authenticity_range'] + scenario['unsafe_authenticity_choices']:
        if level not in approved_authenticity:
            raise SystemExit(f"{path.name}: invalid authenticity level {level}")
    for key in scenario["recommended_language_keys"]:
        if key not in release_language:
            raise SystemExit(f"{path.name}: unknown controlled language key {key}")
    seen = set()
    for card in scenario["evidence_cards"]:
        if card["id"] in seen:
            raise SystemExit(f"{path.name}: duplicate evidence id {card['id']}")
        seen.add(card["id"])
        if 'states' in card:
            raise SystemExit(f"{path.name}: learner-facing states leak scoring indicators")
        if set(card.get("expected_marks", {})) != marks:
            raise SystemExit(f"{path.name}: {card['id']} expected_marks must contain {sorted(marks)}")
        if any(type(value) is not bool for value in card["expected_marks"].values()):
            raise SystemExit(f"{path.name}: expected marks must be strict Booleans")
        for state in card.get('facilitator_indicators',[]):
            if state not in allowed_states:
                raise SystemExit(f"{path.name}: invalid facilitator indicator {state}")
    for mark in marks:
        values=[card['expected_marks'][mark] for card in scenario['evidence_cards']]
        if True not in values or False not in values:
            raise SystemExit(f"{path.name}: mark category {mark} is not discriminative")
    option_ids = set()
    for option in scenario["release_options"]:
        option_ids.add(option["id"])
        if type(option.get("doctrine_score")) is not int or not 0 <= option["doctrine_score"] <= 15:
            raise SystemExit(f"{path.name}: invalid doctrine_score in {option.get('id')}")
        for meter, effect in option["effects"].items():
            if meter not in required_meters or type(effect) is not int:
                raise SystemExit(f"{path.name}: invalid effect in {option.get('id')}")
    if "overclaim" not in option_ids or not any(option["doctrine_score"] == 15 for option in scenario["release_options"]):
        raise SystemExit(f"{path.name}: requires an overclaim path and a full-score controlled path")

print(f"Scenario JSON validation passed for {len(scenario_paths)} scenarios under {VERSION} rules.")
