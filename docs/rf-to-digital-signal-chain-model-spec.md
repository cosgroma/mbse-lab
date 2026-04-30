# RF to Digital Signal Chain SysML v2 Model Specification

This document specifies the intended SysML v2 model for an RF front end and
digital signal processing chain. The model is intended to support architecture
definition, analog/digital domain handoff, delay analysis, noise figure
analysis, digital filter analysis, requirements traceability, and verification.

The model should be useful as both:

- A semantic MBSE model that captures the RF/analog/digital signal chain,
  interfaces, parameters, assumptions, requirements, and verification trace.
- An executable or tool-assisted analysis model that can evaluate delay, noise
  figure, and digital filter metrics through SysML v2 calculations, analysis
  cases, or delegated external computation.

## Goals

- Represent the signal path from antenna input through RF/IF processing, ADC
  conversion, and digital filtering.
- Separate analog, sampled, and digital baseband domains while explicitly
  modeling the conversion boundary.
- Compute RF group delay rollups, cascaded noise figure, ADC-related metrics,
  FIR filter delay, and end-to-end latency.
- Trace delay, noise figure, and filtering requirements to architecture
  elements, analysis cases, and verification cases.
- Support configured variants such as nominal chain, worst-case chain, lab test
  chain, and as-implemented FPGA chain.
- Preserve enough model structure to execute simple analyses directly and
  delegate higher-fidelity RF/DSP calculations to external tools.

## Non-Goals

- This model will not replace RF circuit simulation, EM simulation, MATLAB/Python
  DSP analysis, HDL simulation, FPGA timing closure, or lab measurement.
- This model will not assume every SysML v2 tool can execute all calculations
  natively.
- This model will not initially model complete waveform behavior, nonlinear RF
  effects, clock phase noise, or fixed-point HDL implementation details beyond
  the attributes needed for delay, noise figure, and FIR filter analysis.

## References

- OMG SysML v2 specification: <https://www.omg.org/spec/SysML>
- OMG SysML v2 Language specification PDF:
  <https://www.omg.org/spec/SysML/2.0/Language/PDF>
- OMG KerML specification: <https://www.omg.org/spec/KerML/1.0>
- SysML v2 release repository and examples:
  <https://github.com/Systems-Modeling/SysML-v2-Release>
- OMG Software Radio Components / SDRP specification:
  <https://www.omg.org/spec/SDRP/1.0>
- OMG SDRP Communication Channel and Equipment volume:
  <https://www.omg.org/spec/SDRP/1.0/Vol1/PDF>
- OMG SDRP Component Framework volume:
  <https://www.omg.org/spec/SDRP/1.0/Vol3/PDF>
- Local verification model setup guide:
  `docs/sysml-v2-verification-model-setup.md`
- Local RF link budget model spec:
  `docs/rf-link-budget-model-spec.md`

## MDA Methodology Alignment

This model should use Model Driven Architecture concepts as a layering pattern:

```text
CIM-like layer
  Operational receive-chain need, signal processing mission objective, latency
  concern, sensitivity/noise concern, filtering concern, and stakeholder
  verification objective.

PIM-like layer
  Abstract SignalChain, RFAnalogChain, ConversionBoundary,
  DigitalProcessingChain, signal item types, delay/noise/filter requirements,
  equations, analysis cases, and verification intent independent of selected
  RF parts, ADCs, FPGAs, or tools.

PSM-like layer
  Specific RF components, ADC, clock source, FPGA, sample rates, FIR
  coefficients, HDL implementation, measured response data, lab test setup, and
  selected analysis or simulation tools.

Generated and evidence artifacts
  RF simulation inputs, measured S-parameter or response files, MATLAB/Python
  DSP outputs, FIR coefficient files, HDL test results, timing reports, lab
  measurements, and verification evidence records.
```

The model should preserve traceability across these layers so a signal-chain
performance requirement can be followed to the logical chain model, the concrete
implementation, the analysis execution, and the verification evidence.

