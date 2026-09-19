#!/usr/bin/env python3
"""Reconcile fork-only Modrinth mods across Packwiz MC folders.

For each selected Packwiz/<mc>/ folder:
  - If a Fabric build exists for that Minecraft version, add or update the mod via packwiz
  - If not, record it as temporarily missing

CI passes ``--latest 2`` so only the two newest MC folders are refreshed (older
owned folders keep their existing fork-mod pins). Omitting ``--latest`` updates
every Packwiz folder.

Prints a JSON summary to stdout and writes a markdown fragment for CHANGELOG use.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
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


def version_key(name: str) -> list:
    return [int(x) if x.isdigit() else x for x in name.replace("-", ".").split(".")]


def packwiz_dirs(repo_root: Path, *, latest: int | None = None) -> list[Path]:
    packwiz = repo_root / "Packwiz"
    dirs = sorted(
        (p for p in packwiz.iterdir() if p.is_dir()),
        key=lambda p: version_key(p.name),
    )
    if latest is not None:
        if latest < 1:
            raise SystemExit("--latest must be >= 1")
        dirs = dirs[-latest:]
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
    try:
        result = subprocess.run(
            cmd,
            cwd=pack_dir,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print(f"Warning: packwiz not found on PATH; skipping packwiz {' '.join(args)}", file=sys.stderr)
        return
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


def remove_mod(pack_dir: Path, stem: str, meta_path: Path | None) -> None:
    try:
        run_packwiz(pack_dir, ["remove", stem])
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    if meta_path is not None and meta_path.is_file():
        meta_path.unlink()
        print(f"Removed leftover metadata {meta_path.name}", file=sys.stderr)


def readd_mod(pack_dir: Path, slug: str, stem: str, meta_path: Path | None) -> None:
    remove_mod(pack_dir, stem, meta_path)
    run_packwiz(pack_dir, ["modrinth", "add", slug])


JAR_CACHE: dict[str, dict | None] = {}


def get_fabric_mod_json(url: str | None) -> dict | None:
    if not url:
        return None
    if url in JAR_CACHE:
        return JAR_CACHE[url]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        zf = zipfile.ZipFile(io.BytesIO(data))
        if "fabric.mod.json" in zf.namelist():
            fmj = json.loads(zf.read("fabric.mod.json").decode("utf-8", errors="replace"))
            JAR_CACHE[url] = fmj
            return fmj
    except Exception as exc:
        print(f"Failed to read fabric.mod.json from {url}: {exc}", file=sys.stderr)
    JAR_CACHE[url] = None
    return None


def get_primary_jar_url(version_obj: dict) -> str | None:
    files = version_obj.get("files", [])
    for f in files:
        if f.get("primary") and f.get("filename", "").endswith(".jar"):
            return f.get("url")
    for f in files:
        if f.get("filename", "").endswith(".jar"):
            return f.get("url")
    return files[0].get("url") if files else None


def parse_version(v_str: str) -> tuple[list[int | str], str | None]:
    v = v_str.split("+")[0]
    parts = v.split("-", 1)
    core = parts[0]
    prerelease = parts[1] if len(parts) > 1 else None
    num_parts: list[int | str] = [int(x) if x.isdigit() else x for x in core.split(".")]
    return num_parts, prerelease


def compare_versions(v1_str: str, v2_str: str) -> int:
    v1_parts, v1_pre = parse_version(v1_str)
    v2_parts, v2_pre = parse_version(v2_str)
    max_len = max(len(v1_parts), len(v2_parts))
    p1 = v1_parts + [0] * (max_len - len(v1_parts))
    p2 = v2_parts + [0] * (max_len - len(v2_parts))
    for a, b in zip(p1, p2):
        if isinstance(a, int) and isinstance(b, int):
            if a != b:
                return -1 if a < b else 1
        else:
            if str(a) != str(b):
                return -1 if str(a) < str(b) else 1
    if v1_pre is None and v2_pre is not None:
        return 1
    if v1_pre is not None and v2_pre is None:
        return -1
    if v1_pre is not None and v2_pre is not None:
        if v1_pre != v2_pre:
            return -1 if v1_pre < v2_pre else 1
    return 0


def check_single_constraint(installed_ver: str, cond: str) -> bool:
    cond = cond.strip()
    if not cond or cond == "*":
        return True
    if cond.startswith(">="):
        target = cond[2:].strip().rstrip("-")
        return compare_versions(installed_ver, target) >= 0
    if cond.startswith(">"):
        target = cond[1:].strip()
        return compare_versions(installed_ver, target) > 0
    if cond.startswith("<="):
        target = cond[2:].strip().rstrip("-")
        return compare_versions(installed_ver, target) <= 0
    if cond.startswith("<"):
        target = cond[1:].strip()
        return compare_versions(installed_ver, target) < 0
    if cond.startswith("="):
        target = cond[1:].strip()
        return compare_versions(installed_ver, target) == 0
    if cond.startswith("~"):
        target = cond[1:].strip()
        parts, _ = parse_version(target)
        if len(parts) >= 2 and isinstance(parts[0], int) and isinstance(parts[1], int):
            upper = f"{parts[0]}.{parts[1]+1}.0"
        elif len(parts) >= 1 and isinstance(parts[0], int):
            upper = f"{parts[0]+1}.0.0"
        else:
            upper = target
        return compare_versions(installed_ver, target) >= 0 and compare_versions(installed_ver, upper) < 0
    return compare_versions(installed_ver, cond) == 0


def check_constraint(installed_ver: str, spec: str | list) -> bool:
    if isinstance(spec, list):
        return any(check_constraint(installed_ver, s) for s in spec)
    return all(check_single_constraint(installed_ver, c) for c in str(spec).split())


def load_installed_mods(mods_dir: Path) -> dict[str, dict]:
    installed = {}
    for path in mods_dir.glob("*.pw.toml"):
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        update = data.get("update", {}).get("modrinth", {})
        proj_id = update.get("mod-id")
        if not proj_id:
            continue
        installed[proj_id] = {
            "name": data.get("name", path.stem),
            "stem": path.stem,
            "meta_path": path,
            "version_id": update.get("version"),
            "filename": data.get("filename", ""),
            "url": data.get("download", {}).get("url"),
        }
    return installed


def check_mod_compatibility(
    candidate: dict,
    installed: dict[str, dict],
) -> list[str]:
    conflicts = []
    candidate_jar_url = get_primary_jar_url(candidate)
    candidate_fmj = get_fabric_mod_json(candidate_jar_url) if candidate_jar_url else None

    # Check Modrinth dependencies
    for dep in candidate.get("dependencies", []):
        proj_id = dep.get("project_id")
        dep_type = dep.get("dependency_type")
        dep_ver = dep.get("version_id")
        if proj_id in installed:
            inst = installed[proj_id]
            if dep_type == "incompatible":
                conflicts.append(f"incompatible with installed mod '{inst['name']}'")
            elif dep_type == "required":
                # Check fabric.mod.json constraint if available
                if candidate_fmj and candidate_fmj.get("depends"):
                    inst_fmj = get_fabric_mod_json(inst.get("url")) if inst.get("url") else None
                    inst_mod_id = inst_fmj.get("id") if inst_fmj else inst["stem"]
                    inst_ver = inst_fmj.get("version") if inst_fmj else None
                    if not inst_ver and inst["filename"]:
                        m = re.search(
                            r"(\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9.]+)?(?:\+[a-zA-Z0-9.]+)?|\d+\.\d+)",
                            inst["filename"],
                        )
                        if m:
                            inst_ver = m.group(1)
                    if inst_mod_id in candidate_fmj["depends"]:
                        req_spec = candidate_fmj["depends"][inst_mod_id]
                        if inst_ver and not check_constraint(inst_ver, req_spec):
                            conflicts.append(
                                f"requires {inst['name']} ({inst_mod_id}) {req_spec}, "
                                f"but installed is {inst_ver} ({inst['filename']})"
                            )
                        continue
                if dep_ver and dep_ver != inst["version_id"]:
                    conflicts.append(
                        f"requires {inst['name']} version {dep_ver}, "
                        f"but installed is {inst['version_id']}"
                    )

    # Check fabric.mod.json breaks & conflicts
    if candidate_fmj:
        for brk_id, brk_spec in candidate_fmj.get("breaks", {}).items():
            for inst in installed.values():
                if inst["stem"] == brk_id:
                    inst_fmj = get_fabric_mod_json(inst.get("url")) if inst.get("url") else None
                    inst_ver = inst_fmj.get("version") if inst_fmj else None
                    if not inst_ver and inst["filename"]:
                        m = re.search(
                            r"(\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9.]+)?(?:\+[a-zA-Z0-9.]+)?|\d+\.\d+)",
                            inst["filename"],
                        )
                        if m:
                            inst_ver = m.group(1)
                    if inst_ver and check_constraint(inst_ver, brk_spec):
                        conflicts.append(
                            f"breaks installed mod '{inst['name']}' ({brk_id} {inst_ver} matches {brk_spec})"
                        )

        for cnf_id in candidate_fmj.get("conflicts", {}).keys():
            for inst in installed.values():
                if inst["stem"] == cnf_id:
                    conflicts.append(f"conflicts with installed mod '{inst['name']}'")

    return conflicts


def reconcile_folder(
    pack_dir: Path,
    slugs: list[str],
    *,
    remove_incompatible: bool = True,
) -> dict:
    pack_toml = pack_dir / "pack.toml"
    mc_version = read_minecraft_version(pack_toml)
    mods_dir = pack_dir / "mods"
    changed = False
    updated: list[dict] = []
    added: list[dict] = []
    removed: list[dict] = []
    incompatible: list[dict] = []
    missing: list[str] = []
    unchanged: list[str] = []
    errors: list[dict] = []

    # Index fork .pw.toml files that an upstream merge may have dropped from index.toml.
    run_packwiz(pack_dir, ["refresh"])
    installed = load_installed_mods(mods_dir)

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

        conflicts = check_mod_compatibility(latest, installed)
        if conflicts:
            print(
                f"Incompatible fork mod {slug}: {'; '.join(conflicts)}",
                file=sys.stderr,
            )
            if meta is not None and remove_incompatible:
                print(
                    f"Removing incompatible fork mod {slug} from {pack_dir.name}...",
                    file=sys.stderr,
                )
                remove_mod(pack_dir, stem, meta)
                changed = True
                removed.append(
                    {
                        "slug": slug,
                        "version": version_number,
                        "version_id": version_id,
                        "conflicts": conflicts,
                    }
                )
                if project_id in installed:
                    del installed[project_id]
            else:
                incompatible.append(
                    {
                        "slug": slug,
                        "version": version_number,
                        "version_id": version_id,
                        "conflicts": conflicts,
                    }
                )
            continue

        if meta is None:
            try:
                run_packwiz(pack_dir, ["modrinth", "add", slug])
            except subprocess.CalledProcessError as exc:
                errors.append({"slug": slug, "error": str(exc)})
                print(f"Failed to add {slug}: {exc}", file=sys.stderr)
                continue
            changed = True
            added.append({"slug": slug, "version": version_number, "version_id": version_id})
            installed = load_installed_mods(mods_dir)
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
        installed = load_installed_mods(mods_dir)

    run_packwiz(pack_dir, ["refresh"])

    return {
        "mc_version": mc_version,
        "pack_dir": str(pack_dir),
        "changed": changed,
        "added": added,
        "updated": updated,
        "removed": removed,
        "incompatible": incompatible,
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
        if result.get("removed"):
            any_change = True
            lines.append("Removed (incompatible with upstream):")
            for item in result["removed"]:
                reasons = "; ".join(item.get("conflicts", []))
                lines.append(f"- `{item['slug']}`: {reasons}")
        if result["missing"]:
            lines.append("Temporarily missing (no Fabric build for this MC version yet):")
            for slug in result["missing"]:
                lines.append(f"- `{slug}`")
        if result.get("incompatible"):
            lines.append("Temporarily skipped (incompatible with upstream):")
            for item in result["incompatible"]:
                reasons = "; ".join(item.get("conflicts", []))
                lines.append(f"- `{item['slug']}`: {reasons}")
        if result.get("errors"):
            lines.append("Failed to add or update:")
            for item in result["errors"]:
                lines.append(f"- `{item['slug']}`: {item['error']}")
        if (
            not result["added"]
            and not result["updated"]
            and not result.get("removed")
            and not result["missing"]
            and not result.get("incompatible")
            and not result.get("errors")
        ):
            lines.append("- All fork mods present and up to date.")
        lines.append("")
    if (
        not any_change
        and all(
            not r["missing"]
            and not r.get("incompatible")
            and not r.get("errors")
            for r in results
        )
    ):
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
    parser.add_argument(
        "--latest",
        type=int,
        default=None,
        metavar="N",
        help="Only reconcile the newest N Packwiz MC folders (CI uses 2 to save runtime)",
    )
    parser.add_argument(
        "--no-remove-incompatible",
        action="store_true",
        help="Do not remove already-installed fork mods that became incompatible with upstream",
    )
    args = parser.parse_args()

    fork_mods_path = args.fork_mods or (args.repo_root / "CLI tools" / "fork-mods.txt")
    slugs = load_slugs(fork_mods_path)
    if not slugs:
        raise SystemExit(f"No slugs found in {fork_mods_path}")

    results = []
    selected = packwiz_dirs(args.repo_root, latest=args.latest)
    if args.latest is not None:
        print(
            f"Limiting fork-mod updates to newest {args.latest} folder(s): "
            f"{', '.join(p.name for p in selected) or '(none)'}",
            file=sys.stderr,
        )
    for pack_dir in selected:
        if not (pack_dir / "pack.toml").is_file():
            continue
        print(f"Reconciling fork mods in {pack_dir.name}...", file=sys.stderr)
        results.append(
            reconcile_folder(
                pack_dir,
                slugs,
                remove_incompatible=not args.no_remove_incompatible,
            )
        )

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
