#!/usr/bin/env python3
"""Generate or verify the deterministic source manifest."""

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


def repository_files() -> list[Path]:
    completed = subprocess.run(
        [
            "git",
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )

    paths = []

    for raw in completed.stdout.split(b"\0"):
        if not raw:
            continue

        relative = Path(raw.decode("utf-8"))
        normalized = relative.as_posix()

        if normalized in EXCLUDED:
            continue

        if "__pycache__" in relative.parts:
            continue

        if relative.suffix.lower() in {".pyc", ".pyo"}:
            continue

        target = ROOT / relative

        if target.is_file():
            paths.append(relative)

    return sorted(
        paths,
        key=lambda item: item.as_posix(),
    )


def digest(path: Path) -> str:
    hasher = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            hasher.update(block)

    return hasher.hexdigest()


def expected_content() -> tuple[str, str]:
    entries = []

    for relative in repository_files():
        target = ROOT / relative
        entries.append(
            {
                "path": relative.as_posix(),
                "sha256": digest(target),
                "size_bytes": target.stat().st_size,
            }
        )

    manifest = {
        "name": "peace-governance-crisis-room",
        "version": "0.2.2",
        "release_scope": "public-source-readiness",
        "integrity_scope": (
            "All repository files except MANIFEST.json and "
            "SHA256SUMS.txt; both integrity files are excluded "
            "to avoid cyclic hashing."
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
            "Verify integrity files instead of writing them."
        ),
    )
    args = parser.parse_args()

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
                "MANIFEST.json is stale. Run "
                "`python tools/generate_manifest.py`."
            )

        if (
            sums_path.read_text(encoding="utf-8")
            != sums_text
        ):
            raise SystemExit(
                "SHA256SUMS.txt is stale. Run "
                "`python tools/generate_manifest.py`."
            )

        print(
            "Manifest and SHA-256 inventory "
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
        "Manifest and SHA-256 inventory generated."
    )


if __name__ == "__main__":
    main()
