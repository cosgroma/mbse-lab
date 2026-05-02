# SysML v2 Local Lab Kit

[![Community profile](https://img.shields.io/badge/dynamic/json?label=community&query=%24.health_percentage&suffix=%25&url=https%3A%2F%2Fapi.github.com%2Frepos%2Fcosgroma%2Fmbse-lab%2Fcommunity%2Fprofile)](https://github.com/cosgroma/mbse-lab/community)
[![CI](https://github.com/cosgroma/mbse-lab/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/cosgroma/mbse-lab/actions/workflows/ci.yml)
[![Docs](https://github.com/cosgroma/mbse-lab/actions/workflows/documentation.yml/badge.svg?branch=main)](https://github.com/cosgroma/mbse-lab/actions/workflows/documentation.yml)
[![License: MIT](https://img.shields.io/github/license/cosgroma/mbse-lab)](LICENSE)
[![Python >=3.10](https://img.shields.io/badge/python-%3E%3D3.10-blue)](pyproject.toml)
[![SysML v2](https://img.shields.io/badge/SysML-v2-6f42c1)](https://github.com/cosgroma/mbse-lab)

This repo is a reusable local lab kit for starting SysML v2 work without making
this repo the home for the models themselves. It provides:

- OpenMBEE Flexo MMS as the graph-backed model repository and SysML v2 API service.
- Eclipse SysON as a graphical open-source SysML v2 editor.
- A bridge script that exports Flexo SysML v2 REST data, renders a `.sysml`
  textual snapshot, and imports it into SysON.

The current integration path is intentionally file/text based:

```mermaid
flowchart LR
    flexo["Flexo SysML v2 REST JSON"]
    snapshot["SysML v2 textual snapshot<br/>.sysml"]
    syson["SysON GraphQL import"]

    flexo --> snapshot --> syson
```

SysON and Flexo are separate repository stacks. Treat Flexo as the durable
repository path for API-driven experiments, and use SysON for graphical review or
editing of imported SysML v2 textual content.

## Common Goals

| I want to... | Use this | Details |
| --- | --- | --- |
| Install and inspect the command surface | `make install-cli` and `mbse-lab --help` | [CLI guide](docs/user-guide/cli.md) |
| Bootstrap the local lab for first use | `mbse-lab bootstrap --model-workspace ~/work/my-private-models` | [CLI bootstrap](docs/user-guide/cli.md#bootstrap) |
| Keep real model data outside this repo | `export MBSE_MODEL_WORKSPACE=~/work/my-private-models` | [Private model workspaces](docs/user-guide/private-model-workspaces.md) |
| Create a tiny end-to-end model | `mbse-lab first-model "My First Model"` | [First model](docs/user-guide/cli.md#first-model) |
| Move a Flexo snapshot into SysON | `mbse-lab bridge run <flexo-project-id>` | [Bridge workflow](docs/lab/flexo-syson-bridge.md) |
| Check what the bridge can render | Review supported element mappings | [Modeling conventions](docs/lab/modeling-conventions.md) |
| Collect failure evidence | `mbse-lab diagnostics` | [Harness engineering](docs/lab/harness-engineering.md#observability) |
| Prepare a release | Run the release checklist | [Release process](docs/user-guide/release-process.md) |

## Tooling Repo, Not Model Repo

Use this repo for the container deployment, setup scripts, bridge workflow,
diagnostics, documentation, and public synthetic fixtures. Keep real SysML v2
models in a separate private workspace or private repository.

Recommended layout:

```mermaid
flowchart LR
    public["mbse-lab<br/>public tooling repo"]
    private["private model workspace<br/>or private repository"]

    public --> tooling["compose files<br/>CLI<br/>bridge scripts<br/>docs<br/>synthetic fixtures"]
    private --> models["real SysML v2 models<br/>private exports<br/>generated snapshots"]
    public -. "MBSE_MODEL_WORKSPACE" .-> private
```

```text
~/work/sysmlv2-lab/             this shared tooling repo
~/work/my-private-models/       private model workspace or private repo
```

Set `MBSE_MODEL_WORKSPACE` when you want generated bridge artifacts to default
outside this repo:

```bash
export MBSE_MODEL_WORKSPACE=~/work/my-private-models
```

With that variable set, `flexo-export`, `render-sysml`, and `flexo-to-syson`
write generated artifacts under `$MBSE_MODEL_WORKSPACE/exports/` unless you pass
explicit `--output` or `--output-dir` paths. See the
[private model workspace guide](docs/user-guide/private-model-workspaces.md) for
the full boundary.

## Layout

| Path | Purpose |
| --- | --- |
| [deploy/flexo-mms/](deploy/flexo-mms/README.md) | Flexo MMS Docker Compose environment. |
| [deploy/syson/](deploy/syson/README.md) | SysON Docker Compose environment. |
| [docs/index.md](docs/index.md) | Documentation landing page and task router. |
| [docs/user-guide/](docs/user-guide/cli.md) | CLI, release, and private workspace guidance. |
| [docs/lab/](docs/lab/flexo-syson-bridge.md) | Local lab operations, bridge behavior, and harness notes. |
| [docs/methodology/](docs/methodology/sysml-v2-verification-model-setup.md) | Reusable SysML v2 setup and transformation guidance. |
| [docs/model-specs/](docs/model-specs/rf-link-budget.md) | General-purpose model specifications. |
| [docs/plans/](docs/plans/README.md) | Active and completed execution plans. |
| [exports/](exports/README.md) | Curated publishable example exports only. |
| [WORKFLOW.md](WORKFLOW.md) | Repo-owned workflow contract for agent work. |
| `scripts/flexo_mms_env.py` | Flexo environment manager. |
| `scripts/flexo_syson_bridge.py` | Flexo/SysON bridge and helper CLI. |

## Requirements

- Docker with the Compose plugin
- Python 3.10+
- Hatch for reproducible Python tooling and MkDocs environments
- `curl` and `jq` are useful for inspection, but not required by the Python
  scripts

No Python packages are required for the scripts; they use the standard library.

## Documentation Site

The Markdown documentation under `docs/` is organized for MkDocs. Build the site
through the Hatch-managed docs environment:

```bash
make docs-build
```

Release steps are documented in the
[release process](docs/user-guide/release-process.md).

Serve it locally while editing:

```bash
make docs-serve
```

## CLI

Install the local CLI in editable mode:

```bash
make install-cli
```

Install directly from GitHub when you do not need an editable checkout:

```bash
python3 -m pip install "git+https://github.com/cosgroma/mbse-lab.git"
```

Then inspect the available commands:

```bash
mbse-lab --help
```

Print shell completion setup:

```bash
mbse-lab completion bash
```

Start with file setup and the environment doctor:

```bash
mbse-lab init --model-workspace ~/work/my-private-models
mbse-lab doctor
mbse-lab doctor --fix
```

The CLI is a user-facing wrapper around the same Flexo, SysON, bridge,
diagnostics, and deployment-verification workflows documented below.

For first use, run the guided bootstrap:

```bash
mbse-lab bootstrap --model-workspace ~/work/my-private-models
```

Use `mbse-lab init` when you only want to generate local env files and optional
workspace scaffolding without starting containers.

Preview the bootstrap without changing files or starting containers:

```bash
mbse-lab bootstrap --dry-run --model-workspace ~/work/my-private-models
```

After setup, routine service lifecycle commands are available through the CLI:

```bash
mbse-lab services up
mbse-lab services logs
mbse-lab services down
```

Create a tiny first model after the services are running:

```bash
mbse-lab first-model "My First Model"
```

That command creates a Flexo project with one package, exports and renders the
model, creates a SysON review project, imports the rendered SysML text, and
prints the resulting project IDs and artifact paths.

Routine bridge operations are also available through the CLI:

```bash
mbse-lab flexo list
mbse-lab syson list
mbse-lab bridge run <flexo-project-id> \
  --syson-project-id <syson-project-id> \
  --namespace-id <syson-root-package-id>
```

Before sharing or publishing the tooling repo, run:

```bash
mbse-lab share-check
```

It checks for accidentally tracked runtime env files, service data, generated
private exports, run logs, diagnostics bundles, and known local secret patterns.

Generate a static local lab report:

```bash
mbse-lab report
```

The report writes Markdown, HTML, and JSON snapshots under `reports/latest/`.

Remove generated local reports, diagnostics, run logs, and temporary output:

```bash
mbse-lab cleanup
```

Use `mbse-lab cleanup --dry-run` to preview cleanup targets first.

## Credentials

Runtime credential files are intentionally ignored by git:

```text
deploy/flexo-mms/.env
deploy/flexo-mms/env/*.env
deploy/syson/.env
```

Publishable templates are committed as `.example` files. Flexo runtime env files
are generated by:

```bash
python3 scripts/flexo_mms_env.py init --with-sysmlv2
```

Rotate local Flexo credentials at any time:

```bash
python3 scripts/flexo_mms_env.py rotate-secrets
```

Restart Flexo after rotating credentials. For SysON, create a local env file
from the example and set a private database password:

```bash
cp deploy/syson/.env.example deploy/syson/.env
```

## Services

| Stack | Endpoint | URL |
| --- | --- | --- |
| Flexo MMS | Layer1 API | <http://localhost:18080> |
| Flexo MMS | SysML v2 API | <http://localhost:18083> |
| Flexo MMS | Auth login | <http://localhost:8082/login> |
| Flexo MMS | Fuseki | <http://localhost:3030> |
| Flexo MMS | MinIO | <http://localhost:9000> |
| SysON | Web UI | <http://localhost:18090> |
| SysON | GraphQL API | <http://localhost:18090/api/graphql> |
| SysON | REST API docs | <http://localhost:18090/v3/api-docs/rest-apis> |

## Initialize

Create or refresh the Flexo deployment files:

```bash
python3 scripts/flexo_mms_env.py init --with-sysmlv2
```

Start Flexo:

```bash
python3 scripts/flexo_mms_env.py up --wait --timeout 60
```

Start SysON:

```bash
docker compose -f deploy/syson/docker-compose.yml up -d
```

Initialize the Flexo org used by the SysML v2 service:

```bash
python3 scripts/flexo_syson_bridge.py init-flexo-org
python3 scripts/flexo_mms_env.py backup
```

The backup step is important. The local Fuseki container starts from
`deploy/flexo-mms/mount/cluster.trig`, so initialization changes should be
persisted there.

## Health Checks

Check Flexo containers:

```bash
python3 scripts/flexo_mms_env.py status --with-sysmlv2 --strict
```

Check SysON containers:

```bash
docker compose -f deploy/syson/docker-compose.yml ps
```

Check APIs:

```bash
curl -s http://localhost:18083/projects | jq
curl -I http://localhost:18090/
```

Run a disposable deployment smoke test without touching the normal local lab
containers or data:

```bash
mbse-lab deployment isolated-smoke
```

The isolated smoke test uses a unique Docker Compose project name, random
localhost-only host ports, and temporary bind-mounted data under
`tmp/isolated-deployments/`. It tears the stack down after verification unless
`--keep` is passed.

Get a Flexo auth token:

```bash
python3 scripts/flexo_mms_env.py token
```

## Data Safety

Flexo model graph data is stored in Fuseki. In this local setup, Fuseki is
started from:

```text
deploy/flexo-mms/mount/cluster.trig
```

Use the backup command after creating important model data or changing Flexo
cluster/org setup:

```bash
python3 scripts/flexo_mms_env.py backup
```

Backups are written to:

```text
deploy/flexo-mms/backups/
```

SysON stores its database in a host bind mount:

```text
deploy/syson/data/postgres/
```

Normal `docker compose down` will not delete that data. Avoid `down --volumes`
or manual deletion of the data directories unless you intentionally want to
reset the environment.

## Common Workflows

| Workflow | CLI command | Script command |
| --- | --- | --- |
| List Flexo projects | `mbse-lab flexo list` | `python3 scripts/flexo_syson_bridge.py flexo-list-projects` |
| Create a Flexo SysML v2 project | `mbse-lab flexo create "Example Model"` | `python3 scripts/flexo_syson_bridge.py flexo-create-project "Example Model"` |
| Export Flexo JSON | `mbse-lab flexo export <flexo-project-id>` | `python3 scripts/flexo_syson_bridge.py flexo-export <flexo-project-id>` |
| Render JSON to SysML text | `mbse-lab bridge render exports/flexo/<flexo-project-id>.json` | `python3 scripts/flexo_syson_bridge.py render-sysml exports/flexo/<flexo-project-id>.json` |
| Create a SysON project | `mbse-lab syson create "Imported From Flexo"` | `python3 scripts/flexo_syson_bridge.py syson-create-project "Imported From Flexo"` |
| Find a SysON import namespace | `mbse-lab syson roots <syson-project-id>` | `python3 scripts/flexo_syson_bridge.py syson-roots <syson-project-id>` |
| Import a `.sysml` file into SysON | `mbse-lab bridge import exports/sysml/<flexo-project-id>.sysml --project-id <syson-project-id> --namespace-id <syson-root-package-id>` | `python3 scripts/flexo_syson_bridge.py syson-import-text exports/sysml/<flexo-project-id>.sysml --project-id <syson-project-id> --namespace-id <syson-root-package-id>` |
| Run the full Flexo-to-SysON pipeline | `mbse-lab bridge run <flexo-project-id> --syson-project-id <syson-project-id> --namespace-id <syson-root-package-id>` | `python3 scripts/flexo_syson_bridge.py flexo-to-syson <flexo-project-id> --syson-project-id <syson-project-id> --namespace-id <syson-root-package-id>` |

Default artifacts are written under `exports/flexo/` and `exports/sysml/`, or
under `$MBSE_MODEL_WORKSPACE/exports/` when the private workspace variable is
set. The [bridge workflow](docs/lab/flexo-syson-bridge.md) has the full command
sequence and output table.

## Stop and Restart

Stop SysON:

```bash
docker compose -f deploy/syson/docker-compose.yml down
```

Stop Flexo:

```bash
python3 scripts/flexo_mms_env.py down
```

Restart:

```bash
python3 scripts/flexo_mms_env.py up --wait --timeout 60
docker compose -f deploy/syson/docker-compose.yml up -d
```

## Maintenance

After meaningful Flexo changes:

```bash
python3 scripts/flexo_mms_env.py backup
```

Inspect logs:

```bash
python3 scripts/flexo_mms_env.py logs --tail 100
docker compose -f deploy/syson/docker-compose.yml logs --tail 100 app
```

Update generated Flexo deployment files:

```bash
python3 scripts/flexo_mms_env.py init --with-sysmlv2 --force
```

Be careful with `--force`: it may overwrite local generated deployment files.
Back up first if you have local edits.

Rotate ignored local Flexo credentials:

```bash
python3 scripts/flexo_mms_env.py rotate-secrets
python3 scripts/flexo_mms_env.py down
python3 scripts/flexo_mms_env.py up --wait --timeout 60
```

## Current Bridge Scope

The bridge renderer currently emits a practical subset of SysML v2:

- `Package`
- `PartDefinition`
- `PartUsage`
- `AttributeUsage`
- `PortUsage`
- `RequirementDefinition`
- `RequirementUsage`
- `ConnectionDefinition`
- `ConnectionUsage`
- `InterfaceDefinition`
- `InterfaceUsage`
- `ActionDefinition`
- `ActionUsage`
- `ItemDefinition`
- `ItemUsage`

Unsupported element types remain preserved in the Flexo JSON export, but are not
rendered into the textual `.sysml` file yet. Diagram layout is not round-tripped.

## Troubleshooting

If Flexo project creation fails with:

```text
Org <http://layer1-service/orgs/sysmlv2> does not exist
```

Run:

```bash
python3 scripts/flexo_syson_bridge.py init-flexo-org
python3 scripts/flexo_mms_env.py backup
```

If a host port is already in use, edit the relevant `.env` file:

```text
deploy/flexo-mms/.env
deploy/syson/.env
```

Then restart the affected stack.

If SysON import succeeds but nothing useful appears graphically, check the
generated `.sysml` file first. The import path depends on SysON's textual SysML
parser, and the current renderer is intentionally conservative.
