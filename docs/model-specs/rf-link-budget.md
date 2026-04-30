# RF Link Budget SysML v2 Model Specification

This document specifies the intended SysML v2 model for an RF link budget. The
model is intended to support engineering analysis, requirements traceability,
and verification of communication link performance across configured mission or
test scenarios.

The model should be useful as both:

- A semantic MBSE model that captures the RF link architecture, parameters,
  assumptions, requirements, and verification trace.
- An executable or tool-assisted analysis model that can evaluate link margin
  through SysML v2 calculations, analysis cases, or delegated external
  computation.

## Goals

- Represent an end-to-end RF communication link from transmitter output to
  receiver demodulation.
- Capture link budget parameters with explicit units and ownership.
- Compute received power, noise terms, carrier-to-noise density, energy per bit
  to noise density, and link margin.
- Trace link performance requirements to architecture elements, analysis cases,
  and verification cases.
- Support multiple configured scenarios such as nominal range, worst-case range,
  different data rates, antenna modes, or environmental loss cases.
- Preserve enough model structure to execute simple budgets directly and
  delegate higher-fidelity calculations to external tools.

## Non-Goals

- This model will not replace detailed RF propagation, antenna pattern, orbital
  dynamics, or electromagnetic simulation tools.
- This model will not assume every SysML v2 tool can execute all calculations
  natively.
- This model will not encode detailed waveform, coding, modulation, or channel
  impairment behavior beyond the parameters needed for link budget margin unless
  those extensions are explicitly added later.

## References

- OMG SysML v2 specification: <https://www.omg.org/spec/SysML>
- OMG SysML v2 Language specification PDF:
  <https://www.omg.org/spec/SysML/2.0/Language/PDF>
- OMG KerML specification: <https://www.omg.org/spec/KerML/1.0>
- SysML v2 release repository and examples:
  <https://github.com/Systems-Modeling/SysML-v2-Release>
- Local verification model setup guide:
  `docs/methodology/sysml-v2-verification-model-setup.md`

## MDA Methodology Alignment

This model should use Model Driven Architecture concepts as a layering pattern:

```text
CIM-like layer
  Mission communication need, operational scenario, link availability concern,
  coverage need, and stakeholder performance objectives.

PIM-like layer
  Abstract RFLink, transmitter, antennas, propagation channel, receiver, modem,
  link performance requirements, budget equations, analysis cases, and
  verification intent independent of selected hardware.

PSM-like layer
  Specific radio, antenna, frequency band, waveform, data rate, propagation
  assumptions, ground station, test article, analysis tool, and selected
  implementation parameters.

Generated and evidence artifacts
  Python/MATLAB link budget inputs, simulation outputs, plots, test procedures,
  lab measurements, verification reports, and linked evidence records.
```

The model should preserve traceability across these layers so a stakeholder
link-performance need can be followed to the logical budget model, the concrete
configured link, the analysis execution, and the verification evidence.

## Model Boundary

The model covers the budget from transmit power generation through receiver
input and demodulation performance:

```text
transmitter
  -> transmit line losses
  -> transmit antenna gain
  -> propagation channel losses
  -> receive antenna gain
  -> receive line losses
  -> receiver noise and sensitivity
  -> modem/waveform performance threshold
```

The model should expose the following primary outputs:

- Effective isotropic radiated power, `eirp_dBm`.
- Free-space path loss, `fspl_dB`.
- Total propagation and implementation losses, `totalLoss_dB`.
- Received carrier power, `receivedPower_dBm`.
- Noise density, `noiseDensity_dBmPerHz`.
- Carrier-to-noise density ratio, `cNo_dBHz`.
- Energy per bit to noise density ratio, `ebNo_dB`.
- Required `Eb/N0`, `requiredEbNo_dB`.
- Link margin, `linkMargin_dB`.
- Requirement verdict or analysis status.

## Recommended Package Structure

