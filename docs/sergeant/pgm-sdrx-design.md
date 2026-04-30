# PGM SDRx Design SysML v2 Model Specification

This document specifies a SysML v2 model for the PGM SDRx design located at:

```text
/home/cosgroma/workspace/sergeant/designs/pgm
```

The model is intended to capture the full product build and deployment context:
software component builds, legacy engine builds, VxWorks kernel and runtime
image builds, FPGA bitstream and XSA builds, boot artifacts, device trees,
deployment scripts, CI orchestration, and verification evidence.

This model should sit above the narrower Channel Controller and GEnCor models.
The Channel Controller model covers receiver runtime behavior. The GEnCor model
covers FPGA/IP resource, timing, power, and target trade studies. This PGM SDRx
model covers the end-to-end design variant that selects, builds, packages, and
deploys those pieces together.

## Goals

- Represent each PGM SDRx design variant as the root of a build and deployment
  configuration.
- Capture the software component stack selected by each variant.
- Capture the legacy engine, library, daemon, app, and tool selections used by
  the `smake` build system.
- Capture the VxWorks, VSB, VIP, BSP, boot, U-Boot, ATF, PMU firmware, and
  device-tree build relationships.
- Capture the FPGA build selection: board, part, block design TCL, constraints,
  generics, bitstream, BIN, HDF/HWDEF, and XSA artifacts.
- Capture runtime installation layout under `runtime/<os>/<arch>`.
- Capture deployment profiles, TFTP/FTP paths, UART/TIO deployment scripts, and
  U-Boot commands.
- Trace CI build stages and generated artifacts to source revisions,
  configuration files, build logs, timing checks, runtime checks, and published
  artifact bundles.
- Support variant comparison, build completeness, deployment readiness, and
  evidence coverage analysis.

## Non-Goals

- This model will not replace `make`, CMake, `smake`, Jenkins, Vivado, VxWorks
  tooling, Docker, or deployment scripts.
- This model will not encode every source file in every component.
- This model will not model low-level runtime behavior already covered by the
  Channel Controller model.
- This model will not model GEnCor IP timing/resource internals already covered
  by the GEnCor FPGA resource and timing model.
- This model will not store credentials, private deployment secrets, or
  machine-local passwords.
- This model will not assume that all variant configurations are valid until
  existence, consistency, and evidence checks pass.

## Source References

Primary source tree:

```text
/home/cosgroma/workspace/sergeant/designs/pgm
```

Key local references:

- `README.md`
- `Makefile`
- `CMakeLists.txt`
- `Jenkinsfile`
- `VERSION`
- `check_runtime.py`
- `check_timing.py`
- `config/base.mk`
- `config/config.*.mk`
- `config/fpga/fpga.*.mk`
- `config/fpga/generics*.tcl`
- `config/boot/boot.*.mk`
- `config/deployment/deploy.*.mk`
- `config/dts_files/**`
- `config/uenv_files/**`
- `config/vsb_profiles/**`
- `smake/Makefile`
- `smake/paths.mk`
- `smake/rules/components.mk`
- `smake/rules/fpga.mk`
- `smake/rules/kernel.mk`
- `smake/rules/deployment.mk`
- `smake/rules/docker.mk`
- `smake/rules/devicetrees.mk`
- `smake/rules/bootrom.mk`
- `smake/kernels/vxworks7/vsb.mk`
- `smake/kernels/vxworks7/vip.mk`
- `smake/deployment/makefile`
- `fpga/designs/**`
- `comp/*/CMakeLists.txt`
- `comp/*/Makefile`
- `comp/*/Dockerfile`
- `core/engines/**`
- `core/libsrc/**`
- `runtime/**`
- `.gitmodules`

Related local MBSE references:

- `docs/sergeant/cc-channel-controller.md`
- `docs/sergeant/gencor-fpga-resource-timing.md`
- `docs/model-specs/container-deployment.md`
- `docs/model-specs/security-architecture.md`
- `docs/methodology/sysml-v2-transformation-pipeline-design.md`
- `docs/methodology/sysml-v2-verification-model-setup.md`

