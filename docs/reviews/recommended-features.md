# Recommended Features Review

I reviewed the repository files on `main` through the GitHub integration. I did not run Docker or live Flexo/SysON workflows locally, so runtime observations below are based on the repository’s checked-in docs, tests, CI, and the repo’s own recorded MVP validation notes, not a fresh live execution.

## 1. Executive roadmap summary

The best near-term direction is to make `mbse-lab` a **CLI-first, safety-first local SysML v2 lab kit**: a public tooling repo that gives a new user one reliable path from install → bootstrap → health check → first model → bridge import → report → share check.

The repo already has the right identity and many useful pieces: a public tooling boundary, private workspace guidance, Flexo and SysON Compose deployments, an installable `mbse-lab` CLI, bridge workflows, diagnostics, reports, cleanup, deterministic tests, optional live tests, MkDocs docs, and CI. The README explicitly frames this as a reusable lab kit, not a model repository, with Flexo as the durable API/repository path and SysON as the graphical review/import path.

The most valuable next milestone is **Reliable First-Use Experience**. The repo already has `mbse-lab bootstrap`, `doctor`, `services`, and `first-model`, but the first-run experience is still spread across commands and docs, and the repo’s own MVP catalog marks guided bootstrap as only partially verified because it still needs clean-checkout live validation with Docker.

The main usability gap is **proof and guidance around the first successful workflow**. A beginner should not need to infer the correct sequence from README, CLI docs, release notes, and bridge docs.

The main technical gap is **bridge validation depth**. The renderer intentionally supports a conservative SysML v2 subset, and deterministic tests cover useful fixtures, but unsupported element handling is still mostly “not rendered” rather than surfaced as a coverage report that users can act on.

The main data-safety gap is **safe defaults when no private workspace is configured**. The docs strongly recommend `MBSE_MODEL_WORKSPACE`, `.gitignore` excludes generated exports, and `share-check` flags risky generated exports, but bridge defaults still fall back to `exports/` inside the public tooling repo when the environment variable is unset.

## 2. Product direction

### Clearest product identity

`mbse-lab` should be positioned as:

> A safe, reproducible local SysML v2 lab kit for evaluating and experimenting with Flexo MMS, SysON, and conservative bridge workflows, while keeping real model data outside the public tooling repository.

It is not only a lab kit, CLI, deployment wrapper, bridge tool, or docs package. It is all of those as surfaces, but the product identity should be **the safe local lab workflow**, not any single implementation surface. The CLI should be the primary user path; docs should explain and validate it; scripts should remain stable implementation details.

Evidence: the project has an installable `mbse-lab` console script in `pyproject.toml`, CLI docs describe it as the “user-facing command surface,” and the README says the repo provides deployment, setup scripts, bridge workflow, diagnostics, docs, and public synthetic fixtures.

### What it should become over 3–6 months

In 3–6 months, the repo should become a **release-ready local evaluation harness** with:

1. A single first-use smoke workflow that proves the lab is working.
2. Strong private workspace defaults and explicit public-example escape hatches.
3. Machine-readable bridge evidence: rendered/skipped element counts, unsupported type reports, import results, artifact manifests, and run logs.
4. Optional but repeatable live validation for maintainers.
5. Versioned docs and coverage tables that make the supported SysML v2 subset unambiguous.
6. A maintainable bridge architecture that can grow without turning one script into the entire product.

### What it should explicitly not become

It should not try to become:

* A storage repo for real/private SysML v2 models.
* A production Flexo/SysON deployment platform.
* A managed service.
* A full SysML v2 semantic engine.
* A bidirectional live sync layer between Flexo and SysON.
* A promise of full diagram/layout round-trip.
* A general-purpose MBSE modeling repository.

The repo already states that Flexo and SysON are separate repository stacks, the bridge is file/text based, unsupported element types are preserved in Flexo JSON but not rendered, and diagram layout is not round-tripped.

## 3. Target users

| Persona                                             | Goals                                                                    | Likely pain points                                                                 | Missing workflows                                          | Highest-value features                                                       | Not worth prioritizing for them                  |
| --------------------------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------ |
| MBSE beginner evaluating SysML v2                   | Install, start services, create first model, see something in SysON      | Docker setup, service IDs, project/commit/namespace IDs, uncertainty about success | One-command first-use proof; visual “what happened” report | `mbse-lab smoke first-use`, better doctor next steps, example templates      | Plugin architecture, remote profiles             |
| Experienced systems engineer trying local workflows | Run local experiments, preserve data, inspect generated artifacts        | Knowing where artifacts went, avoiding private-data leakage, resetting safely      | Safe private workspace lifecycle, backup/reset guidance    | workspace preflight, report/run-log manifest, backup-first reset             | Full CI internals                                |
| Developer automating transformations                | Export Flexo JSON, render SysML text, import to SysON, inspect failures  | Unsupported element opacity, lack of structured render coverage                    | Machine-readable render/import reports                     | render coverage JSON, fixture coverage matrix, bridge APIs                   | Beginner tutorials                               |
| Maintainer improving Flexo/SysON integration        | Add element mappings, validate importer behavior, diagnose version drift | Live services are fragile; tests may not cover real import behavior                | Repeatable live validation and fixture matrix              | manual/scheduled live smoke workflow, SysON import parser tests              | Model-domain content library                     |
| Technical lead evaluating open-source MBSE tooling  | Determine viability and risk quickly                                     | Hard to know what is proven versus aspirational                                    | Static lab report, demo script, known-limitations table    | first-use report, coverage matrix, release checklist                         | Deep bridge plugin internals                     |
| User handling private model data safely             | Keep real models out of public tooling repo                              | Generated exports defaulting into repo, credentials, logs, reports                 | Safer defaults and pre-share guardrails                    | workspace required/warn mode, stronger share-check, default password warning | Public showcase fixtures beyond minimal examples |

## 4. Current capability assessment

### High-level assessment

**Existing capabilities**

The repo already includes:

* Installable CLI via `mbse-lab`.
* CLI docs for install, completion, doctor, init, bootstrap, services, first-model, workspace, report, cleanup, share-check, Flexo/SysON, bridge, and deployment verification.
* Flexo and SysON Compose environments.
* Private workspace helpers and default export path behavior.
* Share-safety checks for forbidden tracked paths, untracked generated exports, and known secret-like patterns.
* Redacted diagnostics bundle collection.
* Static report generation and cleanup helpers.
* Deterministic bridge/render/CLI tests and optional live Flexo/SysON/deployment tests.
* CI that runs pre-commit, docs build, prepares env files, and runs `make check`.