## Model Boundary

The model covers the receive signal chain from RF input to filtered digital
baseband output:

```text
antenna input
  -> RF protection / limiter
  -> RF filter
  -> low-noise amplifier
  -> mixer / downconverter
  -> IF filter and gain chain
  -> analog-to-digital converter
  -> digital downconverter
  -> FIR filter / decimator
  -> digital baseband output
```

The model should expose the following primary outputs:

- Total RF/analog group delay, `totalAnalogGroupDelay_ns`.
- Analog group delay variation, `analogGroupDelayVariation_ns`.
- Cascaded noise figure, `cascadeNoiseFigure_dB`.
- Cascaded gain, `cascadeGain_dB`.
- Output noise density, `outputNoiseDensity_dBmPerHz`.
- ADC quantization noise, `quantizationNoise_dB`.
- ADC aperture jitter SNR, `jitterSnr_dB`.
- FIR group delay, `firGroupDelay_samples` and `firGroupDelay_s`.
- Digital processing latency, `digitalLatency_samples` and `digitalLatency_s`.
- End-to-end latency, `endToEndLatency_s`.
- FIR passband ripple, `passbandRipple_dB`.
- FIR stopband attenuation, `stopbandAttenuation_dB`.
- Requirement verdict or analysis status.

## Recommended Package Structure

```text
RFToDigitalSignalChainModel
  Libraries
    Units
    Math
    SignalProcessing
    SoftwareRadioDomain
  Metadata
  Stakeholders_Concerns
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
    DelayRequirements
    NoiseFigureRequirements
    ConversionRequirements
    DigitalFilterRequirements
    EndToEndSignalChainRequirements
  Architecture
    RFAnalogChain
    ConversionBoundary
    DigitalProcessingChain
    ClockAndTimingArchitecture
    TestEquipment
  Configurations
    NominalSignalChain
    WorstCaseSignalChain
    LabTestSignalChain
    AsImplementedSignalChain
  Analysis
    DelayAnalysisCases
    NoiseFigureAnalysisCases
    ConversionAnalysisCases
    DigitalFilterAnalysisCases
    EndToEndAnalysisCases
  Verification
    VerificationCases
    VerificationProcedures
    VerificationResults
  Views_Viewpoints
    SignalChainViews
    DomainBoundaryViews
    RequirementTraceViews
    VerificationTraceViews
```

## Domain Strategy

The model should explicitly separate the analog and digital domains. The ADC is
the primary semantic boundary where continuous-time RF/IF signals become sampled
numeric signals.

```text
AnalogRFSignal
  -> AnalogIFSignal
  -> SampledSignal
  -> DigitalBasebandSignal
```

Recommended rules:

- Use analog signal item types before the ADC.
- Use sampled signal item types at the ADC output and through rate-changing DSP
  blocks.
- Use digital baseband signal item types after downconversion and filtering.
- Model the ADC as a part with both analog and sampled-signal ports.
- Keep units explicit at the boundary: volts, dBm, Hz, samples, seconds, bits,
  full-scale range, and sample rate.
- Represent high-fidelity frequency response, S-parameters, and filter
  coefficients as linked artifacts or tables rather than forcing all curve data
  into scalar attributes.

## SWRadio / SDRP Alignment

The OMG Software Radio Components specification, also known as SDRP, is a UML
profile-era specification for software radio components. It should not be
applied directly as a SysML v2 profile. Instead, this model should reuse SDRP as
a domain reference and translate useful concepts into native SysML v2
definitions.

SDRP is useful for this model because it already identifies concepts for
communication channels, RF-side equipment, subscriber-side I/O, analog ports,
digital ports, physical-layer facilities, radio control facilities, waveform
deployment, and reusable software radio components.

Recommended concept mapping:

```text
SDRP concept                         SysML v2 model concept
LogicalCommunicationChannel          CommunicationChannel or SignalChain
LogicalPhysicalChannel               RFAnalogChain plus ConversionBoundary
LogicalProcessingChannel             DigitalProcessingChain
LogicalIOChannel                     Baseband, host, network, or user I/O
AnalogInputPort                      analog input port typed by AnalogRFSignal or AnalogIFSignal
AnalogOutputPort                     analog output port typed by AnalogRFSignal or AnalogIFSignal
DigitalPort                          digital port typed by SampledSignal or DigitalBasebandSignal
Amplifier                            LowNoiseAmplifier or RFStage specialization
Antenna                              Antenna part definition
Converter                            ADC, DAC, or frequency conversion part definition
Filter                               RF_Filter, IF_Filter, or FIRFilter
FrequencyConverter                   Mixer or DigitalDownconverter
RadioManager                         RadioManager or SignalChainController
ChannelManager                       CommunicationChannelController
Waveform deployment                  Allocation of waveform functions to platform resources
```

The model should include a reusable `SoftwareRadioDomain` library package when
radio-domain reuse matters:

```text
Libraries
  SoftwareRadioDomain
    ItemDefinitions
      AnalogRFSignal
      AnalogIFSignal
      SampledSignal
      DigitalBasebandSignal
      ControlMessage
      WaveformData
    PortDefinitions
      AnalogInputPort
      AnalogOutputPort
      DigitalInputPort
      DigitalOutputPort
      ControlPort
    PartDefinitions
      CommunicationChannel
      LogicalPhysicalChannel
      LogicalProcessingChannel
      LogicalIOChannel
      RadioSet
      RadioSystem
      RadioManager
      ChannelManager
      Antenna
      Amplifier
      Filter
      Converter
      FrequencyConverter
      WaveformComponent
```

Port compatibility rules should follow SDRP intent while using SysML v2 typing:

- Analog output ports connect to analog input ports with compatible signal item
  types.
- Digital output ports connect to digital input ports with compatible sample
  rate, word length, and throughput assumptions.
- Control ports are separated from signal-flow ports.
- Conversion elements such as ADCs, DACs, mixers, and digital downconverters
  explicitly transform signal item types.
- Reconfigurable or dynamic channels are represented by configurations, modes,
  states, or control actions rather than hidden tool state.

SDRP-aligned attributes to preserve where relevant:

- `gain_dB`
- `noiseFigure_dB`
- `insertionLoss_dB`
- `freqResponse`
- `tunedFrequency_Hz`
- `sampleRate_Hz`
- `sampleSize_bits`
- `quantizationNoise_dB`
- `maxThroughput`
- `inputImpedance_ohm`
- `outputImpedance_ohm`
- `inputVSWR`
- `outputVSWR`
- `radiationPattern`
- `polarization`

This alignment should be treated as a modeling aid, not a conformance claim. A
SysML v2 model based on these definitions is not automatically conformant to
SDRP, because SDRP conformance is defined for UML profile and PIM/PSM usage.

## Core Item Definitions

The model should define reusable signal item types under
`Definitions/ItemDefinitions`.

```text
AnalogRFSignal
AnalogIFSignal
SampledSignal
DigitalBasebandSignal
ClockSignal
LocalOscillatorSignal
FilterCoefficientSet
FrequencyResponse
GroupDelayResponse
NoiseFigureResponse
```

### AnalogRFSignal

Expected attributes:

- `carrierFrequency_Hz`
- `bandwidth_Hz`
- `power_dBm`
- `noiseDensity_dBmPerHz`
- `snr_dB`
- `phaseNoise`
- `groupDelay_ns`

### AnalogIFSignal

Expected attributes:

- `centerFrequency_Hz`
- `bandwidth_Hz`
- `power_dBm`
- `noiseDensity_dBmPerHz`
- `snr_dB`
- `groupDelay_ns`

### SampledSignal

Expected attributes:

- `sampleRate_Hz`
- `wordLength_bits`
- `fullScaleVoltage_V`
- `quantizationNoise_dB`
- `latency_samples`
- `latency_s`

