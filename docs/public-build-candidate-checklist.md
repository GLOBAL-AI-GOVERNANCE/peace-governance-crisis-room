# Public Build Candidate Checklist

Use this checklist before publishing a Windows build.

## Runtime Test

- [ ] Open `game/` in Godot 4.x.
- [ ] Run the project from the editor.
- [ ] Complete Scenario 01 end-to-end.
- [ ] Complete Scenario 02 end-to-end.
- [ ] Confirm confidence scoring remains locked until enough evidence is reviewed.
- [ ] Confirm public pressure rises after major choices.
- [ ] Confirm evidence markings affect the score and AAR.
- [ ] Confirm scenario-aware controlled language appears.
- [ ] Confirm Score Summary appears.
- [ ] Confirm AAR export creates a JSON file.
- [ ] Confirm Facilitator / Observer View works.

## Windows Export

- [ ] Install Godot Windows export templates.
- [ ] Export using `game/export_presets.cfg`.
- [ ] Confirm output files exist:
  - `PeaceGovernanceCrisisRoom_v0.2.2.exe`
  - `PeaceGovernanceCrisisRoom_v0.2.2.pck`
- [ ] Test the exported build on a Windows machine.
- [ ] Package as `PeaceGovernanceCrisisRoom_v0.2.2_Windows.zip`.

## Release Hygiene

- [ ] Update README with screenshots or GIF.
- [ ] Confirm release notes mention the executable.
- [ ] Confirm no live data, no classified data, and no operational claims are included.
- [ ] Attach source ZIP and Windows ZIP to GitHub Releases.

## Boundary

Do not publish this as an operational, intelligence, legal, or government tool. It remains a fictional serious-game training prototype.


## v0.2.1 final source polish

This package updates the Godot project title to v0.2.1, separates initial evidence indicators from player markings, and recalibrates scoring so strong playthroughs receive clearer positive feedback while overclaiming remains heavily penalized.