**Implied but incomplete capabilities**

* Guided first-use exists through `bootstrap` and `first-model`, but clean-checkout live validation is called out as a remaining MVP gap.
* Private workspace safety exists, but bridge defaults still write to repo-local `exports/` when `MBSE_MODEL_WORKSPACE` is unset.
* Documentation validation exists, but `scripts/check_docs.py` validates `make`, `python3`, `docker`, `curl`, `git`, `cp`, and `jq` snippets; it does not appear to validate `mbse-lab ...` command snippets, even though the CLI is now the primary user surface.
* Live evals exist, but CI does not start the full Docker stack on every push. The repo explicitly defers automated full-stack CI.

**Risky or fragile workflows**

* `syson-roots` in `scripts/flexo_syson_bridge.py` appears to call SysON REST roots using the project ID as the commit ID segment, while `src/mbse_lab/model.py` correctly obtains the latest commit before reading roots. That should be unified before users rely on it heavily.
* SysON `.env.example` uses `SYSON_POSTGRES_PASSWORD=change-me`, and docs tell users to set a private password, but `ensure_syson_env` simply copies the example if `.env` is missing.
* Unsupported SysML v2 element types are intentionally not rendered, but users may mistake “import succeeded” for “model fully represented.”

### Capability map

| Area                         | What appears to exist                                                                          | Missing                                          | Fragile/risky                                                                   | Highest-value improvement                                            |
| ---------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Local environment setup      | `mbse-lab init`, `bootstrap`, Flexo env generator, SysON env copy, Make targets                | Single first-use proof command                   | SysON default password copy; bootstrap live validation still partially verified | Add `mbse-lab smoke first-use` and random SysON password generation  |
| Docker service lifecycle     | `services up/down/restart/logs`, Flexo env script, SysON Compose                               | Explicit safe reset flow                         | Users may use `down --volumes` or delete bind mounts                            | Add backup-first reset wizard                                        |
| Flexo MMS workflows          | list/create/export, org init, backup/restore, token                                            | Rich project metadata/reporting                  | Local Fuseki startup dataset requires backup discipline                         | Add first-use/live smoke and report integration                      |
| SysON workflows              | create/list/roots/import through bridge and CLI docs                                           | Robust roots/commit handling                     | `syson-roots` lower-level path appears fragile                                  | Fix roots command to resolve latest commit or accept `--commit-id`   |
| Flexo-to-SysON bridge        | Flexo JSON → SysML text → SysON GraphQL import; run logs documented                            | Coverage report; richer failure explanation      | Unsupported elements silently omitted from text                                 | Add render/import report with skipped element details                |
| SysML textual rendering      | Conservative subset with deterministic fixture tests                                           | Element coverage matrix tied to acceptance tests | False confidence if import succeeds but model is incomplete                     | Add coverage matrix and unsupported warnings                         |
| Private workspace management | `MBSE_MODEL_WORKSPACE`, workspace init/check/env, workspace dirs                               | Stronger preflight when unset                    | Default output can land under repo-local `exports/`                             | Require or warn for private workspace on generated private artifacts |
| Data safety/share checks     | `.gitignore`, `share-check`, forbidden path constants, secret pattern scan                     | Secret scanner coverage and policy mode          | Pattern list is intentionally small                                             | Add safety manifest, default-password checks, and test cases         |
| Diagnostics/troubleshooting  | Redacted diagnostics bundle with command logs, HTTP probes, deployment verification, manifest  | Remediation-oriented summary                     | Diagnostics may collect project names/IDs, albeit redacted for secrets          | Add triage summary and “next action” codes                           |
| Reporting                    | Markdown/HTML/JSON report with doctor/status/share/diagnostics                                 | Bridge run artifact manifest                     | HTML currently wraps Markdown in `<pre>`                                        | Add richer report renderer and latest-run section                    |
| Cleanup                      | Removes reports, diagnostics, runs, tmp; optional site; preserves exports/service data         | Safe reset of services/data                      | Cleanup and reset are separate user concepts but reset is not a CLI workflow    | Add explicit `reset` command with backup and confirmation            |
| Documentation                | MkDocs site, nav, strict build, docs workflow                                                  | CLI command snippet validation                   | CLI docs can drift from Click command surface                                   | Extend docs-check to validate `mbse-lab` snippets                    |
| Tests and CI                 | Deterministic unit/eval tests, optional live evals, CI `make check`                            | Manual/scheduled full-stack action               | Full stack not CI-default                                                       | Add manual/scheduled live smoke workflow                             |
| Release/publishing           | Release process docs, Git Flow policy, Dependabot targeting `develop`                          | First tagged release and release evidence        | Install-from-GitHub works, PyPI deferred                                        | Add release evidence artifact and version bump checklist             |
| Developer tooling            | Ruff/pre-commit, Hatch envs, docs check, workflow check                                        | Modularized bridge package                       | `scripts/flexo_syson_bridge.py` is large and multi-purpose                      | Move bridge logic into package modules with stable CLI wrapper       |

## 5. Feature backlog

### P0 — Immediate usability and safety fixes

#### Feature: First-use smoke workflow

* **Problem it solves:** Users have commands for bootstrap, doctor, services, first model, deployment verification, and share-check, but no single “prove my lab works” workflow.
* **Target user:** MBSE beginner, technical lead, maintainer.
* **User story:** As a new user, I want one command that verifies my local lab can start, create a tiny model, import it into SysON, and tell me what happened.
* **Current repo evidence:** `mbse-lab bootstrap` and `first-model` exist in docs; the MVP catalog still marks guided bootstrap as partially verified pending clean-checkout live validation.
* **Proposed behavior:** Add `mbse-lab smoke first-use` or `mbse-lab verify first-use`. It should run doctor, check workspace, start services unless skipped, initialize Flexo org, create/import a disposable first model, run deployment verification, generate a report, and print artifact paths.
* **CLI/docs/API impact:** New CLI group or command; update README, CLI docs, release checklist, and diagnostics docs.
* **Implementation notes:** Reuse `first_model`, `doctor_report`, `service_report`, and deployment verification logic. Add `--dry-run`, `--json-output`, `--keep-projects`, `--skip-services`, and `--model-workspace`.
* **Risks or tradeoffs:** Live service runs are slow and Docker-dependent. Keep deterministic tests separate.
* **Dependencies:** Existing `first-model`, deployment verify, report, workspace helpers.
* **Suggested priority:** P0
* **Estimated effort:** Medium
* **Acceptance criteria:** Command works in dry-run without Docker; live mode creates/imports a disposable model; JSON output includes service status, project IDs, artifact paths, and share-check result; docs include a demo script.
* **Suggested GitHub issue title:** Add first-use smoke workflow for bootstrap-to-import validation
* **Suggested labels:** `priority/p0`, `area/cli`, `area/onboarding`, `area/live-eval`

