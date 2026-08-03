#!/usr/bin/env python3
"""Validate the required, intentionally small CFF 1.2 metadata surface."""
from pathlib import Path
from generate_manifest import ROOT

path = ROOT / 'CITATION.cff'
text = path.read_text(encoding='utf-8')
required = {
    'cff-version: 1.2.0': 'CFF version',
    'title: "Peace OS: Crisis Room"': 'title',
    'message:': 'message',
    'authors:': 'authors',
    '- name: "Global AI Governance contributors"': 'organization author',
    'repository-code: "https://github.com/GLOBAL-AI-GOVERNANCE/peace-os-crisis-room"': 'repository',
}
missing = [label for fragment, label in required.items() if fragment not in text]
if missing:
    raise SystemExit('CITATION.cff missing: ' + ', '.join(missing))
if '\t' in text:
    raise SystemExit('CITATION.cff must not contain tabs.')
print('CITATION.cff required CFF 1.2 metadata passed.')
