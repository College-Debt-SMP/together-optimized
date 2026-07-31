# Agent instructions — Together Optimized

Together Optimized is a **private Fabric modpack fork** of [Fabulously Optimized](https://github.com/Fabulously-Optimized/fabulously-optimized) for the **College Debt SMP**, maintained by CherryQuartzio. Keep FO attribution; do not treat this as upstream FO.

## Remotes (critical)

| Remote | URL | Push |
|--------|-----|------|
| `origin` | `College-Debt-SMP/together-optimized` | Yes |
| `upstream` | `Fabulously-Optimized/fabulously-optimized` | **Never** (`pushurl = DISABLE`) |

Always use `gh … -R College-Debt-SMP/together-optimized` or set `GH_REPO: ${{ github.repository }}`. Bare `gh` may resolve to the FO parent and fail with 403.

## Layout

- **`Packwiz/<mc>/`** — source of truth (`pack.toml`, mods, configs). Newest MC folder is current (e.g. `26.2`). JARs are not in git.
- **`CLI tools/`** — maintainer automation; see `CLI tools/README.md`.
- **`Resource Packs/`** — bundled packs (e.g. Mod Menu Helper). Not the Mod Menu mod.
- **`.github/workflows/`** — active CI only.
- **`.github/upstream-workflows/`** — disabled FO workflows kept for reference.

Do **not** name an active workflow `auto-publish.yml` or `git-repo-sync.yml` — sync moves those filenames into `upstream-workflows/`.

## Versioning

FO version `V` → fork `V.1` on first release for that base; later fork-only bumps → `V.2`, …. Examples: `14.0.0-beta.3` → `14.0.0-beta.3.1`. Helpers: `CLI tools/fork-version.py` (`print`, `bump`, `decide`).

## Fork-only mods

Slugs in `CLI tools/fork-mods.txt` (updated independently of FO). Release policy:

- **Upstream sync** (`sync-upstream.yml`): may release when FO base changes or initial `.1` is applied; also when fork mods change.
- **Fork-only** (no upstream merge, or `update-fork-mods.yml`): create a GitHub Release **only** if at least one fork mod changed.

## CI workflows

| Workflow | Trigger | Role |
|----------|---------|------|
| `sync-upstream.yml` | Weekly Mon 12:00 UTC + manual | Merge FO → prune top 3 Packwiz folders → rebrand → fork mods → version/changelog → push **origin** → Release (zip + mrpack) when releasing |
| `update-fork-mods.yml` | Manual | Fork mods only; release only if mods changed |
| `publish-modrinth.yml` | Release published + manual | Upload release `.mrpack` to Modrinth (not CurseForge) |

Jobs must stay gated with `github.repository_owner != 'Fabulously-Optimized'`.

## Publishing

- **Modrinth:** https://modrinth.com/modpack/together-optimized — `.mrpack` only.
- **CurseForge:** not published (GitHub Releases may still attach a CurseForge-format zip for convenience).
- Secrets/vars: `MODRINTH_TOKEN` (required); optional `MODRINTH_PROJECT_ID` (base62 id — slugs with hyphens break `mc-publish`).
- Project id resolution: `CLI tools/resolve-modrinth-project.py`.

## Conventions for agents

- Prefer Packwiz + scripts in `CLI tools/` over hand-editing many `.pw.toml` files.
- After version bumps in a Packwiz folder: `packwiz refresh -y`.
- Keep workflow/scripts **LF** (`.gitattributes`: `* text=auto eol=lf`). CRLF can break Actions YAML parsing.
- Sync strips FO community files if reintroduced (`FUNDING.yml`, CONTRIBUTING, issue templates, etc.).
- Do not push to `upstream`. Do not re-enable FO Discord/`download.fo` promo in configs.
- License: BSD-3-Clause (same family as FO); see `LICENSE.md`.

## Quick refs

- Mod list: `INCLUDED-MODS.md`
- Changelog: `CHANGELOG.md`
- Maintainer overview: `README.md`, `DEVELOPER-README.md`, `CLI tools/README.md`, `Modrinth/README.md`
