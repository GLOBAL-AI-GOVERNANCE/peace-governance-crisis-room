# Peace Governance Crisis Room

[![Source Checks](https://github.com/GLOBAL-AI-GOVERNANCE/peace-governance-crisis-room/actions/workflows/source-checks.yml/badge.svg?branch=main)](https://github.com/GLOBAL-AI-GOVERNANCE/peace-governance-crisis-room/actions/workflows/source-checks.yml)

**A fictional serious policy simulation for crisis verification, civilian protection, human release authority, and de-escalation under public pressure.**

- **Current source release:** `v0.2.2`
- **Maturity:** Source-ready educational prototype
- **Windows executable:** Not included
- **Runtime status:** Godot execution, Windows export, and external-PC testing remain physical validation gates

This project was previously presented as **Peace OS: Crisis Room**. The current public identity is **Peace Governance Crisis Room** because the repository is a bounded simulation and training prototype, not an operating system.

Players enter a fictional crisis room where viral media, incomplete evidence, public pressure, civilian risk, and escalation dynamics collide. The objective is not to accuse first. The objective is to verify responsibly, protect civilians, preserve institutional credibility, and prevent AI-assisted claims from outrunning evidence.

> Verification before amplification.
> Human control before release.
> Civilian protection before intelligence value.
> Confidence scoring before public attribution.

## Start Here

### Validate the source

From the repository root:

```bash
python tests/validate_scenario_json.py
python tests/validate_release_language.py
python tools/generate_manifest.py --check
python tools/validate_repository.py
```

### Run from source

1. Install a compatible Godot 4.x release.
2. Open `game/project.godot`.
3. Run the project.
4. Select Scenario 01 or Scenario 02.
5. Review evidence, mark risks, choose a confidence level, select release language, and complete the after-action review.

Running the Python checks does not prove that the Godot project launches or that every interaction works. Runtime claims require direct execution in Godot.

## Finished Outcome

A completed simulation session should produce a human-reviewed decision record containing:

- Evidence reviewed and evidence still missing
- Reliability and contradiction markings
- Selected confidence level
- Civilian-protection and information-integrity considerations
- Controlled public-release posture
- Consequence score
- After-action review findings

The simulation supports learning and facilitated discussion. Its output is not an operational intelligence product, factual attribution, legal conclusion, or real-world release authorization.

## Doctrine

The doctrine is documented in [`DOCTRINE.md`](DOCTRINE.md).

Core rules:

- Verification before amplification.
- Human control before release.
- Civilian protection before intelligence value.
- Confidence scoring before public attribution.
- AI may advise. AI may not decide.
- Do not let AI accelerate crisis before evidence catches up.

## Included Source

- Godot 4.x project source
- Two fictional crisis scenarios
- Visual crisis dashboard and meter system
- Public-pressure and decision-clock mechanics
- Evidence review and player marking states
- Confidence scoring and controlled release language
- Diagnostic score summary and after-action review
- Facilitator and observer mode
- Scenario and release-language validation scripts
- Windows export preset
- Source manifest and SHA-256 inventory
- Runtime and Windows release checklists

## Scenarios

1. **The Viral Collision Video**
   A disputed maritime collision video goes viral before verification is complete.

2. **The Deepfake Distress Call**
   A possible synthetic distress call triggers humanitarian urgency, translation uncertainty, and public pressure.

Both scenarios are fictional. They are not incident records, intelligence assessments, or representations of a specific government, organization, or person.

## Core Gameplay Loop

```text
Incident appears
↓
Evidence cards arrive
↓
Player reviews and marks evidence
↓
Public pressure rises
↓
Player assigns confidence
↓
Player checks civilian and information-integrity risks
↓
Player selects release posture
↓
Simulation scores consequences
↓
After-action review explains the result
```

## Evidence and Safety Boundary

This repository is:

- A serious policy simulation
- A training and education prototype
- A fictional crisis-verification exercise
- A bridge between tabletop analysis and interactive learning
- A source-side release candidate for runtime validation

This repository is not:

- An operational system
- An intelligence platform
- A legal attribution tool
- A government product
- A live maritime-awareness system
- A deepfake detection engine
- A substitute for human judgment
- A verified Windows executable release

No live AI, live data, real incident ingestion, classified information, real witness identity data, autonomous release authority, or legal attribution capability is included.

A passing source check establishes only that the committed files satisfy the repository's bounded structural rules. It does not establish runtime correctness, scenario validity for a real crisis, detection accuracy, policy compliance, or operational fitness.

## Runtime and Windows Release Gate

Before publishing a Windows executable:

1. Open the project in Godot 4.x.
2. Run both scenarios end to end.
3. Confirm evidence interactions and decision scoring.
4. Confirm after-action review export.
5. Export the Windows executable and `.pck`.
6. Test the packaged build on an external Windows PC.
7. Record the test environment and observed results.
8. Publish the Windows ZIP as a separate tested artifact.

See:

- [`docs/windows-export-guide.md`](docs/windows-export-guide.md)
- [`docs/public-build-candidate-checklist.md`](docs/public-build-candidate-checklist.md)
- [`docs/release-evidence/source-readiness-v0.2.2.md`](docs/release-evidence/source-readiness-v0.2.2.md)

## Repository Map

```text
game/                 Godot source project and fictional scenario data
tests/                Scenario and controlled-language validators
tools/                Repository and manifest validation
docs/                 Public documentation, provenance, and release evidence
builds/               Build boundary and future tested-package location
aar_reports/          Example or generated after-action material
MANIFEST.json         Deterministic source inventory
SHA256SUMS.txt         SHA-256 inventory for the same bounded file set
```

## Security

Use GitHub private vulnerability reporting for sensitive repository-integrity, unsafe-content, or disclosure concerns. See [`SECURITY.md`](SECURITY.md).

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md), [`DOCTRINE.md`](DOCTRINE.md), and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) before proposing changes.

## License

See [`LICENSE`](LICENSE).

**Do not let AI accelerate crisis before evidence catches up.**
