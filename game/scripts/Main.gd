extends Control

var scenarios: Dictionary = {}
var scenario: Dictionary = {}
var current_scenario_id: String = ""
var controlled_language: Dictionary = {}
var scoring_rubric: Dictionary = {}
var governance_policy: Dictionary = {}
var policy_valid: bool = false
var meters: Dictionary = {}
var starting_meters: Dictionary = {}
var reviewed_cards: Array = []
var card_marks: Dictionary = {}
var confidence_choice: String = ""
var confidence_history: Array = []
var corroboration_choice: String = ""
var corroboration_history: Array = []
var authenticity_choice: String = ""
var authenticity_history: Array = []
var release_choice: Dictionary = {}
var release_history: Array = []
var facilitator_mode: bool = false
var session_mode: String = "practice"
var confirmed_decision_digest: String = ""
var remaining_minutes: int = 30
var last_aar_path: String = ""
var final_performance: String = ""
var pressure_events: Array = []
var evidence_marking_notes: Array = []
var half_time_warning_given: bool = false
var final_warning_given: bool = false
var deadline_hit_given: bool = false
var human_confirmation: bool = false
var decision_finalized: bool = false
var score_breakdown: Dictionary = {}
var decision_digest: String = ""
var audit_events: Array = []
var export_status: String = ""
var export_directory_abs: String = ""
var active_scroll: ScrollContainer
var current_screen_id: String = ""
var scroll_positions: Dictionary = {}

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

const REQUIRED_REVIEWED_CARDS_DEFAULT := 0
const CONFIDENCE_LEVELS := ["Confirmed", "Likely", "Possible", "Unverified"]
const CORROBORATION_LEVELS := ["Corroborated", "Partially corroborated", "Contradictory", "Uncorroborated"]
const AUTHENTICITY_LEVELS := ["No indicators identified", "Manipulation suspected", "Authenticity unclear", "Not applicable"]
const SCENARIO_FILES := [
	"res://data/scenarios/scenario_01_viral_collision_video.json",
	"res://data/scenarios/scenario_02_deepfake_distress_call.json"
]

var root_box: VBoxContainer
var first_focus_control: Control

func _ready() -> void:
	load_all_data()
	show_main_menu()

func load_all_data() -> void:
	load_scenarios()
	load_controlled_language()
	load_scoring_rubric()
	load_governance_policy()

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

func load_governance_policy() -> void:
	policy_valid = false
	var file := FileAccess.open("res://data/governance/policy.json", FileAccess.READ)
	if file == null:
		governance_policy = {}
		push_error("Governance policy is missing. The simulation fails closed.")
		return
	var parsed = JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("Governance policy is not a JSON object. The simulation fails closed.")
		return
	governance_policy = parsed
	var required_booleans := [
		"simulation_only",
		"allow_live_data",
		"allow_autonomous_release",
		"allow_external_action_execution",
		"allow_telemetry",
		"allow_external_ai",
		"require_human_final_confirmation",
		"require_complete_evidence_review",
		"require_in_memory_audit_chain",
		"require_action_budget",
		"require_final_review_screen",
		"require_decision_digest_confirmation",
		"require_separated_experience_modes"
	]
	for key in required_booleans:
		if not governance_policy.has(key) or typeof(governance_policy[key]) != TYPE_BOOL:
			push_error("Governance policy has an invalid Boolean field: " + key)
			return
	if not governance_policy.get("simulation_only", false):
		push_error("Governance policy must keep this project simulation-only.")
		return
	if governance_policy.get("allow_live_data", true) or governance_policy.get("allow_autonomous_release", true) or governance_policy.get("allow_external_action_execution", true) or governance_policy.get("allow_telemetry", true) or governance_policy.get("allow_external_ai", true):
		push_error("Governance policy attempts to enable prohibited capabilities.")
		return
	for safeguard in ["require_human_final_confirmation", "require_complete_evidence_review", "require_in_memory_audit_chain", "require_action_budget", "require_final_review_screen", "require_decision_digest_confirmation", "require_separated_experience_modes"]:
		if not governance_policy.get(safeguard, false):
			push_error("Governance policy disables a mandatory safeguard: " + safeguard)
			return
	if governance_policy.get("audit_hash_algorithm", "") != "sha256" or governance_policy.get("decision_digest_algorithm", "") != "sha256":
		push_error("Governance policy specifies an unsupported digest algorithm.")
		return
	var expected_components := {"evidence_review": 10, "evidence_marking": 20, "confidence": 15, "corroboration": 10, "authenticity": 10, "release": 15, "actions": 15, "timeliness": 5}
	if governance_policy.get("required_score_components", {}) != expected_components:
		push_error("Governance policy score components do not match the executable scoring contract.")
		return
	if governance_policy.get("allowed_confidence_levels", []) != CONFIDENCE_LEVELS:
		push_error("Governance policy confidence levels do not match the executable contract.")
		return
	if governance_policy.get("allowed_corroboration_levels", []) != CORROBORATION_LEVELS:
		push_error("Governance policy corroboration levels do not match the executable contract.")
		return
	if governance_policy.get("allowed_authenticity_levels", []) != AUTHENTICITY_LEVELS:
		push_error("Governance policy authenticity levels do not match the executable contract.")
		return
	policy_valid = true

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
	confidence_history = []
	corroboration_choice = ""
	corroboration_history = []
	authenticity_choice = ""
	authenticity_history = []
	release_choice = {}
	release_history = []
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
	export_status = ""
	export_directory_abs = ""
	final_performance = ""
	pressure_events = []
	evidence_marking_notes = []
	half_time_warning_given = false
	final_warning_given = false
	deadline_hit_given = false
	human_confirmation = false
	confirmed_decision_digest = ""
	decision_finalized = false
	score_breakdown = {}
	decision_digest = ""
	audit_events = []
	scroll_positions = {}
	current_screen_id = ""

func clear_ui(screen_id: String = "") -> void:
	if active_scroll != null and is_instance_valid(active_scroll) and current_screen_id != "":
		scroll_positions[current_screen_id] = active_scroll.scroll_vertical
	first_focus_control = null
	for child in get_children():
		remove_child(child)
		child.queue_free()
	current_screen_id = screen_id
	var scroll := ScrollContainer.new()
	active_scroll = scroll
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
	root_box.custom_minimum_size = Vector2(0, 0)
	root_box.add_theme_constant_override("separation", 10)
	scroll.add_child(root_box)
	if screen_id != "" and scroll_positions.has(screen_id):
		scroll.set_deferred("scroll_vertical", int(scroll_positions[screen_id]))

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

func add_button(text: String, callback: Callable, tooltip: String = "", safe_focus: bool = false) -> Button:
	var button := Button.new()
	button.text = text
	button.focus_mode = Control.FOCUS_ALL
	button.tooltip_text = tooltip if tooltip != "" else text
	button.pressed.connect(callback)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	root_box.add_child(button)
	if safe_focus:
		first_focus_control = button
		button.call_deferred("grab_focus")
	return button

func add_checkbox(text: String, selected: bool, callback: Callable, tooltip: String = "", safe_focus: bool = false) -> CheckBox:
	var checkbox := CheckBox.new()
	checkbox.text = text
	checkbox.button_pressed = selected
	checkbox.focus_mode = Control.FOCUS_ALL
	checkbox.tooltip_text = tooltip if tooltip != "" else text
	checkbox.toggled.connect(callback)
	checkbox.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	checkbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	root_box.add_child(checkbox)
	if safe_focus:
		first_focus_control = checkbox
		checkbox.call_deferred("grab_focus")
	return checkbox