## Source-Derived Facts

The initial model can be seeded from existing repository metadata.

| Source | Extracted model content |
| --- | --- |
| `.gitmodules` | Submodule inventory and external source boundaries |
| `config/config.*.mk` | Design variant definitions, board, architecture, OS, component set, engines, compile flags |
| `config/fpga/fpga.*.mk` | FPGA target, part number, board, block design TCL, XDC, generics, XSA/HDF/BIT/BIN paths |
| `config/deployment/deploy.*.mk` | Deployment servers, TFTP/FTP paths, U-Boot command, UART/TIO script, runtime script |
| `config/boot/boot.*.mk` | Boot image and operational/golden/multiboot selections |
| `smake/paths.mk` | Canonical build, runtime, FPGA, config, component, and install paths |
| `smake/rules/components.mk` | Component and legacy build target organization |
| `smake/rules/fpga.mk` | FPGA, BSP, device tree, U-Boot, ATF, PMU firmware, and bootgen flow |
| `smake/kernels/vxworks7/*.mk` | VxWorks VSB/VIP build steps and kernel component rules |
| `CMakeLists.txt` | Design-level CMake integration, component interface libraries, test build linkage |
| `Jenkinsfile` | CI parameters, build stages, timing/runtime checks, publish targets |
| `check_timing.py` | Timing-pass evidence rule for FPGA build logs/reports |
| `check_runtime.py` | Runtime-log evidence rule for software/target run |

## Model Boundary

The model covers an end-to-end PGM SDRx design variant:

```text
design variant selection
  -> board, processor, OS, and runtime profile
  -> software component and legacy engine selection
  -> Docker/container build environment selection
  -> CMake and smake component builds
  -> VxWorks VSB/VIP/kernel/BSP build
  -> FPGA Vivado block design and bitstream build
  -> XSA/HDF/HWDEF, device tree, boot, U-Boot, ATF, PMU firmware artifacts
  -> runtime install tree
  -> deployment package
  -> TFTP/FTP/UART/TIO deployment
  -> timing, runtime, and deployment evidence
```

The model should expose:

- Design variant catalog.
- Component and engine build selection by variant.
- Build graph from source/configuration to generated artifact.
- FPGA design selection and bitstream artifact trace.
- OS/kernel/runtime artifact trace.
- Deployment readiness checks.
- CI/publish artifact trace.
- Variant comparison views.

## Recommended Package Structure

```text
PgmSdrxDesignModel
  Libraries
    BuildSystems
    FpgaBuilds
    VxWorksBuilds
    DeploymentSystems
    ArtifactManagement
    VerificationEvidence
  Metadata
  Stakeholders_Concerns
    ProductIntegrationConcerns
    BuildReleaseConcerns
    FpgaImplementationConcerns
    RuntimeDeploymentConcerns
    VerificationConcerns
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
    EvidenceDefinitions
  SourceArtifacts
    PgmRepository
    GitSubmodules
    TopLevelMakefiles
    CMakeConfiguration
    SmakeConfiguration
    JenkinsPipeline
    VariantConfigurationFiles
    FpgaConfigurationFiles
    BootConfigurationFiles
    DeploymentConfigurationFiles
    DeviceTreeSources
  ProductLine
    DesignVariants
    BoardProfiles
    ProcessorProfiles
    OperatingSystemProfiles
    RuntimeProfiles
    FpgaProfiles
    DeploymentProfiles
  SourceArchitecture
    SoftwareComponents
    LegacyLibraries
    LegacyEngines
    LegacyDaemons
    LegacyApps
    Tools
    DeviceTrees
    RuntimeScripts
    FpgaBlockDesigns
  BuildArchitecture
    BuildEnvironments
    DockerImages
    CMakeBuilds
    SmakeBuilds
    ComponentBuilds
    VxWorksVsbBuilds
    VxWorksVipBuilds
    BspBuilds
    FpgaVivadoBuilds
    BootArtifactBuilds
    DeploymentPackageBuilds
  DeploymentArchitecture
    RuntimeImage
    TftpDeployment
    FtpRuntimeDeployment
    UBootExecution
    UartTioControl
    BenchNetwork
    PowerControl
  Analysis
    VariantCompletenessAnalysis
    BuildGraphAnalysis
    ArtifactCompletenessAnalysis
    FpgaTimingClosureAnalysis
    RuntimeConfigConsistencyAnalysis
    DeploymentReadinessAnalysis
    VariantComparisonAnalysis
    EvidenceCoverageAnalysis
  Verification
    BuildVerificationCases
    FpgaVerificationCases
    RuntimeVerificationCases
    DeploymentVerificationCases
    ReleaseVerificationCases
  Evidence
    SourceRevisionEvidence
    BuildLogEvidence
    RuntimeLogEvidence
    FpgaReportEvidence
    BitstreamEvidence
    XsaEvidence
    KernelImageEvidence
    DeviceTreeEvidence
    BootImageEvidence
    DeploymentEvidence
    PublishedArtifactEvidence
  Views_Viewpoints
    ProductLineViews
    VariantViews
    BuildGraphViews
    ArtifactTraceViews
    DeploymentViews
    VerificationViews
    ReleaseViews
```

