# CC Channel Controller SysML v2 Model Specification

This document specifies the intended SysML v2 model for the Sergeant PGM
Channel Controller component located at:

```text
~/workspace/sergeant/designs/pgm/comp/cc
```

The model is intended to capture the Channel Controller architecture, runtime
contracts, timing behavior, interfaces, requirements, analysis cases,
verification cases, and evidence traceability. It should not be a file-by-file
translation of the C/C++ source tree. Source files, tests, documents, and
analysis scripts should be linked as implementation and evidence artifacts.

## Goals

- Represent the Channel Controller as a GNSS/SDR runtime component.
- Capture the stable runtime architecture: Main, Pipeline, Channel Manager,
  Channel Monitor, Channel, GEnCor, Napal, and Telemetry Manager.
- Model timing-sensitive behavior such as the 1 kHz TOR-driven epoch,
  channel-worker fanout/fan-in, correlator control latency, and measurement
  generation.
- Capture key IPC surfaces: pipes, events, shared memory, command messages,
  telemetry messages, and measurement/status publication.
- Trace requirements to modules, interfaces, behaviors, tests, analysis
  artifacts, and verification evidence.
- Reuse existing Python `models/` analyses as SysML v2 `analysis case`
  execution backends where appropriate.
- Provide a path to generate SysML v2 views and trace reports from existing
  repository metadata.

## Non-Goals

- This model will not replace the C/C++ source, CMake build, test harnesses, or
  existing developer documentation.
- This model will not encode every struct field, function, macro, or source file
  as a first-class SysML element.
- This model will not attempt cycle-accurate hardware simulation of GEnCor,
  Napal, DMA, or FPGA timing.
- This model will not store sensitive configuration values or runtime secrets.

## Source References

Primary source tree:

```text
/home/cosgroma/workspace/sergeant/designs/pgm/comp/cc
```

Key local references:

- `docs/developer/3_modules/channel/channel_design.md`
- `docs/developer/3_modules/channel/channel_interfaces.md`
- `docs/developer/3_modules/channel_manager/channel_manager_design.md`
- `docs/developer/3_modules/channel_manager/channel_manager_interfaces.md`
- `docs/developer/3_modules/channel_monitor/channel_monitor_design.md`
- `docs/developer/3_modules/gencor/gencor_design.md`
- `docs/developer/3_modules/gencor/gencor_interfaces.md`
- `docs/developer/3_modules/napal/napal_design.md`
- `docs/developer/3_modules/pipeline/pipeline_design.md`
- `docs/developer/3_modules/main/main_design.md`
- `docs/developer/3_modules/telemetry_manager/telemetry_manager_design.md`
- `docs/developer/1_reqts/requirements.md`
- `docs/developer/1_reqts/requirements_traceability_oosem_alignment_and_meta_model.md`
- `docs/developer/5_integration/hotstart_mopd.md`
- `docs/developer/4_testing/README.md`
- `models/docs/domains/gnss.md`
- `models/docs/domains/carrier-baseband-iq.md`
- `models/docs/domains/algorithms-flanking-replica.md`

Related local MBSE references:

- `docs/sysml-v2-verification-model-setup.md`
- `docs/sysml-v2-transformation-pipeline-design.md`
- `docs/rf-to-digital-signal-chain-model-spec.md`
- `docs/security-architecture-model-spec.md`
- `docs/enterprise-architecture-model-spec.md`

## Model Boundary

The model covers the Channel Controller component as a software-defined GNSS
receiver runtime component:

```text
configuration and startup
  -> pipeline construction
  -> channel manager orchestration
  -> channel monitor and assignment
  -> channel acquisition / tracking / measurement
  -> GEnCor / Napal correlator resource interaction
  -> telemetry decode/update path
  -> measurement and status publication
  -> tests, analyses, and evidence
```

The model should expose the following primary outputs:

- Channel Controller component structure.
- 1 kHz runtime behavior and timing contracts.
- Channel lifecycle state model.
- IPC/interface catalog.
- Configuration profile catalog.
- Requirement-to-module trace.
- Requirement-to-test and requirement-to-evidence trace.
- Analysis case outputs for timing, pseudorange, code phase, and correlator
  latency.
- Verification case verdicts.

## Recommended Package Structure

