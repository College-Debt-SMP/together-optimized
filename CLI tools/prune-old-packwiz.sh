#!/usr/bin/env bash
# Keep the top N most recent Minecraft version directories under Packwiz/.
# Shared Packwiz root files (README, scripts, mmc-export.toml) are preserved.
set -euo pipefail

KEEP_COUNT="${1:-3}"
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

if (( ${#versions[@]} <= KEEP_COUNT )); then
  echo "Keeping all ${#versions[@]} Packwiz version folder(s): ${versions[*]}"
  exit 0
fi

keep_start=$(( ${#versions[@]} - KEEP_COUNT ))
keep=("${versions[@]:keep_start}")
echo "Keeping Packwiz folders: ${keep[*]}"

for version in "${versions[@]:0:keep_start}"; do
  echo "Removing Packwiz/$version"
  rm -rf "$packwiz_dir/$version"
done
