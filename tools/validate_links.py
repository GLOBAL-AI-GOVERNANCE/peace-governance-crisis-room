#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path
from generate_manifest import ROOT, controlled_files

link_re=re.compile(r'\[[^\]]*\]\(([^)]+)\)')
failures=[]
for rel in controlled_files():
    if rel.suffix.lower() != '.md':
        continue
    text=(ROOT/rel).read_text(encoding='utf-8')
    for target in link_re.findall(text):
        target=target.strip().split('#',1)[0]
        if not target or target.startswith(('http://','https://','mailto:')):
            continue
        if target.startswith('/'):
            resolved=ROOT/target.lstrip('/')
        else:
            resolved=(ROOT/rel).parent/target
        if not resolved.resolve().exists():
            failures.append(f'{rel.as_posix()} -> {target}')
if failures:
    raise SystemExit('Broken internal links:\n'+'\n'.join(failures))
print('Internal Markdown link validation passed.')
