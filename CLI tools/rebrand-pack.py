#!/usr/bin/env python3
"""Apply Together Optimized branding after upstream merges.

Updates the newest Packwiz MC folder:
- pack.toml name/author
- isxander-main-menu-credits.json (and modpack_defaults copy)
- fabric_loader_dependencies.json (and modpack_defaults copy)
- crash_assistant config.toml promo/support fields (and modpack_defaults copy)
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def newest_pack_dir(repo_root: Path) -> Path:
    packwiz = repo_root / "Packwiz"
    versions = sorted(
        (p for p in packwiz.iterdir() if p.is_dir()),
        key=lambda p: [int(x) if x.isdigit() else x for x in p.name.replace("-", ".").split(".")],
    )
    if not versions:
        raise SystemExit("No Packwiz version directories found")
    return versions[-1]


def rebrand_pack_toml(pack_toml: Path, name: str, author: str) -> None:
    text = pack_toml.read_text(encoding="utf-8")
    text, n1 = re.subn(r'(?m)^name\s*=\s*"[^"]*"', f'name = "{name}"', text, count=1)
    text, n2 = re.subn(r'(?m)^author\s*=\s*"[^"]*"', f'author = "{author}"', text, count=1)
    if n1 != 1 or n2 != 1:
        raise SystemExit(f"Could not rewrite name/author in {pack_toml}")
    pack_toml.write_text(text, encoding="utf-8")
    print(f"Branded {pack_toml}: name={name!r} author={author!r}")


def rebrand_credits(path: Path, name: str, hover: str) -> None:
    if not path.is_file():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    entry = {
        "text": name,
        "hover_event": {"action": "show_text", "value": hover},
    }
    data.setdefault("main_menu", {}).setdefault("bottom_right", [{}])
    data["main_menu"]["bottom_right"][0] = entry
    path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(f"Branded {path}")


def rebrand_fabric_loader(path: Path, name: str) -> None:
    if not path.is_file():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    recommends = (
        data.setdefault("overrides", {})
        .setdefault("minecraft", {})
        .setdefault("+recommends", {})
    )
    # Preserve upstream FO version constraint value when renaming the key.
    fo_value = recommends.pop("Fabulously Optimized", None)
    if fo_value is None and name in recommends:
        fo_value = recommends[name]
    if fo_value is None:
        pack_toml = next((p / "pack.toml" for p in path.parents if (p / "pack.toml").is_file()), None)
        if pack_toml is None:
            raise SystemExit(f"Could not find version constraint in {path}")
        m = re.search(r'(?m)^version\s*=\s*"([^"]+)"', pack_toml.read_text(encoding="utf-8"))
        if not m:
            raise SystemExit(f"Could not read version from {pack_toml}")
        fo_value = f">{m.group(1)}"
    recommends[name] = fo_value
    path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(f"Branded {path}: recommends[{name!r}]={fo_value!r}")


def rebrand_crash_assistant(
    path: Path,
    *,
    modpack_name: str,
    support_name: str,
    help_link: str,
) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    replacements = [
        (r'(?m)^(\s*help_link\s*=\s*)"[^"]*"', rf'\1"{help_link}"'),
        (r'(?m)^(\s*support_name\s*=\s*)"[^"]*"', rf'\1"{support_name}"'),
        (r'(?m)^(\s*modpack_name\s*=\s*)"[^"]*"', rf'\1"{modpack_name}"'),
    ]
    for pattern, repl in replacements:
        text, n = re.subn(pattern, repl, text, count=1)
        if n != 1:
            raise SystemExit(f"Could not rewrite field matching {pattern!r} in {path}")
    path.write_text(text, encoding="utf-8")
    print(f"Branded {path}: modpack_name={modpack_name!r} support_name={support_name!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--pack-dir", type=Path, help="Defaults to newest Packwiz/<mc>/")
    parser.add_argument("--name", default="Together Optimized")
    parser.add_argument("--author", default="CherryQuartzio")
    parser.add_argument("--support-name", default="College Debt SMP")
    parser.add_argument(
        "--credits-hover",
        default="Private pack for College Debt SMP\nBased on Fabulously Optimized",
    )
    parser.add_argument("--help-link", default="CHANGE_ME")
    args = parser.parse_args()

    pack_dir = args.pack_dir or newest_pack_dir(args.repo_root)
    if not pack_dir.is_dir():
        raise SystemExit(f"Missing pack dir {pack_dir}")

    rebrand_pack_toml(pack_dir / "pack.toml", args.name, args.author)

    credit_paths = [
        pack_dir / "config" / "isxander-main-menu-credits.json",
        pack_dir / "config" / "modpack_defaults" / "config" / "isxander-main-menu-credits.json",
    ]
    for path in credit_paths:
        rebrand_credits(path, args.name, args.credits_hover)

    loader_paths = [
        pack_dir / "config" / "fabric_loader_dependencies.json",
        pack_dir / "config" / "modpack_defaults" / "config" / "fabric_loader_dependencies.json",
    ]
    for path in loader_paths:
        rebrand_fabric_loader(path, args.name)

    crash_paths = [
        pack_dir / "config" / "crash_assistant" / "config.toml",
        pack_dir / "config" / "modpack_defaults" / "config" / "crash_assistant" / "config.toml",
    ]
    for path in crash_paths:
        rebrand_crash_assistant(
            path,
            modpack_name=args.name,
            support_name=args.support_name,
            help_link=args.help_link,
        )


if __name__ == "__main__":
    main()
