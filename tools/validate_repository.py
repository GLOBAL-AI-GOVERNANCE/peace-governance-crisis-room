#!/usr/bin/env python3
"""Validate public source readiness without claiming runtime execution."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.2.2"

REQUIRED_FILES = (
    "README.md",
    "VERSION",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "DOCTRINE.md",
    "CHANGELOG.md",
    "RELEASE_NOTES.md",
    "MANIFEST.json",
    "SHA256SUMS.txt",
    "game/project.godot",
    "game/export_presets.cfg",
    "tests/validate_scenario_json.py",
    "tests/validate_release_language.py",
    "tools/generate_manifest.py",
    "tools/validate_repository.py",
    "docs/provenance/source-framework-notes.md",
    "docs/release-evidence/source-readiness-v0.2.2.md",
)

FORBIDDEN_ROOT = (
    "FINAL_REPO_VERIFICATION_REPORT.md",
    "GITHUB_RELEASE_DESCRIPTION_v0.2.1_SOURCE.md",
    "GIT_PUSH_COMMANDS.md",
    "PATCH_NOTES.md",
    "PRE_PUBLISH_CHECKLIST.md",
    "PUBLISH_REPO_NOW.md",
    "REPO_TOPICS.md",
)

FORBIDDEN_BINARY_SUFFIXES = {
    ".exe",
    ".dll",
    ".pck",
    ".msi",
    ".zip",
    ".7z",
    ".rar",
}

REQUIRED_README_HEADINGS = (
    "# Peace Governance Crisis Room",
    "## Start Here",
    "## Finished Outcome",
    "## Doctrine",
    "## Included Source",
    "## Scenarios",
    "## Core Gameplay Loop",
    "## Evidence and Safety Boundary",
    "## Runtime and Windows Release Gate",
    "## Repository Map",
    "## Security",
    "## Contributing",
    "## License",
)

REQUIRED_README_PHRASES = (
    "Source-ready educational prototype",
    "Windows executable:** Not included",
    "Godot execution, Windows export, and external-PC testing",
    "not an operating system",
    "AI may advise. AI may not decide.",
    "No live AI, live data, real incident ingestion",
    "does not establish runtime correctness",
)

MARKDOWN_LINK = re.compile(
    r"!?\[[^\]]*\]\((?P<destination>[^)\n]+)\)"
)
FENCED_CODE = re.compile(
    r"```.*?```|~~~.*?~~~",
    re.DOTALL,
)


def fail(message: str) -> None:
    raise SystemExit(
        f"Source-readiness validation failed: {message}"
    )


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

        target = ROOT / raw.decode("utf-8")

        if target.is_file():
            paths.append(target)

    return paths


def validate_required_files() -> None:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            fail(f"required file is missing: {relative}")

    for relative in FORBIDDEN_ROOT:
        if (ROOT / relative).exists():
            fail(f"obsolete root file remains: {relative}")

    if (ROOT / "ai-governance-peace-os").exists():
        fail("legacy nested source-note directory remains")


def validate_readme() -> None:
    text = (
        ROOT / "README.md"
    ).read_text(encoding="utf-8-sig")

    headings = [
        line.strip()
        for line in text.splitlines()
        if line.lstrip().startswith("#")
    ]

    for heading in REQUIRED_README_HEADINGS:
        if headings.count(heading) != 1:
            fail(
                "README heading must appear exactly once: "
                f"{heading}"
            )

    for phrase in REQUIRED_README_PHRASES:
        if phrase not in text:
            fail(f"README boundary is missing: {phrase}")

    if f"`v{VERSION}`" not in text:
        fail("README version is not current")


def extract_destination(raw: str) -> str:
    value = raw.strip()

    if value.startswith("<") and ">" in value:
        return value[1:value.index(">")].strip()

    return (
        value.split()[0].strip()
        if value
        else ""
    )


def validate_links(files: list[Path]) -> None:
    for path in files:
        if path.suffix.lower() != ".md":
            continue

        text = path.read_text(encoding="utf-8-sig")
        text = FENCED_CODE.sub("", text)

        for match in MARKDOWN_LINK.finditer(text):
            destination = extract_destination(
                match.group("destination")
            )
            lower = destination.lower()

            if (
                not destination
                or destination.startswith("#")
                or lower.startswith(
                    (
                        "http://",
                        "https://",
                        "mailto:",
                        "tel:",
                        "data:",
                    )
                )
            ):
                continue

            path_part = unquote(
                urlsplit(destination).path
            )

            if not path_part:
                continue

            target = (
                ROOT / path_part.lstrip("/")
                if path_part.startswith("/")
                else path.parent / path_part
            )

            if not target.exists():
                fail(
                    "broken local Markdown link in "
                    f"{path.relative_to(ROOT)}: "
                    f"{destination}"
                )


def validate_json(files: list[Path]) -> None:
    for path in files:
        if path.suffix.lower() != ".json":
            continue

        try:
            json.loads(
                path.read_text(encoding="utf-8-sig")
            )
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
        ) as exc:
            fail(
                "invalid JSON in "
                f"{path.relative_to(ROOT)}: {exc}"
            )


def validate_no_packaged_build(
    files: list[Path],
) -> None:
    offenders = [
        path.relative_to(ROOT).as_posix()
        for path in files
        if (
            path.suffix.lower()
            in FORBIDDEN_BINARY_SUFFIXES
        )
    ]

    if offenders:
        fail(
            "unverified packaged or executable "
            f"artifacts are committed: {offenders}"
        )


def validate_workflow() -> None:
    workflow = (
        ROOT
        / ".github"
        / "workflows"
        / "source-checks.yml"
    )

    if not workflow.is_file():
        fail("hosted source-check workflow is missing")

    text = workflow.read_text(encoding="utf-8")

    uses = re.findall(
        r"^\s*uses:\s*([^\s#]+)",
        text,
        re.MULTILINE,
    )

    external = [
        item
        for item in uses
        if not item.startswith(("./", "docker://"))
    ]

    if len(external) != 1:
        fail(
            "expected one external workflow action, "
            f"found {len(external)}"
        )

    if not re.search(r"@[0-9a-f]{40}$", external[0]):
        fail(
            "workflow action is not pinned "
            "to a full SHA"
        )

    if "permissions:\n  contents: read" not in text:
        fail("workflow permissions are not read-only")


def validate_version() -> None:
    version = (
        ROOT / "VERSION"
    ).read_text(
        encoding="utf-8"
    ).strip()

    if version != VERSION:
        fail(
            f"VERSION is {version!r}, "
            f"expected {VERSION!r}"
        )


def run_command(*args: str) -> None:
    completed = subprocess.run(
        list(args),
        cwd=ROOT,
        text=True,
    )

    if completed.returncode != 0:
        fail(
            "command failed: "
            + " ".join(args)
        )


def validate_hygiene(files: list[Path]) -> None:
    for path in files:
        relative = path.relative_to(ROOT)

        if "__pycache__" in relative.parts:
            fail(
                "Python cache directory is present: "
                f"{relative}"
            )

        if path.suffix.lower() in {".pyc", ".pyo"}:
            fail(
                f"Python bytecode is present: {relative}"
            )

        if path.is_file():
            try:
                text = path.read_text(
                    encoding="utf-8-sig"
                )
            except (UnicodeError, OSError):
                continue

            for number, line in enumerate(
                text.splitlines(),
                start=1,
            ):
                if line.rstrip(" \t") != line:
                    fail(
                        "trailing whitespace in "
                        f"{relative}:{number}"
                    )


def main() -> None:
    files = repository_files()

    validate_required_files()
    validate_version()
    validate_readme()
    validate_json(files)
    validate_links(files)
    validate_no_packaged_build(files)
    validate_workflow()
    validate_hygiene(files)

    run_command(
        sys.executable,
        "tools/generate_manifest.py",
        "--check",
    )

    print(
        "Source-readiness validation passed: "
        f"{len(files)} repository files checked; "
        "boundaries, JSON, links, workflow pins, "
        "artifact scope, manifest, and hygiene verified."
    )


if __name__ == "__main__":
    main()