## Product Line Model

The central model element should be `DesignVariant`. A design variant selects
the board, architecture, OS, component set, FPGA target, deployment profile, and
required verification evidence.

```text
DesignVariant
  name
  board
  architecture
  processorMode
  operatingSystem
  containerImage
  componentSet
  legacyEngineSet
  fpgaProfile
  bootProfile
  deploymentProfile
  runtimeProfile
  requiredArtifacts
  requiredVerificationCases
```

Initial variant instances should be extracted from `config/config.*.mk`,
including:

```text
ad9361_altnav
ad9361_mopd
ad9361_performance
altnav_dom0_zcu102
altnav_federated_zcu102
magnompgm_federated_sg_core
magnompgm_integrated_sgt_anv
magnompgm_sgt_mopd_pcode
magnompgm_sgt_mopd_pcode_cdc
magnompgm_sgt_mopd_reprog
multiboot_magnompgm
playback_mopd
playback_mopd_new
pseudoInt_sgt_anv
secure_arch_magnompgm
secure_arch_zcu102
```

The initial deep modeling target should be:

```text
magnompgm_sgt_mopd_reprog
```

This variant currently exposes a useful cross-section of the full stack:
PGM board, ARM architecture, VxWorks runtime, new software components, legacy
engines, GEnCor/MOPD FPGA topology, reprogrammer behavior, U-Boot/ATF settings,
deployment command construction, and runtime script selection.

## Source Architecture Model

### Software Components

The model should represent each component as a buildable software unit with
interfaces, compile definitions, install outputs, and evidence.

Initial new component set:

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

Each `SoftwareComponent` should capture:

```text
SoftwareComponent
  name
  sourcePath
  cmakeFile
  makefile
  dockerfile
  interfaceLibrary
  compileDefinitions
  installOutputs
  tests
  buildEvidence
```

The model should avoid duplicating each component's internal architecture unless
that architecture is relevant to product-level build or deployment. Detailed
runtime behavior should be delegated to component-specific models such as the
Channel Controller model.

### Legacy Engines

Legacy engine selection should be modeled separately from new components.

Example engine set from `magnompgm_sgt_mopd_reprog`:

```text
host
ad9257
max2112
decimator
frequency_mixer
band_separator
gencor
spectrum
collector
one_pps
sample_stream
pcu
ad9912
ad9915
mopd
hotstart_timing
```

Each `LegacyEngine` should capture:

```text
LegacyEngine
  name
  sourcePath
  buildTarget
  installOutputs
  fpgaOrRuntimeRole
  deviceTreeNodeCompatibility
  relatedDriver
  evidence
```

### Device Trees and Runtime Scripts

The model should treat device trees and runtime scripts as integration
artifacts. They bind software, FPGA IP, hardware buses, kernel drivers, and
runtime behavior.

