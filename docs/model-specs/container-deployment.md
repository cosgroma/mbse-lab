# Container Deployment SysML v2 Model Specification

This document specifies the intended SysML v2 model for containerized
deployments, with this repository's local MBSE lab as the initial target. The
model is intended to support deployment architecture definition, configuration
traceability, port and volume management, service health verification, and
backup/restore readiness.

The model should be useful as both:

- A semantic MBSE model that captures Docker Compose stacks, container services,
  networks, ports, environment files, volume mounts, data persistence, and
  operational requirements.
- An executable or tool-assisted deployment verification model that can drive
  Docker, Compose, shell/Python checks, API probes, and backup validation.

## Goals

- Represent multi-container deployments as explicit SysML v2 product/runtime
  structures.
- Capture service dependencies, images, tags, port mappings, environment files,
  bind mounts, named networks, health checks, and backup policies.
- Trace deployment requirements to services, volumes, networks, and verification
  checks.
- Support configured deployments such as local development, clean install,
  restored-from-backup, and tool-specific test deployments.
- Provide enough structure to generate or validate Docker Compose files and
  operational checks.
- Preserve evidence from container status checks, API checks, backup creation,
  and restore tests.

## Non-Goals

- This model will not replace Docker Compose, container runtimes, Kubernetes, or
  infrastructure-as-code tools.
- This model will not assume SysML v2 tools can start containers or execute
  health checks natively.
- This model will not initially model production-grade orchestration features
  such as autoscaling, secrets managers, service meshes, ingress controllers, or
  cloud-specific managed services.

## References

- OMG SysML v2 specification: <https://www.omg.org/spec/SysML>
- OMG SysML v2 Language specification PDF:
  <https://www.omg.org/spec/SysML/2.0/Language/PDF>
- OMG KerML specification: <https://www.omg.org/spec/KerML/1.0>
- Local verification model setup guide:
  `docs/methodology/sysml-v2-verification-model-setup.md`
- Local transformation pipeline design:
  `docs/methodology/sysml-v2-transformation-pipeline-design.md`
- Flexo/SysON bridge notes: `docs/lab/flexo-syson-bridge.md`
- Flexo deployment compose file: `deploy/flexo-mms/docker-compose.yml`
- SysON deployment compose file: `deploy/syson/docker-compose.yml`

## MDA Methodology Alignment

This model should use Model Driven Architecture concepts as a layering pattern:

```text
CIM-like layer
  Operational need for a local MBSE lab, repository availability, graphical
  review capability, data persistence, backup/restore readiness, and repeatable
  developer setup.

PIM-like layer
  Abstract deployment stack, service, network, port, volume, health check,
  persistence, backup, and verification concepts independent of Docker Compose.

PSM-like layer
  Specific Docker Compose files, container images, tags, host ports, bind-mount
  paths, env files, service names, network names, runtime credentials, and local
  host assumptions.

Generated and evidence artifacts
  Rendered compose files, environment templates, container status output, API
  probe results, backup files, restore logs, and verification evidence records.
```

The model should preserve traceability across these layers so an operational
deployment requirement can be followed to the logical deployment model, the
concrete Compose configuration, the runtime check, and the verification
evidence.

## Model Boundary

The model covers local container deployment concerns:

```text
deployment environment
  -> compose stack
  -> container services
  -> images and tags
  -> service dependencies
  -> networks
  -> port mappings
  -> environment variables and env files
  -> volume mounts and persisted data
  -> health checks and API probes
  -> backup and restore procedures
```

The model should expose the following primary outputs:

- Deployment stack status.
- Service health status.
- Host port ownership and conflicts.
- API reachability status.
- Volume persistence coverage.
- Backup policy coverage.
- Restore readiness status.
- Requirement verdict or analysis status.

## Recommended Package Structure

