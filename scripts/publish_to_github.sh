#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
REPO="GLOBAL-AI-GOVERNANCE/peace-os-crisis-room"
BRANCH="feat/web-app-integration"
PUSH=0
[[ "${1:-}" == "--push" ]] && PUSH=1
[[ $# -le 1 ]] || { echo 'STOP: usage: scripts/publish_to_github.sh [--push]'; exit 2; }

: "${EXPECTED_BASE_COMMIT:?Set EXPECTED_BASE_COMMIT to the full, human-reviewed current main SHA}"
[[ "$EXPECTED_BASE_COMMIT" =~ ^[0-9a-fA-F]{40}$ ]] || {
  echo 'STOP: EXPECTED_BASE_COMMIT must be a full 40-character Git SHA.'
  exit 1
}

: "${EXPECTED_SOURCE_ZIP_SHA256:=}"
: "${EXPECTED_PATCH_SHA256:=}"
: "${EXPECTED_GITHUB_LOGIN:=}"
: "${REVIEWED_WORKSPACE:=}"

for command in gh git node; do
  command -v "$command" >/dev/null || { echo "STOP: $command is required"; exit 1; }
done
PYTHON="$(command -v python3 || command -v python || true)"
[[ -n "$PYTHON" ]] || { echo 'STOP: Python 3.9 or newer is required.'; exit 1; }
"$PYTHON" - <<'PY'
import sys
if sys.version_info < (3, 9):
    raise SystemExit('STOP: Python 3.9 or newer is required.')
PY

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEFAULT_REVIEW_PARENT="$(cd -- "$SOURCE_ROOT/.." && pwd)"
REVIEW_ROOT="${PUBLISH_REVIEW_DIR:-$DEFAULT_REVIEW_PARENT/peace-os-integration-review-$STAMP}"
mkdir -p "$REVIEW_ROOT"

if [[ "${KEEP_WORKDIR:-NO}" == "YES" ]]; then
  WORK="$REVIEW_ROOT/work"
  rm -rf "$WORK"
  mkdir -p "$WORK"
  CLEANUP_WORK=0
else
  WORK="$(mktemp -d)"
  CLEANUP_WORK=1
fi

cleanup() {
  if [[ "$CLEANUP_WORK" -eq 1 ]]; then
    rm -rf "$WORK"
  else
    echo "PASS: retained review workspace at $WORK"
  fi
}
trap cleanup EXIT

ACCOUNT="$(gh api user --jq .login)"
NAME="$(gh repo view "$REPO" --json nameWithOwner --jq .nameWithOwner)"
DEFAULT="$(gh repo view "$REPO" --json defaultBranchRef --jq .defaultBranchRef.name)"
PERMISSION="$(gh repo view "$REPO" --json viewerPermission --jq .viewerPermission)"
printf 'WORKING: GitHub account=%s repository=%s permission=%s\n' "$ACCOUNT" "$NAME" "$PERMISSION"
[[ "$NAME" == "$REPO" ]] || { echo "STOP: exact repository identity mismatch: $NAME"; exit 1; }
[[ "$DEFAULT" == "main" ]] || { echo "STOP: default branch is $DEFAULT"; exit 1; }
[[ "$PERMISSION" =~ ^(ADMIN|MAINTAIN|WRITE)$ ]] || { echo "STOP: insufficient repository permission: $PERMISSION"; exit 1; }

if [[ -n "$EXPECTED_GITHUB_LOGIN" ]]; then
  [[ "$ACCOUNT" == "$EXPECTED_GITHUB_LOGIN" ]] || {
    echo "STOP: expected GitHub login $EXPECTED_GITHUB_LOGIN but authenticated as $ACCOUNT"
    exit 1
  }
fi

if [[ "$PUSH" -eq 1 ]]; then
  [[ -n "$EXPECTED_GITHUB_LOGIN" ]] || { echo 'STOP: --push requires EXPECTED_GITHUB_LOGIN.'; exit 1; }
  [[ -n "$EXPECTED_SOURCE_ZIP_SHA256" ]] || { echo 'STOP: --push requires EXPECTED_SOURCE_ZIP_SHA256.'; exit 1; }
  [[ -n "$EXPECTED_PATCH_SHA256" ]] || { echo 'STOP: --push requires EXPECTED_PATCH_SHA256 from the reviewed dry run.'; exit 1; }
fi

if [[ -n "$EXPECTED_SOURCE_ZIP_SHA256" ]]; then
  SOURCE_ZIP_CANDIDATE="${SOURCE_ZIP_PATH:-}"
  if [[ -z "$SOURCE_ZIP_CANDIDATE" ]]; then
    for candidate in \
      "$SOURCE_ROOT/../peace-os-crisis-room-v0.3.0-rc1-source.zip" \
      "$SOURCE_ROOT/../../SOURCE/peace-os-crisis-room-v0.3.0-rc1-source.zip"; do
      if [[ -f "$candidate" ]]; then
        SOURCE_ZIP_CANDIDATE="$candidate"
        break
      fi
    done
  fi
  [[ -n "$SOURCE_ZIP_CANDIDATE" && -f "$SOURCE_ZIP_CANDIDATE" ]] || {
    echo 'STOP: EXPECTED_SOURCE_ZIP_SHA256 set but SOURCE_ZIP_PATH / adjacent source ZIP not found.'
    exit 1
  }
  ACTUAL_SOURCE_HASH="$("$PYTHON" -c "import hashlib,sys; h=hashlib.sha256(); f=open(sys.argv[1],'rb');
import itertools
[h.update(c) for c in iter(lambda:f.read(1048576), b'')]; f.close(); print(h.hexdigest())" "$SOURCE_ZIP_CANDIDATE")"
  [[ "$ACTUAL_SOURCE_HASH" == "$EXPECTED_SOURCE_ZIP_SHA256" ]] || {
    echo "STOP: source ZIP SHA mismatch. expected=$EXPECTED_SOURCE_ZIP_SHA256 actual=$ACTUAL_SOURCE_HASH"
    exit 1
  }
  echo "PASS: source ZIP SHA matches expected binding."
fi

# Preferred: push the exact reviewed workspace commit (no second overlay generation).
if [[ "$PUSH" -eq 1 && -n "$REVIEWED_WORKSPACE" ]]; then
  [[ -d "$REVIEWED_WORKSPACE/.git" ]] || { echo "STOP: REVIEWED_WORKSPACE is not a git repository: $REVIEWED_WORKSPACE"; exit 1; }
  cd "$REVIEWED_WORKSPACE"
  CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
  [[ "$CURRENT_BRANCH" == "$BRANCH" ]] || { echo "STOP: reviewed workspace branch is $CURRENT_BRANCH, expected $BRANCH"; exit 1; }
  [[ -z "$(git status --porcelain)" ]] || { echo 'STOP: reviewed workspace is not clean.'; exit 1; }
  PARENT_COMMIT="$(git rev-parse HEAD^)"
  [[ "$PARENT_COMMIT" == "$EXPECTED_BASE_COMMIT" ]] || {
    echo "STOP: reviewed commit parent $PARENT_COMMIT does not match EXPECTED_BASE_COMMIT=$EXPECTED_BASE_COMMIT"
    exit 1
  }
  if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
    echo "STOP: remote review branch already exists: $BRANCH"
    exit 1
  fi
  if [[ -n "${PUBLISH_REVIEW_DIR:-}" && -f "${PUBLISH_REVIEW_DIR}/integration-review.patch" ]]; then
    REVIEW_ROOT="$PUBLISH_REVIEW_DIR"
  fi
  [[ -f "$REVIEW_ROOT/integration-review.patch" ]] || {
    echo 'STOP: integration-review.patch is missing from the bound review root.'
    exit 1
  }
  RECORDED_PATCH_HASH="$("$PYTHON" -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$REVIEW_ROOT/integration-review.patch")"
  [[ "$RECORDED_PATCH_HASH" == "$EXPECTED_PATCH_SHA256" ]] || {
    echo "STOP: recorded patch SHA mismatch. expected=$EXPECTED_PATCH_SHA256 actual=$RECORDED_PATCH_HASH"
    exit 1
  }
  PUSH_PATCH="$REVIEW_ROOT/push-verification.patch"
  git diff --binary "$EXPECTED_BASE_COMMIT" HEAD > "$PUSH_PATCH"
  PUSH_PATCH_HASH="$("$PYTHON" -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$PUSH_PATCH")"
  [[ "$PUSH_PATCH_HASH" == "$EXPECTED_PATCH_SHA256" ]] || {
    echo "STOP: reviewed workspace commit does not reproduce the approved patch. expected=$EXPECTED_PATCH_SHA256 actual=$PUSH_PATCH_HASH"
    exit 1
  }
  if [[ -f "$REVIEW_ROOT/local-review-commit.txt" ]]; then
    RECORDED_COMMIT="$(tr -d '\r\n' < "$REVIEW_ROOT/local-review-commit.txt")"
    [[ "$(git rev-parse HEAD)" == "$RECORDED_COMMIT" ]] || {
      echo "STOP: reviewed workspace HEAD differs from recorded local review commit $RECORDED_COMMIT"
      exit 1
    }
  fi
  [[ "${ACKNOWLEDGE_REVIEW:-}" == "YES" ]] || {
    echo 'STOP: set ACKNOWLEDGE_REVIEW=YES after reviewing the persistent patch and reports.'
    exit 1
  }
  if [[ -f "$REVIEW_ROOT/deletions-reviewed.txt" && -s "$REVIEW_ROOT/deletions-reviewed.txt" && "${ACKNOWLEDGE_DELETIONS:-}" != "YES" ]]; then
    echo 'STOP: set ACKNOWLEDGE_DELETIONS=YES after reviewing the deletion report before pushing.'
    exit 1
  fi
  git push -u origin "$BRANCH"
  echo "PASS: pushed exact reviewed branch $BRANCH from REVIEWED_WORKSPACE"
  exit 0