```text
CCChannelControllerModel
  Libraries
    GNSSDomain
    SDRDomain
    RealtimeExecution
    MessagingAndIPC
    VerificationEvidence
  Metadata
  Stakeholders_Concerns
    ReceiverStakeholders
    IntegrationConcerns
    TimingConcerns
    VerificationConcerns
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
  Requirements
    ReceiverRequirements
    TimingRequirements
    MeasurementRequirements
    TelemetryRequirements
    IntegrationRequirements
    BuildConfigurationRequirements
  Architecture
    MainRuntimeArchitecture
    PipelineArchitecture
    ChannelManagerArchitecture
    ChannelMonitorArchitecture
    ChannelArchitecture
    GEnCorArchitecture
    NapalArchitecture
    TelemetryManagerArchitecture
    ModelAnalysisArchitecture
  Interfaces
    CommandInterfaces
    PipeEventShmInterfaces
    CorrelatorInterfaces
    TorSvtcInterfaces
    MeasurementInterfaces
    TelemetryInterfaces
    TestHarnessInterfaces
  Behaviors
    StartupBehavior
    OneKhzEpochBehavior
    ChannelLifecycleBehavior
    ChannelAssignmentBehavior
    HotstartBehavior
    CorrelatorControlBehavior
    MeasurementGenerationBehavior
    TelemetryPublicationBehavior
    ShutdownBehavior
  Configurations
    LinuxHostDebug
    VxWorksTarget
    MoPDHotstartChannelsOnly
    TestHarness
    ModelsAnalysisWorkbench
  Analysis
    TimingAnalysisCases
    PseudorangeAnalysisCases
    CodePhaseAnalysisCases
    CorrelatorLatencyAnalysisCases
    ResourceContentionAnalysisCases
    InterfaceCompletenessAnalysisCases
  Verification
    UnitTestVerificationCases
    HarnessVerificationCases
    IntegrationVerificationCases
    TimingVerificationCases
    TraceabilityVerificationCases
    EvidenceRecords
  Views_Viewpoints
    ComponentStructureViews
    RuntimeBehaviorViews
    InterfaceViews
    ConfigurationViews
    AnalysisViews
    VerificationTraceViews
```

## Core Part Definitions

The model should define reusable runtime component types under
`Definitions/PartDefinitions`.

```text
ChannelController
MainRuntime
CliHarness
Pipeline
ChannelManager
ChannelMonitor
ChannelAssigner
SdrChannel
GEnCor
Napal
TelemetryManager
ConfigurationParser
TorClient
SvtcClient
MeasurementPublisher
StatusPublisher
ModelAnalysisWorkbench
TestHarness
```

### ChannelController

`ChannelController` is the primary subject for system-level analysis and
verification.

Expected owned parts:

- `main : MainRuntime`
- `pipelines : Pipeline[1..*]`
- `channelManager : ChannelManager`
- `channelMonitor : ChannelMonitor`
- `channels : SdrChannel[0..*]`
- `gencor : GEnCor`
- `napal : Napal`
- `telemetryManager : TelemetryManager`
- `configurationParser : ConfigurationParser`
- `analysisWorkbench : ModelAnalysisWorkbench`

Expected attributes:

- `componentName`
- `buildProfile`
- `targetPlatform`
- `maxChannels`
- `epochPeriod_ms`
- `mopdEnabled`
- `hotstartChannelsOnly`
- `testBuildEnabled`
- `runtimeStatus`

### MainRuntime

Expected responsibilities:

- Parse CC configuration.
- Initialize Napal and SDR runtime dependencies.
- Construct `CC_Config_t`.
- Initialize Channel Controller.
- Own the production daemon loop.
- Dispatch queued channel commands.

Expected attributes:

- `startupComplete`
- `eventLoopPeriod_ms`
- `systemControllerEnabled`
- `faultManagerEnabled`
- `cliHarnessEnabled`

### Pipeline

Expected responsibilities:

- Compose `ArgsQueue`, `ChannelManager`, and `ChannelMonitor`.
- Own pipeline parameter copy and naming strategy.
- Set up and tear down runtime resources.
- Bridge top-level configuration to manager/monitor runtime objects.

Expected attributes:

- `pipelineId`
- `rfStreamId`
- `constellation`
- `configPipeName`
- `resourceNamespace`

### ChannelManager

Expected responsibilities:

- Own TOR-driven 1 kHz cadence.
- Fan out control updates to channel workers.
- Coordinate channel worker completion.
- Generate navigation measurements and status.
- Drain config messages for channel add/delete.
- Publish measurement and GNSS status outputs.

Expected attributes:

- `blockCount`
- `maxChannels`
- `activeChannelCount`
- `epochPeriod_ms`
- `torSynced`
- `nonRealTimeMode`
- `lateChannelMask`

