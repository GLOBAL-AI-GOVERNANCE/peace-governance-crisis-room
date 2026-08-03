#!/usr/bin/env python3
"""High-confidence offline secret-pattern scan for controlled source files."""
from __future__ import annotations
import re
from pathlib import Path
from generate_manifest import ROOT, controlled_files

PATTERNS = {
    'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'github_token': re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b'),
    'github_pat': re.compile(r'\bgithub_pat_[A-Za-z0-9_]{50,}\b'),
    'aws_access_key': re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
    'slack_token': re.compile(r'\bxox[baprs]-[A-Za-z0-9-]{10,}\b'),
}
TEXT_SUFFIXES = {'.md','.txt','.py','.gd','.json','.yml','.yaml','.cfg','.godot','.tscn','.svg','.sh','.toml'}
findings=[]
for rel in controlled_files():
    if rel.suffix.lower() not in TEXT_SUFFIXES and rel.name not in {'VERSION','LICENSE'}:
        continue
    text=(ROOT/rel).read_text(encoding='utf-8', errors='ignore')
    for name, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            line=text.count('\n',0,match.start())+1
            findings.append(f'{rel.as_posix()}:{line}:{name}')
if findings:
    raise SystemExit('Potential secrets found:\n'+'\n'.join(findings))
print('High-confidence secret scan passed.')
