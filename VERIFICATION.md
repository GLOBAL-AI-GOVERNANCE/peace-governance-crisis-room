# Verification

This is the controlling public verification matrix for `v0.3.0-rc2`.

| Evidence class | Status before live integration | Meaning |
|---|---|---|
| Source inventory and checksums | **PASS** | Controlled source files match `MANIFEST.json` and `SHA256SUMS.txt`. |
| Python regression suite | **PASS** | Governance, scoring, confirmation, privacy, operator, release, and acceptance contracts pass. |
| JavaScript scoring and golden parity | **PASS** | Browser scoring agrees with the Python reference vectors. |
| Shared core/client data parity | **PASS** | Authoritative core data matches web and Godot copies. |
| Extended reference-model analysis | **PASS** | 2,097,152 evidence-marking patterns and 23,552 decision states were exercised; random marking produced no Excellent outcomes. |
| Semantic web source contract | **PASS** | Neutral start, commit-before-results, focus, native controls, local-only behavior, and failure fallbacks are contract-tested. |
| Automated local browser journeys | **PASS with environment boundary** | Both scenarios, all modes, result controls, persistence, failure paths, keyboard entry, and 320-pixel layout passed in bounded local browser validation. |
| Deployed GitHub Pages browser validation | **AUTOMATED CONTRACT IMPLEMENTED; RC2 EXECUTION PENDING** | Pages generates exact-commit deployment metadata, deploys the accepted commit, runs the full public browser journey suite, and publishes hashed evidence. PASS may be recorded only after the merged RC2 workflow succeeds. |
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

The prerelease may be published only after the exact reviewed source is integrated, required checks pass, Pages deploys the exact final commit, `deployment.json` binds the public artifact to that commit, automated deployed-browser journeys pass without console errors or unexpected external requests, deterministic artifacts are rebuilt, provenance matches the final commit, and release assets reverify after download.

Human accessibility, professional, Godot, Windows, certification, and operational evidence remain separate release paths. No result inherits PASS from another client, platform, or evidence class.