fi

gh repo clone "$REPO" "$WORK/repo" -- --depth=1 --branch main
cd "$WORK/repo"
ACTUAL="$(git rev-parse HEAD)"
[[ "$ACTUAL" == "$EXPECTED_BASE_COMMIT" ]] || {
  echo "STOP: reviewed base $EXPECTED_BASE_COMMIT differs from live $ACTUAL"
  exit 1
}
[[ -z "$(git status --porcelain)" ]] || { echo 'STOP: live main clone is not clean'; exit 1; }

if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
  echo "STOP: remote review branch already exists: $BRANCH"
  exit 1
fi
git switch -c "$BRANCH"

DELETION_REPORT="$REVIEW_ROOT/deletions.txt"
OVERLAY_PLAN="$REVIEW_ROOT/overlay-plan.txt"
"$PYTHON" "$SOURCE_ROOT/tools/prepare_integration_overlay.py" \
  --source "$SOURCE_ROOT" \
  --target "$PWD" \
  --plan "$OVERLAY_PLAN" \
  --deletions "$DELETION_REPORT"

if [[ -s "$DELETION_REPORT" ]]; then
  echo 'WORKING: the reviewed overlay removes these live-only files:'
  cat "$DELETION_REPORT"
else
  echo 'PASS: dry-run overlay reports no live-only file deletions.'
