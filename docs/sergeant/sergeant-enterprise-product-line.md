# SERGEANT Enterprise Product-Line SysML v2 Model Specification

This document specifies a SysML v2 model for SERGEANT as a whole, centered on:

```text
/home/cosgroma/workspace/sergeant
```

The SERGEANT model is an umbrella model for product-line architecture,
reusable-asset governance, design-variant traceability, build and deployment
evidence, release readiness, and cross-design analysis.

This model should be federated. It should not duplicate every detail from
lower-level design, component, and engine models. Instead, it should reference
those models and provide portfolio-level structure, traceability, governance,
and evidence rollups.

## Goals

- Represent SERGEANT as an engineering platform and product-line ecosystem.
- Catalog products, designs, design variants, components, engines, FPGA IP,
  libraries, tools, build systems, deployment systems, and evidence sources.
- Relate products such as PGM SDRx and T1TL to the reusable assets they use.
- Trace which products use each component, engine, FPGA IP block, board,
  operating system, build profile, deployment profile, and release artifact.
- Support cross-design reuse analysis, version-drift analysis, release-readiness
  analysis, and evidence-coverage analysis.
- Provide an umbrella structure for lower-level SysML v2 models.
- Support model transformation pipelines that extract source repositories,
  variant configs, build artifacts, CI evidence, and deployment evidence into
  consistent SysML views.

## Non-Goals

- This model will not replace the detailed PGM SDRx, T1TL, GEnCor, Channel
  Controller, security, deployment, or transformation models.
- This model will not encode every source file, function, HDL module, or build
  target in the SERGEANT workspace.
- This model will not store credentials, secret keys, private tokens, or
  machine-local passwords.
- This model will not be the authoritative build tool. Existing Make, CMake,
  `smake`, Jenkins, Vivado, VxWorks, Docker, and deployment tools remain the
  execution authorities.
- This model will not treat declared artifact paths as evidence unless actual
  evidence records confirm production, verification, or deployment.

## Source References

Primary workspace:

```text
/home/cosgroma/workspace/sergeant
```

Known top-level domains:

```text
comps/
designs/
  pgm/
  t1tl/
engines/
  gencor/
  gencor-* worktrees
```

Key local references:

- `/home/cosgroma/workspace/sergeant/engines/AGENTS.md`
- `/home/cosgroma/workspace/sergeant/engines/git-worktree-guidance.md`
- `/home/cosgroma/workspace/sergeant/engines/gencor-worktree-devlog.md`
- `/home/cosgroma/workspace/sergeant/designs/pgm`
- `/home/cosgroma/workspace/sergeant/designs/t1tl`
- `/home/cosgroma/workspace/sergeant/engines/gencor`

Related local MBSE model specs:

- `docs/sergeant/pgm-sdrx-design.md`
- `docs/sergeant/cc-channel-controller.md`
- `docs/sergeant/gencor-fpga-resource-timing.md`
- `docs/model-specs/container-deployment.md`
- `docs/model-specs/security-architecture.md`
- `docs/model-specs/enterprise-architecture.md`
- `docs/methodology/sysml-v2-transformation-pipeline-design.md`
- `docs/methodology/sysml-v2-verification-model-setup.md`

## Modeling Principle

The SERGEANT model should be a federation model:

```text
SERGEANT Enterprise Product-Line Model
  references PGM SDRx Design Model
  references T1TL Design Model
  references GEnCor FPGA/IP Model
  references Channel Controller Model
  references Container Deployment Model
  references Security Architecture Model
  references Transformation Pipeline Model
  references Verification Model Setup Guide
```

The SERGEANT level owns:

- Cross-product structure.
- Reusable-asset cataloging.
- Variant-to-asset traceability.
- Version and evidence rollups.
- Governance views.
- Release-readiness dashboards.
- Portfolio-level analysis.

Lower-level models own:

- Detailed component runtime behavior.
- FPGA/IP internals.
- Product-specific build graphs.
- Product-specific deployment scripts.
- Detailed verification cases and test harness behavior.

## Model Boundary

The SERGEANT model covers:

```text
product-line portfolio
  -> design repositories and variants
  -> reusable components, engines, libraries, and FPGA IP
  -> platform and board targets
  -> operating system and runtime targets
  -> build systems and CI/CD pipelines
  -> deployment systems and bench/target environments
  -> verification and evidence sources
  -> release artifacts and readiness status
```

