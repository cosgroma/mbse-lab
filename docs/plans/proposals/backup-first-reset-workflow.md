# Feature: Backup-First Reset Workflow

Status: Proposed

Release Target: `v0.5.0` candidate

## Problem

Local Docker lab environments can reach bad states because of credential drift,
persistent data, stale containers, or service version changes. Recovery often
involves destructive commands, but service data may matter and users need a
safe, guided reset path.

## Rationale

Reset is a high-risk workflow because it crosses runtime persistence and private
model boundaries. A backup-first, dry-run-capable reset command would make
recovery safer while reinforcing the repo's rule that destructive actions need
explicit intent.

## Target Users

- Users recovering from broken local Flexo/SysON state.
- Maintainers validating service lifecycle changes.
- Users experimenting with disposable lab data.
- Future agents handling service reset tasks.

## Non-Goals

- Do not delete persisted data without explicit confirmation.
- Do not replace non-destructive `cleanup`.
- Do not update tracked Flexo startup seed data during normal reset.
- Do not promise production backup or disaster recovery semantics.

## Current Behavior And Evidence

- `mbse-lab cleanup` removes generated local output but preserves service data.
- `mbse-lab flexo backup` writes ignored backups by default.
- Updating tracked `cluster.nq` requires explicit high-intent flags.
- Doctor checks can identify credential drift and service problems.

## Proposed Behavior

Add a reset workflow that previews, backs up where possible, and then performs
explicitly selected reset actions.

Target-state command examples:

```text
mbse-lab services reset --dry-run
mbse-lab services reset --flexo --backup-first --i-understand-this-deletes-runtime-data
mbse-lab services reset --syson --i-understand-this-deletes-runtime-data
```

Reset scopes:

- Stop containers.
- Remove generated local output.
- Remove selected service data.
- Recreate local env files only when requested.
- Restart services and run readiness checks when requested.

## CLI, Docs, And API Impact

- Add a future `mbse-lab services reset` command.
- Document the difference between cleanup, restart, backup, and reset.
- Add clear confirmation flags and dry-run output.
- Update troubleshooting docs to route destructive recovery through reset.

## Data And Credential Safety

Reset must be explicit, dry-run-capable, and confirmation-gated. Flexo backup
should run before deleting Flexo runtime data unless the user explicitly opts
out. Failure output must make clear which private/runtime paths are affected.

## Validation Plan

- Add deterministic tests for dry-run plans and confirmation gates.
- Use temporary directories for data deletion tests.
- Test that tracked startup seed files are not modified by default.
- Run `make check`.
- Run live evals only when validating full service reset behavior.

## Acceptance Criteria

- Dry-run prints the exact planned actions and affected paths.
- Destructive reset requires explicit high-intent flags.
- Flexo backup-first behavior is the default for Flexo data reset.
- Cleanup and reset remain separate user concepts.
- Tests cover no-confirmation, dry-run, Flexo, SysON, and combined reset paths.

## Rollout And Compatibility Notes

Start with dry-run and confirmation plan generation before implementing live
deletion behavior. Keep existing cleanup, backup, and service lifecycle commands
unchanged.

## Open Decisions

- Should reset live under `services`, `flexo`, and `syson`, or only
  `services reset`?
- Should backup-first be mandatory for Flexo reset or just default?
- Should reset regenerate `.env` files or leave credentials untouched unless
  requested?
