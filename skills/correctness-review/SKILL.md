---
name: correctness-review
description: "Use whenever asked to check code, a file, a package, a diff, or a PR for bugs, to find bugs, or to say whether a change is correct or its tests cover it, even for one small file. Finds logic errors, unhandled edge cases, error-path mistakes, broken contracts with callers, and tests that would pass with the bug."
license: MIT
metadata:
  version: "0.1.0" # x-release-please-version
---

# Correctness Review

## When to Use

- Find inputs or states where changed code does the wrong thing
- Check that a changed function still meets what its callers expect
- Check whether the tests would fail if the change were wrong

Style and design belong to `code-quality-review`, performance and data races to `performance-review`, and vulnerabilities to `appsec-review`. When you see one of those while tracing, note it in one line under Handed Off rather than in the issues table.

## Procedure

Read the code; do not run it. Every finding comes from tracing the code by hand, so say which files and call sites you read.

### 1. Establish Each Contract

For every changed function, method, query, or config value, write down what it promises before judging it:

- **Stated contract**: doc comment, name, parameter and return types, and any spec or issue text the change cites
- **Callers' contract**: search for every call site and read it. Note the range of inputs callers actually send (validated upstream? clamped? user-controlled?) and what they do with outputs and errors
- **Tests' contract**: what the existing tests assert

When these disagree, the disagreement is the first thing to check. A function documented as 1-based whose tests pass 0 is a finding whichever side is wrong.

### 2. Walk the Inputs

For each changed function, run the inputs callers can send through the code by hand:

| Input class | Values to try |
|-------------|--------------|
| Boundaries | empty, zero, one, the last valid index, one past the end, max value, overflow |
| Absent values | nil or null, missing map key, empty string, zero-value struct, unset config |
| Shape | duplicates, unsorted input, mixed case, Unicode, very long values |
| Sign | negative numbers where only positive are expected |
| Time | time zones, DST shifts, zero time, ordering of events |

Only try values a caller can actually send. If no caller can produce an input, it is not a finding, unless the function is exported with no in-repo callers, in which case judge it against its documented contract.

### 3. Check the Error Paths

- Errors swallowed, replaced with a success value, or logged and dropped
- The wrong error returned, or an error wrapped so callers' `errors.Is`/`except` checks stop matching
- Work half done when a later step fails: partial writes, state changed before validation, no rollback
- Cleanup skipped on the error path, or run twice
- Retries of operations that are not idempotent

### 4. Check Changed Contracts

When the change alters a signature, return value, default, error, or persisted format:

- Every caller handles the new behavior, including callers outside the diff
- Zero values and defaults still mean what callers assume
- Data already stored or sent in the old format still reads correctly
- Feature flags and config defaults reach the new path the way the PR says they do

### 5. Check State and Control Flow

- Inverted or off-by-one conditions, `&&` versus `||`, wrong comparison operator
- Early returns or `continue` that skip required work
- Shadowed variables, or a loop variable captured by reference
- Mutating an input the caller still uses
- Switches or matches missing a case the change introduced

### 6. Check the Tests

For each behavior the change adds or alters, ask: would a test fail if this were wrong?

- A test that passes with the bug present is a finding. Name the input and expected result that would catch it.
- A test that only exercises inputs no caller sends does not cover the change.
- Missing tests for changed behavior are one finding per behavior, not per file. Do not ask for coverage percentages.

### 7. Report Only What You Can Trigger

Each finding names a concrete trigger: the input or state, the path through the code, and the wrong result. If you cannot construct one, leave the concern out of the table. List it under Checked if it is something a reader would expect you to have looked at.

## Severity

Use the canonical PR-review severity rubric (shared across all PR review agents; the orchestrator's copy wins on any disagreement):

- **Critical**: data loss, corruption, or a crash in production on a normal path
- **High**: wrong results or broken functionality on a path callers use
- **Medium**: wrong behavior on a rare but reachable path, or a test gap that leaves changed behavior unchecked
- **Low**: edge cases no in-repo caller reaches today, or minor test improvements

## Output Format

```markdown
## Correctness Summary

**Verdict**: ✅ No bugs found | ⚠️ Bugs on rare paths | ❌ Bugs on normal paths

### Issues

| # | Severity | Category | File | Lines | Issue | Trigger | Suggested Fix |
|---|----------|----------|------|-------|-------|---------|---------------|
| 1 | High | Logic | pager.go | L6 | Offset treats 1-based page as 0-based, so page 1 skips the first page | `?page=1` returns items 21-40 | Start at (page-1)*size |
| 2 | Medium | Tests | pager_test.go | L9 | Only test passes page 0, which no caller sends, so it passes with the bug | `Page(items, 1, 2)` should return the first two items | Add cases for page 1, last page, past the end |

Category: Logic, Edge Case, Error Handling, Contract, State, Tests

### Checked
- <concerns examined and cleared, each with the evidence>

### Handed Off
- <one line per style, performance, or security concern seen while tracing, for the reviewer that owns it>
```
