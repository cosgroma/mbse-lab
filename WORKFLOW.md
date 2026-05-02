---
workflow:
  name: mbse-local-lab-agent-workflow
  version: 1
tracker:
  kind: manual
workspace:
  mode: shared-repo
  plans_dir: docs/plans
agent:
  commit_after_chunk: true
  max_chunk_scope: focused
validation:
  required:
    - make workflow-check
    - make check
  before_publish:
    - hatch run lint:all
    - make share-check
  docs_when_docs_change:
    - make docs-build
  live_when_services_running:
    - make live-eval
    - make deployment-verify
observability:
  diagnostics: make diagnostics
  run_logs: runs/
trust:
  environment: trusted-local-lab
  destructive_actions_require_explicit_intent: true
---

# MBSE Local Lab Workflow

This repository uses a lightweight Symphony-style workflow contract: runtime
policy and agent operating expectations live in this repo, next to the code,
docs, evals, and Docker deployment files they govern. This file is not a
daemon configuration yet. It is the authoritative workflow prompt and policy
for Codex work in this MBSE local lab.

## Operating Model

Use this repo as a shared local workspace for MBSE environment setup, Flexo MMS
automation, SysON import/review, bridge workflows, deployment verification, and
diagnostics. Treat it as reusable tooling, not the storage location for private
SysML v2 model repositories. Work in small chunks that land independently.
Commit each chunk after implementation and validation when the user has asked to
continue in this mode.

Keep durable state in files:

- `README.md` for user-facing operations.
- `AGENTS.md` for maintainer and fresh-agent guidance.
- `docs/lab/harness-engineering.md` for harness design.
- `docs/plans/` for task plans when a task needs persistent planning.
- `runs/` for ignored workflow run logs.
- `diagnostics/latest/` for ignored diagnostics bundles.

## Task Plans

Small changes do not need checked-in plans. Create a plan under
`docs/plans/active/` when the task spans multiple chunks, changes persistence
or credential handling, changes live-service workflows, or needs durable
decisions beyond chat history.

Each active plan should capture objective, relevant files, planned steps,
progress, validation commands, decisions, tradeoffs, and follow-up debt. When
the work is complete, move the plan to `docs/plans/completed/` with the final
validation and outcome recorded.

## Required Validation

Run the full deterministic baseline before committing normal code or docs
changes:

```bash
make check
```

Run the focused workflow contract validation when editing this file or changing
agent policy:

```bash
make workflow-check
```

For targeted documentation changes, `make docs-check` may be used during
iteration, but the final chunk should still pass `make check` unless there is a
clear blocker.

```bash
make docs-check
```

Run deterministic evals directly when editing renderers, fixtures, workflow
contracts, diagnostics formatting, or harness behavior:

```bash
make eval
```

Run the local pre-commit suite before publishing branches or pull requests, and
after broad mechanical formatting or lint-related changes:

```bash
hatch run lint:all
```

Run the publish-safety check before sharing the tooling repo:

```bash
make share-check
```

The GitHub CI workflow runs pre-commit, the documentation build, and `make
check`. Local validation should match that before publishing when practical.

## Documentation Site

The documentation is organized for MkDocs. When changing `mkdocs.yml`, docs
navigation, documentation paths, or MkDocs dependencies, build the site locally:

```bash
make docs-build
```

For interactive review of larger documentation changes:

```bash
make docs-serve
```

## Live Validation

When Flexo and SysON are running, verify live service behavior before committing
changes that affect deployment, bridge workflows, service state, or model
imports:

```bash
make live-eval
```

Inspect and verify the model-driven deployment contract with:

```bash
make deployment-contract
make deployment-verify
```

## Diagnostics And Evidence

Collect diagnostics after service failures, unexpected port/mount behavior, or
before handoff when runtime state matters:

```bash
make diagnostics
```

Start triage from:

```text
diagnostics/latest/index.md
diagnostics/latest/manifest.json
diagnostics/latest/deployment-verification.json
```

Bridge runs should use structured run logs when evidence needs to be preserved:

```bash
mbse-lab bridge run <flexo-project-id> \
  --syson-project-id <syson-project-id> \
  --namespace-id <syson-root-package-id>
```

## Data And Credential Boundaries

Runtime secrets and local service data are intentionally ignored. Do not commit
runtime `.env` files, Flexo backup data, SysON database files, diagnostics
bundles, run logs, private Flexo JSON exports, private rendered `.sysml`
snapshots, or real model source. Commit publishable examples and deterministic
fixtures only.

Use `MBSE_MODEL_WORKSPACE` or explicit bridge output paths when generated model
artifacts belong in a private workspace outside this repo. Commands that write
model artifacts (`first-model`, `flexo export`, `bridge render`, `bridge run`)
warn when neither `MBSE_MODEL_WORKSPACE` nor an explicit `--output` path is
provided. Pass `--allow-repo-exports` only when intentionally writing curated
example output under `exports/` in this shared tooling repo.

Before destructive reset actions, such as deleting service data, removing
containers with volumes, or rewriting persisted Flexo startup data, get
explicit user intent. When Flexo graph state matters, back it up first:

```bash
make backup
```

## Handoff

A chunk is complete when:

- The intended change is implemented.
- Relevant deterministic and live checks have passed, or blockers are stated.
- Unrelated working-tree changes are left untouched.
- The chunk is committed with a focused message.
- The final note reports the commit, validation, residual uncommitted state, and
  the recommended next chunk.
