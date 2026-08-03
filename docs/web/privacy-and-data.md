# Browser privacy, data, and embedding boundary

The browser client requires no login, telemetry, analytics, cloud service, or external AI. Session data is stored only in the browser's local storage when that feature is available. If storage is denied or unavailable, the simulation continues in memory-only mode and tells the user that resume is unavailable. Starting a new session or confirming saved-session deletion clears only browser-local session state. Downloaded AAR files are not deleted. AAR files are generated locally through the browser download mechanism.

Hosting infrastructure may independently retain ordinary access logs; the repository does not add analytics.

## Framing limitation

A meta-delivered Content Security Policy cannot enforce `frame-ancestors`. The review client therefore includes a JavaScript frame guard as a limited fallback. A stable deployment should be hosted where HTTP response headers can enforce:

```text
Content-Security-Policy: frame-ancestors 'none'
X-Frame-Options: DENY
```

The JavaScript guard is defense in depth, not a substitute for response-header enforcement.

## Failure handling

Clipboard and download operations report success or failure. Clipboard denial presents a selectable manual-copy field. Download failure leaves copy and print fallbacks available.
