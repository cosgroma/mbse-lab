# Safety And Sharing

This repo is tooling. Keep real SysML v2 source, private Flexo exports,
rendered snapshots, run logs, and service evidence in a private workspace or
private repository.

## Private Workspace Boundary

Recommended layout:

```text
~/work/sysmlv2-lab/             shared tooling repo
~/work/my-private-models/       private model workspace or private repo
```

Set `MBSE_MODEL_WORKSPACE` when you want generated bridge artifacts to default
outside this repo:

```bash
export MBSE_MODEL_WORKSPACE=~/work/my-private-models
```

With that variable set, `flexo-export`, `render-sysml`, and `flexo-to-syson`
write generated artifacts under `$MBSE_MODEL_WORKSPACE/exports/` unless you
pass explicit output paths.

## Runtime Credentials

Runtime credential files are intentionally ignored by git:

```text
deploy/flexo-mms/.env
deploy/flexo-mms/env/*.env
deploy/syson/.env
```

Commit only the `.example` templates. Generate local runtime env files with:

```bash
mbse-lab init
```

Rotate local Flexo credentials at any time:

```bash
mbse-lab flexo rotate-secrets
```

Restart Flexo after rotating credentials. For SysON, `mbse-lab init` creates
`deploy/syson/.env` from the example and replaces the placeholder database
password. When doing that manually, copy the template and set a private
password:

```bash
cp deploy/syson/.env.example deploy/syson/.env
```

## Service Data

Flexo model graph data is stored in Fuseki. In this local setup, Fuseki starts
from:

```text
deploy/flexo-mms/mount/cluster.nq
```

Use a backup after creating important model data or changing Flexo cluster/org
setup:

```bash
mbse-lab flexo backup
```

Backups are written to ignored storage:

```text
deploy/flexo-mms/backups/
```

Updating the tracked startup seed requires explicit intent and should be used
only for synthetic, publishable startup data:

```bash
mbse-lab flexo backup --update-init --i-understand-this-updates-tracked-seed
```

SysON stores its database in a host bind mount:

```text
deploy/syson/data/postgres/
```

Normal `mbse-lab services down` keeps that data. Avoid deleting data directories
unless you intentionally want to reset the environment.

## Share Check

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
When bridge run logs exist, it links the latest run log and generated artifact
paths and summarizes render coverage counts without embedding model content.

Remove generated local reports, diagnostics, run logs, and temporary output:

```bash
mbse-lab cleanup
```

Use `mbse-lab cleanup --dry-run` to preview cleanup targets first.
