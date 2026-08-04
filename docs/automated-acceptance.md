# Automated acceptance validation

The `v0.3.0-rc2` release workflow uses automated acceptance validation to verify the exact public candidate before publication.

The release controller verifies:

- repository identity and exact commit lineage;
- source inventory, tests, scoring invariants, and shared-data parity;
- public/private and personal-data boundaries;
- semantic accessibility source contracts;
- exact GitHub Pages assets, workflow-generated `deployment.json`, and expected product markers;
- complete browser journeys for both scenarios and all three modes;
- confirmation invalidation, retained corrupt-session handling, schema-valid downloaded AARs, print completeness, and narrow-screen behavior;
- absence of unexpected external runtime dependencies;
- exact-commit provenance, SBOM, and release checksums.

The workflow produces human-readable Markdown, machine-readable JSON, and a SHA-256 ledger bound to the deployed URL and exact commit. The workflow fails on a deployment-metadata mismatch, failed journey, failed control, browser console error, or unexpected external request.

Automated acceptance validation does not establish human usability, learning effectiveness, screen-reader compatibility, WCAG conformance, professional assessment validity, operational fitness, or Godot and Windows runtime readiness. Those remain separate evidence streams for stable or desktop releases.
