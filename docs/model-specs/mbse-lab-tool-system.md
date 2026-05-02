# MBSE Lab Tool System SysML v2 Model Specification

This document specifies the first SysML v2 model for this repository itself.
The system of interest is the reusable MBSE lab tooling repo: the command-line
tool, scripts, Docker deployments, bridge workflow, diagnostics, private
workspace boundary, documentation, and verification harness.

The model is intended to be useful as both:

- A semantic model of the lab tool's landed requirements, architecture,
  workflows, runtime services, generated artifacts, and verification evidence.
- A publishable fixture source for improving the Flexo-to-SysON bridge and for
  identifying the next high-value features.

## Goals

- Capture landed user-visible behavior as testable requirements.
- Trace requirements to commands, scripts, docs, Docker services, generated
  artifacts, and validation checks.
- Represent the Flexo-to-SysON snapshot workflow as the core model interchange
  path.
- Preserve the repo boundary between shared tooling and private model data.
- Use the model to expose gaps in automation, verification, rendering coverage,
  and documentation.
- Keep the initial fixture synthetic and small enough to publish in this repo.

## Non-Goals

- This model will not be the home for private user SysML v2 models.
- This model will not claim full SysML v2 semantic coverage while the bridge
  renderer intentionally supports a conservative subset.
- This model will not model live bidirectional synchronization between Flexo and
  SysON.
- This model will not replace the Docker Compose files, CLI implementation,
  tests, or documentation.

## References

- User guide: `README.md`
- Workflow contract: `WORKFLOW.md`
- Agent guide: `AGENTS.md`
- CLI implementation: `src/mbse_lab/cli.py`
- Flexo environment manager: `scripts/flexo_mms_env.py`
- Flexo/SysON bridge: `scripts/flexo_syson_bridge.py`
- Bridge notes: `docs/lab/flexo-syson-bridge.md`
- Harness notes: `docs/lab/harness-engineering.md`
- Modeling conventions: `docs/lab/modeling-conventions.md`
- Private workspace guide: `docs/user-guide/private-model-workspaces.md`
- Container deployment model: `docs/model-specs/container-deployment.md`
- Active plan: `docs/plans/active/mbse-lab-sysml-model-plan.md`

## Model Boundary

The model covers the shared tooling system:

```text
repo and CLI
  -> initialization and bootstrap
  -> local Flexo and SysON runtime deployment
  -> private model workspace boundary
  -> Flexo project operations
  -> SysON project operations
  -> Flexo JSON export
  -> conservative SysML text rendering
  -> SysON textual import
  -> diagnostics, reports, cleanup, and share checks
  -> deterministic and optional live verification
```

Private model source, private Flexo JSON exports, private rendered snapshots,
and run evidence from real programs are outside this model boundary unless
curated as synthetic examples.

## Stakeholders And Concerns

| Stakeholder | Concern |
| --- | --- |
| First-time local user | Bootstrap should create the expected local files, start services when requested, and provide clear next commands. |
| Returning local user | Service lifecycle, diagnostics, reports, cleanup, backup, and restore should be repeatable and non-destructive by default. |
| Model author | Generated artifacts should default to a private workspace, not the shared tooling repo. |
| Reviewer | Flexo snapshots should be importable into SysON for graphical review. |
| Maintainer | Requirements, commands, docs, fixtures, and evals should stay traceable. |
| Release publisher | The repo should pass share checks and avoid committed secrets or private model data. |
| Future agent | Operating rules, plans, checks, and model structure should make work resumable. |

## Viewpoints

The first increment should support these views:

- User workflow view: bootstrap, first model, bridge review, diagnostics, and
  release validation.
- Command surface view: CLI commands, Make targets, and lower-level scripts.
- Runtime deployment view: Flexo stack, SysON stack, ports, data mounts, and API
  probes.
- Artifact view: env templates, runtime env files, Flexo exports, rendered
  SysML, diagnostics bundles, run logs, reports, and fixtures.
- Requirement trace view: landed requirements to implementation and checks.
- Verification trace view: deterministic checks, live evals, docs checks,
  share checks, and deployment verification.

## MDA Methodology Alignment

```text
CIM-like layer
  Stakeholders, setup needs, data safety concerns, graphical review needs,
  release/share concerns, and agent handoff needs.

PIM-like layer
  Tool capabilities, bridge workflow, workspace boundary, artifact lifecycle,
  diagnostics behavior, and verification intent independent of implementation.

PSM-like layer
  Click CLI commands, Python scripts, Docker Compose files, local host ports,
  env files, ignored runtime paths, Make targets, and unittest evals.

Generated and evidence artifacts
  Flexo JSON exports, rendered .sysml snapshots, run logs, diagnostics bundles,
  reports, deployment verification JSON, and validation command output.
```

