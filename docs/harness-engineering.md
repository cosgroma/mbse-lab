# Harness Engineering Setup

This repo already has the core pieces of a useful agent harness: local
instructions, deterministic environment scripts, Dockerized services,
credential boundaries, and repeatable bridge workflows. This document maps the
harness engineering ideas from `walkinglabs/awesome-harness-engineering` onto
this MBSE lab.

## Harness Goals

- Make a fresh agent productive without rediscovering the repo.
- Keep runtime credentials and service data out of published history.
- Make common operations executable through stable commands.
- Preserve enough state to resume long-running Flexo/SysON experiments.
- Add verification and eval hooks before expanding model-generation behavior.

## Current Harness Pieces

```text
AGENTS.md                         Repo-local agent instructions
README.md                         User-facing environment guide
Makefile                          Stable command surface for agents and humans
scripts/flexo_mms_env.py          Environment setup, status, backup, rotation
scripts/flexo_syson_bridge.py     Flexo/SysON workflow automation
docs/flexo-syson-bridge.md        Bridge details
deploy/*/*.example                Publishable config templates
```

## Command Surface

Agents should prefer `make` targets for routine operations:

```bash
make help
make init
make up
make status
make diagnostics
make check
make live-eval
make backup
make flexo-list
make syson-list
```

Use the underlying Python scripts when a workflow needs arguments, for example:

```bash
python3 scripts/flexo_syson_bridge.py flexo-to-syson <flexo-project-id> \
  --syson-project-id <syson-project-id> \
  --namespace-id <syson-root-package-id>
```

## Context And Working State

Keep durable context in files, not in chat history:

- `AGENTS.md` for agent operating rules.
- `README.md` for setup and recovery.
- `docs/` for workflow decisions and architecture notes.
- `exports/` for representative generated artifacts.

When a workflow produces an important Flexo graph state, run:

```bash
make backup
```

Then document the model/project IDs in `docs/` or the task notes.

## Constraints And Guardrails

Credential guardrails:

- Commit `.example` env files only.
- Ignore runtime `.env` files and service data.
- Run `make secret-scan` before publishing.

Environment guardrails:

- Use Docker Compose files under `deploy/`.
- Avoid `down --volumes` unless intentionally resetting local state.
- Use `scripts/flexo_mms_env.py backup` before destructive changes.

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

Run `make live-eval` only when the required local stacks are up.

The eval directory is:

```text
evals/
  fixtures/flexo-basic-package.json
  test_bridge_render.py
  test_live_flexo_export.py
  test_live_syson_import.py
```

## Observability

Current observability is command/log based:

```bash
make status
make logs
make diagnostics
```

`make diagnostics` writes a redacted bundle to `diagnostics/latest/` with git
state, Docker Compose state, service probes, project lists, selected config
files, and recent logs. The diagnostics directory is ignored by git.

If the bridge grows further, prefer structured JSON logs for export/render/import
runs so agent traces can be reviewed without scraping terminal output.

## Recommended Next Steps

1. Add structured JSON run logs for `flexo-to-syson` itself.
2. Add a doc-gardening check for stale or unlinked workflow docs.
3. Add a `docs/modeling-conventions.md` section for each newly supported SysML
   v2 element type.

## Harness Interpretation For This Repo

Harness engineering here should not mean adding a heavyweight agent framework.
It should mean strengthening the repo so agents can reliably operate the MBSE
environment: clear instructions, repeatable commands, state capture, safe
credential handling, deterministic checks, and small evals around the workflows
we care about.