### ChannelMonitor

Expected responsibilities:

- Receive channel status, error, and navigation messages.
- Dispatch monitor messages through the message processor table.
- Maintain channel tracking, bit-sync, error, and diagnostic histories.
- Own or embed assignment policy through `ChannelAssigner`.
- Forward navigation data to Telemetry Manager callbacks.

Expected attributes:

- `messagePipeName`
- `messageEventName`
- `csvLoggingEnabled`
- `messageCount`
- `assignmentPolicy`

### SdrChannel

Expected responsibilities:

- Own per-channel acquisition, tracking, telemetry decode, and measurement
  state.
- Consume channel control messages.
- Interact with correlator resources.
- Emit status, errors, navigation messages, and measurement data.

Expected attributes:

- `channelId`
- `prn`
- `constellation`
- `signalType`
- `codeType`
- `state`
- `acqState`
- `trkState`
- `pdi`
- `adi`
- `codePhase_chips`
- `carrierDoppler_Hz`
- `cnr_dBHz`
- `status`

### GEnCor

Expected responsibilities:

- Represent software-facing correlator control and data cadence.
- Own controller/channel configuration and staged upload/download behavior.
- Provide emulator behavior for tests.
- Represent the 1 ms block cycle: download, apply, upload, run replica, queue
  next download.

Expected attributes:

- `gencorId`
- `blockPeriod_ms`
- `codegenProfile`
- `mopdBaseAddress`
- `pipelineLatency_blocks`
- `emulatorEnabled`

### Napal

Expected responsibilities:

- Manage GEnCor resource availability.
- Provide correlator channel allocation and release.
- Wake Channel layer through process events.
- Bridge GEnCor ISR events to receiver ticks.

Expected attributes:

- `napalStarted`
- `taskPriority`
- `gencorCount`
- `resourceBookStatus`

### TelemetryManager

Expected responsibilities:

- Consume decoded navigation messages.
- Update navigation data state.
- Publish ephemeris, iono/UTC, subframe, and related telemetry products.

Expected attributes:

- `telemetryType`
- `publicationStatus`
- `gpsWeekKnown`
- `lastUpdateStatus`

## Core Item Definitions

The model should define reusable message and data item types under
`Definitions/ItemDefinitions`.

```text
ChannelCommand
SdrControlConfigMessage
ChannelControlMessage
ChannelStatusMessage
ChannelErrorMessage
NavigationDataMessage
MeasurementSatnav
GnssStatus
TorTimeData
SvtcStatus
CorrelatorDump
CorrelatorControl
TelemetryProduct
PseudorangeMeasurement
CarrierPhaseMeasurement
CodePhaseProxyState
AnalysisArtifact
TestEvidence
```

## Interfaces and Ports

The model should define ports and interfaces for command, timing, monitor,
telemetry, and measurement paths.

```text
CommandInterface
  conveys ChannelCommand

ConfigPipeInterface
  conveys SdrControlConfigMessage

ChannelControlInterface
  conveys ChannelControlMessage

MonitorMessageInterface
  conveys ChannelStatusMessage, ChannelErrorMessage, NavigationDataMessage

TorInterface
  conveys TorTimeData

CorrelatorControlInterface
  conveys CorrelatorControl

CorrelatorDumpInterface
  conveys CorrelatorDump

MeasurementPublicationInterface
  conveys MeasurementSatnav

StatusPublicationInterface
  conveys GnssStatus

TelemetryPublicationInterface
  conveys TelemetryProduct
```

Important interface subjects:

- Channel Manager config pipe carrying `SdrCntrlConfigMsg`.
- Channel Manager control queue carrying `ChControlMsgQueueEntry`.
- Channel Manager publication of `MeasurementSatnav`.
- Channel Manager publication of `gnss_status_t`.
- Channel Monitor pipe/event carrying `ChMonMsg`.
- Channel to Telemetry Manager nav-message callback path.
- Channel to GEnCor/Napal correlator request/control path.
- TOR event/SHM timing path.

## Behaviors

The model should capture behavior as reusable action definitions and concrete
action usages under `Behaviors`.

### StartupBehavior

Expected sequence:

```text
parse config
initialize Napal
initialize SDR dependencies
construct CC configuration
initialize Channel Controller
construct pipelines
initialize Channel Manager
initialize Channel Monitor
start worker threads
enter daemon loop
```

### OneKhzEpochBehavior

Expected sequence:

