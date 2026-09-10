# Together Optimized

A private Fabric modpack for the **College Debt SMP** Minecraft server.

Together Optimized is maintained by [CherryQuartzio](https://github.com/CherryQuartzio). It is based on [Fabulously Optimized](https://github.com/Fabulously-Optimized/fabulously-optimized) and adds multiplayer- and performance-oriented mods for the server's use. There is no public release planned at this time.

## About

- **Minecraft:** latest supported version in this repo (`Packwiz/26.2`)
- **Loader:** Fabric
- **Purpose:** performance and graphics enhancements, plus voice chat, VR, and related multiplayer features for College Debt SMP

See [INCLUDED-MODS.md](INCLUDED-MODS.md) for the current mod list.

## Attribution

This project is a fork of **[Fabulously Optimized](https://github.com/Fabulously-Optimized/fabulously-optimized)** by the Fabulously Optimized authors.

Upstream project links:

- Repository: https://github.com/Fabulously-Optimized/fabulously-optimized
- CurseForge: https://www.curseforge.com/minecraft/modpacks/fabulously-optimized
- Modrinth: https://modrinth.com/modpack/fabulously-optimized

Upstream source code remains under the terms in [LICENSE.md](LICENSE.md). Together Optimized retains the original copyright notice and adds fork-specific changes on top.

## Repository layout

| Path | Purpose |
|------|---------|
| `Packwiz/<mc>/` | Packwiz metadata per Minecraft version this fork owns (newest is current) |
| `CLI tools/` | Maintainer scripts (including upstream sync helpers) |
| `CurseForge/`, `Modrinth/`, `MultiMC/` | Export / instance scaffolding inherited from upstream |
| `.github/workflows/sync-upstream.yml` | Merges upstream FO into this fork (never pushes to FO) |

## Syncing with upstream

```bash
find Packwiz -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort -V > /tmp/owned-packwiz.txt
git fetch upstream
git merge upstream/main
# If conflicts: bash "CLI tools/resolve-upstream-merge.sh" && git commit
bash "CLI tools/drop-unowned-packwiz.sh" /tmp/owned-packwiz.txt
python3 "CLI tools/rebrand-pack.py"
python3 "CLI tools/update-fork-mods.py" --latest 2
```

Or run the **Sync upstream and update fork mods** / **Update fork mods** GitHub Actions on this fork. Push is disabled for the `upstream` remote so nothing is posted to the original FO repository. Releases publish CurseForge `.zip` and Modrinth `.mrpack` assets to GitHub Releases.
