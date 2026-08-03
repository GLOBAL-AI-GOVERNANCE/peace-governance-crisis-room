#!/usr/bin/env python3
"""Plan and apply a deterministic source overlay without requiring rsync."""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
from pathlib import Path

EXCLUDED_DIRS = {'.git', '__pycache__', '.pytest_cache', '.godot'}
EXCLUDED_SUFFIXES = {'.pyc', '.pyo'}


def excluded(relative: Path) -> bool:
    if any(part in EXCLUDED_DIRS or part == 'dist' or part.startswith('dist-') for part in relative.parts):
        return True
    if relative.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    if relative.name.startswith('publish-') and relative.suffix == '.log':
        return True
    return False


def files_under(root: Path) -> dict[Path, Path]:
    result: dict[Path, Path] = {}
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if excluded(relative):
            continue
        result[relative] = path
    return result


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def plan(source: Path, target: Path) -> tuple[list[str], list[Path]]:
    source_files = files_under(source)
    target_files = files_under(target)
    rows: list[str] = []
    for relative, source_path in source_files.items():
        target_path = target_files.get(relative)
        if target_path is None:
            rows.append(f'ADD\t{relative.as_posix()}')
        elif digest(source_path) != digest(target_path):
            rows.append(f'MODIFY\t{relative.as_posix()}')
        else:
            rows.append(f'SAME\t{relative.as_posix()}')
    deletions = sorted(set(target_files) - set(source_files))
    rows.extend(f'DELETE\t{relative.as_posix()}' for relative in deletions)
    return rows, deletions


def apply_overlay(source: Path, target: Path, deletions: list[Path]) -> None:
    source_files = files_under(source)
    for relative in deletions:
        path = target / relative
        if path.exists() or path.is_symlink():
            path.unlink()
    for relative, source_path in source_files.items():
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
    # Remove empty directories without entering .git.
    directories = sorted(
        (path for path in target.rglob('*') if path.is_dir() and '.git' not in path.parts),
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for directory in directories:
        try:
            directory.rmdir()
        except OSError:
            pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--target', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--deletions', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()

    source = args.source.resolve()
    target = args.target.resolve()
    if source == target:
        raise SystemExit('STOP: source and target must be different directories.')
    if not source.is_dir() or not target.is_dir():
        raise SystemExit('STOP: source and target must both be existing directories.')

    rows, deletions = plan(source, target)
    args.plan.parent.mkdir(parents=True, exist_ok=True)
    args.deletions.parent.mkdir(parents=True, exist_ok=True)
    args.plan.write_text('\n'.join(rows) + '\n', encoding='utf-8')
    args.deletions.write_text(
        ''.join(f'{relative.as_posix()}\n' for relative in deletions),
        encoding='utf-8',
    )
    if args.apply:
        apply_overlay(source, target, deletions)
        print(f'PASS: applied overlay with {len(deletions)} deletion(s).')
    else:
        print(f'PASS: planned overlay with {len(deletions)} deletion(s).')


if __name__ == '__main__':
    main()