```text
RFLinkBudgetModel
  Libraries
    Units
    Math
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
    LinkPerformanceRequirements
    EnvironmentalAssumptions
    InterfaceRequirements
  Architecture
    RFLinkArchitecture
    GroundSegment
    SpaceSegment
    TestEquipment
  Configurations
    NominalLink
    WorstCaseLink
    TestArticleLinks
  Analysis
    LinkBudgetAnalysisCases
    SensitivityAnalyses
    TradeStudies
  Verification
    VerificationCases
    VerificationProcedures
    VerificationResults
  Views_Viewpoints
    LinkBudgetViews
    RequirementTraceViews
    VerificationTraceViews
```

## Core Part Definitions

The model should define reusable RF component types under
`Definitions/PartDefinitions`.

```text
RFLink
Transmitter
Antenna
PropagationChannel
Receiver
Modem
RFChain
GroundStation
SpacecraftRadio
TestSet
```

### RFLink

`RFLink` is the primary subject for analysis and verification.

Expected owned parts:

- `transmitter : Transmitter`
- `txAntenna : Antenna`
- `channel : PropagationChannel`
- `rxAntenna : Antenna`
- `receiver : Receiver`
- `modem : Modem`

Expected attributes:

- `frequency_MHz`
- `range_km`
- `dataRate_bps`
- `bandwidth_Hz`
- `requiredAvailability`
- `operationalMode`
- `polarization`

### Transmitter

Expected attributes:

- `outputPower_dBm`
- `txLineLoss_dB`
- `txImplementationLoss_dB`
- `powerControlBackoff_dB`

### Antenna

Expected attributes:

- `gain_dBi`
- `pointingLoss_dB`
- `polarizationLoss_dB`
- `scanLoss_dB`

### PropagationChannel

Expected attributes:

- `freeSpacePathLoss_dB`
- `atmosphericLoss_dB`
- `rainLoss_dB`
- `multipathLoss_dB`
- `miscPropagationLoss_dB`
- `interferenceMargin_dB`

### Receiver

Expected attributes:

- `rxLineLoss_dB`
- `noiseFigure_dB`
- `systemNoiseTemperature_K`
- `receiverSensitivity_dBm`
- `implementationLoss_dB`

### Modem

Expected attributes:

- `modulation`
- `codingRate`
- `codingGain_dB`
- `requiredEbNo_dB`
- `dataRate_bps`
- `occupiedBandwidth_Hz`

## Units and Quantities

The model should use explicit quantity definitions or imported unit libraries
for all engineering values. At minimum, the model should distinguish:

- Power in `dBm`, `dBW`, and watts.
- Gain and loss in `dB` and `dBi`.
- Frequency in `Hz`, `MHz`, or `GHz`.
- Distance in `m` or `km`.
- Data rate in `bps`.
- Bandwidth in `Hz`.
- Temperature in `K`.
- Ratios such as `C/N0` in `dB-Hz`.

Avoid unqualified `Real` attributes in production model content where a unitful
quantity is available in the target tool.

## Calculation Definitions

The model should define reusable `calc def` elements under
`Definitions/CalculationDefinitions`.

Required calculations:

```text
CalculateFreeSpacePathLoss
CalculateEirp
CalculateTotalPropagationLoss
CalculateReceivedPower
CalculateNoiseDensity
CalculateCNo
CalculateEbNo
CalculateLinkMargin
CalculateReceiverSensitivityMargin
```

### Baseline Equations

The initial model should support a simple clear-air link budget:

```text
fspl_dB = 32.44 + 20 * log10(range_km) + 20 * log10(frequency_MHz)

eirp_dBm = outputPower_dBm
         - txLineLoss_dB
         - powerControlBackoff_dB
         + txAntennaGain_dBi
         - txPointingLoss_dB

totalLoss_dB = fspl_dB
             + atmosphericLoss_dB
             + rainLoss_dB
             + polarizationLoss_dB
             + miscPropagationLoss_dB
             + interferenceMargin_dB

receivedPower_dBm = eirp_dBm
                  - totalLoss_dB
                  + rxAntennaGain_dBi
                  - rxPointingLoss_dB
                  - rxLineLoss_dB

noiseDensity_dBmPerHz = -174.0
                      + noiseFigure_dB
                      + implementationLoss_dB

cNo_dBHz = receivedPower_dBm - noiseDensity_dBmPerHz

ebNo_dB = cNo_dBHz - 10 * log10(dataRate_bps)

linkMargin_dB = ebNo_dB
              - requiredEbNo_dB
              + codingGain_dB
              - modemImplementationLoss_dB
```

