# Feature: Optional SysML v2 Starter Libraries

Status: Proposed

Release Target: `v0.6.0` candidate

## Problem

New users currently start from a tiny generated model or a blank project. That
is useful for smoke testing, but it does not give them reusable package
structure, requirement organization, deployment concepts, or public reference
content for meaningful SysML v2 experiments.

The repo already contains public model specifications and fixtures, but there
is no formal way to discover or include small public starter libraries when
creating a new model.

## Rationale

Starter libraries extend the lab kit without changing its safety boundary. They
reduce blank-canvas friction, provide deterministic public content for bridge
validation, and make first-use demos more representative. Deferring them until
private workspace and bridge coverage gates are stable keeps the repo from
drifting into a general model-content repository.

## Target Users

- MBSE beginners who need useful starting structure instead of a blank canvas.
- Systems engineers creating repeatable local experiments.
- Maintainers adding deterministic bridge fixtures and public examples.
- Technical leads evaluating whether the lab can support reusable modeling
  workflows.

## Non-Goals

- Do not create an authoritative SysML v2 standard library ecosystem.
- Do not store customer, program, product, vendor, or operationally sensitive
  model content.
- Do not introduce a package manager in the first version.
- Do not require starter libraries for `first-model` or normal bridge use.
- Do not rely on SysON-specific library IDs until that path is proven portable.

## Current Behavior And Evidence

- `mbse-lab first-model` creates a tiny model for end-to-end workflow proof.
- SysON project creation currently sends an empty library list.
- Public model specifications already exist under `docs/model-specs/`.
- Public renderer fixtures already exist under `evals/fixtures/`.
- Curated public output is allowed only under explicit example paths.
- The roadmap keeps generated private artifacts outside this repo by default.

## Proposed Behavior

Add a small, public, optional starter library catalog. The first version should
start with three libraries:

| Library | Purpose |
| --- | --- |
| `base` | Generic package and definition scaffolding. |
| `requirements` | Requirement, verification, and traceability starter structure. |
| `deployment` | Deployment and runtime verification concepts aligned with the existing container deployment model spec. |

The first implementation should use textual copy/include behavior rather than a
full dependency mechanism. Selected libraries would be copied into generated
SysML artifacts or imported through the same conservative text-based workflow
as other synthetic examples.

Target-state command examples:

```text
mbse-lab libraries list
mbse-lab libraries show deployment
mbse-lab first-model "Demo" --library base --library requirements
mbse-lab libraries render deployment --output ~/work/my-private-models/source/libraries/deployment.sysml
```

## CLI, Docs, And API Impact

- Add a future `mbse-lab libraries` command group for discovery, inspection,
  rendering, and possibly import.
- Add a future `--library` option to model creation workflows once the catalog
  format is stable.
- Add a catalog directory such as:

```text
libraries/
  catalog.json
  base/
    library.json
    base.sysml
    README.md
  requirements/
    library.json
    requirements.sysml
    README.md
  deployment/
    library.json
    deployment.sysml
    README.md
```

- Document each library as public, synthetic, optional starter content.
- Keep generated model instances routed through the private workspace policy.

Example library metadata:

```json
{
  "id": "deployment",
  "name": "Deployment Starter Library",
  "version": "0.1.0",
  "description": "Public starter SysML v2 library for local deployment and runtime verification concepts.",
  "entrypoint": "deployment.sysml",
  "tags": ["deployment", "docker", "verification"],
  "publicSafe": true,
  "supportedByBridge": true,
  "testedFixtures": ["evals/fixtures/container-deployment-basic.json"],
  "dependencies": ["base"]
}
```

## Data And Credential Safety

Starter libraries must be public, synthetic, small, versioned, and test-backed.
They must not include private model data, generated private exports, runtime
service data, credentials, diagnostics, or run logs.

Each library should declare `publicSafe: true` in metadata. Any allowlist for
library paths in `share-check` must be explicit and narrow.

Generated model instances that use starter libraries are still private by
default and should be written under `MBSE_MODEL_WORKSPACE` or an explicit output
path.

## Validation Plan

- Validate catalog metadata with deterministic tests.
- Render every starter library fixture deterministically.
- Tie each library to the SysML coverage matrix once that matrix exists.
- Run `make docs-check` after adding CLI/docs examples.
- Run `make check` before landing implementation.
- Use live SysON import validation only after the textual workflow is stable.

## Acceptance Criteria

- A public library catalog lists `base`, `requirements`, and `deployment`.
- Library metadata declares ID, version, entrypoint, public-safety status,
  dependencies, and fixture coverage.
- Users can inspect a library without starting Docker services.
- Generated artifacts still follow the private workspace boundary.
- Library content is covered by deterministic render tests.
- Docs state that starter libraries are optional lab scaffolds, not
  authoritative standards.

## Rollout And Compatibility Notes

This should be additive and deferred until first-use reliability, private
workspace policy, and bridge coverage reporting are stable. The first version
should prefer textual copy/include behavior. SysON `libraryIds` integration can
be a later SysON-specific enhancement if the API proves stable.

## Open Decisions

- Should catalog files live under `libraries/` or under `docs/model-libraries/`
  with rendered examples elsewhere?
- Should `first-model` accept `--library`, or should library use start with a
  new model/template command?
- Should starter libraries be represented first as `.sysml` text, Flexo-style
  JSON fixtures, or both?
- What minimum bridge coverage is required before a starter library can be
  marked supported?
