# GitHub Push Commands

Use after unzipping `peace-os-crisis-room-v0.2.1-doctrine-verified-source.zip`.

```bash
git init
git add .
git commit -m "Release Peace OS: Crisis Room v0.2.1 public build candidate source"
git branch -M main
git remote add origin https://github.com/Global-AI-Governance/peace-os-crisis-room.git
git push -u origin main
```

Create and push the release tag:

```bash
git tag v0.2.1
git push origin v0.2.1
```

Important: confirm `game/export_presets.cfg` is included in the commit:

```bash
git ls-files | grep "game/export_presets.cfg"
```
