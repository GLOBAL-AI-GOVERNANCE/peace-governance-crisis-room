import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "game" / "data" / "governance" / "policy.json"
policy = json.loads(path.read_text(encoding="utf-8"))

required_bool = {
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
}
for key in required_bool:
    if type(policy.get(key)) is not bool:
        raise SystemExit(f"Policy field {key} must be a strict JSON Boolean")
if policy["simulation_only"] is not True:
    raise SystemExit("Policy must remain simulation-only")
for key in ("allow_live_data", "allow_autonomous_release", "allow_external_action_execution", "allow_telemetry", "allow_external_ai"):
    if policy[key] is not False:
        raise SystemExit(f"Policy must keep {key}=false")
for key in ("require_human_final_confirmation","require_complete_evidence_review","require_in_memory_audit_chain","require_action_budget","require_final_review_screen"):
    if policy[key] is not True:
        raise SystemExit(f"Policy must keep {key}=true")
if policy.get("audit_hash_algorithm") != "sha256":
    raise SystemExit("Only sha256 audit hashing is supported")
components = policy.get("required_score_components")
if not isinstance(components, dict) or sum(components.values()) != 100 or len(components) != 8:
    raise SystemExit("Score components must be an eight-part object totaling 100")
if len(policy.get('allowed_confidence_levels',[])) != 4:
    raise SystemExit('Confidence must remain a separate four-level magnitude dimension')
if len(policy.get('allowed_corroboration_levels',[])) != 4:
    raise SystemExit('Corroboration dimension missing')
if len(policy.get('allowed_authenticity_levels',[])) != 4:
    raise SystemExit('Authenticity dimension missing')
if len(policy.get('audit_limit','')) < 80:
    raise SystemExit('Audit limitation must be explicit')
if policy.get('canonical_repository') != 'GLOBAL-AI-GOVERNANCE/peace-os-crisis-room':
    raise SystemExit('Canonical repository mismatch')
if policy.get('public_delivery') != 'semantic_web_first':
    raise SystemExit('Public delivery architecture mismatch')
print("Governance policy validation passed.")
