# SysML v2 Model Setup for End-to-End Verification

This guide captures recommended SysML v2 model organization practices for
supporting traceability from stakeholder concerns through requirements,
architecture, analysis, verification cases, and verification results.

The recommendations are grounded in the OMG SysML v2 and KerML specifications,
the official SysML v2 release examples, and general MBSE requirements and
verification practice.

## References

- OMG SysML v2 specification: <https://www.omg.org/spec/SysML>
- OMG SysML v2 Language specification PDF:
  <https://www.omg.org/spec/SysML/2.0/Language/PDF>
- OMG KerML specification: <https://www.omg.org/spec/KerML/1.0>
- OMG KerML specification PDF: <https://www.omg.org/spec/KerML/1.0/PDF>
- SysML v2 release repository and examples:
  <https://github.com/Systems-Modeling/SysML-v2-Release>
- INCOSE model-based practices:
  <https://sevisionweb.incose.org/model-based-practices>
- INCOSE Requirements Working Group:
  <https://www.incose.org/group/requirements-working-group/>

## Modeling Objective

The model should support a continuous verification path:

```text
stakeholder concern
  -> requirement
  -> architecture element that satisfies the requirement
  -> analysis or verification case that checks the requirement
  -> concrete configuration or test article used as the verification subject
  -> verdict and linked evidence
```

This requires organizing the model around semantic elements and trace
relationships, not around diagrams. Diagrams and views should be projections of
the model, not the primary source of truth.

## Recommended Package Structure

Use a package structure that separates reusable definitions from concrete model
usages, system configurations, and lifecycle evidence.

```text
ProjectModel
  Libraries
  Metadata
  Stakeholders_Concerns
  Definitions
    AttributeDefinitions
    ItemDefinitions
    PartDefinitions
    PortDefinitions
    InterfaceDefinitions
    ActionDefinitions
    RequirementDefinitions
    VerificationDefinitions
  SystemContext
  Requirements
    StakeholderNeeds
    SystemRequirements
    SubsystemRequirements
    DerivedRequirements
  Architecture
    LogicalArchitecture
    PhysicalArchitecture
    Interfaces
    Behaviors
  Configurations
    AsSpecified
    AsDesigned
    AsBuilt
    TestArticles
  Analysis
    TradeStudies
    Budgets
    PerformanceAnalyses
  Verification
    VerificationCases
    VerificationProcedures
    VerificationResources
    VerificationResults
  Views_Viewpoints
    RequirementTraceViews
    VerificationTraceViews
    ArchitectureViews
```

The official SysML v2 examples use a similar separation between definitions,
vehicle configurations, analysis, verification, individuals, and views. That
pattern is a useful baseline for project models.

## Core Organization Rules

Separate definitions from usages. Put reusable `part def`, `item def`,
`port def`, `interface def`, `action def`, `requirement def`, and
`verification def` elements under `Definitions`. Put actual system structures,
configured systems, test articles, and scenario-specific model content in
`Architecture`, `Configurations`, `Analysis`, and `Verification`.

Give every requirement a clear subject. A requirement that does not identify the
system, subsystem, interface, behavior, or attribute it constrains is difficult
to satisfy or verify consistently.

Model satisfaction separately from verification. A satisfaction relationship is
the design claim that an architecture element meets a requirement. A
verification case is the method for checking whether that claim holds.

Verify concrete configurations where possible. A verification case should
usually bind to an actual system configuration, subsystem usage, simulation
configuration, prototype, or test article rather than only an abstract
definition.

Keep verification method and evidence explicit. Verification cases should carry
the intended method, such as inspection, analysis, demonstration, or test.
Evidence such as test reports, simulation outputs, review records, and lab data
can remain external, but it should be traceable from verification results.

Use views and viewpoints for stakeholder review. Requirement trace matrices,
verification coverage views, interface views, and architecture review products
should be generated from model relationships.

## Requirement Setup

Organize requirements by level and derivation path:

```text
Requirements
  StakeholderNeeds
  SystemRequirements
  SubsystemRequirements
  DerivedRequirements
```

Recommended practices:

- Decompose requirements into nested or related subrequirements when the parent
  requirement has independently verifiable parts.
- Bind each requirement to a subject that names what the requirement constrains.
- Avoid requirements that combine unrelated concerns, since they create unclear
  verification ownership.
- Capture derived requirements separately enough that reviewers can distinguish
  externally imposed needs from internally derived design constraints.
- Maintain stable identifiers in metadata or naming conventions if the model is
  exchanged across tools.

## Architecture Setup

Architecture packages should contain the elements expected to satisfy
requirements:

```text
Architecture
  LogicalArchitecture
  PhysicalArchitecture
  Interfaces
  Behaviors
```

Recommended practices:

- Use logical architecture for functional decomposition and allocation choices
  that may precede physical design.
