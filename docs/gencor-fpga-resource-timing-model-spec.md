# GEnCor FPGA Resource and Timing SysML v2 Model Specification

This document specifies a SysML v2 model for the GEnCor FPGA/IP engine located
at:

```text
/home/cosgroma/workspace/sergeant/engines/gencor
```

The model is intended to support architecture trade studies, utilization
rollups, power rollups, sample-rate feasibility, memory/bus pressure analysis,
and timing-closure verification for FPGA targets such as Zynq-7000 and Zynq
UltraScale+.

The model should not replace Vivado, GHDL, or the checked-in design documents.
It should organize the design configuration, architecture, analysis cases, and
evidence so that different target architectures and operating points can be
compared with traceable pass/fail criteria.

## Goals

- Represent GEnCor as a configurable FPGA IP component.
- Capture the IP configuration surface exposed by `component.xml`,
  `hdl/gencor.vhd`, `gencor_generics.tcl`, and build configuration files.
- Support target-specific configurations for Zynq-7000 and Zynq UltraScale+.
- Compare core clock, AXI clock, packet clock, support clock, and sample-rate
  operating points.
- Roll up estimated and reported LUT, FF, BRAM, URAM, DSP, and memory/FIFO
  usage by architectural subsystem.
- Roll up static and dynamic power by target, clock domain, IP block, and
  resource type.
- Capture timing-closure requirements and measured timing evidence from FPGA
  implementation reports.
- Capture sample-rate feasibility and packet/bus throughput constraints.
- Trace each analysis result to the configuration, generated tool run, report,
  testbench, and source artifact that produced it.

## Non-Goals

- This model will not perform FPGA synthesis, implementation, static timing
  analysis, or power estimation internally.
- This model will not be a line-by-line translation of VHDL into SysML v2.
- This model will not replace GHDL functional verification.
- This model will not infer timing closure from compact functional testbenches.
- This model will not treat estimates as final verification evidence when
  Vivado reports or hardware measurements are required.

## Recommended Separation

The model should be separated into four primary concerns:

```text
configuration model
  -> architecture model
  -> analysis model
  -> evidence model
```

This separation is deliberate. Configuration variants define what will be built.
The architecture model defines what the design contains. Analysis cases define
what must be calculated or checked. Evidence records bind the result back to
tool reports, simulations, hardware measurements, and source artifacts.

## Source References

Primary source tree:

```text
/home/cosgroma/workspace/sergeant/engines/gencor
```

Key local references:

- `README.md`
- `config/config.mk`
- `pcores/gencor/component.xml`
- `pcores/gencor/gencor_generics.tcl`
- `pcores/gencor/hdl/gencor.vhd`
- `pcores/gencor/hdl/core/Core.vhd`
- `pcores/gencor/hdl/packages/GEnCor_Pack.vhd`
- `pcores/gencor/Makefile`
- `pcores/gencor/docs/reference/testbench-timing-modes.md`
- `pcores/gencor/docs/reference/codegen-delay-correlation-contract.md`
- `pcores/gencor/docs/reference/memory-code-software-contract-and-risks.md`
- `pcores/gencor/docs/designs/sample-simulation/sample-stimulus-contract.md`
- `pcores/gencor/docs/guides/pktio-validation-bench.md`
- `pcores/gencor/docs/waveforms/index.md`
- `pcores/gencor/docs/schematics/index.md`
- `docs/src/model/modules/component_xml_top_level.yaml`
- `docs/src/sections/components/top/component_xml_top_level_alignment.md`

Related local MBSE references:

- `docs/cc-channel-controller-model-spec.md`
- `docs/rf-to-digital-signal-chain-model-spec.md`
- `docs/sysml-v2-transformation-pipeline-design.md`
- `docs/sysml-v2-verification-model-setup.md`

## Source-Derived Facts

The initial model can be seeded from existing repository metadata.