#### Feature: Fix and harden SysON roots resolution

* **Problem it solves:** The lower-level `syson-roots` workflow appears to use the project ID as the commit ID in the REST roots path, while the `first-model` workflow correctly fetches the latest commit first.
* **Target user:** Anyone importing `.sysml` into SysON manually.
* **User story:** As a user, I want `mbse-lab syson roots <project-id>` to reliably return the import namespace without knowing SysON commit internals.
* **Current repo evidence:** `cmd_syson_roots` in the bridge script builds a roots URL containing `/commits/{project_id}/roots`, while `syson_latest_commit_id` and `syson_root_package_id` in `src/mbse_lab/model.py` use the latest commit before querying roots.
* **Proposed behavior:** Resolve the latest commit automatically, allow `--commit-id` override, and return editing context/root package information together.
* **CLI/docs/API impact:** Update `syson-roots` and `mbse-lab syson roots`; update CLI docs and bridge docs.
* **Implementation notes:** Reuse `syson_latest_commit_id` and `syson_root_package_id`; add deterministic tests with mocked HTTP responses.
* **Risks or tradeoffs:** SysON API shape may differ by version; preserve `--commit-id` for advanced users.
* **Dependencies:** None.
* **Suggested priority:** P0
* **Estimated effort:** Small
* **Acceptance criteria:** Tests prove roots command calls `/commits/<latest-commit-id>/roots`; docs show `--json-output`; command fails with actionable error if no root package is found.
* **Suggested GitHub issue title:** Fix SysON roots command to resolve latest commit before reading roots
* **Suggested labels:** `priority/p0`, `area/bridge`, `area/syson`, `type/bug`

#### Feature: Safer SysON password initialization

* **Problem it solves:** Copying `.env.example` creates `SYSON_POSTGRES_PASSWORD=change-me`, which is not a good default for a local environment and can cause drift with persisted Postgres data.
* **Target user:** New user, private-data user, maintainer.
* **User story:** As a user, I want local runtime secrets generated safely so I do not accidentally run with a placeholder password.
* **Current repo evidence:** `deploy/syson/.env.example` contains `SYSON_POSTGRES_PASSWORD=change-me`; `ensure_syson_env` copies it when `.env` is missing; doctor already checks persisted database credential drift.
* **Proposed behavior:** Generate a random SysON Postgres password during `init`/`bootstrap`; keep `.env.example` publishable; add doctor warning if the local `.env` still contains `change-me`.
* **CLI/docs/API impact:** `mbse-lab init`, `bootstrap`, and `doctor`; update SysON deployment README and CLI docs.
* **Implementation notes:** Add helper `ensure_syson_env(generate_secret=True)`. Preserve an option like `--copy-syson-example` for exact template copy if needed.
* **Risks or tradeoffs:** Existing users may expect copy behavior. Make behavior explicit in command output.
* **Dependencies:** None.
* **Suggested priority:** P0
* **Estimated effort:** Small
* **Acceptance criteria:** New `.env` has non-placeholder password; doctor warns on placeholder; tests cover generated password and existing `.env` preservation.
* **Suggested GitHub issue title:** Generate a random SysON Postgres password during init/bootstrap
* **Suggested labels:** `priority/p0`, `area/safety`, `area/syson`, `area/cli`

#### Feature: Private workspace output preflight

* **Problem it solves:** Generated bridge artifacts are private by default, but if `MBSE_MODEL_WORKSPACE` is unset, default output falls back to repo-local `exports/`.
* **Target user:** Private-data user, systems engineer, technical lead.
* **User story:** As a user handling real models, I want the CLI to stop or warn before writing generated private artifacts into the public tooling repo.
* **Current repo evidence:** `default_output_dir()` returns `$MBSE_MODEL_WORKSPACE/exports` when set, otherwise `exports`; private workspace docs say real `.sysml`, Flexo JSON exports, rendered snapshots, logs, and evidence belong outside this repo; `.gitignore` blocks generated exports.
* **Proposed behavior:** Add a preflight warning or failure when bridge/first-model writes to repo-local `exports/` without explicit `--output`, `--output-dir`, `--public-example`, or `--allow-repo-exports`.
* **CLI/docs/API impact:** Bridge commands, `first-model`, README, CLI docs, private workspace docs.
* **Implementation notes:** Implement as shared path policy helper. Allow deterministic tests to assert warning/failure modes.
* **Risks or tradeoffs:** May break existing quick demos that rely on repo-local `exports/`. Use warning first, then stronger enforcement in next minor release.
* **Dependencies:** Workspace helper.
* **Suggested priority:** P0
* **Estimated effort:** Medium
* **Acceptance criteria:** Commands print clear warning when workspace is unset; optional strict mode fails; docs explain public fixture exception; share-check remains green.
* **Suggested GitHub issue title:** Add private workspace preflight for generated bridge artifacts
* **Suggested labels:** `priority/p0`, `area/safety`, `area/workspace`, `area/bridge`

#### Feature: Validate `mbse-lab` command snippets in docs

* **Problem it solves:** The CLI is now the main user surface, but docs validation does not appear to validate `mbse-lab ...` snippets.
* **Target user:** Maintainer, beginner.
* **User story:** As a maintainer, I want docs to fail CI when they reference non-existent CLI commands or stale options.
* **Current repo evidence:** CLI docs are extensive; `check_docs.py` validates make/script command snippets but its command regex does not include `mbse-lab`.
* **Proposed behavior:** Extend docs-check to parse `mbse-lab` command snippets and validate command/option existence via `mbse-lab --help` or Click command metadata.
* **CLI/docs/API impact:** Docs-check script and CI; no user-facing CLI change.
* **Implementation notes:** Use Click’s command tree directly for deterministic validation, not shelling out for every snippet.
* **Risks or tradeoffs:** Multi-line examples and placeholders require tolerant parsing.
* **Dependencies:** Existing `src/mbse_lab/cli.py`.
* **Suggested priority:** P0
* **Estimated effort:** Medium
* **Acceptance criteria:** A fake stale `mbse-lab` command in docs fails `make docs-check`; existing docs pass.
* **Suggested GitHub issue title:** Extend docs-check to validate mbse-lab CLI snippets
* **Suggested labels:** `priority/p0`, `area/docs`, `area/cli`, `area/ci`

