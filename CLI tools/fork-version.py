#!/usr/bin/env python3
"""Manage Together Optimized fork version suffixes on top of FO versions.

FO version V becomes fork V.1 on first fork release for that FO version.
Fork-only mod updates increment the trailing segment: V.1 -> V.2, etc.

Examples:
  14.0.0-beta.3  -> 14.0.0-beta.3.1
  14.0.0-alpha.2 -> 14.0.0-alpha.2.1
  14.0.0         -> 14.0.0.1
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


FORK_PRE_RE = re.compile(r"^(?P<base>\d+\.\d+\.\d+-(?:alpha|beta)\.\d+)\.(?P<rev>\d+)$")
FORK_STABLE_RE = re.compile(r"^(?P<base>\d+\.\d+\.\d+)\.(?P<rev>\d+)$")


def split_fork_version(version: str) -> tuple[str, int | None]:
    """Return (fo_base, fork_rev_or_None).

    FO versions look like ``14.0.0``, ``14.0.0-beta.3``, or ``14.0.0-alpha.1``.
    Fork versions append another ``.N``: ``14.0.0.1``, ``14.0.0-beta.3.2``.
    """
    match = FORK_PRE_RE.match(version) or FORK_STABLE_RE.match(version)
    if not match:
        return version, None
    return match.group("base"), int(match.group("rev"))


def read_pack_version(pack_toml: Path) -> str:
    data = tomllib.loads(pack_toml.read_text(encoding="utf-8"))
    return str(data["version"])


def write_pack_version(pack_toml: Path, version: str) -> None:
    text = pack_toml.read_text(encoding="utf-8")
    new_text, count = re.subn(
        r'(?m)^version\s*=\s*"[^"]*"',
        f'version = "{version}"',
        text,
        count=1,
    )
    if count != 1:
        raise SystemExit(f"Could not update version field in {pack_toml}")
    pack_toml.write_text(new_text, encoding="utf-8")


def ensure_after_upstream(current: str, upstream: str) -> str:
    """After FO sync to upstream version U, ensure fork version is U.N."""
    base, rev = split_fork_version(current)
    if base == upstream and rev is not None:
        return current
    return f"{upstream}.1"


def bump_fork_revision(current: str) -> str:
    base, rev = split_fork_version(current)
    if rev is None:
        return f"{current}.1"
    return f"{base}.{rev + 1}"


def newest_pack_toml(repo_root: Path) -> Path:
    packwiz = repo_root / "Packwiz"
    versions = sorted(
        (p for p in packwiz.iterdir() if p.is_dir()),
        key=lambda p: [int(x) if x.isdigit() else x for x in p.name.replace("-", ".").split(".")],
    )
    if not versions:
        raise SystemExit("No Packwiz version directories found")
    return versions[-1] / "pack.toml"


def decide_version(
    current: str,
    *,
    start_version: str,
    upstream_synced: bool,
    fork_mods_changed: bool,
) -> tuple[str, bool, str]:
    """Return (new_version, should_release, reason)."""
    cur_base, cur_rev = split_fork_version(current)
    start_base, _ = split_fork_version(start_version or current)
    bare = current if cur_rev is None else cur_base

    if upstream_synced:
        if bare != start_base:
            return (
                f"{bare}.1",
                True,
                f"Upstream FO version base changed ({start_base} -> {bare})",
            )
        if cur_rev is None:
            return (
                f"{bare}.1",
                True,
                f"Applied initial fork suffix for upstream version {bare}",
            )
        if fork_mods_changed:
            return bump_fork_revision(current), True, "Fork mods updated"
        return current, False, "Upstream sync without mod/version changes"

    if fork_mods_changed:
        return bump_fork_revision(current), True, "Fork mods updated"

    return current, False, "No release-producing changes"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    parser.add_argument(
        "--pack-toml",
        type=Path,
        help="Defaults to newest Packwiz/*/pack.toml",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ensure = sub.add_parser("ensure-upstream", help="Set version to FO_VERSION.1 unless already FO_VERSION.N")
    ensure.add_argument("upstream_version")

    sub.add_parser("bump", help="Increment trailing fork revision")
    sub.add_parser("print", help="Print current fork pack version")

    decide = sub.add_parser("decide", help="CI helper: apply version policy and print VERSION/RELEASE/REASON")
    decide.add_argument("--start-version", default="")
    decide.add_argument("--upstream-synced", action="store_true")
    decide.add_argument("--fork-mods-changed", action="store_true")
    decide.add_argument("--env-out", type=Path)

    args = parser.parse_args()
    pack_toml = args.pack_toml or newest_pack_toml(args.repo_root)
    if not pack_toml.is_file():
        raise SystemExit(f"Missing {pack_toml}")

    current = read_pack_version(pack_toml)

    if args.command == "print":
        print(current)
        return

    if args.command == "ensure-upstream":
        new_version = ensure_after_upstream(current, args.upstream_version)
    elif args.command == "bump":
        new_version = bump_fork_revision(current)
    elif args.command == "decide":
        new_version, release, reason = decide_version(
            current,
            start_version=args.start_version,
            upstream_synced=args.upstream_synced,
            fork_mods_changed=args.fork_mods_changed,
        )
    else:  # pragma: no cover
        raise SystemExit(f"Unknown command {args.command}")

    if new_version != current:
        write_pack_version(pack_toml, new_version)
        print(f"Updated {pack_toml}: {current} -> {new_version}", file=sys.stderr)
    else:
        print(f"Unchanged {pack_toml}: {current}", file=sys.stderr)

    if args.command == "decide":
        text = (
            f"VERSION={new_version}\n"
            f"RELEASE={'true' if release else 'false'}\n"
            f"REASON={reason}\n"
        )
        if args.env_out:
            args.env_out.write_text(text, encoding="utf-8")
        print(text, end="")
    else:
        print(new_version)


if __name__ == "__main__":
    main()
