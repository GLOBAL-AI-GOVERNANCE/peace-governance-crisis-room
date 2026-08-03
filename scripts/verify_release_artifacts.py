#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('checksum_record', nargs='?', default='SHA256SUMS.txt')
    parser.add_argument('--expected-commit', help='Require exact provenance source_commit equality.')
    args=parser.parse_args()
    record=Path(args.checksum_record)
    base=record.parent
    failures=[]; count=0
    for line in record.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        expected,name=line.split(None,1); count += 1
        path=base/name.strip()
        if not path.is_file():
            failures.append(f'missing {name}')
            continue
        actual=sha(path)
        if actual != expected:
            failures.append(f'hash mismatch {name}')
    if args.expected_commit:
        if not re.fullmatch(r'[0-9a-fA-F]{40}', args.expected_commit):
            failures.append('expected commit is not a full 40-character SHA')
        provenance_files=sorted(base.glob('*-provenance.json'))
        if len(provenance_files) != 1:
            failures.append(f'expected exactly one provenance file, found {len(provenance_files)}')
        else:
            provenance=json.loads(provenance_files[0].read_text(encoding='utf-8'))
            if provenance.get('source_commit') != args.expected_commit:
                failures.append(
                    f"provenance source_commit {provenance.get('source_commit')!r} != {args.expected_commit!r}"
                )
    if failures:
        raise SystemExit('\n'.join(failures))
    print(f'PASS: verified {count} release artifacts.' + (f' Provenance equals {args.expected_commit}.' if args.expected_commit else ''))


if __name__ == '__main__':
    main()
