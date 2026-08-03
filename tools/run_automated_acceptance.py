#!/usr/bin/env python3
"""Run automated source, deployed-asset, and browser-journey validation."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_REPOSITORY = 'GLOBAL-AI-GOVERNANCE/peace-os-crisis-room'
EXPECTED_ASSETS = {
    '': ('Peace OS: Crisis Room', 'Verification before amplification'),
    'app.js': ('Decision fingerprint', 'Download After-Action Review Record'),
    'styles.css': (':focus-visible', 'prefers-reduced-motion'),
    'scoring.js': ('scoreDecision',),
    'data/scenarios/index.json': ('scenario_01_viral_collision_video', 'scenario_02_deepfake_distress_call'),
    'data/scoring/scoring_rubric.json': ('minimum_evidence_marking', 'score_components'),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_output(*args: str) -> str:
    try:
        return subprocess.check_output(['git', *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return 'NOT_A_GIT_COMMIT'


def fetch(url: str, timeout: int = 30) -> tuple[int, bytes, str]:
    request = urllib.request.Request(url, headers={'User-Agent': 'Peace-OS-Automated-Acceptance/1.0'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.read(), response.headers.get('content-type', '')


def run_source_checks() -> list[dict[str, object]]:
    # The bounded repository validator already runs Python, JavaScript, static-web,
    # HTTP-resource, policy, parity, privacy, link, and workflow checks. Avoid
    # rerunning those child processes here; duplicate local-server checks can add
    # noise and make release execution less reliable without adding coverage.
    commands = [
        [sys.executable, 'tools/validate_repository.py'],
        [sys.executable, 'tools/generate_manifest.py', '--check'],
    ]
    results: list[dict[str, object]] = []
    env = dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    for command in commands:
        with tempfile.TemporaryFile(mode='w+', encoding='utf-8') as stdout_file, tempfile.TemporaryFile(mode='w+', encoding='utf-8') as stderr_file:
            try:
                process = subprocess.run(
                    command,
                    cwd=ROOT,
                    text=True,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    env=env,
                    timeout=300,
                )
                returncode = process.returncode
                timed_out = False
            except subprocess.TimeoutExpired:
                returncode = 124
                timed_out = True
            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout = stdout_file.read()
            stderr = stderr_file.read()
        results.append({
            'command': ' '.join(command),
            'returncode': returncode,
            'status': 'PASS' if returncode == 0 else 'FAIL',
            'timed_out': timed_out,
            'stdout_tail': stdout[-2000:],
            'stderr_tail': stderr[-2000:],
        })
    return results


def deployment_asset_checks(base_url: str) -> list[dict[str, object]]:
    normalized = base_url.rstrip('/') + '/'
    results: list[dict[str, object]] = []
    for relative, markers in EXPECTED_ASSETS.items():
        url = urllib.parse.urljoin(normalized, relative)
        try:
            status, data, content_type = fetch(url)
            text = data.decode('utf-8', errors='replace')
            missing = [marker for marker in markers if marker not in text]
            results.append({
                'asset': relative or 'index.html',
                'url': url,
                'http_status': status,
                'content_type': content_type,
                'bytes': len(data),
                'sha256': sha256(data),
                'missing_markers': missing,
                'status': 'PASS' if status == 200 and not missing else 'FAIL',
            })
        except Exception as exc:
            results.append({'asset': relative or 'index.html', 'url': url, 'status': 'FAIL', 'error': str(exc)})
    return results


def external_reference_check() -> dict[str, object]:
    files = [ROOT/'web'/'index.html', ROOT/'web'/'app.js', ROOT/'web'/'styles.css', ROOT/'web'/'manifest.webmanifest']
    refs: list[str] = []
    pattern = re.compile(r'https?://[^\s"\'<>)]+' )
    for path in files:
        refs.extend(pattern.findall(path.read_text(encoding='utf-8')))
    allowed = [ref for ref in refs if ref.startswith('https://github.com/GLOBAL-AI-GOVERNANCE/peace-os-crisis-room')]
    unexpected = sorted(set(refs) - set(allowed))
    return {'status': 'PASS' if not unexpected else 'FAIL', 'unexpected_external_references': unexpected}


def run_browser_journeys(base_url: str, expected_commit: str, output_json: Path, output_md: Path) -> dict[str, object]:
    command = [
        'node', 'tests/deployed_browser_uat.mjs',
        '--base-url', base_url,
        '--expected-commit', expected_commit,
        '--output-json', str(output_json),
        '--output-md', str(output_md),
    ]
    with tempfile.TemporaryFile(mode='w+', encoding='utf-8') as stdout_file, tempfile.TemporaryFile(mode='w+', encoding='utf-8') as stderr_file:
        try:
            process = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                stdout=stdout_file,
                stderr=stderr_file,
                timeout=600,
            )
            returncode = process.returncode
            timed_out = False
        except subprocess.TimeoutExpired:
            returncode = 124
            timed_out = True
        stdout_file.seek(0)
        stderr_file.seek(0)
        stdout = stdout_file.read()
        stderr = stderr_file.read()
    if output_json.exists():
        record = json.loads(output_json.read_text(encoding='utf-8'))
    else:
        record = {
            'status': 'FAIL',
            'error': 'browser journey report was not created',
        }
    record['command'] = ' '.join(command)
    record['returncode'] = returncode
    record['timed_out'] = timed_out
    record['stdout_tail'] = stdout[-4000:]
    record['stderr_tail'] = stderr[-4000:]
    if returncode != 0:
        record['status'] = 'FAIL'
    return record


def render_markdown(record: dict[str, object]) -> str:
    lines = [
        '# Peace OS Automated Acceptance Validation Report',
        '',
        f"**Repository:** `{record['repository']}`  ",
        f"**Commit:** `{record['commit']}`  ",
        f"**Pages URL:** `{record.get('pages_url') or 'not supplied'}`  ",
        f"**Generated:** `{record['generated_at_utc']}`  ",
        f"**Overall status:** **{record['status']}**",
        '',
        '> Automated acceptance validation is not human user acceptance testing or a WCAG conformance claim.',
        '',
        '## Source validation',
        '',
        '| Check | Status |',
        '|---|---|',
    ]
    for item in record['source_checks']:
        lines.append(f"| `{item['command']}` | **{item['status']}** |")
    lines.extend(['', '## Deployed asset validation', '', '| Asset | Status | SHA-256 |', '|---|---|---|'])
    if record['deployment_asset_checks']:
        for item in record['deployment_asset_checks']:
            lines.append(f"| `{item['asset']}` | **{item['status']}** | `{item.get('sha256','')}` |")
    else:
        lines.append('| Deployment not supplied | **SKIPPED** | |')
    browser = record.get('deployed_browser_journeys')
    lines.extend(['', '## Deployed browser journeys', ''])
    if browser:
        lines.append(f"**Status:** **{browser.get('status', 'FAIL')}**  ")
        lines.append(f"**Browser:** `{browser.get('browser', {}).get('version', 'not recorded')}`")
        for journey in browser.get('journeys', []):
            lines.append(f"- `{journey.get('scenario_id')}` / `{journey.get('mode')}`: **{journey.get('status')}**")
    else:
        lines.append('**SKIPPED:** no deployed URL was supplied.')
    lines.extend([
        '',
        '## Boundaries',
        '',
        '- This report verifies automated source, deployment, and browser-journey contracts.',
        '- Human accessibility, learning effectiveness, subject-matter validity, Godot runtime, Windows runtime, certification, and operational fitness are not established.',
        '',
    ])
    return '\n'.join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', help='Exact deployed GitHub Pages URL to verify.')
    parser.add_argument('--expected-commit', help='Require the current source commit to equal this full SHA.')
    parser.add_argument('--skip-source-checks', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--output-json', default='automated-acceptance.json')
    parser.add_argument('--output-md', default='automated-acceptance.md')
    parser.add_argument('--browser-output-json')
    parser.add_argument('--browser-output-md')
    args = parser.parse_args()

    commit = git_output('rev-parse', 'HEAD')
    if args.expected_commit and commit != args.expected_commit:
        raise SystemExit(f'STOP: source commit {commit} != expected {args.expected_commit}')
    if args.base_url and not args.expected_commit:
        raise SystemExit('STOP: deployed acceptance requires --expected-commit')

    source_checks = [] if args.skip_source_checks else run_source_checks()
    assets = deployment_asset_checks(args.base_url) if args.base_url else []
    external = external_reference_check()
    browser: dict[str, object] | None = None
    if args.base_url:
        browser_json = Path(args.browser_output_json) if args.browser_output_json else Path(tempfile.gettempdir()) / 'peace-os-deployed-browser-uat.json'
        browser_md = Path(args.browser_output_md) if args.browser_output_md else Path(tempfile.gettempdir()) / 'peace-os-deployed-browser-uat.md'
        browser = run_browser_journeys(args.base_url, args.expected_commit, browser_json, browser_md)

    pass_all = all(item['status'] == 'PASS' for item in source_checks)
    pass_all = pass_all and all(item['status'] == 'PASS' for item in assets)
    pass_all = pass_all and external['status'] == 'PASS'
    if args.base_url:
        pass_all = pass_all and browser is not None and browser.get('status') == 'PASS'

    record: dict[str, object] = {
        'schema_version': '1.1',
        'acceptance_class': 'automated_acceptance_validation',
        'human_uat_status': 'PENDING_FOR_STABLE',
        'repository': EXPECTED_REPOSITORY,
        'commit': commit,
        'pages_url': args.base_url,
        'generated_at_utc': datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z'),
        'source_checks': source_checks,
        'deployment_asset_checks': assets,
        'deployed_browser_journeys': browser,
        'external_reference_check': external,
        'status': 'PASS' if pass_all else 'FAIL',
        'stable_release_holds': [
            'human keyboard and assistive-technology completion',
            'WCAG conformance',
            'physical mobile and zoom review',
            'subject-matter and human-learning validation',
            'Godot runtime',
            'Windows runtime',
            'professional, certification, and operational claims',
        ],
    }
    Path(args.output_json).write_text(json.dumps(record, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    Path(args.output_md).write_text(render_markdown(record), encoding='utf-8')
    if not pass_all:
        raise SystemExit('STOP: automated acceptance validation failed.')
    print('PASS: automated acceptance validation complete.')


if __name__ == '__main__':
    main()
