# Feature Development Agent Prompt

Use this page when handing a proposal-backed feature to a fresh agent. The goal
is to give the agent enough repo context, planning context, safety boundaries,
and validation expectations to implement a focused feature without relying on
chat history.

For prompts with issue, proposal, and release details already filled in, use
the [Feature Development Prompt Pack](feature-development-prompt-pack.md).

## When To Use This Prompt

Use this prompt for work tied to:

- A GitHub feature issue.
- A proposal under `docs/plans/proposals/`.
- A release-plan issue.
- Any change that affects CLI workflows, bridge behavior, generated artifacts,
  credentials, service state, diagnostics, reports, release validation, or docs
  structure.

Small copy edits and narrow bug fixes do not need this full prompt unless they
touch one of those boundaries.

## Copyable Prompt

```text
You are working in the `cosgroma/mbse-lab` repository.

Task:
- Implement GitHub issue: <issue URL or number>
- Proposal doc: <docs/plans/proposals/...md>
- Release target: <v0.x.y candidate or unassigned>

Start by reading:
- `AGENTS.md`
- `README.md`
- `WORKFLOW.md`
- `docs/roadmap.md`
- `docs/plans/README.md`
- the proposal doc named above
- the GitHub issue named above

Repo identity:
- This repo is a local SysML v2 lab kit for Flexo MMS, SysON, and the
  snapshot bridge between them.
- It is reusable tooling, not the home for private SysML v2 models.
- Treat Flexo as the API-driven repository path and SysON as the graphical
  review/import path.
- Do not promise live repository sync or diagram round-trip.

Before implementation:
- Inspect `git status --short --branch`.
- Identify unrelated dirty worktree changes and leave them untouched.
- Restate the feature's problem, rationale, non-goals, acceptance criteria,
  data-safety impact, release target, and validation plan.
- If the feature is larger than one focused chunk or changes persistence,
  credentials, live-service behavior, or bridge contracts, create or update an
  active plan under `docs/plans/active/`.

Implementation rules:
- Follow existing repo patterns and command surfaces.
- Prefer `mbse-lab` for user-facing workflows.
- Keep compatibility wrappers stable unless the issue explicitly changes them.
- Add tests proportional to risk.
- Keep generated private artifacts out of this repo.
- Use `MBSE_MODEL_WORKSPACE` or explicit output paths when generated model
  artifacts are involved.
- Do not commit runtime `.env` files, service data, diagnostics bundles, run
  logs, private Flexo JSON exports, private `.sysml` snapshots, or real model
  source.
- Do not update tracked Flexo startup seed data unless the task explicitly
  calls for synthetic publishable seed data and uses the high-intent backup
  path.

Validation expectations:
- Run focused tests while iterating.
- Run `make docs-check` when docs, snippets, navigation, or CLI docs change.
- Run `make workflow-check` when workflow or agent policy changes.
- Run `make docs-build` when MkDocs navigation or larger docs content changes.
- Run `make share-check` when data, credentials, artifacts, diagnostics,
  reports, backups, or workspace behavior changes.
- Run `make check` before handing off normal repo changes.
- Run `make live-eval` and `make deployment-verify` only when live Flexo/SysON
  behavior is changed and services are available.

Handoff expectations:
- Summarize what changed and why.
- List the files changed.
- Report validation commands that passed or explain blockers.
- Mention any residual uncommitted worktree state.
- Note the next recommended issue or chunk.
- If GitHub issue state should change, say exactly which issue and why.
```

## Fresh-Agent Checklist

Use this checklist before editing files:

- The issue and proposal agree on scope.
- The release target is known or explicitly unassigned.
- Acceptance criteria are concrete and testable.
- Non-goals are clear.
- Private-data and credential impact has been reviewed.
- Required validation commands are known.
- Any live-service dependency is explicit.
- Any docs or CLI compatibility impact is identified.

Use this checklist before handoff:

- The intended change is implemented.
- Relevant docs and generated references are updated.
- Tests or checks cover the risky behavior.
- `make check` passed, or blockers are stated.
- `make share-check` passed when safety boundaries changed.
- Unrelated user work was left untouched.
- The final note names residual risk and the next useful step.

## Scope Triage

If a fresh agent finds that the issue is too broad, split the work this way:

| Chunk | Good boundary |
| --- | --- |
| Design or pre-plan | Clarify proposal, release target, acceptance criteria, and data-safety impact. |
| CLI surface | Add command/options and dry-run or JSON output shape without live mutation. |
| Core behavior | Implement the deterministic domain logic and tests. |
| Safety gate | Add workspace, share-check, public-safe, credential, or reset guards. |
| Evidence | Add reports, manifests, logs, or coverage outputs without embedding private content. |
| Docs | Update README, user guide, CLI reference, roadmap, or proposal status. |
| Live validation | Run service-dependent checks and record evidence only after deterministic checks pass. |

Prefer completing one focused chunk with validation over partially editing
several layers.

## GitHub Coordination

Milestones answer which release the work targets. The GitHub Project answers
what state the work is in. Labels describe the kind of work and risk.

For proposal-backed features:

- Keep the feature issue linked to its proposal doc.
- Keep the release-plan issue checklist current when feature scope moves.
- Use `status/proposed` until the feature is accepted for implementation.
- Use `status/ready` only when acceptance criteria and validation are clear.
- Keep `risk/data-safety`, `risk/service-state`, `risk/docs-drift`, or
  `risk/false-confidence` labels when they explain review focus.

Do not close a proposal-backed feature issue only because a design doc exists.
Close it when the accepted implementation and validation have landed, or when
the feature is explicitly rejected or superseded.
