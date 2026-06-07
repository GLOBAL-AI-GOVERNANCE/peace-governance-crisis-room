# Design Document

## Game Title

Peace OS: Crisis Room

## Genre

Serious policy simulation / crisis decision game.

## Current Version

`0.2.1` — Runtime Polish & Public Build Candidate source release.

## Core Question

Can a player prevent AI-assisted claims from escalating a crisis before evidence is strong enough?

## Design Goal

Make players feel why verification-before-amplification matters under public, political, humanitarian, and information-integrity pressure.

## Current Playable Scope

The v0.2.1 prototype contains two fictional scenarios:

1. **Scenario 01: The Viral Collision Video** — tests viral video pressure, missing metadata, incomplete AIS-style evidence, civilian witness risk, translation uncertainty, bot amplification, and cautious public release.
2. **Scenario 02: The Deepfake Distress Call** — tests humanitarian urgency, possible synthetic audio, translation uncertainty, family/civilian privacy risk, and the separation of safety action from public attribution.

The player reviews and marks evidence, assigns confidence, selects public release posture, chooses governance actions, receives a score summary, exports an AAR, and may view facilitator / observer notes.

## Core Gameplay Loop

```text
Scenario briefing
→ crisis dashboard
→ evidence review and marking
→ public pressure rises
→ confidence scoring
→ controlled release language
→ governance actions
→ consequence screen
→ score summary
→ diagnostic AAR
→ facilitator / observer view
```

## v0.2.1 Design Changes

This release implements the super UX review recommendations at the source level:

- public pressure now rises automatically after major choices,
- evidence marking affects scoring and AAR diagnostics,
- Scenario 02 receives scenario-aware controlled language recommendations,
- AAR feedback is organized into diagnostic sections,
- facilitator documentation is updated to reflect implemented observer mode.

## Learning Model

The game is not a prediction tool. It is a decision-friction laboratory. It reveals overclaiming, evidence gaps, civilian-risk failures, information-integrity failures, release-language mistakes, and the cost of letting public pressure outrun evidence.

## What This Game Can Claim

The game may support structured learning about decision friction, confidence discipline, civilian protection, information integrity, public release governance, and workshop facilitation.

## What This Game Cannot Claim

The game does not prove real-world policy effectiveness, forecast state behavior, conduct legal attribution, process live operational data, or replace expert judgment.
