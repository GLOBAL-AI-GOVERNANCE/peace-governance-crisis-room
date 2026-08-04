# RC2 Exact-Deployment Evidence Contract

This contract controls the `v0.3.0-rc2` browser prerelease evidence.

## Exact deployment binding

The Pages artifact must include `deployment.json`, generated during the Pages workflow from:

- the exact workflow commit SHA;
- the canonical repository identity;
- the workflow run ID and attempt;
- a UTC generation time.

The deployed-browser UAT must fetch that file from the public Pages URL and reject the deployment unless its commit equals the exact accepted merge commit.

## Required deployed evidence

The Pages workflow publishes one immutable workflow artifact containing:

- `peace-os-crisis-room-v0.3.0-rc2-deployed-uat.json`;
- `peace-os-crisis-room-v0.3.0-rc2-deployed-uat.md`;
- `peace-os-crisis-room-v0.3.0-rc2-deployed-uat-SHA256SUMS.txt`.

The JSON record must identify the commit, deployed URL, browser, Node version, platform, UTC execution time, journeys, control checks, console findings, network findings, deployment metadata, and final status.

## Fail-closed behavior

A failed journey, failed control, console error, unexpected external request, deployment-metadata mismatch, or commit mismatch produces a failed workflow. It does not authorize the RC2 prerelease.

## Human evidence boundary

Exact deployed automated UAT is sufficient for the RC2 prerelease publication gate. It does not establish human usability, cross-browser certification, accessibility conformance, print/PDF usability, learning effectiveness, or professional validity. Those remain separate stable or post-publication evidence tracks and are not claimed by RC2.

## Stable evidence still open

RC2 does not establish WCAG conformance, full cross-browser support, physical-device coverage, educational validity, professional qualification, Godot readiness, Windows readiness, certification, or operational fitness.