The model should expose:

- Product and design catalog.
- Reusable asset catalog.
- Cross-design dependency map.
- Build/release pipeline catalog.
- Deployment environment catalog.
- Evidence repository and traceability map.
- Version drift and reuse risk views.
- Release-readiness views.

## Recommended Package Structure

```text
SergeantEnterpriseProductLineModel
  Libraries
    ProductLineEngineering
    ReusableAssetManagement
    BuildReleaseEngineering
    DeploymentEngineering
    VerificationEvidence
    SecurityGovernance
  Metadata
  Stakeholders_Concerns
    ProductLineStakeholders
    ProgramStakeholders
    BuildReleaseStakeholders
    IntegrationStakeholders
    VerificationStakeholders
    SecurityStakeholders
  Definitions
    AttributeDefinitions
    ItemDefinitions
    PartDefinitions
    InterfaceDefinitions
    RequirementDefinitions
    AnalysisDefinitions
    VerificationDefinitions
    EvidenceDefinitions
  EnterpriseContext
    Organizations
    Programs
    Products
    OperationalContexts
    EngineeringEnvironments
  ProductLine
    ProductFamilies
    ProductDefinitions
    DesignDefinitions
    DesignVariants
    FeatureCatalog
    CapabilityCatalog
  ReusableAssetLibrary
    ComponentCatalog
    EngineCatalog
    FpgaIpCatalog
    LibraryCatalog
    ToolCatalog
    ContainerImageCatalog
    RuntimeAssetCatalog
  PlatformCatalog
    BoardProfiles
    ProcessorProfiles
    FpgaProfiles
    OperatingSystemProfiles
    RuntimeProfiles
    DeploymentTargetProfiles
  BuildAndReleaseArchitecture
    BuildSystems
    BuildProfiles
    CiPipelines
    ArtifactRepositories
    ReleasePipelines
    ReleaseArtifacts
  DeploymentArchitecture
    DeploymentProfiles
    BenchEnvironments
    TftpProfiles
    FtpProfiles
    UartProfiles
    HardwareTargetProfiles
  VerificationArchitecture
    VerificationStrategies
    VerificationCases
    AnalysisCases
    TestHarnesses
    EvidenceRequirements
  SecurityArchitecture
    SecurityConcerns
    SecurityControls
    SupplyChainControls
    SecretHandlingPolicies
    ReleaseIntegrityControls
  EvidenceRepository
    SourceRevisionEvidence
    BuildEvidence
    FpgaEvidence
    RuntimeEvidence
    DeploymentEvidence
    ReleaseEvidence
    WaiverEvidence
  TransformationPipelines
    SourceExtractionPipelines
    BuildGraphExtractionPipelines
    EvidenceIngestionPipelines
    ViewGenerationPipelines
  Views_Viewpoints
    ProductPortfolioViews
    ReuseViews
    VariantViews
    BuildReleaseViews
    DeploymentViews
    VerificationViews
    SecurityViews
    EvidenceViews
```

## Core Model Elements

### Product Family

```text
ProductFamily
  name
  missionDomain
  products
  sharedCapabilities
  reusableAssets
  supportedPlatforms
  governancePolicies
```

Initial product family:

```text
SERGEANT
```

### Product

```text
Product
  name
  productFamily
  owningProgram
  designRepositories
  designVariants
  supportedBoards
  supportedOperatingSystems
  reusableAssets
  buildProfiles
  deploymentProfiles
  releaseArtifacts
  verificationStatus
```

Initial product instances:

```text
PGM_SDRx
T1TL
```

### Design Repository

```text
DesignRepository
  name
  path
  repositoryType
  owningProduct
  sourceRevision
  submodules
  buildSystems
  designVariants
  linkedModel
```

Initial repositories:

```text
designs/pgm
designs/t1tl
engines/gencor
comps/os
```

### Design Variant

At the SERGEANT level, a design variant is a portfolio-level configuration. Its
detailed build and deployment graph belongs in the product-level model.

```text
DesignVariant
  name
  product
  sourceRepository
  boardProfile
  processorProfile
  fpgaProfile
  operatingSystemProfile
  runtimeProfile
  selectedComponents
  selectedEngines
  selectedFpgaIp
  buildProfile
  deploymentProfile
  evidenceSummary
```

