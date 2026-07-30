# Packwiz

[Packwiz](https://github.com/comp500/packwiz) manages this pack via TOML metadata under `Packwiz/<minecraft-version>/`.

Together Optimized keeps **only the latest** Minecraft version folder. After syncing from [Fabulously Optimized](https://github.com/Fabulously-Optimized/fabulously-optimized), run:

```bash
bash "CLI tools/prune-old-packwiz.sh"
```

## Requirements

1. Install [packwiz](https://github.com/packwiz/packwiz) (prebuilt binaries from GitHub Actions / nightly builds, or `go install`).
2. For MultiMC/Prism auto-update instances, place [packwiz-installer-bootstrap](https://github.com/comp500/packwiz-installer-bootstrap/releases) in the instance's `.minecraft` folder.

The `pre-launch` / `post-exit` scripts can optionally disable selected mods after an update.