func add_rich_text(text: String) -> RichTextLabel:
	var rich := RichTextLabel.new()
	rich.bbcode_enabled = false
	rich.fit_content = true
	rich.text = text
	rich.custom_minimum_size = Vector2(0, 120)
	rich.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	root_box.add_child(rich)
	return rich

func add_facilitator_banner() -> void:
	if facilitator_mode:
		var banner := Label.new()
		banner.text = "FACILITATOR MODE  -  answer-revealing indicators are visible. Do not use this mode for blind assessment."
		banner.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		banner.add_theme_font_size_override("font_size", 17)
		root_box.add_child(banner)

func add_progress_indicator(step: int, total: int, label: String) -> void:
	add_text("Step %s of %s  -  %s" % [step, total, label])

func add_status_strip() -> void:
	add_text("Time: %s min | Reviewed: %s/%s | Confidence: %s | Corroboration: %s | Authenticity: %s" % [remaining_minutes, reviewed_cards.size(), scenario.get("evidence_cards", []).size(), confidence_choice if confidence_choice != "" else "Not selected", corroboration_choice if corroboration_choice != "" else "Not selected", authenticity_choice if authenticity_choice != "" else "Not selected"])
	if pressure_events.size() > 0:
		add_text("Latest pressure event: " + str(pressure_events[pressure_events.size() - 1]))

func meter_label(key: String) -> String:
	var meta = scoring_rubric.get("meters", {}).get(key, {})
	return meta.get("label", key.capitalize())

func add_dashboard() -> void:
	add_subtitle("Crisis Dashboard")
	add_text("Decision clock: %s minutes remaining | Evidence reviewed: %s / %s | Current confidence: %s" % [remaining_minutes, reviewed_cards.size(), scenario.get("evidence_cards", []).size(), confidence_choice if confidence_choice != "" else "Not selected"])
	if pressure_events.size() > 0:
		add_text("Latest pressure event: " + str(pressure_events[pressure_events.size() - 1]))
	var indicators := {
		"Evidence Integrity": int(meters.get("truth_integrity", 0)),
		"Escalation Control": 100 - int(meters.get("escalation_risk", 0)),
		"Civilian Protection": int(meters.get("civilian_safety", 0)),
		"Institutional Credibility": int(meters.get("institutional_credibility", 0)),
		"Decision Timeliness": int(meters.get("decision_timeliness", 0))
	}
	for label_text in indicators.keys():
		var value := clamp(int(indicators[label_text]), 0, 100)
		var label := Label.new()
		label.text = "↑ %s: %s / 100 (higher is better)" % [label_text, value]
		root_box.add_child(label)
		var bar := ProgressBar.new()
		bar.min_value = 0
		bar.max_value = 100
		bar.value = value
		bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		root_box.add_child(bar)
	add_text("Scenario state  -  Public Pressure: %s / 100. This is context, not a performance score." % int(meters.get("public_pressure", 0)))

func change_meter(name: String, amount: int) -> void:
	meters[name] = clamp(int(meters.get(name, 0)) + amount, 0, 100)

func advance_time() -> void:
	invalidate_human_confirmation("decision clock advanced")
	var step := int(scenario.get("time_step_minutes", 5))
	apply_pressure_tick(step, 8, "Manual pressure advance")
	show_evidence()

func show_time_advance_confirmation() -> void:
	clear_ui("advance_time_confirmation")
	add_title("Confirm Time Advance")
	add_text("Advancing time increases public pressure and may reduce decision timeliness. This cannot be undone within the current simulation run.")
	add_button("Cancel and Return to Evidence", Callable(self, "show_evidence"), "Do not advance time", true)
	add_button("Confirm: Advance 5 Minutes", Callable(self, "advance_time"), "Apply the simulated time and pressure change")

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
	clear_ui("main_menu")
	add_title("Peace OS: Crisis Room")
	add_text("Peace OS is the product name. This project is not a computer operating system, operational command platform, intelligence product, or autonomous decision system. Crisis Room is a bounded fictional governance simulation.")
	if not policy_valid:
		add_text("STOP: Governance policy validation failed. The simulation is unavailable until the policy is repaired.")
		add_button("Reload Policy", Callable(self, "reload_policy"), "Reload and validate the local governance policy", true)
		return
	add_text("Doctrine: verification before amplification, human control before release, civilian protection before intelligence value, and explicit uncertainty before public attribution.")
	add_subtitle("Select Experience Mode")
	add_text("Current mode: " + mode_label())
	add_text("Mode boundary: Assessment withholds coaching but is not secure or proctored. Facilitator mode intentionally exposes teaching and scoring guidance.")
	add_button("Practice Mode  -  guided learner run", func(): set_session_mode("practice"), "Use for learning and revision", session_mode == "practice")
	add_button("Assessment Mode  -  cues withheld until finalization", func(): set_session_mode("assessment"), "Self-guided assessment mode; not secure or proctored")
	add_button("Facilitator Mode  -  instructor/observer view", func(): set_session_mode("facilitator"), "Answer-revealing mode; do not use for blind assessment")
	add_subtitle("Select Scenario")
	var first_scenario := true
	for id in scenarios.keys():
		var sc = scenarios[id]
		add_button(sc.get("title", id), func(sid=id): start_scenario(sid), "Open this fictional scenario", first_scenario and session_mode != "")
		first_scenario = false
	add_button("Policy Boundary", Callable(self, "show_policy_boundary"))

func reload_policy() -> void:
	load_governance_policy()
	show_main_menu()

func mode_label() -> String:
	match session_mode:
		"practice": return "Practice"
		"assessment": return "Assessment"
		"facilitator": return "Facilitator"
		_: return "Practice"

func set_session_mode(mode: String) -> void:
	if not ["practice", "assessment", "facilitator"].has(mode):
		mode = "practice"
	session_mode = mode
	facilitator_mode = mode == "facilitator"
	show_main_menu()

func toggle_facilitator_mode() -> void:
	set_session_mode("practice" if facilitator_mode else "facilitator")

func set_facilitator_mode(enabled: bool) -> void:
	set_session_mode("facilitator" if enabled else "practice")

func start_scenario(scenario_id: String) -> void:
	reset_for_scenario(scenario_id)
	append_audit_event("scenario_started", {"scenario_id": scenario_id, "policy_version": governance_policy.get("policy_version", "unknown")})
	show_briefing()

func show_policy_boundary() -> void:
	clear_ui("policy_boundary")
	add_title("Policy Boundary")
	add_text("This is a fictional serious-game source prototype. It is not an operational tool, intelligence system, legal attribution engine, official government product, or autonomous release authority. It uses no live data and executes no external action.")
	add_text("The in-memory hash chain is tamper-evident only while the original record is retained. It is unsigned and not independently anchored. It does not independently prove who made the decision or when.")
	add_button("Back", Callable(self, "show_main_menu"), "Return to the main menu", true)

func show_briefing() -> void:
	clear_ui("briefing")
	add_progress_indicator(1, 8, "Scenario briefing")
	add_facilitator_banner()
	add_title(scenario.get("title", "Scenario"))
	add_text(scenario.get("briefing", ""))
	add_status_strip()
	if facilitator_mode:
		add_facilitator_panel()
	add_text("Mission: review every evidence card, classify it without answer leakage, separate confidence from corroboration and authenticity, choose bounded actions, and review the complete package before human confirmation.")
	add_button("Open Evidence Inbox", Callable(self, "show_evidence"), "Begin evidence review", true)
	add_button("Back to Main Menu", Callable(self, "show_main_menu"))