Example PGM variant references:

```text
magnompgm_sgt_mopd_reprog
magnompgm_integrated_sgt_anv
magnompgm_sgt_mopd_pcode
secure_arch_zcu102
playback_mopd
```

Example T1TL variant references:

```text
navdc
magnompnt
smp-navdc
gnss
```

## Reusable Asset Model

Reusable assets should be modeled as first-class elements because the most
valuable SERGEANT-level questions are reuse, version drift, and impact.

### Component

```text
ReusableComponent
  name
  sourceRepository
  sourcePath
  owner
  interfacePackages
  supportedProducts
  supportedOperatingSystems
  buildSystems
  releaseVersion
  evidenceSummary
```

Initial component candidates:

```text
os
cc
sm
mio
em
sc
fm
pp
th
```

### Engine

```text
ReusableEngine
  name
  sourceRepository
  sourcePath
  engineType
  supportedProducts
  fpgaOrRuntimeRole
  buildSystems
  interfaceContracts
  evidenceSummary
```

Initial engine candidates include:

```text
gencor
mopd
sample_stream
collector
decimator
frequency_mixer
band_separator
spectrum
one_pps
pcu
ad9257
ad9912
ad9915
max2112
hotstart_timing
```

### FPGA IP

```text
ReusableFpgaIp
  name
  sourceRepository
  ipIdentity
  supportedFamilies
  productsUsingIp
  designVariantsUsingIp
  resourceModel
  timingModel
  verificationEvidence
```

Initial FPGA IP:

```text
GEnCor
MOPD
ReadyLock
SampleStreamer
Collector
```

## Platform Catalog

The platform catalog should normalize boards, processors, FPGA parts, OSes, and
deployment targets so product variants can be compared.

```text
BoardProfile
  name
  product
  fpgaPart
  processorFamily
  memoryProfile
  interfaces
  deploymentTargets

OperatingSystemProfile
  name
  version
  architecture
  processorMode
  kernelBuildSystem
  runtimeLayout

FpgaProfile
  family
  partNumber
  board
  supportedProducts
  toolVersion
  buildFlow
```

Initial profiles:

```text
PGM / xqzu15eg-ffrc900-1m-m
ZCU102 / xczu9eg-ffvb1156-2-e
NAVDC / xqzu9eg family
VxWorks 7
Linux
Zynq UltraScale+
Zynq-7000
```

## Build and Release Model

The SERGEANT model should catalog build systems and CI/CD pipelines across
products.

```text
BuildSystem
  name
  buildTool
  repository
  supportedProducts
  buildTargets
  producedArtifactTypes

CiPipeline
  name
  repository
  parameters
  stages
  producedArtifacts
  publishTargets
  evidenceRecords

ReleaseArtifact
  name
  product
  designVariant
  artifactType
  sourceRevision
  producer
  repositoryUrl
  checksum
  verificationStatus
```

Known build systems:

- Top-level Make.
- CMake.
- `smake`.
- Jenkins.
- Vivado.
- VxWorks VSB/VIP.
- Docker or Podman.
- GHDL for FPGA/IP verification.
- Documentation build systems.

Known artifact types:

- Component libraries.
- Runtime binaries.
- VxWorks kernel image.
- Runtime install tree.
- FPGA bitstream.
- FPGA XSA/HDF/HWDEF.
- Device tree source and blob.
- Boot image.
- Deployment tarball.
- CI logs.
- Verification reports.

## Deployment Model

SERGEANT deployment should be modeled at a reusable pattern level, with
product-specific details delegated to product models.

```text
DeploymentProfile
  name
  product
  designVariant
  targetEnvironment
  transportMechanisms
  requiredArtifacts
  runtimeLaunchMethod
  evidenceRequirements
```

Deployment patterns:

- TFTP/FTP/U-Boot deployment.
- UART/TIO controlled deployment.
- Runtime image deployment.
- FPGA bitstream loading.
- Test harness deployment.
- Bench power-control integration.
- Containerized simulation deployment.

## Verification and Evidence Model

The SERGEANT model should support evidence rollup across products and assets.

