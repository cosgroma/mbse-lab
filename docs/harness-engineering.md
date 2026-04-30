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
make check
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

The next useful eval layer should be a small deterministic bridge eval:

1. Create or load a tiny Flexo model fixture.
2. Export it through `flexo-export`.
3. Render `.sysml`.
4. Assert expected textual declarations are present.
5. Optionally import into a disposable SysON project and assert the expected
   element appears through SysON REST.

A future eval directory could look like:

```text
evals/
  fixtures/
  test_bridge_roundtrip.py
  README.md
```

## Observability

Current observability is command/log based:

```bash
make status
make logs
docker compose -f deploy/syson/docker-compose.yml logs --tail 100 app
python3 scripts/flexo_mms_env.py logs --tail 100
```

If the bridge grows, prefer structured JSON logs for export/render/import runs
so agent traces can be reviewed without scraping terminal output.

## Recommended Next Steps

1. Add `evals/test_bridge_roundtrip.py` for the Flexo JSON to `.sysml` renderer.
2. Add a fixture model that does not require live services.
3. Add an optional live integration eval gated by an environment variable.
4. Add a `make eval` target once the evals exist.
5. Add a `docs/modeling-conventions.md` file for supported SysML v2 subsets.

## Harness Interpretation For This Repo

Harness engineering here should not mean adding a heavyweight agent framework.
It should mean strengthening the repo so agents can reliably operate the MBSE
environment: clear instructions, repeatable commands, state capture, safe
credential handling, deterministic checks, and small evals around the workflows
we care about.