### P1 — High-value workflow improvements

#### Feature: Render coverage and unsupported-element report

* **Problem it solves:** Unsupported element types are preserved in JSON but not emitted to `.sysml`; users need explicit evidence of what was omitted.
* **Target user:** Developer automating transformations, maintainer, technical lead.
* **User story:** As a bridge user, I want a report showing rendered, skipped, and unsupported elements so I know whether the SysON import is representative.
* **Current repo evidence:** Docs state unsupported elements are not emitted; tests assert unsupported elements are not rendered.
* **Proposed behavior:** `render-sysml` writes optional `render-report.json` with counts by `@type`, rendered IDs, skipped IDs, root coverage, warnings, and output path.
* **CLI/docs/API impact:** Add `--report` and perhaps `--fail-on-unsupported`; update modeling conventions.
* **Implementation notes:** Refactor renderer to return both text and metadata.
* **Risks or tradeoffs:** More output artifacts to manage; route defaults through private workspace policy.
* **Dependencies:** Private workspace preflight.
* **Suggested priority:** P1
* **Estimated effort:** Medium
* **Acceptance criteria:** Existing fixtures produce deterministic reports; unsupported fixture has non-zero skipped count; report is linked from run logs.
* **Suggested GitHub issue title:** Add render coverage report for supported and unsupported SysML elements
* **Suggested labels:** `priority/p1`, `area/bridge`, `area/sysml`, `area/reporting`

#### Feature: Doctor remediation codes and next-step grouping

* **Problem it solves:** Doctor already checks many things, but users need clearer “do this next” guidance.
* **Target user:** New user, maintainer.
* **User story:** As a user, I want doctor output to group failures by prerequisite, file setup, service reachability, credentials, and private workspace.
* **Current repo evidence:** `doctor` checks Python, Docker, Compose, repo markers, env files, workspace, ports, HTTP, and SysON DB credentials; the MVP catalog notes doctor could produce clearer next-step grouping.
* **Proposed behavior:** Add remediation codes like `DOCKER_MISSING`, `SYSON_PASSWORD_DRIFT`, `WORKSPACE_UNSET`, and `FLEXO_ORG_MISSING`; print grouped next commands; include codes in JSON.
* **CLI/docs/API impact:** `mbse-lab doctor`, reports, diagnostics.
* **Implementation notes:** Convert checks to typed records; keep current text stable enough for users.
* **Risks or tradeoffs:** Avoid over-engineering a health framework.
* **Dependencies:** None.
* **Suggested priority:** P1
* **Estimated effort:** Medium
* **Acceptance criteria:** JSON output includes codes; text output groups next actions; tests cover common failure states.
* **Suggested GitHub issue title:** Add remediation codes and grouped next steps to mbse-lab doctor
* **Suggested labels:** `priority/p1`, `area/diagnostics`, `area/cli`, `area/onboarding`

#### Feature: Report and run-log artifact manifest

* **Problem it solves:** Reports summarize health, but they do not fully connect bridge runs, generated exports, render reports, and import results.
* **Target user:** Systems engineer, technical lead, maintainer.
* **User story:** As a user, I want one report showing the latest lab state and the artifacts generated by my last bridge run.
* **Current repo evidence:** `report` writes Markdown/HTML/JSON with doctor/status/share/diagnostics; bridge run logs are documented under `runs/flexo-to-syson/`.
* **Proposed behavior:** Include latest run log summaries, artifact paths, render coverage, import status, and private/public location flags in `mbse-lab report`.
* **CLI/docs/API impact:** `mbse-lab report`; docs; report schema.
* **Implementation notes:** Add `runs/latest.json` or discover latest by timestamp.
* **Risks or tradeoffs:** Avoid including private model content in reports; include paths and counts only by default.
* **Dependencies:** Render coverage report.
* **Suggested priority:** P1
* **Estimated effort:** Medium
* **Acceptance criteria:** Report shows latest bridge run without embedding private model text; tests cover no-run and one-run cases.
* **Suggested GitHub issue title:** Include bridge run artifacts and render coverage in lab report
* **Suggested labels:** `priority/p1`, `area/reporting`, `area/bridge`, `area/safety`

#### Feature: Manual or scheduled live smoke GitHub Action

* **Problem it solves:** Optional live evals exist, but CI currently validates mostly deterministic/local checks and does not start the full stack.
* **Target user:** Maintainer, technical lead.
* **User story:** As a maintainer, I want a manual or scheduled workflow that starts Flexo/SysON and runs live evals so releases have repeatable evidence.
* **Current repo evidence:** Live tests are gated by `MBSE_LIVE_EVAL=1`; CI currently runs pre-commit, docs, env prep, and `make check`; full Docker-stack CI is explicitly deferred beyond MVP.
* **Proposed behavior:** Add `live-smoke.yml` with `workflow_dispatch` and maybe weekly schedule. It runs init, services up, doctor, first-use smoke, deployment verify, live-eval, diagnostics upload.
* **CLI/docs/API impact:** GitHub Actions, release docs.
* **Implementation notes:** Keep out of default PR CI until stable; upload diagnostics artifact on failure.
* **Risks or tradeoffs:** Docker startup time, flaky external image pulls, GitHub runner resource limits.
* **Dependencies:** First-use smoke command.
* **Suggested priority:** P1
* **Estimated effort:** Medium/Large
* **Acceptance criteria:** Workflow can be manually run; failure uploads diagnostics; release checklist references latest successful run.
* **Suggested GitHub issue title:** Add manual live-smoke GitHub Action for Flexo/SysON workflows
* **Suggested labels:** `priority/p1`, `area/ci`, `area/live-eval`, `area/release`

#### Feature: Endpoint and workspace profiles