func add_facilitator_panel() -> void:
	add_subtitle("Facilitator / Observer Notes")
	add_text("Defensible confidence range: " + ", ".join(scenario.get("correct_confidence_range", [])))
	add_text("Defensible corroboration range: " + ", ".join(scenario.get("correct_corroboration_range", [])))
	add_text("Defensible authenticity range: " + ", ".join(scenario.get("correct_authenticity_range", [])))
	add_text("Unsafe confidence choices: " + ", ".join(scenario.get("unsafe_choices", [])))
	for note in scenario.get("facilitator_notes", []):
		add_text("• " + note)

func show_evidence() -> void:
	clear_ui("evidence")
	add_progress_indicator(2, 8, "Evidence review")
	add_facilitator_banner()
	add_title("Evidence Inbox")
	add_text("Review every card. Mark what requires attention, protection, follow-up, and use in the final assessment. Learner mode does not expose the scoring key.")
	add_text("Required before scoring: %s of %s evidence cards." % [required_cards(), scenario.get("evidence_cards", []).size()])
	var focused := false
	for card in scenario.get("evidence_cards", []):
		var card_id := card.get("id", "")
		var marks = card_marks.get(card_id, {})
		var state := "[Reviewed] " if marks.get("reviewed", false) else "[Unread] "
		var flags: Array = []
		if marks.get("flagged", false): flags.append("Flagged")
		if marks.get("sensitive", false): flags.append("Sensitive")
		if marks.get("follow_up", false): flags.append("Follow-Up")
		if marks.get("used", false): flags.append("Used in Assessment")
		var suffix := "" if flags.size() == 0 else "  -  Player marks: " + ", ".join(flags)
		if facilitator_mode and card.get("facilitator_indicators", []).size() > 0:
			suffix += "  -  Facilitator indicators: " + ", ".join(card.get("facilitator_indicators", []))
		var should_focus := not focused and not marks.get("reviewed", false)
		add_button(state + card.get("title", "Evidence") + suffix, func(c=card): open_card(c), "Open evidence card", should_focus)
		if should_focus:
			focused = true
	add_text("Reviewed cards: %s / %s" % [reviewed_cards.size(), scenario.get("evidence_cards", []).size()])
	if reviewed_cards.size() >= required_cards():
		add_button("Proceed to Confidence Assessment", Callable(self, "show_confidence"), "Continue after complete review", not focused)
	else:
		add_text("Gate active: assessment is locked until every evidence card is reviewed.")
		var locked := Button.new()
		locked.text = "Assessment Locked"
		locked.disabled = true
		root_box.add_child(locked)
	add_button("Advance 5 Minutes", Callable(self, "show_time_advance_confirmation"), "Opens a confirmation before simulated time advances")
	add_button("Back to Briefing", Callable(self, "show_briefing"))
	add_status_strip()

func required_cards() -> int:
	if governance_policy.get("require_complete_evidence_review", true):
		return scenario.get("evidence_cards", []).size()
	return int(scenario.get("minimum_evidence_cards_required_before_scoring", REQUIRED_REVIEWED_CARDS_DEFAULT))

func open_card(card: Dictionary) -> void:
	var card_id := card.get("id", "")
	var marks = card_marks.get(card_id, {})
	if not marks.get("reviewed", false):
		invalidate_human_confirmation("evidence reviewed")
		marks["reviewed"] = true
		if not reviewed_cards.has(card_id): reviewed_cards.append(card_id)
		apply_card_effects(card)
		apply_pressure_tick(2, 3, "Evidence reviewed: " + card.get("title", "Evidence"))
		append_audit_event("evidence_reviewed", {"card_id": card_id})
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
	var card_id := card.get("id", "")
	clear_ui("card_" + card_id)
	add_facilitator_banner()
	var marks = card_marks.get(card_id, {})
	add_title(card.get("title", "Evidence"))
	add_text(card.get("description", ""))
	if session_mode == "assessment":
		add_text("Assessment mode: authored metadata labels are withheld. Evaluate the evidence description and record your own judgment.")
	else:
		add_text("Tags: " + ", ".join(card.get("tags", [])))
		add_text("Source reliability label: " + card.get("reliability", "partial"))
	if facilitator_mode:
		var indicators: Array = card.get("facilitator_indicators", [])
		add_text("Facilitator indicators: " + (", ".join(indicators) if indicators.size() > 0 else "None listed"))
	add_text("Player markings: " + card_state_text(card_id))
	add_subtitle("Evidence Actions")
	add_checkbox("Flag for integrity risk", marks.get("flagged", false), func(value: bool, cid=card_id, c=card): set_card_mark(value, cid, "flagged", c), "Mark an integrity or reliability concern")
	add_checkbox("Protect as sensitive", marks.get("sensitive", false), func(value: bool, cid=card_id, c=card): set_card_mark(value, cid, "sensitive", c), "Mark civilian, privacy, or protected information")
	add_checkbox("Request follow-up", marks.get("follow_up", false), func(value: bool, cid=card_id, c=card): set_card_mark(value, cid, "follow_up", c), "Request additional verification")
	add_checkbox("Use in final assessment", marks.get("used", false), func(value: bool, cid=card_id, c=card): set_card_mark(value, cid, "used", c), "Use this item in the final epistemic assessment")
	add_button("Back to Evidence Inbox", Callable(self, "show_evidence"), "Return to the evidence list", true)
	add_status_strip()

func toggle_card_mark(card_id: String, key: String, card: Dictionary) -> void:
	var marks = card_marks.get(card_id, {})
	set_card_mark(not marks.get(key, false), card_id, key, card)

func invalidate_human_confirmation(reason: String) -> void:
	if human_confirmation or confirmed_decision_digest != "":
		human_confirmation = false
		confirmed_decision_digest = ""
		append_audit_event("human_confirmation_invalidated", {"reason": reason})

func set_card_mark(value: bool, card_id: String, key: String, card: Dictionary) -> void:
	var marks = card_marks.get(card_id, {})
	if bool(marks.get(key, false)) != value:
		invalidate_human_confirmation("evidence mark changed")
	marks[key] = value
	card_marks[card_id] = marks
	append_audit_event("evidence_mark_changed", {"card_id": card_id, "mark": key, "value": value})
	show_card_detail(card)

func card_state_text(card_id: String) -> String:
	var marks = card_marks.get(card_id, {})
	var states: Array = []
	states.append("Reviewed" if marks.get("reviewed", false) else "Unread")
	if marks.get("flagged", false): states.append("Flagged")
	if marks.get("sensitive", false): states.append("Sensitive")
	if marks.get("follow_up", false): states.append("Follow-up requested")
	if marks.get("used", false): states.append("Used in final assessment")
	return ", ".join(states)

func show_confidence() -> void:
	if reviewed_cards.size() < required_cards():
		show_evidence()
		return
	clear_ui("confidence")
	add_progress_indicator(3, 8, "Confidence magnitude")
	add_facilitator_banner()
	add_title("Confidence Assessment")
	add_text("Select the highest defensible confidence magnitude. Corroboration and media authenticity are assessed separately on the next screens.")
	add_button("Back to Evidence Inbox", Callable(self, "show_evidence"), "Revise evidence review", true)
	for level in CONFIDENCE_LEVELS:
		add_button(level, func(l=level): choose_confidence(l))
	add_status_strip()

