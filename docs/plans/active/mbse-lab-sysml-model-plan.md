# MBSE Lab SysML v2 Model Plan

## Objective

Build a SysML v2 model of this repository as a tool system: the local MBSE lab
kit that deploys Flexo MMS and SysON, manages private model workspaces, bridges
Flexo snapshots into SysON, verifies runtime state, and protects shareability.

The model should become both:

- A semantic description of the tool's requirements, architecture, workflows,
  runtime deployment, artifacts, and verification evidence.
- A useful fixture source for improving the Flexo-to-SysON bridge, reporting,
  deployment verification, and future model-template workflows.

## Starting Position

Starting with requirements for landed features makes sense, but the first step
should be a short model-boundary and viewpoint pass. Without that boundary, the
requirements risk becoming a flat command inventory instead of a traceable model
of the tool system.

Recommended starting sequence:

1. Define model boundary, stakeholders, concerns, and viewpoints.
2. Write requirements for landed behavior, grouped by user value.
3. Map requirements to features, commands, scripts, docs, runtime services, and
   verification checks.
4. Add architecture and workflow structure once the requirement taxonomy is
   stable.

## Relevant Files

- `README.md`
- `WORKFLOW.md`
- `AGENTS.md`
- `Makefile`
- `pyproject.toml`
- `src/mbse_lab/cli.py`
- `src/mbse_lab/model.py`
- `src/mbse_lab/health.py`
- `src/mbse_lab/reports.py`
- `src/mbse_lab/share.py`
- `src/mbse_lab/workspace.py`
- `scripts/flexo_mms_env.py`
- `scripts/flexo_syson_bridge.py`
- `scripts/collect_diagnostics.py`
- `scripts/check_docs.py`
- `deploy/flexo-mms/docker-compose.yml`
- `deploy/syson/docker-compose.yml`
- `docs/lab/flexo-syson-bridge.md`
- `docs/lab/harness-engineering.md`
- `docs/lab/modeling-conventions.md`
- `docs/model-specs/container-deployment.md`
- `docs/model-specs/enterprise-architecture.md`
- `docs/user-guide/cli.md`
- `docs/user-guide/private-model-workspaces.md`
- `evals/fixtures/*.json`
- `evals/test_bridge_*.py`
- `evals/test_live_*.py`

## Planned Model Artifacts

- `docs/model-specs/mbse-lab-tool-system.md`: human-readable model
  specification.
- `evals/fixtures/mbse-lab-tool-system.json`: synthetic Flexo-style fixture for
  deterministic renderer and analysis tests.
- `exports/examples/sysml/mbse-lab-tool-system.public.sysml`: curated
  publishable rendered textual snapshot, if it stays small and synthetic.
- Optional future private-workspace artifact: richer live Flexo export generated
  from the local model once the workflow is stable.

## Planned Package Structure

```text
MBSELabToolSystem
  Libraries
    Tooling
    Workflow
    Deployment
    Verification
  Metadata
  Stakeholders_Concerns
  SystemContext
  Requirements
    BootstrapRequirements
    ServiceLifecycleRequirements
    PrivateWorkspaceRequirements
    BridgeRequirements
    ModelRenderingRequirements
    DiagnosticsReportingRequirements
    ShareSafetyRequirements
    VerificationRequirements
    DocumentationRequirements
    ReleaseReadinessRequirements
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
    UserWorkflowViews
    CommandSurfaceViews
    RequirementTraceViews
    DeploymentRuntimeViews
    VerificationTraceViews
```

## Requirement Taxonomy

Initial requirements should describe landed user-visible behavior, not desired
future behavior. Candidate groups:

- Bootstrap and initialization: repo discovery, env generation, optional private
  workspace setup, dry-run behavior, service URL reporting.
- Service lifecycle: start, stop, restart, status, logs, Flexo backup, Flexo
  restore, and non-destructive data handling.
- Private workspace boundary: `MBSE_MODEL_WORKSPACE`, generated artifact
  defaults, workspace layout, shareable tooling repo separation.
- Bridge workflow: Flexo project list/create/export, SysML render, SysON
  project list/create/root discovery/import, full snapshot bridge, run logs.
