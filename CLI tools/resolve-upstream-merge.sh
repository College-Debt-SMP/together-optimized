#!/usr/bin/env bash
# Resolve predictable conflicts when merging Fabulously Optimized into this fork.
#
# Policy:
# - Fork-owned docs (CHANGELOG, INCLUDED-MODS): keep ours
# - MultiMC FO instance (intentionally removed): keep deletion
# - Packwiz modify/delete: restore upstream only when this fork already owned that
#   MC folder (HEAD had Packwiz/<ver>/); otherwise keep deletion (FO-only older tree)
# - Everything else: take upstream (theirs); drop-unowned-packwiz + rebrand/fork-mods
#   run afterward
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

if ! git rev-parse -q --verify MERGE_HEAD >/dev/null; then
  echo "Not in a merge; nothing to resolve." >&2
  exit 0
fi

mapfile -t unmerged < <(git diff --name-only --diff-filter=U)
if ((${#unmerged[@]} == 0)); then
  echo "No unmerged paths."
  exit 0
fi

keep_ours=(
  CHANGELOG.md
  INCLUDED-MODS.md
)

is_keep_ours() {
  local path="$1"
  local item
  for item in "${keep_ours[@]}"; do
    if [[ "$path" == "$item" ]]; then
      return 0
    fi
  done
  return 1
}

# Stages present for a path: e.g. "1 2 3" or "1 3 " (modify/delete).
stages_for() {
  git ls-files -u -- "$1" | awk '{print $3}' | sort -u | tr '\n' ' '
}

fork_owns_packwiz_version() {
  local ver="$1"
  git ls-tree -d --name-only HEAD "Packwiz/$ver" 2>/dev/null | grep -qx "Packwiz/$ver"
}

resolved=0
for path in "${unmerged[@]}"; do
  stages="$(stages_for "$path")"
  if is_keep_ours "$path"; then
    echo "ours (fork doc): $path"
    git checkout --ours -- "$path"
    git add -- "$path"
    resolved=$((resolved + 1))
    continue
  fi

  # modify/delete: deleted in ours (stage 2 missing), modified in theirs
  if [[ "$stages" == "1 3 " ]]; then
    case "$path" in
      MultiMC/*)
        echo "delete (fork removed): $path"
        git rm -f -- "$path" >/dev/null
        ;;
      Packwiz/*)
        ver="${path#Packwiz/}"
        ver="${ver%%/*}"
        if fork_owns_packwiz_version "$ver"; then
          echo "theirs (owned Packwiz/$ver): $path"
          git checkout --theirs -- "$path"
          git add -- "$path"
        else
          echo "delete (unowned Packwiz/$ver): $path"
          git rm -f -- "$path" >/dev/null
        fi
        ;;
      *)
        echo "theirs (restore upstream): $path"
        git checkout --theirs -- "$path"
        git add -- "$path"
        ;;
    esac
    resolved=$((resolved + 1))
    continue
  fi

  # modify/delete: deleted in theirs, modified in ours
  if [[ "$stages" == "1 2 " ]]; then
    echo "ours (upstream deleted): $path"
    git checkout --ours -- "$path"
    git add -- "$path"
    resolved=$((resolved + 1))
    continue
  fi

  echo "theirs (upstream): $path"
  git checkout --theirs -- "$path"
  git add -- "$path"
  resolved=$((resolved + 1))
done

remaining="$(git diff --name-only --diff-filter=U | wc -l | tr -d ' ')"
if [[ "$remaining" != "0" ]]; then
  echo "Unresolved conflicts remain:" >&2
  git diff --name-only --diff-filter=U >&2
  exit 1
fi

echo "Resolved $resolved conflict path(s)."
