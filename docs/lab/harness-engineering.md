# Harness Engineering Setup

This repo already has the core pieces of a useful agent harness: local
instructions, deterministic environment scripts, Dockerized services,
credential boundaries, and repeatable bridge workflows. This document maps the
harness engineering ideas from `walkinglabs/awesome-harness-engineering` onto
this MBSE lab.

## Harness Goals

- Make a fresh agent productive without rediscovering the repo.
- Keep this repo shareable as tooling, not as the home for private SysML v2
  models.
- Keep runtime credentials and service data out of published history.
- Make common operations executable through stable commands.
- Preserve enough state to resume long-running Flexo/SysON experiments.
- Add verification and eval hooks before expanding model-generation behavior.

## Current Harness Pieces

| File or area | Harness role |
| --- | --- |
| `AGENTS.md` | Repo-local agent instructions. |
| `README.md` | User-facing environment guide. |
| `WORKFLOW.md` | Repo-owned workflow contract for agent runs. |
| `Makefile` | Stable shortcut surface for agents and humans. |
| `mbse-lab` | Canonical CLI for setup, services, bridge, diagnostics, and deployment checks. |
| `scripts/flexo_mms_env.py` | Compatibility/maintainer entry point for Flexo environment operations. |
| `scripts/flexo_syson_bridge.py` | Compatibility/maintainer entry point for bridge and deployment operations. |
| `scripts/check_docs.py` | Documentation link and command hygiene checks. |
| [Private Model Workspaces](../user-guide/private-model-workspaces.md) | Tooling repo versus private model workspace boundary. |
| [Bridge Workflow](flexo-syson-bridge.md) | Flexo export, SysML render, and SysON import details. |
| [Modeling Conventions](modeling-conventions.md) | Supported SysML v2 bridge subset. |
| [Feature Development Agent Prompt](feature-development-agent-prompt.md) | Copyable prompt for handing proposal-backed feature work to a fresh agent. |
| [Feature Development Prompt Pack](feature-development-prompt-pack.md) | Filled prompts for selected proposal-backed feature issues. |
| [Plans](../plans/README.md) | Execution plan conventions. |
| `deploy/*/*.example` | Publishable config templates. |

## Command Surface

Agents should prefer `mbse-lab` for user-facing operations and `make` targets
for repeatable repo checks:

```bash
make help
make init
make up
make status
make diagnostics
make check
make workflow-check
make docs-check
make live-eval
make backup
make flexo-list
make syson-list
```

Use the CLI directly when a workflow needs arguments, for example:

```bash
mbse-lab bridge run <flexo-project-id> \
  --syson-project-id <syson-project-id> \
  --namespace-id <syson-root-package-id>
```

The Python scripts remain callable for compatibility, but new user-visible
behavior should be exposed through `mbse-lab` first.

Inspect the fixture-derived deployment runtime contract before running Docker
checks with:

```bash
make deployment-contract
```

Verify the running Docker containers against that contract with:

```bash
make deployment-verify
```

Test the deployment contract in an isolated disposable Compose project with:

```bash
make deployment-isolated-smoke
```

The isolated smoke test is intended for CI and shared development hosts. It
uses random localhost-only host ports, temp bind-mounted data, and Compose
project labels so it does not require or disturb the normal `mbse-lab services
up` containers.

## Context And Working State

Keep durable context in files, not in chat history:

- `AGENTS.md` for agent operating rules.
- `WORKFLOW.md` for the repo-owned workflow contract inspired by Symphony.
- `README.md` for setup and recovery.
- `docs/` for workflow decisions and architecture notes.
- `exports/` for representative generated artifacts.

Keep private SysML v2 model source, Flexo exports, rendered `.sysml` snapshots,
run evidence, and program-specific analysis results in a separate private
workspace. Set `MBSE_MODEL_WORKSPACE` when bridge defaults should write there.

When a workflow produces an important Flexo graph state, run:

```bash
make backup
```

This writes ignored backup data. Refresh the tracked startup seed only with the
explicit high-intent backup flags, and only for synthetic, publishable seed
data. Then document the model/project IDs in `docs/` or the task notes.

## Constraints And Guardrails

Credential guardrails:

- Commit `.example` env files only.
- Ignore runtime `.env` files and service data.
- Run `make share-check` before publishing.

