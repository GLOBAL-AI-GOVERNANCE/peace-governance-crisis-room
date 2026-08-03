# Design Document: Peace OS: Crisis Room

## Release

`v0.3.0-rc1` is a source release candidate correcting the rc1 learning-validity, decision-flow, publication-identity, and source-UX defects. Runtime behavior remains unverified until Godot executes the project.

## Learning design

The participant must:

1. review every evidence card;
2. classify integrity, sensitivity, follow-up, and assessment use without being shown the answer key;
3. assess confidence magnitude;
4. assess independent corroboration;
5. assess media authenticity;
6. choose public language proportionate to those judgments;
7. construct a governance action plan within explicit time and authority budgets;
8. review the complete package;
9. provide explicit human confirmation before finalization.

The transparent doctrine score totals 100 points:

- evidence review: 10
- chance-corrected evidence marking: 20
- confidence magnitude: 15
- corroboration: 10
- authenticity: 10
- release posture: 15
- bounded governance actions: 15
- timeliness: 5

Diagnostic meters remain visible but do not create a second, contradictory outcome headline.

## Evidence-marking model

Each mark category is scored independently using chance-corrected balanced skill:

```text
skill = max(0, sensitivity + specificity - 1)
```

The four category skills are averaged and mapped to 20 points. All-positive, all-negative, and chance strategies do not receive the raw-agreement advantage present in rc1. Precision, recall, specificity, and skill are included in the AAR.

## Action model

Each action has:

- doctrine points;
- time cost;
- authority cost.

Each scenario defines finite budgets. Selecting every action exceeds at least one budget and blocks continuation. A scenario-specific doctrine-aligned plan reaches the full 15 action points within both budgets.

## Architecture

- `policy.json` establishes simulation-only boundaries and required safeguards before scenario use.
- Scenario JSON carries evidence, expected markings, three epistemic dimensions, release postures, action points, costs, and budgets.
- `Main.gd` provides UI state, reversible navigation, final-review and human-confirmation gates, scoring, decision digest, linked audit events, and AAR export.
- Python reference tests verify source contracts and scoring invariants without claiming Godot runtime equivalence.
- GitHub publication tooling fails closed on canonical identity and reviewed base-commit mismatch.

## Open design and validation questions

- Does the project parse and run in the current Godot 4 runtime?
- Does explicit safe focus produce a coherent keyboard and screen-reader order?
- Does scroll restoration behave correctly after live Control-tree rebuilds?
- Are the scenario markings, epistemic ranges, costs, and budgets professionally defensible?
- Do participants learn better judgment rather than merely optimize the rubric?
- Does the interface remain usable at 200% scaling and narrow window widths?

## Digest-bound confirmation

The human confirmation records the canonical digest of the current decision input. Any material revision invalidates confirmation. Finalization and AAR export fail closed unless the confirmed, final, and current digests agree.

## Assessment boundary

Assessment mode withholds authored metadata labels, coaching, and doctrine points until finalization. It remains a self-guided mode, not a secure or proctored assessment system.