| Source | Extracted model content |
| --- | --- |
| `component.xml` | IP identity, VLNV, supported FPGA families, bus interfaces, clocks, resets, interrupt, model parameters, filesets |
| `hdl/gencor.vhd` | Top-level entity, generic defaults, ports, engine parameter schema, clock and interface declarations |
| `gencor_generics.tcl` | Vivado preset values and intended configurable IP defaults |
| `config/config.mk` | Build-time defaults such as `FPGA_PART`, `CLK_FREQ`, `NUM_ENGINES`, and generated CIP configuration variables |
| `GEnCor_Pack.vhd` | Code type enumeration and string-to-code-type mapping |
| `Makefile` | GHDL verification targets, testbench inventory, stimulus generation targets, waveform/schematic generation targets |
| `component_xml_top_level.yaml` | Existing derived summary of IP-XACT identity, interfaces, filesets, and top-level alignment |
| `testbench-timing-modes.md` | Classification of compact functional, hybrid, and hardware-faithful timing evidence |

The model should treat these as source artifacts, not duplicated prose. SysML
elements should carry source links and extraction timestamps so drift can be
detected.

## Model Boundary

The model covers the GEnCor FPGA/IP design as used by the Sergeant receiver
stack:

```text
host control and packetized configuration
  -> AXI-Lite and AXIS interfaces
  -> packet decode and sequence handling
  -> activation and timing control
  -> sample ingress
  -> configurable Type-2 correlator engine array
  -> code generation, NCO, delay, and accumulation
  -> packetized output and interrupt signaling
  -> optional MOPD sideband integration
  -> FPGA implementation evidence
```

The model should expose:

- Configurable IP parameter sets.
- Target architecture profiles.
- Engine topology and code-type allocation.
- Interface and clock-domain catalog.
- Resource, power, bandwidth, and timing requirements.
- Analysis case definitions.
- Evidence records from GHDL, Vivado, generated docs, and hardware runs.
- Requirement-to-analysis-to-evidence trace.

## Recommended Package Structure

```text
GEnCorFpgaResourceTimingModel
  Libraries
    FpgaTargets
    XilinxIpInterfaces
    GnssCorrelationDomain
    TimingAndClocks
    ResourceAccounting
    PowerAccounting
    VerificationEvidence
  Metadata
  Stakeholders_Concerns
    ReceiverIntegrationConcerns
    FpgaImplementationConcerns
    TimingClosureConcerns
    PowerResourceConcerns
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
    EvidenceDefinitions
  SourceArtifacts
    GEnCorRepository
    IpXactComponentXml
    VhdlTopLevel
    VivadoPresetScripts
    BuildConfiguration
    TestbenchInventory
    ExistingDerivedDocs
  ConfigurationModel
    TargetProfiles
    ClockProfiles
    SampleRateProfiles
    EngineProfiles
    InterfaceProfiles
    BuildProfiles
    TradeStudyConfigurations
  ArchitectureModel
    GEnCorIpArchitecture
    InterfaceArchitecture
    ClockAndResetArchitecture
    PacketControlArchitecture
    TimingEpochArchitecture
    CorrelatorEngineArchitecture
    CodeGenerationArchitecture
    MemoryAndFifoArchitecture
    MopdIntegrationArchitecture
  AnalysisModel
    UtilizationRollupAnalysis
    PowerRollupAnalysis
    TimingClosureAnalysis
    SampleRateFeasibilityAnalysis
    PacketThroughputAnalysis
    MemoryBusPressureAnalysis
    FifoPressureAnalysis
    ConfigurationConsistencyAnalysis
    TargetTradeStudyAnalysis
  EvidenceModel
    GhdlEvidence
    VivadoSynthesisEvidence
    VivadoImplementationEvidence
    VivadoPowerEvidence
    HardwareMeasurementEvidence
    WaveformEvidence
    SchematicEvidence
    ReportParserEvidence
  Requirements
    ResourceRequirements
    TimingClosureRequirements
    PowerRequirements
    ThroughputRequirements
    SampleRateRequirements
    InterfaceRequirements
    VerificationRequirements
  Verification
    FunctionalVerificationCases
    HardwareFaithfulTimingVerificationCases
    ImplementationVerificationCases
    ReportIngestionVerificationCases
    TraceabilityVerificationCases
  Views_Viewpoints
    ConfigurationViews
    ArchitectureViews
    ClockDomainViews
    InterfaceViews
    ResourceViews
    PowerViews
    TimingClosureViews
    TradeStudyViews
    EvidenceTraceViews
```

## Configuration Model

The configuration model defines the variables used to generate and compare
architecture instances.

### Target Profile

Each target profile should capture the FPGA family and implementation context.

