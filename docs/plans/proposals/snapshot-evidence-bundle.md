# Feature: Snapshot Evidence Bundle

Status: Proposed

Release Target: `v0.4.0` candidate

## Problem

Bridge runs can produce Flexo exports, rendered SysML, render reports, run logs,
diagnostics, and lab reports. These artifacts are useful, but a reviewer still
has to know which files matter and how to read them without exposing private
model content.

## Rationale

An evidence bundle makes the snapshot workflow reviewable. It gives technical
leads and maintainers a compact handoff artifact while preserving the repo's
safety boundary: include status, counts, paths, and warnings, not private model
text.

## Target Users

- Technical leads reviewing local lab results.
- Maintainers comparing bridge runs.
- Users handing off evidence from a private workspace.
- Release publishers collecting validation artifacts.

## Non-Goals

- Do not archive private model content by default.
- Do not replace diagnostics bundles for service failure analysis.
- Do not replace full run logs.
- Do not require live services to summarize existing artifacts.

## Current Behavior And Evidence

- `mbse-lab bridge run` writes structured run logs.
- Render reports summarize rendered, skipped, and unsupported elements.
- `mbse-lab report` can include latest bridge run evidence.
- Public-safe diagnostics can omit sensitive service/project details.

## Proposed Behavior

Add a workflow that reads a bridge run log and related artifacts, then writes a
compact public-safe evidence summary.

Target-state command examples:

```text
mbse-lab bridge evidence runs/flexo-to-syson/latest.json
mbse-lab bridge evidence runs/flexo-to-syson/latest.json --public-safe --output evidence.md
mbse-lab bridge evidence runs/flexo-to-syson/latest.json --json-output
```

Bundle contents:

- Run status and step outcomes.
- Artifact paths and hashes where useful.
- Render coverage counts and warnings.
- Import target IDs or redacted IDs in public-safe mode.
- Service/version metadata if available.
- Validation commands run or recommended.

## CLI, Docs, And API Impact

- Add a future `mbse-lab bridge evidence` command.
- Add Markdown and JSON evidence output.
- Link evidence bundles from `mbse-lab report` where appropriate.
- Document public-safe behavior.

## Data And Credential Safety

Public-safe mode must avoid embedding private model text, full Flexo exports,
rendered SysML content, project names, credentials, or logs. It may include
paths, counts, high-level warnings, hashes, and redacted IDs.

Private evidence mode can be more detailed but should still avoid credentials.

## Validation Plan

- Add fixture run logs and artifact summaries.
- Test Markdown and JSON output for no-run, success, warning, and failure
  states.
- Test public-safe output does not include fixture model text.
- Run `make docs-check` and `make check`.

## Acceptance Criteria

- A run log can be converted into deterministic Markdown and JSON evidence.
- Public-safe mode excludes private model content.
- Evidence includes artifact paths, render coverage counts, warnings, and
  import status.
- `mbse-lab report` can link to or summarize the latest evidence bundle without
  duplicating private content.

## Rollout And Compatibility Notes

Start as a standalone command over existing run logs. Integrate into bridge run
or report generation after the schema is stable.

## Open Decisions

- Should evidence bundles be stored under `runs/`, `reports/`, or a private
  workspace path by default?
- Should hashes be included by default for artifact integrity?
- How much SysON/Flexo ID detail should public-safe mode retain?
