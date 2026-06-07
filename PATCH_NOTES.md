# Peace OS v0.2.1 GitHub Publication Patch Notes

This patch is not v0.3 and does not change gameplay doctrine.

It prepares the project for public GitHub publication by adding:

- a public-facing README replacement,
- a corrected `.gitignore` that keeps `game/export_presets.cfg` commit-ready,
- stronger contribution guidance,
- issue templates,
- a pull request template,
- release description text,
- repository topics,
- Git push commands,
- a pre-publish checklist.

Most important fix:

The previous `.gitignore` ignored `export_presets.cfg`. That could prevent the Windows export preset from being committed to GitHub. This patch preserves the preset while still excluding credentials and build outputs.
