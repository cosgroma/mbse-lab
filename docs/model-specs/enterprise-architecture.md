# Enterprise Architecture SysML v2 Model Specification

This document specifies the intended SysML v2 model for enterprise architecture
(EA) modeling. The model is aligned conceptually with the OMG Unified
Architecture Framework (UAF), ISO/IEC/IEEE 42010 architecture description
concepts, and model-driven architecture practices.

SysML v2 is not treated as a complete enterprise architecture framework by
itself. Instead, SysML v2 is used as the precise semantic modeling language for
implementing EA viewpoints, traceability, requirements, analyses, verification,
and transformations.

The model should be useful as both:

- A semantic enterprise model that captures strategy, capabilities, operations,
  services, resources, information, security, standards, projects, roadmaps, and
  actual deployed resources.
- An executable or tool-assisted architecture analysis model that can drive
  capability gap analysis, dependency analysis, interface completeness checks,
  conformance checks, security coverage checks, cost analysis, and transition
  planning.

## Goals

- Represent enterprise strategy, capabilities, outcomes, operational activities,
  services, systems, information, resources, standards, projects, and deployed
  configurations.
- Align SysML v2 views and model elements with UAF-style enterprise and
  system-of-systems viewpoints.
- Trace stakeholder concerns to capabilities, requirements, services, systems,
  projects, deployed resources, verification cases, and evidence.
- Support comparison between current, planned, and target enterprise
  architectures.
- Support architecture analysis such as capability gaps, dependency impact,
  service coverage, standards conformance, security coverage, and transition
  readiness.
- Preserve enough structure to generate review views, trace matrices, service
  catalogs, deployment inventories, roadmaps, and conformance reports.

## Non-Goals

- This model will not replace UAF, TOGAF, DoDAF, NAF, portfolio management
  tools, enterprise repositories, CMDBs, or governance workflows.
- This model will not claim UAF conformance unless a separate UAF-conformant
  implementation is built and verified.
- This model will not initially model finance, contracting, HR, or portfolio
  governance in full detail.
- This model will not assume every SysML v2 tool can execute all architecture
  analyses natively.

## References

- OMG UAF specification page: <https://www.omg.org/spec/UAF>
- OMG UAF v1.3 Domain Metamodel PDF:
  <https://www.omg.org/spec/UAF/1.3/DMM/PDF>
- OMG UAF overview: <https://www.omg.org/uaf/>
- OMG SysML v2 specification: <https://www.omg.org/spec/SysML>
- OMG SysML v2 Language specification PDF:
  <https://www.omg.org/spec/SysML/2.0/Language/PDF>
- OMG KerML specification: <https://www.omg.org/spec/KerML/1.0>
- OMG Model Driven Architecture overview: <https://www.omg.org/mda/>
- Local verification model setup guide:
  `docs/methodology/sysml-v2-verification-model-setup.md`
- Local transformation pipeline design:
  `docs/methodology/sysml-v2-transformation-pipeline-design.md`
- Local security architecture model spec:
  `docs/model-specs/security-architecture.md`
- Local container deployment model spec:
  `docs/model-specs/container-deployment.md`

## UAF Alignment

UAF should be treated as the enterprise architecture viewpoint taxonomy. SysML
v2 should be treated as the implementation language for precise model elements,
relationships, requirements, analyses, verification cases, and transformations.

Recommended concept mapping:

```text
UAF concept                          SysML v2 model concept
Stakeholder                          actor, part, metadata, or stakeholder item
Concern                              concern item, requirement, viewpoint concern
Enterprise Goal                      EnterpriseGoal requirement or objective
Capability                           Capability part/item with outcomes and measures
Operational Performer                OperationalPerformer part
Operational Activity                 action def or action usage
Operational Exchange                 item flow, connection, interface, exchange item
Service                              Service part, interface, or behavioral contract
Resource Performer                   ResourcePerformer, system, application, organization
System                               system part or part definition
Software / Application               SoftwareApplication part
Information Element                  item def InformationAsset or DataEntity
Project                              Project part or lifecycle activity
Standard                             StandardRequirement or ConformanceConstraint
Actual Resource                      DeployedResource or runtime configuration
Security Viewpoint                   imported/aligned security architecture package
```

The model should support UAF-style enterprise questions:

- What enterprise goals and outcomes are being pursued?
- Which capabilities realize those goals?
- Which operational activities use or provide those capabilities?
- Which services and resources implement the operations?
- What information is exchanged between performers, services, and systems?
- Which standards and constraints apply?
- Which projects or increments transition the enterprise?
- What is deployed now versus planned or target?
- Which risks, controls, and security concerns affect the architecture?
- Which architecture requirements have been verified?

## Enterprise View Specifications

The model should provide SysML v2 views aligned to major UAF-style viewpoints.

