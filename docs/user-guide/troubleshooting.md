# Troubleshooting

Start with a structured environment check:

```bash
mbse-lab doctor
```

Apply low-risk local setup fixes:

```bash
mbse-lab doctor --fix
```

Collect diagnostics after service failures:

```bash
mbse-lab diagnostics
```

Use a reduced bundle when the output may be shared outside a private project
team:

```bash
mbse-lab diagnostics --public-safe
```

## Docker Is Not Running

Likely cause: Docker Desktop or the Docker daemon is stopped, or the current
user cannot access the Docker socket.

Check:

```bash
mbse-lab doctor
docker compose version
```

Recovery:

Start Docker, then rerun:

```bash
mbse-lab services up
```

If Docker is running but access fails, fix local Docker permissions outside this
repo and rerun `mbse-lab doctor`.

## Port Conflict

Likely cause: another local process is already using one of the Flexo or SysON
host ports.

Check:

```bash
mbse-lab doctor
mbse-lab status
```

Recovery:

Edit the relevant ignored env file:

```text
deploy/flexo-mms/.env
deploy/syson/.env
```

Then restart the affected stack:

```bash
mbse-lab services restart
```

## Flexo Org Is Missing

Symptom:

```text
Org <http://layer1-service/orgs/sysmlv2> does not exist
```

Likely cause: the Flexo SysML v2 org has not been initialized in the local
Fuseki graph.

Recovery:

```bash
mbse-lab flexo init-org
mbse-lab flexo backup
```

Then retry the Flexo create or bridge command.

## SysON Password Drift

Likely cause: `deploy/syson/.env` was regenerated or edited after Postgres data
already existed under `deploy/syson/data/postgres/`.

Check:

```bash
mbse-lab doctor
mbse-lab services logs --syson-service syson-app --tail 80
```

Recovery:

Restore the password that matches the persisted database, or intentionally reset
the local SysON database by stopping services and removing the ignored Postgres
data directory. Only remove the data directory when you accept losing local
SysON projects.

```bash
mbse-lab services down --no-flexo
```

After the password or data reset is fixed:

```bash
mbse-lab services up --no-flexo
```

## SysON Starts Slowly

Likely cause: first startup, database migration, or a busy local Docker engine.

Check:

```bash
mbse-lab services logs --syson-service syson-app --tail 100
curl -I http://localhost:18090/
```

Recovery:

Increase the wait timeout:

```bash
mbse-lab services up --timeout 180
```

If the app keeps restarting, collect diagnostics:

```bash
mbse-lab diagnostics --public-safe
```

## Import Succeeds But The Diagram Looks Empty

Likely cause: the bridge imports textual SysML into SysON, but diagram layout is
not round-tripped. The current renderer also emits a conservative subset of
SysML v2 element types.

Check the rendered text and coverage report first:

```bash
mbse-lab bridge render exports/flexo/<flexo-project-id>.json --report
mbse-lab report
```

Recovery:

Open the imported package in SysON and create or adjust graphical views there.
Use the render coverage report to see which Flexo element types were rendered,
unsupported, or skipped. The bridge is a snapshot import path, not a live
diagram sync.