- First model workflow: tiny end-to-end package creation, export, render, SysON
  review project creation, import, JSON summary.
- Conservative rendering: supported element types, deterministic naming,
  preservation of unsupported data in raw exports.
- Diagnostics and reporting: diagnostics bundle, deployment verification report,
  static report, cleanup.
- Share safety: forbidden tracked paths, generated export warnings, secret-like
  pattern scan, credential template boundaries.
- Verification and CI: `make check`, deterministic evals, docs checks, workflow
  checks, optional live evals, deployment contract verification.
- Documentation and release readiness: CLI docs, private workspace docs, release
  process, known limitations.

## Planned Steps

### Step 1: Scope And Viewpoints

- Define the system of interest as the MBSE lab tooling repo, not the models it
  helps users build.
- Identify primary stakeholders: first-time user, returning local-lab user,
  model author, maintainer, release publisher, future agent.
- Capture concerns: setup success, data safety, repeatability, bridge fidelity,
  diagnostic clarity, shareability, verification coverage.
- Decide which views are needed for the first model increment.

### Step 2: Landed Feature Requirements

- Translate landed CLI, script, docs, deployment, and eval behavior into
  requirement definitions/usages.
- Keep requirements testable and traceable to existing commands or docs.
- Avoid requirements for deferred features unless marked as future or
  out-of-scope.

### Step 3: Feature And Artifact Architecture

- Model command groups, scripts, runtime services, environment files, generated
  artifacts, ignored runtime data, and publishable fixtures.
- Link architecture parts to requirements.
- Reuse concepts from the existing container deployment model for Docker
  services and runtime checks.

### Step 4: Workflow Model

- Model the main action flows:
  - `mbse-lab bootstrap`
  - `mbse-lab first-model`
  - `mbse-lab bridge run`
  - `mbse-lab diagnostics`
  - release/share validation
- Connect inputs, outputs, generated artifacts, and verification evidence.

### Step 5: Verification Trace

- Map each requirement group to deterministic checks, live evals, share checks,
  docs checks, deployment checks, or manual release validation.
- Identify requirements that currently lack automated verification.

### Step 6: Publishable Fixture And Rendered Snapshot

- Create a synthetic Flexo-style JSON fixture for the model subset supported by
  the bridge renderer.
- Render the fixture to SysML text.
- Add deterministic eval coverage for key declarations and traces.

### Step 7: Future Feature Backlog From Model Gaps

- Use missing requirements, unverified requirements, and unsupported model
  elements to prioritize new tool features.
- Candidate future features include bridge review automation, richer render
  evidence reports, model templates, snapshot diffs, CLI backup/restore polish,
  and remote endpoint profiles.

## Progress Log

- 2026-05-01: Created initial plan. Decision: start with scope/viewpoints, then
  requirements for landed behavior.
- 2026-05-01: Added first model increment: tool-system model spec, synthetic
  Flexo-style fixture, MkDocs navigation entry, and deterministic render eval.
- 2026-05-01: Added curated rendered SysML snapshot generated from the fixture
  and eval coverage to keep it synchronized.

## Validation Commands

Run after changing docs or model specs:

```bash
make docs-check
```

Run after adding fixtures or renderer assertions:

```bash
make eval
make check
```

Run when the live model workflow is exercised against local services:

```bash
make live-eval
mbse-lab deployment verify
```

Run before sharing generated artifacts:

```bash
mbse-lab share-check
```

## Decisions And Tradeoffs

- The first model increment covers landed behavior only. Deferred features can
  appear as model gaps or future requirements, but should not be mixed into the
  current baseline.
- Requirements come after boundary and viewpoint definition so they remain
  organized by stakeholder concern and verification value.
- The publishable fixture should stay synthetic and small enough to live in the
  tooling repo.
- Richer model exports, run evidence, and experimental traces should live in a
  private model workspace unless explicitly curated for publication.

## Follow-Up Debt

- Decide how much traceability the current conservative renderer can represent
  before requiring renderer expansion.
- Decide whether the model should become the source for future docs/report
  generation, or remain a verification and planning artifact.
