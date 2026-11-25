#!/usr/bin/env bash
set -euo pipefail

# Runs a command with EVAL_WORKSPACE set to a copy of evals/workspace whose
# links are resolved, then removes the copy. promptfooconfig.yaml copies that
# directory again for each case, which only works when no link points outside it.
#
#   evals/with-workspace.sh npx promptfoo eval -c evals/promptfooconfig.yaml

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

cp -RL "$here/workspace" "$tmp/workspace"

# The PR review cases call the same Claude Code subagents an install writes.
"$here/../install.sh" --claude-agents "$tmp/workspace/.claude/agents"

# Each prs/<repo>/ holds base/, the tree on main, and heads/<branch>/, the files
# one PR adds or changes, plus MESSAGE (its commit message) and an optional
# DELETED (paths it removes). Each becomes a git repo at <repo>/ in the
# workspace, with main at base and one branch per head, left on main.
for src in "$tmp/workspace/prs"/*/; do
  [ -d "$src" ] || continue
  repo="$tmp/workspace/$(basename "$src")"
  g() { git -C "$repo" -c user.name=eval -c user.email=eval@example.com "$@"; }
  git init -q -b main "$repo"
  cp -R "$src/base/." "$repo/"
  g add -A
  g commit -qm "initial import"
  for head in "$src/heads"/*/; do
    g checkout -q -b "$(basename "$head")" main
    cp -R "$head/." "$repo/"
    rm "$repo/MESSAGE"
    if [ -f "$repo/DELETED" ]; then
      rm "$repo/DELETED"
      while IFS= read -r path; do g rm -q "$path"; done < "$head/DELETED"
    fi
    g add -A
    g commit -qm "$(cat "$head/MESSAGE")"
  done
  g checkout -q main
done
rm -rf "$tmp/workspace/prs"
EVAL_WORKSPACE="$tmp/workspace" "$@"