func choose_confidence(level: String) -> void:
	if confidence_choice == level:
		show_corroboration()
		return
	var revision := confidence_choice != ""
	invalidate_human_confirmation("confidence changed")
	confidence_choice = level
	confidence_history.append(level)
	if revision:
		pressure_events.append("Confidence revised before finalization without a correction penalty.")
	else:
		apply_pressure_tick(2, 3, "Confidence magnitude selected")
	append_audit_event("confidence_selected", {"level": level, "revision": revision})
	show_corroboration()

func show_corroboration() -> void:
	clear_ui("corroboration")
	add_progress_indicator(4, 8, "Corroboration")
	add_facilitator_banner()
	add_title("Corroboration Assessment")
	add_text("Assess whether independent evidence supports, partly supports, contradicts, or fails to corroborate the claim.")
	add_button("Back to Confidence Assessment", Callable(self, "show_confidence"), "Revise confidence magnitude", true)
	for level in CORROBORATION_LEVELS:
		add_button(level, func(l=level): choose_corroboration(l))
	add_status_strip()

func choose_corroboration(level: String) -> void:
	if corroboration_choice == level:
		show_authenticity()
		return
	var revision := corroboration_choice != ""
	invalidate_human_confirmation("corroboration changed")
	corroboration_choice = level
	corroboration_history.append(level)
	append_audit_event("corroboration_selected", {"level": level, "revision": revision})
	show_authenticity()

func show_authenticity() -> void:
	clear_ui("authenticity")
	add_progress_indicator(5, 8, "Media authenticity")
	add_facilitator_banner()
	add_title("Authenticity Assessment")
	add_text("Assess media-integrity indicators separately from confidence and corroboration.")
	add_button("Back to Corroboration Assessment", Callable(self, "show_corroboration"), "Revise corroboration", true)
	for level in AUTHENTICITY_LEVELS:
		add_button(level, func(l=level): choose_authenticity(l))
	add_status_strip()

func choose_authenticity(level: String) -> void:
	if authenticity_choice == level:
		show_release_language()
		return
	var revision := authenticity_choice != ""
	invalidate_human_confirmation("authenticity changed")
	authenticity_choice = level
	authenticity_history.append(level)
	append_audit_event("authenticity_selected", {"level": level, "revision": revision})
	show_release_language()

func controlled_language_key(level: String) -> String:
	match level:
		"Confirmed": return "confirmed"
		"Likely": return "likely"
		"Possible": return "possible"
		"Unverified": return "unverified"
		_: return "unverified"

func recommended_language() -> String:
	var key := controlled_language_key(confidence_choice)
	return controlled_language.get(key, "Use cautious language matched to the evidence. Do not overclaim.")

func safer_language_recommendation() -> String:
	if scenario.get("correct_confidence_range", []).has(confidence_choice) and scenario.get("correct_corroboration_range", []).has(corroboration_choice) and scenario.get("correct_authenticity_range", []).has(authenticity_choice):
		return "Current epistemic choices are within the scenario's defensible ranges."
	var scenario_keys: Array = scenario.get("recommended_language_keys", [])
	var lines: Array = []
	for key in scenario_keys:
		if controlled_language.has(key):
			lines.append("[%s] %s" % [key, controlled_language.get(key, "")])
	return "System critique: the current package may overstate the evidence. Safer alternatives:\n" + "\n".join(lines)

func show_release_language() -> void:
	if confidence_choice == "" or corroboration_choice == "" or authenticity_choice == "":
		show_confidence()
		return
	clear_ui("release")
	add_progress_indicator(6, 8, "Public release posture")
	add_facilitator_banner()
	add_title("Public Release Decision")
	add_text("Current choice: confidence = %s; corroboration = %s; authenticity = %s." % [confidence_choice, corroboration_choice, authenticity_choice])
	add_text("Language aligned to the player's current confidence choice:")
	add_text("\"%s\"" % recommended_language())
	if session_mode == "assessment":
		add_text("Assessment mode: coaching and safer-answer feedback are withheld until finalization. This is self-guided and not a secure or proctored assessment.")
	elif session_mode == "facilitator":
		add_text("Facilitator analysis: " + safer_language_recommendation())
	else:
		add_text(safer_language_recommendation())
	add_button("Back to Authenticity Assessment", Callable(self, "show_authenticity"), "Revise authenticity assessment", true)
	for option in scenario.get("release_options", []):
		add_button(option.get("label", "Release option"), func(o=option): choose_release(o))
	add_status_strip()

func choose_release(option: Dictionary) -> void:
	var option_id := str(option.get("id", ""))
	if release_choice.get("id", "") == option_id:
		show_actions()
		return
	var revision := release_choice.size() > 0
	invalidate_human_confirmation("release posture changed")
	release_choice = option
	release_history.append(option_id)
	if revision:
		pressure_events.append("Release posture revised before finalization without a correction penalty.")
	else:
		apply_pressure_tick(2, 3, "Release posture selected")
	append_audit_event("release_posture_selected", {"release_id": option_id, "revision": revision})
	show_actions()

func action_summary(reveal_scores: bool = false) -> String:
	var lines: Array = []
	for key in action_labels.keys():
		var prefix := "✓ " if actions.get(key, false) else "○ "
		var costs: Dictionary = scenario.get("action_costs", {}).get(key, {})
		var label := "%s%s [time %s, authority %s]" % [prefix, action_labels[key], costs.get("time", 0), costs.get("authority", 0)]
		if reveal_scores:
			label += " [facilitator doctrine score %s]" % scenario.get("action_scores", {}).get(key, 0)
		lines.append(label)
	return "\n".join(lines)

func selected_action_costs() -> Dictionary:
	var result := {"time": 0, "authority": 0}
	var configured: Dictionary = scenario.get("action_costs", {})
	for action_name in configured.keys():
		if actions.get(action_name, false):
			result["time"] += int(configured[action_name].get("time", 0))
			result["authority"] += int(configured[action_name].get("authority", 0))
	return result

func action_plan_valid() -> bool:
	var costs := selected_action_costs()
	var budget: Dictionary = scenario.get("action_budget", {})
	return int(costs.get("time", 0)) <= int(budget.get("time", 0)) and int(costs.get("authority", 0)) <= int(budget.get("authority", 0))

func action_budget_text() -> String:
	var costs := selected_action_costs()
	var budget: Dictionary = scenario.get("action_budget", {})
	return "Action resources: time %s/%s; authority %s/%s." % [costs.get("time", 0), budget.get("time", 0), costs.get("authority", 0), budget.get("authority", 0)]

func show_actions() -> void:
	clear_ui("actions")
	add_progress_indicator(7, 8, "Bounded governance actions")
	add_facilitator_banner()
	add_title("Governance Action Plan")
	add_text("Choose a bounded plan. Selecting every action is not permitted because time and authority are limited.")
	add_button("Back to Public Release Decision", Callable(self, "show_release_language"), "Revise release posture", true)
	for key in action_labels.keys():
		var cost: Dictionary = scenario.get("action_costs", {}).get(key, {})
		var label := "%s [time %s, authority %s]" % [action_labels[key], cost.get("time", 0), cost.get("authority", 0)]
		if facilitator_mode:
			label += " [facilitator doctrine score %s]" % scenario.get("action_scores", {}).get(key, 0)
		add_checkbox(label, actions.get(key, false), func(value: bool, k=key): set_action(value, k), "Select or clear this simulated action")
	add_subtitle("Selected Plan")
	add_text(action_budget_text())
	if not action_plan_valid():
		add_text("Gate active: selected actions exceed the time or authority budget. Remove actions before continuing.")
	else:
		add_button("Review Complete Decision Package", Callable(self, "show_final_review"), "Open the consolidated final review")
	add_status_strip()

