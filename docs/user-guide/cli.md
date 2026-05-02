# CLI

The `mbse-lab` CLI is the user-facing command surface for this local SysML v2
lab kit. It wraps the existing Flexo, SysON, bridge, diagnostics, deployment,
and private workspace workflows behind one command tree.

## Command Map

| Goal | Command family | Start with |
| --- | --- | --- |
| Check local setup | `doctor`, `status` | `mbse-lab doctor` |
| Prepare runtime files | `init`, `bootstrap` | `mbse-lab bootstrap --model-workspace ~/work/my-private-models` |
| Manage containers | `services` | `mbse-lab services up` |
| Create a smoke-test model | `first-model` | `mbse-lab first-model "My First Model"` |
| Prove first-use setup | `smoke` | `mbse-lab smoke first-use --json-output` |
| Keep artifacts private | `workspace` | `mbse-lab workspace init ~/work/my-private-models` |
| Move snapshots between tools | `flexo`, `syson`, `bridge` | `mbse-lab bridge run <flexo-project-id> --create-syson-project "Imported From Flexo"` |
| Collect evidence | `diagnostics`, `report`, `deployment` | `mbse-lab diagnostics` |
| Prepare sharing | `share-check`, `cleanup` | `mbse-lab share-check` |

## Install

Install the CLI from this repo in editable mode:

```bash
make install-cli
```

Equivalent explicit command:

```bash
python3 -m pip install -e .
```

Install directly from GitHub when you want the command without an editable
working copy:

```bash
python3 -m pip install "git+https://github.com/cosgroma/mbse-lab.git"
```

Install from the active development branch when you want the latest unreleased
changes:

```bash
python3 -m pip install "git+https://github.com/cosgroma/mbse-lab.git@develop"
```

Check the command surface:

```bash
mbse-lab --help
```

For every command and option, use the generated
[CLI Reference](cli-reference.md). `make docs-check` fails when that reference
drifts from the Click command tree.

Print shell completion setup:

```bash
mbse-lab completion bash
mbse-lab completion zsh
mbse-lab completion fish
```

For the current shell session, evaluate the printed command. To enable
completion permanently, add the printed line to the matching shell startup file,
such as `~/.bashrc`, `~/.zshrc`, or `~/.config/fish/config.fish`.

## Doctor

Run a local environment check:

```bash
mbse-lab doctor
```

The doctor checks Python, Docker, Docker Compose, expected repo files, local
runtime env files, `MBSE_MODEL_WORKSPACE`, common service ports, and basic Flexo
and SysON reachability. When SysON has persisted Postgres data and the database
container is running, it also checks whether the ignored local
`deploy/syson/.env` password works with that persisted database. This catches
the common case where `syson-app` exits after a local `.env` password change.

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

## Isolated Deployment Smoke Test

Use a disposable Docker deployment when you need to test the multi-container
stack without colliding with already-running lab containers:

```bash
mbse-lab deployment isolated-smoke
```

This command starts Flexo and SysON from isolated Compose files with a generated
project name, random localhost-only host ports, and temp data directories under
`tmp/isolated-deployments/`. It verifies the fixture-derived runtime contract
by Compose labels rather than fixed container names, then runs
`docker compose down --remove-orphans --volumes` for that project. Pass `--keep`
to leave the disposable stack running for inspection.

## First-Use Smoke

Run the first-use proof workflow when you want one command to start services,
initialize the Flexo SysML v2 org, create a disposable model, import it into
SysON, and write the lab report:

```bash
mbse-lab smoke first-use --json-output
```

Preview the same workflow without Docker or service calls:

```bash
mbse-lab smoke first-use --dry-run --json-output
```

The JSON output includes overall status, Flexo and SysON IDs, generated artifact
paths, service URLs, and the report path.

## Init

Prepare local runtime env files without starting services:

```bash
mbse-lab init --model-workspace ~/work/my-private-models
```

The init command:

- generates Flexo runtime files with SysML v2 enabled
- creates `deploy/syson/.env` from the publishable example when needed
- optionally initializes a private model workspace
- prints next commands for checking and starting the lab

Preview the setup without changing files:

```bash
mbse-lab init --dry-run --model-workspace ~/work/my-private-models
```

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
- waits for the Flexo `/projects` API and SysON web UI to answer
- initializes the Flexo SysML v2 org
- backs up Flexo graph state after org initialization
- runs final status checks
- prints local service URLs and next commands, including
  `mbse-lab first-model "My First Model"`

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

