# Feature Development Prompt Pack

Use these filled prompts when handing release or proposal-backed feature work to
a fresh agent. They are concrete examples built from the generic
[Feature Development Agent Prompt](feature-development-agent-prompt.md).

Copy one complete prompt block into a fresh agent session. Before starting
implementation, verify that the linked GitHub issue is still open, assigned to
the expected milestone, and selected for the current work cycle.

## Prompt Selection

| Prompt | GitHub issue | Proposal | Release target | Best first chunk |
| --- | --- | --- | --- | --- |
| [v0.2.1 Release Closeout](#v021-release-closeout) | [#67](https://github.com/cosgroma/mbse-lab/issues/67) | Release plan issue | `v0.2.1` | Verify PR #72 satisfied the checklist, then prepare the release branch. |
| [SysML Coverage Matrix Gate](#sysml-coverage-matrix-gate) | [#31](https://github.com/cosgroma/mbse-lab/issues/31) | [sysml-coverage-matrix-gate.md](../plans/proposals/sysml-coverage-matrix-gate.md) | `v0.3.0` candidate | Matrix source of truth plus drift test. |
| [Model-Like JSON Share Check](#model-like-json-share-check) | [#59](https://github.com/cosgroma/mbse-lab/issues/59) | [model-like-json-share-check.md](../plans/proposals/model-like-json-share-check.md) | `v0.3.0` candidate | High-confidence blocking heuristic plus tests. |
| [Bridge Import Preflight](#bridge-import-preflight) | [#60](https://github.com/cosgroma/mbse-lab/issues/60) | [bridge-import-preflight.md](../plans/proposals/bridge-import-preflight.md) | `v0.4.0` candidate | Deterministic preflight outcome model before live checks. |

## v0.2.1 Release Closeout

Use this prompt when assigning a fresh agent to evaluate whether the `v0.2.1`
release-plan issue is complete and, if it is, prepare the release branch. This
is a release-closeout prompt, not a new feature prompt.

```text
You are working in the `cosgroma/mbse-lab` repository.

Task:
- Evaluate GitHub issue: https://github.com/cosgroma/mbse-lab/issues/67
- Confirm whether merged PR #72 completed the `v0.2.1` release-plan checklist.
- If the checklist is complete, prepare the `v0.2.1` release branch using the
  documented release process.
- Release target: `v0.2.1`

Start by reading:
- `AGENTS.md`
- `README.md`
- `WORKFLOW.md`
- `docs/roadmap.md`
- `docs/user-guide/release-process.md`
- `docs/lab/feature-development-agent-prompt.md`
- GitHub issue #67
- Merged PR #72

Repo identity:
- This repo is a local SysML v2 lab kit for Flexo MMS, SysON, and the snapshot
  bridge between them.
- It is reusable tooling, not the home for private SysML v2 models.
- Treat Flexo as the API-driven repository path and SysON as the graphical
  review/import path.
- Do not add new user-facing workflows, bridge behavior changes, stricter
  safety gates, or broad feature scope to `v0.2.1`.

Release context:
- Release promise: planning and maintainer hygiene.
- Candidate scope: roadmap/proposal docs, release planning docs, docs
  validation, workflow validation, and optional narrow maintainer checks only if
  already scoped and validated.
- Excluded scope: new CLI workflows, bridge behavior changes, and stricter
  safety gates.
- Latest relevant PR: #72, `[codex] Add roadmap planning process`, merged into
  `develop` on May 3, 2026.
- Initial assessment: #67 appears mostly complete after PR #72, but the issue
  checklist still needs explicit verification and GitHub updates.

Issue #67 checklist to verify:
- Roadmap and proposal docs are landed and discoverable.
- Release planning docs are linked from the procedural release process.
- Docs validation and workflow validation cover the new planning surfaces.
- Optional narrow maintainer checks are either complete or explicitly not
  selected for this release.
- Required evidence is current: `make check`, `make docs-build`, and
  `make share-check`.

Before release work:
- Inspect `git status --short --branch`.
- Fetch and align local `develop` with `origin/develop`.
- Identify unrelated dirty worktree changes and leave them untouched.
- Restate whether #67 is complete, partially complete, or blocked, with
  evidence from the repo and PR #72.
- If anything in #67 is incomplete, stop at a focused docs or validation fix
  instead of starting the release branch.

Implementation rules:
- Keep the release focused on planning and maintainer hygiene.
- Prefer docs, checklist, and validation updates over feature expansion.
- Follow `docs/user-guide/release-process.md`.
- Use the repo Git Flow policy: release branches target `main`, and after the
  release, `main` is synced back to `develop`.
- Do not commit runtime `.env` files, service data, diagnostics bundles, run
  logs, private Flexo JSON exports, private `.sysml` snapshots, or real model
  source.
- Do not update tracked Flexo startup seed data.

Validation expectations:
- Run `make docs-build`.
- Run `make share-check`.
- Run `make check`.
- Run any release-process commands required by
  `docs/user-guide/release-process.md`.
- Do not run live service evals unless the release process explicitly calls for
  them and services are available.

GitHub coordination:
- If #67 is complete, update the issue checklist or comment with the exact
  evidence and say it is ready for release branch work.
- If a release PR is opened, target `main` from a `release/v0.2.1` branch.
- Do not close #67 until the release branch has landed or the release plan is
  explicitly superseded.

Handoff expectations:
- Summarize whether #67 is complete and why.
- List any files changed.
- Report validation commands that passed or explain blockers.
- Mention any residual uncommitted worktree state.
- Name the release branch or PR if one was created.
- State the next action for issue #67.
```

## SysML Coverage Matrix Gate

```text
You are working in the `cosgroma/mbse-lab` repository.

Task:
- Implement GitHub issue: https://github.com/cosgroma/mbse-lab/issues/31
- Proposal doc: `docs/plans/proposals/sysml-coverage-matrix-gate.md`
- Release target: `v0.3.0` candidate
- Related release plan: https://github.com/cosgroma/mbse-lab/issues/68

Start by reading:
- `AGENTS.md`
- `README.md`
- `WORKFLOW.md`
- `docs/roadmap.md`
- `docs/plans/README.md`
- `docs/lab/feature-development-agent-prompt.md`
- `docs/plans/proposals/sysml-coverage-matrix-gate.md`
- GitHub issue #31 and release-plan issue #68

Repo identity:
- This repo is a local SysML v2 lab kit for Flexo MMS, SysON, and the
  snapshot bridge between them.
- It is reusable tooling, not the home for private SysML v2 models.
- Treat Flexo as the API-driven repository path and SysON as the graphical
  review/import path.
- Do not promise live repository sync, diagram round-trip, or full SysML v2
  coverage.

Feature context:
- Problem: bridge support claims can drift across renderer code, fixtures,
  docs, and user expectations. Import success can create false confidence when
  unsupported elements remain in raw JSON but are omitted from rendered text.
- Rationale: a coverage matrix makes "supported" auditable by tying each
  supported element type to documentation, synthetic fixtures, and
  deterministic assertions.
- Target users: maintainers adding renderer mappings, bridge workflow users,
  technical leads evaluating bridge evidence, and users interpreting render
  reports.
- Current issue labels to preserve unless scope changes: `type/feature`,
  `area/bridge`, `area/sysml`, `risk/false-confidence`, `status/proposed`.

Non-goals:
- Do not expand SysML v2 renderer support in this first increment.
- Do not promise full semantic correctness for each listed type.
- Do not make live SysON import validation mandatory for every row.
- Do not replace render reports; the matrix should complement them.

Acceptance criteria:
- Every renderer-supported element type has a matrix row.
- Every `supported` row names a fixture and deterministic assertion.
- Matrix and renderer support data cannot drift without a failing test.
- Modeling conventions link to or include the matrix.
- Unsupported and preserved-only rows are explicit.

Suggested first chunk:
- Identify the current renderer support source and fixture coverage.
- Choose the smallest durable matrix source of truth, such as docs YAML,
  Python registry data, or a documented combination.
- Add the drift test before broadening docs.
- Update modeling conventions only after the matrix shape is stable.

Data-safety impact:
- The matrix must contain only public element-type metadata and references to
  synthetic fixtures.
- Do not embed private model names, Flexo exports, SysON IDs, rendered private
  model text, diagnostics, or run logs.

Before implementation:
- Inspect `git status --short --branch`.
- Identify unrelated dirty worktree changes and leave them untouched.
- Restate the problem, rationale, non-goals, acceptance criteria, data-safety
  impact, release target, and validation plan.
- If the implementation spans multiple chunks or changes bridge contracts in a
  way that needs durable decisions, create or update an active plan under
  `docs/plans/active/`.

Implementation rules:
- Follow existing repo patterns and command surfaces.
- Prefer `mbse-lab` for user-facing workflows.
- Keep compatibility wrappers stable unless the issue explicitly changes them.
- Add tests proportional to risk.
- Keep generated private artifacts out of this repo.
- Use `MBSE_MODEL_WORKSPACE` or explicit output paths when generated model
  artifacts are involved.
- Do not update tracked Flexo startup seed data.

Validation expectations:
- Run focused renderer, fixture, and docs tests while iterating.
- Run `make docs-check` because modeling conventions or docs links should
  change.
- Run `make share-check` if any fixture, export, report, or artifact policy
  changes.
- Run `make check` before handing off.
- Run live import evals only for rows where live service evidence is practical
  and services are available.

Handoff expectations:
- Summarize what changed and why.
- List the files changed.
- Report validation commands that passed or explain blockers.
- Mention any residual uncommitted worktree state.
- Note whether issue #31 should move from `status/proposed` to `status/ready`,
  remain proposed, or close after implementation lands.
- Note any update needed in release-plan issue #68.
```

## Model-Like JSON Share Check

```text
You are working in the `cosgroma/mbse-lab` repository.

Task:
- Implement GitHub issue: https://github.com/cosgroma/mbse-lab/issues/59
- Proposal doc: `docs/plans/proposals/model-like-json-share-check.md`
- Release target: `v0.3.0` candidate
- Related release plan: https://github.com/cosgroma/mbse-lab/issues/68

Start by reading:
- `AGENTS.md`
- `README.md`
- `WORKFLOW.md`
- `docs/roadmap.md`
- `docs/plans/README.md`
- `docs/lab/feature-development-agent-prompt.md`
- `docs/plans/proposals/model-like-json-share-check.md`
- `docs/user-guide/safety-and-sharing.md`
- GitHub issue #59 and release-plan issue #68

Repo identity:
- This repo is a local SysML v2 lab kit for Flexo MMS, SysON, and the
  snapshot bridge between them.
- It is reusable tooling, not the home for private SysML v2 models.
- The strongest product boundary is "public tooling here, private models in a
  private workspace."

Feature context:
- Problem: `share-check` blocks many known private artifact paths and model
  suffixes, but a private Flexo-style JSON export could be force-added outside
  obvious export directories.
- Rationale: a lightweight JSON heuristic adds a safety net for likely private
  model leaks without requiring a full model scanner.
- Target users: users handling private SysML v2 models, maintainers reviewing
  branches, release publishers, and future agents staging focused changes.
- Current issue labels to preserve unless scope changes: `type/feature`,
  `area/safety`, `area/workspace`, `risk/data-safety`, `status/proposed`.

Non-goals:
- Do not parse or validate full SysML v2 semantics.
- Do not flag curated public fixtures or explicitly public examples.
- Do not scan ignored runtime directories that are already outside git.
- Do not replace existing path, suffix, and secret-pattern checks.

Acceptance criteria:
- Tracked private-looking JSON outside allowlists fails `share-check`.
- Public fixture and curated example JSON remains allowed.
- Failure output names the file and high-level reason without dumping content.
- Tests cover positive, negative, and allowlisted cases.

Suggested first chunk:
- Find the current `share-check` implementation and tests.
- Add high-confidence structural markers first, such as `source:
  flexo-sysmlv2`, top-level `project`/`commit`/`roots`/`elements`, repeated
  `@type`, `@id`, `declaredName`, or `ownedRelationship` fields.
- Keep lower-confidence patterns out of blocking mode until false-positive
  risk is better understood.
- Preserve explicit allowlists for public fixtures and examples.

Data-safety impact:
- The scanner should read only tracked JSON files in the working tree.
- Failure messages must not print sensitive JSON content.
- Output should report file paths, reason codes, and high-level marker names
  only.

Before implementation:
- Inspect `git status --short --branch`.
- Identify unrelated dirty worktree changes and leave them untouched.
- Restate the problem, rationale, non-goals, acceptance criteria, data-safety
  impact, release target, and validation plan.
- If the work changes share-check policy in a way that needs durable decisions,
  create or update an active plan under `docs/plans/active/`.

Implementation rules:
- Follow existing repo patterns and command surfaces.
- Keep `mbse-lab share-check` as the user-facing command.
- Keep compatibility wrappers stable unless the issue explicitly changes them.
- Add temporary-repo tests for tracked model-like JSON and allowlisted JSON.
- Keep generated private artifacts out of this repo.
- Do not commit runtime `.env` files, service data, diagnostics bundles, run
  logs, private Flexo JSON exports, private `.sysml` snapshots, or real model
  source.

Validation expectations:
- Run focused share-check tests while iterating.
- Run `make share-check` because this changes a safety boundary.
- Run `make docs-check` if docs or command snippets change.
- Run `make check` before handing off.

Handoff expectations:
- Summarize what changed and why.
- List the files changed.
- Report validation commands that passed or explain blockers.
- Mention any residual uncommitted worktree state.
- Note whether issue #59 should move from `status/proposed` to `status/ready`,
  remain proposed, or close after implementation lands.
- Note any update needed in release-plan issue #68.
```

## Bridge Import Preflight

```text
You are working in the `cosgroma/mbse-lab` repository.

Task:
- Implement GitHub issue: https://github.com/cosgroma/mbse-lab/issues/60
- Proposal doc: `docs/plans/proposals/bridge-import-preflight.md`
- Release target: `v0.4.0` candidate
- Related release plan: https://github.com/cosgroma/mbse-lab/issues/69

Start by reading:
- `AGENTS.md`
- `README.md`
- `WORKFLOW.md`
- `docs/roadmap.md`
- `docs/plans/README.md`
- `docs/lab/feature-development-agent-prompt.md`
- `docs/plans/proposals/bridge-import-preflight.md`
- `docs/lab/flexo-syson-bridge.md`
- `docs/user-guide/private-model-workspaces.md`
- GitHub issue #60 and release-plan issue #69

Repo identity:
- This repo is a local SysML v2 lab kit for Flexo MMS, SysON, and the
  snapshot bridge between them.
- It is reusable tooling, not the home for private SysML v2 models.
- Treat Flexo as the API-driven repository path and SysON as the graphical
  review/import path.
- Preflight must not imply live sync, diagram round-trip, or guaranteed SysON
  graphical layout quality.

Feature context:
- Problem: users can run a bridge import and only later discover that the
  render was empty, unsupported element coverage was high, the target SysON
  namespace was wrong, services were not ready, or output paths were unsafe.
- Rationale: preflight turns existing renderer, workspace, and service checks
  into a decision point before SysON state is modified.
- Target users: users importing Flexo projects into SysON, maintainers testing
  bridge behavior, technical leads reviewing bridge evidence, and users
  handling private model artifacts.
- Current issue labels to preserve unless scope changes: `type/feature`,
  `area/bridge`, `area/safety`, `risk/false-confidence`, `status/proposed`.

Non-goals:
- Do not import or mutate SysON state during preflight.
- Do not guarantee SysON graphical layout quality.
- Do not hide unsupported elements; report them directly.
- Do not replace full bridge run logs or render reports.

Acceptance criteria:
- Preflight reports snapshot validity, render coverage, unsupported counts, and
  output-path safety.
- Optional SysON context checks do not mutate the project.
- JSON output includes stable outcome codes and next actions.
- `blocked` and `warning` states are deterministic in tests.

Suggested first chunk:
- Define the deterministic outcome model first: `passed`, `warning`, and
  `blocked`, with stable reason codes.
- Implement input snapshot, renderability, unsupported-count, and workspace
  safety checks before live SysON readiness checks.
- Add mocked SysON target-context checks before attempting live validation.
- Keep any future `bridge run` integration separate unless this issue
  explicitly grows to include it.

Data-safety impact:
- Preflight reads model snapshots and may expose private model structure.
- Terminal and JSON output should summarize counts, reason codes, and next
  actions by default.
- Any generated preflight report should follow private workspace output policy.
- Do not embed private model text, full Flexo JSON, SysON IDs beyond the user
  supplied target IDs, diagnostics, or run logs in public docs or fixtures.

Before implementation:
- Inspect `git status --short --branch`.
- Identify unrelated dirty worktree changes and leave them untouched.
- Restate the problem, rationale, non-goals, acceptance criteria, data-safety
  impact, release target, and validation plan.
- Because this changes bridge workflow shape and may span multiple chunks,
  create or update an active plan under `docs/plans/active/` if implementation
  goes beyond a deterministic first increment.

Implementation rules:
- Follow existing repo patterns and command surfaces.
- Prefer a user-facing `mbse-lab bridge preflight` command when adding CLI
  surface.
- Keep compatibility wrappers stable unless the issue explicitly changes them.
- Add tests proportional to risk.
- Keep generated private artifacts out of this repo.
- Use `MBSE_MODEL_WORKSPACE` or explicit output paths when generated model
  artifacts are involved.
- Do not import into SysON, create SysON projects, or mutate service state in
  preflight.

Validation expectations:
- Run focused fixture tests for valid, empty, unsupported-heavy, and malformed
  snapshots while iterating.
- Run mocked SysON target-context tests if target checks are implemented.
- Run workspace policy tests if output paths or generated reports are involved.
- Run `make docs-check` when CLI docs or bridge docs change.
- Run `make share-check` if generated reports or artifact policy changes.
- Run `make check` before handing off.
- Run `make live-eval` and `make deployment-verify` only when real service
  readiness checks are implemented and services are available.

Handoff expectations:
- Summarize what changed and why.
- List the files changed.
- Report validation commands that passed or explain blockers.
- Mention any residual uncommitted worktree state.
- Note whether issue #60 should move from `status/proposed` to `status/ready`,
  remain proposed, or close after implementation lands.
- Note any update needed in release-plan issue #69.
```