func toggle_action(name: String) -> void:
	set_action(not actions.get(name, false), name)

func set_action(value: bool, name: String) -> void:
	if bool(actions.get(name, false)) != value:
		invalidate_human_confirmation("governance action changed")
	actions[name] = value
	append_audit_event("governance_action_changed", {"action": name, "value": value})
	show_actions()

func toggle_human_confirmation() -> void:
	set_human_confirmation(not human_confirmation)

func set_human_confirmation(value: bool) -> void:
	human_confirmation = value
	confirmed_decision_digest = compute_decision_digest() if value else ""
	append_audit_event("human_confirmation_changed", {"confirmed": human_confirmation, "confirmed_decision_digest": confirmed_decision_digest})
	show_final_review()

func unresolved_risks() -> Array:
	var risks: Array = []
	if scenario.get("unsafe_choices", []).has(confidence_choice):
		risks.append("Confidence magnitude exceeds the scenario's defensible range.")
	if scenario.get("unsafe_corroboration_choices", []).has(corroboration_choice):
		risks.append("Corroboration is overstated.")
	if scenario.get("unsafe_authenticity_choices", []).has(authenticity_choice):
		risks.append("Media authenticity is overstated.")
	if release_choice.get("id", "") == "overclaim":
		risks.append("The selected release posture makes unsupported attribution.")
	if not actions.get("protect_civilians", false):
		risks.append("Civilian protection is not selected.")
	if not action_plan_valid():
		risks.append("Action plan exceeds available resources.")
	return risks

func show_final_review() -> void:
	if not action_plan_valid():
		show_actions()
		return
	clear_ui("final_review")
	add_progress_indicator(8, 8, "Final human review")
	add_facilitator_banner()
	add_title("Final Decision Review")
	add_text("Review the complete simulated package before human confirmation. Nothing on this screen executes a real-world action or publication.")
	add_button("Back to Governance Actions", Callable(self, "show_actions"), "Revise the action plan", true)
	add_subtitle("Epistemic Assessment")
	add_text("Confidence: " + confidence_choice)
	add_text("Corroboration: " + corroboration_choice)
	add_text("Authenticity: " + authenticity_choice)
	add_subtitle("Release Posture")
	add_text(release_choice.get("label", "None selected"))
	add_subtitle("Action Plan")
	add_text(action_budget_text())
	add_text(action_summary(facilitator_mode))
	add_subtitle("Unresolved Risks")
	var risks := unresolved_risks()
	if risks.size() == 0:
		add_text("No critical contradiction detected by the bounded source model. This is not professional validation.")
	else:
		for risk in risks:
			add_text("• " + str(risk))
	add_checkbox("Human release authority confirms this simulated decision after review", human_confirmation, Callable(self, "set_human_confirmation"), "Required human confirmation")
	if human_confirmation:
		add_button("Submit Final Simulated Decision", Callable(self, "finalize_decision"), "Finalize this fictional decision only")
	else:
		add_text("Gate active: finalization remains locked until explicit human confirmation.")

func evaluate_evidence_marks() -> void:
	evidence_marking_notes = []
	for card in scenario.get("evidence_cards", []):
		var card_id := str(card.get("id", ""))
		var title := str(card.get("title", card_id))
		var marks: Dictionary = card_marks.get(card_id, {})
		var expected: Dictionary = card.get("expected_marks", {})
		for mark_name in ["flagged", "sensitive", "follow_up", "used"]:
			var actual := bool(marks.get(mark_name, false))
			var wanted := bool(expected.get(mark_name, false))
			if actual == wanted:
				if actual:
					evidence_marking_notes.append("Aligned mark: '%s' correctly set %s." % [title, mark_name])
			else:
				if wanted:
					evidence_marking_notes.append("Missing mark: '%s' should have %s selected." % [title, mark_name])
				else:
					evidence_marking_notes.append("Overmarking: '%s' did not require %s." % [title, mark_name])
	var mark_score := evidence_marking_score()
	change_meter("truth_integrity", int(round(float(mark_score - 10) * 0.8)))
	change_meter("institutional_credibility", int(round(float(mark_score - 10) * 0.5)))
	if mark_score >= 18:
		change_meter("civilian_safety", 6)
	elif mark_score < 10:
		change_meter("civilian_safety", -8)
	evidence_marking_notes.append("Evidence-marking doctrine score: %s / 20." % mark_score)

func evidence_marking_metrics() -> Dictionary:
	var metrics: Dictionary = {}
	for mark_name in ["flagged", "sensitive", "follow_up", "used"]:
		var tp := 0
		var tn := 0
		var fp := 0
		var fn := 0
		for card in scenario.get("evidence_cards", []):
			var card_id := str(card.get("id", ""))
			var actual := bool(card_marks.get(card_id, {}).get(mark_name, false))
			var wanted := bool(card.get("expected_marks", {}).get(mark_name, false))
			if wanted and actual:
				tp += 1
			elif wanted and not actual:
				fn += 1
			elif not wanted and actual:
				fp += 1
			else:
				tn += 1
		var positives := tp + fn
		var negatives := tn + fp
		var recall := 0.0 if positives == 0 else float(tp) / float(positives)
		var specificity := 0.0 if negatives == 0 else float(tn) / float(negatives)
		var precision := 0.0 if tp + fp == 0 else float(tp) / float(tp + fp)
		var skill := max(0.0, recall + specificity - 1.0) if positives > 0 and negatives > 0 else 0.0
		metrics[mark_name] = {"tp": tp, "tn": tn, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "specificity": specificity, "chance_corrected_skill": skill}
	return metrics

func evidence_marking_score() -> int:
	var metrics := evidence_marking_metrics()
	if metrics.size() == 0:
		return 0
	var total_skill := 0.0
	for value in metrics.values():
		total_skill += float(value.get("chance_corrected_skill", 0.0))
	return int(round(20.0 * total_skill / float(metrics.size())))

func evidence_marking_feedback() -> String:
	var lines: Array = []
	for mark_name in evidence_marking_metrics().keys():
		var metric: Dictionary = evidence_marking_metrics()[mark_name]
		lines.append("%s  -  precision %.2f, recall %.2f, specificity %.2f, chance-corrected skill %.2f" % [mark_name.capitalize().replace("_", " "), metric.get("precision", 0.0), metric.get("recall", 0.0), metric.get("specificity", 0.0), metric.get("chance_corrected_skill", 0.0)])
	if evidence_marking_notes.size() > 0:
		for note in evidence_marking_notes:
			lines.append("• " + note)
	return "Evidence marking was not evaluated." if lines.size() == 0 else "\n".join(lines)

