# Semantic web client

Serve this directory through HTTP. It uses the generated `web/data/` copy of the authoritative `core/` contracts.

```bash
python -m http.server 8000 --directory web
```

The client is local-only: no account, telemetry, cloud backend, or external AI. It provides explicit resume, start-new, and delete-session controls. AAR files are created locally through browser download.

The review client includes a restrictive meta CSP and an external JavaScript frame guard. Stable anti-framing protection requires HTTP response headers from a host that supports `frame-ancestors 'none'`.

GitHub Pages deployment is a review gate, not proof of accessibility or professional validity.