```text
StrategicViews
  Goals, capabilities, outcomes, capability dependencies, and capability
  increments.

OperationalViews
  Operational performers, activities, scenarios, exchanges, and operational
  constraints.

ServiceViews
  Services, service interfaces, service consumers, service providers, and
  service dependencies.

ResourceViews
  Systems, applications, infrastructure, facilities, organizations, people,
  technologies, and resource interfaces.

InformationViews
  Information assets, data entities, data stores, information exchanges, and
  ownership.

SecurityViews
  Security assets, controls, risks, enclaves, trust boundaries, and assurance
  evidence.

StandardsViews
  Policies, technical standards, compliance requirements, and conformance
  status.

ProjectViews
  Projects, increments, transitions, milestones, dependencies, and roadmaps.

ActualResourceViews
  Deployed systems, running services, container stacks, configured environments,
  and operational baselines.

TraceabilityViews
  Trace from concerns to goals, capabilities, requirements, services, resources,
  projects, deployed assets, verification cases, and evidence.
```

## MDA Methodology Alignment

This model should use Model Driven Architecture concepts as a layering pattern:

```text
CIM-like layer
  Enterprise mission, strategy, stakeholders, concerns, goals, outcomes,
  policies, operational needs, and governance drivers.

PIM-like layer
  Capabilities, operational activities, service contracts, information
  exchanges, logical resources, requirements, analysis cases, and verification
  intent independent of a specific platform or deployment.

PSM-like layer
  Specific systems, applications, infrastructure, container deployments,
  protocols, tools, vendors, standards, data stores, teams, projects, and
  runtime configurations.

Generated and evidence artifacts
  Capability maps, service catalogs, interface control documents, deployment
  inventories, trace matrices, conformance reports, analysis outputs, and
  verification evidence records.
```

The model should preserve traceability across these layers so an enterprise
concern can be followed to the strategy, capability, logical architecture,
implementation architecture, deployed resources, and evidence.

## Model Boundary

The model covers enterprise architecture concerns:

```text
stakeholders and concerns
  -> goals and outcomes
  -> capabilities
  -> operational activities and performers
  -> services
  -> systems, applications, organizations, infrastructure
  -> information assets and exchanges
  -> security, standards, and constraints
  -> projects and roadmaps
  -> actual deployed resources
  -> analyses, verification cases, and evidence
```

The model should expose the following primary outputs:

- Capability map and capability gap status.
- Operational activity and exchange model.
- Service catalog and service dependency model.
- System/application/resource inventory.
- Information exchange and ownership model.
- Security and standards coverage.
- Project roadmap and transition status.
- Current/planned/target architecture comparison.
- Architecture conformance and verification status.

## Recommended Package Structure

```text
EnterpriseArchitectureModel
  Libraries
    Enterprise
    Strategy
    Operations
    Services
    Resources
    Information
    Security
    Standards
    Projects
  Metadata
  Stakeholders_Concerns
    EnterpriseStakeholders
    BusinessConcerns
    MissionConcerns
    TechnicalConcerns
    SecurityConcerns
  Definitions
    AttributeDefinitions
    ItemDefinitions
    PartDefinitions
    PortDefinitions
    InterfaceDefinitions
    RequirementDefinitions
    CalculationDefinitions
    AnalysisDefinitions
    VerificationDefinitions
  SystemContext
  Strategy
    EnterpriseGoals
    Outcomes
    Capabilities
    CapabilityIncrements
  Operations
    OperationalPerformers
    OperationalActivities
    OperationalScenarios
    OperationalExchanges
  Services
    BusinessServices
    SystemServices
    ServiceInterfaces
    ServiceDependencies
  Resources
    Systems
    Applications
    Infrastructure
    Facilities
    Organizations
    People
  Information
    InformationAssets
    DataEntities
    DataStores
    InformationExchanges
  Security
    SecurityAssets
    Risks
    Controls
    Enclaves
  Standards
    Policies
    TechnicalStandards
    ComplianceRequirements
  Projects
    Roadmaps
    Increments
    TransitionArchitectures
  ActualResources
    DeployedSystems
    RunningServices
    ConfiguredEnvironments
  Requirements
    ArchitectureRequirements
    CapabilityRequirements
    ServiceRequirements
    ResourceRequirements
    ComplianceRequirements
  Analysis
    CapabilityGapAnalysisCases
    DependencyAnalysisCases
    ServiceCoverageAnalysisCases
    StandardsConformanceAnalysisCases
    CostAnalysisCases
    RiskAnalysisCases
  Verification
    ArchitectureConformanceCases
    ServiceReadinessCases
    SecurityVerificationCases
    EvidenceRecords
  Views_Viewpoints
    StrategicViews
    OperationalViews
    ServiceViews
    ResourceViews
    InformationViews
    SecurityViews
    StandardsViews
    ProjectViews
    ActualResourceViews
    TraceabilityViews
```

