# Together Optimized repository

Private Fabric modpack fork for **College Debt SMP**, maintained by **CherryQuartzio**.

Based on [Fabulously Optimized](https://github.com/Fabulously-Optimized/fabulously-optimized). This fork keeps Packwiz metadata for the latest Minecraft version only and adds extra mods for the server.

## Layout

* `Packwiz/26.2/` — current pack metadata, configs, and resource-pack references
* `CLI tools/` — maintainer helpers (including `prune-old-packwiz.sh`)
* `CurseForge/`, `Modrinth/`, `MultiMC/`, `MultiMC-Packwiz/` — export scaffolding inherited from upstream
* `.github/workflows/sync-upstream.yml` — merges upstream FO into this fork; never pushes to FO
* `.github/upstream-workflows/` — disabled upstream GitHub Actions (publish / Bitbucket sync)

## Notes

* JAR files are not stored in git (see `.gitignore`) out of respect for mod authors. Use Packwiz, CurseForge, or Modrinth to download mods.
* Older Minecraft Packwiz folders are intentionally removed; after an upstream sync, run `bash "CLI tools/prune-old-packwiz.sh"` (also done by the sync workflow).

## Working with Packwiz

```bash
cd Packwiz/26.2
packwiz list
packwiz modrinth add -y <modrinth-url>
packwiz refresh
```

Export a Modrinth pack when needed:

```bash
cd Packwiz/26.2
packwiz modrinth export
```

There is no public CurseForge/Modrinth publish pipeline for this fork yet.