```text
ContainerDeploymentModel
  Libraries
    Deployment
    Networking
    Storage
    Operations
  Metadata
  Stakeholders_Concerns
  Definitions
    AttributeDefinitions
    PartDefinitions
    PortDefinitions
    InterfaceDefinitions
    RequirementDefinitions
    CalculationDefinitions
    AnalysisDefinitions
    VerificationDefinitions
  SystemContext
  Requirements
    ServiceAvailabilityRequirements
    ApiReachabilityRequirements
    PortMappingRequirements
    PersistenceRequirements
    BackupRestoreRequirements
    CredentialHandlingRequirements
  Architecture
    DeploymentArchitecture
    FlexoMMSDeployment
    SysONDeployment
    NetworkArchitecture
    StorageArchitecture
  Configurations
    LocalDevelopment
    CleanInstall
    RestoredFromBackup
    FlexoOnly
    SysONOnly
  Analysis
    PortConflictAnalysisCases
    DependencyAnalysisCases
    VolumePersistenceAnalysisCases
    BackupCoverageAnalysisCases
  Verification
    VerificationCases
    VerificationProcedures
    VerificationResults
  Views_Viewpoints
    DeploymentTopologyViews
    PortMappingViews
    VolumePersistenceViews
    RequirementTraceViews
    VerificationTraceViews
```

## Core Part Definitions

The model should define reusable deployment types under
`Definitions/PartDefinitions`.

```text
DeploymentEnvironment
DockerComposeStack
ContainerService
ContainerImage
ImageTag
Network
PortMapping
EnvironmentVariable
EnvironmentFile
SecretInput
VolumeMount
BindMount
DataStore
HealthCheck
ApiProbe
BackupPolicy
RestoreProcedure
RuntimeCommand
```

### DeploymentEnvironment

Expected owned parts:

- `stacks : DockerComposeStack[0..*]`
- `networks : Network[0..*]`
- `dataStores : DataStore[0..*]`
- `backupPolicies : BackupPolicy[0..*]`

Expected attributes:

- `name`
- `host`
- `runtime`
- `composePluginRequired`
- `status`

### DockerComposeStack

Expected owned parts:

- `services : ContainerService[0..*]`
- `networks : Network[0..*]`
- `volumes : VolumeMount[0..*]`

Expected attributes:

- `composeFilePath`
- `projectName`
- `stackStatus`
- `startCommand`
- `stopCommand`

### ContainerService

Expected owned parts:

- `image : ContainerImage`
- `ports : PortMapping[0..*]`
- `environmentVariables : EnvironmentVariable[0..*]`
- `environmentFiles : EnvironmentFile[0..*]`
- `volumeMounts : VolumeMount[0..*]`
- `dependsOn : ContainerService[0..*]`
- `healthChecks : HealthCheck[0..*]`

Expected attributes:

- `serviceName`
- `containerName`
- `hostname`
- `imageReference`
- `restartPolicy`
- `command`
- `status`

### PortMapping

Expected attributes:

- `containerPort`
- `hostPort`
- `protocol`
- `hostInterface`
- `requiredReachability`
- `conflictStatus`

### VolumeMount

Expected attributes:

- `sourcePath`
- `targetPath`
- `accessMode`
- `persistenceRequired`
- `backupRequired`
- `restoreRequired`
- `dataSensitivity`

### HealthCheck

Expected attributes:

- `checkName`
- `method`
- `command`
- `expectedResult`
- `timeout_s`
- `status`

### BackupPolicy

Expected attributes:

- `policyName`
- `subject`
- `backupCommand`
- `backupPath`
- `retention`
- `restoreProcedure`
- `lastBackupStatus`

## Units and Quantities

The model should distinguish:

- Ports as integer network ports.
- Timeouts and durations in seconds.
- Storage sizes in bytes, MB, or GB.
- File paths as host or container paths.
- Versions and tags as strings.
- Boolean operational properties such as `backupRequired` and
  `persistenceRequired`.

## Repository Deployment Architecture

