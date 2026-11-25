#!/usr/bin/env bash
set -euo pipefail

title="$1"
slug="$(printf '%s' "$title" | tr '[:upper:] ' '[:lower:]-' | tr -cd 'a-z0-9-')"
curl -fsS -X POST "https://deploy.example.com/previews" \
  -H "Authorization: Bearer $DEPLOY_TOKEN" \
  -d "slug=$slug" -d "dir=dist"
