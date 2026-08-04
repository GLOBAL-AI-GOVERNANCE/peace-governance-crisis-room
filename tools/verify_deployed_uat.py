#!/usr/bin/env python3
"""Fail closed unless deployed-browser UAT is PASS for the exact deployment."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


def normalized_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        raise SystemExit(f'STOP: invalid deployed URL: {value!r}')
    return value.rstrip('/') + '/'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--expected-commit', required=True)
    parser.add_argument('--expected-url', required=True)
    args = parser.parse_args()

    path = Path(args.input)
    record = json.loads(path.read_text(encoding='utf-8'))
    commit = args.expected_commit.lower()
    expected_url = normalized_url(args.expected_url)

    failures: list[str] = []
    if record.get('status') != 'PASS':
        failures.append('overall deployed UAT status is not PASS')
    if record.get('expected_commit') != commit:
        failures.append('expected_commit does not equal the exact merge SHA')
    if normalized_url(str(record.get('base_url', ''))) != expected_url:
        failures.append('base_url does not equal the Pages deployment URL')
    deployment = record.get('deployment_metadata') or {}
    if deployment.get('commit') != commit:
        failures.append('deployment metadata does not bind the exact merge SHA')
    if deployment.get('repository') != 'GLOBAL-AI-GOVERNANCE/peace-os-crisis-room':
        failures.append('deployment metadata repository identity is wrong')
    if record.get('console_errors'):
        failures.append('console errors were recorded')
    if record.get('unexpected_network_requests'):
        failures.append('unexpected network requests were recorded')
    journeys = record.get('journeys') or []
    if not journeys or any(item.get('status') != 'PASS' for item in journeys):
        failures.append('one or more deployed browser journeys did not pass')
    controls = record.get('control_checks') or {}
    if not controls or not all(value is True for value in controls.values()):
        failures.append('one or more deployed browser control checks did not pass')

    if failures:
        raise SystemExit('STOP: deployed UAT verification failed:\n- ' + '\n- '.join(failures))
    print(f'PASS: deployed UAT is bound to {commit} at {expected_url}.')


if __name__ == '__main__':
    main()
