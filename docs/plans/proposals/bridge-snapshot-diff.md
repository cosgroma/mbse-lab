# Feature: Bridge Snapshot Diff

Status: Proposed

Release Target: `v0.4.0` candidate

## Problem

The Flexo-to-SysON workflow is snapshot-based. Users can export and import model
snapshots, but they do not have a focused way to understand what changed
between two Flexo exports, two rendered SysML files, or two render reports
before updating a SysON review project.

## Rationale

A snapshot diff is aligned with the current bridge contract. It improves trust
in the file/text workflow without implying live repository synchronization or
round-trip behavior. It also creates reusable evidence for reviews, release
notes, and model handoffs.

## Target Users

- Systems engineers reviewing model changes before SysON import.
- Developers validating renderer behavior across fixture revisions.
- Maintainers evaluating bridge regressions.
- Technical leads comparing evidence across workflow runs.

## Non-Goals

- Do not implement live sync between Flexo and SysON.
- Do not attempt semantic model differencing in the first version.
- Do not compare diagram layout or graphical views.
- Do not embed private model content in public-safe summaries by default.

## Current Behavior And Evidence

- Bridge runs produce Flexo JSON exports, rendered `.sysml` snapshots, render
  reports, and run logs.
- Reports can surface latest bridge artifacts.
- Unsupported elements are preserved in raw exports but may be omitted from
  rendered text.

## Proposed Behavior

Add a bridge diff workflow that compares two compatible artifacts and reports
structural and textual deltas.

Target-state command examples:

```text
mbse-lab bridge diff old-export.json new-export.json
mbse-lab bridge diff old.render-report.json new.render-report.json --json-output
mbse-lab bridge diff old.sysml new.sysml --markdown-output diff.md
```

Initial comparison dimensions:

- Element counts by `@type`.
- Added, removed, and changed declared names.
- Supported, skipped, and unsupported count deltas.
- Rendered text diff summary.
- Artifact paths and source metadata.

## CLI, Docs, And API Impact

- Add a future `mbse-lab bridge diff` command.
- Add JSON and Markdown output schemas.
- Document public-safe behavior and private-content handling.
- Consider adding diff summaries to reports or evidence bundles later.

## Data And Credential Safety

Diffs may reveal private model names and structure. Default terminal output
should be concise. Public-safe mode should report counts, paths, statuses, and
type-level summaries without embedding model text or full element names.

Generated diff artifacts should follow the same private workspace policy as
other bridge evidence.

## Validation Plan

- Add deterministic fixture pairs with known added, removed, and changed
  elements.
- Test JSON schema stability.
- Test public-safe summaries exclude model text.
- Run `make docs-check` and `make check`.

## Acceptance Criteria

- Users can compare two Flexo JSON exports and get element/type deltas.
- Users can compare two render reports and get coverage deltas.
- Users can compare two `.sysml` snapshots and get a textual summary.
- JSON output is deterministic for fixture inputs.
- Public-safe mode avoids embedding private model content.

## Rollout And Compatibility Notes

Start with shallow structural and textual diffing. Defer semantic SysML
differencing until the renderer coverage and model representation are more
complete.

## Open Decisions

- Should `.sysml` text diffing use standard unified diff output or a custom
  summary?
- Should diff support be limited to matching artifact kinds at first?
- Should diff summaries be integrated into `mbse-lab report` immediately or
  after the standalone command is stable?
