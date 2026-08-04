#!/usr/bin/env python3
"""Validate immutable GitHub Actions and RC2 exact-deployment controls."""
import re
from pathlib import Path
from generate_manifest import ROOT

workflows = sorted((ROOT / '.github/workflows').glob('*.y*ml'))
if not workflows:
    raise SystemExit('No GitHub Actions workflow found')

for path in workflows:
    text = path.read_text(encoding='utf-8')
    for use in re.findall(r'uses:\s*([^\s#]+)', text):
        if '@' not in use:
            raise SystemExit(f'{path.name}: unpinned action {use}')
        ref = use.rsplit('@', 1)[1]
        if not re.fullmatch(r'[0-9a-f]{40}', ref):
            raise SystemExit(f'{path.name}: action not pinned to full SHA: {use}')

pages = ROOT / '.github/workflows/pages.yml'
if not pages.exists():
    raise SystemExit('pages.yml is required')
text = pages.read_text(encoding='utf-8')
required = {
    'exact commit checkout': 'ref: ${{ github.sha }}',
    'deployment metadata writer': 'tools/write_deployment_metadata.py',
    'deployment metadata output': 'web/deployment.json',
    'deploy page URL output': 'page_url: ${{ steps.deployment.outputs.page_url }}',
    'post-deploy UAT job': 'deployed-browser-uat:',
    'deployment dependency': 'needs: deploy',
    'exact expected commit': 'EXPECTED_COMMIT: ${{ github.sha }}',
    'deployed UAT runner': 'tests/deployed_browser_uat.mjs',
    'deployed UAT verifier': 'tools/verify_deployed_uat.py',
    'deployed evidence upload': 'Publish exact deployed UAT evidence',
    'evidence checksum ledger': 'deployed-uat-SHA256SUMS.txt',
}
for label, marker in required.items():
    if marker not in text:
        raise SystemExit(f'pages.yml: missing RC2 deployment control: {label}')

positions = {
    'deploy': text.find('\n  deploy:'),
    'uat': text.find('\n  deployed-browser-uat:'),
}
if positions['deploy'] < 0 or positions['uat'] <= positions['deploy']:
    raise SystemExit('pages.yml: deployed-browser UAT must follow the deploy job')

print(f'Workflow pinning and exact-deployment controls passed for {len(workflows)} workflow(s).')