* **Problem it solves:** CLI commands accept URLs and env vars, but users need named local/remote profiles as workflows mature.
* **Target user:** Developer, maintainer, advanced systems engineer.
* **User story:** As a user, I want to switch between local Docker and a remote test Flexo/SysON endpoint without retyping URLs and workspace paths.
* **Current repo evidence:** CLI commands expose `--flexo-url`, `--syson-url`, and `MBSE_MODEL_WORKSPACE`; MVP catalog notes a decision remains on local Docker versus remote endpoint profile support.
* **Proposed behavior:** Add `mbse-lab profile init/list/use/check` and a local ignored config file, such as `.mbse-lab/profiles.json`.
* **CLI/docs/API impact:** New CLI group; docs for local-only default and remote profile limitations.
* **Implementation notes:** Keep local profile default; avoid storing credentials unless explicitly supported and ignored.
* **Risks or tradeoffs:** Could blur local-lab identity. Defer remote auth complexity.
* **Dependencies:** Product decision on local-only versus remote.
* **Suggested priority:** P1/P2
* **Estimated effort:** Medium
* **Acceptance criteria:** Profiles can set URLs and workspace path; doctor uses active profile; config is ignored by default.
* **Suggested GitHub issue title:** Add named endpoint/workspace profiles for local and remote lab use
* **Suggested labels:** `priority/p1`, `area/cli`, `area/config`, `area/extensibility`

### P2 — Bridge and modeling capability improvements

#### Feature: SysML v2 coverage matrix

* **Problem it solves:** Supported element types are documented, but users need a versioned matrix showing support status, fixture coverage, render behavior, and SysON import validation.
* **Target user:** Developer, maintainer, technical lead.
* User story:** As a maintainer, I want every supported element type tied to a fixture and test so coverage expands safely.
* **Current repo evidence:** Modeling conventions list supported types and require fixture/test/doc updates before adding new types.
* **Proposed behavior:** Add `docs/lab/sysml-coverage.md` plus generated or manually maintained matrix with columns: Flexo `@type`, textual form, fixture, deterministic render test, live import test, status.
* **CLI/docs/API impact:** Docs and tests.
* **Implementation notes:** Generate matrix from a small YAML/JSON registry if practical.
* **Risks or tradeoffs:** Manual matrix can drift; pair with docs-check.
* **Dependencies:** Render coverage report.
* **Suggested priority:** P2
* **Estimated effort:** Small/Medium
* **Acceptance criteria:** Matrix exists; every `RENDERABLE_TYPES` entry has a row; docs-check fails if registry and renderer disagree.
* **Suggested GitHub issue title:** Add SysML v2 bridge coverage matrix tied to fixtures and tests
* **Suggested labels:** `priority/p2`, `area/docs`, `area/bridge`, `area/sysml`

#### Feature: Synthetic example model gallery

* **Problem it solves:** `first-model` creates a tiny package, but users need slightly richer synthetic examples to understand what the lab is for.
* **Target user:** Beginner, technical lead, systems engineer.
* **User story:** As an evaluator, I want to create or import a known public example like RF link budget or container deployment without real model data.
* **Current repo evidence:** Docs include model specs, fixtures include RF link budget and container deployment, and deterministic tests render those fixtures.
* **Proposed behavior:** Add `mbse-lab examples list`, `mbse-lab examples render rf-link-budget`, and `mbse-lab examples import rf-link-budget`.
* **CLI/docs/API impact:** New CLI group; docs and examples.
* **Implementation notes:** Treat fixtures as canonical public examples; avoid writing to private workspace unless import/export generates artifacts.
* **Risks or tradeoffs:** Do not over-invest in domain model content at the expense of lab reliability.
* **Dependencies:** Render coverage report.
* **Suggested priority:** P2
* **Estimated effort:** Medium
* **Acceptance criteria:** Examples list is generated from fixtures; RF link budget renders and imports in live mode; no private content included.
* **Suggested GitHub issue title:** Add CLI example gallery for public synthetic SysML fixtures
* **Suggested labels:** `priority/p2`, `area/examples`, `area/cli`, `area/onboarding`

#### Feature: SysON import validation harness

* **Problem it solves:** Rendering text is not enough; the text must import into SysON and produce expected elements.
* **Target user:** Maintainer, bridge developer.
* **User story:** As a maintainer, I want each supported fixture to prove both deterministic render output and live SysON import behavior when services are running.
* **Current repo evidence:** `test_live_syson_import.py` imports the basic fixture into a disposable SysON project and waits for an expected package.
* **Proposed behavior:** Extend live SysON import tests to run a fixture table, verify expected element names/types, and record import coverage.
* **CLI/docs/API impact:** Live evals and coverage docs.
* **Implementation notes:** Keep live tests opt-in; add fixture metadata for expected names/types.
* **Risks or tradeoffs:** Live tests may become slow/flaky.
* **Dependencies:** Coverage matrix.
* **Suggested priority:** P2
* **Estimated effort:** Medium
* **Acceptance criteria:** At least three fixtures import live; failure points to fixture and expected element.
* **Suggested GitHub issue title:** Expand live SysON import evals across supported bridge fixtures
* **Suggested labels:** `priority/p2`, `area/live-eval`, `area/syson`, `area/bridge`

#### Feature: Safer reset workflow

* **Problem it solves:** Cleanup protects service data, but users eventually need controlled resets of SysON/Flexo local state.
* **Target user:** Systems engineer, maintainer.
* **User story:** As a user, I want to reset local service data only when I explicitly request it, with backup guidance first.
* **Current repo evidence:** README warns not to use `down --volumes` or manually delete data unless intentionally resetting; cleanup intentionally does not touch service data, env files, backups, or model exports.
* **Proposed behavior:** Add `mbse-lab reset syson`, `reset flexo`, and `reset all` with `--backup-first`, `--dry-run`, and explicit confirmation.
* **CLI/docs/API impact:** New CLI command; docs.
* **Implementation notes:** For Flexo, call backup before resetting startup/data; for SysON, archive data dir before deletion.
* **Risks or tradeoffs:** Destructive command risk. Require explicit flags.
* **Dependencies:** Backup behavior and private workspace policy.
* **Suggested priority:** P2
* **Estimated effort:** Medium
* **Acceptance criteria:** Dry-run lists exact paths; destructive mode refuses without confirmation; tests prove protected paths.
* **Suggested GitHub issue title:** Add backup-first reset workflow for Flexo and SysON local service data
* **Suggested labels:** `priority/p2`, `area/safety`, `area/services`, `area/cli`

### P3 — Long-term architecture and extensibility

#### Feature: Modular bridge package architecture