func apply_final_confidence_effects() -> void:
	var correct_range: Array = scenario.get("correct_confidence_range", [])
	var unsafe: Array = scenario.get("unsafe_choices", [])
	if correct_range.has(confidence_choice):
		change_meter("truth_integrity", 10)
		change_meter("institutional_credibility", 6)
	elif unsafe.has(confidence_choice):
		change_meter("truth_integrity", -25)
		change_meter("escalation_risk", 18)
		change_meter("institutional_credibility", -18)
	else:
		change_meter("truth_integrity", -5)
	if confidence_history.size() > 1 and unsafe.has(confidence_history[0]) and correct_range.has(confidence_choice):
		change_meter("institutional_credibility", 4)
	if scenario.get("correct_corroboration_range", []).has(corroboration_choice):
		change_meter("truth_integrity", 6)
	elif scenario.get("unsafe_corroboration_choices", []).has(corroboration_choice):
		change_meter("truth_integrity", -12)
		change_meter("escalation_risk", 8)
	if scenario.get("correct_authenticity_range", []).has(authenticity_choice):
		change_meter("truth_integrity", 6)
	elif scenario.get("unsafe_authenticity_choices", []).has(authenticity_choice):
		change_meter("truth_integrity", -12)
		change_meter("institutional_credibility", -8)

func apply_final_release_effects() -> void:
	for key in release_choice.get("effects", {}).keys():
		change_meter(key, int(release_choice["effects"][key]))

func apply_final_action_effects() -> void:
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
		change_meter("truth_integrity", 8)
		change_meter("institutional_credibility", 3)
	if actions.get("senior_review", false):
		change_meter("institutional_credibility", 9)
	if actions.get("humanitarian_check", false):
		change_meter("civilian_safety", 10)
		change_meter("institutional_credibility", 4)

func evidence_review_score() -> int:
	var total := scenario.get("evidence_cards", []).size()
	if total == 0:
		return 0
	return int(round(10.0 * float(reviewed_cards.size()) / float(total)))

func categorical_score(choice: String, correct: Array, unsafe: Array, maximum: int) -> int:
	if correct.has(choice):
		return maximum
	if unsafe.has(choice):
		return 0
	return int(floor(float(maximum) / 2.0))

func confidence_score() -> int:
	return categorical_score(confidence_choice, scenario.get("correct_confidence_range", []), scenario.get("unsafe_choices", []), 15)

func corroboration_score() -> int:
	return categorical_score(corroboration_choice, scenario.get("correct_corroboration_range", []), scenario.get("unsafe_corroboration_choices", []), 10)

func authenticity_score() -> int:
	return categorical_score(authenticity_choice, scenario.get("correct_authenticity_range", []), scenario.get("unsafe_authenticity_choices", []), 10)

func release_score() -> int:
	return clamp(int(release_choice.get("doctrine_score", 0)), 0, 15)

func actions_score() -> int:
	if not action_plan_valid():
		return 0
	var points := 0
	var configured: Dictionary = scenario.get("action_scores", {})
	for action_name in configured.keys():
		if actions.get(action_name, false):
			points += int(configured[action_name])
	return clamp(points, 0, 15)

func timeliness_score() -> int:
	if remaining_minutes >= 10:
		return 5
	if remaining_minutes >= 5:
		return 4
	if remaining_minutes > 0:
		return 2
	return 0

func build_score_breakdown() -> Dictionary:
	return {
		"evidence_review": {"points": evidence_review_score(), "maximum": 10},
		"evidence_marking": {"points": evidence_marking_score(), "maximum": 20, "metrics": evidence_marking_metrics()},
		"confidence": {"points": confidence_score(), "maximum": 15, "self_correction_recognized": confidence_history.size() > 1},
		"corroboration": {"points": corroboration_score(), "maximum": 10, "self_correction_recognized": corroboration_history.size() > 1},
		"authenticity": {"points": authenticity_score(), "maximum": 10, "self_correction_recognized": authenticity_history.size() > 1},
		"release": {"points": release_score(), "maximum": 15},
		"actions": {"points": actions_score(), "maximum": 15, "costs": selected_action_costs(), "budget": scenario.get("action_budget", {})},
		"timeliness": {"points": timeliness_score(), "maximum": 5}
	}

func finalize_decision() -> void:
	if decision_finalized:
		show_consequence()
		return
	if governance_policy.get("require_human_final_confirmation", true) and not human_confirmation:
		show_final_review()
		return
	if governance_policy.get("require_decision_digest_confirmation", true) and confirmed_decision_digest != compute_decision_digest():
		human_confirmation = false
		confirmed_decision_digest = ""
		append_audit_event("human_confirmation_digest_mismatch", {"reason": "decision changed after confirmation"})
		show_final_review()
		return
	if reviewed_cards.size() < required_cards() or confidence_choice == "" or corroboration_choice == "" or authenticity_choice == "" or release_choice.size() == 0 or not action_plan_valid():
		show_final_review()
		return
	decision_digest = compute_decision_digest()
	if decision_digest != confirmed_decision_digest:
		human_confirmation = false
		confirmed_decision_digest = ""
		decision_digest = ""
		append_audit_event("human_confirmation_digest_mismatch", {"reason": "decision changed during finalization"})
		show_final_review()
		return
	pressure_events.append("Final simulated governance package submitted without altering the confirmed decision input.")
	evaluate_evidence_marks()
	apply_final_confidence_effects()
	apply_final_release_effects()
	apply_final_action_effects()
	score_breakdown = build_score_breakdown()
	append_audit_event("decision_finalized", {"decision_digest": decision_digest, "score": performance_score()})
	decision_finalized = true
	show_consequence()

func raw_performance_score() -> int:
	if score_breakdown.size() == 0:
		score_breakdown = build_score_breakdown()
	var total := 0
	for component in score_breakdown.values():
		total += int(component.get("points", 0))
	return clamp(total, 0, 100)

func performance_score() -> int:
	var raw_score := raw_performance_score()
	if raw_score >= 75 and not credible_gate_passes():
		return 74
	if raw_score >= 90 and not excellent_gate_passes():
		return 89
	return raw_score

func credible_gate_passes() -> bool:
	return evidence_marking_score() >= int(scoring_rubric.get("credible_gate", {}).get("minimum_evidence_marking", 10))

func excellent_gate_passes() -> bool:
	var gate: Dictionary = scoring_rubric.get("excellent_gate", {})
	if evidence_marking_score() < int(gate.get("minimum_evidence_marking", 18)):
		return false
	if actions_score() < int(gate.get("minimum_action_score", 0)):
		return false
	if not scenario.get("correct_confidence_range", []).has(confidence_choice):
		return false
	if not scenario.get("correct_corroboration_range", []).has(corroboration_choice):
		return false
	if not scenario.get("correct_authenticity_range", []).has(authenticity_choice):
		return false
	if release_score() != 15 or not action_plan_valid():
		return false
	for safeguard in scenario.get("critical_safeguards", []):
		if not actions.get(safeguard, false):
			return false
	return true
func performance_label() -> String:
	var score := performance_score()
	if score >= 90 and excellent_gate_passes():
		return "Strong doctrine alignment"
	if score >= 75:
		return "Bounded crisis handling"
	if score >= 60:
		return "Mixed doctrine alignment"
	return "High governance risk"