The model may also compute a simpler receiver-sensitivity margin:

```text
sensitivityMargin_dB = receivedPower_dBm - receiverSensitivity_dBm
```

### SysML v2 Calculation Sketch

The exact syntax may need adjustment for the target tool parser, but the model
intent should be captured as reusable calculations:

```sysml
calc def CalculateFreeSpacePathLoss {
  in range_km : Real;
  in frequency_MHz : Real;
  return fspl_dB : Real;
}

calc def CalculateEirp {
  in outputPower_dBm : Real;
  in txLineLoss_dB : Real;
  in powerControlBackoff_dB : Real;
  in txAntennaGain_dBi : Real;
  in txPointingLoss_dB : Real;
  return eirp_dBm : Real;
}

calc def CalculateLinkMargin {
  in ebNo_dB : Real;
  in requiredEbNo_dB : Real;
  in codingGain_dB : Real;
  in modemImplementationLoss_dB : Real;
  return linkMargin_dB : Real;
}
```

## Requirements

Requirements should be organized under `Requirements/LinkPerformanceRequirements`
and should use `RFLink` or a concrete link configuration as their subject.

Initial requirements:

```text
MinimumLinkMargin
MinimumReceivedPower
MaximumDataRateAtRange
RequiredAvailability
WorstCaseEnvironmentMargin
VerificationEvidenceRequired
```

Example requirement intent:

```text
MinimumLinkMargin
  subject: RFLink or configured RFLink usage
  constraint: linkMargin_dB >= requiredMinimumMargin_dB
  default threshold: 3.0 dB

MinimumReceivedPower
  subject: RFLink or configured RFLink usage
  constraint: receivedPower_dBm >= receiverSensitivity_dBm

WorstCaseEnvironmentMargin
  subject: WorstCaseLink configuration
  constraint: linkMargin_dB >= 0.0 dB
```

## Architecture Model

The architecture package should show ownership and signal path structure. The
minimum structural model is:

```text
RFLinkArchitecture
  part uhfDownlink : RFLink
    part spacecraftRadio : Transmitter
    part spacecraftAntenna : Antenna
    part spaceToGroundChannel : PropagationChannel
    part groundAntenna : Antenna
    part groundReceiver : Receiver
    part groundModem : Modem
```

The model should include ports and item flows when the tool supports them well:

```text
RFSignal
  frequency
  bandwidth
  modulation
  carrierPower
```

Candidate ports:

- `rfOut` on transmitter.
- `txRadiated` on transmit antenna.
- `rxIncident` on receive antenna.
- `rfIn` on receiver.
- `basebandOut` on modem or receiver chain.

## Configurations

The model should include concrete link configurations under `Configurations`.
Each configuration should bind numerical values for the RF link and its owned
parts.

Initial configurations:

```text
NominalLink
WorstCaseRangeLink
WorstCaseLossLink
LowDataRateLink
HighDataRateLink
GroundTestLink
```

Each configuration should identify:

- Frequency.
- Range.
- Data rate.
- Transmit power.
- Antenna gains.
- Loss assumptions.
- Receiver performance.
- Modem threshold.
- Environmental case.
- Source of each value when known.

## Analysis Cases

Analysis cases are the main place to evaluate the budget before formal
verification.

Required analysis cases:

```text
NominalLinkBudgetAnalysis
WorstCaseLinkBudgetAnalysis
DataRateSensitivityAnalysis
RangeSensitivityAnalysis
LossSensitivityAnalysis
```

Each analysis case should have:

- A subject, usually a configured `RFLink`.
- Explicit input parameters or bindings to subject attributes.
- Returned outputs for `receivedPower_dBm`, `cNo_dBHz`, `ebNo_dB`, and
  `linkMargin_dB`.
- A status indicating whether the analysis completed and whether assumptions
  are valid.

## Verification Cases

Verification cases should consume analysis results or test evidence and return a
verdict. Use the SysML v2 verification result concepts where supported by the
tool: `pass`, `fail`, `inconclusive`, or `error`.

Required verification cases:

```text
VerifyMinimumNominalLinkMargin
VerifyWorstCaseLinkMargin
VerifyReceiverSensitivityMargin
VerifyLinkBudgetEvidenceExists
```

Each verification case should link to:

- The requirement being verified.
- The link configuration or test article used as the verification subject.
- The analysis case, test procedure, or external evidence source used to make
  the decision.
- The verdict.
- The evidence artifact or result record.

## Executability Approach

SysML v2 can express executable-style model behavior through calculations,
actions, analysis cases, and verification cases. However, execution is tool
dependent. The RF link budget model should be designed so it can degrade
gracefully across tools:

```text
Level 1: Static model
  Architecture, requirements, parameters, and trace links are modeled.

Level 2: Native calculation
  The SysML v2 tool evaluates simple calc definitions and analysis cases.

Level 3: External calculation
  The SysML v2 model provides parameters to Python, MATLAB, or another solver,
  and results are imported or linked back to analysis and verification results.

Level 4: High-fidelity delegated simulation
  Specialized tools compute propagation, antenna pattern, orbital geometry,
  interference, or Monte Carlo results, while SysML v2 preserves traceability.
```

For the local Flexo/SysON lab, assume Level 1 initially and design the model so
Level 3 can be added through scripts. Do not rely on graphical tool execution as
the only source of analysis truth until the tool capability has been verified.

## External Execution Interface

If external execution is used, the script or tool adapter should accept a
configuration record with these inputs:

```text
configurationId
frequency_MHz
range_km
dataRate_bps
outputPower_dBm
txLineLoss_dB
txAntennaGain_dBi
txPointingLoss_dB
atmosphericLoss_dB
rainLoss_dB
polarizationLoss_dB
miscPropagationLoss_dB
interferenceMargin_dB
rxAntennaGain_dBi
rxPointingLoss_dB
rxLineLoss_dB
noiseFigure_dB
receiverSensitivity_dBm
requiredEbNo_dB
codingGain_dB
modemImplementationLoss_dB
```

Expected outputs:

```text
configurationId
fspl_dB
eirp_dBm
totalLoss_dB
receivedPower_dBm
noiseDensity_dBmPerHz
cNo_dBHz
ebNo_dB
linkMargin_dB
sensitivityMargin_dB
status
messages
```

## Traceability Checklist

- Every link performance requirement has a subject.
- Every RF link configuration binds the required numerical inputs.
- Every analysis case has a configured `RFLink` subject.
- Every verification case identifies the requirement it verifies.
- Every verification case identifies the analysis result or evidence it uses.
- Every computed output has a unit and a source calculation.
- Every failed or inconclusive result is visible in review views.
- Every external evidence artifact is linked from the verification result.

## Initial Review Views

The model should support these review views:

- RF link architecture.
- Link budget parameter table.
- Requirement to analysis case trace.
- Requirement to verification case trace.
- Configuration to link margin table.
- Link margin sensitivity by range.
- Link margin sensitivity by data rate.
- Failed or missing verification results.

## Open Design Decisions

- Whether to use purely scalar link parameters initially or introduce richer
  quantity/value types for dB, dBm, dBi, and dB-Hz.
- Whether to represent atmospheric, rain, pointing, and interference losses as
  independent model elements or attributes on `PropagationChannel`.
- Which external execution format should be the first supported target: JSON,
  CSV, or direct SysML v2 API extraction.
- Whether the first implementation should target a simple downlink only or a
  bidirectional link with separate uplink and downlink configurations.