```text
DeviceTreeArtifact
  sourceDtsPath
  generatedDtbPath
  designVariant
  compatibleNodes
  hardwareBindings
  generatedFromXsa
  deploymentRole

RuntimeScript
  path
  designVariant
  launchedBy
  runtimeRole
  requiredFiles
```

## Build Architecture Model

The build architecture should distinguish build systems and artifact producers.

### Build Environment

```text
BuildEnvironment
  hostOs
  containerRuntime
  containerImage
  vivadoVersion
  vxWorksToolchain
  crossCompiler
  requiredEnvironmentVariables
  requiredSecretsOrCredentials
```

Credentials should only be represented as required secret types, not stored
values.

### Component Build

The top-level build has both CMake and `smake` surfaces. The model should
capture both:

```text
ComponentBuild
  component
  buildSystem: CMake | Smake | Make | External
  buildTarget
  cleanTarget
  installTarget
  containerized
  compileDefinitions
  inputArtifacts
  outputArtifacts
  buildLog
```

### VxWorks Build

The VxWorks build should be modeled as separate but connected steps.

```text
VxWorksBuild
  vsbProfile
  vipProfile
  bsp
  kernelComponents
  kernelDefines
  processor
  procMode
  outputImage
  buildLogs
```

Important build products:

- VSB project and output.
- VIP project and `uVxWorks`.
- BSP generated from XSA.
- Kernel modules or partial images.
- Runtime install tree under `runtime/<os>/<arch>`.

### FPGA Build

The FPGA build model should bind a design variant to a block design and
generated artifacts.

```text
FpgaBuild
  designVariant
  board
  boardClass
  fpgaPart
  targetName
  targetVersion
  synthMode
  numEngines
  numMopdBsgs
  systemBdTcl
  systemBdXdc
  systemBdWrapper
  designGenericsTcl
  buildDirectory
  bitstream
  binFile
  hdfFile
  hwdefFile
  xsaFile
  timingReport
  utilizationReport
  powerReport
  buildLog
```

For `magnompgm_sgt_mopd_reprog`, seed values include:

```text
board = pgm
fpgaPart = xqzu15eg-ffrc900-1m-m
numEngines = 18
numMopdBsgs = 12
systemBdTcl = fpga/designs/magnom.pgm.xqzu15eg-ffrc900-1m-m.pgm/system_bd_sgt_mopd_reprog.tcl
systemBdXdc = fpga/designs/magnom.pgm.xqzu15eg-ffrc900-1m-m.pgm/system_bd_sgt_mopd_reprog.xdc
designGenericsTcl = config/fpga/generics.magnompgm_sgt_mopd_reprog_4gb_ddr.tcl
```

The model should connect this to the GEnCor FPGA resource and timing model for
engine-level resource, timing, and power analysis.

### Boot Artifact Build

Boot artifacts should be represented explicitly because they cross software,
FPGA, hardware, and security concerns.

```text
BootArtifactBuild
  bootProfile
  fsbl
  pmuFirmware
  armTrustedFirmware
  uBoot
  bootBin
  bifFile
  keyMaterialRequirement
  goldenOrOperationalRole
  multibootRole
```

## Deployment Architecture Model

Deployment profiles should bind generated artifacts to bench infrastructure.

```text
DeploymentProfile
  designVariant
  tftpServer
  tftpRoot
  ftpServer
  ftpRoot
  uartHost
  uartPort
  runtimeScript
  uBootCommand
  deploymentKernel
  deploymentDtb
  deploymentFpgaBitstream
  deploymentRuntimeImage
  deploymentLogs
```

The `deploy.*.mk` files should be treated as source artifacts for deployment
profiles. For `magnompgm_sgt_mopd_reprog`, deployment includes:

- TFTP server and root.
- FTP server and runtime root.
- UART host/port.
- `uVxWorks` image.
- `a53_operational.dtb`.
- FPGA `.bit`.
- U-Boot command that loads kernel, DTB, and bitstream before booting.
- TIO script that resets the board, interrupts autoboot, and executes the
  generated U-Boot command.

## Analysis Model

### Variant Completeness Analysis

