These scripts help maintain Together Optimized (originally adapted from Fabulously Optimized maintainer tools).

| Script | Purpose |
|--------|---------|
| `drop-unowned-packwiz.sh` | After FO merge, remove Packwiz MC folders FO introduced that this fork did not own (keeps owned folders; adopts newer MC versions) |
| `fork-mods.txt` | Modrinth slugs updated independently of upstream FO |
| `fork-version.py` | Fork version suffix helpers (`print`, `bump`, `ensure-upstream`, `decide`) |
| `rebrand-pack.py` | Reset newest pack branding (pack.toml, credits, loader deps, crash assistant) after upstream merges |
| `resolve-upstream-merge.sh` | Auto-resolve predictable FO→fork merge conflicts (keep fork docs; drop unowned Packwiz/MultiMC; take upstream elsewhere) |
| `update-fork-mods.py` | Add/update fork mods via Modrinth (`--latest N` limits to newest N folders; CI uses 2) |
| `resolve-modrinth-project.py` | Resolve Modrinth base62 project id for CI publish |
| `update-changelog.py` | Prepend a release section to `CHANGELOG.md` |
| `export-release.sh [outdir]` | Export CurseForge `.zip` + Modrinth `.mrpack` from the newest folder |

GitHub Actions:

- `.github/workflows/sync-upstream.yml` — merge FO, drop FO-only older Packwiz trees, update fork mods on 2 newest folders, release (upstream sync can release without fork-mod changes; fork-only path releases only if a fork mod updated)
- `.github/workflows/update-fork-mods.yml` — manual fork-mod update on 2 newest folders; releases only if a fork mod updated
- `.github/workflows/publish-modrinth.yml` — publish GitHub Release `.mrpack` to Modrinth
