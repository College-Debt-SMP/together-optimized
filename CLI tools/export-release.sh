#!/usr/bin/env bash
# Export Together Optimized release artifacts (CurseForge zip + Modrinth mrpack)
# from the newest retained Packwiz Minecraft folder.
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
out_dir="${1:-$repo_root/dist}"
mkdir -p "$out_dir"

mapfile -t versions < <(
  find "$repo_root/Packwiz" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort -V
)
if [[ ${#versions[@]} -eq 0 ]]; then
  echo "No Packwiz version folders found." >&2
  exit 1
fi

newest="${versions[-1]}"
pack_dir="$repo_root/Packwiz/$newest"
pack_toml="$pack_dir/pack.toml"

version="$(python3 - <<PY
import tomllib
from pathlib import Path
data = tomllib.loads(Path("$pack_toml").read_text(encoding="utf-8"))
print(data["version"])
PY
)"

safe_version="${version//\//-}"
base_name="Together.Optimized-${safe_version}"
zip_path="$out_dir/${base_name}.zip"
mrpack_path="$out_dir/${base_name}.mrpack"

echo "Exporting from Packwiz/$newest (version $version)"
cd "$pack_dir"

rm -f "$zip_path" "$mrpack_path"
packwiz curseforge export -y -o "$zip_path"
packwiz modrinth export -y -o "$mrpack_path"

echo "ZIP=$zip_path"
echo "MRPACK=$mrpack_path"
echo "VERSION=$version"
echo "MC=$newest"
