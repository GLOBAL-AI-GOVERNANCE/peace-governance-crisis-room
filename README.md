# Peace OS: Crisis Room

**Peace OS: Crisis Room** is a fictional serious policy simulation game about AI governance, crisis verification, civilian protection, and de-escalation under public pressure.

Players enter a simulated crisis room where viral media, incomplete evidence, public pressure, civilian risk, and escalation dynamics collide. The objective is not to accuse first. The objective is to verify responsibly, protect civilians, preserve institutional credibility, and prevent AI-assisted claims from outrunning truth.

> Verification before amplification.  
> Human control before release.  
> Civilian protection before intelligence value.  
> Confidence scoring before public attribution.


## Doctrine

The doctrine is documented in [`DOCTRINE.md`](DOCTRINE.md).

Short form:

> Do not let AI accelerate crisis before truth catches up.

Core rules:

- Verification before amplification.
- Human control before release.
- Civilian protection before intelligence value.
- Confidence scoring before public attribution.
- AI may advise. AI may not decide.

## Current Release

**Version:** `v0.2.1`  
**Label:** `Public Build Candidate Source`  
**Windows executable:** Not included yet  
**Next gate:** Godot runtime test, Windows export, external PC test, Windows ZIP package

This release is source-side complete. It is ready to be opened in Godot 4.x, run end-to-end, exported to Windows, and tested outside Godot.

## What Is Included

- Godot 4.x source project
- Two fictional crisis scenarios
- Visual crisis dashboard and meter system
- Public pressure / decision clock
- Evidence review and player marking states
- Confidence scoring and controlled release language
- Diagnostic score summary and after-action review
- Facilitator / observer mode
- Scenario and release-language validation scripts
- Windows export preset and release checklist

## Scenarios

1. **The Viral Collision Video**  
   A disputed maritime collision video goes viral before verification is complete.

2. **The Deepfake Distress Call**  
   A possible synthetic distress call triggers humanitarian urgency, translation uncertainty, and public pressure.

## What This Is

- A serious policy simulation game
- A source-side public build candidate
- A training and education prototype
- A fictional crisis-verification exercise
- A bridge between tabletop analysis and interactive learning

## What This Is Not

This is not:

- an operational system
- an intelligence platform
- a legal attribution tool
- a government product
- a live maritime-awareness system
- a deepfake detection engine
- a substitute for human judgment

No live AI, live data, real incident ingestion, classified information, real witness identity data, or legal attribution capability is included.

## Run From Source

1. Install Godot 4.x.
2. Open `game/project.godot`.
3. Run the project.
4. Select Scenario 01 or Scenario 02.
5. Review evidence, mark risks, choose confidence, select release language, and complete the AAR.

## Validate The Source

From the repository root:

```bash
python tests/validate_scenario_json.py
python tests/validate_release_language.py
```

Both tests should pass before release.

## Build Windows Release

The source includes a Windows export preset. The final public Windows release is pending physical export and external testing.

Expected final Windows ZIP:

```text
PeaceOS_CrisisRoom_v0.2.1_Windows/
├── PeaceOS_CrisisRoom_v0.2.1.exe
├── PeaceOS_CrisisRoom_v0.2.1.pck
├── README_PLAY.md
├── RELEASE_NOTES_WINDOWS.md
└── LICENSE
```

See:

- `docs/windows-export-guide.md`
- `docs/public-build-candidate-checklist.md`

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
Player assigns confidence level
↓
Player checks civilian and information-integrity risks
↓
Player selects release posture
↓
Game scores consequences
↓
AAR explains what happened
```

## Core Lesson

**Do not let AI accelerate crisis before truth catches up.**

## Suggested Repository Topics

`godot`, `serious-game`, `policy-simulation`, `ai-governance`, `crisis-simulation`, `verification`, `osint`, `wargame`, `training-tool`, `peacebuilding`

## License

See `LICENSE`.
