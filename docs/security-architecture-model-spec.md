# Security Architecture SysML v2 Model Specification

This document specifies the intended SysML v2 model for security architecture
modeling. The model is aligned conceptually with the OMG Unified Architecture
Framework (UAF) Security viewpoint and with systems security engineering
practices such as NIST SP 800-160, NIST SP 800-53, and the NIST Cybersecurity
Framework.

The model is intended to support security architecture definition, asset and
enclave modeling, security requirements, control allocation, threat and risk
analysis, security verification, and evidence traceability.

The model should be useful as both:

- A semantic MBSE model that captures assets, data flows, enclaves, controls,
  risks, threats, mitigations, security requirements, and verification evidence.
- An executable or tool-assisted assurance model that can drive control coverage
  analysis, risk analysis, interface checks, deployment checks, and security
  verification workflows.

## Goals

- Represent security-relevant assets, data, interfaces, exchanges, enclaves,
  boundaries, controls, risks, threats, and mitigations.
- Align SysML v2 views and model elements with the intent of UAF Security view
  specifications.
- Trace security concerns to requirements, architecture elements, controls,
  analysis cases, verification cases, and evidence.
- Support security architecture modeling for system, software, hardware,
  deployment, and operational contexts.
- Support control frameworks such as NIST SP 800-53 without hard-coding the
  model to one framework.
- Preserve enough structure to generate security views, control matrices, risk
  registers, verification plans, and evidence reports.

## Non-Goals

- This model will not replace threat modeling tools, vulnerability scanners,
  GRC platforms, SIEM tools, penetration testing, or authorization packages.
- This model will not claim conformance to UAF unless a separate UAF-conformant
  implementation is built and verified.
- This model will not initially model every NIST SP 800-53 control, control
  enhancement, assessment objective, or assessment method.
- This model will not store secret values, credentials, keys, or exploit
  details that should remain outside the engineering model.

## References

- OMG UAF specification page: <https://www.omg.org/spec/UAF>
- OMG UAF v1.3 Domain Metamodel PDF:
  <https://www.omg.org/spec/UAF/1.3/DMM/PDF>
- OMG UAF overview: <https://www.omg.org/uaf/>
- OMG SysML v2 specification: <https://www.omg.org/spec/SysML>
- OMG SysML v2 Language specification PDF:
  <https://www.omg.org/spec/SysML/2.0/Language/PDF>
- OMG KerML specification: <https://www.omg.org/spec/KerML/1.0>
- NIST SP 800-160 Vol. 1, Systems Security Engineering:
  <https://www.nist.gov/privacy-framework/nist-sp-800-160-vol-1>
- NIST SP 800-53 Rev. 5, Security and Privacy Controls:
  <https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final>
- NIST Cybersecurity Framework 2.0:
  <https://www.nist.gov/publications/nist-cybersecurity-framework-csf-20>
- Local verification model setup guide:
  `docs/sysml-v2-verification-model-setup.md`
- Local transformation pipeline design:
  `docs/sysml-v2-transformation-pipeline-design.md`
- Local container deployment model spec:
  `docs/container-deployment-model-spec.md`

## UAF Security Alignment

UAF Security should be treated as the viewpoint taxonomy for this model. SysML
v2 should be treated as the implementation language for precise architecture,
requirements, analysis, and verification modeling.

Recommended concept mapping:

```text
UAF concept                          SysML v2 model concept
Security Asset                       SecurityAsset, protected part, protected item
Security Enclave                     SecurityEnclave, trust zone, deployment boundary
Security Category                    SecurityCategory metadata or CIA impact attributes
Security Classification              SecurityClassification metadata
Security Constraint                  SecurityRequirement or SecurityConstraint
SubjectOfSecurityConstraint          Asset, exchange, interface, service, process, data item
Security Control                     SecurityControl or SecurityMitigation
Security Process                     SecurityProcess action or behavior
Security Risk                        SecurityRisk item or risk record
Operational Mitigation               OperationalSecurityMitigation
Resource Mitigation                  ResourceSecurityMitigation
Security Connectivity                ports, interfaces, connections, exchanges, item flows
Security Structure                   assets, enclaves, resources, information, data stores
Security Traceability                satisfy, verify, allocate, dependency, evidence links
```

The model should support UAF-style security questions:

- What assets need protection?
- Where are assets processed, stored, and transmitted?
- Which enclaves or trust zones contain those assets?
- Which exchanges cross security boundaries?
- What constraints, policies, classifications, or caveats apply?
- Which controls or mitigations apply to each asset or exchange?
- Which risks affect which assets?
- Which controls mitigate which risks?
- Which requirements and verification cases prove the controls are effective?

