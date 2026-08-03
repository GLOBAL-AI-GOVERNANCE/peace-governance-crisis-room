#!/usr/bin/env python3
"""Scan working, staged, archive, and optional Git-history publication surfaces."""
from __future__ import annotations
import argparse, re, subprocess, zipfile
from pathlib import Path

SECRET_PATTERNS = {
    'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'github_token': re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b'),
    'github_pat': re.compile(r'\bgithub_pat_[A-Za-z0-9_]{50,}\b'),
    'aws_access_key': re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
    'slack_token': re.compile(r'\bxox[baprs]-[A-Za-z0-9-]{10,}\b'),
}
PUBLIC_PATTERNS = {
    'email_address': re.compile(r'(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])'),
    'us_ssn': re.compile(r'(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)'),
    'unix_home_path': re.compile(r'(?<![\w])/(?:home|Users)/[A-Za-z0-9._-]+/'),
    'windows_user_path': re.compile(r'(?i)\b[A-Z]:\\Users\\[^\\\r\n]+\\'),
    'composer_export_name': re.compile(r'(?i)\bPasted (?:text|markdown)(?: \(\d+\))*\b'),
}
TEXT_SUFFIXES = {'.md', '.txt', '.py', '.gd', '.json', '.yml', '.yaml', '.cfg', '.godot', '.tscn', '.svg', '.sh', '.toml', '.cff', '.csv', '.html', '.css', '.js', '.mjs', '.webmanifest'}
FORBIDDEN_SUFFIXES = {'.zip', '.7z', '.rar', '.ots', '.exe', '.pck', '.dll'}
EXCLUDED_PARTS = {'.git', '__pycache__', '.pytest_cache', '.godot'}


def excluded(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    return any(part in EXCLUDED_PARTS or part == 'dist' or part.startswith('dist-') or part.startswith('peace-os-integration-review-') for part in rel.parts)


def scan_text(label: str, text: str, patterns: dict[str, re.Pattern[str]], findings: list[str]) -> None:
    for name, pattern in patterns.items():
        for match in pattern.finditer(text):
            line = text.count('\n', 0, match.start()) + 1
            findings.append(f'{label}:{line}:{name}')


def scan_file(path: Path, label: str, findings: list[str]) -> None:
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        findings.append(f'{label}:forbidden-artifact')
        return
    if path.suffix.lower() in TEXT_SUFFIXES or path.name in {'VERSION', 'LICENSE', '.gitignore'}:
        text = path.read_text(encoding='utf-8', errors='ignore')
        scan_text(label, text, SECRET_PATTERNS, findings)
        if path.name not in {'secret_scan.py', 'pii_scan.py', 'scan_publication_surface.py'}:
            scan_text(label, text, PUBLIC_PATTERNS, findings)


def staged_paths(root: Path) -> list[tuple[str, str]]:
    result = subprocess.run(['git', 'diff', '--cached', '--name-status', '-z'], cwd=root, check=True, capture_output=True)
    fields = result.stdout.decode('utf-8', errors='surrogateescape').split('\0')
    rows=[]; index=0
    while index < len(fields) and fields[index]:
        status=fields[index]; index += 1
        path=fields[index]; index += 1
        if status.startswith(('R', 'C')):
            path=fields[index]; index += 1
        rows.append((status, path))
    return rows


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source-root', type=Path)
    parser.add_argument('--staged', action='store_true')
    parser.add_argument('--archive', type=Path, action='append', default=[])
    parser.add_argument('--history-report', type=Path)
    args=parser.parse_args()
    root=args.root.resolve(); findings=[]
    for path in sorted(root.rglob('*')):
        if path.is_file() and not excluded(path, root):
            scan_file(path, path.relative_to(root).as_posix(), findings)
    if args.staged:
        source=(args.source_root or root).resolve()
        for status, rel_text in staged_paths(root):
            rel=Path(rel_text)
            if any(part == 'dist' or part.startswith('dist-') for part in rel.parts):
                findings.append(f'{rel_text}:generated-path-staged')
            if status[0] != 'D' and not (source / rel).is_file():
                findings.append(f'{rel_text}:staged-path-not-in-reviewed-source')
    for archive in args.archive:
        with zipfile.ZipFile(archive) as bundle:
            for info in bundle.infolist():
                rel=Path(info.filename)
                if info.is_dir():
                    continue
                if rel.suffix.lower() in FORBIDDEN_SUFFIXES:
                    findings.append(f'{archive.name}:{info.filename}:nested-forbidden-artifact')
                if rel.suffix.lower() in TEXT_SUFFIXES or rel.name in {'VERSION', 'LICENSE', '.gitignore'}:
                    text=bundle.read(info).decode('utf-8', errors='ignore')
                    scan_text(f'{archive.name}:{info.filename}', text, SECRET_PATTERNS, findings)
                    scan_text(f'{archive.name}:{info.filename}', text, PUBLIC_PATTERNS, findings)
    if args.history_report:
        history=subprocess.run(['git','log','--all','-p','--no-ext-diff','--'], cwd=root, capture_output=True, text=True, errors='ignore')
        historical=[]
        scan_text('git-history', history.stdout, SECRET_PATTERNS, historical)
        args.history_report.parent.mkdir(parents=True, exist_ok=True)
        args.history_report.write_text(('\n'.join(historical) + '\n') if historical else 'PASS: no high-confidence secret pattern found in reachable Git history.\n', encoding='utf-8')
        findings.extend(historical)
    if findings:
        raise SystemExit('Publication-surface scan failed:\n' + '\n'.join(sorted(set(findings))))
    print('Publication-surface scan passed.')

if __name__ == '__main__':
    main()
