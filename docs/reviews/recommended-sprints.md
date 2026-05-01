# Recommended Sprint Sequence

I’d treat the current sprint as the **foundation sprint**, then sequence the next work so each sprint produces a visible workflow improvement and leaves behind testable evidence.

Current state I see: sprint issue #18 is scoped around first-use hardening, with #9 checked off and #10, #11, #12, and #14 still listed as the remaining selected issues in the sprint plan. Its done criteria require the selected issues to be closed or carried over, the demo script to pass or have linked blockers, docs/tests to be updated, and `make check` to pass.  There is also an open draft PR #35 targeting `develop` that claims implementation for #10, #11, #12, and #14, with `make check` steps passing 79 tests, but it is still draft/open/unmerged.  PR #34 already merged into `develop` and appears to have covered #9 plus some extra safety-related work such as share-check hardening, public-safe diagnostics, and repo-local export fallback warnings.

## Post-sprint-1 landing checklist

Before starting Sprint 2, I would do this cleanup pass:

1. Merge PR #35 after review, or split if any part is too broad.
2. Update issue #18 so the checklist reflects reality.
3. Close #10, #11, #12, and #14 if PR #35 satisfies their acceptance criteria. PR #35 does not appear to use GitHub closing keywords in the body, so these may not auto-close.
4. Reconcile overlap from PR #34 against #26 and #27. Since PR #34 says it already added share-check hardening and public-safe diagnostics, those issues may need to be closed, narrowed, or converted into follow-up gaps rather than implemented from scratch.
5. Run the #18 demo script once as the acceptance gate.

After that, I would move into this sprint sequence.

---

# Sprint 2: First-Use Success Path

## Goal

Turn the hardened first-use mechanics into a clear, beginner-friendly path from clone to “I created and imported a model.”

## Recommended issues

Primary:

* #8 — Add first-use smoke workflow for bootstrap-to-import validation
* #24 — Add readiness waits for SysON and Flexo APIs
* #21 — Make bootstrap final next step point to first-model
* #19 — Add five-minute quickstart to README
* #20 — Add “Which command should I run?” table

Stretch:

* #23 — Add troubleshooting-by-symptom page

## Why this sprint next

Sprint 1 hardens the pieces. Sprint 2 should make the workflow obvious and reliable. #8 gives you the one-command proof path, #24 reduces “container is up but API is not ready” confusion, and #19/#20/#21 make the repo’s entry point much easier to follow.

## Expected user-visible outcome

A new user can follow one README section and run a first-use validation workflow without piecing together commands from multiple docs pages.

## Acceptance criteria

* `mbse-lab smoke first-use` or equivalent has dry-run and live modes.
* `mbse-lab bootstrap` ends by pointing to `mbse-lab first-model "My First Model"`.
* `bootstrap` and `services up` wait for Flexo/SysON API readiness, not only container startup.
* README has a five-minute quickstart and command decision table.
* `first-model` gives a clear error if services are not reachable.
* Deterministic tests cover readiness wait behavior without live Docker.
* `make check` passes.

## Demo script

These demo scripts are target-state examples for the proposed sprint work, not
a current CLI reference.

```text
python3 -m pip install -e .
mbse-lab bootstrap --dry-run --model-workspace ~/work/mbse-demo-models
mbse-lab bootstrap --model-workspace ~/work/mbse-demo-models
export MBSE_MODEL_WORKSPACE=~/work/mbse-demo-models
mbse-lab smoke first-use --json-output
mbse-lab report
mbse-lab share-check
```

## Board grouping

Use a project section or custom field value like:

`Sprint 2 — First-Use Success Path`

---

# Sprint 3: Public/Private Safety Gates

## Goal

Make it much harder for private model state, service data, generated artifacts, or diagnostics to leak into the public tooling repo.

## Recommended issues

Primary:

* #25 — Stop updating tracked `cluster.trig` by default during backup
* #26 — Expand share-check to block tracked model artifacts
* #27 — Add public-safe diagnostics mode
* #28 — Add tests for share-check safety gaps

But because PR #34 already claims some share-check/public-safe diagnostics work, start Sprint 3 with a one-hour audit of #26/#27/#28 against what PR #34 actually landed.

## Why this sprint after onboarding

Once users can succeed quickly, the next highest risk is accidental publication of private artifacts. #25 is especially important because the issue identifies a path where live Flexo graph state can be written into a tracked startup seed. That is exactly the sort of public/private boundary risk this repo should treat as first-class.

## Expected user-visible outcome