## Security View Specifications

The model should provide SysML v2 views aligned to the major UAF Security views.

```text
SecurityTaxonomyView
  Defines assets, security categories, classifications, controls, risks,
  mitigations, and enclaves.

SecurityStructureView
  Shows allocation of assets to systems, data stores, resources, and enclaves.

SecurityConnectivityView
  Shows security-relevant exchanges across ports, interfaces, resources,
  performers, enclaves, and trust boundaries.

SecurityProcessesView
  Shows actions and processes that implement or enforce controls.

SecurityConstraintsView
  Shows policies, rules, requirements, constraints, classifications, caveats,
  risk statements, and control applicability.

SecurityTraceabilityView
  Shows trace from concerns to requirements, controls, assets, risks,
  mitigations, verification cases, and evidence.
```

## MDA Methodology Alignment

This model should use Model Driven Architecture concepts as a layering pattern:

```text
CIM-like layer
  Mission, enterprise, operational, stakeholder, threat, regulatory, and
  assurance concerns.

PIM-like layer
  Abstract assets, trust boundaries, security categories, risks, controls,
  policies, requirements, analysis cases, and verification intent independent
  of a specific implementation platform.

PSM-like layer
  Specific deployment, services, interfaces, protocols, container stacks,
  identity provider, data stores, control implementations, scanners, tests,
  audit artifacts, and operational procedures.

Generated and evidence artifacts
  Control coverage matrices, risk registers, data-flow reports, security test
  results, scan results, audit logs, authorization evidence, and verification
  reports.
```

The model should preserve traceability across these layers so a security
concern can be followed to the security architecture, the concrete implementation
controls, the verification execution, and the evidence used for assurance.

## Model Boundary

The model covers security architecture concerns:

```text
stakeholder and security concerns
  -> protected assets and data
  -> security categories and classifications
  -> enclaves and trust boundaries
  -> interfaces and exchanges
  -> threats, vulnerabilities, and risks
  -> controls and mitigations
  -> security requirements
  -> analysis and verification cases
  -> evidence records
```

The model should expose the following primary outputs:

- Asset inventory and security categorization.
- Security enclave and boundary model.
- Security-relevant connectivity and data-flow model.
- Risk and mitigation trace.
- Control allocation and coverage.
- Security requirement satisfaction.
- Security verification status.
- Evidence coverage status.

## Recommended Package Structure

```text
SecurityArchitectureModel
  Libraries
    Security
    Controls
    Risk
    Evidence
  Metadata
  Stakeholders_Concerns
    SecurityStakeholders
    SecurityConcerns
    AssuranceConcerns
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
    SecurityRequirements
    PolicyRequirements
    ControlRequirements
    AssuranceRequirements
  Architecture
    AssetArchitecture
    EnclaveArchitecture
    SecurityConnectivity
    SecurityProcesses
    ControlArchitecture
  Configurations
    AsSpecified
    AsDesigned
    AsDeployed
    AsAssessed
  Analysis
    ThreatAnalysisCases
    RiskAnalysisCases
    ControlCoverageAnalysisCases
    BoundaryAnalysisCases
  Verification
    SecurityVerificationCases
    ControlAssessmentCases
    EvidenceRecords
  Views_Viewpoints
    SecurityTaxonomyViews
    SecurityStructureViews
    SecurityConnectivityViews
    SecurityProcessViews
    SecurityConstraintViews
    SecurityTraceabilityViews
```

## Core Definitions

The model should define reusable security types under `Definitions`.

```text
SecurityAsset
InformationAsset
DataAsset
ServiceAsset
SoftwareAsset
HardwareAsset
DeploymentAsset
CredentialAsset
SecurityEnclave
TrustBoundary
SecurityCategory
SecurityClassification
SecurityConstraint
SecurityControl
SecurityMitigation
SecurityRisk
Threat
Vulnerability
AttackPath
SecurityProcess
EvidenceRecord
ControlAssessment
```

### SecurityAsset

Expected attributes:

- `assetId`
- `assetName`
- `assetType`
- `owner`
- `missionImpact`
- `confidentialityImpact`
- `integrityImpact`
- `availabilityImpact`
- `classification`
- `dataSensitivity`
- `protectionRequired`

### SecurityEnclave

Expected attributes:

- `enclaveName`
- `boundaryType`
- `trustLevel`
- `owner`
- `allowedIngress`
- `allowedEgress`
- `monitoringRequired`
- `authenticationRequired`
- `authorizationRequired`

### SecurityControl

Expected attributes:

- `controlId`
- `controlName`
- `controlFamily`
- `framework`
- `controlTextReference`
- `implementationStatus`
- `responsibleOwner`
- `assessmentMethod`
- `evidenceRequired`

### SecurityRisk

Expected attributes:

- `riskId`
- `riskStatement`
- `affectedAsset`
- `threat`
- `vulnerability`
- `likelihood`
- `impact`
- `riskLevel`
- `riskOwner`
- `riskTreatment`
- `residualRisk`

### SecurityMitigation

Expected attributes:

- `mitigationId`
- `mitigationName`
- `mitigatedRisk`
- `implementedBy`
- `controlReference`
- `effectiveness`
- `verificationStatus`

### EvidenceRecord

Expected attributes:

- `evidenceId`
- `evidenceType`
- `source`
- `collectionMethod`
- `timestamp`
- `reviewStatus`
- `linkedRequirement`
- `linkedControl`
- `linkedVerificationCase`

## Security Categories and Impact

The model should support confidentiality, integrity, and availability impact
ratings for assets and exchanges.

Initial impact values:

```text
low
moderate
high
notApplicable
unknown
```

Recommended representation:

```text
SecurityCategory
  confidentialityImpact
  integrityImpact
  availabilityImpact
```

This follows the UAF SecurityCategory concept, where security category captures
the potential impact for confidentiality, integrity, and availability.

## Architecture Model

The architecture package should show assets, boundaries, data stores, services,
interfaces, and controls.

Minimum structural model:

```text
SecurityArchitecture
  part protectedSystem
  part securityEnclaves : SecurityEnclave[0..*]
  part securityAssets : SecurityAsset[0..*]
  part controls : SecurityControl[0..*]
  part mitigations : SecurityMitigation[0..*]
  part risks : SecurityRisk[0..*]
```

Security connectivity should represent exchanges explicitly:

```text
SecurityExchange
  source
  destination
  conveyedAsset
  protocol
  classification
  securityCategory
  boundaryCrossed
  requiredControls
```

## Requirements

Requirements should be organized by security objective and should use
`SecurityAsset`, `SecurityEnclave`, `SecurityExchange`, `SecurityControl`, or
concrete system elements as their subjects.

Initial requirements:

```text
AssetCategorizationRequired
BoundaryProtectionRequired
AuthenticationRequired
AuthorizationRequired
EncryptionInTransitRequired
EncryptionAtRestRequired
AuditLoggingRequired
BackupProtectionRequired
CredentialProtectionRequired
ControlEvidenceRequired
RiskMitigationRequired
SecurityVerificationRequired
```

Example requirement intent:

```text
EncryptionInTransitRequired
  subject: SecurityExchange
  constraint: exchanges carrying protected data across trust boundaries use an
              approved protection mechanism.

CredentialProtectionRequired
  subject: CredentialAsset
  constraint: credential values are not committed to source control and are
              supplied through approved runtime mechanisms.

ControlEvidenceRequired
  subject: SecurityControl
  constraint: implemented controls have linked evidence records.
```

## Analysis Cases

Analysis cases are the main place to evaluate security coverage before formal
verification.

Required analysis cases:

```text
AssetCategorizationAnalysis
SecurityBoundaryAnalysis
SecurityConnectivityAnalysis
ControlCoverageAnalysis
ThreatCoverageAnalysis
RiskExposureAnalysis
EvidenceCoverageAnalysis
CredentialExposureAnalysis
```

Each analysis case should have:

- A subject, usually a configured system, deployment, enclave, asset, or
  exchange.
- Explicit input parameters or bindings to model attributes.
- Returned outputs for coverage, risk, or compliance status.
- A status indicating whether the analysis completed and whether assumptions
  are valid.

## Verification Cases

Verification cases should consume analysis results, inspection results, test
results, scan outputs, audit logs, or assessment evidence and return a verdict.
Use the SysML v2 verification result concepts where supported by the tool:
`pass`, `fail`, `inconclusive`, or `error`.

Required verification cases:

```text
VerifyAssetCategorizationComplete
VerifyBoundaryControlsAllocated
VerifyCredentialProtection
VerifyEncryptionInTransit
VerifyEncryptionAtRest
VerifyAuditLogging
VerifyBackupProtection
VerifyControlEvidenceExists
VerifyRiskMitigationsLinked
```

