# ai-loadout

Personal collection of AI coding **subagents**, **skills**, and Claude Code **mods**, kept in one place
so they can be versioned, shared, and reused across AI coding harnesses.

## Structure

```
ai-loadout/
├── install.sh        # symlinks agents and skills into their live locations
├── .claude-plugin/   # marketplace.json listing the mods
├── agents/           # *.agent.md subagents
├── skills/           # one folder per skill, each containing a SKILL.md
└── mods/             # one Claude Code plugin of function hooks per folder
```

## Contents

### Agents

| Agent | Purpose |
|-------|---------|
| `pr-code-quality` | Reviews idioms, style consistency, design patterns, architectural fit |
| `pr-issue-alignment` | Verifies PR changes align with a GitHub issue's requirements |
| `pr-performance` | Finds performance bottlenecks, scalability and concurrency risks |
| `pr-review` | Comprehensive PR review orchestrating the above |

### Skills

| Skill | Description |
|-------|-------------|
| `code-quality-review` | Evaluate code idioms, style, design patterns, and architectural fit |
| `issue-alignment` | Verify PR changes align with a GitHub issue's requirements |
| `performance-review` | Find performance bottlenecks, scalability and concurrency risks |
| `fantasy-waiver-sweep` | Weekly Sleeper waiver sweep: bench audit, league-winner pickups, bids, streamers |
| `fantasy-start-sit` | Start/sit, waiver, and streaming calls from a lineup or matchup screenshot |
| `golf-swing-analysis` | Coaching feedback from swing videos or golf-etl sessions |

### Private context

Skills hold nothing personal. A skill that needs to know who you are (your
leagues, where your golf sessions live) reads an optional
`~/.agents/context/<skill>.md`, and anything in it overrides the skill's
defaults. It lives outside the skill folder, so installing or upgrading a skill
leaves it alone. `context.example.md` in the skill folder lists the fields.
Without it, the skill takes what it needs from the conversation or asks.

### Mods

Claude Code only. Each mod is a plugin whose hooks module runs inside the session.

| Mod | Description |
|-----|-------------|
| `checkout-guard` | Shows a band when another Claude session is working in the same git checkout and blocks `checkout`, `switch`, `rebase`, `pull`, `merge`, `stash`, `reset --hard`, `clean`, and `restore` there. Subagents started in a worktree are left alone |
| `pr-session` | Renames the session `pr-<repo>-<number>` after the first PR it mentions, unless you named it yourself. Adds `/handoff [note]`, which writes `~/.claude/handoffs/<repo>/<session>.md` for a fresh session to pick up, and `/resume-handoff [name or number]` to list or load them |
| `session-info` | Adds `<repo>:<branch> · k8s:<kubectl context> · <model> <effort>` to the dim hint line under the prompt, leaving out whatever is unknown. Repo and kube context refresh every 15s and around each turn, effort comes from the request the turn sends |

A new mod needs a folder under `mods/` and an entry in
`.claude-plugin/marketplace.json`. To check one:

```bash
claude plugin validate mods/<name>
claude plugin test mods/<name>
```

### Always-on instructions

A skill whose frontmatter carries `metadata.applyTo` is personal *context* (voice, style,
standing preferences) rather than a procedure to run on request. Claude Code
discovers it by `description` at run time like any other skill, but Copilot has no
on-demand skill discovery, so `install.sh` also generates an always-on
`<name>.instructions.md` for it in the VS Code prompts directories (local and
Remote).