```text
wait for TOR event
read receiver time
fan out pending channel control messages
run manager maintenance
generate measurements and status
post per-channel process events
wait for channel completion
drain config pipe
update diagnostics
```

### ChannelLifecycleBehavior

Expected lifecycle states:

```text
Unassigned
Assigned
Acquiring
Handover
Tracking
Measuring
Released
Error
```

Initial mapping to existing status names:

```text
CHANNEL_NEEDS_ASSIGN     -> Unassigned
CHANNEL_STATUS_ACQUIRING -> Acquiring
CHANNEL_STATUS_HANDOVER  -> Handover
CHANNEL_STATUS_TRACKING  -> Tracking
CHANNEL_STATUS_MEASURING -> Measuring
CHANNEL_STATUS_RELEASED  -> Released
CHANNEL_STATUS_ERROR     -> Error
CHANNEL_STATUS_ACQFAIL   -> Error
CHANNEL_STATUS_TRKFAIL   -> Error
```

### HotstartBehavior

Expected properties:

- Strict channel assignment when hotstart ranking is unavailable.
- VxWorks TOR sync requirement before assignment.
- Minimum assignment pacing of 10 ms in hotstart mode.
- Maximum concurrent acquisition load threshold.
- Optional MoPD delay compensation.
- 1 ms ToR shift in navigation pseudorange path under
  `HOTSTART_CHANNELS_ONLY`.

### CorrelatorControlBehavior

Expected properties:

- Control values are staged before upload.
- Hardware applies staged values after the GEnCor upload/apply cadence.
- Control response has a two-epoch latency model.
- `Correlator_TrackInit` freshness depends on `ref_block_count`.

## Configurations

The model should represent build/runtime configurations as first-class model
content.

```text
LinuxHostDebug
  targetPlatform = "linux-x86_64"
  vxWorksTarget = false
  testBuildEnabled = configurable

VxWorksTarget
  targetPlatform = "vxworks"
  vxWorksTarget = true
  napalDriver = "vxBus"

MoPDHotstartChannelsOnly
  MOPD = TRUE
  HOTSTART_CHANNELS_ONLY = TRUE
  MOPD_DELAY = configurable

TestHarness
  testExecutable = "cc-test"
  nonRealTimeMode = true

ModelsAnalysisWorkbench
  sourcePath = "models/"
  analysisBackend = "python"
```

Important build/configuration knobs:

- `SERGEANT_BUILD_EXE`
- `ENABLE_DEBUG_PRINTS`
- `DETAILED_LOGGING`
- `TEST_BUILD`
- `MOPD`
- `HOTSTART_CHANNELS_ONLY`
- `MOPD_DELAY`
- `VX_TARGET_TYPE`

## Requirements

Requirements should be organized by runtime concern and should use components,
interfaces, behaviors, or configurations as subjects.

Initial requirements:

```text
OneKhzEpochCadenceRequired
ChannelAssignmentPolicyRequired
MeasurementPublicationRequired
GnssStatusPublicationRequired
TelemetryForwardingRequired
CorrelatorControlLatencyBounded
HotstartAssignmentSafetyRequired
MoPDHandoverSynchronizationRequired
ConfigurationProfileTraceRequired
TestEvidenceRequired
AnalysisEvidenceRequired
```

Example requirement intent:

```text
OneKhzEpochCadenceRequired
  subject: ChannelManager
  constraint: manager epoch behavior is synchronized to TOR-driven 1 ms cadence.

MeasurementPublicationRequired
  subject: ChannelManager
  constraint: valid channels contribute to MeasurementSatnav output with
              receiver-time aligned pseudorange and related observables.

CorrelatorControlLatencyBounded
  subject: SdrChannel to GEnCor control path
  constraint: staged control values have a documented and verified epoch
              latency model.

HotstartAssignmentSafetyRequired
  subject: ChannelAssigner
  constraint: hotstart-only mode does not assign channels without required SV
              ranking and timing readiness.
```

## Analysis Cases

Analysis cases should connect the SysML v2 model to existing Python model code,
developer docs, and generated analysis artifacts.

Required analysis cases:

```text
OneKhzTimingAnalysis
ChannelFanoutFanInAnalysis
PseudorangeComputationAnalysis
CodePhaseProxyAnalysis
CorrelatorControlLatencyAnalysis
GEnCorPipelineLagAnalysis
MoPDDelayCompensationAnalysis
ResourceContentionAnalysis
InterfaceCompletenessAnalysis
RequirementTraceCompletenessAnalysis
```

