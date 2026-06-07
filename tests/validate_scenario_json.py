import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIO_DIR = ROOT / "game" / "data" / "scenarios"
RELEASE_LANGUAGE_PATH = ROOT / "game" / "data" / "release_language" / "controlled_language.json"

required_keys = {
    "scenario_id", "version", "title", "briefing", "decision_clock_minutes",
    "time_step_minutes", "starting_meters", "evidence_cards",
    "correct_confidence_range", "unsafe_choices", "release_options",
    "minimum_evidence_cards_required_before_scoring", "learning_objectives",
    "facilitator_notes", "debrief_prompts", "recommended_language_keys"
}
required_meters = {
    "truth_integrity", "escalation_risk", "civilian_safety",
    "institutional_credibility", "decision_timeliness", "public_pressure"
}
approved_confidence = {"Confirmed", "Likely", "Possible", "Unverified", "Disputed", "Manipulated / Unclear"}
allowed_states = {"Unread", "Reviewed", "Flagged", "Sensitive", "Contradictory", "Requires Follow-Up", "Partial"}

release_language = json.loads(RELEASE_LANGUAGE_PATH.read_text(encoding="utf-8"))
if not {"confirmed", "likely", "possible", "unverified", "disputed", "manipulated_unclear"}.issubset(release_language):
    raise SystemExit("Controlled language file missing core confidence entries")

scenario_paths = sorted(SCENARIO_DIR.glob("*.json"))
if len(scenario_paths) < 2:
    raise SystemExit("v0.2 requires at least two scenarios")

for path in scenario_paths:
    scenario = json.loads(path.read_text(encoding="utf-8"))
    missing = required_keys - set(scenario)
    if missing:
        raise SystemExit(f"{path.name}: missing keys {sorted(missing)}")

    for key in scenario.get("recommended_language_keys", []):
        if key not in release_language:
            raise SystemExit(f"{path.name}: recommended language key not found in controlled language: {key}")
    if not scenario.get("version", "").startswith("0.2"):
        raise SystemExit(f"{path.name}: scenario version should be 0.2.x")

    meters = scenario["starting_meters"]
    if set(meters) != required_meters:
        raise SystemExit(f"{path.name}: meters must be exactly {sorted(required_meters)}")
    for key, value in meters.items():
        if not isinstance(value, int) or not 0 <= value <= 100:
            raise SystemExit(f"{path.name}: meter {key} must be integer 0-100")

    if not isinstance(scenario["decision_clock_minutes"], int) or scenario["decision_clock_minutes"] <= 0:
        raise SystemExit(f"{path.name}: decision_clock_minutes must be positive int")
    if not isinstance(scenario["time_step_minutes"], int) or scenario["time_step_minutes"] <= 0:
        raise SystemExit(f"{path.name}: time_step_minutes must be positive int")

    for level in scenario["correct_confidence_range"] + scenario["unsafe_choices"]:
        if level not in approved_confidence:
            raise SystemExit(f"{path.name}: invalid confidence level {level}")

    cards = scenario["evidence_cards"]
    if len(cards) < scenario["minimum_evidence_cards_required_before_scoring"]:
        raise SystemExit(f"{path.name}: evidence gate exceeds card count")
    seen_ids = set()
    for card in cards:
        for key in ["id", "title", "description", "tags", "reliability", "states"]:
            if key not in card:
                raise SystemExit(f"{path.name}: evidence card missing {key}: {card}")
        if card["id"] in seen_ids:
            raise SystemExit(f"{path.name}: duplicate evidence id {card['id']}")
        seen_ids.add(card["id"])
        if not isinstance(card["tags"], list) or not isinstance(card["states"], list):
            raise SystemExit(f"{path.name}: tags and states must be lists")
        for state in card["states"]:
            if state not in allowed_states:
                raise SystemExit(f"{path.name}: invalid state {state}")

    option_ids = {option.get("id") for option in scenario["release_options"]}
    if "overclaim" not in option_ids:
        raise SystemExit(f"{path.name}: missing unsafe overclaim option")
    if not option_ids.intersection({"safe_cautious", "corrective", "humanitarian_cautious"}):
        raise SystemExit(f"{path.name}: missing safe/corrective release option")
    for option in scenario["release_options"]:
        for key in ["id", "label", "effects"]:
            if key not in option:
                raise SystemExit(f"{path.name}: release option missing {key}")
        for meter, effect in option["effects"].items():
            if meter not in required_meters:
                raise SystemExit(f"{path.name}: release option modifies unknown meter {meter}")
            if not isinstance(effect, int):
                raise SystemExit(f"{path.name}: release option effect must be int")

print(f"Scenario JSON validation passed for {len(scenario_paths)} scenarios with v0.2.1 rules.")
