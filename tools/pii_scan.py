#!/usr/bin/env python3
"""Conservative public-release scan for direct contact data and local-path leakage.

This does not prove that a repository contains no personal information. It
catches high-confidence patterns that should not appear in this bounded public
source release.
"""
from __future__ import annotations

import re
from generate_manifest import ROOT, controlled_files

PATTERNS = {
    "email_address": re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])"),
    "us_phone_number": re.compile(
        r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?!\d)"
    ),
    "us_ssn": re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)"),
    "unix_home_path": re.compile(r"(?<![\w])/(?:home|Users)/[A-Za-z0-9._-]+/"),
    "windows_user_path": re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\r\n]+\\"),
    "composer_export_name": re.compile(r"(?i)\bPasted (?:text|markdown)(?: \(\d+\))*\b"),
}
TEXT_SUFFIXES = {
    ".md", ".txt", ".py", ".gd", ".json", ".yml", ".yaml", ".cfg",
    ".godot", ".tscn", ".svg", ".sh", ".toml", ".cff", ".csv"
}

findings: list[str] = []
for rel in controlled_files():
    if rel.as_posix() == "tools/pii_scan.py":
        continue
    if rel.suffix.lower() not in TEXT_SUFFIXES and rel.name not in {"VERSION", "LICENSE"}:
        continue
    text = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
    for name, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(f"{rel.as_posix()}:{line}:{name}")

if findings:
    raise SystemExit("Potential public-release personal/local data found:\n" + "\n".join(findings))
print("Public-release personal/local data scan passed.")
