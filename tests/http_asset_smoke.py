#!/usr/bin/env python3
"""Verify every public web resource over a bounded local HTTP server."""
from __future__ import annotations

import http.server
import socket
import threading
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = [
    '/',
    '/app.js',
    '/frame-guard.js',
    '/scoring.js',
    '/styles.css',
    '/manifest.webmanifest',
    '/data/scenarios/index.json',
    '/data/scenarios/scenario_01_viral_collision_video.json',
    '/data/scenarios/scenario_02_deepfake_distress_call.json',
    '/data/scoring/scoring_rubric.json',
    '/data/governance/policy.json',
]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'

    def log_message(self, *_args: object) -> None:
        return


def main() -> None:
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]

    server = http.server.HTTPServer(
        ('127.0.0.1', port),
        lambda *args, **kwargs: QuietHandler(*args, directory=str(ROOT / 'web'), **kwargs),
    )
    server.timeout = 5

    def serve_expected_requests() -> None:
        for _ in PATHS:
            server.handle_request()

    thread = threading.Thread(target=serve_expected_requests, daemon=True)
    thread.start()

    try:
        for path in PATHS:
            request = urllib.request.Request(
                f'http://127.0.0.1:{port}{path}',
                headers={'Connection': 'close', 'User-Agent': 'Peace-OS-HTTP-Smoke/1.0'},
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                payload = response.read()
                if response.status != 200 or not payload:
                    raise SystemExit(f'HTTP asset smoke failed: {path}')
        thread.join(timeout=10)
        if thread.is_alive():
            raise SystemExit('HTTP asset smoke failed to stop its bounded local server cleanly.')
        print(f'HTTP asset smoke passed for {len(PATHS)} web resources.')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