The initial concrete deployment model should represent this repository's two
Docker Compose stacks.

```text
MBSELocalLabDeployment
  part flexoMmsStack : DockerComposeStack
  part sysonStack : DockerComposeStack
```

### Flexo MMS Stack

Source compose file:

```text
deploy/flexo-mms/docker-compose.yml
```

Services:

```text
openldap-server
quad-store-server
minio-server
auth-service
store-service
layer1-service
sysmlv2-service
```

Network:

```text
flexo-mms-test-network
```

Port mappings:

```text
quad-store-server: ${FLEXO_MMS_FUSEKI_HOST_PORT:-3030} -> 3030
minio-server:      ${FLEXO_MMS_MINIO_HOST_PORT:-9000} -> 9000
auth-service:      ${FLEXO_MMS_AUTH_HOST_PORT:-8082} -> 8080
store-service:     ${FLEXO_MMS_STORE_HOST_PORT:-8081} -> 8080
layer1-service:    ${FLEXO_MMS_LAYER1_HOST_PORT:-18080} -> 8080
sysmlv2-service:   ${FLEXO_MMS_SYSMLV2_HOST_PORT:-18083} -> 8080
```

Persistent or operational mounts:

```text
quad-store-server: ./mount -> /tmp/mount
minio-server:      ./data/minio -> /data
```

Important data paths:

```text
deploy/flexo-mms/mount/cluster.nq
deploy/flexo-mms/data/minio/
deploy/flexo-mms/backups/
deploy/flexo-mms/env/
deploy/flexo-mms/.env
```

Service dependencies:

```text
auth-service depends on openldap-server, quad-store-server
store-service depends on minio-server
layer1-service depends on store-service, auth-service, quad-store-server
sysmlv2-service depends on layer1-service
```

### SysON Stack

Source compose file:

```text
deploy/syson/docker-compose.yml
```

Services:

```text
database
app
```

Network:

```text
syson-test-network
```

Port mappings:

```text
app: ${SYSON_HOST_PORT:-18090} -> 8080
```

Persistent mounts:

```text
database: ./data/postgres -> /var/lib/postgresql/data
```

Important data paths:

```text
deploy/syson/data/postgres/
deploy/syson/.env
```

Service dependencies:

```text
app depends on database
```

## Requirements

Requirements should be organized by operational domain and should use
`DeploymentEnvironment`, `DockerComposeStack`, `ContainerService`, or concrete
service usages as their subjects.

Initial requirements:

```text
FlexoLayer1ApiReachable
FlexoSysMLv2ApiReachable
FlexoFusekiReachable
FlexoMinioReachable
FlexoAuthReachable
SysONUiReachable
SysONDatabasePersistent
FlexoGraphDataPersistent
FlexoBackupRequired
NoHostPortConflicts
RuntimeCredentialsNotCommitted
```

Example requirement intent:

```text
FlexoSysMLv2ApiReachable
  subject: sysmlv2-service
  constraint: HTTP GET http://localhost:18083/projects returns a reachable API

SysONUiReachable
  subject: syson app service
  constraint: HTTP HEAD http://localhost:18090/ returns a successful response

FlexoGraphDataPersistent
  subject: quad-store-server volume mount
  constraint: cluster.nq is persisted and backup workflow is available

NoHostPortConflicts
  subject: MBSELocalLabDeployment
  constraint: each required host port is owned by at most one service
```

## Analysis Cases

Analysis cases are the main place to evaluate deployment consistency before
runtime verification.

Required analysis cases:

```text
PortConflictAnalysis
ServiceDependencyAnalysis
VolumePersistenceAnalysis
BackupCoverageAnalysis
CredentialFileAnalysis
ComposeConfigurationAnalysis
```

Each analysis case should have:

- A subject, usually a configured deployment stack or service.
- Explicit input parameters or bindings to compose-derived model attributes.
- Returned outputs for the analysis result.
- A status indicating whether the analysis completed and whether assumptions
  are valid.

