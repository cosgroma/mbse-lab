# Services

Use the `mbse-lab services` commands for routine Flexo and SysON lifecycle
operations. They wrap the repo-owned Docker Compose files while preserving the
service data directories by default.

## Endpoints

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

## Start

Create or refresh local runtime files first:

```bash
mbse-lab init
```

Start Flexo and SysON:

```bash
mbse-lab services up
```

By default, `services up` waits for the selected service APIs. Use `--no-wait`
only when you want container startup to return immediately.

Initialize the Flexo org used by the SysML v2 service after first setup:

```bash
mbse-lab flexo init-org
mbse-lab flexo backup
```

The backup step writes an ignored N-Quads backup under
`deploy/flexo-mms/backups/`. It does not refresh the tracked startup seed unless
you explicitly pass the seed-update flags.

## Status

Check local service status:

```bash
mbse-lab status
```

Check APIs directly when you need lower-level confirmation:

```bash
curl -s http://localhost:18083/projects | jq
curl -I http://localhost:18090/
```

Run a disposable deployment smoke test without touching normal local containers
or data:

```bash
mbse-lab deployment isolated-smoke
```

The isolated smoke test uses a unique Docker Compose project name, random
localhost-only host ports, and temporary bind-mounted data under
`tmp/isolated-deployments/`. It tears the stack down after verification unless
`--keep` is passed.

## Logs

Inspect recent logs:

```bash
mbse-lab services logs --tail 100
```

Use `--follow`, `--flexo-service`, and `--syson-service` for focused log
inspection.

## Stop And Restart

Stop both service families without deleting runtime data:

```bash
mbse-lab services down
```

Stop only SysON:

```bash
mbse-lab services down --no-flexo
```

Stop only Flexo:

```bash
mbse-lab services down --no-syson
```

Restart the lab:

```bash
mbse-lab services restart
```

Use `services down --volumes` only when you intentionally want to remove
Compose-managed volumes. It does not remove the ignored SysON Postgres bind
mount; see [Safety And Sharing](safety-and-sharing.md) for the service data
boundary.

## Maintenance

After meaningful Flexo graph changes:

```bash
mbse-lab flexo backup
```

Refresh the tracked synthetic startup seed only with explicit intent:

```bash
mbse-lab flexo backup --update-init --i-understand-this-updates-tracked-seed
```

Rotate ignored local Flexo credentials:

```bash
mbse-lab flexo rotate-secrets
mbse-lab services restart --no-syson
```

The forced Flexo regeneration path remains a maintainer operation because it may
overwrite local generated deployment files:

```bash
python3 scripts/flexo_mms_env.py init --with-sysmlv2 --force
```
