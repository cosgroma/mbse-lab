# Modeling Conventions

This repo treats Flexo as the API-driven SysML v2 repository and SysON as the
graphical import/review environment. The bridge intentionally supports a narrow,
deterministic subset first, then expands as we verify importer behavior.

## Current Supported Textual Subset

The Flexo to SysON renderer currently emits these SysML v2 element types:

| Flexo `@type` | Rendered textual form |
| --- | --- |
| `Package` | `package <name> { ... }` or `package <name>;` |
| `PartDefinition` | `part def <name> { ... }` or `part def <name>;` |
| `PartUsage` | `part <name>;` |
| `AttributeUsage` | `attribute <name>;` |
| `PortUsage` | `port <name>;` |
| `RequirementDefinition` | `requirement def <name> { ... }` or `requirement def <name>;` |
| `RequirementUsage` | `requirement <name>;` |
| `ConnectionDefinition` | `connection def <name>;` |
| `ConnectionUsage` | `connection <name>;` |
| `InterfaceDefinition` | `interface def <name>;` |
| `InterfaceUsage` | `interface <name>;` |
| `ActionDefinition` | `action def <name>;` |
| `ActionUsage` | `action <name>;` |
| `ItemDefinition` | `item def <name>;` |
| `ItemUsage` | `item <name>;` |

Unsupported element types remain preserved in the Flexo JSON export and are not
emitted into `.sysml` yet.

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
