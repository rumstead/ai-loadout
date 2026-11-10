#!/usr/bin/env bash
set -euo pipefail

# Copies each shared file into the skills that ship it. A skill is released,
# zipped and installed as its own folder, so it carries a copy rather than a
# link. Edit the file under shared/, then run this. `--check` fails if a copy
# has drifted, which CI runs on every PR.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# shared file -> skills that ship it under scripts/
TARGETS=(
  "shared/fantasy/sleeper_data.py:fantasy-start-sit fantasy-waiver-sweep"
)

check=false
[[ "${1:-}" == "--check" ]] && check=true

status=0
for entry in "${TARGETS[@]}"; do
  src="${entry%%:*}"
  for skill in ${entry#*:}; do
    dest="skills/$skill/scripts/$(basename "$src")"
    if $check; then
      if ! cmp -s "$REPO_DIR/$src" "$REPO_DIR/$dest"; then
        echo "$dest differs from $src, run shared/sync.sh" >&2
        status=1
      fi
    else
      mkdir -p "$REPO_DIR/$(dirname "$dest")"
      cp "$REPO_DIR/$src" "$REPO_DIR/$dest"
      echo "copied $src to $dest"
    fi
  done
done
exit "$status"
