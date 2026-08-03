#!/usr/bin/env python3
import re
from pathlib import Path
from generate_manifest import ROOT
workflows=sorted((ROOT/'.github/workflows').glob('*.y*ml'))
if not workflows:
    raise SystemExit('No GitHub Actions workflow found')
for path in workflows:
    text=path.read_text(encoding='utf-8')
    for use in re.findall(r'uses:\s*([^\s#]+)', text):
        if '@' not in use:
            raise SystemExit(f'{path.name}: unpinned action {use}')
        ref=use.rsplit('@',1)[1]
        if not re.fullmatch(r'[0-9a-f]{40}', ref):
            raise SystemExit(f'{path.name}: action not pinned to full SHA: {use}')
print(f'Workflow pinning passed for {len(workflows)} workflow(s).')
