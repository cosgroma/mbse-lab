# CLI

The `mbse-lab` CLI is the user-facing command surface for this local SysML v2
lab kit. It wraps the existing Flexo, SysON, bridge, diagnostics, deployment,
and private workspace workflows behind one command tree.

## Install

Install the CLI from this repo in editable mode:

```bash
make install-cli
```

Equivalent explicit command:

```bash
python3 -m pip install -e .
```

Check the command surface:

```bash
mbse-lab --help
```

## Doctor

Run a local environment check:

```bash
mbse-lab doctor
```

The doctor checks Python, Docker, Docker Compose, expected repo files, local
runtime env files, `MBSE_MODEL_WORKSPACE`, common service ports, and basic Flexo
and SysON reachability.

## Bootstrap

Prepare the local lab for first use:

```bash
mbse-lab bootstrap --model-workspace ~/work/my-private-models
```

The bootstrap command:

- generates Flexo runtime files with SysML v2 enabled
- creates `deploy/syson/.env` from the publishable example when needed
- optionally initializes a private model workspace
- starts Flexo and SysON
- initializes the Flexo SysML v2 org
- backs up Flexo graph state after org initialization
- runs final status checks
- prints local service URLs and next commands

Preview the planned operations without changing files or starting containers:

```bash
mbse-lab bootstrap --dry-run --model-workspace ~/work/my-private-models
```

Useful options:

```bash
mbse-lab bootstrap --skip-start
mbse-lab bootstrap --skip-flexo-org
mbse-lab bootstrap --skip-status
```

## Private Workspaces

Initialize a private model workspace:

```bash
mbse-lab workspace init ~/work/my-private-models
```

Print the shell export command for a workspace:

```bash
mbse-lab workspace env ~/work/my-private-models
```

Check an existing workspace:

```bash
mbse-lab workspace check ~/work/my-private-models
```

When `MBSE_MODEL_WORKSPACE` is set, bridge commands default generated exports to
that private workspace instead of this tooling repo.

## Lab Operations

Run status checks:

```bash
mbse-lab status
```

Collect diagnostics:

```bash
mbse-lab diagnostics
```

Inspect and verify the container deployment contract:

```bash
mbse-lab deployment contract
mbse-lab deployment verify
```

These commands expect to run from the shared lab repo. If you run the CLI from
another directory, pass `--repo-root`:

```bash
mbse-lab --repo-root ~/work/sysmlv2-lab doctor
```