```text
FpgaTargetProfile
  targetFamily: Zynq7000 | ZynqUltraScalePlus
  partNumber
  package
  speedGrade
  boardProfile
  vivadoVersion
  supportedFamilyName
  availableLUTs
  availableFFs
  availableBRAMs
  availableURAMs
  availableDSPs
  psPlPortCatalog
  ddrProfile
```

Initial target profiles:

- `Zynq7000_ZC706_xc7z045ffg900_3`
- `ZynqUltraScalePlus_Generic`
- `ZynqUltraScalePlus_NAVDC`

The checked-in `config/config.mk` currently exposes
`FPGA_PART=xc7z045ffg900-3`. The checked-in IP-XACT metadata identifies both
`zynq` and `zynquplus` as supported families. These should be modeled as
separate target profiles rather than a single generic Xilinx target.

### Clock Profile

Clock profiles should be explicit and should not rely on signal names alone.

```text
ClockProfile
  coreClockMHz
  axiLiteClockMHz
  packetInputClockMHz
  packetOutputClockMHz
  sampleInputClockMHz
  supportClockMHz
  clockDomainBindings
  derivedClockPeriodsNs
```

The VHDL top level exposes `clk_300`, `clk_100`, `s00_axi_aclk`,
`s_axis_pio_aclk`, `m_axis_pio_aclk`, and `s_axis_samples_aclk`. Testbenches
often drive several of these from a common fast clock for compact functional
verification. The model must distinguish that testbench convenience from a
hardware clocking requirement.

### Sample Rate Profile

Sample-rate profiles should capture physical signal assumptions separately from
testbench replay modes.

```text
SampleRateProfile
  sampleRateHz
  samplesPerChip
  codeRateHz
  blockDurationMs
  blockSamples
  blockSamplesM1
  replayMode: CompactFunctional | HybridFunctionalIntegration | HardwareFaithfulTiming
```

The current packetized top-level benches are primarily compact functional or
hybrid integration benches. They should not be used as direct evidence that a
configuration is feasible at a physical sample rate unless the bench is
explicitly hardware-faithful.

### Engine Profile

The GEnCor entity exposes a scalable engine schema:

```text
EngineProfile
  engineIndex
  physicalCorrelators
  virtualCorrelators
  fixedDelayEnabled
  codeType
```

The code type domain should be normalized to:

```text
CaCode
MCode
PCode
Streaming
GalE1
MemoryCode
Mopd
```

The model should preserve the source spelling where needed, but use a normalized
domain internally. `GEnCor_Pack.vhd` maps `MemoryCode` into the internal memory
code enum value.

### Configuration Normalization Rules

The model should include a configuration consistency analysis before any
trade-study results are accepted.

Known normalization checks:

- `E*_NVIRT` is the VHDL top-level generic spelling.
- Some build/preset surfaces use `E*_VIRT`; those should be normalized to
  `E*_NVIRT` before report generation.
- Boolean values such as `false`, `0`, and tool-specific string forms should be
  normalized into a single SysML boolean value.
- Code type strings should be checked against the normalized code type domain.
- `NUM_ENGINES` must not exceed the number of engine profiles provided.
- MOPD sideband width must be consistent with `NUM_MOPD_CHANNELS` and the number
  of engines using `Mopd`.

## Architecture Model

The architecture model should describe the stable IP structure and interfaces
without attempting to translate every VHDL signal.

### Core Part Definitions

```text
GEnCorIp
IpXactComponent
GEnCorTopEntity
AxiLiteConfigInterface
AxisPacketInputInterface
AxisPacketOutputInterface
AxisSampleInputInterface
ClockDomain
ResetDomain
InterruptOutput
MopdSideband
PacketDecoder
SequenceModule
PacketRegisterModule
TimerModule
ActivateModule
PreProcessor
Type2CorrelatorEngine
NcoCore
CodeGenerator
CaCodeCore
MemoryCodeCore
MPrimeCodeCore
PCodeCore
GalileoCodeCore
StreamingCodeCore
DelayCore
DelayUnit
AccumulatorCore
AccumulatorEncoder
OutputFifo
ConfigurationRom
```

### Interface Architecture

The model should import or mirror the IP-XACT interface catalog:

- `s00_axi`: AXI-Lite configuration slave.
- `s_axis_pio`: AXIS packet input slave.
- `m_axis_pio`: AXIS packet output master.
- `s_axis_samples`: AXIS sample input slave.
- Clock and reset interfaces for each AXI/AXIS interface.
- `clk_300` processing clock.
- `clk_100` support or activation timing clock.
- `IP2IF_IntrEvent` interrupt output.
- `EpochOut` exported epoch pulse.
- `MopdChip`, `MopdChipReady`, and `MopdChipRead` sideband ports.

### Engine Architecture

Each configured engine instance should bind:

```text
Type2CorrelatorEngine
  engineIndex
  codeType
  physicalCorrelators
  virtualCorrelators
  fixedDelayEnabled
  inputSampleStream
  packetControlInput
  ncoCore
  codeGenerator
  delayCore
  accumulatorBank
  packetOutputFifo
  interruptContribution
```

The model should define resource accounting at the engine level and roll those
values up to the full IP instance.

## Analysis Model

Analysis cases should have clear inputs, outputs, and evidence requirements.

### Utilization Rollup

Purpose: estimate or report resource usage for each target/configuration.

Inputs:

- Target profile.
- Engine profiles.
- IP block inventory.
- Vivado utilization report, when available.

Outputs:

```text
estimatedLUTs
estimatedFFs
estimatedBRAMs
estimatedURAMs
estimatedDSPs
reportedLUTs
reportedFFs
reportedBRAMs
reportedURAMs
reportedDSPs
utilizationPercentByResource
resourceMarginByResource
```

Rule:

```text
resourceMargin = resourceBudget - reportedUsage
resourcePass = reportedUsage <= resourceBudget
```

Estimated usage may support early trade studies. Reported usage from Vivado
should be required for implementation verification.

### Power Rollup

Purpose: compare power by target, clock profile, activity profile, and resource
composition.

Inputs:

- Target profile.
- Clock profile.
- Activity assumptions.
- Utilization results.
- Vivado power report, when available.

Outputs:

```text
estimatedStaticPowerW
estimatedDynamicPowerW
reportedStaticPowerW
reportedDynamicPowerW
reportedTotalPowerW
powerByClockDomain
powerByResourceType
thermalMargin
```

Rule:

```text
powerPass = reportedTotalPowerW <= allocatedPowerBudgetW
```

### Timing Closure

Purpose: determine whether each architecture target closes timing at the
requested clock rates.

Inputs:

- Target profile.
- Clock profile.
- Constraint set.
- Vivado timing summary.

Outputs:

```text
requiredPeriodNs
reportedWnsNs
reportedTnsNs
reportedWhsNs
reportedThsNs
reportedFmaxMHz
violatingPathCount
timingClosed
```

Rule:

```text
requiredPeriodNs = 1000.0 / coreClockMHz
timingClosed = reportedWnsNs >= 0.0 and reportedTnsNs >= 0.0
```

Timing closure must be based on implementation timing reports, not GHDL
functional testbench results.

### Sample-Rate Feasibility

Purpose: determine whether an operating point can process the sample stream
without violating epoch, FIFO, or processing-cycle constraints.

Inputs:

- Sample rate profile.
- Clock profile.
- Engine profiles.
- Timer configuration.
- Replay mode.
- Hardware-faithful timing evidence, when required.

Outputs:

```text
samplesPerBlock
cyclesPerSample
cyclesPerBlock
processingLatencyCycles
fifoDepthRequired
sampleRateFeasible
```

Rule:

```text
cyclesPerSample = coreClockHz / sampleRateHz
sampleRateFeasible = processingLatencyCycles <= cyclesPerBlock
```

The model should flag compact functional benches as insufficient evidence for
this analysis unless the question is only packet ordering or functional decode.

### Packet Throughput and Bus Pressure

Purpose: quantify packet input/output and memory pressure for each
configuration.

Inputs:

- Packet sizes by transaction type.
- Output packet count per epoch.
- Engine count.
- Correlator count.
- AXIS data width.
- DMA burst policy.
- Target memory/bus profile.

Outputs:

```text
packetInputBytesPerEpoch
packetOutputBytesPerEpoch
sampleInputBytesPerSecond
axisUtilizationPercent
averageBandwidthMBps
instantaneousBurstBandwidthMBps
burstDurationUs
busPressurePass
```

The model should preserve the distinction between sustained average bandwidth
and instantaneous burst bandwidth. Prior Channel Controller analysis showed that
the wording around bytes per millisecond can be ambiguous; this model should
make the interval and burst duration explicit.