Candidate external execution backends:

```text
models/gnss/navigation/*
models/gnss/receiver/*
models/algorithms/gnss_pseudorange_workbench.py
models/algorithms/gnss_receiver_analysis_workbench.py
models/algorithms/gnss_flanking_replica_workbench.py
models/algorithms/gnss_correlator_workbench.py
models/carrier/carrier_loop_experiment.py
scripts/analysis/*
```

Each analysis case should have:

- A subject, usually a configured component, interface, behavior, or test
  scenario.
- Explicit model inputs and assumptions.
- A structured output artifact.
- Trace links to requirements and verification cases.

## Verification Cases

Verification cases should consume tests, harness runs, analysis outputs, docs
validation, or integration evidence and return a verdict.

Required verification cases:

```text
VerifyOneKhzEpochCadence
VerifyChannelLifecycleTransitions
VerifyHotstartAssignmentSafety
VerifyMeasurementPublication
VerifyTelemetryForwarding
VerifyCorrelatorControlLatency
VerifyMoPDHotstartIntegration
VerifyInterfaceCompleteness
VerifyRequirementTraceCompleteness
VerifyModelEvidenceExists
```

Candidate evidence sources:

```text
tests/ChannelManager/*
tests/Channel/*
tests/GEnCor/*
tests/MoPD/*
tests/test_utils/*
docs/developer/4_testing/**
docs/developer/5_integration/**
docs/developer/1.3_analysis/**
models/tests/**
build/*/tests
site/analysis/*
```

Each verification case should link to:

- The requirement being verified.
- The architecture element, behavior, or configuration used as the subject.
- The test, analysis, or inspection method.
- The evidence artifact.
- The verdict: `pass`, `fail`, `inconclusive`, or `error`.

## Transformation Pipeline

The first implementation should be extraction and trace generation, not model
round-trip editing.

Recommended pipeline:

```text
Sergeant cc source/docs/tests
  -> inventory extraction
  -> normalized model input JSON
  -> SysML v2 textual skeleton
  -> SysON/Flexo import
  -> generated views and trace matrices
```

Model-to-analysis path:

```text
SysML v2 configured analysis case
  -> Python analysis input
  -> models/ or scripts/ execution
  -> structured result JSON
  -> SysML analysis result / evidence link
  -> verification case verdict
```

Recommended source extractors:

- CMake target extractor for build profiles and deliverables.
- Docs frontmatter extractor for requirements, designs, testing, plans, and
  evidence.
- Module inventory extractor for `docs/developer/3_modules/**`.
- Test inventory extractor for `tests/**` and `models/tests/**`.
- Analysis inventory extractor for `models/**` and `docs/developer/1.3_analysis/**`.

## Traceability Strategy

The model should preserve the layered traceability semantics already identified
in the Sergeant requirements traceability work:

```text
source/customer requirement
  -> repo system requirement
  -> logical component
  -> implementation module
  -> build artifact or runtime configuration
  -> analysis case or verification case
  -> evidence artifact
```

Recommended relation semantics:

- `derives_from`
- `refines`
- `allocated_to`
- `satisfied_by`
- `implemented_by`
- `realized_by`
- `verified_by`
- `validated_by`
- `evidenced_by`

## Initial Review Views

The model should support these review views:

- Channel Controller component structure.
- Runtime module dependency view.
- 1 kHz epoch sequence view.
- Channel lifecycle state view.
- Hotstart/MoPD configuration view.
- IPC surface and message catalog.
- Measurement generation trace view.
- Telemetry publication trace view.
- Requirement to module trace.
- Requirement to test/evidence trace.
- Analysis case to Python backend trace.
- Failed or missing verification evidence view.

## Open Design Decisions

- Whether the first textual SysML v2 artifact should live in this MBSE repo or
  under `~/workspace/sergeant/designs/pgm/comp/cc/models`.
- Whether existing PlantUML diagrams should be linked as evidence only or used
  to generate initial SysML v2 view definitions.
- Whether docs frontmatter should become the primary source for stable model
  element IDs.
- Whether C structs such as `SdrChannel`, `ChannelManager`, and `Pipeline`
  should be represented as detailed SysML attribute structures or only as
  implementation references on higher-level parts.
- Which configuration should be modeled first: `LinuxHostDebug`,
  `VxWorksTarget`, or `MoPDHotstartChannelsOnly`.
- Whether verification results should be imported into Flexo/SysML v2 or kept as
  external evidence files linked from verification cases.
