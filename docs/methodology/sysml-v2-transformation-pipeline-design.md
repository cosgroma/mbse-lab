# SysML v2 Transformation Pipeline Design

This document defines the transformation pipeline strategy for the local MBSE
lab. It connects official SysML v2 transformation concepts, local Flexo/SysON
interchange, and model-specific execution pipelines for analysis and
verification.

## Purpose

The transformation pipeline should make SysML v2 models useful beyond static
documentation. The model should be the authoritative source for structure,
requirements, configurations, analyses, verification intent, and traceability.
Transformations should derive review, analysis, implementation, and evidence
artifacts from that source.

Primary objectives:

- Preserve model semantics and traceability across tools.
- Generate reproducible analysis inputs from configured SysML v2 model content.
- Import or link analysis and verification results back to the model.
- Keep transformation assumptions explicit and reviewable.
- Support gradual growth from simple file-based workflows to API-backed
  automation.

## References

- OMG SysML v2 specification: <https://www.omg.org/spec/SysML>
- OMG SysML v2 Transformation specification:
  <https://www.omg.org/spec/SysML/2.0/Transformation/PDF>
- OMG SysML v2 API and Services specification:
  <https://www.omg.org/spec/SysML/2.0/API/PDF>
- OMG SysML v2 Language specification:
  <https://www.omg.org/spec/SysML/2.0/Language/PDF>
- OMG MDA overview: <https://www.omg.org/mda/>
- Local Flexo/SysON bridge notes: `docs/lab/flexo-syson-bridge.md`
- Local verification model setup guide:
  `docs/methodology/sysml-v2-verification-model-setup.md`

## Transformation Types

The lab should distinguish several transformation types.

```text
Migration transformation
  SysML v1.x model -> SysML v2 model

Interchange transformation
  repository JSON -> textual .sysml -> graphical tool import

Analysis transformation
  SysML v2 configuration -> solver/script input -> computed results

Verification transformation
  analysis/test result -> verification verdict/evidence record

Document transformation
  SysML v2 model -> review tables, trace matrices, ICDs, reports

Implementation transformation
  SysML v2 model -> code stubs, HDL parameters, test scripts, config files
```

The official OMG SysML v2 Transformation specification primarily addresses
SysML v1-to-v2 migration. The other transformation types are project workflow
transformations built on SysML v2 textual notation, APIs, exports, scripts, and
tool adapters.

## Transformation Principles

- Treat SysML v2 as the semantic source of truth.
- Keep source model exports, generated inputs, computed outputs, and imported
  results as separate artifacts.
- Preserve stable identifiers across transformation boundaries.
- Prefer structured formats such as JSON or CSV over unstructured text for
  execution interfaces.
- Record the transformation version, input model version, execution timestamp,
  tool version, and assumptions in generated outputs.
- Do not overwrite model-owned values with computed values unless the update is
  intentional, traceable, and reviewable.
- Link evidence artifacts back to analysis cases, verification cases, and
  requirements.
- Keep transformations deterministic where practical.
- Make unsupported element types visible rather than silently dropping them.

## Local Tool Flow

The current local tool flow is intentionally conservative:

```text
Flexo SysML v2 REST JSON
  -> SysML v2 textual .sysml
  -> SysON GraphQL textual import
```

Flexo MMS should be treated as the durable API-backed repository path for
experiments. SysON should be treated as the graphical review and editing surface.

Current artifacts:

```text
exports/flexo/<project-id>.json
exports/sysml/<project-id>.sysml
```

Current commands:

```bash
mbse-lab flexo export <flexo-project-id>
mbse-lab bridge render exports/flexo/<flexo-project-id>.json
mbse-lab bridge import \
  exports/sysml/<flexo-project-id>.sysml \
  --project-id <syson-project-id> \
  --namespace-id <syson-root-package-id>
```

