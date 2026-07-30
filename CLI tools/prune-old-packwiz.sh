#!/usr/bin/env bash
# Keep only the latest Minecraft version directory under Packwiz/.
# Shared Packwiz root files (README, scripts, mmc-export.toml) are preserved.
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
packwiz_dir="$repo_root/Packwiz"

if [[ ! -d "$packwiz_dir" ]]; then
  echo "Packwiz directory not found at $packwiz_dir" >&2
  exit 1
fi

mapfile -t versions < <(
  find "$packwiz_dir" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort -V
)

if [[ ${#versions[@]} -eq 0 ]]; then
  echo "No Packwiz version directories found." >&2
  exit 1
fi

latest="${versions[-1]}"
echo "Keeping Packwiz/$latest"

for version in "${versions[@]}"; do
  if [[ "$version" != "$latest" ]]; then
    echo "Removing Packwiz/$version"
    rm -rf "$packwiz_dir/$version"
  fi
done