* **Problem it solves:** `scripts/flexo_syson_bridge.py` contains HTTP helpers, rendering, deployment contract logic, SysON GraphQL, run logging, and CLI parsing in one large script.
* **Target user:** Maintainer, bridge developer.
* **User story:** As a maintainer, I want bdge logic in importable modules so features can grow without making the script fragile.
* **Current repo evidence:** The bridge script includes export, render, deployment contract, verification, SysON project/import, HTTP, and CLI behavior.
* **Proposed behavior:** Move bridge logic into `src/mbse_lab/bridge/` modules: `flexo.py`, `syson.py`, `render.py`, `coverage.py`, `deployment.py`, `runlog.py`.
* **CLI/docs/API impact:** Keep script as compatibility wrapper; `mbse-lab` uses package modules directly.
* **Implementation notes:** Refactor in small steps with tests unchanged first.
* **Risks or tradeoffs:** Refactor churn without user-visible value unless paired with coverage/report features.
* **Dependencies:** P0/P1 stabilization.
* **Suggested priority:** P3
* **Estimated effort:** Large
* **Acceptance criteria:** Existing CLI/script commands still work; tests import package modules; no behavior regression.
* **Suggested GitHub issue title:** Refactor bridge script into maintainable package modules
* **Suggested labels:** `priority/p3`, `area/architecture`, `area/bridge`, `type/refactor`

#### Feature: Renderer plugin/registry model

* **Problem it solves:** Adding element mappings through hard-coded dictionaries will become difficult as SysML coverage expands.
* **Target user:** Bridge developer, maintainer.
* **User story:** As a contributor, I want to add a renderer for one SysML element type with a fixture, tests, and docs without editing unrelated logic.
* **Current repo evidence:** `RENDERABLE_TYPES` and keyword mapping are currently in the bridge script.
* **Proposed behavior:** Introduce a renderer registry with per-type renderers and metadata used by coverage docs.
* **CLI/docs/API impact:** Internal architecture; generated coverage docs possible.
* **Implementation notes:** Keep simple function registry, not a heavy plugin framework initially.
* **Risks or tradeoffs:** Premature abstraction if added before coverage report.
* **Dependencies:** Modular bridge package and coverage matrix.
* **Suggested priority:** P3
* **Estimated effort:** Medium/Large
* **Acceptance criteria:** Existing supported types render through registry; coverage matrix can be generated from registry metadata.
* **Suggested GitHub issue title:** Introduce renderer registry for incremental SysML v2 element support
* **Suggested labels:** `priority/p3`, `area/architecture`, `area/sysml`, `area/bridge`

#### Feature: Release evidence and distribution hardening

* **Problem it solves:** The repo has release docs and install-from-GitHub, but long-term users will need stable release evidence and possibly PyPI distribution.
* **Target user:** Technical lead, maintainer.
* **User story:** As an evaluator, I want to know exactly which release was validated and what workflows passed.
* **Current repo evidence:** Release checklist exists; PyPI is deferred beyond MVP.
* **Proposed behavior:** Add release evidence artifact template, versioned coverage report, changelog, and optional PyPI decision.
* **CLI/docs/API impact:** Release docs, CI, packaging.
* **Implementation notes:** Start with GitHub releases; defer PyPI until demand is clear.
* **Risks or tradeoffs:** Distribution overhead can distract from workflow quality.
* **Dependencies:** Live smoke workflow.
* **Suggested priority:** P3
* **Estimated effort:** Medium
* **Acceptance criteria:** Release checklist links to deterministic CI, docs build, live smoke run, coverage matrix, and share-check result.
* **Suggested GitHub issue title:** Add release evidence checklist and versioned validation summary
* **Suggested labels:** `priority/p3`, `area/release`, `area/docs`, `area/ci`

## 6. Prioritization table

| Feature                             | User impact | Risk reduction |       Effort | Priority | Why now?                                                       |
| ----------------------------------- | ----------: | -------------: | -----------: | -------- | -------------------------------------------------------------- |
| First-use smoke workflow            |        High |           High |       Medium | P0       | Converts many existing commands into one reliable success path |
| Fix SysON roots resolution          |        High |           High |        Small | P0       | Manual import workflow may fail or confuse users               |
| Safer SysON password initialization |        High |           High |        Small | P0       | Prevents default-password and credential-drift friction        |
| Private workspace output preflight  |        High |           High |       Medium | P0       | Directly protects the public/private repo boundary             |
| Validate `mbse-lab` docs snippets   |      Medium |         Medium |       Medium | P0       | CLI docs are central and must not drift                        |
| Render coverage report              |        High |           High |       Medium | P1       | Reduces false confidence in bridge output                      |
| Doctor remediation codes            |      Medium |         Medium |       Medium | P1       | Improves troubleshooting without changing architecture         |
| Report/run-log artifact manifest    |      Medium |         Medium |       Medium | P1       | Turns workflow evidence into visible value                     |
| Manual live-smoke GitHub Action     |      Medium |           High | Medium/Large | P1       | Makes release validation repeatable                            |
| Endpoint/workspace profiles         |      Medium |         Medium |       Medium | P1/P2    | Supports advanced workflows once local path is reliable        |
| SysML coverage matrix               |      Medium |           High | Small/Medium | P2       | Makes bridge expansion disciplined                             |
| Example model gallery               |      Medium |            Low |       Medium | P2       | Improves demos after first-use path is solid                   |
| SysON import validation harness     |      Medium |           High |       Medium | P2       | Bridges deterministic renderer tests to real importer behavior |
| Safer reset workflow                |      Medium |           High |       Medium | P2       | Helps users recover without accidental data loss               |
| Modular bridge package              |      Medium |         Medium |        Large | P3       | Needed after user-facing gaps are closed                       |
| Renderer registry                   |      Medium |         Medium | Medium/Large | P3       | Helps long-term extensibility after coverage/reporting exists  |
| Release evidence hardening          |      Medium |         Medium |       Medium | P3       | Useful once live smoke is repeatable                           |

## 7. Suggested milestones

### Milestone 1: Reliable First-Use Experience

* **Goal:** A new user can prove the lab works with one documented workflow.
* **Included features:** First-use smoke workflow, SysON roots fix, safer SysON password generation, doctor remediation grouping, docs-check for `mbse-lab` snippets.
* **Excluded features:** Expanded SysML coverage, plugin architecture, remote profiles.
* **Acceptance criteria:** Fresh checkout can run install/init/smoke; smoke JSON includes Flexo/SysON status, model import result, artifact paths, and report path; docs snippets validate in CI.
* **Demo scenario:** `mbse-lab init --model-workspace ~/work/demo-models`; `mbse-lab smoke first-use --json-output`; open generated report.

