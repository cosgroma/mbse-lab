# Feature Proposals

Use this directory for feature pre-planning. A proposal is the place to decide
whether a feature is worth doing, what problem it solves, what is out of scope,
and what evidence will prove it is done.

Do not use proposals as implementation logs. Once a feature is approved and the
work spans multiple chunks, create an execution plan under
`docs/plans/active/`.

## When To Create A Proposal

Create a proposal before work that changes:

- CLI workflow shape or command compatibility.
- Persistence, credentials, generated artifacts, diagnostics, backup, cleanup,
  or share checks.
- Flexo/SysON bridge behavior, renderer coverage, or import evidence.
- Service lifecycle, live validation, release gates, or Docker runtime behavior.
- Public documentation structure or maintainer workflow policy.

Small bug fixes and narrow documentation edits do not need a proposal unless
they change one of those boundaries.

## Proposal Lifecycle

1. Copy [Feature Pre-Plan Template](feature-preplan-template.md).
2. Name the proposal with a short kebab-case feature name.
3. Fill in problem, users, non-goals, safety impact, validation, and acceptance
   criteria before implementation starts.
4. Link the proposal from the relevant GitHub issue, sprint-plan issue, or
   active execution plan.
5. Keep rejected or superseded proposals in this directory if they record a
   useful decision. Mark the status clearly at the top.

## Current Proposals

- [Feature Pre-Plan Template](feature-preplan-template.md)