The bridge currently preserves the raw Flexo JSON export and renders a
supported subset of SysML v2 textual notation. Unsupported model element types
must remain visible in the source export and should be added to the renderer
before those elements become critical to a workflow.

## Target Pipeline Architecture

The intended pipeline has four layers:

```text
1. Model repository layer
   Flexo MMS, SysML v2 API, textual .sysml snapshots

2. Transformation layer
   extractors, renderers, validators, model-to-analysis adapters,
   model-to-document adapters, result importers

3. Execution layer
   Python, MATLAB, RF tools, DSP tools, spreadsheets, test systems,
   HDL simulation, CI jobs

4. Evidence layer
   analysis result JSON, plots, reports, test logs, verification verdicts,
   linked external artifacts
```

Transformations should be small, composable, and model-aware. For example, an
RF link budget adapter should understand `RFLink` configurations instead of
scraping arbitrary text.

## Generic Analysis Pipeline

The common analysis pattern should be:

```text
SysML v2 model configuration
  -> extract configuration and parameters
  -> validate required inputs
  -> generate structured analysis input
  -> execute analysis tool or script
  -> write structured result artifact
  -> link or import result into SysML analysis case
  -> evaluate verification case verdict
  -> link evidence to requirement and verification result
```

Recommended input artifact fields:

```text
modelId
projectId
configurationId
configurationName
analysisCaseId
analysisCaseName
modelBaseline
transformationName
transformationVersion
inputs
assumptions
sourceElementIds
```

Recommended output artifact fields:

```text
modelId
projectId
configurationId
analysisCaseId
executionId
executionTimestamp
toolName
toolVersion
transformationName
transformationVersion
status
results
messages
evidenceArtifacts
sourceElementIds
```

## Verification Result Pipeline

Verification results should not be treated as informal notes. A verification
pipeline should produce a structured result that can be traced:

```text
analysis result or test result
  -> requirement threshold lookup
  -> comparison rule
  -> verdict
  -> evidence record
  -> verification result linked to verification case and requirement
```

Recommended verdict values:

```text
pass
fail
inconclusive
error
```

Recommended verification result fields:

```text
verificationCaseId
requirementId
subjectId
configurationId
method
verdict
measuredOrComputedValues
thresholds
comparisonRules
evidenceArtifacts
executionTimestamp
reviewStatus
```

## Model-Specific Pipelines

### RF Link Budget

Source model:

```text
RFLinkBudgetModel
  Configurations
  Analysis/LinkBudgetAnalysisCases
  Requirements/LinkPerformanceRequirements
  Verification/VerificationCases
```

Pipeline:

```text
configured RFLink
  -> link_budget_input.json
  -> Python/MATLAB link budget execution
  -> link_budget_result.json
  -> LinkBudgetAnalysis result
  -> VerifyMinimumLinkMargin verdict
  -> linked evidence
```

Expected inputs:

```text
frequency_MHz
range_km
dataRate_bps
outputPower_dBm
txLineLoss_dB
txAntennaGain_dBi
pathLoss_dB or path-loss inputs
rxAntennaGain_dBi
rxLineLoss_dB
noiseFigure_dB
requiredEbNo_dB
```

Expected outputs:

```text
fspl_dB
eirp_dBm
receivedPower_dBm
cNo_dBHz
ebNo_dB
linkMargin_dB
sensitivityMargin_dB
verdict inputs
```

### CCA Rollup

Source model:

```text
CCARollupModel
  Configurations
  Analysis/MassRollupAnalysisCases
  Analysis/PowerRollupAnalysisCases
  Analysis/CostRollupAnalysisCases
  Requirements
  Verification/VerificationCases
```

Pipeline:

```text
configured CircuitCardAssembly
  -> cca_rollup_input.json
  -> Python/spreadsheet/ERP-backed rollup execution
  -> cca_rollup_result.json
  -> mass, power, and cost analysis results
  -> budget verification verdicts
  -> linked evidence
```

Expected inputs:

