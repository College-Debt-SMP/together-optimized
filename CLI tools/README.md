These scripts help maintain Together Optimized (originally adapted from Fabulously Optimized maintainer tools).

| Script | Purpose |
|--------|---------|
| `prune-old-packwiz.sh [N]` | Keep the newest `N` Packwiz MC folders (default 3) |
| `fork-mods.txt` | Modrinth slugs updated independently of upstream FO |
| `fork-version.py` | Fork version suffix helpers (`print`, `bump`, `ensure-upstream`, `decide`) |
| `ensure-initial-fork-suffix.py` | Apply `.1` when pack version still has no fork suffix |
| `rebrand-pack.py` | Reset newest `pack.toml` name/author after upstream merges |
| `update-fork-mods.py` | Add/update fork mods on all retained Packwiz folders via Modrinth |
| `update-changelog.py` | Prepend a release section to `CHANGELOG.md` |
| `export-release.sh [outdir]` | Export CurseForge `.zip` + Modrinth `.mrpack` from the newest folder |

GitHub Actions:

- `.github/workflows/sync-upstream.yml` — merge FO, prune, update fork mods, release
- `.github/workflows/update-fork-mods.yml` — manual fork-mod-only update + release
