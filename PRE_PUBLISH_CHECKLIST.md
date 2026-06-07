# Pre-Publish Checklist

## Before First Push

- [ ] Unzip `peace-os-crisis-room-v0.2.1-doctrine-verified-source.zip`.
- [ ] Review the repository root and confirm the final publication files are present.
- [ ] Confirm `.gitignore` does not exclude `game/export_presets.cfg`.
- [ ] Run `python tests/validate_scenario_json.py`.
- [ ] Run `python tests/validate_release_language.py`.
- [ ] Confirm README says this is a source-side public build candidate, not a Windows executable release.

## Before GitHub Release

- [ ] Create tag `v0.2.1`.
- [ ] Use release title: `Peace OS: Crisis Room v0.2.1 — Public Build Candidate Source`.
- [ ] Attach `peace-os-crisis-room-v0.2.1-doctrine-verified-source.zip`.
- [ ] Attach `peace-os-crisis-room-v0.2.1-final-verification-report.md`.
- [ ] Optional: attach `peace-os-crisis-room-v0.2.1-doctrine-verified.git.bundle`.
- [ ] Do not attach a Windows executable ZIP until it is exported and tested outside Godot.

## After GitHub Release

- [ ] Open source in Godot 4.x.
- [ ] Run both scenarios end-to-end.
- [ ] Confirm AAR export.
- [ ] Export Windows build.
- [ ] Test on another Windows PC.
- [ ] Package `PeaceOS_CrisisRoom_v0.2.1_Windows.zip`.
- [ ] Attach Windows ZIP to release or publish follow-up build asset.
