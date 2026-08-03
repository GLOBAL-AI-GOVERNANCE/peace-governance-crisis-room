#!/usr/bin/env python3
"""Run the complete bounded source validation suite."""
from __future__ import annotations
import os, shutil, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
COMMANDS=[
    [sys.executable,'tests/validate_governance_policy.py'],
    [sys.executable,'tests/validate_scenario_json.py'],
    [sys.executable,'tests/validate_release_language.py'],
    [sys.executable,'tests/validate_gdscript_contract.py'],
    [sys.executable,'tools/check_core_parity.py'],
    ['node','--test','tests/js/scoring.test.mjs','tests/js/golden-parity.test.mjs'],
    ['node','tests/js/web-static-check.mjs'],
    [sys.executable,'tests/http_asset_smoke.py'],
    [sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py','-v'],
    [sys.executable,'tools/check_naming.py'],
    [sys.executable,'tools/check_public_private_boundary.py'],
    [sys.executable,'tools/validate_citation.py'],
    [sys.executable,'tools/scan_publication_surface.py'],
    [sys.executable,'tools/secret_scan.py'],
    [sys.executable,'tools/pii_scan.py'],
    [sys.executable,'tools/validate_links.py'],
    [sys.executable,'tools/check_workflows.py'],
]

def remove_python_cache() -> None:
    """Remove generated reviewer/test bytecode without changing controlled source."""
    for cache_dir in ROOT.rglob('__pycache__'):
        if '.git' not in cache_dir.parts and 'dist' not in cache_dir.parts:
            shutil.rmtree(cache_dir, ignore_errors=True)
    for pattern in ('*.pyc', '*.pyo'):
        for bytecode in ROOT.rglob(pattern):
            if '.git' not in bytecode.parts and 'dist' not in bytecode.parts:
                bytecode.unlink(missing_ok=True)


def main():
    remove_python_cache()
    env=dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE']='1'
    for command in COMMANDS:
        print('WORKING:', ' '.join(command), flush=True)
        result=subprocess.run(command,cwd=ROOT,env=env)
        if result.returncode:
            print('STOP: validation failed', flush=True)
            raise SystemExit(result.returncode)
    remove_python_cache()
    forbidden=[]
    for suffix in ('*.exe','*.pck','*.dll'):
        forbidden.extend(p.relative_to(ROOT).as_posix() for p in ROOT.rglob(suffix) if '.git' not in p.parts and 'dist' not in p.parts)
    if forbidden:
        raise SystemExit('Binary artifacts forbidden in the bounded source tree: '+', '.join(sorted(forbidden)))
    print('PASS: bounded source validation complete. Godot runtime remains unverified.')

if __name__=='__main__':
    main()
