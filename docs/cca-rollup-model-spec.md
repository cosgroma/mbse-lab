# CCA Rollup SysML v2 Model Specification

This document specifies the intended SysML v2 model for a circuit card assembly
(CCA) that supports power, mass, and cost rollups. The model is intended to
support product structure definition, engineering budget analysis, requirements
traceability, and verification of board-level constraints.

The model should be useful as both:

- A semantic MBSE model that captures CCA product structure, component
  attributes, operating modes, assumptions, requirements, and verification trace.
- An executable or tool-assisted rollup model that can evaluate mass, power, and
  cost totals through SysML v2 calculations, analysis cases, or delegated
  external computation.

## Goals

- Represent the CCA as a hierarchical assembly with owned electrical,
  mechanical, and manufacturing elements.
- Capture component quantities, mass, cost, and power by operating mode.
- Compute assembly-level rollups for mass, power, and cost.
- Trace board-level requirements to CCA structure, analysis cases, and
  verification cases.
- Support configured variants such as engineering model, flight model, spare,
  low-power mode, peak-load mode, and as-built board.
- Preserve enough model structure to execute simple rollups directly and
  delegate richer calculations to external tools.

## Non-Goals

- This model will not replace electrical CAD, PCB layout, SPICE, thermal, or
  manufacturing resource planning tools.
- This model will not assume every SysML v2 tool can execute all calculations
  natively.
- This model will not initially model detailed circuit behavior, signal
  integrity, derating, or thermal behavior beyond the attributes needed for
  power, mass, and cost rollups.

## References

- OMG SysML v2 specification: <https://www.omg.org/spec/SysML>
- OMG SysML v2 Language specification PDF:
  <https://www.omg.org/spec/SysML/2.0/Language/PDF>
- OMG KerML specification: <https://www.omg.org/spec/KerML/1.0>
- SysML v2 release repository and examples:
  <https://github.com/Systems-Modeling/SysML-v2-Release>
- Local verification model setup guide:
  `docs/sysml-v2-verification-model-setup.md`

## MDA Methodology Alignment

This model should use Model Driven Architecture concepts as a layering pattern:

```text
CIM-like layer
  Stakeholder budget concerns, board-level constraints, mission or product
  affordability objectives, mass allocation, and power allocation.

PIM-like layer
  Abstract CCA product structure, component classes, operating modes, mass,
  power, and cost attributes, rollup equations, requirements, analysis cases,
  and verification intent independent of a specific board implementation.

PSM-like layer
  Specific board variant, selected parts, reference designators, quantities,
  vendor data, ECAD/BOM data, manufacturing assumptions, labor rates, test
  flow, procurement status, and as-built configuration data.

Generated and evidence artifacts
  BOM exports, rollup JSON/CSV inputs, spreadsheet or Python outputs, measured
  board mass, power test data, cost reports, and verification evidence records.
```

The model should preserve traceability across these layers so a budget
requirement can be followed to the product structure, the configured board, the
rollup execution, and the evidence used to verify the result.

## Model Boundary

The model covers the CCA product structure from board-level assembly down to
parts whose mass, power, or cost contribute to the rollup:

```text
circuit card assembly
  -> printed wiring board
  -> electrical components
  -> connectors
  -> programmable devices
  -> mechanical hardware
  -> assembly, test, and non-recurring cost contributors
```

The model should expose the following primary outputs:

- Total CCA mass, `totalMass_g`.
- Nominal CCA power, `nominalPower_W`.
- Standby CCA power, `standbyPower_W`.
- Peak CCA power, `peakPower_W`.
- Power by named operating mode, `powerByMode_W`.
- Total recurring unit cost, `totalRecurringCost_usd`.
- Total non-recurring cost, `totalNonRecurringCost_usd`.
- Total estimated unit cost, `totalUnitCost_usd`.
- Requirement verdict or analysis status.

## Recommended Package Structure

```text
CCARollupModel
  Libraries
    Units
    CostAccounting
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
    MassRequirements
    PowerRequirements
    CostRequirements
    ManufacturingRequirements
  Architecture
    CCAArchitecture
    ElectricalArchitecture
    MechanicalArchitecture
    ManufacturingBreakdown
  Configurations
    CCA_AsSpecified
    CCA_AsDesigned
    CCA_AsBuilt
    CCA_EngineeringModel
    CCA_FlightModel
    CCA_Spare
  Analysis
    MassRollupAnalysisCases
    PowerRollupAnalysisCases
    CostRollupAnalysisCases
    SensitivityAnalyses
  Verification
    VerificationCases
    VerificationProcedures
    VerificationResults
  Views_Viewpoints
    CCAProductStructureViews
    RollupViews
    RequirementTraceViews
    VerificationTraceViews
```

## Core Part Definitions