## Recommended Package Structure

```text
MBSELabToolSystem
  Libraries
    Tooling
    Workflow
    Deployment
    Verification
  Stakeholders_Concerns
  SystemContext
  Requirements
    BootstrapRequirements
    ServiceLifecycleRequirements
    PrivateWorkspaceRequirements
    BridgeRequirements
    RenderingRequirements
    DiagnosticsReportingRequirements
    ShareSafetyRequirements
    VerificationRequirements
    DocumentationRequirements
  Architecture
    CommandArchitecture
    ScriptArchitecture
    RuntimeDeploymentArchitecture
    ArtifactArchitecture
    BridgePipelineArchitecture
  Workflows
    BootstrapWorkflow
    FirstModelWorkflow
    FlexoToSysONSnapshotWorkflow
    DiagnosticsWorkflow
    ReleaseValidationWorkflow
  Verification
    DeterministicChecks
    LiveServiceChecks
    ShareSafetyChecks
    DocumentationChecks
    DeploymentVerificationChecks
  Views_Viewpoints
```

## Landed Feature Requirements

### Bootstrap And Initialization

| Requirement | Statement | Evidence |
| --- | --- | --- |
| `BootstrapLocalLab` | The tool shall initialize local Flexo and SysON runtime files and optionally initialize a private model workspace. | `mbse-lab init`, `mbse-lab bootstrap`, `make init` |
| `PreviewBootstrapChanges` | The tool shall provide dry-run modes for setup workflows that would otherwise change files or containers. | `mbse-lab init --dry-run`, `mbse-lab bootstrap --dry-run` |
| `ReportServiceEndpoints` | The tool shall print local Flexo and SysON service URLs after startup-oriented workflows. | `mbse-lab services up`, `mbse-lab bootstrap` |

### Service Lifecycle And Data Safety

| Requirement | Statement | Evidence |
| --- | --- | --- |
| `ManageLocalServices` | The tool shall start, stop, restart, inspect, and read logs for the Flexo and SysON service families. | `mbse-lab services`, `make up`, `make down`, `make status`, `make logs` |
| `AvoidDestructiveRuntimeReset` | Routine service stop commands shall not delete persisted runtime data. | `mbse-lab services down`, `WORKFLOW.md` |
| `BackupFlexoGraphState` | The tool shall support backing up Flexo graph state and refreshing the startup dataset when graph state must persist. | `scripts/flexo_mms_env.py backup`, `make backup` |

### Private Workspace Boundary

| Requirement | Statement | Evidence |
| --- | --- | --- |
| `PreservePrivateModelBoundary` | The shared tooling repo shall not be the default long-term home for private model data. | `MBSE_MODEL_WORKSPACE`, private workspace docs |
| `InitializePrivateWorkspace` | The CLI shall create and inspect a private model workspace layout. | `mbse-lab workspace init`, `mbse-lab workspace check` |
| `DefaultGeneratedArtifactsToWorkspace` | Bridge artifacts shall default to the configured private workspace when `MBSE_MODEL_WORKSPACE` is set. | bridge commands, workspace docs |

### Bridge And Rendering

| Requirement | Statement | Evidence |
| --- | --- | --- |
| `ListAndCreateFlexoProjects` | The tool shall list, create, and export Flexo SysML v2 projects. | `mbse-lab flexo list`, `mbse-lab flexo create`, `mbse-lab flexo export` |
| `ListAndCreateSysONProjects` | The tool shall list SysON projects, create SysON projects, and discover import roots. | `mbse-lab syson list`, `mbse-lab syson create`, `mbse-lab syson roots` |
| `ProvideSnapshotBridge` | The tool shall move a Flexo snapshot into SysON through rendered SysML text. | `mbse-lab bridge run`, `flexo-to-syson` |
| `RenderConservativeSysMLSubset` | The bridge shall render only verified SysML v2 element mappings and preserve unsupported source data in the raw export. | renderer evals, modeling conventions |
| `RecordBridgeRunEvidence` | Full bridge runs shall write structured run logs by default. | `runs/flexo-to-syson/`, bridge run-log tests |

### First Model Workflow

