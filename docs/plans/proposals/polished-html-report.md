# Feature: Polished HTML Report

Status: Proposed

Release Target: `v0.4.0` candidate

## Problem

`mbse-lab report` is useful, but the HTML output is still closer to a rendered
artifact dump than a polished evidence report. Technical leads and users doing
handoffs need a readable, scannable report that summarizes status without
embedding private model content.

## Rationale

Reports are the visible face of the lab's evidence-producing workflow. A better
HTML report improves demos, release handoffs, and troubleshooting while
reusing existing doctor, service, share-check, bridge, and diagnostics data.

## Target Users

- Technical leads evaluating the local lab.
- Users sharing public-safe workflow evidence.
- Maintainers reviewing release readiness.
- Users troubleshooting service and bridge runs.

## Non-Goals

- Do not embed private model text or full Flexo exports.
- Do not require a web server.
- Do not replace JSON report output.
- Do not build a dashboard or long-running UI.

## Current Behavior And Evidence

- `mbse-lab report` writes Markdown, HTML, and JSON outputs.
- Reports include local lab health and bridge evidence.
- Public-safe diagnostics already avoid sensitive service details.
- The current HTML can be improved without changing core workflows.

## Proposed Behavior

Render a structured HTML report with sections for:

- Overall status and timestamp.
- Doctor and service health.
- Container/runtime summary.
- Share-check status and warnings.
- Latest bridge run evidence.
- Render coverage counts and warnings.
- Diagnostics/report artifact links.

The report should remain static and file-based.

## CLI, Docs, And API Impact

- Keep `mbse-lab report` command shape stable.
- Improve HTML rendering internals.
- Preserve JSON output schema or version any changes explicitly.
- Update report docs and screenshots/examples if added later.

## Data And Credential Safety

The HTML report must not embed private model text, full JSON exports, rendered
SysML content, credentials, or sensitive logs by default. It may include paths,
counts, statuses, warnings, redacted IDs, and links to local artifacts.

## Validation Plan

- Add deterministic report rendering tests for empty, passing, warning, and
  bridge-run states.
- Test that private fixture model text is not embedded in HTML.
- Run `make docs-check` and `make check`.
- Manually inspect the generated report for layout readability.

## Acceptance Criteria

- HTML output has structured sections instead of a plain preformatted dump.
- Report remains readable without network access or a dev server.
- JSON output remains compatible or schema changes are documented.
- Tests prove private model content is not embedded by default.
- Docs describe report content and safety boundaries.

## Rollout And Compatibility Notes

This is additive from a user perspective, but internal rendering should be kept
small and dependency-light. Avoid adding a heavy web framework.

## Open Decisions

- Should Markdown remain the source and HTML be custom-rendered, or should
  report generation use a shared structured model first?
- Should local artifact links be relative, absolute, or both?
- Should report styling be embedded CSS or a minimal external asset?