Users can run backups, diagnostics, bridge exports, and share checks with much stronger confidence that private data is either ignored, redacted, or explicitly blocked.

## Acceptance criteria

* Default Flexo backup writes ignored backup files only.
* Updating tracked `deploy/flexo-mms/mount/cluster.trig` requires an explicit high-intent flag or separate command.
* `share-check` catches tracked generated exports, tracked `.sysml`, tracked `.nq`/`.trig` outside allowlists, and dirty tracked seed files.
* Public-safe diagnostics omits or hashes project names, IDs, private artifact paths, and import logs by default.
* Tests use temporary repos and do not require live services.
* Curated public fixtures/examples remain possible through an explicit allowlist.

## Demo script

```text
mbse-lab diagnostics --public-safe
mbse-lab share-check
python3 scripts/flexo_mms_env.py backup
git status --short
```

Expected: diagnostics are reduced/public-safe, `share-check` passes, and backup does not dirty tracked seed files by default.

## Board grouping

`Sprint 3 — Public/Private Safety Gates`

---

# Sprint 4: Bridge Evidence and Coverage

## Goal

Make the bridge honest and inspectable: users should know what rendered, what was skipped, and how much confidence to place in the SysON import.

## Recommended issues

Primary:

* #13 — Add render coverage report for supported and unsupported SysML elements
* #17 — Add SysML v2 bridge coverage matrix
* #16 — Include latest bridge run artifacts in lab report

Stretch:

* #31 — Add fixture coverage for more SysML v2 element types

## Why this sprint here

#13 depends on #11, which is part of Sprint 1. Once private workspace preflight lands, it is safe to add more generated bridge evidence. #16 and #17 both depend on #13, so they belong in the same theme but should be ordered carefully: first render report, then coverage matrix, then report integration.

## Expected user-visible outcome

A bridge run no longer just produces `.json` and `.sysml`; it also produces an evidence trail that says what happened.

## Acceptance criteria

* `render-sysml` or `bridge run` can produce `render-report.json`.
* Report includes counts by Flexo `@type`: rendered, skipped, unsupported.
* Unsupported elements appear in warnings.
* `mbse-lab report` links latest bridge run artifacts without embedding private model content.
* Coverage matrix maps supported element types to textual form, fixture coverage, and validation status.
* Tests cover all fixture reports deterministically.

## Demo script

```text
mbse-lab bridge render evals/fixtures/rf-link-budget-basic.json --report
mbse-lab report
```

Expected: rendered `.sysml`, render coverage report, and lab report all agree on bridge coverage.

## Board grouping

`Sprint 4 — Bridge Evidence and Coverage`

---

# Sprint 5: Routine Bridge Workflow and Live Confidence

## Goal

Make the bridge easier to use for routine local work and prove it through a repeatable live validation path.

## Recommended issues

Primary:

* #30 — Add bridge auto-create SysON review project option
* #15 — Add manual live-smoke GitHub Action

Stretch:

* Additional live import coverage from #31, if Sprint 4 does not absorb it.

## Why this sprint after bridge evidence

The bridge should not get more convenient until it is also more transparent. Once render coverage exists, #30 can safely simplify the workflow by auto-creating a SysON review project and importing into its root namespace. #15 then gives maintainers repeatable live validation of the first-use and bridge workflows.

## Expected user-visible outcome

A user with a Flexo project ID can run one bridge command and get a SysON review project without manually creating a SysON project or discovering namespace IDs.

## Acceptance criteria

* `mbse-lab bridge run <flexo-project-id> --create-syson-project "Imported From Flexo"` works.
* Command output includes Flexo project ID, SysON project ID, namespace/root ID, artifact paths, render report path, and SysON URL.
* Dry-run shows the planned sequence.
* Manual `workflow_dispatch` GitHub Action starts services, runs first-use smoke/live evals, and uploads diagnostics on failure.
* Release docs reference the live-smoke workflow.

## Demo script

```text
mbse-lab bridge run <flexo-project-id> \
  --create-syson-project "Imported From Flexo" \
  --json-output

mbse-lab report
```

## Board grouping

`Sprint 5 — Routine Bridge and Live Confidence`

---

# Sprint 6: Documentation System and CLI Reference

## Goal

Make docs easier to navigate and harder to drift from implementation.

## Recommended issues

Primary:

* #22 — Split README details into task-oriented docs pages
* #23 — Add troubleshooting-by-symptom page, if not completed earlier
* #29 — Generate and validate CLI reference docs

## Why this sprint here