## Verification Cases

Verification cases should consume Docker/Compose status, API checks, filesystem
checks, backup execution results, or restore-test evidence and return a verdict.
Use the SysML v2 verification result concepts where supported by the tool:
`pass`, `fail`, `inconclusive`, or `error`.

Required verification cases:

```text
VerifyFlexoContainersRunning
VerifyFlexoLayer1ApiReachable
VerifyFlexoSysMLv2ApiReachable
VerifyFlexoFusekiReachable
VerifyFlexoMinioReachable
VerifySysONContainersRunning
VerifySysONUiReachable
VerifySysONDatabaseVolumeMounted
VerifyFlexoBackupCreated
VerifyRuntimeCredentialFilesIgnored
```

Example checks:

```bash
mbse-lab status
curl -s http://localhost:18083/projects
curl -I http://localhost:18090/
mbse-lab flexo backup
```

Each verification case should link to:

- The requirement being verified.
- The deployment stack, service, port, or volume used as the verification
  subject.
- The command, API probe, or filesystem check used to make the decision.
- The verdict.
- The evidence artifact or result record.

## Transformation and Executability Approach

SysML v2 should express the deployment architecture, requirements, and
verification intent. Docker, Compose, shell/Python scripts, and API clients
should execute the deployment checks.

Recommended pipeline:

```text
SysML v2 deployment configuration
  -> compose/deployment check input
  -> Docker Compose and API probe execution
  -> structured deployment result JSON
  -> analysis or verification result
  -> linked evidence
```

Potential transformation directions:

```text
docker-compose.yml -> SysML v2 deployment model
SysML v2 deployment model -> docker-compose.yml validation report
SysML v2 deployment model -> health-check script input
health-check output -> SysML v2 verification result
```

For this local lab, assume the first implementation validates existing compose
files rather than generating them. Compose generation can be added later after
the model definitions stabilize.

## External Execution Interface

If external execution is used, the script or tool adapter should accept a
configuration record with these inputs:

```text
deploymentId
stackName
composeFilePath
services[]
  serviceName
  containerName
  imageReference
  hostName
  ports[]
    hostPort
    containerPort
    protocol
  envFiles[]
  volumeMounts[]
    sourcePath
    targetPath
    persistenceRequired
    backupRequired
  dependsOn[]
checks[]
  checkName
  method
  commandOrUrl
  expectedResult
```

Expected outputs:

```text
deploymentId
stackName
executionTimestamp
serviceStatuses[]
portCheckResults[]
apiProbeResults[]
volumeCheckResults[]
backupCheckResults[]
credentialCheckResults[]
overallStatus
messages
```

## Traceability Checklist

- Every deployment requirement has a subject.
- Every exposed host port is represented as a `PortMapping`.
- Every persisted path is represented as a `VolumeMount`.
- Every volume that contains durable model data has a backup policy.
- Every service dependency is represented.
- Every runtime credential input is represented without committing secret
  values.
- Every verification case identifies the command, probe, or check it uses.
- Every failed or inconclusive deployment check is visible in review views.
- Every evidence artifact is linked from the verification result.

## Initial Review Views

The model should support these review views:

- Deployment topology by stack.
- Service dependency graph.
- Host port mapping table.
- Environment file and credential input table.
- Volume persistence and backup coverage table.
- API reachability matrix.
- Requirement to verification case trace.
- Failed or missing deployment verification results.

## Open Design Decisions

- Whether to model Docker Compose files as source artifacts only or generate
  them from SysML v2 later.
- Whether extraction should parse compose YAML directly or consume a normalized
  JSON representation.
- How to preserve stable identifiers for services, ports, and volume mounts
  across compose edits.
- Whether backup/restore verification should be modeled as mandatory for all
  durable volumes or only model-repository volumes.
- Whether future production deployment models should target Kubernetes,
  Compose, or both.
