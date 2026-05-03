# Feature: Model-Like JSON Share Check

Status: Proposed

Release Target: `v0.3.0` candidate

## Problem

`share-check` blocks many known private artifact paths and model file suffixes,
but a private Flexo-style JSON export could still be force-added outside
obvious export directories. Path and suffix checks alone are not enough to catch
model-looking JSON in arbitrary tracked locations.

## Rationale

The strongest product boundary in this repo is "public tooling here, private
models elsewhere." A lightweight JSON heuristic adds another safety net for the
most likely private-data leak class without requiring a heavyweight secret or
model scanner.

## Target Users

- Users handling private SysML v2 models.
- Maintainers reviewing branches before publication.
- Release publishers running share checks.
- Future agents staging focused changes.

## Non-Goals

- Do not parse or validate full SysML v2 semantics.
- Do not flag curated public fixtures or explicitly public examples.
- Do not scan ignored runtime directories that are already outside git.
- Do not replace existing path, suffix, and secret-pattern checks.

## Current Behavior And Evidence

- `share-check` blocks forbidden tracked paths and generated export locations.
- `share-check` flags tracked `.sysml`, `.nq`, and `.trig` outside allowlists.
- Public fixtures and curated examples are intentionally allowed.
- JSON exports from Flexo can contain model names, element IDs, and structure.

## Proposed Behavior

Extend `share-check` to inspect tracked JSON files outside known public
allowlists. Flag files that look like private Flexo/SysML exports based on
structural markers.

Candidate markers:

- `source: flexo-sysmlv2`.
- Top-level `project`, `commit`, `roots`, or `elements`.
- Repeated `@type`, `@id`, `declaredName`, or `ownedRelationship` fields.
- Large arrays of SysML-like element objects.

Allowlists should remain explicit for public fixtures and examples.

## CLI, Docs, And API Impact

- Update `mbse-lab share-check` behavior and messages.
- Add docs explaining model-like JSON detection and allowlists.
- Add test fixtures for blocked private-looking JSON and allowed public fixture
  JSON.

## Data And Credential Safety

This feature only reads tracked JSON files in the working tree. It should not
print sensitive JSON content in failure messages. It should report file paths,
reason codes, and high-level marker names only.

## Validation Plan

- Add temporary-repo tests for tracked model-like JSON outside allowlists.
- Add tests for allowed `evals/fixtures/` and curated public example paths.
- Add tests that failure messages avoid dumping JSON content.
- Run `make share-check` and `make check`.

## Acceptance Criteria

- Tracked private-looking JSON outside allowlists fails `share-check`.
- Public fixture and curated example JSON remains allowed.
- Failure output names the file and high-level reason without dumping content.
- Tests cover positive, negative, and allowlisted cases.

## Rollout And Compatibility Notes

Start in blocking mode for high-confidence markers. If false positives appear,
split lower-confidence patterns into warnings before broadening coverage.

## Open Decisions

- Which JSON markers are high-confidence enough to block immediately?
- Should there be a documented inline allowlist mechanism, or only path-based
  allowlists?
- Should the heuristic inspect only tracked files, or also staged untracked
  files before commit?