### DigitalBasebandSignal

Expected attributes:

- `sampleRate_Hz`
- `symbolRate_sps`
- `wordLength_bits`
- `modulation`
- `ebNo_dB`
- `latency_samples`
- `latency_s`

### Response Artifacts

Frequency-dependent properties should be modeled as response artifacts when
needed:

```text
GroupDelayResponse
  frequency_Hz[]
  groupDelay_ns[]
  source
  confidence

NoiseFigureResponse
  frequency_Hz[]
  noiseFigure_dB[]
  source
  confidence

FrequencyResponse
  frequency_Hz[]
  magnitude_dB[]
  phase_deg[]
  source
  confidence
```

## Core Part Definitions

The model should define reusable chain element types under
`Definitions/PartDefinitions`.

```text
SignalChain
RFStage
PassiveRFStage
Limiter
RF_Filter
LowNoiseAmplifier
Mixer
LocalOscillator
IF_Filter
VariableGainAmplifier
ADC
DigitalDownconverter
FIRFilter
Decimator
DigitalProcessor
ClockSource
TestInstrument
```

### SignalChain

`SignalChain` is the primary subject for end-to-end analysis and verification.

Expected owned parts:

- `rfInputProtection : Limiter`
- `rfFilter : RF_Filter`
- `lna : LowNoiseAmplifier`
- `mixer : Mixer`
- `localOscillator : LocalOscillator`
- `ifFilter : IF_Filter`
- `adc : ADC`
- `digitalDownconverter : DigitalDownconverter`
- `firFilter : FIRFilter`
- `decimator : Decimator`
- `digitalProcessor : DigitalProcessor`

Expected attributes:

- `inputFrequency_Hz`
- `signalBandwidth_Hz`
- `sampleRate_Hz`
- `outputSampleRate_Hz`
- `totalAnalogGroupDelay_ns`
- `cascadeNoiseFigure_dB`
- `digitalLatency_samples`
- `endToEndLatency_s`

### RFStage

Expected attributes:

- `gain_dB`
- `noiseFigure_dB`
- `insertionLoss_dB`
- `groupDelay_ns`
- `groupDelayVariation_ns`
- `inputP1dB_dBm`
- `outputP1dB_dBm`
- `inputFrequency_Hz`
- `outputFrequency_Hz`
- `bandwidth_Hz`
- `temperature_K`

### PassiveRFStage

Expected attributes:

- `insertionLoss_dB`
- `equivalentNoiseFigure_dB`
- `groupDelay_ns`
- `groupDelayVariation_ns`
- `temperature_K`

For a passive lossy stage near reference temperature, initial analysis may use:

```text
equivalentNoiseFigure_dB ~= insertionLoss_dB
gain_dB = -insertionLoss_dB
```

### ADC

Expected attributes:

- `sampleRate_Hz`
- `resolution_bits`
- `fullScaleVoltage_V`
- `inputBandwidth_Hz`
- `apertureJitter_s`
- `snr_dB`
- `enob_bits`
- `latency_samples`
- `latency_s`
- `quantizationNoise_dB`

### FIRFilter

Expected attributes:

- `sampleRate_Hz`
- `inputWordLength_bits`
- `coefficientWordLength_bits`
- `outputWordLength_bits`
- `numberOfTaps`
- `latency_samples`
- `groupDelay_samples`
- `groupDelay_s`
- `passbandRipple_dB`
- `stopbandAttenuation_dB`
- `transitionBandwidth_Hz`
- `decimationFactor`
- `coefficientSet`

## Ports and Interfaces

The architecture should include domain-specific ports when the tool supports
them well:

```text
analogRfIn
analogRfOut
analogIfIn
analogIfOut
sampledSignalOut
digitalBasebandIn
digitalBasebandOut
clockIn
loIn
controlIn
```

Recommended interface pairings:

- RF stages accept and emit `AnalogRFSignal` or `AnalogIFSignal`.
- The ADC accepts `AnalogIFSignal` and emits `SampledSignal`.
- Digital processing blocks accept and emit `SampledSignal` or
  `DigitalBasebandSignal`.
- Clocked digital blocks depend on `ClockSignal`.
- Mixer stages depend on `LocalOscillatorSignal`.

## Units and Quantities

The model should use explicit quantity definitions or imported unit libraries
for all engineering values. At minimum, the model should distinguish:

- Frequency in `Hz`, `MHz`, and `GHz`.
- Bandwidth and sample rate in `Hz`.
- Power in `dBm`, `dBW`, watts, and volts where applicable.
- Gain, loss, SNR, and noise figure in `dB`.
- Noise density in `dBm/Hz`.
- Delay and latency in `ns`, `s`, and samples.
- Phase in degrees or radians.
- Temperature in `K`.
- Resolution and word length in bits.

Avoid unqualified `Real` attributes in production model content where a unitful
quantity is available in the target tool.

## Calculation Definitions

The model should define reusable `calc def` elements under
`Definitions/CalculationDefinitions`.

Required calculations:

```text
CalculateAnalogGroupDelayRollup
CalculateAnalogDelayVariation
CalculateNoiseFigureCascade
CalculateCascadeGain
CalculateAdcQuantizationNoise
CalculateAdcJitterSnr
CalculateFirGroupDelay
CalculateDigitalLatency
CalculateEndToEndLatency
CalculateFilterRequirementMargin
```

### Baseline Equations

The initial model should support simple deterministic analyses.

Analog delay:

```text
totalAnalogGroupDelay_ns =
  sum(stage.groupDelay_ns)

analogGroupDelayVariation_ns =
  max(stage.groupDelayVariation_ns)
```

Cascaded noise figure using Friis:

```text
F_i = 10 ^ (noiseFigure_i_dB / 10)
G_i = 10 ^ (gain_i_dB / 10)

F_total =
  F_1
  + (F_2 - 1) / G_1
  + (F_3 - 1) / (G_1 * G_2)
  + ...
  + (F_n - 1) / (G_1 * G_2 * ... * G_(n-1))

cascadeNoiseFigure_dB =
  10 * log10(F_total)

cascadeGain_dB =
  sum(stage.gain_dB)
```

ADC quantization and jitter approximations:

```text
idealAdcSnr_dB =
  6.02 * resolution_bits + 1.76

jitterSnr_dB =
  -20 * log10(2 * pi * inputFrequency_Hz * apertureJitter_s)

quantizationNoise_dB =
  -idealAdcSnr_dB
```

Linear-phase FIR delay:

```text
firGroupDelay_samples =
  (numberOfTaps - 1) / 2

firGroupDelay_s =
  firGroupDelay_samples / sampleRate_Hz
```

End-to-end latency:

```text
digitalLatency_s =
  digitalLatency_samples / sampleRate_Hz

endToEndLatency_s =
  totalAnalogGroupDelay_ns * 1e-9
  + adc.latency_s
  + digitalLatency_s
```

### SysML v2 Calculation Sketch

The exact syntax may need adjustment for the target tool parser, but the model
intent should be captured as reusable calculations:

```sysml
calc def CalculateFirGroupDelay {
  in numberOfTaps : Real;
  in sampleRate_Hz : Real;
  return groupDelay_samples : Real;
  return groupDelay_s : Real;
}

calc def CalculateAnalogGroupDelayRollup {
  in stageGroupDelays_ns : Real[*];
  return totalAnalogGroupDelay_ns : Real;
}

calc def CalculateEndToEndLatency {
  in analogDelay_ns : Real;
  in adcLatency_s : Real;
  in digitalLatency_s : Real;
  return endToEndLatency_s : Real;
}
```

## Requirements

Requirements should be organized by signal-chain performance domain and should
use `SignalChain`, `RFStage`, `ADC`, `FIRFilter`, or concrete configured usages
as their subjects.