Purpose: verify that a design variant has all required source configuration
files and selected build/deployment profiles.

Checks:

- `config/config.<variant>.mk` exists.
- `config/fpga/fpga.<variant>.mk` exists when FPGA build is required.
- `config/deployment/deploy.<variant>.mk` exists when deployment is required.
- Referenced board configuration exists.
- Referenced boot profile exists when boot artifacts are required.
- Referenced device tree paths exist.
- Referenced runtime scripts exist.

### Build Graph Analysis

Purpose: derive the artifact dependency graph from source, configuration, and
build rules.

Outputs:

```text
artifactProducer
artifactConsumers
sourceInputs
configurationInputs
toolInputs
buildTarget
buildLogPath
```

The model should answer questions such as:

- Which target produces the bitstream?
- Which target produces XSA?
- Which target consumes XSA to produce BSP?
- Which target produces `uVxWorks`?
- Which deployment target consumes bitstream, DTB, runtime scripts, and kernel?

### Artifact Completeness Analysis

Purpose: verify that a completed build produced all required artifacts.

Required artifact categories:

- Component libraries and interfaces.
- Runtime binaries.
- Runtime scripts and configuration.
- FPGA `.bit`, `.bin`, `.xsa`, `.hdf` or `.hwdef`.
- Device tree `.dts` and `.dtb`.
- VxWorks `uVxWorks`.
- Boot images such as `BOOT.bin`, when selected.
- Build logs and verification logs.
- Published artifact tarballs, when CI publishing is selected.

### FPGA Timing Closure Analysis

Purpose: connect FPGA build output to timing closure evidence.

Inputs:

- FPGA target profile.
- Generated timing reports.
- `check_timing.py` result.
- Jenkins stage verdict, when available.

Outputs:

```text
timingReportPath
timingMet
violatingClocks
criticalWarnings
timingEvidenceStatus
```

Timing closure should trace to the selected block design TCL, XDC, generics,
Vivado version, FPGA part, and build log.

### Runtime Configuration Consistency Analysis

Purpose: check that software build flags, FPGA build parameters, device-tree
nodes, and deployment artifacts describe the same target system.

Example checks:

- `NUM_ENGINES` in FPGA config is compatible with GEnCor/CC runtime assumptions.
- MOPD enable flags in CC build are compatible with MOPD FPGA topology.
- Device-tree compatible nodes include selected FPGA IP.
- Runtime scripts align with selected program mode.
- Deployment profile uses the generated bitstream target version.
- Kernel/BSP processor profile matches the FPGA/XSA processor profile.

### Deployment Readiness Analysis

Purpose: verify that a deployable target image is ready for bench or hardware
execution.

Checks:

- TFTP and FTP paths resolve.
- Kernel, DTB, bitstream, and runtime tree exist.
- Bitstream size is available for U-Boot `fpga loadb`.
- U-Boot command is fully constructed.
- UART/TIO script has host and port bindings.
- Runtime script exists in the installed runtime tree.
- Required credentials are represented as external prerequisites.

### Variant Comparison Analysis

Purpose: compare variants across target platform, component set, FPGA design,
deployment mode, and evidence state.

Outputs:

- Board and FPGA part comparison.
- Component and engine deltas.
- FPGA design TCL/XDC deltas.
- Boot/deployment profile deltas.
- Evidence completeness by variant.
- Risk flags by missing artifact or stale evidence.

### Evidence Coverage Analysis

Purpose: determine whether each requirement and artifact has sufficient
evidence.

Coverage dimensions:

- Source exists.
- Build target exists.
- Build ran.
- Artifact produced.
- Artifact checked.
- Artifact deployed.
- Runtime verified.
- Release published.

## Evidence Model

### Evidence Types