- Use physical architecture for concrete parts, subsystems, ports, connections,
  and interfaces.
- Keep behavior models close to the structural elements that perform them, but
  maintain enough package separation that behavior can be reviewed independently.
- Make interface definitions reusable and explicit, since interface
  requirements often need independent verification.
- Use satisfaction relationships from architecture elements to requirements
  rather than embedding requirement intent only in names or comments.

## Configuration Setup

Verification needs configuration control. Model the difference between what is
specified, designed, built, and tested:

```text
Configurations
  AsSpecified
  AsDesigned
  AsBuilt
  TestArticles
```

Recommended practices:

- Treat configurations as first-class model elements when verification depends
  on product variant, build state, operational mode, or test setup.
- Bind verification case subjects to these configurations when possible.
- Keep test article structure explicit enough to identify deviations from the
  intended system design.
- Preserve enough configuration metadata to reproduce a verification result.

## Analysis Setup

Use analysis models as early verification aids:

```text
Analysis
  TradeStudies
  Budgets
  PerformanceAnalyses
```

Recommended practices:

- Link analysis cases to the requirements they evaluate.
- Link analysis inputs to the architecture or configuration elements that
  provide those values.
- Treat budgets, margins, simulations, and trade studies as model elements when
  they support requirement satisfaction or verification claims.
- Distinguish analysis assumptions from verified system properties.

## Verification Setup

Organize verification around reusable verification definitions, concrete
verification cases, resources, procedures, and results:

```text
Verification
  VerificationCases
  VerificationProcedures
  VerificationResources
  VerificationResults
```

Recommended practices:

- Create one verification case per independently checkable verification
  objective.
- Link each verification case to the requirement or requirement set it verifies.
- Bind each verification case to a verification subject, preferably a concrete
  configuration, test article, subsystem usage, or simulation configuration.
- Record the verification method as explicit metadata or model structure.
- Capture verdicts using the SysML v2 result concepts where supported by the
  tool: pass, fail, inconclusive, or error.
- Link evidence artifacts from verification results instead of burying evidence
  in free text.

## MDA Methodology Alignment

Model Driven Architecture (MDA) concepts can be applied to SysML v2 models as a
methodology for separating concerns and governing transformations. SysML v2
should not be treated as just a UML-profile MDA workflow, but the MDA layering
pattern is useful for organizing system models.

Recommended interpretation:

```text
MDA CIM  -> mission context, stakeholder concerns, operational scenarios, needs
MDA PIM  -> logical system architecture, behavior, interfaces, requirements,
            analyses, and verification intent
MDA PSM  -> concrete hardware, software, tools, protocols, part selections,
            deployment, test articles, and implementation constraints
Artifacts -> generated analysis inputs, code, HDL, test procedures, reports,
             evidence records, and external data products
```

Recommended practices:

- Keep stakeholder needs and operational scenarios independent of specific
  hardware, software, tools, or vendors.
- Keep logical architecture and requirements separate from implementation
  configurations when possible.
- Treat concrete configurations, selected parts, software stacks, protocols,
  test equipment, and deployment choices as platform-specific model content.
- Use transformations, scripts, APIs, or tool adapters to generate analysis
  inputs, implementation artifacts, and verification assets from the model.
- Preserve trace links from generated or external artifacts back to the
  requirements, architecture elements, analysis cases, and verification cases
  that justified them.
- Make transformation assumptions explicit so generated artifacts can be
  reviewed, reproduced, and verified.

## Traceability Checklist

Use this checklist during model reviews:

- Every stakeholder need traces to one or more requirements.
- Every requirement has a subject.
- Every system or subsystem requirement is satisfied by at least one
  architecture or configuration element.
- Every requirement that must be verified is linked to at least one verification
  or analysis case.
- Every verification case has a verification subject.
- Every verification case identifies a method.
- Every executed verification has a verdict.
- Every verdict has traceable evidence or a reference to the external evidence
  record.
- Failed or inconclusive verification results remain visible in review views.
- Views are generated from relationships rather than maintained as disconnected
  diagrams.

## Review Views

Recommended views and matrices:

- Stakeholder need to requirement trace.
- Requirement decomposition tree.
- Requirement to satisfying architecture element matrix.
- Requirement to verification case matrix.
- Verification case to test article or configuration matrix.
- Verification status by requirement.
- Failed, inconclusive, or missing verification results.
- Interface requirements and interface verification coverage.
- Safety, mission-critical, or high-risk requirement verification coverage.

## Tooling Notes

For this local MBSE lab, treat Flexo MMS as the durable API-backed repository
path and SysON as the graphical review and editing surface. Preserve textual
`.sysml` snapshots and JSON exports when moving model content between tools.

The bridge currently supports a practical subset of SysML v2 elements. If a
verification workflow depends on unsupported element types, keep the source JSON
export and extend the renderer before relying on the textual import as the only
representation.