Each verification case should link to:

- The requirement being verified.
- The asset, enclave, exchange, control, or deployment used as the verification
  subject.
- The analysis, inspection, test, scan, audit, or assessment evidence used to
  make the decision.
- The verdict.
- The evidence artifact or result record.

## Local MBSE Lab Security Application

The first concrete application should align this model with the local container
deployment model.

Candidate security assets:

```text
Flexo model repository graph
Flexo SysML v2 API
Flexo Layer1 API
Fuseki dataset
MinIO object data
LDAP user accounts
JWT signing material
SysON project database
Runtime credential files
Backup files
Generated SysML and JSON exports
```

Candidate enclaves:

```text
LocalHost
FlexoMMSNetwork
SysONNetwork
HostFilesystem
BrowserClient
ExternalAnalysisScripts
```

Candidate security requirements:

```text
Runtime credentials shall not be committed to git.
Model repository data shall be persisted and backed up.
Backups shall be protected as sensitive engineering data.
Only required service ports shall be exposed on localhost.
SysML v2 API access shall be reachable only through approved local ports.
Generated exports containing model data shall be treated as controlled artifacts.
```

Candidate verification checks:

```bash
git check-ignore deploy/flexo-mms/.env
git check-ignore 'deploy/flexo-mms/env/flexo-mms-jwt.env'
git check-ignore deploy/syson/.env
python3 scripts/flexo_mms_env.py status --with-sysmlv2 --strict
python3 scripts/flexo_mms_env.py backup
docker compose -f deploy/syson/docker-compose.yml ps
```

## Transformation and Executability Approach

SysML v2 should express the security architecture, requirements, analysis, and
verification intent. External tools should execute checks and produce evidence.

Recommended pipeline:

```text
SysML v2 security architecture
  -> security analysis input
  -> control coverage / risk / deployment check execution
  -> structured security result JSON
  -> analysis or verification result
  -> linked evidence
```

Potential transformation directions:

```text
container deployment model -> security asset and boundary model
security architecture model -> control coverage matrix
security architecture model -> verification checklist
verification output -> SysML v2 evidence record
```

## External Execution Interface

If external execution is used, the script or tool adapter should accept a
configuration record with these inputs:

```text
securityModelId
configurationId
assets[]
  assetId
  assetType
  owner
  confidentialityImpact
  integrityImpact
  availabilityImpact
enclaves[]
  enclaveId
  trustLevel
  boundaryType
exchanges[]
  exchangeId
  source
  destination
  conveyedAsset
  protocol
  boundaryCrossed
controls[]
  controlId
  framework
  implementationStatus
  allocatedTo
risks[]
  riskId
  affectedAsset
  likelihood
  impact
  mitigations
checks[]
  checkName
  method
  commandOrUrl
  expectedResult
```

Expected outputs:

```text
securityModelId
configurationId
executionTimestamp
assetCoverageResults[]
boundaryCheckResults[]
controlCoverageResults[]
riskCoverageResults[]
evidenceCoverageResults[]
verificationVerdicts[]
overallStatus
messages
```

## Traceability Checklist

- Every security concern traces to one or more security requirements.
- Every security requirement has a subject.
- Every protected asset has a security category or impact rating.
- Every data flow crossing a trust boundary is represented.
- Every security risk is linked to an affected asset.
- Every risk has a treatment decision or mitigation.
- Every mitigation is linked to a control or architectural element.
- Every implemented control has verification evidence.
- Every verification case identifies the evidence it uses.
- Failed or inconclusive security checks remain visible in review views.

## Initial Review Views

The model should support these review views:

- Security asset inventory.
- Security category and classification table.
- Security enclave and boundary view.
- Security connectivity and data-flow view.
- Control allocation matrix.
- Risk to mitigation trace.
- Requirement to control trace.
- Control to evidence trace.
- Verification status by security requirement.
- Failed or missing security verification results.

## Open Design Decisions

- Whether to model NIST SP 800-53 controls as imported library elements,
  external references, or a small curated local subset.
- Whether to model threats using a generic threat library or align to a specific
  framework such as MITRE ATT&CK or CAPEC later.
- Whether the first implementation should focus on the local container
  deployment, RF systems, CCA systems, or all of them.
- Whether security evidence should be stored as SysML v2 elements or external
  files linked from verification results.
- How to preserve security classification and sensitivity markings when model
  artifacts are exported across tools.
