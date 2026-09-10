#!/usr/bin/env bash
# After an upstream merge, drop Packwiz MC folders FO introduced that this fork
# did not already own — unless the folder is newer than our previous newest
# (a new Minecraft version we should adopt).
#
# Usage:
#   drop-unowned-packwiz.sh /path/to/owned-dirs.txt
# owned-dirs.txt: one Packwiz/<mc> folder name per line (from before the merge).
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
packwiz_dir="$repo_root/Packwiz"
owned_file="${1:?owned Packwiz dir list required}"

if [[ ! -d "$packwiz_dir" ]]; then
  echo "Packwiz directory not found at $packwiz_dir" >&2
  exit 1
fi

if [[ ! -f "$owned_file" ]]; then
  echo "Owned dirs file not found: $owned_file" >&2
  exit 1
fi

mapfile -t owned < <(grep -v '^[[:space:]]*$' "$owned_file" | sort -V)
declare -A owned_set=()
for ver in "${owned[@]}"; do
  owned_set["$ver"]=1
done

newest_owned=""
if ((${#owned[@]} > 0)); then
  newest_owned="${owned[-1]}"
fi

is_newer_than_newest_owned() {
  local candidate="$1"
  if [[ -z "$newest_owned" ]]; then
    return 0
  fi
  local top
  top="$(printf '%s\n%s\n' "$newest_owned" "$candidate" | sort -V | tail -n1)"
  [[ "$top" == "$candidate" && "$candidate" != "$newest_owned" ]]
}

mapfile -t present < <(
  find "$packwiz_dir" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort -V
)

echo "Owned Packwiz folders (pre-merge): ${owned[*]:-none}"
echo "Present after merge: ${present[*]:-none}"

dropped=0
for ver in "${present[@]}"; do
  if [[ -n "${owned_set[$ver]+x}" ]]; then
    echo "Keeping owned Packwiz/$ver"
    continue
  fi
  if is_newer_than_newest_owned "$ver"; then
    echo "Keeping new Minecraft Packwiz/$ver (newer than $newest_owned)"
    continue
  fi
  echo "Dropping unowned older Packwiz/$ver (FO-only; not previously kept by this fork)"
  rm -rf "$packwiz_dir/$ver"
  dropped=$((dropped + 1))
done

echo "Dropped $dropped unowned Packwiz folder(s)."
