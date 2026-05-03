# Execution Plans

Use this directory for work that is too large to rely on chat history alone.

```text
docs/plans/proposals/    Feature pre-plans before implementation starts
docs/plans/active/       Plans currently being executed
docs/plans/completed/    Completed plans with final decisions and validation
```

Use [Feature Proposals](proposals/README.md) before work that changes CLI
workflow shape, data or credential handling, bridge behavior, service lifecycle,
release gates, or public documentation structure. A proposal decides whether the
feature is worth doing, what is out of scope, and what evidence will prove it is
done.

Use active execution plans after a feature is accepted and the work is large
enough to need durable implementation memory. Each active plan should include:

- objective
- relevant files
- planned steps
- progress log
- validation commands
- decisions and tradeoffs
- follow-up debt

Small changes do not need a checked-in proposal or plan. Large bridge changes,
persistence changes, credential handling changes, live-service workflow changes,
and roadmap-changing documentation work should use one.

## Proposals

- [Feature Proposals](proposals/README.md)
- [Feature Pre-Plan Template](proposals/feature-preplan-template.md)

## Active Plans

- [MVP Feature Catalog](active/mvp-feature-catalog.md)
- [MBSE Lab SysML Model](active/mbse-lab-sysml-model-plan.md)
- [SysML JSON Rendering Reuse Spike](active/sysml-json-rendering-reuse-spike.md)
- [Usability Remediation](active/usability-remediation.md)

## Completed Plans

- [OpenMBEE View Editor Flexo Experiment](completed/openmbee-view-editor-flexo-experiment.md)
