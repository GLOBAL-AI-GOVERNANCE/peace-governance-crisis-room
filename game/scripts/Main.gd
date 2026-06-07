extends Control

var scenarios: Dictionary = {}
var scenario: Dictionary = {}
var current_scenario_id: String = ""
var controlled_language: Dictionary = {}
var scoring_rubric: Dictionary = {}
var meters: Dictionary = {}
var starting_meters: Dictionary = {}
var reviewed_cards: Array = []
var card_marks: Dictionary = {}
var confidence_choice: String = ""
var release_choice: Dictionary = {}
var facilitator_mode: bool = false
var remaining_minutes: int = 30
var last_aar_path: String = ""
var final_performance: String = ""
var pressure_events: Array = []
var evidence_marking_notes: Array = []
var half_time_warning_given: bool = false
var final_warning_given: bool = false
var deadline_hit_given: bool = false

var actions: Dictionary = {
	"protect_civilians": false,
	"request_original_media": false,
	"info_integrity_review": false,
	"deescalation_channel": false,
	"senior_review": false,
	"humanitarian_check": false
}

var action_labels: Dictionary = {
	"protect_civilians": "Protect civilian identities / redact sensitive details",
	"request_original_media": "Request original media and metadata",
	"info_integrity_review": "Trigger information-integrity review",
	"deescalation_channel": "Activate de-escalation / diplomatic review channel",
	"senior_review": "Escalate to senior human review",
	"humanitarian_check": "Check humanitarian / safety channels without public overclaiming"
}

const REQUIRED_REVIEWED_CARDS_DEFAULT := 4
const CONFIDENCE_LEVELS := ["Confirmed", "Likely", "Possible", "Unverified", "Disputed", "Manipulated / Unclear"]
const SCENARIO_FILES := [
	"res://data/scenarios/scenario_01_viral_collision_video.json",
	"res://data/scenarios/scenario_02_deepfake_distress_call.json"
]

var root_box: VBoxContainer

func _ready() -> void:
	load_all_data()
	show_main_menu()

func load_all_data() -> void:
	load_scenarios()
	load_controlled_language()
	load_scoring_rubric()

func load_scenarios() -> void:
	scenarios = {}
	for path in SCENARIO_FILES:
		var file := FileAccess.open(path, FileAccess.READ)
		if file == null:
			push_error("Scenario file missing: " + path)
			continue
		var parsed = JSON.parse_string(file.get_as_text())
		if typeof(parsed) == TYPE_DICTIONARY:
			scenarios[parsed.get("scenario_id", path)] = parsed

func load_controlled_language() -> void:
	var file := FileAccess.open("res://data/release_language/controlled_language.json", FileAccess.READ)
	if file == null:
		controlled_language = {}
		return
	var parsed = JSON.parse_string(file.get_as_text())
	if typeof(parsed) == TYPE_DICTIONARY:
		controlled_language = parsed

func load_scoring_rubric() -> void:
	var file := FileAccess.open("res://data/scoring/scoring_rubric.json", FileAccess.READ)
	if file == null:
		scoring_rubric = {}
		return
	var parsed = JSON.parse_string(file.get_as_text())
	if typeof(parsed) == TYPE_DICTIONARY:
		scoring_rubric = parsed

func reset_for_scenario(scenario_id: String) -> void:
	current_scenario_id = scenario_id
	scenario = scenarios.get(scenario_id, {})
	meters = scenario.get("starting_meters", {}).duplicate(true)
	starting_meters = meters.duplicate(true)
	reviewed_cards = []
	card_marks = {}
	for card in scenario.get("evidence_cards", []):
		card_marks[card.get("id", "")] = {
			"reviewed": false,
			"flagged": false,
			"sensitive": false,
			"follow_up": false,
			"used": false
		}
	confidence_choice = ""
	release_choice = {}
	actions = {
		"protect_civilians": false,
		"request_original_media": false,
		"info_integrity_review": false,
		"deescalation_channel": false,
		"senior_review": false,
		"humanitarian_check": false
	}
	remaining_minutes = int(scenario.get("decision_clock_minutes", 30))
	last_aar_path = ""
	final_performance = ""
	pressure_events = []
	evidence_marking_notes = []
	half_time_warning_given = false
	final_warning_given = false
	deadline_hit_given = false