```text
EvidenceRecord
  id
  evidenceType
  product
  designVariant
  reusableAsset
  sourceRevision
  artifact
  verificationCase
  verdict
  timestamp
  producer
```

Evidence types:

- Source revision evidence.
- Submodule revision evidence.
- Build log evidence.
- CI stage evidence.
- FPGA timing evidence.
- FPGA utilization evidence.
- FPGA power evidence.
- GHDL test evidence.
- Runtime log evidence.
- Deployment evidence.
- Release publish evidence.
- Waiver evidence.

Evidence rollups should answer:

- Which product variants are release-ready?
- Which variants have missing timing closure evidence?
- Which reusable assets lack current test evidence?
- Which design variants depend on stale or divergent asset revisions?
- Which release artifacts trace back to source revisions and CI stages?

## Analysis Model

### Reuse Impact Analysis

Purpose: identify which products and variants are affected by a reusable asset
change.

Inputs:

- Reusable asset.
- Products using the asset.
- Design variants using the asset.
- Current source revisions.
- Evidence status.

Outputs:

```text
impactedProducts
impactedVariants
requiredRebuilds
requiredReverification
riskLevel
```

### Version Drift Analysis

Purpose: identify when products or worktrees use different revisions of the
same reusable asset.

Outputs:

```text
assetName
revisionByProduct
revisionByVariant
revisionByWorktree
driftDetected
recommendedReconciliation
```

### Release Readiness Analysis

Purpose: determine whether a product variant is ready to release or deploy.

Checks:

- Required source revisions captured.
- Required build artifacts produced.
- FPGA timing evidence present when applicable.
- Runtime evidence present when applicable.
- Deployment evidence present when applicable.
- Security and secret-handling policies satisfied.
- Waivers recorded for missing evidence.

### Cross-Product Build Graph Analysis

Purpose: identify common build patterns and product-specific differences.

Outputs:

- Products using Make, CMake, `smake`, Jenkins, Vivado, VxWorks, Docker.
- Artifact types by product.
- Build stages by product.
- Reusable tooling dependencies.
- Build risk areas.

### Security and Supply-Chain Analysis

Purpose: connect security architecture concerns to build, release, deployment,
and evidence flows.

Checks:

- Container images are identified and traceable.
- Artifact repositories are identified.
- Secret-bearing configuration files are excluded from model content.
- Boot/security artifacts are classified.
- Release artifacts have checksums and source trace.
- Deployment credentials are represented as external prerequisites, not stored
  values.

## Requirements

### Product-Line Requirements

```text
REQ-SGT-PL-001
  The SERGEANT model shall identify each product, design repository, and design
  variant included in the modeled product line.

REQ-SGT-PL-002
  The SERGEANT model shall identify reusable assets and the products and design
  variants that use them.
```

### Reuse Requirements

```text
REQ-SGT-REUSE-001
  Each reusable asset shall trace to a source repository, source path, supported
  products, and evidence summary.

REQ-SGT-REUSE-002
  The model shall support impact analysis from a reusable asset to affected
  products and design variants.
```

### Build and Release Requirements

```text
REQ-SGT-BUILD-001
  Each modeled product shall identify its build systems, CI pipelines, produced
  artifact types, and release repositories.

REQ-SGT-BUILD-002
  Each release artifact shall trace to source revision evidence, build evidence,
  verification evidence, and publish evidence.
```

### Deployment Requirements

```text
REQ-SGT-DEPLOY-001
  Each deployable product variant shall identify its deployment pattern,
  required artifacts, target environment, and deployment evidence.
```

### Evidence Requirements

```text
REQ-SGT-EVIDENCE-001
  The SERGEANT model shall distinguish declared configuration, generated
  artifact, verification result, and release evidence.

REQ-SGT-EVIDENCE-002
  Evidence rollups shall identify missing, stale, waived, failed, and passing
  evidence states.
```

### Security Requirements

```text
REQ-SGT-SEC-001
  The SERGEANT model shall represent required secret types and security controls
  without storing secret values.

REQ-SGT-SEC-002
  Release artifacts shall trace to integrity evidence such as checksums,
  source revisions, and producing pipelines.
```

## Transformation and Execution Pipeline

The model should support a staged extraction and federation pipeline:

```text
SERGEANT workspace
  -> scan product repositories
  -> extract design variants
  -> extract reusable assets
  -> extract build and deployment profiles
  -> extract source revisions and submodule status
  -> ingest lower-level model summaries
  -> ingest build/release/deployment evidence
  -> instantiate SERGEANT SysML packages
  -> render product-line, reuse, evidence, and release views
```

Lower-level models should publish summary artifacts that the SERGEANT model can
consume:

```text
PGM SDRx summary
T1TL summary
GEnCor summary
Channel Controller summary
Security summary
Deployment summary
```

## Parser and Summary Contract

The SERGEANT model should ingest normalized JSON summaries from lower-level
extractors.

Example product summary:

```json
{
  "product": "PGM_SDRx",
  "repository": "/home/cosgroma/workspace/sergeant/designs/pgm",
  "designVariants": [
    "magnompgm_sgt_mopd_reprog",
    "magnompgm_integrated_sgt_anv",
    "secure_arch_zcu102",
    "playback_mopd"
  ],
  "components": ["os", "cc", "sm", "mio", "em", "sc", "fm", "pp", "th"],
  "engines": ["gencor", "mopd", "sample_stream", "collector"],
  "buildSystems": ["Make", "CMake", "smake", "Jenkins", "Vivado", "VxWorks"],
  "deploymentPatterns": ["TFTP", "FTP", "U-Boot", "UART/TIO"]
}
```

Example reusable asset summary:

```json
{
  "asset": "gencor",
  "assetType": "FpgaIpAndRuntimeEngine",
  "repository": "/home/cosgroma/workspace/sergeant/engines/gencor",
  "usedByProducts": ["PGM_SDRx"],
  "usedByVariants": ["magnompgm_sgt_mopd_reprog"],
  "linkedModel": "docs/sergeant/gencor-fpga-resource-timing.md",
  "evidenceStatus": "partial"
}
```

Example evidence rollup:

```json
{
  "product": "PGM_SDRx",
  "variant": "magnompgm_sgt_mopd_reprog",
  "sourceRevisionCaptured": true,
  "buildEvidence": "present",
  "fpgaTimingEvidence": "unknown",
  "runtimeEvidence": "unknown",
  "deploymentEvidence": "unknown",
  "releaseReadiness": "not_ready"
}
```

## Views

The model should provide these stakeholder views:

- SERGEANT product-line overview.
- Product portfolio view.
- Product-to-design-repository map.
- Design variant catalog.
- Product-to-component matrix.
- Product-to-engine matrix.
- Product-to-FPGA-IP matrix.
- Reusable asset impact view.
- Version drift view.
- Cross-product build system view.
- CI/release pipeline view.
- Deployment pattern view.
- Evidence coverage dashboard.
- Release readiness dashboard.
- Security and supply-chain trace view.
- Lower-level model federation view.

## Open Questions

- Should `comps/`, `designs/`, and `engines/` be treated as one workspace model
  or as separate federated source repositories with a workspace overlay?
- Which SERGEANT products should be included in the first modeled portfolio:
  only PGM SDRx and T1TL, or additional inactive/archived products?
- What is the canonical source of truth for reusable component ownership?
- Should GEnCor worktrees under `engines/gencor-*` be modeled as development
  branches, forks, experiments, or temporary evidence sources?
- Which CI systems besides Jenkins should be modeled?
- Which artifact repositories are authoritative for release evidence?
- What policy defines stale evidence: time-based, source-revision-based, or
  artifact-version-based?
- Which security controls should be inherited from the UAF/security model and
  applied to build and release evidence?

## Initial Implementation Steps

1. Create a SERGEANT workspace extractor that inventories `comps/`, `designs/`,
   and `engines/`.
2. Extract product repositories and design repositories from the workspace.
3. Import the PGM SDRx model summary from the PGM design model.
4. Add a T1TL design summary extractor for variants, build systems, FPGA
   profiles, and deployment patterns.
5. Import the GEnCor model summary from the GEnCor FPGA/IP model.
6. Define reusable asset records for components, engines, libraries, FPGA IP,
   tools, and container images.
7. Add source revision and worktree status evidence ingestion.
8. Build initial product-to-asset, asset-impact, version-drift, and
   release-readiness views.
9. Add security and supply-chain trace fields for artifact repositories,
   container images, boot artifacts, checksums, and secret-handling policies.