| Requirement | Statement | Evidence |
| --- | --- | --- |
| `CreateFirstModelEndToEnd` | The CLI shall create a minimal Flexo model, export it, render it, create a SysON review project, and import the snapshot. | `mbse-lab first-model` |
| `SummarizeFirstModelOutputs` | The first-model workflow shall print project IDs, artifact paths, and support machine-readable JSON output. | `mbse-lab first-model --json-output` |

### Diagnostics, Reporting, Cleanup, And Share Safety

| Requirement | Statement | Evidence |
| --- | --- | --- |
| `CollectRedactedDiagnostics` | The tool shall collect a redacted diagnostics bundle for service failures and handoff. | `mbse-lab diagnostics`, `make diagnostics` |
| `GenerateStaticLabReport` | The tool shall generate Markdown, HTML, and JSON local lab reports. | `mbse-lab report` |
| `CleanupGeneratedLocalArtifacts` | The tool shall remove generated reports, diagnostics, run logs, and temporary outputs on request. | `mbse-lab cleanup` |
| `ProtectShareSafety` | The tool shall detect accidentally tracked runtime credentials, service data, private exports, run logs, reports, and secret-like patterns. | `mbse-lab share-check`, `make share-check` |

### Verification And Documentation

| Requirement | Statement | Evidence |
| --- | --- | --- |
| `SupportDeterministicValidation` | The repo shall provide deterministic validation that does not require live services. | `make check`, `make eval`, `make docs-check` |
| `SupportOptionalLiveValidation` | The repo shall provide optional live service evals for Flexo, SysON, and deployment runtime behavior. | `make live-eval`, `mbse-lab deployment verify` |
| `DocumentSupportedOperations` | User-facing docs shall describe setup, CLI use, private workspaces, bridge workflows, limitations, and release steps. | README and docs site |
| `MaintainAgentHandoffContext` | Maintainer-facing docs shall preserve workflow expectations, task plans, validation commands, and data boundaries. | `AGENTS.md`, `WORKFLOW.md`, `docs/plans/` |

## Initial Architecture Elements

| Element | Kind | Responsibility |
| --- | --- | --- |
| `MBSELabToolingRepo` | part definition | Shared source, docs, fixtures, scripts, CLI, and deployment definitions. |
| `CommandLineInterface` | part definition | User-facing command surface exposed as `mbse-lab`. |
| `FlexoEnvironmentManager` | part usage | Flexo env generation, lifecycle, token, backup, and restore helper. |
| `FlexoSysONBridge` | part usage | Flexo export, SysML rendering, SysON import, deployment contract, and run logs. |
| `DiagnosticsCollector` | part usage | Redacted diagnostics bundle generation. |
| `DockerDeployment` | part usage | Local Flexo and SysON Docker Compose runtime. |
| `PrivateModelWorkspace` | part usage | External workspace for private models and generated artifacts. |
| `VerificationHarness` | part usage | Deterministic evals, docs checks, share checks, and optional live evals. |

## Initial Workflow Elements

| Workflow | Purpose |
| --- | --- |
| `BootstrapWorkflow` | Prepare local files, optional private workspace, services, Flexo org, backup, and status checks. |
| `FirstModelWorkflow` | Create a tiny model and prove the end-to-end Flexo-to-SysON path. |
| `FlexoToSysONSnapshotWorkflow` | Export a selected Flexo commit, render SysML, and import into a SysON namespace. |
| `DiagnosticsWorkflow` | Collect redacted local state, logs, probes, and deployment verification results. |
| `ReleaseValidationWorkflow` | Run deterministic checks, docs checks, evals, share checks, and optional live validation. |

## First Fixture Scope

The first checked-in fixture should stay within the current renderer subset:

- `Package`
- `RequirementDefinition`
- `PartDefinition`
- `PartUsage`
- `ActionDefinition`
- `ItemDefinition`

The fixture should cover the model backbone rather than every requirement. Rich
traceability relationships can be added after the bridge supports more SysML v2
relationship forms.

The first curated rendered snapshot is:

```text
exports/examples/sysml/mbse-lab-tool-system.public.sysml
```

It is generated from:

```text
evals/fixtures/mbse-lab-tool-system.json
```

The deterministic render eval keeps the curated snapshot synchronized with the
fixture.

## Known Model Gaps

- Requirement satisfaction, derivation, and verification relationships are not
  rendered yet.
- Command options and environment variables are documented but not modeled as
  structured attributes in the first fixture.
- Runtime deployment details are currently covered more deeply by the container
  deployment fixture than by this tool-system fixture.
- The model does not yet generate reports or docs from SysML source.