func clear_ui() -> void:
	for child in get_children():
		child.queue_free()
	var scroll := ScrollContainer.new()
	scroll.anchor_right = 1
	scroll.anchor_bottom = 1
	scroll.offset_left = 24
	scroll.offset_top = 18
	scroll.offset_right = -24
	scroll.offset_bottom = -18
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(scroll)
	root_box = VBoxContainer.new()
	root_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	root_box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root_box.custom_minimum_size = Vector2(900, 0)
	root_box.add_theme_constant_override("separation", 10)
	scroll.add_child(root_box)

func add_title(text: String) -> void:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 28)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root_box.add_child(label)

func add_subtitle(text: String) -> void:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 20)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root_box.add_child(label)

func add_text(text: String) -> Label:
	var label := Label.new()
	label.text = text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.add_theme_font_size_override("font_size", 16)
	root_box.add_child(label)
	return label

func add_button(text: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.pressed.connect(callback)
	root_box.add_child(button)
	return button

func meter_label(key: String) -> String:
	var meta = scoring_rubric.get("meters", {}).get(key, {})
	return meta.get("label", key.capitalize())

func add_dashboard() -> void:
	add_subtitle("Crisis Dashboard")
	add_text("Decision clock: %s minutes remaining | Evidence reviewed: %s / %s | Current confidence: %s" % [remaining_minutes, reviewed_cards.size(), scenario.get("evidence_cards", []).size(), confidence_choice if confidence_choice != "" else "Not selected"])
	if pressure_events.size() > 0:
		add_text("Latest pressure event: " + str(pressure_events[pressure_events.size() - 1]))
	for key in ["truth_integrity", "escalation_risk", "civilian_safety", "institutional_credibility", "decision_timeliness", "public_pressure"]:
		var value := int(meters.get(key, 0))
		var label := Label.new()
		label.text = "%s: %s / 100" % [meter_label(key), value]
		root_box.add_child(label)
		var bar := ProgressBar.new()
		bar.min_value = 0
		bar.max_value = 100
		bar.value = value
		bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		root_box.add_child(bar)

func change_meter(name: String, amount: int) -> void:
	meters[name] = clamp(int(meters.get(name, 0)) + amount, 0, 100)

func advance_time() -> void:
	var step := int(scenario.get("time_step_minutes", 5))
	apply_pressure_tick(step, 8, "Manual pressure advance")
	show_current_screen_hint()

func apply_pressure_tick(minutes: int, public_delta: int, reason: String) -> void:
	if minutes <= 0:
		return
	remaining_minutes = max(0, remaining_minutes - minutes)
	change_meter("public_pressure", public_delta)
	change_meter("decision_timeliness", -int(ceil(float(minutes) / 2.0)))
	if int(meters.get("public_pressure", 0)) > 75:
		change_meter("escalation_risk", 3)
	if reason != "":
		pressure_events.append("%s: -%s minutes, public pressure +%s." % [reason, minutes, public_delta])
	if remaining_minutes <= 15 and not half_time_warning_given:
		half_time_warning_given = true
		pressure_events.append("Media demand intensifies: 15 minutes or less remain.")
		change_meter("public_pressure", 5)
	if remaining_minutes <= 5 and not final_warning_given:
		final_warning_given = true
		pressure_events.append("Senior office pressure appears: 5 minutes or less remain.")
		change_meter("public_pressure", 8)
		change_meter("institutional_credibility", -3)
	if remaining_minutes == 0 and not deadline_hit_given:
		deadline_hit_given = true
		pressure_events.append("Decision deadline reached: timeliness and credibility penalties applied.")
		change_meter("decision_timeliness", -10)
		change_meter("institutional_credibility", -5)

func show_current_screen_hint() -> void:
	show_evidence()

func show_main_menu() -> void:
	clear_ui()
	add_title("Peace OS: Crisis Room")
	add_text("A serious PC game about AI governance under crisis pressure.")
	add_text("Doctrine: verification before amplification, human control before release, civilian protection before intelligence value, confidence scoring before public attribution.")
	var prefix := "✓ " if facilitator_mode else "☐ "
	add_button(prefix + "Facilitator / Observer Mode", Callable(self, "toggle_facilitator_mode"))
	add_subtitle("Select Scenario")
	for id in scenarios.keys():
		var sc = scenarios[id]
		add_button(sc.get("title", id), func(sid=id): start_scenario(sid))
	add_button("Policy Boundary", Callable(self, "show_policy_boundary"))

func toggle_facilitator_mode() -> void:
	facilitator_mode = not facilitator_mode
	show_main_menu()

func start_scenario(scenario_id: String) -> void:
	reset_for_scenario(scenario_id)
	show_briefing()

func show_policy_boundary() -> void:
	clear_ui()
	add_title("Policy Boundary")
	add_text("This is a fictional serious-game prototype. It is not an operational tool, intelligence system, legal attribution engine, or official government product. It uses no live data and no AI decision automation.")
	add_text("Game purpose: reveal decision friction, evidence gaps, overclaiming risk, civilian exposure, and public-release pressure.")
	add_button("Back", Callable(self, "show_main_menu"))

func show_briefing() -> void:
	clear_ui()
	add_title(scenario.get("title", "Scenario"))
	add_text(scenario.get("briefing", ""))
	add_dashboard()
	if facilitator_mode:
		add_facilitator_panel()
	add_text("Mission: Review evidence, assign a defensible confidence level, protect civilians, and decide whether public release is allowed.")
	add_button("Open Evidence Inbox", Callable(self, "show_evidence"))
	add_button("Back to Main Menu", Callable(self, "show_main_menu"))

func add_facilitator_panel() -> void:
	add_subtitle("Facilitator / Observer Notes")
	add_text("Hidden defensible confidence range: " + ", ".join(scenario.get("correct_confidence_range", [])))
	add_text("Unsafe confidence choices: " + ", ".join(scenario.get("unsafe_choices", [])))
	for note in scenario.get("facilitator_notes", []):
		add_text("• " + note)

func show_evidence() -> void:
	clear_ui()
	add_title("Evidence Inbox")
	add_dashboard()
	add_text("Click cards to review, flag, mark sensitive, request follow-up, or mark as used in confidence assessment.")
	add_text("Required before scoring: review at least %s of %s evidence cards." % [required_cards(), scenario.get("evidence_cards", []).size()])
	add_button("Advance 5 Minutes: public pressure rises", Callable(self, "advance_time"))
	for card in scenario.get("evidence_cards", []):
		var card_id := card.get("id", "")
		var marks = card_marks.get(card_id, {})
		var state := "[Reviewed] " if marks.get("reviewed", false) else "[Unread] "
		var flags: Array = []
		if marks.get("flagged", false): flags.append("Player Flagged")
		if marks.get("sensitive", false): flags.append("Player Marked Sensitive")
		if marks.get("follow_up", false): flags.append("Player Requested Follow-Up")
		if marks.get("used", false): flags.append("Used in Assessment")
		var indicators: Array = card.get("states", [])
		var suffix_parts: Array = []
		if indicators.size() > 0: suffix_parts.append("Indicators: " + ", ".join(indicators))
		if flags.size() > 0: suffix_parts.append("Marks: " + ", ".join(flags))
		var suffix := "" if suffix_parts.size() == 0 else " — " + " | ".join(suffix_parts)
		add_button(state + card.get("title", "Evidence") + suffix, func(c=card): open_card(c))
	add_text("Reviewed cards: %s / %s" % [reviewed_cards.size(), scenario.get("evidence_cards", []).size()])
	if reviewed_cards.size() >= required_cards():
		add_button("Proceed to Confidence Scoring", Callable(self, "show_confidence"))
	else:
		add_text("Gate active: confidence scoring is locked until enough evidence is reviewed. This enforces verification before amplification.")
		var locked := Button.new()
		locked.text = "Confidence Scoring Locked"
		locked.disabled = true
		root_box.add_child(locked)
	add_button("Back to Briefing", Callable(self, "show_briefing"))

func required_cards() -> int:
	return int(scenario.get("minimum_evidence_cards_required_before_scoring", REQUIRED_REVIEWED_CARDS_DEFAULT))

func open_card(card: Dictionary) -> void:
	var card_id := card.get("id", "")
	var marks = card_marks.get(card_id, {})
	if not marks.get("reviewed", false):
		marks["reviewed"] = true
		if not reviewed_cards.has(card_id): reviewed_cards.append(card_id)
		apply_card_effects(card)
		apply_pressure_tick(2, 3, "Evidence reviewed: " + card.get("title", "Evidence"))
	card_marks[card_id] = marks
	show_card_detail(card)

func apply_card_effects(card: Dictionary) -> void:
	var reliability := card.get("reliability", "partial")
	var tags: Array = card.get("tags", [])
	if reliability == "sensitive": change_meter("civilian_safety", -5)
	if tags.has("metadata_missing") or tags.has("original_missing"): change_meter("truth_integrity", -3)
	if tags.has("viral"): change_meter("escalation_risk", 5); change_meter("public_pressure", 5)
	if tags.has("bot_amplification") or tags.has("synthetic_audio_possible"): change_meter("truth_integrity", -4); change_meter("escalation_risk", 4)
	if tags.has("humanitarian_claim"): change_meter("public_pressure", 8)

func show_card_detail(card: Dictionary) -> void:
	clear_ui()
	var card_id := card.get("id", "")
	var marks = card_marks.get(card_id, {})
	add_title(card.get("title", "Evidence"))
	add_text(card.get("description", ""))
	add_text("Tags: " + ", ".join(card.get("tags", [])))
	add_text("Reliability: " + card.get("reliability", "partial"))
	var indicators: Array = card.get("states", [])
	add_text("Initial indicators: " + (", ".join(indicators) if indicators.size() > 0 else "None listed"))
	add_text("Player markings: " + card_state_text(card_id))
	add_dashboard()
	add_subtitle("Evidence Actions")
	add_button("Flag / Unflag", func(): toggle_card_mark(card_id, "flagged", card))
	add_button("Mark Sensitive / Clear Sensitive", func(): toggle_card_mark(card_id, "sensitive", card))
	add_button("Request Follow-Up / Clear Follow-Up", func(): toggle_card_mark(card_id, "follow_up", card))
	add_button("Use in Confidence Assessment / Remove", func(): toggle_card_mark(card_id, "used", card))
	add_button("Back to Evidence Inbox", Callable(self, "show_evidence"))

func toggle_card_mark(card_id: String, key: String, card: Dictionary) -> void:
	var marks = card_marks.get(card_id, {})
	marks[key] = not marks.get(key, false)
	card_marks[card_id] = marks
	show_card_detail(card)

func card_state_text(card_id: String) -> String:
	var marks = card_marks.get(card_id, {})
	var states: Array = []
	states.append("Reviewed" if marks.get("reviewed", false) else "Unread")
	if marks.get("flagged", false): states.append("Flagged by player")
	if marks.get("sensitive", false): states.append("Marked sensitive by player")
	if marks.get("follow_up", false): states.append("Follow-up requested by player")
	if marks.get("used", false): states.append("Used in Confidence Assessment")
	return ", ".join(states)

func show_confidence() -> void:
	if reviewed_cards.size() < required_cards():
		show_evidence()
		return
	clear_ui()
	add_title("Confidence Scoring")
	add_dashboard()
	add_text("Select the highest defensible confidence level. Do not let the public claim exceed the evidence.")
	for level in CONFIDENCE_LEVELS:
		add_button(level, func(l=level): choose_confidence(l))
	add_button("Back to Evidence Inbox", Callable(self, "show_evidence"))

func choose_confidence(level: String) -> void:
	confidence_choice = level
	apply_pressure_tick(3, 4, "Confidence scoring decision selected")
	var correct_range: Array = scenario.get("correct_confidence_range", [])
	var unsafe: Array = scenario.get("unsafe_choices", [])
	if correct_range.has(level):
		change_meter("truth_integrity", 16)
		change_meter("institutional_credibility", 10)
		change_meter("decision_timeliness", -1)
	elif unsafe.has(level):
		change_meter("truth_integrity", -35)
		change_meter("escalation_risk", 25)
		change_meter("institutional_credibility", -25)
		change_meter("public_pressure", 8)
	else:
		change_meter("truth_integrity", -8)
		change_meter("institutional_credibility", -5)
	show_release_language()

func controlled_language_key(level: String) -> String:
	match level:
		"Confirmed": return "confirmed"
		"Likely": return "likely"
		"Possible": return "possible"
		"Unverified": return "unverified"
		"Disputed": return "disputed"
		"Manipulated / Unclear": return "manipulated_unclear"
		_: return "unverified"

func recommended_language() -> String:
	var scenario_keys: Array = scenario.get("recommended_language_keys", [])
	if scenario_keys.size() > 0:
		var lines: Array = []
		for key in scenario_keys:
			if controlled_language.has(key):
				lines.append("[%s] %s" % [key, controlled_language.get(key, "")])
		if lines.size() > 0:
			return "\n".join(lines)
	var key := controlled_language_key(confidence_choice)
	return controlled_language.get(key, "Use cautious language matched to the evidence. Do not overclaim.")

func show_release_language() -> void:
	clear_ui()
	add_title("Public Release Decision")
	add_dashboard()
	add_text("Confidence selected: " + confidence_choice)
	add_text("Recommended controlled language:")
	add_text("\"%s\"" % recommended_language())
	add_text("Choose a release posture. Language must match evidence level and escalation risk.")
	for option in scenario.get("release_options", []):
		add_button(option.get("label", "Release option"), func(o=option): choose_release(o))
	add_button("Back to Confidence Scoring", Callable(self, "show_confidence"))

func choose_release(option: Dictionary) -> void:
	release_choice = option
	apply_pressure_tick(3, 5, "Public release posture selected")
	for key in option.get("effects", {}).keys():
		change_meter(key, int(option["effects"][key]))
	show_actions()

func action_summary() -> String:
	var lines: Array = []
	for key in action_labels.keys():
		var prefix := "✓ " if actions.get(key, false) else "✗ "
		lines.append(prefix + action_labels[key])
	return "\n".join(lines)

func show_actions() -> void:
	clear_ui()
	add_title("Final Governance Actions")
	add_dashboard()
	add_text("Choose immediate actions before final decision.")
	for key in action_labels.keys():
		var prefix := "✓ " if actions.get(key, false) else "☐ "
		add_button(prefix + action_labels[key], func(k=key): toggle_action(k))
	add_subtitle("Selected Actions")
	add_text(action_summary())
	add_button("Submit Final Decision", Callable(self, "finalize_decision"))

func toggle_action(name: String) -> void:
	actions[name] = not actions[name]
	show_actions()

func evaluate_evidence_marks() -> void:
	evidence_marking_notes = []
	var used_count := 0
	var reviewed_count := reviewed_cards.size()
	for card in scenario.get("evidence_cards", []):
		var card_id := card.get("id", "")
		var marks = card_marks.get(card_id, {})
		var tags: Array = card.get("tags", [])
		var states: Array = card.get("states", [])
		var title := card.get("title", card_id)
		if marks.get("used", false):
			used_count += 1
		var civilian_sensitive := tags.has("civilian_risk") or tags.has("privacy_risk") or tags.has("family_inquiry") or states.has("Sensitive") or card.get("reliability", "") == "sensitive"
		if civilian_sensitive:
			if marks.get("sensitive", false):
				change_meter("civilian_safety", 6)
				evidence_marking_notes.append("Civilian protection: '%s' was treated as sensitive." % title)
			else:
				change_meter("civilian_safety", -12)
				change_meter("institutional_credibility", -6)
				evidence_marking_notes.append("Civilian protection gap: '%s' carried civilian or privacy risk but was not marked sensitive." % title)
		var integrity_sensitive := tags.has("bot_amplification") or tags.has("synthetic_audio_possible") or tags.has("viral") or tags.has("casualty_claim_unverified")
		if integrity_sensitive:
			if marks.get("flagged", false):
				change_meter("truth_integrity", 5)
				evidence_marking_notes.append("Information integrity: '%s' was flagged for review." % title)
			else:
				change_meter("truth_integrity", -6)
				change_meter("public_pressure", 4)
				evidence_marking_notes.append("Information-integrity miss: '%s' had viral, bot, synthetic, or casualty-claim risk but was not flagged." % title)
		var followup_needed := states.has("Requires Follow-Up") or tags.has("translation_uncertainty") or tags.has("original_missing") or tags.has("metadata_missing")
		if followup_needed:
			if marks.get("follow_up", false):
				change_meter("institutional_credibility", 4)
				evidence_marking_notes.append("Follow-up discipline: '%s' was marked for follow-up." % title)
			else:
				change_meter("institutional_credibility", -5)
				evidence_marking_notes.append("Follow-up gap: '%s' needed follow-up but was not marked." % title)
	if used_count >= 2:
		change_meter("truth_integrity", 10)
		change_meter("institutional_credibility", 3)
		evidence_marking_notes.append("Confidence discipline: %s evidence items were marked as used in the confidence assessment." % used_count)
	else:
		change_meter("truth_integrity", -8)
		change_meter("institutional_credibility", -5)
		evidence_marking_notes.append("Confidence discipline gap: fewer than 2 evidence items were marked as used in the confidence assessment.")
	if reviewed_count >= scenario.get("evidence_cards", []).size():
		change_meter("institutional_credibility", 7)
		change_meter("truth_integrity", 4)
		evidence_marking_notes.append("Evidence completeness: all available evidence cards were reviewed.")

func evidence_marking_feedback() -> String:
	if evidence_marking_notes.size() == 0:
		return "Evidence marking was not evaluated."
	var lines: Array = []
	for note in evidence_marking_notes:
		lines.append("• " + note)
	return "\n".join(lines)

func finalize_decision() -> void:
	apply_pressure_tick(2, 4, "Final governance action package submitted")
	evaluate_evidence_marks()
	if actions.get("protect_civilians", false):
		change_meter("civilian_safety", 20)
		change_meter("institutional_credibility", 5)
	else:
		change_meter("civilian_safety", -18)
		change_meter("institutional_credibility", -5)
	if actions.get("info_integrity_review", false):
		change_meter("truth_integrity", 10)
		change_meter("escalation_risk", -10)
		change_meter("public_pressure", -4)
	else:
		change_meter("truth_integrity", -6)
	if actions.get("deescalation_channel", false):
		change_meter("escalation_risk", -14)
		change_meter("institutional_credibility", 4)
	if actions.get("request_original_media", false):
		change_meter("truth_integrity", 5)
		change_meter("decision_timeliness", -4)
	if actions.get("senior_review", false):
		change_meter("institutional_credibility", 7)
		change_meter("decision_timeliness", -3)
	if actions.get("humanitarian_check", false):
		change_meter("civilian_safety", 10)
		change_meter("institutional_credibility", 4)
	show_consequence()

func performance_score() -> int:
	var score := 0
	score += int(meters.get("truth_integrity", 0))
	score += int(100 - meters.get("escalation_risk", 0))
	score += int(meters.get("civilian_safety", 0))
	score += int(meters.get("institutional_credibility", 0))
	score += int(meters.get("decision_timeliness", 0))
	score += int(100 - meters.get("public_pressure", 0))
	var base := int(round(float(score) / 6.0))
	var bonus := 0
	if reviewed_cards.size() >= scenario.get("evidence_cards", []).size(): bonus += 3
	if scenario.get("correct_confidence_range", []).has(confidence_choice): bonus += 4
	if release_choice.get("id", "") in ["safe_cautious", "corrective", "humanitarian_cautious"]: bonus += 3
	if actions.get("protect_civilians", false): bonus += 3
	if actions.get("info_integrity_review", false): bonus += 3
	return clamp(base + bonus, 0, 100)

func performance_label() -> String:
	var score := performance_score()
	if score >= 85: return "Excellent governance discipline"
	if score >= 70: return "Credible crisis handling"
	if score >= 55: return "Mixed outcome"
	return "Governance failure risk"

func show_consequence() -> void:
	clear_ui()
	add_title("Consequence Screen")
	add_dashboard()
	final_performance = performance_label()
	add_text("Overall performance: %s (%s / 100)" % [final_performance, performance_score()])
	if meters.get("truth_integrity", 0) >= 75 and meters.get("civilian_safety", 0) >= 70 and meters.get("escalation_risk", 100) <= 55:
		add_text("Responsible crisis handling. The team avoided overclaiming, protected civilians, and preserved decision space.")
	elif meters.get("truth_integrity", 0) < 50:
		add_text("Truth failure. Weak or ambiguous evidence became too strong a claim.")
	elif meters.get("civilian_safety", 0) < 50:
		add_text("Civilian protection failure. Sensitive people or locations may have been exposed.")
	elif meters.get("escalation_risk", 0) > 70:
		add_text("Escalation warning. Public or institutional action increased crisis pressure.")
	else:
		add_text("Mixed outcome. The team preserved some credibility but missed key governance gates.")
	add_button("Score Summary", Callable(self, "show_score_summary"))
	add_button("Open After-Action Review", Callable(self, "show_aar"))
	add_button("Facilitator / Observer View", Callable(self, "show_facilitator_observer"))
	add_button("Restart Scenario", Callable(self, "restart"))

func show_score_summary() -> void:
	clear_ui()
	add_title("Score Summary")
	add_text("Scenario: " + scenario.get("title", ""))
	add_text("Final Confidence Choice: " + confidence_choice)
	add_text("Public Release Decision: " + release_choice.get("label", "None"))
	add_subtitle("Actions Taken")
	add_text(action_summary())
	add_dashboard()
	add_text("Overall Performance: %s (%s / 100)" % [performance_label(), performance_score()])
	add_button("Export AAR Report", Callable(self, "export_aar_report"))
	if last_aar_path != "": add_text("Last exported AAR: " + last_aar_path)
	add_button("Open After-Action Review", Callable(self, "show_aar"))

func bullet_section(title: String, items: Array) -> String:
	var body := "• No major note recorded."
	if items.size() > 0:
		var lines: Array = []
		for item in items:
			lines.append("• " + str(item))
		body = "\n".join(lines)
	return title + "\n" + body

func aar_feedback() -> String:
	var got_right: Array = []
	var overclaimed: Array = []
	var missed: Array = []
	var civilian_review: Array = []
	var integrity_review: Array = []
	var recommended: Array = []
	var correct_range: Array = scenario.get("correct_confidence_range", [])
	var unsafe: Array = scenario.get("unsafe_choices", [])

	if reviewed_cards.size() >= required_cards():
		got_right.append("You reviewed enough evidence to unlock confidence scoring: %s / %s." % [reviewed_cards.size(), scenario.get("evidence_cards", []).size()])
	else:
		missed.append("You did not review enough evidence before judgment. This should remain locked.")

	if correct_range.has(confidence_choice):
		got_right.append("Your confidence choice was defensible for the available evidence: " + confidence_choice + ".")
	elif unsafe.has(confidence_choice):
		overclaimed.append("You selected " + confidence_choice + ", but the evidence did not support that certainty.")
		recommended.append("Use a lower confidence level within: " + ", ".join(correct_range) + ".")
	else:
		missed.append("Confidence choice was partly misaligned. Safer range: " + ", ".join(correct_range) + ".")

	if release_choice.get("id", "") == "overclaim":
		overclaimed.append("Release language made a strong attribution that increased escalation risk and reduced credibility.")
		recommended.append("Use controlled language matched to uncertainty.")
	elif release_choice.get("id", "") in ["safe_cautious", "corrective", "humanitarian_cautious"]:
		got_right.append("Release language was proportionate and avoided premature attribution.")
	elif release_choice.get("id", "") == "hold_all":
		missed.append("Holding all comment protected truth but may have reduced timeliness. A cautious holding statement may be stronger.")

	if actions.get("protect_civilians", false):
		civilian_review.append("Civilian protection action was selected.")
	else:
		civilian_review.append("Civilian protection action was not selected. Sensitive people or locations may remain exposed.")
		recommended.append("Select civilian protection or redaction when civilian-risk evidence appears.")

	if actions.get("info_integrity_review", false):
		integrity_review.append("Information-integrity review was triggered.")
	else:
		integrity_review.append("Information-integrity review was not triggered.")
		recommended.append("Trigger information-integrity review when viral, synthetic, translated, or bot-amplified material appears.")

	if actions.get("deescalation_channel", false):
		got_right.append("De-escalation / diplomatic review channel was activated.")
	if actions.get("humanitarian_check", false):
		got_right.append("Humanitarian check separated safety action from public attribution.")
	if actions.get("senior_review", false):
		got_right.append("Senior human review strengthened institutional accountability.")

	if evidence_marking_notes.size() > 0:
		missed.append("Evidence marking generated additional diagnostic notes below.")

	var sections: Array = []
	sections.append(bullet_section("What You Got Right", got_right))
	sections.append(bullet_section("What You Overclaimed", overclaimed))
	sections.append(bullet_section("What You Missed", missed))
	sections.append(bullet_section("Civilian Protection Review", civilian_review))
	sections.append(bullet_section("Information Integrity Review", integrity_review))
	sections.append("Evidence Marking Review\n" + evidence_marking_feedback())
	sections.append(bullet_section("Recommended Better Decision", recommended))
	if facilitator_mode:
		sections.append(bullet_section("Facilitator Notes", scenario.get("facilitator_notes", [])))
	return "\n\n".join(sections)

func show_aar() -> void:
	clear_ui()
	add_title("After-Action Review")
	add_text("Confidence choice: " + confidence_choice)
	add_text("Release choice: " + release_choice.get("label", "None"))
	add_subtitle("Selected Actions")
	add_text(action_summary())
	add_subtitle("Decision-Specific Feedback")
	add_text(aar_feedback())
	add_subtitle("Core Lessons")
	for objective in scenario.get("learning_objectives", []): add_text("• " + objective)
	add_button("Export AAR Report", Callable(self, "export_aar_report"))
	if last_aar_path != "": add_text("Last exported AAR: " + last_aar_path)
	add_button("Facilitator / Observer View", Callable(self, "show_facilitator_observer"))
	add_button("Restart Scenario", Callable(self, "restart"))

func export_aar_report() -> void:
	var dir_abs := ProjectSettings.globalize_path("user://aar_reports")
	DirAccess.make_dir_recursive_absolute(dir_abs)
	var unix := Time.get_unix_time_from_system()
	var file_name := "aar_%s_%s.json" % [scenario.get("scenario_id", "scenario"), unix]
	var report_path := "user://aar_reports/" + file_name
	var payload := {
		"game_version": "0.2.1",
		"scenario_id": scenario.get("scenario_id", ""),
		"scenario_title": scenario.get("title", ""),
		"evidence_reviewed": reviewed_cards,
		"card_marks": card_marks,
		"confidence_choice": confidence_choice,
		"correct_confidence_range": scenario.get("correct_confidence_range", []),
		"release_choice": release_choice,
		"actions": actions,
		"meters_final": meters,
		"meters_starting": starting_meters,
		"remaining_minutes": remaining_minutes,
		"performance_score": performance_score(),
		"performance_label": performance_label(),
		"pressure_events": pressure_events,
		"evidence_marking_notes": evidence_marking_notes,
		"aar_feedback": aar_feedback(),
		"debrief_prompts": scenario.get("debrief_prompts", [])
	}
	var file := FileAccess.open(report_path, FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(payload, "\t"))
		last_aar_path = report_path
	show_score_summary()

func show_facilitator_observer() -> void:
	clear_ui()
	add_title("Facilitator / Observer Mode")
	add_text("Scenario: " + scenario.get("title", ""))
	add_text("Player confidence choice: " + confidence_choice)
	add_text("Hidden correct-confidence range: " + ", ".join(scenario.get("correct_confidence_range", [])))
	add_text("Unsafe confidence choices: " + ", ".join(scenario.get("unsafe_choices", [])))
	add_text("Evidence reviewed: " + ", ".join(reviewed_cards))
	add_subtitle("Player Actions")
	add_text(action_summary())
	add_subtitle("Score Summary")
	add_dashboard()
	add_subtitle("Teaching Notes")
	for note in scenario.get("facilitator_notes", []): add_text("• " + note)
	add_subtitle("Debrief Prompts")
	for prompt in scenario.get("debrief_prompts", []): add_text("• " + prompt)
	add_button("Back to AAR", Callable(self, "show_aar"))
	add_button("Restart Scenario", Callable(self, "restart"))

func restart() -> void:
	if current_scenario_id != "": reset_for_scenario(current_scenario_id)
	show_main_menu()
