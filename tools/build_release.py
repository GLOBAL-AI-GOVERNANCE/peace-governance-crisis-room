#!/usr/bin/env python3
"""Build deterministic source release artifacts. Does not build Godot binaries."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True

from generate_manifest import ROOT, controlled_files


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_output(*args: str) -> str | None:
    try:
        return subprocess.check_output(
            ['git', *args],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def source_commit() -> str:
    return git_output('rev-parse', 'HEAD') or 'PRE_MERGE_OVERLAY_NOT_A_GIT_COMMIT'


def ensure_clean_git_tree() -> None:
    """Reject source changes not represented by HEAD; ignore generated dist folders."""
    if git_output('rev-parse', '--is-inside-work-tree') != 'true':
        return
    status = git_output('status', '--porcelain', '--untracked-files=all') or ''
    unexpected: list[str] = []
    for line in status.splitlines():
        path = line[3:].strip()
        if ' -> ' in path:
            path = path.split(' -> ', 1)[1]
        first = Path(path).parts[0] if Path(path).parts else path
        if first == 'dist' or first.startswith('dist-'):
            continue
        unexpected.append(line)
    if unexpected:
        raise SystemExit(
            'STOP: working tree is not clean; commit or remove these changes before building:\n'
            + '\n'.join(unexpected)
        )


def remove_python_cache() -> None:
    for cache_dir in ROOT.rglob('__pycache__'):
        if 'dist' not in cache_dir.parts:
            shutil.rmtree(cache_dir, ignore_errors=True)
    for pattern in ('*.pyc', '*.pyo'):
        for bytecode in ROOT.rglob(pattern):
            if 'dist' not in bytecode.parts:
                bytecode.unlink(missing_ok=True)


def validation_env() -> dict[str, str]:
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    return env


def parse_release_timestamp(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith('Z'):
        normalized = normalized[:-1] + '+00:00'
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise SystemExit(
            'STOP: release timestamp must be ISO 8601, for example 2026-08-03T04:45:00Z.'
        ) from exc
    if parsed.tzinfo is None:
        raise SystemExit('STOP: release timestamp must include a timezone offset or Z.')
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def resolve_release_timestamp(argument: str | None) -> datetime:
    if argument:
        return parse_release_timestamp(argument)
    source_date_epoch = os.environ.get('SOURCE_DATE_EPOCH')
    if source_date_epoch:
        try:
            return datetime.fromtimestamp(int(source_date_epoch), tz=timezone.utc).replace(microsecond=0)
        except ValueError as exc:
            raise SystemExit('STOP: SOURCE_DATE_EPOCH must be an integer Unix timestamp.') from exc
    commit_time = git_output('show', '-s', '--format=%cI', 'HEAD')
    if commit_time:
        return parse_release_timestamp(commit_time)
    raise SystemExit(
        'STOP: no Git commit timestamp is available. Supply --release-timestamp with an ISO 8601 value.'
    )


def zip_timestamp(release_time: datetime) -> tuple[int, int, int, int, int, int]:
    year = max(1980, release_time.year)
    # ZIP stores seconds in two-second increments.
    second = release_time.second - (release_time.second % 2)
    return (year, release_time.month, release_time.day, release_time.hour, release_time.minute, second)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', default='dist')
    parser.add_argument('--skip-validation', action='store_true')
    parser.add_argument(
        '--release-timestamp',
        help='ISO 8601 timestamp. Required outside Git; otherwise the HEAD commit timestamp is used.',
    )
    args = parser.parse_args()

    remove_python_cache()
    ensure_clean_git_tree()
    release_time = resolve_release_timestamp(args.release_timestamp)
    fixed_zip_time = zip_timestamp(release_time)

    output = (ROOT / args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    if not args.skip_validation:
        env = validation_env()
        subprocess.run([sys.executable, 'tools/validate_repository.py'], cwd=ROOT, check=True, env=env)
        subprocess.run([sys.executable, 'tools/generate_manifest.py', '--check'], cwd=ROOT, check=True, env=env)
    remove_python_cache()

    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    archive_name = f'peace-os-crisis-room-v{version}-source.zip'
    archive = output / archive_name
    include = list(controlled_files()) + [Path('MANIFEST.json'), Path('SHA256SUMS.txt')]
    sorted_include = sorted(include, key=lambda relative: relative.as_posix())

    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for relative in sorted_include:
            data = (ROOT / relative).read_bytes()
            info = zipfile.ZipInfo(f'peace-os-crisis-room-v{version}/{relative.as_posix()}', fixed_zip_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if relative.suffix == '.sh' else 0o644) << 16
            bundle.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    commit = source_commit()
    timestamp_utc = release_time.isoformat().replace('+00:00', 'Z')
    provenance = {
        'schema_version': '1.2',
        'artifact': 'Peace OS: Crisis Room',
        'repository': 'GLOBAL-AI-GOVERNANCE/peace-os-crisis-room',
        'version': version,
        'release_timestamp_utc': timestamp_utc,
        'release_date': release_time.date().isoformat(),
        'source_commit': commit,
        'source_commit_requirement': 'For a public release, source_commit must equal the exact released commit and the Git worktree must be clean.',
        'source_zip': {
            'filename': archive_name,
            'bytes': archive.stat().st_size,
            'sha256': sha(archive),
        },
        'verified_boundary': 'Repository validators, Python/JavaScript tests, parity contracts, cache checks, and deterministic packaging passed.',
        'runtime_status': 'Automated acceptance validates source, deployed assets, and browser journeys for the prerelease. Human user testing, assistive-technology, physical-device, professional, Godot, and Windows evidence remains separate.',
        'web_security_boundary': 'Review client uses meta CSP and JavaScript frame guard; stable hosting requires response-header frame-ancestors protection.',
        'windows_executable_included': False,
    }
    provenance_path = output / f'peace-os-crisis-room-v{version}-provenance.json'
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + '\n', encoding='utf-8')

    sbom_files = []
    sbom_relationships = []
    for index, relative in enumerate(sorted_include, start=1):
        spdx_id = f'SPDXRef-File-{index:04d}'
        sbom_files.append({
            'SPDXID': spdx_id,
            'checksums': [{'algorithm': 'SHA256', 'checksumValue': sha(ROOT / relative)}],
            'copyrightText': 'NOASSERTION',
            'fileName': relative.as_posix(),
            'licenseConcluded': 'NOASSERTION',
        })
        sbom_relationships.append({
            'spdxElementId': 'SPDXRef-Package-PeaceOS-CrisisRoom',
            'relationshipType': 'CONTAINS',
            'relatedSpdxElement': spdx_id,
        })

    release_sbom = {
        'SPDXID': 'SPDXRef-DOCUMENT',
        'creationInfo': {
            'created': timestamp_utc,
            'creators': [
                'Organization: GLOBAL-AI-GOVERNANCE',
                'Tool: Peace OS deterministic release builder',
            ],
        },
        'dataLicense': 'CC0-1.0',
        'documentNamespace': f'https://github.com/GLOBAL-AI-GOVERNANCE/peace-os-crisis-room/spdx/{version}/{commit}',
        'name': f'peace-os-crisis-room-v{version}-release',
        'packages': [
            {
                'SPDXID': 'SPDXRef-Package-PeaceOS-CrisisRoom',
                'checksums': [{'algorithm': 'SHA256', 'checksumValue': sha(archive)}],
                'copyrightText': 'NOASSERTION',
                'downloadLocation': f'https://github.com/GLOBAL-AI-GOVERNANCE/peace-os-crisis-room/releases/tag/v{version}',
                'externalRefs': [
                    {
                        'referenceCategory': 'PACKAGE-MANAGER',
                        'referenceLocator': f'pkg:github/GLOBAL-AI-GOVERNANCE/peace-os-crisis-room@v{version}',
                        'referenceType': 'purl',
                    }
                ],
                'filesAnalyzed': True,
                'licenseConcluded': 'MIT',
                'licenseDeclared': 'MIT',
                'name': 'Peace OS: Crisis Room',
                'versionInfo': version,
            }
        ],
        'files': sbom_files,
        'relationships': [
            {
                'relatedSpdxElement': 'SPDXRef-Package-PeaceOS-CrisisRoom',
                'relationshipType': 'DESCRIBES',
                'spdxElementId': 'SPDXRef-DOCUMENT',
            },
            *sbom_relationships,
        ],
        'spdxVersion': 'SPDX-2.3',
    }
    sbom_path = output / f'peace-os-crisis-room-v{version}-SBOM.spdx.json'
    sbom_path.write_text(json.dumps(release_sbom, indent=2, sort_keys=True) + '\n', encoding='utf-8')

    sums = output / f'peace-os-crisis-room-v{version}-SHA256SUMS.txt'
    sums.write_text(
        ''.join(
            f'{sha(path)}  {path.name}\n'
            for path in (archive, provenance_path, sbom_path)
        ),
        encoding='utf-8',
    )
    remove_python_cache()
    print(archive)
    print(provenance_path)
    print(sbom_path)
    print(sums)


if __name__ == '__main__':
    main()
