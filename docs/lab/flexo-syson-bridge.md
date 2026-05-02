# Flexo to SysON Bridge

This is the initial bridge path:

```mermaid
flowchart LR
    flexo["Flexo project<br/>SysML v2 REST API"]
    export["Flexo JSON export<br/>exports/flexo/*.json"]
    render["text renderer<br/>supported SysML v2 subset"]
    sysml["SysML v2 text<br/>exports/sysml/*.sysml"]
    syson["SysON project<br/>GraphQL textual import"]

    flexo --> export --> render --> sysml --> syson
```

The script is intentionally conservative. It preserves the Flexo JSON export and
renders a supported subset of SysML v2 textual notation for import into SysON.

## Private Model Workspaces

This repo is the shared tooling repo. Real model data should normally live in a
separate private workspace or private repository.

Set `MBSE_MODEL_WORKSPACE` before generating artifacts:

```bash
export MBSE_MODEL_WORKSPACE=~/work/my-private-models
```

When set, `flexo-export`, `render-sysml`, and `flexo-to-syson` default generated
artifacts to:

```text
$MBSE_MODEL_WORKSPACE/exports/
```

Use explicit `--output` or `--output-dir` paths when a run needs a different
location. The canonical boundary is documented in
[Private Model Workspaces](../user-guide/private-model-workspaces.md).

## Preflight

Make sure both stacks are running:

```bash
mbse-lab status
```

Initialize the Flexo org used by the SysML v2 service if project creation fails
with `Org <http://layer1-service/orgs/sysmlv2> does not exist`:

```bash
mbse-lab flexo init-org
mbse-lab flexo backup
```

The backup writes ignored N-Quads data under `deploy/flexo-mms/backups/`.
Refreshing the tracked startup seed requires `mbse-lab flexo backup
--update-init --i-understand-this-updates-tracked-seed` and should be used only
for synthetic, publishable seed data.

| Check | Command | Expected signal |
| --- | --- | --- |
| Service status | `mbse-lab status` | Flexo and SysON containers are reachable. |
| Flexo org exists | `mbse-lab flexo init-org` | Needed only when project creation reports the missing `sysmlv2` org. |
| Graph backup exists | `mbse-lab flexo backup` | Ignored backup file is written under `deploy/flexo-mms/backups/`. |

## Flexo Commands

| Task | CLI command |
| --- | --- |
| List projects | `mbse-lab flexo list` |
| Create project | `mbse-lab flexo create "Example Model"` |
| Export JSON | `mbse-lab flexo export <flexo-project-id>` |
| Render SysML text | `mbse-lab bridge render exports/flexo/<flexo-project-id>.json` |

## SysON Commands

| Task | CLI command |
| --- | --- |
| Create project | `mbse-lab syson create "Imported From Flexo"` |
| Find import namespace | `mbse-lab syson roots <syson-project-id>` |
| Import SysML text | `mbse-lab bridge import exports/sysml/<flexo-project-id>.sysml --project-id <syson-project-id> --namespace-id <syson-root-package-id>` |
| Run full pipeline | `mbse-lab bridge run <flexo-project-id> --syson-project-id <syson-project-id> --namespace-id <syson-root-package-id>` |

The roots command resolves the latest SysON REST commit before fetching root
namespace elements. Use `mbse-lab syson roots <syson-project-id> --json-output`
when you need the raw root package ID for `--namespace-id`.

For the full pipeline, the expanded CLI form is:

```bash
mbse-lab bridge run <flexo-project-id> \
  --syson-project-id <syson-project-id> \
  --namespace-id <syson-root-package-id>
```

## Artifacts

| Artifact | Default location | Share guidance |
| --- | --- | --- |
| Flexo JSON export | `exports/flexo/<flexo-project-id>.json` | Keep private unless the model is synthetic and publishable. |
| Rendered SysML text | `exports/sysml/<flexo-project-id>.sysml` | Derived from the export; keep private for real models. |
| Full-pipeline run log | `runs/flexo-to-syson/` | Ignored by git; may include private project IDs and names. |
| Private workspace exports | `$MBSE_MODEL_WORKSPACE/exports/` | Preferred location for real model bridge artifacts. |

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

## Renderer Reuse Assessment

A reuse spike checked whether this bridge could replace the local renderer with
an existing SysML v2 JSON-to-text path. No supported offline renderer was found.
SysON can export textual SysML from existing SysON EMF documents, but its public
REST data-version facade did not materialize a tested API-shaped Flexo payload
into an exportable document. The OMG SysML v2 Pilot Implementation has a
repository API to EMF path, but no supported JSON file to `.sysml` command.

For now, the supported path remains the conservative Python renderer shown
above. Keep additions fixture-driven, update
[Modeling Conventions](modeling-conventions.md), and validate generated text
through SysON import behavior before broadening the subset.

## Related Docs

| Page | Why it matters |
| --- | --- |
| [CLI](../user-guide/cli.md) | Describes the user-facing `mbse-lab bridge`, `flexo`, and `syson` commands. |
| [Private Model Workspaces](../user-guide/private-model-workspaces.md) | Defines where generated model artifacts should live. |
| [Modeling Conventions](modeling-conventions.md) | Lists supported rendered element types and naming rules. |
| [Transformation Pipeline](../methodology/sysml-v2-transformation-pipeline-design.md) | Places the bridge in the broader model transformation strategy. |
