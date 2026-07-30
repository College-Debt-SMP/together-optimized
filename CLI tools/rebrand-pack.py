#!/usr/bin/env python3
"""Ensure newest pack.toml uses Together Optimized branding after upstream merges."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def newest_pack_toml(repo_root: Path) -> Path:
    packwiz = repo_root / "Packwiz"
    versions = sorted(
        (p for p in packwiz.iterdir() if p.is_dir()),
        key=lambda p: [int(x) if x.isdigit() else x for x in p.name.replace("-", ".").split(".")],
    )
    if not versions:
        raise SystemExit("No Packwiz version directories found")
    return versions[-1] / "pack.toml"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--pack-toml", type=Path)
    parser.add_argument("--name", default="Together Optimized")
    parser.add_argument("--author", default="CherryQuartzio")
    args = parser.parse_args()

    pack_toml = args.pack_toml or newest_pack_toml(args.repo_root)
    text = pack_toml.read_text(encoding="utf-8")
    text, n1 = re.subn(r'(?m)^name\s*=\s*"[^"]*"', f'name = "{args.name}"', text, count=1)
    text, n2 = re.subn(r'(?m)^author\s*=\s*"[^"]*"', f'author = "{args.author}"', text, count=1)
    if n1 != 1 or n2 != 1:
        raise SystemExit(f"Could not rewrite name/author in {pack_toml}")
    pack_toml.write_text(text, encoding="utf-8")
    print(f"Branded {pack_toml}: name={args.name!r} author={args.author!r}")


if __name__ == "__main__":
    main()
