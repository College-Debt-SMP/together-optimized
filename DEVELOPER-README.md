# Together Optimized repository

Private Fabric modpack fork for **College Debt SMP**, maintained by **CherryQuartzio**.

Based on [Fabulously Optimized](https://github.com/Fabulously-Optimized/fabulously-optimized). This fork keeps Packwiz metadata for every Minecraft version it already owns (and adopts newer FO MC versions), and adds extra mods for the server.

## Layout

* `Packwiz/<mc>/` — pack metadata per owned Minecraft version (newest is current, e.g. `26.2`)
* `CLI tools/` — maintainer helpers (including `drop-unowned-packwiz.sh`, merge conflict resolver)
* `CurseForge/`, `Modrinth/`, `MultiMC/`, `MultiMC-Packwiz/` — export scaffolding inherited from upstream
* `.github/workflows/sync-upstream.yml` — merge upstream FO, drop FO-only older Packwiz trees, update fork mods on 2 newest folders, publish zip+mrpack GitHub Releases (never pushes to FO)
* `.github/workflows/update-fork-mods.yml` — manual fork-mod update on 2 newest folders + release
* `.github/upstream-workflows/` — disabled upstream GitHub Actions (publish / Bitbucket sync)
* `CLI tools/fork-mods.txt` — Modrinth slugs maintained independently of FO

## Notes

* JAR files are not stored in git (see `.gitignore`) out of respect for mod authors. Use Packwiz, CurseForge, or Modrinth to download mods.
* Owned Packwiz MC folders are kept across syncs. FO-only older folders this fork never kept are dropped after merge (`CLI tools/drop-unowned-packwiz.sh`).

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
