#!/usr/bin/env python3
"""Generate or verify deterministic source inventories."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {'.git', 'dist', '__pycache__', '.pytest_cache', '.godot'}
EXCLUDED_FILES = {'MANIFEST.json', 'SHA256SUMS.txt', '.DS_Store'}
EXCLUDED_SUFFIXES = {'.pyc', '.pyo', '.exe', '.pck'}


def controlled_files():
    for path in sorted(ROOT.rglob('*'), key=lambda item: item.relative_to(ROOT).as_posix()):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in rel.parts) or (rel.parts and rel.parts[0].startswith('dist')):
            continue
        if rel.name in EXCLUDED_FILES or rel.suffix.lower() in EXCLUDED_SUFFIXES or (rel.name.startswith('publish-') and rel.suffix == '.log'):
            continue
        yield rel


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def build_records():
    return [
        {'path': rel.as_posix(), 'bytes': (ROOT / rel).stat().st_size, 'sha256': sha256(ROOT / rel)}
        for rel in controlled_files()
    ]


def render(records):
    manifest = {
        'schema_version': '1.0',
        'artifact': 'peace-os-crisis-room',
        'version': (ROOT / 'VERSION').read_text(encoding='utf-8').strip(),
        'hash_algorithm': 'sha256',
        'inventory_exclusions': sorted(EXCLUDED_FILES),
        'file_count': len(records),
        'files': records,
    }
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + '\n'
    sums_text = ''.join(f"{row['sha256']}  {row['path']}\n" for row in records)
    return manifest_text, sums_text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    records = build_records()
    manifest_text, sums_text = render(records)
    targets = {ROOT / 'MANIFEST.json': manifest_text, ROOT / 'SHA256SUMS.txt': sums_text}
    if args.check:
        failures = []
        for path, expected in targets.items():
            actual = path.read_text(encoding='utf-8') if path.exists() else ''
            if actual != expected:
                failures.append(path.name)
        if failures:
            raise SystemExit('Inventory mismatch: ' + ', '.join(failures) + '. Run tools/generate_manifest.py')
        print(f"Manifest parity passed for {len(records)} controlled files.")
        return
    for path, text in targets.items():
        path.write_text(text, encoding='utf-8', newline='\n')
    print(f"Wrote deterministic inventories for {len(records)} controlled files.")

if __name__ == '__main__':
    main()
