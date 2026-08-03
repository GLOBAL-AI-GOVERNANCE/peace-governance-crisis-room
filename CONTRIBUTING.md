# Contributing

Read `DOCTRINE.md`, `SECURITY.md`, and `CODE_OF_CONDUCT.md` before contributing.

A change is reviewable when it includes:

- the problem and evidence;
- the doctrine or learning objective affected;
- tests for scoring, policy, or data-contract changes;
- declared assumptions and remaining limitations;
- no live incident data, personal data, classified material, or autonomous-action capability.

Changes to scoring, scenario data, policy, release language, AAR records, or finalization gates trigger re-audit under `docs/validation/re-audit-triggers.md`.

Run before opening a pull request:

```bash
python tools/sync_core_data.py
python tests/generate_golden_vectors.py
python tools/validate_repository.py
python tools/generate_manifest.py --check
python tests/browser_smoke.py
```

The browser smoke script may report HOLD when the local container cannot execute Chromium. Required browser evidence must be collected from a supported environment or deployed review URL.
