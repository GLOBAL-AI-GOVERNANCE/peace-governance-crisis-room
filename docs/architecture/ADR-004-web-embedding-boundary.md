# ADR-004: Web embedding boundary

**Decision:** The review client uses a restrictive meta CSP and an external JavaScript frame guard. Stable publication requires response-header anti-framing controls.

**Reason:** GitHub Pages cannot configure arbitrary response headers, and browsers ignore `frame-ancestors` when it is delivered through a meta tag.

**Stable gate:** Host the stable web client where `Content-Security-Policy: frame-ancestors 'none'` and `X-Frame-Options: DENY` can be sent as HTTP response headers.