### FIFO Pressure

Purpose: determine whether output FIFOs and memory-code FIFOs are sized for the
selected engine topology and burst behavior.

Inputs:

- XCI FIFO configuration.
- Packet output profile.
- Engine topology.
- Readout cadence.
- Burst overlap assumptions.

Outputs:

```text
fifoDepth
maxOccupancy
overflowMargin
underflowRisk
fifoPressurePass
```

### Configuration Consistency

Purpose: detect mismatches before generating tool runs or accepting evidence.

Checks:

- IP-XACT model parameters match VHDL generics.
- Top-level port names and directions match IP-XACT metadata.
- Preset TCL uses current generic names.
- Build configuration variables map to VHDL generic names.
- Code type strings are valid.
- Clock profile names bind to actual ports.
- Target family is supported by IP-XACT metadata.

Existing derived docs already report that `component.xml` and `entity gencor`
align for top-level ports and generic defaults after the 2026-04-12 refresh.
The SysML model should import that result as an evidence record and rerun the
check when source artifacts change.

## Evidence Model

The evidence model records how each result was produced.

### Evidence Types

```text
SourceEvidence
  sourcePath
  sourceKind
  extractionTimestamp
  sourceRevision
  checksum

GhdlTestEvidence
  testbenchName
  makeTarget
  stopTime
  waveFormat
  verdict
  logPath
  waveformPath
  timingMode

VivadoSynthesisEvidence
  targetProfile
  configurationProfile
  vivadoVersion
  synthRunId
  utilizationReportPath
  utilizationJsonPath

VivadoImplementationEvidence
  targetProfile
  configurationProfile
  implementationRunId
  timingSummaryPath
  routeStatusPath
  timingJsonPath

VivadoPowerEvidence
  targetProfile
  configurationProfile
  activityAssumptions
  powerReportPath
  powerJsonPath

HardwareMeasurementEvidence
  boardId
  bitstreamId
  clockProfile
  sampleRateProfile
  measurementTool
  measurementLogPath
  measuredMetrics

GeneratedDocEvidence
  waveformSvgPath
  schematicSvgPath
  sourceSpecPath
  generationCommand
```

### Evidence Acceptance Rules

- Functional correctness may use GHDL evidence.
- Interface metadata may use IP-XACT and VHDL extraction evidence.
- Timing closure requires Vivado implementation timing evidence.
- Utilization verification requires Vivado synthesis or implementation
  utilization evidence.
- Power verification requires Vivado power evidence or hardware measurement
  evidence.
- Physical sample-rate feasibility requires hardware-faithful timing simulation
  or hardware measurement evidence.
- Compact functional testbenches may verify packet contracts, ordering,
  register effects, and scoreable correlation behavior, but not physical
  sample-rate timing.

## Transformation and Execution Pipeline

The model should support a repeatable transformation pipeline:

```text
SysML configuration instance
  -> normalized GEnCor configuration JSON
  -> generated Vivado TCL/IP parameter script
  -> generated constraints and clock definitions
  -> Vivado synth/implement/report flow
  -> report parser output JSON
  -> SysML analysis result objects
  -> verification case verdicts
  -> trade-study views
```

The pipeline should also support GHDL evidence:

```text
SysML verification case
  -> make target and TB arguments
  -> GHDL run
  -> log/waveform artifacts
  -> parsed verdict
  -> SysML evidence record
```

## Report Parser Contract

The SysML model should ingest normalized JSON rather than parsing raw report
text directly in model logic.

Example utilization result:

```json
{
  "configurationId": "gencor-zynq7000-1eng-256corr-100mhz",
  "target": "xc7z045ffg900-3",
  "tool": "Vivado",
  "toolVersion": "TBD",
  "utilization": {
    "lut": { "used": 0, "available": 0 },
    "ff": { "used": 0, "available": 0 },
    "bram": { "used": 0, "available": 0 },
    "uram": { "used": 0, "available": 0 },
    "dsp": { "used": 0, "available": 0 }
  }
}
```

Example timing result:

```json
{
  "configurationId": "gencor-zynquplus-4eng-256corr-200mhz",
  "target": "zynquplus",
  "clock": "core",
  "requestedMHz": 200.0,
  "requiredPeriodNs": 5.0,
  "wnsNs": 0.0,
  "tnsNs": 0.0,
  "whsNs": 0.0,
  "thsNs": 0.0,
  "violatingPaths": 0
}
```