By default, `services up` waits for the selected service APIs before printing
the service URLs. Use `--no-wait` only when you want to start containers and
return immediately.

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
targeted operations. `services logs` also supports `--follow`,
`--flexo-service`, and `--syson-service` for focused log inspection. Use
`services down --volumes` only when you intentionally want to remove Flexo
compose-managed volumes. Add `--dry-run` to preview the underlying script and
Docker Compose commands.

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

Use a reduced bundle when the output may be shared outside a private project
team:

```bash
mbse-lab diagnostics --public-safe
```

Public-safe diagnostics omit project-list probes and recent service logs so the
bundle does not include private project names, project IDs, import log messages,
or generated artifact paths from those sources.

Customize diagnostics output when collecting evidence for a specific run:

```bash
mbse-lab diagnostics --output diagnostics/run-001 --timeout 30 --log-tail 40
```

Generate a static local lab report:

```bash
mbse-lab report
```

When bridge run logs exist, the report links the latest run log and generated
artifact paths and summarizes render coverage counts without embedding Flexo
JSON or SysML model content.

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

Run Flexo maintenance operations through the same CLI:

```bash
mbse-lab flexo init-org
mbse-lab flexo token
mbse-lab flexo backup
mbse-lab flexo rotate-secrets
```

`mbse-lab flexo backup` writes an ignored backup file by default. Refreshing the
tracked startup seed requires explicit intent and should be reserved for
synthetic, publishable seed data:

```bash
mbse-lab flexo backup --update-init --i-understand-this-updates-tracked-seed
```

Restore graph startup data only when you intend to replace
`deploy/flexo-mms/mount/cluster.nq`:

```bash
mbse-lab flexo restore deploy/flexo-mms/backups/<backup-file>.nq
```

List or create SysON projects and inspect import roots:

```bash
mbse-lab syson list
mbse-lab syson create "Imported From Flexo"
mbse-lab syson roots <syson-project-id>
```

`mbse-lab syson roots` resolves the latest SysON REST commit automatically
before listing root namespace elements. Use `--json-output` when you need the
raw root IDs for a scripted import.

Render, import, or run the full bridge:

```bash
mbse-lab bridge render exports/flexo/<flexo-project-id>.json --report
mbse-lab bridge import exports/sysml/<flexo-project-id>.sysml \
  --project-id <syson-project-id> \
  --namespace-id <syson-root-package-id>
mbse-lab bridge run <flexo-project-id> \
  --create-syson-project "Imported From Flexo" \
  --json-output
```

Use `--syson-project-id` and `--namespace-id` instead when importing into an
existing SysON project.

Inspect and verify the container deployment contract:

```bash
mbse-lab deployment contract
mbse-lab deployment verify
```

Use `--json-output` for machine-readable deployment contract or verification
output, and `--fixture` when testing an alternate deployment contract fixture.

## Legacy Script Compatibility

`mbse-lab` is the canonical user-facing command surface. The
`scripts/flexo_mms_env.py`, `scripts/flexo_syson_bridge.py`, and
`scripts/collect_diagnostics.py` entry points remain callable for compatibility
and maintainer workflows while their production logic is moved into package
modules. Prefer adding new user-visible behavior to `mbse-lab` first, then keep
scripts as thin shims or low-level escape hatches.

These commands expect to run from the shared lab repo. If you run the CLI from
another directory, pass `--repo-root`:

```bash
mbse-lab --repo-root ~/work/sysmlv2-lab doctor
```

## Related Docs

| Page | Why it matters |
| --- | --- |
| [Private Model Workspaces](private-model-workspaces.md) | Explains the `MBSE_MODEL_WORKSPACE` boundary used by bridge commands. |
| [CLI Reference](cli-reference.md) | Generated reference for every `mbse-lab` command and option. |
| [Services](services.md) | Focused service lifecycle, endpoint, status, and maintenance commands. |
| [Safety And Sharing](safety-and-sharing.md) | Share-check, credentials, service data, cleanup, and private artifact boundaries. |
| [Troubleshooting](troubleshooting.md) | Symptom-oriented recovery steps for common local lab failures. |
| [Bridge Workflow](../lab/flexo-syson-bridge.md) | Shows the Flexo export, SysML render, and SysON import sequence. |
| [Harness Engineering](../lab/harness-engineering.md) | Documents evals, diagnostics, reports, and guardrails behind the CLI. |
| [Release Process](release-process.md) | Uses the CLI for release smoke tests and share checks. |