### Milestone 2: Safe Private Workspace Workflow

* **Goal:** Generated private artifacts are kept out of the public tooling repo by default or with explicit warnings.
* **Included features:** Private workspace output preflight, share-check expansion, report safety flags, backup-first reset design.
* **Excluded features:** Remote profile auth, full bridge expansion.
* **Acceptance criteria:** Bridge commands warn or fail when writing repo-local generated artifacts without explicit intent; `share-check` catches risky generated artifacts and placeholder secrets; docs explain curated public examples.
* **Demo scenario:** Run bridge with workspace unset and observe warning/failure; set `MBSE_MODEL_WORKSPACE` and observe artifacts written under private workspace.

### Milestone 3: Repeatable Bridge Validation

* **Goal:** Users and maintainers can see exactly what the bridge rendered, skipped, and imported.
* **Included features:** Render coverage report, SysML coverage matrix, expanded live SysON import fixture harness, report/run-log integration.
* **Excluded features:** Full SysML v2 coverage, diagram round-trip.
* **Acceptance criteria:** Every supported type has fixture coverage; render report lists unsupported types; live import tests cover at least basic package, RF link budget, and container deployment fixtures.
* **Demo scenario:** Render RF link budget fixture; inspect `.sysml`, `render-report.json`, run log, and report.

### Milestone 4: Maintainer-Friendly Architecture

* **Goal:** The bridge and CLI become easier to evolve without script sprawl.
* **Included features:** Modular bridge package, renderer registry, shared HTTP/config helpers, test fixtures organized by workflow.
* **Excluded features:** New modeling semantics beyond current coverage unless needed for refactor tests.
* **Acceptance criteria:** Existing script and CLI commands remain compatible; tests import package modules; adding a new element renderer requires a focused module/fixture/test/doc change.
* **Demo scenario:** Add a new simple element renderer using the registry and show docs/tests update.

### Milestone 5: Expanded SysML v2 Coverage

* **Goal:** Grow bridge usefulness while preserving honesty about limitations.
* **Included features:** Additional SysML element mappings, relationship/type rendering, example gallery, versioned coverage docs.
* **Excluded features:** Live bidirectional sync, diagram layout round-trip, production deployment.
* **Acceptance criteria:** Coverage expands only with fixtures, render assertions, and where practical live SysON import validation.
* **Demo scenario:** Import a richer synthetic example into SysON and show coverage report with high supported-element ratio.

## 8. First 10 GitHub issues to open

### Issue 1: Add first-use smoke workflow for bootstrap-to-import validation

* **Problem:** New users must chain multiple commands to prove the lab works.
* **Proposed change:** Add `mbse-lab smoke first-use` or equivalent.
* **Acceptance criteria:** Dry-run works without Docker; live run creates/imports disposable first model; JSON output includes status, IDs, artifact paths, report path.
* **Suggested labels:** `priority/p0`, `area/cli`, `area/onboarding`, `area/live-eval`
* **Suggested milestone:** Milestone 1
* **Dependencies:** None

### Issue 2: Fix SysON roots command to resolve latest commit

* **Problem:** Lower-level `syson-roots` appears to use project ID as commit ID.
* **Proposed change:** Fetch latest SysON commit before calling roots; add optional `--commit-id`.
* **Acceptance criteria:** Tests verify correct REST path; docs updated; command returns root package IDs reliably.
* **Suggested labels:** `priority/p0`, `type/bug`, `area/syson`, `area/bridge`
* **Suggested milestone:** Milestone 1
* **Dependencies:** None

### Issue 3: Generate random SysON Postgres password during init/bootstrap

* **Problem:** `deploy/syson/.env.example` has `change-me`, and init copies it.
* **Proposed change:** Generate a random local `.env` password and warn if placeholder remains.
* **Acceptance criteria:** New `.env` does not contain `change-me`; doctor flags placeholder; tests cover existing `.env` preservation.
* **Suggested labels:** `priority/p0`, `area/safety`, `area/syson`, `area/cli`
* **Suggested milestone:** Milestone 1
* **Dependencies:** None

### Issue 4: Add private workspace preflight for generated artifacts

* **Problem:** Bridge defaults can write to repo-local `exports/` when `MBSE_MODEL_WORKSPACE` is unset.
* **Proposed change:** Warn or fail unless explicit output/public-example intent is provided.
* **Acceptance criteria:** Tests cover unset workspace, explicit `--output`, explicit `--allow-repo-exports`, and workspace-set cases.
* **Suggested labels:** `priority/p0`, `area/safety`, `area/workspace`, `area/bridge`
* **Suggested milestone:** Milestone 2
* **Dependencies:** Issue 1 helpful but not required

### Issue 5: Extend docs-check to validate `mbse-lab` command snippets

* **Problem:** Docs validation does not appear to validate the main CLI command surface.
* **Proposed change:** Parse `mbse-lab` snippets and validate command/option existence.
* **Acceptance criteria:** Fake stale CLI command fails docs-check; existing docs pass; CI runs it.
* **Suggested labels:** `priority/p0`, `area/docs`, `area/cli`, `area/ci`
* **Suggested milestone:** Milestone 1
* **Dependencies:** None

### Issue 6: Add render coverage report for supported and unsupported SysML elements

* **Problem:** Unsupported elements are omitted from text without a user-facing coverage summary.
* **Proposed change:** Add optional/default `render-report.json` with rendered/skipped counts and warnings.
* **Acceptance criteria:** Fixture tests verify report contents; unsupported types appear in report; docs updated.
* **Suggested labels:** `priority/p1`, `area/bridge`, `area/sysml`, `area/reporting`
* **Suggested milestone:** Milestone 3
* **Dependencies:** Issue 4

### Issue 7: Add remediation codes and grouped next steps to doctor

* **Problem:** Doctor checks many items but could guide users more clearly.
* **Proposed change:** Add typed remediation codes and grouped next actions.
* **Acceptance criteria:** JSON includes codes; text groups prerequisites/setup/services/workspace; tests cover common failures.
* **Suggested labels:** `priority/p1`, `area/diagnostics`, `area/cli`, `area/onboarding`
* **Suggested milestone:** Milestone 1
* **Dependencies:** Issue 3

### Issue 8: Add manual live-smoke GitHub Action