func show_consequence() -> void:
	clear_ui("consequence")
	add_title("Consequence Screen")
	final_performance = performance_label()
	var score := performance_score()
	add_text("Overall performance: %s (%s / 100)" % [final_performance, score])
	if score >= 90:
		add_text("The complete scoring model classifies this as strong doctrine alignment. Review the diagnostic meters and AAR for remaining limitations.")
	elif score >= 75:
		add_text("The complete scoring model classifies this as bounded crisis handling with material improvement opportunities.")
	elif score >= 60:
		add_text("The complete scoring model classifies this as mixed doctrine alignment. Several governance controls were incomplete or misapplied.")
	else:
		add_text("The complete scoring model identifies high governance risk. Do not treat the decision as a responsible outcome.")
	var risks := unresolved_risks()
	if risks.size() > 0:
		add_subtitle("Critical Review Flags")
		for risk in risks:
			add_text("• " + str(risk))
	add_dashboard()
	add_button("Score Summary", Callable(self, "show_score_summary"), "Open score components", true)
	add_button("Open After-Action Review", Callable(self, "show_aar"))
	if facilitator_mode:
		add_button("Facilitator / Observer View", Callable(self, "show_facilitator_observer"))
	add_button("Restart Scenario", Callable(self, "restart"))

func show_score_summary() -> void:
	clear_ui("score_summary")
	add_title("Score Summary")
	add_text("Scenario: " + scenario.get("title", ""))
	add_text("Confidence: " + confidence_choice)
	add_text("Corroboration: " + corroboration_choice)
	add_text("Authenticity: " + authenticity_choice)
	add_text("Public release decision: " + release_choice.get("label", "None"))
	add_text(action_budget_text())
	add_text("Overall performance: %s (%s / 100)" % [performance_label(), performance_score()])
	if raw_performance_score() != performance_score():
		add_text("Evidence-quality ceiling applied: the raw component total was %s, but an Excellent outcome requires the complete evidence and governance gate." % raw_performance_score())
	add_subtitle("Doctrine Score Breakdown")
	for component_name in score_breakdown.keys():
		var component: Dictionary = score_breakdown[component_name]
		add_text("%s: %s / %s" % [component_name.capitalize().replace("_", " "), component.get("points", 0), component.get("maximum", 0)])
	add_text("Decision fingerprint (technical digest): " + decision_digest)
	add_button("Open After-Action Review", Callable(self, "show_aar"), "Open detailed feedback", true)
	add_button("Export AAR Report", Callable(self, "export_aar_report"))
	if export_status != "": add_text(export_status)

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
	var recommended: Array = []
	if reviewed_cards.size() >= required_cards():
		got_right.append("Every evidence card was reviewed before judgment.")
	if scenario.get("correct_confidence_range", []).has(confidence_choice):
		got_right.append("Confidence magnitude was defensible: " + confidence_choice + ".")
	elif scenario.get("unsafe_choices", []).has(confidence_choice):
		overclaimed.append("Confidence magnitude exceeded the evidence: " + confidence_choice + ".")
		recommended.append("Use one of: " + ", ".join(scenario.get("correct_confidence_range", [])) + ".")
	if scenario.get("correct_corroboration_range", []).has(corroboration_choice):
		got_right.append("Corroboration was assessed separately and defensibly: " + corroboration_choice + ".")
	else:
		missed.append("Corroboration assessment was outside the strongest defensible range.")
	if scenario.get("correct_authenticity_range", []).has(authenticity_choice):
		got_right.append("Authenticity was assessed separately and defensibly: " + authenticity_choice + ".")
	else:
		missed.append("Authenticity assessment was outside the strongest defensible range.")
	if release_choice.get("id", "") == "overclaim":
		overclaimed.append("Release language made unsupported attribution.")
		recommended.append("Use controlled language matched to uncertainty.")
	elif release_score() == 15:
		got_right.append("Release language was proportionate and doctrine-aligned.")
	else:
		missed.append("Release posture preserved some truth but did not reach the strongest doctrine-aligned path.")
	if actions.get("protect_civilians", false):
		got_right.append("Civilian protection was included.")
	else:
		missed.append("Civilian protection was not selected.")
	if action_plan_valid():
		got_right.append("The action plan remained within explicit time and authority budgets.")
	else:
		missed.append("The action plan exceeded available resources.")
	if confidence_history.size() > 1 or corroboration_history.size() > 1 or authenticity_history.size() > 1 or release_history.size() > 1:
		got_right.append("The decision was revised before finalization. Corrective reasoning was preserved without a scoring penalty.")
	var sections: Array = []
	sections.append(bullet_section("What You Got Right", got_right))
	sections.append(bullet_section("What You Overclaimed", overclaimed))
	sections.append(bullet_section("What You Missed", missed))
	sections.append("Evidence Marking Review\n" + evidence_marking_feedback())
	sections.append(bullet_section("Recommended Better Decision", recommended))
	if facilitator_mode:
		sections.append(bullet_section("Facilitator Notes", scenario.get("facilitator_notes", [])))
	return "\n\n".join(sections)

func show_aar() -> void:
	clear_ui("aar")
	add_title("After-Action Review")
	add_text("Confidence: " + confidence_choice)
	add_text("Corroboration: " + corroboration_choice)
	add_text("Authenticity: " + authenticity_choice)
	add_text("Release choice: " + release_choice.get("label", "None"))
	add_text("Human final confirmation: " + ("Recorded" if human_confirmation else "Not recorded"))
	add_text("Decision fingerprint (technical digest): " + decision_digest)
	add_text(action_budget_text())
	add_subtitle("Decision-Specific Feedback")
	add_rich_text(aar_feedback())
	add_subtitle("Audit Boundary")
	add_text(governance_policy.get("audit_limit", "The audit chain is unsigned and unanchored."))
	add_subtitle("Core Lessons")
	for objective in scenario.get("learning_objectives", []): add_text("• " + objective)
	add_button("Export AAR Report", Callable(self, "export_aar_report"), "Write a JSON after-action record", true)
	if export_status != "": add_text(export_status)
	if export_directory_abs != "": add_button("Open Export Folder", Callable(self, "open_export_folder"))
	if facilitator_mode:
		add_button("Facilitator / Observer View", Callable(self, "show_facilitator_observer"))
	add_button("Restart Scenario", Callable(self, "restart"))

func aar_payload_valid(payload: Dictionary) -> bool:
	var required := ["game_version", "scenario_id", "session_mode", "score_breakdown", "decision_record", "decision_digest", "audit_chain", "audit_chain_valid", "human_final_confirmation", "confirmed_decision_digest", "corroboration_choice", "authenticity_choice", "action_budget", "action_costs", "audit_limit"]
	for key in required:
		if not payload.has(key):
			return false
	if not payload.get("audit_chain_valid", false) or not payload.get("human_final_confirmation", false):
		return false
	var final_digest := str(payload.get("decision_digest", ""))
	var confirmed_digest := str(payload.get("confirmed_decision_digest", ""))
	return final_digest != "" and final_digest == confirmed_digest and final_digest == compute_decision_digest()

