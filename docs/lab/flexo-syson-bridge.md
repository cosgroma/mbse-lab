# Flexo to SysON Bridge

This is the initial bridge path:

```text
Flexo SysML v2 REST JSON -> SysML v2 textual .sysml -> SysON GraphQL import
```

The script is intentionally conservative. It preserves the Flexo JSON export and
renders a supported subset of SysML v2 textual notation for import into SysON.

## Preflight

Make sure both stacks are running:

```bash
python3 scripts/flexo_mms_env.py status --with-sysmlv2
docker compose -f deploy/syson/docker-compose.yml ps
```

Initialize the Flexo org used by the SysML v2 service if project creation fails
with `Org <http://layer1-service/orgs/sysmlv2> does not exist`:

```bash
python3 scripts/flexo_syson_bridge.py init-flexo-org
python3 scripts/flexo_mms_env.py backup
```

The backup matters because the local Fuseki container starts from
`deploy/flexo-mms/mount/cluster.trig`.

## Flexo Commands

```bash
python3 scripts/flexo_syson_bridge.py flexo-list-projects
python3 scripts/flexo_syson_bridge.py flexo-create-project "Example Model"
python3 scripts/flexo_syson_bridge.py flexo-export <flexo-project-id>
python3 scripts/flexo_syson_bridge.py render-sysml exports/flexo/<flexo-project-id>.json
```

## SysON Commands

Create a SysON project:

```bash
python3 scripts/flexo_syson_bridge.py syson-create-project "Imported From Flexo"
```

Find a namespace/root element to import into:

```bash
python3 scripts/flexo_syson_bridge.py syson-roots <syson-project-id>
```

Import a generated `.sysml` file:

```bash
python3 scripts/flexo_syson_bridge.py syson-import-text \
  exports/sysml/<flexo-project-id>.sysml \
  --project-id <syson-project-id> \
  --namespace-id <syson-root-package-id>
```

Or run the full pipeline:

```bash
python3 scripts/flexo_syson_bridge.py flexo-to-syson <flexo-project-id> \
  --syson-project-id <syson-project-id> \
  --namespace-id <syson-root-package-id>
```

## Current Scope

The renderer currently handles a practical subset:

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

Unsupported element types remain in the raw Flexo JSON export but are not emitted
into the textual `.sysml` file yet.
