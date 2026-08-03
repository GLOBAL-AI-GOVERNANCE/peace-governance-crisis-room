from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / "game" / "scripts" / "Main.gd").read_text(encoding="utf-8")
required_fragments = [
    'load_governance_policy()',
    'require_complete_evidence_review',
    'require_human_final_confirmation',
    'require_action_budget',
    'require_final_review_screen',
    'func evidence_marking_metrics()',
    'chance_corrected_skill',
    'func show_corroboration()',
    'func show_authenticity()',
    'func show_final_review()',
    'func action_plan_valid()',
    'func build_score_breakdown()',
    'func raw_performance_score()',
    'if raw_score >= 75 and not credible_gate_passes():',
    'func append_audit_event(',
    '"timestamp_unix": Time.get_unix_time_from_system()',
    'func verify_audit_chain()',
    'func compute_decision_digest()',
    'func invalidate_human_confirmation(',
    'confirmed_decision_digest',
    'human_confirmation_invalidated',
    'func set_session_mode(',
    'Assessment Mode  -  cues withheld until finalization',
    'Facilitator Mode  -  instructor/observer view',
    'func credible_gate_passes()',
    'Assessment mode: coaching and safer-answer feedback are withheld until finalization.',
    'final_digest == confirmed_digest',
    'button.focus_mode = Control.FOCUS_ALL',
    'button.call_deferred("grab_focus")',
    'func add_checkbox(',
    'CheckBox.new()',
    'Governance policy disables a mandatory safeguard',
    'AAR export refused because the audit chain is invalid or empty',
    '"decision_record": decision_record()',
    '"audit_limit": governance_policy.get("audit_limit", "")',
    'ProjectSettings.globalize_path(report_path)',
    'OS.shell_open(export_directory_abs)',
]
missing = [fragment for fragment in required_fragments if fragment not in text]
if missing:
    raise SystemExit(f"Main.gd is missing required contract fragments: {missing}")

# Automatic focus is prohibited. Focus must be explicitly requested by the screen.
add_button_start = text.index('func add_button(')
add_button_end = text.index('\nfunc ', add_button_start + 1)
add_button_block = text[add_button_start:add_button_end]
if 'if first_focus_control == null' in add_button_block:
    raise SystemExit('add_button still auto-focuses the first control')
if 'if safe_focus:' not in add_button_block:
    raise SystemExit('add_button lacks explicit safe-focus control')

# Learner mode must not show hidden facilitator indicators without a mode gate.
show_evidence_start = text.index('func show_evidence(')
show_evidence_end = text.index('\nfunc ', show_evidence_start + 1)
evidence_block = text[show_evidence_start:show_evidence_end]
if 'facilitator_indicators' in evidence_block and 'if facilitator_mode' not in evidence_block:
    raise SystemExit('Evidence screen exposes facilitator indicators to learners')

# Confidence, corroboration, authenticity, and release selections must not directly apply meter effects.
def block(name: str, next_name: str) -> str:
    start = text.index(f"func {name}")
    end = text.index(f"func {next_name}", start)
    return text[start:end]

for name, next_name in (
    ("choose_confidence", "show_corroboration"),
    ("choose_corroboration", "show_authenticity"),
    ("choose_authenticity", "controlled_language_key"),
    ("choose_release", "action_summary"),
):
    section = block(name, next_name)
    if 'change_meter(' in section:
        raise SystemExit(f"{name} applies cumulative meter effects before finalization")

# Final actions must be reversible and must route through final review.
actions_block = block('show_actions', 'toggle_action')
for fragment in ('Back to Public Release Decision', 'Review Complete Decision Package'):
    if fragment not in actions_block:
        raise SystemExit(f'show_actions missing {fragment!r}')
if 'Submit Final Simulated Decision' in actions_block:
    raise SystemExit('show_actions bypasses the final review screen')

# Consequence headline must be score-driven, not independently meter-classified.
consequence_block = block('show_consequence', 'show_score_summary')
if 'var score := performance_score()' not in consequence_block:
    raise SystemExit('Consequence screen is not driven by the unified score')
if 'meters.get("truth_integrity"' in consequence_block:
    raise SystemExit('Consequence screen still has a separate meter headline model')

# Responsive width and scroll preservation.
if 'root_box.custom_minimum_size = Vector2(900, 0)' in text:
    raise SystemExit('Fixed 900-pixel content width remains')
for fragment in ('scroll_positions[current_screen_id]', 'scroll.set_deferred("scroll_vertical"'):
    if fragment not in text:
        raise SystemExit('Scroll preservation contract missing')

# Very small structural sanity checks. These are not a Godot parser.
func_lines=[line for line in text.splitlines() if line.startswith('func ')]
func_names=[line.split('(')[0] for line in func_lines]
if len(func_names) != len(set(func_names)):
    dup=sorted({n for n in func_names if func_names.count(n)>1})
    raise SystemExit(f"Duplicate GDScript function names found: {dup}")
