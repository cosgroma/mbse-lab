# MVP Feature Catalog

## Objective

Define the minimum useful release shape for `mbse-lab`: a public tooling repo
that lets a user bootstrap a local SysML v2 lab, keep private models outside
the tooling repo, run Flexo and SysON, move conservative model snapshots between
them, and verify that the repo is safe to share.

This catalog distinguishes features that are implemented and verified from
features that still need development or release hardening.

## Status Legend

| Status | Meaning |
| --- | --- |
| Verified | Implemented and covered by deterministic checks, GitHub CI, docs validation, or community profile checks. |
| Partially verified | Implemented, but the important user path depends on live services, manual validation, or incomplete automated coverage. |
| Needs development | Required for a strong MVP but not yet implemented or not yet usable enough. |

## Required MVP Features

| Feature | Status | Current evidence | MVP gap |
| --- | --- | --- | --- |
| Public repo identity and community readiness | Verified | README badges, MIT license, community files, GitHub community profile reports 100%. | None for MVP. |
| Git Flow and repository automation | Verified | `git-flow-policy.yml`, CI, Pages workflow, Dependabot targeting `develop`, branch policy runs, release process docs. | Run the release procedure for the first tagged release. |
| Documentation site | Verified | MkDocs config, docs workflow, GitHub Pages deployment, `make docs-build`. | None for MVP. |
| CLI install paths | Verified | `pyproject.toml`, `mbse-lab` console script, `make install-cli`, editable install docs, install-from-GitHub docs, fresh virtualenv install from GitHub `develop`. | None for MVP. |
| CLI shell completion | Verified | `mbse-lab completion bash/zsh/fish`, deterministic CLI evals. | None for MVP. |
| Environment doctor | Verified | `mbse-lab doctor`, JSON output, `doctor --fix`, deterministic CLI evals. | Doctor could produce clearer next-step grouping, but current behavior is MVP-usable. |
| Local runtime initialization | Verified | `mbse-lab init`, Flexo env generation, SysON env creation, dry-run tests, live smoke workspace initialization. | None for MVP. |
| Guided bootstrap | Partially verified | `mbse-lab bootstrap`, dry-run tests, docs. | Needs live end-to-end validation from a clean repo checkout with Docker running. |
| Flexo deployment management | Verified | Flexo compose config is checked, env manager exists, service wrappers exist, status command exists, live smoke reported Flexo containers running and Flexo projects API HTTP 200. | None for MVP. |
| SysON deployment management | Verified | SysON compose config is checked, service wrappers exist, status command exists, live smoke reported SysON app running and web UI HTTP 200. | Add a doctor hint for persisted database password drift when this recurs. |
| Private model workspace boundary | Verified | `MBSE_MODEL_WORKSPACE`, workspace init/check/env, share-check protections, README/docs diagrams. | None for MVP. |
| Share-safety checks | Verified | `mbse-lab share-check`, forbidden path scan, secret-like pattern scan, CI/check integration. | Add more patterns only as specific risks appear. |
| Flexo project operations | Verified | CLI wrappers for list/create/export, bridge script commands, live Flexo eval, live first-model project creation and export. | None for MVP. |
| SysON project operations | Verified | CLI wrappers for list/create/roots/import, bridge script commands, live SysON eval, live first-model review project and import. | None for MVP. |
| Conservative SysML rendering | Verified | Deterministic renderer evals for basic package, RF link budget, and container deployment fixtures. | Rendering scope is intentionally limited; unsupported element behavior must remain documented. |
| Flexo-to-SysON snapshot bridge | Verified | `flexo-to-syson`, run logs, deterministic wrapper tests, live evals, live first-model import into SysON. | None for MVP. |
| First model workflow | Verified | `mbse-lab first-model`, dry-run test, model service code, live smoke model created and imported. | None for MVP. |
| Deployment contract inspection | Verified | Container deployment fixture, `deployment contract`, deterministic evals. | None for MVP. |
| Runtime deployment verification | Verified | `deployment verify`, deterministic report evals, optional live deployment eval, live smoke reported 9 services and 19 checks passing. | None for MVP. |
| Diagnostics bundle | Verified | `mbse-lab diagnostics`, `collect_diagnostics.py`, diagnostics manifest evals, live diagnostics bundle collection. | Continue checking redaction when adding new diagnostic artifacts. |
| Static local lab report | Verified | `mbse-lab report`, Markdown/HTML/JSON outputs, deterministic CLI eval. | None for MVP. |
| Cleanup of generated local artifacts | Verified | `mbse-lab cleanup`, dry-run and removal evals, protected paths. | None for MVP. |
| Published example fixtures | Verified | Public fixtures under `evals/fixtures`, deterministic evals, curated `exports/README.md`. | Keep fixture content synthetic and small. |
| Known limitations and modeling conventions | Verified | `AGENTS.md`, bridge docs, modeling conventions docs. | README should continue to keep limitations concise and link to detailed docs. |