By Sprint 6, the command surface will have changed materially: smoke workflow, readiness waits, safer backup behavior, public-safe diagnostics, render reports, bridge auto-create, and maybe live-smoke CI. That is the right time to reorganize docs and generate/reference-check CLI help.

## Expected user-visible outcome

README becomes a concise entry point, while detailed task docs cover setup, services, bridge, safety, diagnostics, troubleshooting, and CLI reference.

## Acceptance criteria

* README focuses on identity, quickstart, first model, common commands, safety boundary, bridge scope, and docs links.
* Detailed docs pages exist and are linked from MkDocs navigation.
* CLI reference is generated or mechanically validated from Click command help.
* CI fails if CLI reference/docs drift.
* Troubleshooting page is symptom-oriented and links to doctor/remediation codes.

## Demo script

```text
make docs-check
make docs-build
mbse-lab --help
```

Expected: docs build strictly, CLI reference is current, and README is shorter.

## Board grouping

`Sprint 6 — Docs and CLI Reference`

---

# Sprint 7: Maintainer-Friendly Bridge Architecture

## Goal

Refactor only after user-facing behavior is stabilized and covered by tests.

## Recommended issues

Primary:

* #32 — Refactor bridge script into package modules
* #33 — Add typed data contracts for bridge and deployment reports

## Why this should wait

The bridge script is doing too much, but refactoring before coverage/reporting is in place would create churn without enough safety. By this point, render reports, coverage matrix, live smoke, and CLI docs should provide a much better regression net.

## Expected maintainer-visible outcome

Bridge logic moves out of the monolithic script into package modules, with typed/validated data contracts for snapshots, render reports, run logs, deployment contracts, and verification reports.

## Acceptance criteria

* `scripts/flexo_syson_bridge.py` remains callable as a compatibility shim.
* Core logic lives in package modules.
* Tests import package modules directly.
* Existing JSON output schemas remain stable or changes are documented.
* Malformed input tests cover bridge/deployment contracts.
* No broad behavior changes are introduced in the refactor.

## Board grouping

`Sprint 7 — Maintainer Architecture`

---

## Recommended project board structure

For the GitHub Project, I’d use these fields:

| Field     | Suggested values                                                              |
| --------- | ----------------------------------------------------------------------------- |
| Sprint    | Current, Sprint 2, Sprint 3, Sprint 4, Sprint 5, Sprint 6, Sprint 7, Backlog  |
| Theme     | Onboarding, Safety, Bridge, Diagnostics, Docs, CI, Architecture               |
| Risk type | Data safety, Service fragility, Docs drift, False confidence, Maintainability |
| Effort    | Small, Medium, Large                                                          |
| Gate      | `make check`, `make docs-build`, live smoke, share-check, manual demo         |
| Status    | Backlog, Ready, In progress, Review, Blocked, Done                            |

I would also keep one issue per sprint plan, like #18, rather than relying only on individual feature issues. That gives you a clean place to track sprint goal, selected issues, demo script, done criteria, and carry-over.

## Suggested sprint-plan issues to create next

Create these after #18 is closed or carried over:

1. `Sprint plan: first-use success path`

   * Issues: #8, #19, #20, #21, #24
   * Stretch: #23

2. `Sprint plan: public/private safety gates`

   * Issues: #25, #26, #27, #28
   * First task: audit overlap from PR #34

3. `Sprint plan: bridge evidence and coverage`

   * Issues: #13, #16, #17
   * Stretch: #31

4. `Sprint plan: routine bridge and live confidence`

   * Issues: #30, #15
   * Stretch: additional fixture/live import coverage

5. `Sprint plan: docs and CLI reference`

   * Issues: #22, #23, #29

6. `Sprint plan: maintainer bridge architecture`

   * Issues: #32, #33

## Dependency map to keep visible

```text
#10 -> #14
#11 -> #13
#13 -> #16
#13 -> #17
#13 -> #31
#8  -> #15
#9  -> #30
#24 supports #8, #15, and #30
#25/#26/#27/#28 form the safety hardening cluster
#32/#33 should wait until #13/#16/#17 are stable
```

## My recommendation for the next sprint after #18

Pick **Sprint 2: First-Use Success Path**.

Reason: Sprint 1 makes the mechanics safer; Sprint 2 converts that into a strong user-facing product moment. It also gives you the right foundation for later live-smoke CI, bridge auto-create, and release demos. The ideal next deliverable is: “Clone repo, run quickstart, wait for readiness, run smoke, see report, share-check passes.”
