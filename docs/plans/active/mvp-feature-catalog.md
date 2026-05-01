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
| CLI install paths | Verified | `pyproject.toml`, `mbse-lab` console script, `make install-cli`, editable install docs, install-from-GitHub docs. | Validate direct GitHub install in a fresh virtual environment before first release. |
| CLI shell completion | Verified | `mbse-lab completion bash/zsh/fish`, deterministic CLI evals. | None for MVP. |
| Environment doctor | Verified | `mbse-lab doctor`, JSON output, `doctor --fix`, deterministic CLI evals. | Doctor could produce clearer next-step grouping, but current behavior is MVP-usable. |
| Local runtime initialization | Verified | `mbse-lab init`, Flexo env generation, SysON env creation, dry-run tests. | Actual first-run smoke should be validated on a clean machine or container host before MVP announcement. |
| Guided bootstrap | Partially verified | `mbse-lab bootstrap`, dry-run tests, docs. | Needs live end-to-end validation from a clean repo checkout with Docker running. |
| Flexo deployment management | Partially verified | Flexo compose config is checked, env manager exists, service wrappers exist, status command exists. | Live startup and org initialization need an explicit MVP smoke checklist. |
| SysON deployment management | Partially verified | SysON compose config is checked, service wrappers exist, status command exists. | Live startup and web/API reachability need an explicit MVP smoke checklist. |
| Private model workspace boundary | Verified | `MBSE_MODEL_WORKSPACE`, workspace init/check/env, share-check protections, README/docs diagrams. | None for MVP. |
| Share-safety checks | Verified | `mbse-lab share-check`, forbidden path scan, secret-like pattern scan, CI/check integration. | Add more patterns only as specific risks appear. |
| Flexo project operations | Partially verified | CLI wrappers for list/create/export, bridge script commands, live Flexo eval exists. | Needs live validation against current Flexo containers before MVP release. |
| SysON project operations | Partially verified | CLI wrappers for list/create/roots/import, bridge script commands, live SysON eval exists. | Needs live validation against current SysON containers before MVP release. |
| Conservative SysML rendering | Verified | Deterministic renderer evals for basic package, RF link budget, and container deployment fixtures. | Rendering scope is intentionally limited; unsupported element behavior must remain documented. |
| Flexo-to-SysON snapshot bridge | Partially verified | `flexo-to-syson`, run logs, deterministic wrapper tests, live evals exist. | Needs live full-bridge validation on running Flexo and SysON before MVP release. |
| First model workflow | Partially verified | `mbse-lab first-model`, dry-run test, model service code. | Needs live validation creating a disposable Flexo project and SysON review project through the CLI. |
| Deployment contract inspection | Verified | Container deployment fixture, `deployment contract`, deterministic evals. | None for MVP. |
| Runtime deployment verification | Partially verified | `deployment verify`, deterministic report evals, optional live deployment eval. | Needs live verification run against the current Docker stack before MVP release. |
| Diagnostics bundle | Verified | `mbse-lab diagnostics`, `collect_diagnostics.py`, diagnostics manifest evals. | Confirm redaction against a real failed-service bundle before broad sharing. |
| Static local lab report | Verified | `mbse-lab report`, Markdown/HTML/JSON outputs, deterministic CLI eval. | None for MVP. |
| Cleanup of generated local artifacts | Verified | `mbse-lab cleanup`, dry-run and removal evals, protected paths. | None for MVP. |
| Published example fixtures | Verified | Public fixtures under `evals/fixtures`, deterministic evals, curated `exports/README.md`. | Keep fixture content synthetic and small. |
| Known limitations and modeling conventions | Verified | `AGENTS.md`, bridge docs, modeling conventions docs. | README should continue to keep limitations concise and link to detailed docs. |

## Required MVP Work Remaining

1. Run a clean live smoke pass with Docker:

   ```bash
   mbse-lab init --model-workspace ~/workspace/projects/mbse-mvp-smoke-models
   mbse-lab doctor
   mbse-lab services up
   mbse-lab first-model "MVP Smoke Model"
   mbse-lab deployment verify
   make live-eval
   mbse-lab share-check
   ```

2. Validate direct GitHub install in a fresh virtual environment:

   ```bash
   python3 -m venv /tmp/mbse-lab-install-smoke
   /tmp/mbse-lab-install-smoke/bin/python -m pip install "git+https://github.com/cosgroma/mbse-lab.git@develop"
   /tmp/mbse-lab-install-smoke/bin/mbse-lab --help
   ```

3. Decide whether the MVP promises only local Docker use or also supports a
   remote Flexo/SysON endpoint profile. The current CLI has URL options, but the
   documented happy path is local Docker.

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
