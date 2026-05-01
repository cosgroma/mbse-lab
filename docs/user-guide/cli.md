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

Print a structured report for automation:

```bash
mbse-lab doctor --json-output
```

Apply low-risk local setup fixes:

```bash
mbse-lab doctor --fix
```

The fix mode can create `deploy/syson/.env` from the checked-in example and
initialize the directory layout for an already configured
`MBSE_MODEL_WORKSPACE`. It prints remaining commands for Flexo runtime files,
service startup, or other setup that should stay explicit.

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

## Services

Start both Flexo and SysON:

```bash
mbse-lab services up
```

Stop both service families without deleting runtime data:

```bash
mbse-lab services down
```

Restart the lab:

```bash
mbse-lab services restart
```

Show recent service logs:

```bash
mbse-lab services logs --tail 100
```

Each service command accepts `--flexo/--no-flexo` and `--syson/--no-syson` for
targeted operations. Add `--dry-run` to preview the underlying script and Docker
Compose commands.

## First Model

After the services are running, create a tiny end-to-end model:

```bash
mbse-lab first-model "My First Model"
```

The command:

- creates a Flexo SysML v2 project
- commits one root `Package`
- exports Flexo JSON
- renders textual SysML
- creates a SysON review project
- imports the rendered SysML into the SysON root package
- prints Flexo IDs, SysON IDs, and generated artifact paths

Preview the workflow without creating projects:

```bash
mbse-lab first-model "My First Model" --dry-run
```

Use explicit names or output locations when needed:

```bash
mbse-lab first-model "Radio Demo" \
  --package-name "Radio Demo Package" \
  --syson-project-name "Radio Demo Review" \
  --output-dir ~/work/my-private-models/exports
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

Print service status as JSON:

```bash
mbse-lab status --json-output
```

Collect diagnostics:

```bash
mbse-lab diagnostics
```

Generate a static local lab report:

```bash
mbse-lab report
```

The report writes:

```text
reports/latest/index.md
reports/latest/index.html
reports/latest/doctor.json
reports/latest/status.json
reports/latest/report.json
```

The report includes service URLs, doctor/status summaries, container state,
workspace settings, diagnostics bundle links, and share-check results.

Remove generated local reports, diagnostics, run logs, and temporary output:

```bash
mbse-lab cleanup
```

Preview cleanup targets first:

```bash
mbse-lab cleanup --dry-run
```

By default cleanup does not touch service data, env files, backups, model
exports, or MkDocs `site/` output. Use `--include-site` to remove `site/`.

Check that the tooling repo is safe to share:

```bash
mbse-lab share-check
```

The share check flags tracked runtime env files, service data, run logs,
diagnostics bundles, generated private exports, and known local secret patterns.

List or create Flexo projects:

```bash
mbse-lab flexo list
mbse-lab flexo create "Example Model"
mbse-lab flexo export <flexo-project-id>
```

List or create SysON projects and inspect import roots:

```bash
mbse-lab syson list
mbse-lab syson create "Imported From Flexo"
mbse-lab syson roots <syson-project-id>
```

Render, import, or run the full bridge:

```bash
mbse-lab bridge render exports/flexo/<flexo-project-id>.json
mbse-lab bridge import exports/sysml/<flexo-project-id>.sysml \
  --project-id <syson-project-id> \
  --namespace-id <syson-root-package-id>
mbse-lab bridge run <flexo-project-id> \
  --syson-project-id <syson-project-id> \
  --namespace-id <syson-root-package-id>
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
