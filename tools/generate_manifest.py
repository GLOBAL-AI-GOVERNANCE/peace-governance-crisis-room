#!/usr/bin/env python3
"""Generate or verify a deterministic manifest from Git index blobs."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {
    "MANIFEST.json",
    "SHA256SUMS.txt",
}


def run_git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )


def ensure_index_is_release_ready() -> None:
    unstaged = run_git("diff", "--name-only", "-z").stdout
    untracked = run_git(
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
    ).stdout

    ignored = {
        b"MANIFEST.json",
        b"SHA256SUMS.txt",
    }

    unstaged_paths = {
        item
        for item in unstaged.split(b"\0")
        if item and item not in ignored
    }
    untracked_paths = {
        item
        for item in untracked.split(b"\0")
        if item and item not in ignored
    }

    if unstaged_paths:
        decoded = sorted(
            item.decode("utf-8")
            for item in unstaged_paths
        )
        raise SystemExit(
            "Unstaged source changes exist. Stage them before "
            f"generating the manifest: {decoded}"
        )

    if untracked_paths:
        decoded = sorted(
            item.decode("utf-8")
            for item in untracked_paths
        )
        raise SystemExit(
            "Untracked source files exist. Stage or remove them "
            f"before generating the manifest: {decoded}"
        )


def index_entries() -> list[dict[str, object]]:
    completed = run_git("ls-files", "-s", "-z")
    entries: list[dict[str, object]] = []

    for raw in completed.stdout.split(b"\0"):
        if not raw:
            continue

        decoded = raw.decode("utf-8")
        metadata, raw_path = decoded.split("\t", 1)
        _mode, blob_sha, stage = metadata.split(" ", 2)

        if stage != "0":
            raise SystemExit(
                "Unmerged index entry detected for "
                f"{raw_path!r}."
            )

        relative = Path(raw_path)
        normalized = relative.as_posix()

        if normalized in EXCLUDED:
            continue

        if "__pycache__" in relative.parts:
            continue

        if relative.suffix.lower() in {".pyc", ".pyo"}:
            continue

        blob = run_git(
            "cat-file",
            "blob",
            blob_sha,
        ).stdout

        entries.append(
            {
                "path": normalized,
                "sha256": hashlib.sha256(blob).hexdigest(),
                "size_bytes": len(blob),
            }
        )

    return sorted(
        entries,
        key=lambda item: str(item["path"]),
    )


def expected_content() -> tuple[str, str]:
    entries = index_entries()

    manifest = {
        "name": "peace-governance-crisis-room",
        "version": "0.2.2",
        "release_scope": "public-source-readiness",
        "integrity_scope": (
            "All stage-0 Git index blobs except MANIFEST.json "
            "and SHA256SUMS.txt. Hashing index blobs makes the "
            "inventory independent of local checkout line endings."
        ),
        "file_count": len(entries),
        "files": entries,
    }

    manifest_text = (
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    sums_text = "".join(
        f"{entry['sha256']}  {entry['path']}\n"
        for entry in entries
    )

    return manifest_text, sums_text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Verify integrity files against Git index blobs "
            "instead of writing them."
        ),
    )
    args = parser.parse_args()

    ensure_index_is_release_ready()
    manifest_text, sums_text = expected_content()

    manifest_path = ROOT / "MANIFEST.json"
    sums_path = ROOT / "SHA256SUMS.txt"

    if args.check:
        if not manifest_path.is_file():
            raise SystemExit("MANIFEST.json is missing.")

        if not sums_path.is_file():
            raise SystemExit("SHA256SUMS.txt is missing.")

        if (
            manifest_path.read_text(encoding="utf-8")
            != manifest_text
        ):
            raise SystemExit(
                "MANIFEST.json is stale relative to the "
                "Git index. Stage source changes, then run "
                "`python tools/generate_manifest.py`."
            )

        if (
            sums_path.read_text(encoding="utf-8")
            != sums_text
        ):
            raise SystemExit(
                "SHA256SUMS.txt is stale relative to the "
                "Git index. Stage source changes, then run "
                "`python tools/generate_manifest.py`."
            )

        print(
            "Git-index manifest and SHA-256 inventory "
            "verification passed."
        )
        return

    manifest_path.write_text(
        manifest_text,
        encoding="utf-8",
        newline="\n",
    )
    sums_path.write_text(
        sums_text,
        encoding="utf-8",
        newline="\n",
    )

    print(
        "Git-index manifest and SHA-256 inventory generated."
    )


if __name__ == "__main__":
    main()