```text
SourceRevisionEvidence
  repositoryPath
  gitCommit
  submoduleStatus
  dirtyState
  extractionTimestamp

BuildLogEvidence
  buildTarget
  designVariant
  logPath
  verdict
  timestamp

FpgaReportEvidence
  designVariant
  fpgaPart
  vivadoVersion
  timingReport
  utilizationReport
  powerReport
  checkTimingVerdict

BitstreamEvidence
  bitstreamPath
  binPath
  xsaPath
  hdfPath
  hwdefPath
  targetVersion
  checksum

KernelImageEvidence
  kernelImagePath
  bsp
  processor
  procMode
  vsbProfile
  vipProfile

DeviceTreeEvidence
  dtsPath
  dtbPath
  compatibleNodes
  sourceXsa

DeploymentEvidence
  deploymentProfile
  tftpPath
  ftpPath
  uartLogPath
  uBootCommand
  deploymentVerdict

RuntimeLogEvidence
  runtimeLogPath
  checkRuntimeVerdict
  observedServices
  observedErrors

PublishedArtifactEvidence
  artifactUrl
  artifactName
  artifactType
  publishRepository
  checksum
```

### Evidence Acceptance Rules

- A build artifact is not verified only because its path is declared. It must be
  produced by a build or found with a source revision and timestamp.
- FPGA timing closure requires timing-report evidence and `check_timing.py` or
  equivalent parser evidence.
- Runtime readiness requires runtime-log evidence or a documented waiver.
- Deployment readiness requires the kernel, DTB, FPGA bitstream, runtime script,
  and U-Boot command to be mutually consistent.
- Release readiness requires source revision evidence, build logs, artifact
  checksums, and publish evidence.
- CI evidence should preserve Jenkins parameters such as design variant, golden
  image variant, make target, FPGA build enable, and operational boot enable.

## Requirements

### Variant Requirements

```text
REQ-PGM-VARIANT-001
  Each modeled design variant shall identify its board, architecture,
  processor mode, operating system, component set, FPGA profile, boot profile,
  deployment profile, and required artifacts.

REQ-PGM-VARIANT-002
  Each modeled design variant shall trace to its source configuration files.
```

### Build Requirements

```text
REQ-PGM-BUILD-001
  The model shall identify the build target that produces each required
  software, FPGA, kernel, boot, and deployment artifact.

REQ-PGM-BUILD-002
  The model shall distinguish source configuration, generated artifact, and
  verification evidence.
```

### FPGA Requirements

```text
REQ-PGM-FPGA-001
  Each FPGA-enabled design variant shall identify its FPGA board, part,
  block-design TCL, constraints, generics, build directory, bitstream, and XSA.

REQ-PGM-FPGA-002
  Each FPGA-enabled design variant shall trace timing-closure status to FPGA
  implementation evidence.
```

### Runtime Requirements

```text
REQ-PGM-RUNTIME-001
  Each runtime-enabled design variant shall identify its runtime installation
  tree, kernel image, device tree, runtime scripts, and selected component
  outputs.
```

### Deployment Requirements

```text
REQ-PGM-DEPLOY-001
  Each deployable design variant shall identify its TFTP/FTP deployment paths,
  UART/TIO control path, U-Boot command, and required deployment artifacts.
```

### Evidence Requirements

```text
REQ-PGM-EVIDENCE-001
  Each verification verdict shall trace to source revision, design variant,
  build target, generated artifacts, logs, parser or checker, and timestamp.
```

## Transformation and Execution Pipeline

The model should support this extraction and execution pipeline:

```text
PGM source tree
  -> extract variants from config/config.*.mk
  -> extract FPGA profiles from config/fpga/fpga.*.mk
  -> extract deployment profiles from config/deployment/deploy.*.mk
  -> extract build rules from smake and top-level Makefiles
  -> extract CI stages from Jenkinsfile
  -> generate normalized model JSON
  -> instantiate SysML v2 packages
  -> run completeness and consistency analyses
  -> ingest build, timing, runtime, and deployment evidence
  -> render build graph, artifact trace, and verification views
```

The model should also support build execution as a controlled transformation:

```text
SysML DesignVariant instance
  -> normalized build command set
  -> make / cmake / smake / Vivado / VxWorks commands
  -> generated artifacts
  -> parser/checker outputs
  -> SysML evidence records
  -> requirement verification status
```

## Report and Artifact Parser Contract