Skill frontmatter sticks to the fields in the
[Agent Skills specification](https://agentskills.io/specification), so anything
harness-specific goes under `metadata`.

Claude Code only consults such a skill when the task matches its description. Rules that must apply to *every* reply (no em dashes) belong in
`~/.claude/CLAUDE.md`, which is loaded into every session.

## Portability across harnesses

The canonical source of truth is the files in this repo:

- `agents/*.agent.md` — agent prompt bodies with Copilot-style frontmatter
- `skills/*/SKILL.md` — reusable skill procedures

The **prompt bodies and skills are plain Markdown** and transfer across harnesses
unchanged. Only the agent *frontmatter* is harness-specific:

| | GitHub Copilot | Claude Code | Windsurf |
|---|---|---|---|
| Agent file | `*.agent.md` | `*.md` | `*.md` (workflow) |
| `tools` field | `[read, search, web, execute, agent]` | `Read, Grep, Glob, WebFetch, WebSearch, Bash` | — |
| Delegation | `agents:` + skill IDs | main-thread subagents + model-invoked skills | — |

`install.sh` handles this: Copilot and Windsurf consume the canonical files via
symlink, while for Claude Code it **generates** adapted subagents (rewriting the
`tools` list to Claude Code's PascalCase tool names, dropping Copilot-only keys,
and using `<name>.md` filenames). The comprehensive review workflow includes a
direct skill-based fallback for harnesses without nested delegation, and a
GitHub CLI fallback for harnesses without GitHub-native tools.

## Install

```bash
./install.sh
```

This installs into each harness's live locations:

| Harness | Agents | Skills |
|---------|--------|--------|
| **GitHub Copilot** | `~/Library/Application Support/Code/User/prompts/` on macOS or `~/.config/Code/User/prompts/` elsewhere (VS Code), `~/.config/copilot/agents/` and `~/.copilot/agents/` (CLI) — symlinked | `~/.copilot/skills/` — symlinked |
| **Windsurf** | `~/.codeium/windsurf/global_workflows/` — symlinked | (delivered as workflows) |
| **Claude Code** | `~/.claude/agents/` — generated | `~/.claude/skills/` — symlinked |
| **Other Agent Skills harnesses** | none | `~/.agents/skills/` (symlinked) |

For Claude Code it also adds this repo as the `rumstead-ai-loadout` plugin
marketplace and installs every mod in it at user scope. The mods are read in place
from `mods/`, so an edit takes effect at the next session start or `/reload-plugins`.

Plus `~/.config/Code/User/prompts/` and `~/.vscode-server/data/User/prompts/`
(generated `*.instructions.md` for any skill marked `metadata.applyTo`).

To install skills without a checkout, on any machine:

```bash
npx skills add rumstead/ai-loadout -g            # every skill, from main
npx skills add https://github.com/rumstead/ai-loadout/tree/<tag>/skills/<skill> -g   # one skill at a release
```

## Releases

Each skill and each mod is versioned on its own. release-please keeps a release
PR open from conventional commits on `main`. Merging it tags each changed skill
or mod as `<name>-v<version>`, bumps `metadata.version` in its `SKILL.md` (or
`version` in its `plugin.json`), and writes its `CHANGELOG.md`. A skill release
also carries `<skill>.zip` for uploading to claude.ai.

## Checks

Every PR runs the Agent Skills validator (`skills-ref`), `claude plugin validate`
and `claude plugin test` on the mods, shellcheck on `install.sh`, and gitleaks
with an extra rule for Sleeper IDs.

Evals run only on a PR labeled `run-evals`, and again on each push while the
label stays. They use promptfoo with the Claude Agent SDK against
`evals/promptfooconfig.yaml`, on Sonnet unless an `eval-model:opus` or
`eval-model:haiku` label says otherwise. They authenticate with a
`CLAUDE_CODE_OAUTH_TOKEN` repo secret (from `claude setup-token`, billed to
your Claude plan) or an `ANTHROPIC_API_KEY` one, and read
`WAIVER_SWEEP_CONTEXT`, the contents of your waiver sweep context file. To run them locally:

```bash
cd evals && npx -p promptfoo@0.125.1 -p @anthropic-ai/claude-agent-sdk@0.3.316 promptfoo eval
```

## License

[MIT](LICENSE)
