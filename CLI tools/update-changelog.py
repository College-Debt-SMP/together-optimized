#!/usr/bin/env python3
"""Prepend a fork release section to CHANGELOG.md."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--changelog", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--fragment", type=Path, required=True, help="Markdown fragment to include")
    parser.add_argument("--reason", default="Fork release", help="Short reason line")
    args = parser.parse_args()

    fragment = args.fragment.read_text(encoding="utf-8").strip()
    today = dt.date.today().isoformat()
    section = (
        f"## {args.version} ({today})\n\n"
        f"{args.reason}\n\n"
        f"{fragment}\n\n"
    )

    existing = args.changelog.read_text(encoding="utf-8") if args.changelog.exists() else "# Changelog\n\n"
    # Insert after the first heading block
    lines = existing.splitlines(keepends=True)
    if not lines:
        new_text = f"# Changelog\n\n{section}"
    else:
        # Find end of initial title + intro paragraphs (before first ## or end)
        insert_at = 0
        seen_title = False
        for i, line in enumerate(lines):
            if line.startswith("# "):
                seen_title = True
                insert_at = i + 1
                continue
            if seen_title and line.startswith("## "):
                insert_at = i
                break
            if seen_title:
                insert_at = i + 1
        new_text = "".join(lines[:insert_at])
        if not new_text.endswith("\n\n"):
            if not new_text.endswith("\n"):
                new_text += "\n"
            new_text += "\n"
        new_text += section + "".join(lines[insert_at:])

    args.changelog.write_text(new_text, encoding="utf-8")
    print(f"Updated {args.changelog} with {args.version}")


if __name__ == "__main__":
    main()