fi

"$PYTHON" "$SOURCE_ROOT/tools/prepare_integration_overlay.py" \
  --source "$SOURCE_ROOT" \
  --target "$PWD" \
  --plan "$OVERLAY_PLAN" \
  --deletions "$DELETION_REPORT" \
  --apply
find . -type d -name __pycache__ -prune -exec rm -rf {} +
find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

"$PYTHON" tools/generate_manifest.py
"$PYTHON" tools/validate_repository.py
"$PYTHON" tools/generate_manifest.py --check
"$PYTHON" tools/run_extended_vv.py \
  --output "$REVIEW_ROOT/extended-vv-results-v0.3.0-rc1.json"
node --test tests/js/*.test.mjs
echo 'HOLD: browser runtime is not a branch-upload gate; complete deployed Pages UAT after merge.'

git add -A
git diff --cached --check
if git diff --cached --quiet; then
  echo 'STOP: overlay produced no staged changes.'
  exit 1
fi

while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  if [[ ! -f "$SOURCE_ROOT/$path" ]]; then
    echo "STOP: staged path is not in the reviewed source allowlist: $path"
    exit 1
  fi
done < <(git diff --cached --name-only --diff-filter=ACMR)

if git diff --cached --name-only | grep -Eq '(^|/)dist(?:-|/|$)'; then
  echo 'STOP: generated dist output is staged.'
  exit 1
fi

"$PYTHON" tools/scan_publication_surface.py \
  --root "$PWD" \
  --source-root "$SOURCE_ROOT" \
  --staged \
  --history-report "$REVIEW_ROOT/git-history-secret-scan.txt"

git status --short > "$REVIEW_ROOT/git-status-short.txt"
git diff --cached --stat > "$REVIEW_ROOT/integration-review.stat.txt"
git diff --cached --name-status > "$REVIEW_ROOT/integration-review.name-status.txt"
git diff --cached --binary > "$REVIEW_ROOT/integration-review.patch"
cp "$DELETION_REPORT" "$REVIEW_ROOT/deletions-reviewed.txt"

PATCH_SHA="$("$PYTHON" -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$REVIEW_ROOT/integration-review.patch")"
printf '%s\n' "$PATCH_SHA" > "$REVIEW_ROOT/integration-review.patch.sha256"
printf 'PASS: integration-review.patch SHA-256=%s\n' "$PATCH_SHA"

if [[ -n "$EXPECTED_PATCH_SHA256" ]]; then
  [[ "$PATCH_SHA" == "$EXPECTED_PATCH_SHA256" ]] || {
    echo "STOP: produced patch SHA $PATCH_SHA does not match EXPECTED_PATCH_SHA256=$EXPECTED_PATCH_SHA256"
    exit 1
  }
  echo 'PASS: produced patch matches EXPECTED_PATCH_SHA256 binding.'
fi

printf '\nWORKING: staged change summary\n'
cat "$REVIEW_ROOT/integration-review.stat.txt"
printf '\nWORKING: staged name/status report\n'
cat "$REVIEW_ROOT/integration-review.name-status.txt"

git commit -m "feat: integrate Peace OS web review candidate v0.3.0-rc1"
LOCAL_COMMIT="$(git rev-parse HEAD)"
printf '%s\n' "$LOCAL_COMMIT" > "$REVIEW_ROOT/local-review-commit.txt"
printf 'PASS: local review branch prepared at %s\n' "$LOCAL_COMMIT"
printf 'PASS: persistent review evidence written to %s\n' "$REVIEW_ROOT"
printf 'PASS: set REVIEWED_WORKSPACE=%s for exact-commit push\n' "$PWD"
printf 'PASS: set EXPECTED_PATCH_SHA256=%s for push binding\n' "$PATCH_SHA"

if [[ "$PUSH" -eq 1 ]]; then
  [[ "${ACKNOWLEDGE_REVIEW:-}" == "YES" ]] || {
    echo 'STOP: set ACKNOWLEDGE_REVIEW=YES after reviewing the persistent patch and reports.'
    exit 1
  }
  if [[ -s "$DELETION_REPORT" && "${ACKNOWLEDGE_DELETIONS:-}" != "YES" ]]; then
    echo 'STOP: set ACKNOWLEDGE_DELETIONS=YES after reviewing the deletion report before pushing.'
    exit 1
  fi
  if [[ -z "$EXPECTED_PATCH_SHA256" ]]; then
    echo 'STOP: --push requires EXPECTED_PATCH_SHA256 from the reviewed dry-run, or REVIEWED_WORKSPACE for exact push.'
    echo "Recorded patch SHA for this run: $PATCH_SHA"
    exit 1
  fi
  git push -u origin "$BRANCH"
  echo "PASS: pushed review branch $BRANCH"
else
  echo 'DRY RUN: branch was not pushed. Review integration-review.patch and deletion reports before --push.'
  echo "Next: EXPECTED_BASE_COMMIT=$EXPECTED_BASE_COMMIT EXPECTED_SOURCE_ZIP_SHA256=<SOURCE_ZIP_SHA> EXPECTED_PATCH_SHA256=$PATCH_SHA EXPECTED_GITHUB_LOGIN=$ACCOUNT REVIEWED_WORKSPACE=$PWD PUBLISH_REVIEW_DIR=$REVIEW_ROOT ACKNOWLEDGE_REVIEW=YES scripts/publish_to_github.sh --push"
fi
