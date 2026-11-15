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
EVAL_WORKSPACE="$tmp/workspace" "$@"
