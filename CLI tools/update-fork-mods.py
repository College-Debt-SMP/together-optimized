#!/usr/bin/env python3
"""Reconcile fork-only Modrinth mods across retained Packwiz MC folders.

For each Packwiz/<mc>/ folder:
  - If a Fabric build exists for that Minecraft version, add or update the mod via packwiz
  - If not, record it as temporarily missing

Prints a JSON summary to stdout and writes a markdown fragment for CHANGELOG use.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

USER_AGENT = "together-optimized/1.0 (College-Debt-SMP; +https://github.com/College-Debt-SMP/together-optimized)"
API = "https://api.modrinth.com/v2"


def load_slugs(path: Path) -> list[str]:
    slugs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        slugs.append(line)
    return slugs


def packwiz_dirs(repo_root: Path) -> list[Path]:
    packwiz = repo_root / "Packwiz"
    dirs = sorted(
        (p for p in packwiz.iterdir() if p.is_dir()),
        key=lambda p: [int(x) if x.isdigit() else x for x in p.name.replace("-", ".").split(".")],
    )
    return dirs


def read_minecraft_version(pack_toml: Path) -> str:
    data = tomllib.loads(pack_toml.read_text(encoding="utf-8"))
    return str(data["versions"]["minecraft"])


def modrinth_get(url: str) -> object:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def latest_fabric_version(slug: str, mc_version: str) -> dict | None:
    params = urllib.parse.urlencode(
        {
            "loaders": json.dumps(["fabric"]),
            "game_versions": json.dumps([mc_version]),
            "include_changelog": "false",
        }
    )
    url = f"{API}/project/{urllib.parse.quote(slug)}/version?{params}"
    try:
        versions = modrinth_get(url)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    if not isinstance(versions, list) or not versions:
        return None
    return versions[0]


def existing_modrinth_meta(mods_dir: Path, project_id: str) -> Path | None:
    for path in mods_dir.glob("*.pw.toml"):
        text = path.read_text(encoding="utf-8")
        if f'mod-id = "{project_id}"' in text or f"mod-id = '{project_id}'" in text:
            return path
        data = tomllib.loads(text)
        update = data.get("update", {}).get("modrinth", {})
        if update.get("mod-id") == project_id:
            return path
    return None


def read_pinned_version(meta_path: Path) -> str | None:
    data = tomllib.loads(meta_path.read_text(encoding="utf-8"))
    return data.get("update", {}).get("modrinth", {}).get("version")


def run_packwiz(pack_dir: Path, args: list[str], *, yes: bool = True) -> None:
    cmd = ["packwiz", *args]
    if yes:
        cmd.append("-y")
    result = subprocess.run(
        cmd,
        cwd=pack_dir,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n", file=sys.stderr)
    if result.stderr:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n", file=sys.stderr)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            cmd,
            output=result.stdout,
            stderr=result.stderr,
        )


def packwiz_id(slug: str, meta_path: Path | None) -> str:
    """Packwiz looks up mods by .pw.toml stem, not the display-name field."""
    if meta_path is not None:
        return meta_path.stem
    return slug


def readd_mod(pack_dir: Path, slug: str, stem: str, meta_path: Path | None) -> None:
    try:
        run_packwiz(pack_dir, ["remove", stem])
    except subprocess.CalledProcessError:
        if meta_path is not None and meta_path.is_file():
            meta_path.unlink()
            print(f"Removed leftover metadata {meta_path.name}", file=sys.stderr)
    run_packwiz(pack_dir, ["modrinth", "add", slug])


def reconcile_folder(pack_dir: Path, slugs: list[str]) -> dict:
    pack_toml = pack_dir / "pack.toml"
    mc_version = read_minecraft_version(pack_toml)
    mods_dir = pack_dir / "mods"
    changed = False
    updated: list[dict] = []
    added: list[dict] = []
    missing: list[str] = []
    unchanged: list[str] = []
    errors: list[dict] = []

    # Index fork .pw.toml files that an upstream merge may have dropped from index.toml.
    run_packwiz(pack_dir, ["refresh"])

    for slug in slugs:
        latest = latest_fabric_version(slug, mc_version)
        if latest is None:
            missing.append(slug)
            continue

        project_id = latest["project_id"]
        version_id = latest["id"]
        version_number = latest.get("version_number", version_id)
        meta = existing_modrinth_meta(mods_dir, project_id)
        stem = packwiz_id(slug, meta)

        if meta is None:
            try:
                run_packwiz(pack_dir, ["modrinth", "add", slug])
            except subprocess.CalledProcessError as exc:
                errors.append({"slug": slug, "error": str(exc)})
                print(f"Failed to add {slug}: {exc}", file=sys.stderr)
                continue
            changed = True
            added.append({"slug": slug, "version": version_number, "version_id": version_id})
            continue

        pinned = read_pinned_version(meta)
        if pinned == version_id:
            unchanged.append(slug)
            continue

        try:
            run_packwiz(pack_dir, ["update", stem])
        except subprocess.CalledProcessError:
            try:
                readd_mod(pack_dir, slug, stem, meta)
            except subprocess.CalledProcessError as exc:
                errors.append({"slug": slug, "error": str(exc)})
                print(f"Failed to update {slug}: {exc}", file=sys.stderr)
                continue
        changed = True
        updated.append(
            {
                "slug": slug,
                "version": version_number,
                "version_id": version_id,
                "previous_version_id": pinned,
            }
        )

    run_packwiz(pack_dir, ["refresh"])

    return {
        "mc_version": mc_version,
        "pack_dir": str(pack_dir),
        "changed": changed,
        "added": added,
        "updated": updated,
        "missing": missing,
        "unchanged": unchanged,
        "errors": errors,
    }


def markdown_report(results: list[dict]) -> str:
    lines = ["### Fork mod status", ""]
    any_change = False
    for result in results:
        mc = result["mc_version"]
        lines.append(f"#### Minecraft {mc}")
        if result["added"]:
            any_change = True
            lines.append("Added:")
            for item in result["added"]:
                lines.append(f"- `{item['slug']}` → {item['version']}")
        if result["updated"]:
            any_change = True
            lines.append("Updated:")
            for item in result["updated"]:
                lines.append(f"- `{item['slug']}` → {item['version']}")
        if result["missing"]:
            lines.append("Temporarily missing (no Fabric build for this MC version yet):")
            for slug in result["missing"]:
                lines.append(f"- `{slug}`")
        if result.get("errors"):
            lines.append("Failed to add or update:")
            for item in result["errors"]:
                lines.append(f"- `{item['slug']}`: {item['error']}")
        if (
            not result["added"]
            and not result["updated"]
            and not result["missing"]
            and not result.get("errors")
        ):
            lines.append("- All fork mods present and up to date.")
        lines.append("")
    if not any_change and all(not r["missing"] and not r.get("errors") for r in results):
        lines.append("_No fork-mod changes._")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    parser.add_argument(
        "--fork-mods",
        type=Path,
        default=None,
        help="Path to fork-mods.txt (default: CLI tools/fork-mods.txt)",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        help="Optional path to write a markdown summary fragment",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional path to write the JSON summary",
    )
    args = parser.parse_args()

    fork_mods_path = args.fork_mods or (args.repo_root / "CLI tools" / "fork-mods.txt")
    slugs = load_slugs(fork_mods_path)
    if not slugs:
        raise SystemExit(f"No slugs found in {fork_mods_path}")

    results = []
    for pack_dir in packwiz_dirs(args.repo_root):
        if not (pack_dir / "pack.toml").is_file():
            continue
        print(f"Reconciling fork mods in {pack_dir.name}...", file=sys.stderr)
        results.append(reconcile_folder(pack_dir, slugs))

    summary = {
        "changed": any(r["changed"] for r in results),
        "results": results,
        "markdown": markdown_report(results),
    }

    if args.json_out:
        args.json_out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.write_text(summary["markdown"], encoding="utf-8")

    print(json.dumps(summary, indent=2))
    # Exit 0 even when unchanged; workflows decide whether to bump versions.
    if summary["changed"]:
        print("FORK_MODS_CHANGED=true")
    else:
        print("FORK_MODS_CHANGED=false")


if __name__ == "__main__":
    main()