func export_aar_report() -> void:
	if not verify_audit_chain():
		export_status = "Export failed: the audit chain is invalid or empty."
		push_error("AAR export refused because the audit chain is invalid or empty.")
		show_aar()
		return
	if decision_digest == "" or decision_digest != compute_decision_digest():
		export_status = "Export failed: the decision digest does not match the final decision record."
		push_error("AAR export refused because the final decision digest does not match the decision record.")
		show_aar()
		return
	var dir_abs := ProjectSettings.globalize_path("user://aar_reports")
	var dir_error := DirAccess.make_dir_recursive_absolute(dir_abs)
	if dir_error != OK and dir_error != ERR_ALREADY_EXISTS:
		export_status = "Export failed: the AAR directory could not be created at " + dir_abs
		show_aar()
		return
	var unix := Time.get_unix_time_from_system()
	var file_name := "aar_%s_%s.json" % [scenario.get("scenario_id", "scenario"), unix]
	var report_path := "user://aar_reports/" + file_name
	var payload := {
		"game_version": "0.3.0-rc2",
		"policy_id": governance_policy.get("policy_id", ""),
		"policy_version": governance_policy.get("policy_version", ""),
		"scenario_id": scenario.get("scenario_id", ""),
		"scenario_title": scenario.get("title", ""),
		"session_mode": session_mode,
		"evidence_reviewed": reviewed_cards,
		"card_marks": card_marks,
		"evidence_marking_metrics": evidence_marking_metrics(),
		"confidence_choice": confidence_choice,
		"confidence_history": confidence_history,
		"corroboration_choice": corroboration_choice,
		"corroboration_history": corroboration_history,
		"authenticity_choice": authenticity_choice,
		"authenticity_history": authenticity_history,
		"release_choice": release_choice,
		"release_history": release_history,
		"actions": actions,
		"action_budget": scenario.get("action_budget", {}),
		"action_costs": selected_action_costs(),
		"human_final_confirmation": human_confirmation,
		"confirmed_decision_digest": confirmed_decision_digest,
		"meters_final": meters,
		"meters_starting": starting_meters,
		"remaining_minutes": remaining_minutes,
		"performance_score": performance_score(),
		"raw_component_total": raw_performance_score(),
		"performance_label": performance_label(),
		"score_breakdown": score_breakdown,
		"decision_record": decision_record(),
		"decision_digest": decision_digest,
		"audit_chain": audit_events,
		"audit_chain_valid": true,
		"audit_limit": governance_policy.get("audit_limit", ""),
		"pressure_events": pressure_events,
		"evidence_marking_notes": evidence_marking_notes,
		"aar_feedback": aar_feedback(),
		"debrief_prompts": scenario.get("debrief_prompts", [])
	}
	if not aar_payload_valid(payload):
		export_status = "Export failed: the AAR payload did not satisfy the runtime-required field contract."
		show_aar()
		return
	var file := FileAccess.open(report_path, FileAccess.WRITE)
	if file == null:
		export_status = "Export failed: the report file could not be opened at " + ProjectSettings.globalize_path(report_path)
		show_aar()
		return
	file.store_string(JSON.stringify(payload, "\t"))
	file.close()
	last_aar_path = ProjectSettings.globalize_path(report_path)
	export_directory_abs = dir_abs
	export_status = "Export succeeded: " + last_aar_path
	show_aar()

func open_export_folder() -> void:
	if export_directory_abs == "":
		export_status = "No export folder is available yet."
		show_aar()
		return
	var result := OS.shell_open(export_directory_abs)
	if result != OK:
		export_status = "Could not open the export folder automatically. Path: " + export_directory_abs
		show_aar()

func show_facilitator_observer() -> void:
	if not facilitator_mode:
		show_aar()
		return
	clear_ui("facilitator_observer")
	add_facilitator_banner()
	add_title("Facilitator / Observer Mode")
	add_text("Scenario: " + scenario.get("title", ""))
	add_text("Player confidence: " + confidence_choice)
	add_text("Player corroboration: " + corroboration_choice)
	add_text("Player authenticity: " + authenticity_choice)
	add_text("Defensible confidence range: " + ", ".join(scenario.get("correct_confidence_range", [])))
	add_text("Defensible corroboration range: " + ", ".join(scenario.get("correct_corroboration_range", [])))
	add_text("Defensible authenticity range: " + ", ".join(scenario.get("correct_authenticity_range", [])))
	add_text("Evidence reviewed: " + ", ".join(reviewed_cards))
	add_text(action_budget_text())
	add_subtitle("Score Summary")
	add_dashboard()
	add_subtitle("Teaching Notes")
	for note in scenario.get("facilitator_notes", []): add_text("• " + note)
	add_subtitle("Audit Boundary")
	add_text(governance_policy.get("audit_limit", ""))
	add_subtitle("Debrief Prompts")
	for prompt in scenario.get("debrief_prompts", []): add_text("• " + prompt)
	add_button("Back to AAR", Callable(self, "show_aar"), "Return to after-action review", true)
	add_button("Restart Scenario", Callable(self, "restart"))

func canonical_json(value) -> String:
	match typeof(value):
		TYPE_DICTIONARY:
			var keys: Array = value.keys()
			keys.sort()
			var parts: Array = []
			for key in keys:
				parts.append(JSON.stringify(str(key)) + ":" + canonical_json(value[key]))
			return "{" + ",".join(parts) + "}"
		TYPE_ARRAY:
			var items: Array = []
			for item in value:
				items.append(canonical_json(item))
			return "[" + ",".join(items) + "]"
		TYPE_STRING:
			return JSON.stringify(value)
		TYPE_BOOL:
			return "true" if value else "false"
		TYPE_NIL:
			return "null"
		_:
			return str(value)

func sha256_text(text: String) -> String:
	var context := HashingContext.new()
	context.start(HashingContext.HASH_SHA256)
	context.update(text.to_utf8_buffer())
	return context.finish().hex_encode()

func append_audit_event(event_type: String, data: Dictionary) -> void:
	var previous_hash := "GENESIS" if audit_events.size() == 0 else str(audit_events[audit_events.size() - 1].get("event_hash", ""))
	var event := {
		"sequence": audit_events.size() + 1,
		"timestamp_unix": Time.get_unix_time_from_system(),
		"event_type": event_type,
		"data": data,
		"previous_hash": previous_hash
	}
	event["event_hash"] = sha256_text(canonical_json(event))
	audit_events.append(event)

func verify_audit_chain() -> bool:
	if governance_policy.get("require_in_memory_audit_chain", true) and audit_events.size() == 0:
		return false
	var previous_hash := "GENESIS"
	var expected_sequence := 1
	for stored_event in audit_events:
		if int(stored_event.get("sequence", 0)) != expected_sequence:
			return false
		if str(stored_event.get("previous_hash", "")) != previous_hash:
			return false
		var event_copy: Dictionary = stored_event.duplicate(true)
		var stored_hash := str(event_copy.get("event_hash", ""))
		event_copy.erase("event_hash")
		if sha256_text(canonical_json(event_copy)) != stored_hash:
			return false
		previous_hash = stored_hash
		expected_sequence += 1
	return true

func decision_input_record() -> Dictionary:
	return {
		"policy_id": governance_policy.get("policy_id", ""),
		"policy_version": governance_policy.get("policy_version", ""),
		"scenario_id": scenario.get("scenario_id", ""),
		"session_mode": session_mode,
		"reviewed_cards": reviewed_cards,
		"card_marks": card_marks,
		"confidence_choice": confidence_choice,
		"confidence_history": confidence_history,
		"corroboration_choice": corroboration_choice,
		"corroboration_history": corroboration_history,
		"authenticity_choice": authenticity_choice,
		"authenticity_history": authenticity_history,
		"release_id": release_choice.get("id", ""),
		"release_history": release_history,
		"actions": actions,
		"action_budget": scenario.get("action_budget", {}),
		"action_costs": selected_action_costs(),
		"remaining_minutes": remaining_minutes
	}

func decision_record() -> Dictionary:
	var record := decision_input_record()
	record["human_final_confirmation"] = human_confirmation
	record["confirmed_decision_digest"] = confirmed_decision_digest
	record["score_breakdown"] = score_breakdown
	return record

func compute_decision_digest() -> String:
	return sha256_text(canonical_json(decision_input_record()))

func restart() -> void:
	if current_scenario_id != "": reset_for_scenario(current_scenario_id)
	show_main_menu()
