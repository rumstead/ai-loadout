#!/usr/bin/env bash
set -euo pipefail

# Prints the promptfoo flags that pick the eval cases a diff touches: nothing
# to run every case, `--filter-metadata skills=<a>,<b>` to run the cases tagged
# with those skills, or `none` when no case covers what changed.
#
#   evals/cases-for-diff.sh <base> <head>

base="$1"
head="$2"
config="$(dirname "${BASH_SOURCE[0]}")/promptfooconfig.yaml"

declare -A skills=()
while IFS= read -r path; do
  case "$path" in
    evals/promptfooconfig.yaml | evals/*.sh | evals/workspace/.claude/* | .github/workflows/evals.yml)
      exit 0
      ;;
    skills/*/*)
      name="${path#skills/}"
      skills["${name%%/*}"]=1
      ;;
    shared/fantasy/* | evals/workspace/fantasy/*)
      skills[fantasy-start-sit]=1
      skills[fantasy-waiver-sweep]=1
      ;;
    evals/workspace/golf/*)
      skills[golf-swing-analysis]=1
      ;;
    evals/workspace/*)
      skills[code-quality-review]=1
      ;;
  esac
done < <(git diff --name-only "$base" "$head")

covered=()
for skill in "${!skills[@]}"; do
  if grep -Eq "^      skills: \[.*\b${skill}\b" "$config"; then
    covered+=("$skill")
  fi
done

if ((${#covered[@]} == 0)); then
  echo none
else
  echo "--filter-metadata skills=$(IFS=,; echo "${covered[*]}")"
fi