Model data guardrails:

- Treat this repo as reusable tooling, not a private model repository.
- Keep real model data outside the repo or in a private repo.
- Use `MBSE_MODEL_WORKSPACE` or explicit bridge output paths for generated
  Flexo JSON and `.sysml` files.
- Commit only synthetic fixtures and curated publishable examples.

Environment guardrails:

- Use Docker Compose files under `deploy/`.
- Avoid `down --volumes` unless intentionally resetting local state.
- Use `mbse-lab flexo backup` before destructive changes.

Workflow guardrails:

- Treat Flexo as the API-driven model repository.
- Treat SysON as a graphical import/review environment.
- Do not assume live bidirectional sync between Flexo and SysON.

## Evals And Verification

The current baseline check is:

```bash
make check
```

That validates Python syntax, Docker Compose config, tracked-secret hygiene, and
git cleanliness.

The deterministic local eval is:

```bash
make eval
```

It loads a tiny Flexo model fixture, renders `.sysml`, and asserts expected
textual declarations are present. It does not require Docker services.

The optional live service evals are:

```bash
make live-eval
```

They currently cover:

- Flexo export/render: create a disposable Flexo project, commit a minimal
  package payload, export through the bridge, render `.sysml`, and delete the
  project.
- SysON import: create a disposable SysON project, import rendered `.sysml`,
  verify the expected package appears through SysON REST, and delete the
  project.
- Deployment runtime: inspect the Flexo and SysON Docker containers, verify the
  containers modeled in `fixtures/container-deployment-basic.json` are running,
  confirm configured host ports are published, and check persisted bind mounts
  for Fuseki seed data, MinIO data, and SysON Postgres data.
- Isolated deployment smoke: start the same Flexo/SysON service graph in a
  disposable Compose project, verify by Compose labels instead of fixed
  container names, then tear down the project with its temporary volumes.

Run `make live-eval` only when the required local stacks are up.

The eval directory is:

```text
evals/
  fixtures/flexo-basic-package.json
  fixtures/container-deployment-basic.json
  fixtures/rf-link-budget-basic.json
  test_bridge_render.py
  test_live_deployment_runtime.py
  test_live_flexo_export.py
  test_live_syson_import.py
```

The RF link-budget fixture is the first model-spec-derived fixture. It captures
the backbone of `docs/model-specs/rf-link-budget.md`: a root package,
definitions, the `RFLink` part definition, core attributes and parts,
`MinimumLinkMargin`, and a simple architecture package.

The container deployment fixture captures the backbone of
`docs/model-specs/container-deployment.md`: deployment definitions, reachability
and persistence requirements, and a local lab deployment with Flexo and SysON
stacks. It also carries the runtime contract used by the live deployment eval:
container names, Compose service names, published port expectations, host port
environment overrides, and persisted bind mounts.

## Observability

Current observability is command/log based:

```bash
make status
make logs
make diagnostics
```

`make diagnostics` writes a redacted bundle to `diagnostics/latest/` with git
state, Docker Compose state, service probes, project lists, selected config
files, recent logs, and `deployment-verification.json` from the model-driven
Docker runtime verifier. It also writes `index.md` and `manifest.json` as
summary entry points. The diagnostics directory is ignored by git.

Use `mbse-lab diagnostics --public-safe` before sharing evidence outside a
private project team. Public-safe bundles omit project-list probes and recent
service logs, which are the most likely diagnostics sources for private project
names, project IDs, import messages, and generated artifact paths.

`flexo-to-syson` writes a structured JSON run log under
`runs/flexo-to-syson/` by default. Run logs include inputs, generated artifact
paths, Flexo project/commit metadata, SysON import metadata, step timings, final
status, and failure details when a run fails. The `runs/` directory is ignored
by git.

Use `--run-log <path>` to pin a specific log path for a workflow run.

## Recommended Next Steps

1. Add a doc-gardening check for stale or unlinked workflow docs.
2. Add a `docs/lab/modeling-conventions.md` section for each newly supported SysML
   v2 element type.

## Harness Interpretation For This Repo

Harness engineering here should not mean adding a heavyweight agent framework.
It should mean strengthening the repo so agents can reliably operate the MBSE
environment: clear instructions, repeatable commands, state capture, safe
credential handling, deterministic checks, and small evals around the workflows
we care about.
