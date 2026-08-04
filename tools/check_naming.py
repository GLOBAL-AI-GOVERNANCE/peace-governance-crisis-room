#!/usr/bin/env python3
from generate_manifest import ROOT, controlled_files

CANONICAL = 'Peace OS: Crisis Room'
SLUG = 'peace-os-crisis-room'
REPOSITORY = 'GLOBAL-AI-GOVERNANCE/peace-os-crisis-room'
VERSION = '0.3.0-rc2'
DISCLAIMER = 'Peace OS is the product name. This project is not a computer operating system.'

for rel in ('README.md', 'game/project.godot', 'RELEASE_NOTES.md', 'web/index.html'):
    if CANONICAL not in (ROOT / rel).read_text(encoding='utf-8'):
        raise SystemExit(f'{rel} missing canonical product name')

if DISCLAIMER not in (ROOT / 'README.md').read_text(encoding='utf-8'):
    raise SystemExit('README missing the non-operating-system clarification')
if REPOSITORY not in (ROOT / 'scripts/publish_to_github.sh').read_text(encoding='utf-8'):
    raise SystemExit('Publication script does not target the canonical repository')
if (ROOT / 'VERSION').read_text(encoding='utf-8').strip() != VERSION:
    raise SystemExit('Unexpected VERSION')

historical_name_allowlist = {
    'CHANGELOG.md',
    'RELEASE_NOTES.md',
    'docs/architecture/ADR-001-canonical-identity.md',
    'docs/audit/v0.2.1-public-scoring-audit-summary.md',
    'tests/test_program_lineage_contract.py',
}

text_suffixes = {'.md', '.txt', '.py', '.gd', '.json', '.cfg', '.godot', '.yml', '.yaml', '.sh', '.cff', '.html', '.js', '.css', '.example'}

for rel in controlled_files():
    path = ROOT / rel
    if rel.as_posix() == 'tools/check_naming.py':
        continue
    rel_text = rel.as_posix()
    if rel.suffix.lower() not in text_suffixes and rel.name not in {'VERSION', 'LICENSE'}:
        continue
    text = path.read_text(encoding='utf-8', errors='ignore')
    if 'peace-governance-crisis-room' in text:
        raise SystemExit(f'Retired repository slug in {rel_text}')
    if 'Peace_Governance_Crisis_Room' in text:
        raise SystemExit(f'Retired filename-form identity in {rel_text}')
    if 'Peace Governance Crisis Room' in text and rel_text not in historical_name_allowlist:
        raise SystemExit(f'Historical product name outside the allowed record in {rel_text}')
    for stale in ('0.3.0-rc3', '0.3.0-rc4', '0.3.0-rc5'):
        if stale in text and not rel_text.startswith('docs/audit/'):
            raise SystemExit(f'Internal candidate version leaked into {rel_text}')

print('Canonical Peace OS identity, repository, clarification, and version checks passed.')
