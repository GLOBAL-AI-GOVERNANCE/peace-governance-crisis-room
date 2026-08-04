# Public Release Gate

## `v0.3.0-rc2` prerelease scope

The approved public label is:

> **Peace OS: Crisis Room v0.3.0-rc2: Primer Closure and Contract Hardening**

A prerelease may be published after:

- the exact reviewed candidate is integrated through a protected pull request;
- required CI and repository protections permit merge;
- GitHub Pages deploys from the validated final `main` commit;
- deployed asset and browser-journey validation passes for that exact commit;
- source, provenance, release SBOM, checksums, and acceptance reports are generated against the same final commit;
- downloaded release assets reverify.

Automated validation does not replace human user testing, accessibility conformance evaluation, professional learning validation, or platform-specific runtime evidence.

## Web security boundary

The review client uses a restrictive meta CSP and JavaScript frame guard. GitHub Pages does not provide repository-controlled arbitrary response headers. Before a stable security claim, either use hosting that can send `Content-Security-Policy: frame-ancestors 'none'` or explicitly accept and document the reduced anti-framing boundary.

## Stable-release holds

The following remain HOLD until independently evidenced:

- human keyboard-only and assistive-technology completion;
- WCAG conformance;
- real-device mobile and 200 percent zoom review;
- independent subject-matter and measured human-learning validation;
- professional workshop, assessment, or certification use;
- Godot parser, import, runtime, and filesystem behavior;
- Windows executable distribution;
- operational, intelligence, emergency-response, or legal-attribution use.

The browser prerelease is a public review candidate, not a stable or certified product.