The model should ingest normalized JSON from parsers instead of parsing Makefile
or log text inside SysML logic.

Example variant extraction:

```json
{
  "variant": "magnompgm_sgt_mopd_reprog",
  "board": "pgm",
  "arch": "armarch7",
  "os": "vx7",
  "procMode": "SMP",
  "components": ["os", "cc", "sm", "mio", "em", "sc", "fm", "pp", "th"],
  "engines": [
    "host",
    "ad9257",
    "max2112",
    "decimator",
    "frequency_mixer",
    "band_separator",
    "gencor",
    "spectrum",
    "collector",
    "one_pps",
    "sample_stream",
    "pcu",
    "ad9912",
    "ad9915",
    "mopd",
    "hotstart_timing"
  ]
}
```

Example FPGA profile extraction:

```json
{
  "variant": "magnompgm_sgt_mopd_reprog",
  "board": "pgm",
  "fpgaPart": "xqzu15eg-ffrc900-1m-m",
  "numEngines": 18,
  "numMopdBsgs": 12,
  "systemBdTcl": "fpga/designs/magnom.pgm.xqzu15eg-ffrc900-1m-m.pgm/system_bd_sgt_mopd_reprog.tcl",
  "systemBdXdc": "fpga/designs/magnom.pgm.xqzu15eg-ffrc900-1m-m.pgm/system_bd_sgt_mopd_reprog.xdc",
  "designGenerics": "config/fpga/generics.magnompgm_sgt_mopd_reprog_4gb_ddr.tcl"
}
```

Example artifact status:

```json
{
  "variant": "magnompgm_sgt_mopd_reprog",
  "artifact": "fpgaBitstream",
  "path": "build/fpga/<target-version>/<target-version>.bit",
  "producer": "make fpga",
  "status": "produced",
  "evidence": "build/logs/build-fpga.log"
}
```

## Views

The model should provide these stakeholder views:

- Design variant catalog.
- Variant-to-component matrix.
- Variant-to-FPGA profile matrix.
- Build graph view.
- Software component build view.
- Legacy engine build view.
- FPGA build and artifact view.
- VxWorks VSB/VIP/kernel build view.
- Boot artifact view.
- Device-tree binding view.
- Runtime install tree view.
- Deployment readiness view.
- Jenkins pipeline evidence view.
- Requirement verification dashboard.
- Release artifact trace view.

## Open Questions

- Which PGM design variant should be treated as the initial canonical baseline?
- Which Jenkins parameters should be modeled as first-class variant controls?
- Should generated build artifacts be indexed from local `build/` directories,
  Nexus-published tarballs, or both?
- Should submodule revision capture be performed from the parent PGM repo only,
  or also recursively within component repos?
- Which runtime log patterns from `check_runtime.py` are authoritative
  pass/fail criteria?
- Which FPGA timing reports should be parsed directly versus relying on
  `check_timing.py`?
- How should machine-local deployment assumptions be represented without
  storing sensitive server or credential values?
- Should this model generate build commands, or only verify commands generated
  by the existing make/Jenkins flow?

## Initial Implementation Steps

1. Create a source extraction script for `config/config.*.mk`,
   `config/fpga/fpga.*.mk`, `config/deployment/deploy.*.mk`, `smake/paths.mk`,
   and `.gitmodules`.
2. Generate normalized JSON for design variants, component sets, engine sets,
   FPGA profiles, deployment profiles, and required artifacts.
3. Create SysML v2 package skeletons for product line, source architecture,
   build architecture, deployment architecture, analysis, and evidence.
4. Implement variant completeness checks for `magnompgm_sgt_mopd_reprog`.
5. Implement FPGA artifact checks for block design TCL, XDC, generics, bitstream
   path, and XSA path.
6. Implement deployment readiness checks for kernel, DTB, bitstream, runtime
   script, TFTP/FTP paths, and U-Boot command construction.
7. Ingest `check_timing.py`, `check_runtime.py`, and Jenkins stage outcomes as
   verification evidence.
8. Build initial views for variant catalog, build graph, artifact trace, and
   deployment readiness.
