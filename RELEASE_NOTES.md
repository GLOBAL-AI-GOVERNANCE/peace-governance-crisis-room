# Release Notes

## v0.2.2 — Public Source Readiness

### Public identity

- Aligns the repository to **Peace Governance Crisis Room**.
- Preserves **Peace OS: Crisis Room** as the prior project title.
- Clarifies that this is a simulation and training prototype, not an operating system.

### Source verification

- Runs both existing scenario and controlled-language validators.
- Adds repository structure, boundary, link, JSON, workflow-pin, and artifact checks.
- Adds a deterministic source manifest and SHA-256 inventory.
- Adds hosted source checks with read-only workflow permissions.

### Public cleanup

- Removes one-time publishing instructions and stale root-level verification artifacts.
- Moves source-framework notes into `docs/provenance/`.
- Replaces the old final-verification claim with bounded source-readiness evidence.

### Physical gates still open

This source release does not claim:

- Godot runtime execution
- End-to-end scenario completion
- After-action review export
- Windows export
- External-PC package testing
- A production-ready game or operational system

Those gates must be completed before a Windows executable is published.
