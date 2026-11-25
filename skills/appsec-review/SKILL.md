---
name: appsec-review
description: "Use whenever asked for a security review, or to check code, a file, a diff, a PR, dependencies, or a CI workflow for vulnerabilities, even for one small file with no obvious attack surface. Finds broken authorization, injection, path traversal, SSRF, leaked secrets, weak crypto, risky dependencies, and unsafe GitHub Actions workflows."
license: MIT
metadata:
  version: "0.1.0" # x-release-please-version
---

# Application Security Review

## When to Use

- A change touches handlers, auth, sessions, input parsing, or anything built from input
- A change adds or bumps dependencies
- A change edits CI workflows, Dockerfiles, infrastructure as code, or access policy

Logic bugs with no attacker belong to `correctness-review`, and resource exhaustion under normal load to `performance-review`. Note those in one line under Handed Off.

## Procedure

Read only. Do not run scanners, exploits, or requests against live systems.

### 1. Map the Attack Surface

Before looking for bugs, write down for the changed code:

- **Entry points**: HTTP routes, RPC methods, message consumers, CLI arguments, files or archives read from users, webhooks, CI events
- **Who can reach them**: anonymous, any signed-in user, an admin, another service, a fork PR author
- **What they control**: which parameters, headers, bodies, file names, and event fields carry their values

Trace from each entry point to the changed code, and from each controlled value to every place it is used. A finding needs that path.

### 2. Authentication and Authorization

- Compare each changed handler with its peers. When peers check ownership, role, or tenant and the changed one does not, that is a finding (IDOR or missing authorization).
- New routes registered outside the auth middleware, or middleware that fails open on error
- Checks done on the client, or on an ID the caller supplies, instead of on the session's identity
- Session and token handling: expiry, rotation on login, comparison in constant time, cookies missing `HttpOnly`, `Secure`, or `SameSite`

### 3. Untrusted Input Reaching a Sink

| Sink | Vulnerability | What makes it safe |
|------|---------------|--------------------|
| SQL built from strings | Injection | Parameters or a query builder that binds values |
| Shell or `exec` with a shell | Command injection | Argument arrays, no shell, allow-listed values |
| File paths joined from input | Path traversal | `filepath.Join` does not stop `..`; check `filepath.IsLocal`, use `os.Root`, or resolve and confirm the prefix |
| Archive extraction | Zip slip | The same path checks on every entry name |
| HTML, templates | XSS | Context-aware auto-escaping, no raw insertion |
| Outbound URL from input | SSRF | Allow-listed hosts, blocked internal ranges after DNS resolution |
| Redirect target from input | Open redirect | Relative paths or allow-listed hosts only |
| Deserializing input | Object injection, decompression bombs | Safe formats, size limits |
| Regex built or run on input | ReDoS | Linear-time engines or bounded input |
| Response headers from input | Header injection | Reject CR and LF |

### 4. Secrets and Cryptography

- Secrets committed, logged, put in URLs, or returned in responses or errors
- Non-cryptographic random used for tokens, IDs, or nonces
- Hand-rolled crypto, ECB mode, static IVs, MD5 or SHA-1 for passwords or signatures
- TLS verification turned off

### 5. Data Exposure

- Responses that return more fields than the caller may see
- Error messages that reveal internals, stack traces, or whether an account exists
- Personal data or tokens written to logs

### 6. Dependencies

For each added or bumped dependency:

- Name matches the intended package (typosquats, look-alike scopes)
- Known advisories for the pinned version. Check OSV (`https://api.osv.dev/v1/query`) when web access is available, and say when it was not.
- Install scripts or a maintainer change in a package that does not need them

### 7. CI and Infrastructure

| Pattern | Risk |
|---------|------|
| `pull_request_target` or `workflow_run` that checks out or runs PR head code | Fork author runs code with the base repo's secrets and write token |
| `${{ github.event.* }}` (titles, branch names, bodies, comments) inside `run:` | Script injection: the value is pasted in before the shell parses it |
| `actions/checkout` without `persist-credentials: false` before running untrusted code | The token in `.git/config` is readable |
| Broad `permissions:` or none set | Token can write more than the job needs |
| Third-party actions on a tag instead of a commit SHA | A moved tag runs new code with your secrets |
| Containers running as root, secrets in image layers or build args | Escalation, leaked credentials |
| IaC or RBAC that widens access (`*` actions, public buckets, `0.0.0.0/0`) | Exposure beyond intent |

### 8. Report Only What an Attacker Can Reach

Each finding names the attacker, what they control, the path from entry point to sink with `file:line` for each hop, and what they gain. Drop it when the attacker would need the access the exploit grants. List concerns you checked and cleared under Checked, with the evidence.

## Severity

Use the canonical PR-review severity rubric (shared across all PR review agents; the orchestrator's copy wins on any disagreement):

- **Critical**: exploitable by an outside or low-privilege attacker for code execution, secret theft, auth bypass, or access to other users' data
- **High**: exploitable with conditions that are common in practice, or a missing control on a sensitive path
- **Medium**: defense in depth gaps that need another flaw to exploit
- **Low**: hardening and pinning with little direct risk

## Output Format

```markdown
## Security Summary

**Verdict**: ✅ No vulnerabilities found | ⚠️ Hardening gaps | ❌ Exploitable vulnerabilities

**Attack surface**: <entry points the change touches and who can reach them>

### Issues

| # | Severity | Category | File | Lines | Issue | Attack Path | Suggested Fix |
|---|----------|----------|------|-------|-------|-------------|---------------|
| 1 | Critical | Authorization | handlers.go | L57-67 | Delete has no owner check, unlike Get | Any signed-in user sends `DELETE /notes/{id}` with another user's note ID | Add `AND owner_id = $2` and return 404 when no row is deleted |

Category: Authentication, Authorization, Injection, Path Traversal, SSRF, Secrets, Crypto, Data Exposure, Dependencies, CI/CD, Infrastructure

### Checked
- <concerns examined and cleared, each with the evidence>

### Handed Off
- <one line per correctness or performance concern seen while tracing>
```