## Core Definitions

The model should define reusable enterprise types under `Definitions`.

```text
Enterprise
EnterpriseGoal
Outcome
Capability
CapabilityIncrement
OperationalPerformer
OperationalActivity
OperationalScenario
OperationalExchange
BusinessService
SystemService
ServiceInterface
ResourcePerformer
SystemResource
SoftwareApplication
InfrastructureResource
OrganizationResource
FacilityResource
PersonRole
InformationAsset
DataEntity
DataStore
InformationExchange
Policy
TechnicalStandard
ComplianceConstraint
Project
Roadmap
TransitionArchitecture
DeployedResource
RunningService
ArchitectureEvidence
```

### Capability

Expected attributes:

- `capabilityId`
- `capabilityName`
- `description`
- `owner`
- `maturityLevel`
- `priority`
- `targetState`
- `currentState`
- `gapStatus`
- `effectivenessMeasure`

### OperationalActivity

Expected attributes:

- `activityId`
- `activityName`
- `performer`
- `inputs`
- `outputs`
- `preconditions`
- `postconditions`
- `operationalConstraints`

### Service

Expected attributes:

- `serviceId`
- `serviceName`
- `provider`
- `consumers`
- `serviceLevelObjective`
- `availabilityTarget`
- `criticality`
- `interface`
- `status`

### ResourcePerformer

Expected attributes:

- `resourceId`
- `resourceName`
- `resourceType`
- `owner`
- `lifecycleState`
- `location`
- `interfaces`
- `supportedCapabilities`
- `implementedServices`

### InformationAsset

Expected attributes:

- `informationId`
- `informationName`
- `owner`
- `classification`
- `dataSensitivity`
- `sourceOfTruth`
- `retentionRequirement`
- `qualityStatus`

### Project

Expected attributes:

- `projectId`
- `projectName`
- `sponsor`
- `startDate`
- `targetDate`
- `status`
- `deliveredCapabilities`
- `affectedResources`
- `transitionState`

### DeployedResource

Expected attributes:

- `deploymentId`
- `resource`
- `environment`
- `version`
- `configurationBaseline`
- `operationalStatus`
- `deploymentDate`
- `evidence`

## Requirements

Requirements should be organized by architecture concern and should use
capabilities, services, resources, information assets, projects, or deployed
resources as subjects.

Initial requirements:

```text
CapabilityTraceRequired
CapabilityGapAssessmentRequired
ServiceOwnerRequired
ServiceInterfaceRequired
InformationOwnerRequired
SystemOfRecordRequired
SecurityControlsRequired
StandardsConformanceRequired
ProjectTraceToCapabilityRequired
DeploymentBaselineRequired
ArchitectureEvidenceRequired
```

Example requirement intent:

```text
CapabilityTraceRequired
  subject: Capability
  constraint: each critical capability traces to at least one operational
              activity, service, resource, and owning stakeholder concern.

ServiceInterfaceRequired
  subject: SystemService
  constraint: each externally consumed service has a defined interface and
              identified provider and consumers.

DeploymentBaselineRequired
  subject: DeployedResource
  constraint: each deployed resource has a version, configuration baseline,
              operational status, and evidence record.
```

## Analysis Cases

Analysis cases are the main place to evaluate architecture quality, gaps, and
transition readiness.

Required analysis cases:

```text
CapabilityGapAnalysis
CapabilityCoverageAnalysis
OperationalDependencyAnalysis
ServiceDependencyAnalysis
InterfaceCompletenessAnalysis
InformationOwnershipAnalysis
StandardsConformanceAnalysis
SecurityCoverageAnalysis
ProjectImpactAnalysis
TransitionReadinessAnalysis
CostAndResourceImpactAnalysis
```

Each analysis case should have:

- A subject, usually an enterprise configuration, capability set, service set,
  resource architecture, project, or deployed baseline.
- Explicit input parameters or bindings to model attributes.
- Returned outputs for gap, coverage, dependency, impact, cost, risk, or
  readiness status.
- A status indicating whether the analysis completed and whether assumptions
  are valid.

## Verification Cases

Verification cases should consume analysis results, architecture reviews,
deployment checks, service evidence, conformance records, or governance evidence
and return a verdict. Use the SysML v2 verification result concepts where
supported by the tool: `pass`, `fail`, `inconclusive`, or `error`.

Required verification cases:

```text
VerifyCapabilityTraceComplete
VerifyCapabilityGapAssessmentComplete
VerifyServiceInterfacesDefined
VerifyInformationOwnershipDefined
VerifyStandardsConformance
VerifySecurityCoverage
VerifyProjectCapabilityTrace
VerifyDeploymentBaselineComplete
VerifyArchitectureEvidenceExists
```

