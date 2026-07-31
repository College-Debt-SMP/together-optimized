Modrinth packs can be generated with [packwiz](https://github.com/packwiz/packwiz) (`packwiz modrinth export` from `Packwiz/26.2`) or [mmc-export](https://github.com/RozeFound/mmc-export).

Together Optimized is published at https://modrinth.com/modpack/together-optimized. GitHub Actions (`.github/workflows/publish-modrinth.yml`) uploads the `.mrpack` from each GitHub Release to Modrinth. The pack is not published to CurseForge.

Required Actions configuration:

- Secret `MODRINTH_TOKEN` — Modrinth PAT with at least `VERSION_CREATE` (and `PROJECT_READ` / `USER_READ` if the project id is not set below)
- Optional variable `MODRINTH_PROJECT_ID` — base62 project id from the Modrinth project page (avoids draft-project lookup)