Initial requirements:

```text
MaximumAnalogGroupDelay
MaximumAnalogGroupDelayVariation
MaximumCascadeNoiseFigure
MinimumCascadeGain
MinimumAdcSnr
MaximumEndToEndLatency
MaximumDigitalLatency
MaximumFirPassbandRipple
MinimumFirStopbandAttenuation
MaximumFirTransitionBandwidth
AnalysisEvidenceRequired
VerificationEvidenceRequired
```

Example requirement intent:

```text
MaximumCascadeNoiseFigure
  subject: SignalChain or RFAnalogChain usage
  constraint: cascadeNoiseFigure_dB <= maximumNoiseFigure_dB

MaximumEndToEndLatency
  subject: SignalChain or configured signal chain usage
  constraint: endToEndLatency_s <= maximumLatency_s

MinimumFirStopbandAttenuation
  subject: FIRFilter or configured FIR filter usage
  constraint: stopbandAttenuation_dB >= minimumStopbandAttenuation_dB
```

## Architecture Model

The architecture package should show the signal path and domain boundaries. The
minimum structural model is:

```text
RFToDigitalArchitecture
  part receiverSignalChain : SignalChain
    part rfInputProtection : Limiter
    part rfFilter : RF_Filter
    part lna : LowNoiseAmplifier
    part mixer : Mixer
    part localOscillator : LocalOscillator
    part ifFilter : IF_Filter
    part adc : ADC
    part digitalDownconverter : DigitalDownconverter
    part firFilter : FIRFilter
    part decimator : Decimator
    part digitalProcessor : DigitalProcessor
```

The ADC should appear in `ConversionBoundary` as the point where analog and
sampled domains meet.

```text
ConversionBoundary
  part adc : ADC
    in analogIfIn : AnalogIFSignal
    out sampledSignalOut : SampledSignal
```

## Configurations

The model should include concrete signal-chain configurations under
`Configurations`. Each configuration should bind numerical values for the chain
and its owned parts.

Initial configurations:

```text
NominalSignalChain
WorstCaseNoiseFigureChain
WorstCaseDelayChain
LabTestSignalChain
AsImplementedFpgaChain
```

Each configuration should identify:

- RF/IF frequency plan.
- Signal bandwidth.
- RF stage gains and losses.
- RF stage noise figures.
- RF stage group delays and delay variation.
- ADC sample rate, resolution, jitter, and latency.
- FIR filter taps, sample rate, decimation factor, and coefficient set.
- Digital processing latency.
- Source of each value when known.

## Analysis Cases

Analysis cases are the main place to evaluate delay, noise figure, conversion,
and filter performance before formal verification.

Required analysis cases:

```text
AnalogGroupDelayAnalysis
NoiseFigureCascadeAnalysis
AdcPerformanceAnalysis
FirFilterDelayAnalysis
FirFilterFrequencyResponseAnalysis
DigitalLatencyAnalysis
EndToEndLatencyAnalysis
WorstCaseSignalChainAnalysis
```

Each analysis case should have:

- A subject, usually a configured `SignalChain`, `RFStage`, `ADC`, or
  `FIRFilter`.
- Explicit input parameters or bindings to subject attributes.
- Returned outputs for the performance metric being evaluated.
- A status indicating whether the analysis completed and whether assumptions
  are valid.

## Verification Cases

Verification cases should consume analysis results, simulation results, lab
measurements, or implementation evidence and return a verdict. Use the SysML v2
verification result concepts where supported by the tool: `pass`, `fail`,
`inconclusive`, or `error`.

Required verification cases:

```text
VerifyAnalogGroupDelay
VerifyAnalogGroupDelayVariation
VerifyCascadeNoiseFigure
VerifyAdcSnr
VerifyFirPassbandRipple
VerifyFirStopbandAttenuation
VerifyDigitalLatency
VerifyEndToEndLatency
VerifyAnalysisEvidenceExists
```

