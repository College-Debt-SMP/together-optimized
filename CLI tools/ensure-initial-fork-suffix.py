#!/usr/bin/env python3
"""If the newest pack version has no fork suffix, apply .1 and mark RELEASE=true."""

from __future__ import annotations

import argparse
from importlib.machinery import SourceFileLoader
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--env-file", type=Path, required=True)
    args = parser.parse_args()

    helper = Path(__file__).resolve().parent / "fork-version.py"
    mod = SourceFileLoader("fv", str(helper)).load_module()
    pack = mod.newest_pack_toml(args.repo_root)
    current = mod.read_pack_version(pack)
    _base, rev = mod.split_fork_version(current)

    if rev is None:
        new = f"{current}.1"
        mod.write_pack_version(pack, new)
        env = (
            f"VERSION={new}\n"
            f"RELEASE=true\n"
            f"REASON=Applied initial fork suffix {new}\n"
        )
        args.env_file.write_text(env, encoding="utf-8")
        print(f"Applied initial fork suffix: {new}")
    else:
        print(f"Fork suffix already present: {current}")

    print(args.env_file.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
