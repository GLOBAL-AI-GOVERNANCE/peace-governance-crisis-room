#!/usr/bin/env python3
"""Write deployment-only metadata into the Pages artifact.

The generated file is intentionally not committed. It binds the deployed browser
artifact to the exact GitHub Actions commit and workflow run that produced it.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--run-attempt', required=True)
    args = parser.parse_args()

    commit = args.commit.strip().lower()
    if len(commit) != 40 or any(ch not in '0123456789abcdef' for ch in commit):
        raise SystemExit('STOP: deployment commit must be a full 40-character Git SHA.')

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    record = {
        'schema_version': '1.0',
        'repository': args.repository,
        'commit': commit,
        'workflow_run_id': str(args.run_id),
        'workflow_run_attempt': str(args.run_attempt),
        'generated_at_utc': datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
        'purpose': 'Exact-commit binding for the deployed Peace OS browser review candidate.',
        'limitations': [
            'Workflow-generated metadata, not an external trusted timestamp.',
            'Does not establish identity or prove real-world activity.',
        ],
    }
    output.write_text(json.dumps(record, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(f'PASS: deployment metadata written for {commit}.')


if __name__ == '__main__':
    main()
