# Source Readiness Evidence — v0.2.2

## Decision

**PASS for public source readiness.**

**NOT YET VERIFIED as a runtime-tested Godot build or Windows executable release.**

## Automated checks

The release candidate must pass:

```bash
python tests/validate_scenario_json.py
python tests/validate_release_language.py
python tools/generate_manifest.py --check
python tools/validate_repository.py
```

These checks cover:

- Two required fictional scenarios
- Controlled confidence and release-language keys
- JSON parsing
- Required repository files
- Internal Markdown links
- Public maturity and safety boundaries
- Absence of committed executable and packaged-build artifacts
- Full-SHA GitHub Actions pinning
- Deterministic manifest and SHA-256 parity
- Removal of one-time publishing clutter

## Human review boundary

The automated checks do not open Godot, execute the simulation, inspect the visual experience, validate accessibility, test after-action review export, export Windows binaries, or test a package on an external PC.

## Remaining physical gate

Before a Windows release:

1. Run both scenarios in Godot.
2. Exercise evidence marking, confidence selection, release posture, scoring, and after-action review.
3. Confirm expected local output behavior.
4. Export the Windows executable and `.pck`.
5. Test the ZIP on another Windows computer.
6. Record the Godot version, operating system, test date, tester, results, and known limitations.
7. Publish the tested artifact separately.

## Evidence boundary

This evidence supports only the source-readiness claim for commit-level repository content. It is not proof of operational suitability, factual attribution capability, legal compliance, or real-world crisis performance.
