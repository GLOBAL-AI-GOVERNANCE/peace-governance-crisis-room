import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "game" / "data" / "release_language" / "controlled_language.json"
data = json.loads(path.read_text(encoding="utf-8"))
required = {
    "confirmed", "likely", "possible", "unverified", "disputed",
    "manipulated_unclear", "humanitarian_unverified", "translation_uncertain"
}
missing = required - set(data)
if missing:
    raise SystemExit(f"Missing release language entries: {sorted(missing)}")
for key, value in data.items():
    if not isinstance(value, str) or len(value.strip()) < 20:
        raise SystemExit(f"Release language entry {key} is too short or invalid")
print("Release language validation passed.")
