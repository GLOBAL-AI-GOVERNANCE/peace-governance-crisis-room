# Contributing

Contributions should preserve the project’s purpose: a fictional, bounded, safe serious game about AI governance, crisis verification, civilian protection, and de-escalation.

## Good Contributions

- fictional scenario improvements
- clearer evidence and AAR language
- accessibility improvements
- scoring/adjudication refinements
- facilitator notes and workshop guidance
- Godot UI polish
- documentation fixes
- validation test improvements

## Do Not Submit

Do not submit:

- live incident data
- classified, controlled, or sensitive material
- real witness identities or civilian personal data
- operational targeting details
- legal attribution claims
- autonomous escalation features
- live AI, live web scraping, or real-time incident ingestion for this release line

## Scenario Contribution Rule

Scenarios must be fictional or safely generalized. They may be inspired by real crisis patterns, but they must not claim to represent a real active incident or identify real private persons.

## Pull Request Checklist

Before opening a pull request:

```bash
python tests/validate_scenario_json.py
python tests/validate_release_language.py
```

Also confirm that new documentation does not describe the game as an operational tool, intelligence system, legal attribution engine, or government product.