## Live Validation Results

Live validation on May 1, 2026 passed against the local Docker stack after
aligning the ignored local SysON env file with the existing persisted database
password.

Commands run:

```bash
python3 -m venv /tmp/mbse-lab-install-smoke
/tmp/mbse-lab-install-smoke/bin/python -m pip install "git+https://github.com/cosgroma/mbse-lab.git@develop"
/tmp/mbse-lab-install-smoke/bin/mbse-lab --help
export MBSE_MODEL_WORKSPACE=~/workspace/projects/mbse-mvp-smoke-models
mbse-lab init --model-workspace "$MBSE_MODEL_WORKSPACE"
mbse-lab doctor
mbse-lab services up
mbse-lab first-model "MVP Smoke Model" --json-output
mbse-lab deployment verify
make live-eval
mbse-lab diagnostics
mbse-lab share-check
```

Observed results:

- GitHub install from `develop` resolved commit `e819d25` and exposed the CLI.
- `mbse-lab doctor` reported Python, Docker, Docker Compose, repo markers,
  `MBSE_MODEL_WORKSPACE`, Flexo, and SysON as OK.
- `mbse-lab first-model` created Flexo project
  `aceb2496-9cca-4e97-9b17-bcfd5b076a4b` and SysON review project
  `3a8a0b23-af07-4b73-a789-8dd714d66612`.
- Generated smoke artifacts were written under
  `~/workspace/projects/mbse-mvp-smoke-models/exports/`.
- `mbse-lab deployment verify` passed with 9 services and 19 checks.
- `make live-eval` ran 4 live tests successfully.
- `mbse-lab diagnostics` wrote `diagnostics/latest`.
- `mbse-lab share-check` passed after live validation.

Local-state note:

- The first smoke attempt exposed a local SysON credential drift: the persisted
  Postgres data volume was initialized with password `password`, while ignored
  `deploy/syson/.env` contained `change-me`. Updating the ignored local env file
  to match the existing database allowed SysON to start without deleting runtime
  data.

## Required MVP Work Remaining

1. Decide whether the MVP promises only local Docker use or also supports a
   remote Flexo/SysON endpoint profile. The current CLI has URL options, but the
   documented happy path is local Docker.

2. Consider adding a doctor check for SysON persisted database credential drift
   when `deploy/syson/.env` and `deploy/syson/data/postgres/` disagree.

## Deferred Beyond MVP

- Full SysML v2 element coverage.
- Diagram layout round-trip between Flexo and SysON.
- Live repository synchronization between Flexo and SysON.
- Hosted package distribution through PyPI.
- Automated CI that starts the full Docker stack on every push.
- Rich model templates beyond the tiny first-model flow.

## Validation To Keep Current

Run the deterministic baseline after changing this catalog:

```bash
make check
```

Run the live smoke pass before calling the MVP release-ready.