The model should define reusable CCA component types under
`Definitions/PartDefinitions`.

```text
CircuitCardAssembly
PrintedWiringBoard
ElectronicComponent
IntegratedCircuit
Processor
FPGA
MemoryDevice
PowerConverter
VoltageRegulator
Oscillator
PassiveComponent
Connector
HarnessInterface
MechanicalHardware
ConformalCoating
AssemblyLabor
TestActivity
```

### CircuitCardAssembly

`CircuitCardAssembly` is the primary subject for analysis and verification.

Expected owned parts:

- `board : PrintedWiringBoard`
- `components : ElectronicComponent[0..*]`
- `connectors : Connector[0..*]`
- `mechanicalHardware : MechanicalHardware[0..*]`
- `coating : ConformalCoating[0..1]`
- `assemblyLabor : AssemblyLabor[0..1]`
- `testActivity : TestActivity[0..1]`

Expected attributes:

- `totalMass_g`
- `standbyPower_W`
- `nominalPower_W`
- `peakPower_W`
- `totalRecurringCost_usd`
- `totalNonRecurringCost_usd`
- `totalUnitCost_usd`
- `boardArea_cm2`
- `operatingMode`
- `configurationState`

### PrintedWiringBoard

Expected attributes:

- `bareBoardMass_g`
- `bareBoardCost_usd`
- `layerCount`
- `boardArea_cm2`
- `boardThickness_mm`
- `material`
- `fabricationYield`

### ElectronicComponent

Expected attributes:

- `referenceDesignator`
- `partNumber`
- `manufacturer`
- `quantity`
- `mass_g`
- `unitCost_usd`
- `standbyPower_W`
- `nominalPower_W`
- `peakPower_W`
- `voltage_V`
- `current_A`
- `procurementStatus`
- `sourceConfidence`

### PowerConverter

Expected attributes:

- `inputVoltage_V`
- `outputVoltage_V`
- `outputCurrent_A`
- `efficiency`
- `quiescentPower_W`
- `nominalOutputPower_W`
- `peakOutputPower_W`

### Connector

Expected attributes:

- `quantity`
- `mass_g`
- `unitCost_usd`
- `pinCount`
- `matingInterface`

### MechanicalHardware

Expected attributes:

- `quantity`
- `mass_g`
- `unitCost_usd`
- `material`
- `function`

### AssemblyLabor

Expected attributes:

- `laborHours`
- `laborRate_usdPerHour`
- `setupCost_usd`
- `inspectionCost_usd`

### TestActivity

Expected attributes:

- `testHours`
- `testRate_usdPerHour`
- `fixtureCost_usd`
- `environmentalScreeningCost_usd`

## Units and Quantities

The model should use explicit quantity definitions or imported unit libraries
for all engineering and cost values. At minimum, the model should distinguish:

- Mass in `g` and `kg`.
- Power in `W` and `mW`.
- Voltage in `V`.
- Current in `A` and `mA`.
- Area in `cm2`.
- Thickness in `mm`.
- Cost in `USD`.
- Labor rate in `USD/hour`.
- Dimensionless factors such as efficiency and yield.

Avoid unqualified `Real` attributes in production model content where a unitful
quantity is available in the target tool.

## Operating Modes

Power rollups should be mode-aware. The initial mode set should be:

```text
Off
Standby
Initialization
Nominal
PeakProcessing
Transmit
SafeMode
Test
```

Each component does not need a value for every mode at first, but the model
should support mode-specific power as the design matures.

Recommended representation:

```text
PowerMode
  name
  description
  dutyCycle

ComponentPowerByMode
  component
  mode
  power_W
  source
  confidence
```

## Calculation Definitions

The model should define reusable `calc def` elements under
`Definitions/CalculationDefinitions`.

Required calculations:

```text
CalculateMassRollup
CalculateStandbyPowerRollup
CalculateNominalPowerRollup
CalculatePeakPowerRollup
CalculatePowerByMode
CalculateRecurringCostRollup
CalculateNonRecurringCostRollup
CalculateUnitCost
CalculateCostWithYield
CalculateLaborCost
CalculateTestCost
```

### Baseline Equations

The initial model should support simple deterministic rollups:

```text
componentMassRollup_g =
  sum(component.mass_g * component.quantity)

totalMass_g =
  board.bareBoardMass_g
  + componentMassRollup_g
  + sum(connector.mass_g * connector.quantity)
  + sum(mechanicalHardware.mass_g * mechanicalHardware.quantity)
  + coating.mass_g

standbyPower_W =
  sum(component.standbyPower_W * component.quantity)

nominalPower_W =
  sum(component.nominalPower_W * component.quantity)

peakPower_W =
  sum(component.peakPower_W * component.quantity)

powerByMode_W[mode] =
  sum(component.powerByMode_W[mode] * component.quantity)

componentCost_usd =
  sum(component.unitCost_usd * component.quantity)

laborCost_usd =
  assemblyLabor.laborHours * assemblyLabor.laborRate_usdPerHour
  + assemblyLabor.setupCost_usd
  + assemblyLabor.inspectionCost_usd

testCost_usd =
  testActivity.testHours * testActivity.testRate_usdPerHour
  + testActivity.fixtureCost_usd
  + testActivity.environmentalScreeningCost_usd

recurringCost_usd =
  board.bareBoardCost_usd
  + componentCost_usd
  + sum(connector.unitCost_usd * connector.quantity)
  + sum(mechanicalHardware.unitCost_usd * mechanicalHardware.quantity)
  + laborCost_usd
  + testCost_usd

unitCostWithYield_usd =
  recurringCost_usd / fabricationYield

totalUnitCost_usd =
  unitCostWithYield_usd + allocatedNonRecurringCost_usd
```

### SysML v2 Calculation Sketch

The exact syntax may need adjustment for the target tool parser, but the model
intent should be captured as reusable calculations:

```sysml
calc def CalculateMassRollup {
  in boardMass_g : Real;
  in componentMasses_g : Real[*];
  in componentQuantities : Real[*];
  in connectorMasses_g : Real[*];
  in connectorQuantities : Real[*];
  in hardwareMasses_g : Real[*];
  in hardwareQuantities : Real[*];
  in coatingMass_g : Real;
  return totalMass_g : Real;
}

calc def CalculatePowerRollup {
  in componentPowers_W : Real[*];
  in componentQuantities : Real[*];
  return totalPower_W : Real;
}

calc def CalculateRecurringCostRollup {
  in boardCost_usd : Real;
  in componentCosts_usd : Real[*];
  in componentQuantities : Real[*];
  in connectorCosts_usd : Real[*];
  in connectorQuantities : Real[*];
  in hardwareCosts_usd : Real[*];
  in hardwareQuantities : Real[*];
  in laborCost_usd : Real;
  in testCost_usd : Real;
  return recurringCost_usd : Real;
}
```

## Requirements

Requirements should be organized by budget domain and should use
`CircuitCardAssembly` or a concrete CCA configuration as their subject.

Initial requirements:

```text
MaximumCCAMass
MaximumStandbyPower
MaximumNominalPower
MaximumPeakPower
MaximumRecurringUnitCost
MaximumTotalUnitCost
PowerModeCoverageRequired
RollupEvidenceRequired
```

Example requirement intent:

```text
MaximumCCAMass
  subject: CircuitCardAssembly or configured CCA usage
  constraint: totalMass_g <= maximumMass_g

MaximumNominalPower
  subject: CircuitCardAssembly or configured CCA usage
  constraint: nominalPower_W <= maximumNominalPower_W

MaximumRecurringUnitCost
  subject: CircuitCardAssembly or configured CCA usage
  constraint: totalRecurringCost_usd <= maximumRecurringCost_usd
```

## Architecture Model

The architecture package should show the CCA product structure and relevant
electrical interfaces. The minimum structural model is:

```text
CCAArchitecture
  part avionicsControllerCca : CircuitCardAssembly
    part board : PrintedWiringBoard
    part processor : Processor
    part fpga : FPGA
    part memory : MemoryDevice
    part powerConverters : PowerConverter[0..*]
    part passives : PassiveComponent[0..*]
    part connectors : Connector[0..*]
    part hardware : MechanicalHardware[0..*]
```

The model should include ports and item flows when the tool supports them well:

```text
PowerInput
PowerRail
DigitalSignal
AnalogSignal
DiscreteSignal
GroundReference
```

Candidate ports:

- `primaryPowerIn` on CCA.
- `regulatedPowerOut` on power converters.
- `dataBus` on processor, FPGA, and connectors.
- `testInterface` on CCA.
- `chassisGround` or `signalGround` where relevant.

## Configurations

The model should include concrete CCA configurations under `Configurations`.
Each configuration should bind numerical values for the product structure and
rollup attributes.

Initial configurations:

```text
CCA_AsSpecified
CCA_AsDesigned
CCA_AsBuilt
CCA_EngineeringModel
CCA_FlightModel
CCA_Spare
CCA_TestArticle
```

Each configuration should identify:

- Part list and quantities.
- Board fabrication assumptions.
- Operating modes covered by power data.
- Mass source for each part.
- Cost source for each part.
- Procurement status.
- Confidence or maturity of each data source.
- Configuration date or baseline identifier.

## Analysis Cases

Analysis cases are the main place to evaluate rollups before formal
verification.

Required analysis cases:

```text
MassRollupAnalysis
StandbyPowerRollupAnalysis
NominalPowerRollupAnalysis
PeakPowerRollupAnalysis
ModePowerRollupAnalysis
RecurringCostRollupAnalysis
TotalUnitCostRollupAnalysis
CostSensitivityAnalysis
PowerSensitivityAnalysis
```

Each analysis case should have:

- A subject, usually a configured `CircuitCardAssembly`.
- Explicit input parameters or bindings to subject attributes.
- Returned outputs for the rollup result being evaluated.
- A status indicating whether the analysis completed and whether assumptions
  are valid.

## Verification Cases

Verification cases should consume analysis results, measured data, BOM exports,
or cost evidence and return a verdict. Use the SysML v2 verification result
concepts where supported by the tool: `pass`, `fail`, `inconclusive`, or
`error`.

Required verification cases:

```text
VerifyCCAMassLimit
VerifyStandbyPowerLimit
VerifyNominalPowerLimit
VerifyPeakPowerLimit
VerifyRecurringCostLimit
VerifyTotalUnitCostLimit
VerifyRollupEvidenceExists
```

Each verification case should link to:

- The requirement being verified.
- The CCA configuration or test article used as the verification subject.
- The analysis case, measurement procedure, BOM export, or external evidence
  source used to make the decision.
- The verdict.
- The evidence artifact or result record.

## Executability Approach

SysML v2 can express executable-style model behavior through calculations,
actions, analysis cases, and verification cases. However, execution is tool
dependent. The CCA rollup model should be designed so it can degrade gracefully
across tools:

```text
Level 1: Static model
  Product structure, requirements, attributes, and trace links are modeled.

Level 2: Native calculation
  The SysML v2 tool evaluates simple calc definitions and analysis cases.

Level 3: External calculation
  The SysML v2 model provides parameters to Python, spreadsheets, ERP/MRP
  exports, or another solver, and results are imported or linked back to
  analysis and verification results.

Level 4: Integrated digital thread
  ECAD, PLM, ERP, procurement, test, and measurement systems provide governed
  source data while SysML v2 preserves product structure and traceability.
```

For the local Flexo/SysON lab, assume Level 1 initially and design the model so
Level 3 can be added through scripts. Do not rely on graphical tool execution as
the only source of rollup truth until the tool capability has been verified.

## External Execution Interface

If external execution is used, the script or tool adapter should accept a
configuration record with these inputs:

```text
configurationId
configurationState
boardMass_g
boardCost_usd
fabricationYield
allocatedNonRecurringCost_usd
components[]
  referenceDesignator
  partNumber
  componentType
  quantity
  mass_g
  unitCost_usd
  standbyPower_W
  nominalPower_W
  peakPower_W
  powerByMode_W
connectors[]
  referenceDesignator
  partNumber
  quantity
  mass_g
  unitCost_usd
mechanicalHardware[]
  name
  quantity
  mass_g
  unitCost_usd
assemblyLabor
  laborHours
  laborRate_usdPerHour
  setupCost_usd
  inspectionCost_usd
testActivity
  testHours
  testRate_usdPerHour
  fixtureCost_usd
  environmentalScreeningCost_usd
```

Expected outputs:

```text
configurationId
totalMass_g
standbyPower_W
nominalPower_W
peakPower_W
powerByMode_W
componentCost_usd
laborCost_usd
testCost_usd
totalRecurringCost_usd
allocatedNonRecurringCost_usd
totalUnitCost_usd
status
messages
```

## Traceability Checklist

- Every CCA budget requirement has a subject.
- Every configured CCA binds the required product structure and quantities.
- Every rollup input has a source or confidence marker.
- Every analysis case has a configured `CircuitCardAssembly` subject.
- Every verification case identifies the requirement it verifies.
- Every verification case identifies the analysis result or evidence it uses.
- Every computed output has a unit and a source calculation.
- Every failed or inconclusive result is visible in review views.
- Every external evidence artifact is linked from the verification result.

## Initial Review Views

The model should support these review views:

- CCA product structure tree.
- BOM-style component table.
- Mass rollup by assembly branch.
- Power rollup by operating mode.
- Cost rollup by cost category.
- Requirement to analysis case trace.
- Requirement to verification case trace.
- Configuration to rollup result table.
- Failed or missing verification results.

## Open Design Decisions

- Whether to represent the initial CCA as one flat BOM or as a deeper hierarchy
  with functional subassemblies.
- Whether to represent power by mode as attributes on components or as separate
  `ComponentPowerByMode` usages.
- Whether cost should include procurement-only cost at first or include labor,
  test, yield, and allocated non-recurring cost in the first implementation.
- Which external execution format should be the first supported target: JSON,
  CSV, spreadsheet import, or direct SysML v2 API extraction.
- Whether the first implementation should model a generic CCA or a specific
  avionics board configuration.
