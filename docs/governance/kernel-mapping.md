# Governance Kernel Mapping

This document maps doctrine to the v0.3.0-rc1 simulation implementation.

| Doctrine requirement | Implementation | Evidence boundary |
|---|---|---|
| Policy before scoring | `game/data/governance/policy.json` is loaded and validated before scenarios | Static source and Python tests; runtime unverified |
| Complete evidence review | Assessment refuses fewer than all scenario cards | Reference test plus static GDScript contract |
| Human final authority | Consolidated review and separate confirmation are required before finalization | Simulation Boolean, not authenticated human identity |
| Confidence discipline | Confidence magnitude is scored separately from corroboration and authenticity | Scenario-defined educational rubric |
| Corroboration discipline | Independent support, contradiction, and absence of support are separate choices | Source model only; professional validity unverified |
| Authenticity discipline | Media-integrity status is separate from confidence | Source model only; no real authentication occurs |
| Corrective behavior | Final judgments are scored; histories are retained without correction penalty | Does not establish real-world judgment quality |
| Evidence-marking validity | Category-balanced, chance-corrected skill replaces raw agreement | Mathematical source contract; human-learning effect unverified |
| Bounded authority | Actions consume time and authority budgets; select-all fails closed | Educational resource model, not real authorization |
| Exact decision record | Canonical decision record is SHA-256 digested | Digest is unsigned |
| Traceability | Timestamped, sequence-numbered, hash-linked in-memory audit events | No independent anchor; full-chain recomputation remains possible |
| No external action | Policy disables live data, autonomous release, and action execution | Source boundary only |
| Publication control | Script asserts exact repository identity, default branch, permission, and reviewed base commit | Requires authenticated human maintainer and live GitHub execution |

The implementation is a bounded source demonstration. It is not a production governance kernel, safety certification, compliance determination, identity-proof system, or authorization service.
