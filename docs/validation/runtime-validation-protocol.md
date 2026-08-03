# Runtime Validation Protocol

Use the current stable Godot 4.x release selected by the maintainer and record its exact version, download source, operating system, architecture, commit, display scale, input devices, and assistive technology. Source tests do not satisfy this protocol.

## Import and parser gate

1. Start from a clean extracted source tree.
2. Import `game/project.godot`.
3. Record every parser, import, warning, and runtime message.
4. Require zero parser errors and zero blocker or critical startup defects.

## Scenario protocol

For each scenario:

1. Start from a clean launch.
2. Confirm the policy boundary is visible before play.
3. Verify main-menu focus starts on a scenario, not facilitator mode.
4. Verify learner mode hides facilitator indicators.
5. Attempt early assessment and confirm complete-evidence refusal.
6. Review every card and test every CheckBox marking control.
7. Confirm mark toggles preserve card scroll position and focus context.
8. Test time advance; verify a confirmation screen appears before time changes.
9. Change an unsafe confidence to a defensible choice and confirm no correction penalty.
10. Repeat for corroboration and authenticity.
11. Verify the release screen distinguishes current choice, system critique, and safer alternatives.
12. Enter the action screen, confirm Back navigation works, and verify select-all exceeds budget and cannot continue.
13. Verify a valid bounded action plan can continue.
14. Confirm the consolidated final-review screen includes epistemic judgments, release posture, action costs, budget, and unresolved risks.
15. Attempt finalization without human confirmation and verify refusal.
16. Finalize and confirm score and consequence headline agree.
17. Export the AAR; verify visible success, absolute path, Open Folder, required fields, decision digest, audit chain, event timestamps, and audit limitation.
18. Induce a filesystem error if safely possible and verify visible failure feedback.
19. Restart and repeat without stale state.

## Accessibility and responsive checks

- keyboard-only traversal and visible focus;
- screen-reader names and state announcements;
- 200% text/display scaling;
- narrow-window behavior without clipping or hidden horizontal overflow;
- color-independent meter meaning;
- reduced-motion behavior if motion is introduced;
- touch and gamepad behavior only if claimed.

## Pass rule

A runtime PASS requires:

- zero parser errors;
- no blocker or critical defect;
- expected scores for all regression cases;
- valid bounded action behavior;
- coherent score and consequence feedback;
- successful and failed AAR export paths visibly handled;
- recorded evidence for both scenarios;
- no accessibility blocker for the claimed input modes.