for left, right in (("(", ")"), ("[", "]"), ("{", "}")):
    if text.count(left) != text.count(right):
        raise SystemExit(f"Unbalanced {left}{right} characters in Main.gd")

# Every block opener must be followed by a more-indented nonblank line.
lines=text.splitlines()
for index,line in enumerate(lines):
    stripped=line.strip()
    if not stripped or stripped.startswith('#') or not stripped.endswith(':'):
        continue
    indent=len(line)-len(line.lstrip('\t'))
    next_line=None
    for candidate in lines[index+1:]:
        if candidate.strip() and not candidate.strip().startswith('#'):
            next_line=candidate
            break
    if next_line is None:
        raise SystemExit(f"GDScript block at line {index+1} has no body")
    next_indent=len(next_line)-len(next_line.lstrip('\t'))
    if next_indent <= indent:
        raise SystemExit(f"GDScript block at line {index+1} appears empty")

# Learner and assessment action labels must not expose answer-revealing doctrine points.
actions_block = block('show_actions', 'toggle_action')
if 'doctrine score' in actions_block and 'if facilitator_mode' not in actions_block:
    raise SystemExit('show_actions exposes doctrine score without facilitator gate')
if 'doctrine %s' in actions_block or 'action_scores' in actions_block.split('if facilitator_mode:')[0]:
    raise SystemExit('show_actions exposes action_scores before facilitator gate')
summary_block = block('action_summary', 'selected_action_costs')
if 'doctrine score' in summary_block and 'reveal_scores' not in summary_block:
    raise SystemExit('action_summary exposes doctrine score without explicit reveal flag')

# Final human confirmation must be bound to a digest and invalidated after material changes.
if 'confirmed_decision_digest = compute_decision_digest() if value else ""' not in text:
    raise SystemExit('human confirmation is not bound to the current decision digest')
if 'confirmed_decision_digest != compute_decision_digest()' not in text:
    raise SystemExit('finalization does not enforce confirmed digest equality')
for fragment in (
    'invalidate_human_confirmation("evidence reviewed")',
    'invalidate_human_confirmation("evidence mark changed")',
    'invalidate_human_confirmation("confidence changed")',
    'invalidate_human_confirmation("corroboration changed")',
    'invalidate_human_confirmation("authenticity changed")',
    'invalidate_human_confirmation("release posture changed")',
    'invalidate_human_confirmation("governance action changed")',
    'invalidate_human_confirmation("decision clock advanced")',
):
    if fragment not in text:
        raise SystemExit(f'material revision invalidation missing: {fragment}')



# Assessment evidence view must withhold authored metadata labels.
card_block = block('show_card_detail', 'toggle_card_mark')
if 'if session_mode == "assessment":' not in card_block:
    raise SystemExit('Assessment evidence metadata gate is missing')
if 'authored metadata labels are withheld' not in card_block:
    raise SystemExit('Assessment evidence metadata boundary text is missing')

# Assessment mode must not receive predecision coaching.
release_block = block('show_release_language', 'choose_release')
if 'if session_mode == "assessment":' not in release_block:
    raise SystemExit('Assessment-mode coaching gate is missing')
assessment_pos = release_block.index('if session_mode == "assessment":')
practice_feedback_pos = release_block.index('add_text(safer_language_recommendation())')
if practice_feedback_pos < assessment_pos:
    raise SystemExit('Safer-answer coaching appears before the assessment-mode gate')

# No decision-input mutation may occur after confirmed-digest equality and before
# the final decision digest is fixed.
finalize_block = block('finalize_decision', 'raw_performance_score')
digest_check_pos = finalize_block.index('confirmed_decision_digest != compute_decision_digest()')
digest_set_pos = finalize_block.index('decision_digest = compute_decision_digest()')
if 'apply_pressure_tick(' in finalize_block[digest_check_pos:digest_set_pos]:
    raise SystemExit('Finalization mutates decision input after confirmation')
if 'decision_digest != confirmed_decision_digest' not in finalize_block:
    raise SystemExit('Finalization does not enforce final digest equality')

# AAR export must require current, final, and confirmed digests to agree.
aar_block = block('aar_payload_valid', 'export_aar_report')
for fragment in ('final_digest == confirmed_digest', 'final_digest == compute_decision_digest()'):
    if fragment not in aar_block:
        raise SystemExit(f'AAR digest-equality contract missing: {fragment}')

print("GDScript governance and UX contract validation passed (static only).")

text=(ROOT/'game/scripts/Main.gd').read_text(encoding='utf-8')
for fragment in ['Evidence Integrity','Escalation Control','Civilian Protection','Scenario state  -  Public Pressure']:
    if fragment not in text: raise SystemExit('Missing normalized public indicator: '+fragment)
print('Normalized public-indicator contract passed.')
