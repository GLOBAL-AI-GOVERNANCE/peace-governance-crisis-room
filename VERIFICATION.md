# Verification

This is the controlling public verification matrix for `v0.3.0-rc2`.

| Evidence class | Current status | Meaning |
|---|---|---|
| Source inventory and checksums | **PASS** | Controlled source files match `MANIFEST.json` and `SHA256SUMS.txt`. |
| Python regression suite | **PASS** | Governance, scoring, confirmation, privacy, operator, release, and acceptance contracts pass. |
| JavaScript scoring and golden parity | **PASS** | Browser scoring agrees with the Python reference vectors. |
| Shared core/client data parity | **PASS** | Authoritative core data matches web and Godot copies. |
| Extended reference-model analysis | **PASS** | 2,097,152 evidence-marking patterns and 23,552 decision states were exercised; random marking produced no Excellent outcomes. |
| Semantic web source contract | **PASS** | Neutral start, commit-before-results, focus, native controls, local-only behavior, and failure fallbacks are contract-tested. |
| Automated local browser journeys | **PASS with environment boundary** | Both scenarios, all modes, result controls, persistence, failure paths, keyboard entry, and 320-pixel layout passed in bounded local browser validation. |
| Deployed GitHub Pages browser validation | **PASS** | [Pages run `30897461431`](https://github.com/GLOBAL-AI-GOVERNANCE/peace-os-crisis-room/actions/runs/30897461431) deployed exact RC2 release commit `aa6d8f75ce755fd143a4aa457eadf91b54604bd5`. The full public browser journey suite passed and published commit-bound evidence artifact `peace-os-v0.3.0-rc2-deployed-uat-aa6d8f75ce755fd143a4aa457eadf91b54604bd5` with digest `sha256:32c3ad4b4176816e310d1ea4694b6556fa255e6408e56e16b4f572fcd4952e4c`. |
| Human keyboard and screen-reader completion | **PENDING FOR STABLE** | No conformance claim is made. |
| Real mobile device and 200% zoom | **PENDING FOR STABLE** | Automated responsiveness does not replace physical-device testing. |
| Firefox and Safari/WebKit human review | **PENDING FOR STABLE** | The prerelease remains a review candidate. |
| Human print/PDF and cross-browser usability | **PENDING FOR STABLE** | Automated output checks do not establish human usability or certification. |
| Godot import and runtime | **PENDING** | Static contracts do not establish parser, runtime, or filesystem behavior. |
| Windows package | **NOT INCLUDED** | A separately evidenced desktop release is required. |
| Subject-matter and human-learning validity | **PENDING** | Authored simulation coherence is not professional or educational validation. |

## Reproducible source checks

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tools/validate_repository.py
python3 tools/generate_manifest.py --check
node --test tests/js/*.test.mjs
node tests/js/web-static-check.mjs
python3 tests/http_asset_smoke.py
python3 tools/run_extended_vv.py --output /tmp/peace-os-extended-vv.json
python3 tools/run_automated_acceptance.py \
  --output-json /tmp/peace-os-acceptance.json \
  --output-md /tmp/peace-os-acceptance.md
```

## Public prerelease evidence

The public prerelease was published as [`v0.3.0-rc2`](https://github.com/GLOBAL-AI-GOVERNANCE/peace-os-crisis-room/releases/tag/v0.3.0-rc2) from exact release commit `aa6d8f75ce755fd143a4aa457eadf91b54604bd5` after required checks, Pages deployment, commit-bound `deployment.json`, deployed-browser journeys, deterministic rebuilds, matching provenance, and downloaded release-asset reverification passed. Later documentation or workflow maintenance may advance `main` and Pages without moving the RC2 tag or replacing the verified RC2 release assets.

Human accessibility, professional, Godot, Windows, certification, and operational evidence remain separate release paths. No result inherits PASS from another client, platform, or evidence class.