* **Problem:** Full live workflow validation is optional and local.
* **Proposed change:** Add `workflow_dispatch` action that starts services, runs smoke/live evals, and uploads diagnostics on failure.
* **Acceptance criteria:** Workflow runs manually; diagnostics artifact uploaded on failure; release docs reference it.
* **Suggested labels:** `priority/p1`, `area/ci`, `area/live-eval`, `area/release`
* **Suggested milestone:** Milestone 3
* **Dependencies:** Issue 1

### Issue 9: Include latest bridge run artifacts in lab report

* **Problem:** Reports summarize lab health but not recent bridge workflow evidence.
* **Proposed change:** Add latest run log, artifact paths, render coverage, and import status to `mbse-lab report`.
* **Acceptance criteria:** Report handles no-run and one-run states; private model content is not embedded; tests cover JSON/Markdown output.
* **Suggested labels:** `priority/p1`, `area/reporting`, `area/bridge`, `area/safety`
* **Suggested milestone:** Milestone 3
* **Dependencies:** Issue 6

### Issue 10: Add SysML v2 bridge coverage matrix

* **Problem:** Supported types are documented but not presented as a validation matrix.
* **Proposed change:** Add coverage matrix tied to renderer registry/fixtures/tests.
* **Acceptance criteria:** Every `RENDERABLE_TYPES` entry has a row; docs-check or test fails if renderer and matrix diverge.
* **Suggested labels:** `priority/p2`, `area/docs`, `area/bridge`, `area/sysml`
* **Suggested milestone:** Milestone 3
* **Dependencies:** Issue 6

## 9. Roadmap risks and mitigations

| Risk                                                         | Why it matters                                                                            | Mitigation                                                                                                                          |
| ------------------------------------------------------------ | ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Repo tries to become too many things                         | It already spans CLI, Compose, docs, bridge, reports, diagnostics, tests, and methodology | Define product identity as “safe local lab workflow”; treat CLI as primary surface and scripts/docs as support                      |
| Bridge functionality outpaces validation                     | More SysML mappings can create false confidence                                           | Require fixture + render test + coverage matrix update + optional live import validation per mapping                                |
| Users confuse public tooling repo with private model storage | The repo is public and generatrtifacts may include sensitive model names/IDs          | Add workspace preflight; strengthen share-check; keep docs explicit; default generated outputs to private workspace when configured |
| Docker/service fragility                                     | Flexo/SysON stacks have many containers and persisted data                                | Improve doctor remediation; add first-use smoke; add manual live-smoke CI; upload diagnostics on failure                            |
| Unsupported SysML v2 element types create false confidence   | Import success does not mean full model fidelity                                          | Add render coverage report and `--fail-on-unsupported` option                                                                       |
| Docs drift from CLI behavior                                 | CLI docs are extensive and central to onboarding                                          | Extend docs-check to validate `mbse-lab` snippets and options                                                                       |
| CI does not validate real workflows                          | Current CI does not start full stack by default                                           | Add manual/scheduled live-smoke workflow; keep PR CI deterministic                                                                  |
| Credential drift/default password friction                   | SysON persisted DB can disagree with `.env`; example password is placeholder              | Generate local password; doctor warns on drift and placeholder                                                                      |
| Destructive reset accidents                                  | Users may delete service data or use volumes reset                                        | Add explicit backup-first reset command with dry-run and confirmation                                                               |
| Flexo/SysON version drift                                    | Compose images may change behavior over time                                              | Record service versions in reports/diagnostics; pin versions where practical; live-smoke before release                             |

## 10. Recommended next sprint

### Sprint goal

Make the first successful workflow safer, clearer, and more testable without expanding SysML scope yet.

### Selected issues

1. Fix SysON roots command to resolve latest commit.
2. Generate random SysON Postgres password during init/bootstrap.
3. Add private workspace preflight for generated artifacts.
4. Extend docs-check to validate `mbse-lab` snippets.
5. Add doctor remediation codes for the most common first-run failures.

### Expected user-visible outcome

A new user gets safer local credentials, clearer doctor output, fewer manual SysON import traps, and stronger assurance that docs match the CLI. Private model artifacts are less likely to land silently in the public tooling repo.

### Tests/docs to update

* `evals/test_bridge_cli.py` for roots command and private workspace preflight.
* New tests for SysON password generation and placeholder warning.
* `scripts/check_docs.py` tests or fixtures for `mbse-lab` snippet validation.
* README, CLI docs, private workspace docs, SysON deployment README.
* Release checklist if `doctor` output changes.

### Final demo script

```bash
python3 -m pip install -e .
mbse-lab init --model-workspace ~/work/mbse-demo-models
export MBSE_MODEL_WORKSPACE=~/work/mbse-demo-models
mbse-lab doctor
mbse-lab services up
mbse-lab first-model "Sprint Demo Model"
mbse-lab syson roots <printed-syson-project-id>
mbse-lab report
mbse-lab share-check
```

Expected demo result: generated artifacts are under the private workspace, doctor gives grouped next steps or passes, SysON roots resolves correctly, report is generated, and share-check passes.

## 11. Decision log

These decisions should be made before the roadmap expands:

| Decision                                                                           | Recommendation                                                                                                                          |
| ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Is the repo CLI-first or docs-first?                                               | CLI-first. Docs should explain, validate, and contextualize CLI workflows.                                                              |
| Is MVP local-only or remote-capable?                                               | MVP should promise local Docker. Remote profiles can be experimental P1/P2.                                                             |
| What is the boundary between curated public exports and private generated exports? | Generated outputs are private by default. Public examples require explicit fixture/example path and documentation.                      |
| What subset of SysML v2 is supported?                                              | Use a versioned coverage matrix. “Supported” means fixture, deterministic render test, docs row, and preferably live import validation. |
| Should bridge rendering be plugin-based?                                           | Not immediately. First add coverage reports; then refactor to a simple registry.                                                        |
| What workflows must be CI-validated before release?                                | Determiic CI on every PR; manual/scheduled live-smoke before release.                                                               |
| How should service-dependent tests be handled?                                     | Keep `MBSE_LIVE_EVAL=1` opt-in locally; add manual GitHub Action with diagnostics artifact.                                             |
| How destructive should cleanup/reset be?                                           | Cleanup remains non-destructive. Reset becomes explicit, backup-first, dry-run capable, and confirmation-gated.                         |
| Should reports include private model content?                                      | No. Reports should include paths, IDs, counts, statuses, and warnings, not full private model text by default.                          |
| Should the bridge promise round-trip behavior?                                     | No. It should remain an honest snapshot/import bridge until evidence supports more.                                                     |
