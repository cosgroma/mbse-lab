# Feature: SysML Coverage Matrix Gate

Status: Proposed

Release Target: `v0.3.0` candidate

## Problem

The bridge renderer supports a practical subset of SysML v2, but support can
drift across renderer code, fixtures, docs, and user expectations. Import
success can also create false confidence if unsupported elements were preserved
in raw JSON but omitted from rendered text.

## Rationale

This is one of the highest-leverage bridge features because it makes support
claims auditable. A coverage matrix turns "the renderer supports these types"
into a testable contract: supported means documented, fixture-backed, and
asserted in deterministic checks.

## Target Users

- Maintainers adding renderer mappings.
- Developers using the bridge in transformation workflows.
- Technical leads evaluating what SysML content is proven.
- Users interpreting render reports and SysON import results.

## Non-Goals

- Do not expand SysML v2 support as part of the first matrix.
- Do not promise full semantic correctness for every listed type.
- Do not make live SysON import validation mandatory for every row at first.
- Do not replace render reports; the matrix should complement them.

## Current Behavior And Evidence

- The renderer declares supported element types in code.
- Deterministic fixtures exercise several bridge scenarios.
- Render reports include rendered, skipped, and unsupported counts.
- Modeling conventions document the supported subset at a human level.

## Proposed Behavior

Add a machine-readable coverage matrix that lists each relevant Flexo/SysML
element type, textual form, status, fixture coverage, deterministic test
coverage, and optional live import coverage.

Suggested statuses:

| Status | Meaning |
| --- | --- |
| `supported` | Rendered to textual SysML and covered by deterministic tests. |
| `partial` | Rendered with known limits documented in the row. |
| `preserved-only` | Preserved in Flexo JSON but not rendered to text. |
| `unsupported` | Known but intentionally not handled yet. |

Add a test that fails when the renderer support registry and coverage matrix
diverge.

## CLI, Docs, And API Impact

- Add a matrix source such as `docs/lab/sysml-coverage.yml` or
  `src/mbse_lab/bridge/capabilities.py`.
- Update modeling conventions and bridge docs to include a generated or
  synchronized coverage table.
- Keep the public CLI behavior unchanged for the first increment.
- Optionally expose the matrix later through `mbse-lab bridge capabilities`.

## Data And Credential Safety

The matrix should contain only public element-type metadata and references to
synthetic fixtures. It must not embed private model names, Flexo exports, SysON
IDs, or rendered private model text.

## Validation Plan

- Add deterministic tests that compare renderer support data with the matrix.
- Add fixture assertions for every `supported` row.
- Run `make docs-check` and `make check`.
- Run live import evals only for rows where live service evidence is practical.

## Acceptance Criteria

- Every renderer-supported element type has a matrix row.
- Every `supported` row names a fixture and deterministic assertion.
- Matrix and renderer support data cannot drift without a failing test.
- Modeling conventions link to or include the matrix.
- Unsupported and preserved-only rows are explicit.

## Rollout And Compatibility Notes

This is additive. It should land before broad renderer expansion so future
element mappings have a clear documentation and test gate.

## Open Decisions

- Should the source of truth live in docs YAML, Python registry code, or both?
- Should generated Markdown be committed, generated during docs build, or kept
  manually synchronized by tests?
- What minimum evidence is required before a row can be marked `supported`?