Placeholder zeros should not be accepted as verification data. The model should
require an evidence status such as `estimated`, `reported`, `measured`, or
`unknown`.

## Trade Study Configurations

Initial configurations should include:

```text
GEnCor_Zynq7000_1Engine_256Corr_100MHz
GEnCor_Zynq7000_1Engine_256Corr_150MHz
GEnCor_Zynq7000_4Engine_256Corr_100MHz
GEnCor_ZynqUltraScalePlus_1Engine_256Corr_200MHz
GEnCor_ZynqUltraScalePlus_4Engine_256Corr_200MHz
GEnCor_ZynqUltraScalePlus_MopdMemoryCodeMixed_200MHz
```

Each trade-study configuration should bind:

- Target profile.
- Clock profile.
- Sample-rate profile.
- Engine profile list.
- Interface width profile.
- FIFO/memory profile.
- Requirement set.
- Required evidence set.

## Requirements

The following requirement groups should be modeled.

### Resource Requirements

```text
REQ-GENCOR-RESOURCE-001
  The configured GEnCor IP shall fit within the allocated LUT, FF, BRAM, URAM,
  and DSP budgets for the selected FPGA target.

REQ-GENCOR-RESOURCE-002
  The configured GEnCor IP shall maintain configurable resource margin for
  integration with the rest of the FPGA design.
```

### Timing Requirements

```text
REQ-GENCOR-TIMING-001
  The configured GEnCor IP shall close timing at the selected core clock rate.

REQ-GENCOR-TIMING-002
  The configured GEnCor IP shall close timing for each declared AXI, AXIS,
  support, and sample input clock domain used by the target integration.
```

### Sample-Rate Requirements

```text
REQ-GENCOR-SAMPLERATE-001
  The configured GEnCor IP shall process the selected sample rate without
  violating epoch, sample-ingress, FIFO, or output-readout constraints.
```

### Power Requirements

```text
REQ-GENCOR-POWER-001
  The configured GEnCor IP shall remain within the allocated static, dynamic,
  and total power budgets for the selected target and activity profile.
```

### Interface Requirements

```text
REQ-GENCOR-IF-001
  The SysML interface model shall match the IP-XACT bus interface and top-level
  VHDL port declarations for the selected GEnCor source revision.
```

### Evidence Requirements

```text
REQ-GENCOR-EVIDENCE-001
  Each implementation verification result shall trace to a source revision,
  target profile, configuration profile, tool run, report artifact, parser
  version, and SysML analysis result.
```

## Views

The model should provide these stakeholder views:

- Target comparison matrix.
- Configuration parameter table.
- Engine topology view.
- IP-XACT interface view.
- Clock-domain view.
- Resource utilization rollup.
- Power rollup.
- Timing closure summary.
- Sample-rate feasibility matrix.
- FIFO and packet burst pressure view.
- Evidence trace view.
- Requirement verification dashboard.

## Open Questions

- Which Vivado version should be authoritative for Zynq-7000 and Zynq
  UltraScale+ comparisons?
- Which UltraScale+ part number and board profile should be treated as the
  primary target?
- What integration-level resource budgets should be allocated to GEnCor for
  each target?
- What power budget and activity profile should be used for early trade
  studies?
- Which clock names map to physical clocks in each board-level integration?
- Which testbench, if any, should become the hardware-faithful sample-rate
  timing evidence source?
- Should the Vivado report parsers live in this MBSE repo, the GEnCor repo, or
  a shared tooling repo?

## Initial Implementation Steps

1. Generate a source extraction script for `component.xml`, `gencor.vhd`,
   `gencor_generics.tcl`, `config.mk`, and the GHDL Makefile.
2. Emit normalized configuration JSON for target profiles, engine profiles,
   interfaces, and clocks.
3. Create SysML v2 package skeletons for configuration, architecture, analysis,
   and evidence.
4. Add configuration consistency checks for generic spelling, code type values,
   interface alignment, and target-family support.
5. Define Vivado TCL generation for one Zynq-7000 and one Zynq UltraScale+
   baseline configuration.
6. Define parsers for utilization, timing summary, and power reports.
7. Import parsed results as SysML analysis result and evidence records.
8. Build comparison views for utilization, power, timing closure, and
   sample-rate feasibility.
