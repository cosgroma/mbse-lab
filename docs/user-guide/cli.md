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