Each verification case should link to:

- The requirement being verified.
- The capability, service, resource, information asset, project, or deployment
  used as the verification subject.
- The analysis, review, inspection, deployment check, or governance evidence
  used to make the decision.
- The verdict.
- The evidence artifact or result record.

## Local MBSE Lab Enterprise Application

The first concrete application can treat this repository as a small enterprise
architecture slice for a local MBSE experimentation capability.

Candidate capabilities:

```text
ModelRepositoryCapability
SysMLv2ApiExperimentationCapability
GraphicalModelReviewCapability
ModelTransformationCapability
ModelVerificationCapability
SecurityArchitectureModelingCapability
ContainerDeploymentVerificationCapability
```

Candidate services:

```text
FlexoLayer1ApiService
FlexoSysMLv2ApiService
FlexoAuthService
FlexoStoreService
FusekiGraphStoreService
MinioObjectStoreService
SysONGraphicalModelingService
SysONGraphQLService
```

Candidate actual resources:

```text
FlexoMMSDockerComposeStack
SysONDockerComposeStack
FlexoSysMLv2Container
Layer1ServiceContainer
FusekiContainer
MinioContainer
SysONAppContainer
SysONPostgresContainer
BridgeScript
ExportedSysMLSnapshots
```

Candidate enterprise requirements:

```text
Local lab shall support API-backed SysML v2 model experiments.
Local lab shall support graphical review of imported SysML v2 text.
Local lab shall preserve model repository data across container restarts.
Local lab shall support backup of durable model repository data.
Local lab shall provide traceable model transformation artifacts.
```

## Transformation and Executability Approach

SysML v2 should express the enterprise architecture, requirements, analyses, and
verification intent. External scripts, repositories, deployment tools, and
governance systems should execute checks and provide evidence.

Recommended pipeline:

```text
SysML v2 enterprise architecture model
  -> architecture analysis input
  -> coverage / dependency / conformance / deployment analysis
  -> structured architecture result JSON
  -> analysis or verification result
  -> linked evidence
```

Potential transformation directions:

```text
enterprise model -> service catalog
enterprise model -> capability map
enterprise model -> deployment inventory
enterprise model -> standards conformance matrix
enterprise model -> architecture review package
analysis output -> SysML v2 verification result
```

## External Execution Interface

If external execution is used, the script or tool adapter should accept a
configuration record with these inputs:

```text
enterpriseModelId
configurationId
capabilities[]
  capabilityId
  owner
  currentState
  targetState
  supportedBy
services[]
  serviceId
  provider
  consumers
  interfaces
  implementedBy
resources[]
  resourceId
  resourceType
  lifecycleState
  supportedCapabilities
informationAssets[]
  informationId
  owner
  sourceOfTruth
  classification
projects[]
  projectId
  deliveredCapabilities
  affectedResources
deployedResources[]
  deploymentId
  version
  baseline
  status
checks[]
  checkName
  method
  expectedResult
```

Expected outputs:

```text
enterpriseModelId
configurationId
executionTimestamp
capabilityCoverageResults[]
serviceCoverageResults[]
dependencyResults[]
interfaceCompletenessResults[]
standardsConformanceResults[]
deploymentBaselineResults[]
verificationVerdicts[]
overallStatus
messages
```

## Traceability Checklist

- Every stakeholder concern traces to one or more goals or requirements.
- Every goal traces to one or more capabilities or outcomes.
- Every critical capability traces to operational activities, services, and
  resources.
- Every service has a provider, consumers, and interface definition.
- Every information asset has an owner and source-of-truth status.
- Every standard or policy has a conformance subject.
- Every project traces to affected capabilities or resources.
- Every deployed resource has a baseline and operational status.
- Every architecture requirement has a verification case.
- Every verification case has evidence or an explicit evidence gap.

## Initial Review Views

The model should support these review views:

- Enterprise goal to capability map.
- Capability gap matrix.
- Operational activity and exchange view.
- Service catalog.
- Service dependency graph.
- Resource/application inventory.
- Information ownership table.
- Standards conformance matrix.
- Security coverage matrix.
- Project roadmap and transition view.
- Current/planned/target architecture comparison.
- Requirement to verification case trace.
- Failed or missing architecture verification results.

## Open Design Decisions

- Whether to model UAF concepts as a local SysML v2 domain library or keep them
  as lightweight naming conventions.
- Whether to model TOGAF-specific architecture domains later.
- Whether the first implementation should focus on the local MBSE lab enterprise
  slice or a broader organization-level example.
- Whether service catalogs and deployment inventories should be generated from
  SysML v2 or imported from external repositories.
- How to preserve architecture governance status and review decisions in the
  model without turning the model into a workflow tool.