```text
board mass and cost
component list
reference designators
quantities
component mass
component unit cost
power by mode
labor assumptions
test assumptions
yield assumptions
allocated non-recurring cost
```

Expected outputs:

```text
totalMass_g
standbyPower_W
nominalPower_W
peakPower_W
powerByMode_W
totalRecurringCost_usd
totalUnitCost_usd
verdict inputs
```

### RF to Digital Signal Chain

Source model:

```text
RFToDigitalSignalChainModel
  Configurations
  Analysis/DelayAnalysisCases
  Analysis/NoiseFigureAnalysisCases
  Analysis/DigitalFilterAnalysisCases
  Requirements
  Verification/VerificationCases
```

Pipeline:

```text
configured SignalChain
  -> signal_chain_analysis_input.json
  -> Python/MATLAB/RF/DSP/HDL analysis execution
  -> signal_chain_analysis_result.json
  -> delay, noise figure, ADC, and FIR analysis results
  -> signal-chain verification verdicts
  -> linked evidence
```

Expected inputs:

```text
RF stage gains
RF stage noise figures
RF stage losses
RF stage group delays
ADC sample rate, resolution, jitter, and latency
FIR tap count, sample rate, coefficients, and latency
digital block latencies
```

Expected outputs:

```text
totalAnalogGroupDelay_ns
cascadeNoiseFigure_dB
cascadeGain_dB
idealAdcSnr_dB
jitterSnr_dB
firGroupDelay_samples
firGroupDelay_s
digitalLatency_s
endToEndLatency_s
verdict inputs
```

## Validation Gates

Each transformation should validate the source model before execution.

Recommended gates:

- Required packages exist.
- Required configurations exist.
- Required analysis cases have subjects.
- Required verification cases reference requirements.
- Required input attributes are present and unit-compatible.
- Referenced external evidence files or model artifacts exist.
- Unsupported element types are reported.
- Generated output includes transformation metadata.
- Result values are within basic sanity bounds.

## Traceability Requirements

Each generated artifact should retain traceability to the model elements that
produced it:

```text
requirementId
analysisCaseId
verificationCaseId
subjectId
configurationId
sourceElementIds[]
```

When a transformation creates a derived artifact, it should include enough
metadata to answer:

- Which model version produced this artifact?
- Which transformation produced it?
- Which input elements were used?
- Which assumptions were applied?
- Which tool executed the analysis?
- Which requirement or verification case consumes the result?

## Storage Layout

Recommended future artifact layout:

```text
exports/
  flexo/
  sysml/
  analysis/
    rf-link-budget/
    cca-rollup/
    rf-to-digital-signal-chain/
  verification/
    rf-link-budget/
    cca-rollup/
    rf-to-digital-signal-chain/
```

For early experiments, keep generated artifacts under `exports/` and avoid
committing large binary outputs unless they are intentionally curated examples.

## Implementation Roadmap

1. Keep the current Flexo JSON to SysML text to SysON import workflow stable.
2. Add validation reporting for unsupported or dropped element types.
3. Define JSON schemas for each model-specific analysis input and result.
4. Implement RF link budget extraction and result generation.
5. Implement CCA rollup extraction and result generation.
6. Implement RF-to-digital signal chain extraction and result generation.
7. Add result import or evidence-link creation back into the model repository.
8. Add trace matrix/report generation from model and result artifacts.
9. Add CI checks for transformation validation when model examples are added.

## Open Design Decisions

- Whether source extraction should operate on Flexo JSON, textual `.sysml`, the
  SysML v2 API, or all three.
- Whether analysis result import should create SysML v2 result elements directly
  or maintain external evidence files linked from model elements.
- Whether JSON schemas should be hand-authored or generated from SysML v2 model
  definitions.
- How stable identifiers should be assigned and preserved across Flexo, SysON,
  textual SysML, and generated artifacts.
- Which model-specific pipeline should be implemented first.
