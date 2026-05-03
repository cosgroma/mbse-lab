# Feature: Bridge Import Preflight

Status: Proposed

Release Target: `v0.4.0` candidate

## Problem

Users can run a bridge import and later discover that the render was empty,
unsupported element coverage was high, the target SysON namespace was wrong, or
services were not ready. The bridge has evidence after a run, but users need a
clear "should I import this?" check before modifying a SysON project.

## Rationale

Preflight lowers the risk of confusing or low-value imports. It fits the lab's
evidence-first posture by turning existing renderer, workspace, and service
checks into a decision point: safe to import, import with warnings, or blocked.

## Target Users

- Users importing existing Flexo projects into SysON.
- Maintainers testing bridge behavior with new fixtures.
- Technical leads reviewing whether a bridge run is representative.
- Users working with private model artifacts who need output-path safety.

## Non-Goals

- Do not import or mutate SysON state during preflight.
- Do not guarantee SysON graphical layout quality.
- Do not hide unsupported elements; report them directly.
- Do not replace full bridge run logs or render reports.

## Current Behavior And Evidence

- `mbse-lab bridge render` can produce a render coverage report.
- `mbse-lab bridge run` can create/import into a SysON review project.
- `doctor` and service commands already know how to check local service
  readiness.
- Private workspace warnings exist for generated artifacts.

## Proposed Behavior

Add a bridge preflight workflow that checks the input snapshot, renderability,
artifact placement, optional SysON target context, and service readiness without
performing an import.

Target-state command examples:

```text
mbse-lab bridge preflight export.json
mbse-lab bridge preflight export.json --syson-project-id <project-id> --namespace-id <root-id>
mbse-lab bridge preflight export.json --json-output
```

Preflight outcomes:

- `passed`: import is likely useful.
- `warning`: import can proceed, but coverage or target context needs review.
- `blocked`: import should not proceed until a concrete issue is fixed.

## CLI, Docs, And API Impact

- Add a future `mbse-lab bridge preflight` command.
- Add JSON output for automated workflows.
- Document how preflight relates to render reports, bridge runs, and doctor.
- Consider integrating preflight into `bridge run` as an automatic first step.

## Data And Credential Safety

Preflight reads model snapshots and may expose private model structure. JSON and
terminal outputs should summarize counts and warnings by default. Any generated
preflight reports should follow private workspace output policy.

## Validation Plan

- Add deterministic fixtures for valid, empty, unsupported-heavy, and malformed
  snapshots.
- Mock SysON target checks for project/root validation.
- Test workspace policy outcomes.
- Run `make docs-check` and `make check`.
- Run live evals only when integrating real service readiness checks.

## Acceptance Criteria

- Preflight reports snapshot validity, render coverage, unsupported counts, and
  output-path safety.
- Optional SysON context checks do not mutate the project.
- JSON output includes stable outcome codes and next actions.
- `blocked` and `warning` states are deterministic in tests.

## Rollout And Compatibility Notes

This should be additive. Once stable, `bridge run` can call the preflight logic
internally while keeping an override for advanced workflows.

## Open Decisions

- What unsupported-element threshold should turn a pass into a warning?
- Should an empty render be blocked or warning-only?
- Should preflight write a report file by default or only when requested?
