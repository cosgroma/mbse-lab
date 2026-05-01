# Contributing

Thanks for improving `mbse-lab`. This repository is a public tooling kit for
local SysML v2 workflows with OpenMBEE Flexo MMS, Eclipse SysON, and the bridge
scripts between them.

## Repository Boundary

Keep this repository focused on reusable tooling, documentation, public
synthetic fixtures, and container setup. Do not add private SysML v2 models,
runtime service data, credentials, generated diagnostics, or private exports.

Use a separate private workspace for real model work:

```bash
export MBSE_MODEL_WORKSPACE=~/work/my-private-models
```

## Local Setup

Install the CLI in editable mode:

```bash
make install-cli
```

Generate local environment files:

```bash
mbse-lab init --model-workspace ~/work/my-private-models
```

Run the environment doctor:

```bash
mbse-lab doctor
```

## Development Workflow

This repo follows Git Flow:

- Open feature and bugfix work against `develop`.
- Copilot-authored `copilot/*` branches may target `develop`.
- Reserve `main` for release and hotfix flow.
- Keep changes small enough to validate and review.
- Avoid unrelated refactors in focused fixes.

Before opening a pull request, run:

```bash
make check
```

For broader changes or publication-sensitive changes, also run:

```bash
hatch run lint:all
make share-check
```

When changing documentation structure, MkDocs configuration, or docs
dependencies, run:

```bash
make docs-build
```

## Pull Requests

Good pull requests include:

- A concise summary of the user-facing or maintainer-facing change.
- The validation commands that passed.
- Notes about any checks that could not be run.
- Screenshots or logs only when they are relevant and redacted.

Do not include local `.env` files, service databases, diagnostics bundles,
private Flexo exports, private rendered `.sysml` snapshots, or real model
source.
