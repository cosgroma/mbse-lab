# Roadmap

This roadmap is the durable planning index for `mbse-lab`. Use it to decide
what should be worked next, what is intentionally deferred, and which planning
artifact should be created before implementation starts.

The roadmap is not a replacement for GitHub issues or execution plans. GitHub
issues track backlog items and sprint work. Proposal documents capture feature
shape before execution. Active plans track multi-chunk implementation.

## Product Direction

`mbse-lab` is a CLI-first, safety-first local SysML v2 lab kit. Its job is to
help users bootstrap Flexo MMS and SysON locally, keep real model data outside
the tooling repo, move conservative Flexo snapshots into SysON, and collect
evidence that the workflow is working.

## Roadmap Themes

| Theme | Purpose | Planning gate |
| --- | --- | --- |
| First-use success path | Make install, bootstrap, smoke, report, and share-check easy to run and easy to understand. | Any CLI workflow change needs acceptance criteria and deterministic tests. |
| Public/private model safety | Keep private SysML source, exports, snapshots, logs, credentials, and service data out of this repo. | Any artifact, credential, diagnostics, backup, or cleanup change needs a data-safety review. |
| Bridge evidence and SysML coverage | Show what the bridge rendered, skipped, imported, and did not support. | Any renderer expansion needs fixture coverage, render assertions, and documentation. |
| Live validation and release confidence | Keep service-dependent workflows repeatable without making every PR depend on Docker runtime behavior. | Live checks stay optional/manual unless they are deterministic and cheap enough for CI. |
| Maintainer architecture | Keep the CLI, bridge, deployment helpers, diagnostics, and reports easy to extend. | Refactors should preserve command compatibility and JSON output contracts unless explicitly versioned. |
| Expanded SysML v2 usefulness | Grow examples, coverage, and model workflow support after safety and evidence gates are stable. | New modeling scope needs an explicit non-goal list and validation plan. |

## Now

These are the preferred near-term bets.

| Item | Outcome | Evidence required |
| --- | --- | --- |
| Fixture-driven SysML coverage | Every supported renderer type is tied to a fixture, matrix row, and deterministic test. | `make check`, coverage matrix update, fixture assertions. |
| Recursive Python/static validation | Package submodules are covered by compile/static checks as the codebase grows. | `make check` covers all tracked Python files or an equivalent recursive path. |
| Nested CLI docs validation | Documentation checks validate `mbse-lab` groups, subcommands, and options, not only top-level commands. | A stale nested command or option fails `make docs-check`. |
| Planning system cleanup | Roadmap, proposals, active plans, and completed plans have clear ownership. | `make workflow-check`, `make docs-check`, updated plan index. |

## Next

These should follow once the near-term planning and validation gaps are closed.

| Item | Outcome | Evidence required |
| --- | --- | --- |
| Stricter private workspace policy | Model-generating commands require `MBSE_MODEL_WORKSPACE`, explicit output paths, or explicit repo-export intent. | CLI tests for workspace-set, explicit-output, and blocked/default cases. |
| Model-like JSON share checks | Force-added Flexo/SysML-looking JSON outside curated allowlists is flagged before sharing. | Temporary-repo share-check tests. |
| Better HTML report | `mbse-lab report` produces a readable HTML evidence report without embedding private model content. | Report tests for empty, passing, warning, and bridge-run states. |
| Scheduled live smoke evaluation | External image and runtime drift are caught on a conservative cadence. | Manual/scheduled workflow, public-safe diagnostics on failure. |

## Later

These are useful only after the core workflow remains stable.

| Item | Outcome | Entry condition |
| --- | --- | --- |
| Endpoint and workspace profiles | Advanced users can switch between local and experimental remote endpoints. | Local Docker workflow remains the documented default. |
| Backup-first reset workflow | Users can recover from local service state problems without accidental data loss. | Backup, dry-run, and confirmation behavior is designed and tested. |
| Renderer registry | Adding a SysML element renderer becomes a focused module, fixture, test, and docs change. | Coverage reports and matrix are already established. |
| Example model gallery | Public synthetic examples demonstrate useful MBSE patterns. | Public/private export policy is explicit and enforced. |

## Out Of Scope

- Storing real/private SysML v2 models in this repository.
- Production Flexo or SysON hosting.
- Full SysML v2 semantic execution.
- Bidirectional live sync between Flexo and SysON.
- Diagram layout round-trip between Flexo and SysON.
- Promise of full SysML v2 element coverage without fixture and import evidence.

## Planning Rules

Use a proposal in `docs/plans/proposals/` before work that changes:

- CLI workflow shape or command compatibility.
- Persistence, credentials, generated artifacts, diagnostics, backup, cleanup,
  or share checks.
- Flexo/SysON bridge behavior, renderer coverage, or import evidence.
- Service lifecycle, live validation, release gates, or Docker runtime behavior.
- Public documentation structure or maintainer workflow policy.

Create an active execution plan in `docs/plans/active/` when accepted work spans
multiple chunks, needs durable decisions, or carries data-safety or live-service
risk. Move completed plans to `docs/plans/completed/` with final validation and
outcome recorded.

## Review Cadence

Review this roadmap before opening a new sprint-plan issue, before a release
branch, and whenever an active plan is completed or abandoned. Update the
`Now`, `Next`, and `Later` sections with the smallest useful change.
