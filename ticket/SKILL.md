---
name: ticket
description: Work a Jira ticket end-to-end. Fetch the ticket via Atlassian MCP, plan with the user, branch from develop, implement with repo tooling, commit incrementally, and open a PR using the repo template when asked. Invoke as /ticket ABC-123.
---

# ticket

Drive a single Jira ticket from "just opened" to "PR up" in one consistent workflow. The user invokes as `/ticket <KEY>` (e.g. `/ticket ABC-123`).

## Input

One Jira ticket key, like `ABC-123`. If the user invoked without a key, ask for it.

## Step 1: Fetch the ticket

1. Look up the Atlassian cloudId once per session: `mcp__claude_ai_Atlassian__getAccessibleAtlassianResources` (no args). Reuse the returned `id`.
2. `mcp__claude_ai_Atlassian__getJiraIssue` with `issueIdOrKey: <KEY>`, `responseContentFormat: "markdown"`, and that `cloudId`.
3. Summarize to the user in 3-5 lines: title, status, the gist of the description, any acceptance criteria, the most recent comments. Do not dump the raw payload.

If the fetch fails (bad key, auth), report the error and stop.

## Step 2: Set up the branch

Check `git rev-parse --abbrev-ref HEAD`.

- If it already matches the ticket key (e.g. `ABC-123` for `ABC-123`), keep it.
- Otherwise:
  ```
  git checkout develop
  git pull --ff-only
  git checkout -b <KEY>
  ```

Never branch off `main`. The PR target is `develop` unless instructed otehrwise or the repo simply has no `develop`.

## Step 3: Plan in plan mode

Call `EnterPlanMode`. Build the plan against the ticket description and any acceptance criteria from comments. Cover all of:

- code changes
- tests to add or update
- docs (READMEs, operations guide, doxygen)
- dependencies (pin / version bumps)
- build and tooling impact (CMake, scripts, CI, pre-commit)

Surface loose ends in the plan rather than letting them surface at PR time. `ExitPlanMode` when the user approves.

## Step 4: Implement, committing as you go

Work the plan in small, logically grouped commits.

- Commit subject: `[<KEY>] <short summary>` (e.g. `[ABC-123] Ads parameters for memory configuration`).
- No `Co-Authored-By` trailer. No "Generated with Claude Code" footer.
- Run pre-commit before each commit: `pre-commit run --files <changed paths>`, or `pre-commit run --all-files` for cross-cutting changes. Re-run until clean.
- Run the relevant tests / builds for what changed. The repo's PR template points at `README.md` and `docs/operations_guide.md` for build and regression test instructions.
- Touch docs, deps, build, and tooling that the change implies. A feature without docs, an unpinned dep, or a script that silently broke is a loose end.

Do not push. Pushing is the user's call.

## Step 5: Pausing

If work pauses or hands off mid-ticket, post a short Jira comment with `mcp__claude_ai_Atlassian__addCommentToJiraIssue`:

- current state
- what's left
- branch name

Plain markdown only, no Jira wiki markup. Keep it short. Do not transition the ticket; transitions happen automatically off commits and PRs in this org.

## Step 6: Pull request

Only when the user has pushed and asked for the PR.

```
gh pr create --base develop --title "[<KEY>] <summary>" --body-file <tmpfile>
```

Body follows `.github/pull_request_template.md`:

- Summary line referencing the ticket and (if known from the Jira data) the parent epic.
- Base requirements checkboxes (Build, Test). Check only what was actually verified.
- A short `## Changes` section listing the salient deltas. Supplement the template, do not replace it.

No "Generated with Claude Code" footer unless the user asks for it.

## Operating notes

- Spartan prose and commit messages.
- No em dashes.
- `rg` if available, not `grep`.
- Python: `.venv/bin/python` by absolute path; activation does not persist across Bash calls.
- Don't document non-changes: if a doc section would say "nothing to do" or describe reverted behavior, delete it instead.
- Never push without an explicit user request.
- suggest bumping the minor, or patch version accordingly. A major change is possible but would be very clearly indicated.
