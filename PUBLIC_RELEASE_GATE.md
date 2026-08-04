# Public Release Gate

## `v0.3.0-rc2` prerelease scope

The approved public label is:

> **Peace OS: Crisis Room v0.3.0-rc2: Primer Closure and Contract Hardening**

A prerelease may be published after:

- the exact reviewed candidate is integrated through a protected pull request;
- required CI and repository protections permit merge;
- GitHub Pages deploys from the validated final `main` commit;
- deployment metadata served from the Pages site identifies that exact commit;
- deployed asset and browser-journey validation passes for that exact commit with no console errors or unexpected external requests;
- source, provenance, release SBOM, checksums, and acceptance reports are generated against the same final commit;
- downloaded release assets reverify;
- repository, release, tag, Pages, and public profile surfaces agree on the RC2 prerelease state.

For this RC2 prerelease, exact deployed automated UAT is the publication gate. Human keyboard, cross-browser, screen-reader, print/PDF, physical-device, and learning validation remain separate stable or post-publication evidence tracks and are not claimed by RC2.

## RC2 publication record

- Public prerelease: [`v0.3.0-rc2`](https://github.com/GLOBAL-AI-GOVERNANCE/peace-os-crisis-room/releases/tag/v0.3.0-rc2)
- Exact release commit: `aa6d8f75ce755fd143a4aa457eadf91b54604bd5`
- Exact deployed Pages workflow: [`30897461431`](https://github.com/GLOBAL-AI-GOVERNANCE/peace-os-crisis-room/actions/runs/30897461431) — **PASS**
- Commit-bound deployed-UAT artifact: `peace-os-v0.3.0-rc2-deployed-uat-aa6d8f75ce755fd143a4aa457eadf91b54604bd5`
- Artifact digest: `sha256:32c3ad4b4176816e310d1ea4694b6556fa255e6408e56e16b4f572fcd4952e4c`
- Ten custom release and evidence assets were downloaded and independently reverified after publication.
- Post-release documentation or workflow maintenance may advance `main` and Pages without moving the RC2 tag or replacing the verified release assets.

## Web security boundary

The review client uses a restrictive meta CSP and JavaScript frame guard. GitHub Pages does not provide repository-controlled arbitrary response headers. Before a stable security claim, either use hosting that can send `Content-Security-Policy: frame-ancestors 'none'` or explicitly accept and document the reduced anti-framing boundary.

## Stable-release holds

The following remain HOLD until independently evidenced:

- human keyboard-only and assistive-technology completion;
- human cross-browser and print/PDF acceptance;
- WCAG conformance;
- real-device mobile and 200 percent zoom review;
- independent subject-matter and measured human-learning validation;
- professional workshop, assessment, or certification use;
- Godot parser, import, runtime, and filesystem behavior;
- Windows executable distribution;
- operational, intelligence, emergency-response, or legal-attribution use.

The browser prerelease is a public review candidate, not a stable or certified product.
