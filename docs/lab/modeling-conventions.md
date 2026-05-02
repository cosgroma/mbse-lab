# Modeling Conventions

This repo treats Flexo as the API-driven SysML v2 repository and SysON as the
graphical import/review environment. The bridge intentionally supports a narrow,
deterministic subset first, then expands as we verify importer behavior.

## Current Supported Textual Subset

The Flexo to SysON renderer currently emits these SysML v2 element types. The
matrix is intentionally tied to the renderer registry and fixture assertions.

| Flexo `@type` | Rendered textual form | Fixture coverage | Validation status |
| --- | --- | --- | --- |
| `Package` | `package <name> { ... }` or `package <name>;` | `flexo-basic-package`, `rf-link-budget-basic`, `container-deployment-basic` | deterministic render test |
| `PartDefinition` | `part def <name> { ... }` or `part def <name>;` | `flexo-basic-package`, `rf-link-budget-basic`, `container-deployment-basic` | deterministic render test |
| `PartUsage` | `part <name>;` | `rf-link-budget-basic`, `container-deployment-basic` | deterministic render test |
| `AttributeUsage` | `attribute <name>;` | `flexo-basic-package`, `rf-link-budget-basic` | deterministic render test |
| `PortUsage` | `port <name>;` | `flexo-basic-package` | deterministic render test |
| `RequirementDefinition` | `requirement def <name> { ... }` or `requirement def <name>;` | `flexo-basic-package`, `rf-link-budget-basic`, `container-deployment-basic` | deterministic render test |
| `RequirementUsage` | `requirement <name>;` | planned fixture expansion | renderer registry only |
| `ConnectionDefinition` | `connection def <name>;` | planned fixture expansion | renderer registry only |
| `ConnectionUsage` | `connection <name>;` | planned fixture expansion | renderer registry only |
| `InterfaceDefinition` | `interface def <name>;` | planned fixture expansion | renderer registry only |
| `InterfaceUsage` | `interface <name>;` | planned fixture expansion | renderer registry only |
| `ActionDefinition` | `action def <name>;` | planned fixture expansion | renderer registry only |
| `ActionUsage` | `action <name>;` | planned fixture expansion | renderer registry only |
| `ItemDefinition` | `item def <name>;` | planned fixture expansion | renderer registry only |
| `ItemUsage` | `item <name>;` | planned fixture expansion | renderer registry only |

Unsupported element types remain preserved in the Flexo JSON export and are not
emitted into `.sysml` yet. `mbse-lab bridge render --report` writes a
`render-report.json` file with rendered, skipped, and unsupported counts by
Flexo `@type` plus warnings for unsupported types.

## Naming

Names are sanitized for textual SysML output:

- non-alphanumeric characters become `_`
- empty names become `Unnamed`
- names starting with a digit are prefixed with `_`

This makes the renderer deterministic and keeps generated text importable by
SysON's textual parser.

## State And Ownership

- Flexo JSON exports are the raw source snapshots.
- Generated `.sysml` files are derived artifacts.
- SysON imports are snapshots, not live sync.
- Diagram layout is not round-tripped.

## Expansion Rules

Before adding a new rendered element type:

1. Add or update a fixture under `evals/fixtures/`.
2. Add assertions in `evals/test_bridge_render.py`.
3. Update the table in this file.
4. Run `make eval` and `make check`.

Prefer small, verified additions over broad guessed mappings. When Flexo JSON
shape is unclear, preserve the raw JSON and defer textual rendering until the
mapping can be tested.

## Related Docs

| Page | Why it matters |
| --- | --- |
| [Bridge Workflow](flexo-syson-bridge.md) | Shows where these mappings are used in the Flexo-to-SysON pipeline. |
| [Transformation Pipeline](../methodology/sysml-v2-transformation-pipeline-design.md) | Describes broader transformation rules for model-derived artifacts. |
| [Verification Model Setup](../methodology/sysml-v2-verification-model-setup.md) | Provides package and traceability conventions for source model structure. |