Each verification case should link to:

- The requirement being verified.
- The signal-chain configuration or test article used as the verification
  subject.
- The analysis case, RF simulation, DSP simulation, HDL result, lab measurement,
  or external evidence source used to make the decision.
- The verdict.
- The evidence artifact or result record.

## Executability Approach

SysML v2 can express executable-style model behavior through calculations,
actions, analysis cases, and verification cases. However, execution is tool
dependent. The RF-to-digital signal chain model should be designed so it can
degrade gracefully across tools:

```text
Level 1: Static model
  Architecture, requirements, parameters, and trace links are modeled.

Level 2: Native calculation
  The SysML v2 tool evaluates simple calc definitions and analysis cases.

Level 3: External calculation
  The SysML v2 model provides parameters to Python, MATLAB, RF tools, DSP tools,
  or HDL simulation, and results are imported or linked back to analysis and
  verification results.

Level 4: Integrated digital engineering workflow
  RF simulation, measurement systems, filter-design tools, HDL implementation,
  timing closure, and test systems provide governed evidence while SysML v2
  preserves traceability.
```

For the local Flexo/SysON lab, assume Level 1 initially and design the model so
Level 3 can be added through scripts. Do not rely on graphical tool execution as
the only source of analysis truth until the tool capability has been verified.

## External Execution Interface

If external execution is used, the script or tool adapter should accept a
configuration record with these inputs:

```text
configurationId
inputFrequency_Hz
signalBandwidth_Hz
rfStages[]
  name
  type
  gain_dB
  noiseFigure_dB
  insertionLoss_dB
  groupDelay_ns
  groupDelayVariation_ns
  temperature_K
adc
  sampleRate_Hz
  resolution_bits
  fullScaleVoltage_V
  inputBandwidth_Hz
  apertureJitter_s
  latency_samples
firFilters[]
  name
  sampleRate_Hz
  numberOfTaps
  latency_samples
  decimationFactor
  passbandRipple_dB
  stopbandAttenuation_dB
  transitionBandwidth_Hz
digitalBlocks[]
  name
  sampleRate_Hz
  latency_samples
```

Expected outputs:

```text
configurationId
totalAnalogGroupDelay_ns
analogGroupDelayVariation_ns
cascadeNoiseFigure_dB
cascadeGain_dB
idealAdcSnr_dB
jitterSnr_dB
firGroupDelay_samples
firGroupDelay_s
digitalLatency_samples
digitalLatency_s
endToEndLatency_s
status
messages
```

## Traceability Checklist

- Every delay, noise figure, ADC, or FIR filter requirement has a subject.
- Every signal-chain configuration binds the required numerical inputs.
- Every analog/digital boundary is represented explicitly.
- Every analysis case has a configured subject.
- Every verification case identifies the requirement it verifies.
- Every verification case identifies the analysis result or evidence it uses.
- Every computed output has a unit and a source calculation.
- Every linked response artifact has a source and confidence marker.
- Every failed or inconclusive result is visible in review views.

## Initial Review Views

The model should support these review views:

- RF-to-digital signal chain architecture.
- Analog/digital domain boundary view.
- RF stage gain/noise/delay table.
- ADC performance table.
- FIR filter parameter table.
- End-to-end latency rollup.
- Cascaded noise figure rollup.
- Requirement to analysis case trace.
- Requirement to verification case trace.
- Failed or missing verification results.

## Open Design Decisions

- Whether to represent frequency-dependent data as SysML-owned tables, external
  artifacts, or both.
- Whether to model one receive chain first or separate receive/transmit chains.
- Whether to use simple scalar RF stage parameters initially or introduce
  S-parameter and measured response artifacts in the first implementation.
- Whether FIR coefficients should be represented directly in SysML v2 or linked
  as external generated artifacts.
- Which external execution format should be the first supported target: JSON,
  CSV, MATLAB data, Python data, or direct SysML v2 API extraction.
