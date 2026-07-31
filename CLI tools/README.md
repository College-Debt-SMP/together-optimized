These scripts help maintain Together Optimized (originally adapted from Fabulously Optimized maintainer tools).

| Script | Purpose |
|--------|---------|
| `prune-old-packwiz.sh [N]` | Keep the newest `N` Packwiz MC folders (default 3) |
| `fork-mods.txt` | Modrinth slugs updated independently of upstream FO |
| `fork-version.py` | Fork version suffix helpers (`print`, `bump`, `ensure-upstream`, `decide`) |
| `rebrand-pack.py` | Reset newest `pack.toml` name/author after upstream merges |
| `update-fork-mods.py` | Add/update fork mods on all retained Packwiz folders via Modrinth |
| `resolve-modrinth-project.py` | Resolve Modrinth base62 project id for CI publish |
| `update-changelog.py` | Prepend a release section to `CHANGELOG.md` |
| `export-release.sh [outdir]` | Export CurseForge `.zip` + Modrinth `.mrpack` from the newest folder |

GitHub Actions:

- `.github/workflows/sync-upstream.yml` — merge FO, prune, update fork mods, release (upstream sync can release without fork-mod changes; fork-only path releases only if a fork mod updated)
- `.github/workflows/update-fork-mods.yml` — manual fork-mod-only update; releases only if a fork mod updated
- `.github/workflows/publish-modrinth.yml` — publish GitHub Release `.mrpack` to Modrinth
