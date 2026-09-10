# Packwiz

[Packwiz](https://github.com/comp500/packwiz) manages this pack via TOML metadata under `Packwiz/<minecraft-version>/`.

Together Optimized keeps every Minecraft version folder this fork already owns. After syncing from [Fabulously Optimized](https://github.com/Fabulously-Optimized/fabulously-optimized), drop FO-only older trees (folders we never kept) while adopting any newer MC version:

```bash
# owned-dirs.txt is the pre-merge Packwiz/<mc> list (one name per line)
bash "CLI tools/drop-unowned-packwiz.sh" owned-dirs.txt
```

## Requirements

1. Install [packwiz](https://github.com/packwiz/packwiz) (prebuilt binaries from GitHub Actions / nightly builds, or `go install`).
2. For MultiMC/Prism auto-update instances, place [packwiz-installer-bootstrap](https://github.com/comp500/packwiz-installer-bootstrap/releases) in the instance's `.minecraft` folder.

The `pre-launch` / `post-exit` scripts can optionally disable selected mods after an update.
