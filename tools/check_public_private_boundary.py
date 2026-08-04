#!/usr/bin/env python3
"""Fail closed if private, generated, or internal workpaper material enters public source."""
from pathlib import Path
from generate_manifest import ROOT, controlled_files

required = [
    ROOT / 'PUBLIC_RELEASE_GATE.md',
    ROOT / 'VERIFICATION.md',
    ROOT / 'docs/source-boundary.md',
]
for path in required:
    if not path.is_file():
        raise SystemExit(f'Missing required public boundary record: {path.relative_to(ROOT)}')

forbidden_suffixes = {'.zip', '.7z', '.rar', '.ots', '.exe', '.pck', '.dll'}
forbidden_prefixes = {
    'docs/archive/',
    'docs/portfolio/',
    'docs/program-lineage/',
    'docs/release-evidence/',
    'docs/maintainers/release/',
}
forbidden_exact = {
    'SBOM.spdx.json',
    'docs/audit/internal-candidate-corrective-history.md',
    'docs/audit/v0.3.0-rc2-final-publication-hardening.md',
    'docs/audit/v0.3.0-rc2-integrated-vv.md',
    'docs/validation/local-chromium-uat-v0.3.0-rc2.json',
    'docs/validation/local-chromium-uat-v0.3.0-rc2.md',
}
forbidden_markers = {
    'truth_architecture_dossier_9-11',
    'RAW_CLAIM_EXTRACT_PRIVATE',
    'COMPLETE_PRIVATE_REVIEW_2026-07-30',
    'awakening_wave_campaign_plan_v1.0_COMPLETE_PRIVATE_REVIEW',
}
violations = []
for rel in controlled_files():
    rel_text = rel.as_posix()
    path = ROOT / rel
    if rel_text == 'tools/check_public_private_boundary.py':
        continue
    if rel_text in forbidden_exact or any(rel_text.startswith(prefix) for prefix in forbidden_prefixes):
        violations.append(f'non-public path: {rel_text}')
        continue
    if any(part == 'dist' or part.startswith('dist-') for part in rel.parts):
        violations.append(f'generated path: {rel_text}')
        continue
    if path.suffix.lower() in forbidden_suffixes:
        violations.append(f'forbidden artifact: {rel_text}')
        continue
    if path.suffix.lower() in {'.md', '.txt', '.csv', '.json', '.py', '.gd', '.sh', '.yml', '.yaml', '.cfg', '.cff'}:
        text = path.read_text(encoding='utf-8', errors='ignore')
        for marker in forbidden_markers:
            if marker in text:
                violations.append(f'private/public marker {marker!r} in {rel_text}')
if violations:
    raise SystemExit('Public source boundary failed: ' + '; '.join(violations))
print('Public source boundary passed.')
