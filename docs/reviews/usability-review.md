## Executive summary

I reviewed the repository statically from the GitHub contents on `main`, including README, docs, deployment files, Python package/CLI, scripts, evals/tests, CI workflows, ignore rules, and bridge/deployment code. I did not run Docker services locally, so runtime conclusions are based on the checked-in code, docs, and the repo’s own recorded live-validation notes.

Overall, `cosgroma/mbse-lab` is already a credible reusable SysML v2 local lab kit. The purpose is unusually clear for a young tooling repo: the README says this is a “SysML v2 Local Lab Kit,” not the long-term home for models, and it explains the Flexo-to-SysON snapshot path near the top. The CLI surface is also much stronger than a typical script-only lab repo: `bootstrap`, `doctor`, `first-model`, `services`, `bridge`, `share-check`, `report`, and `cleanup` form a coherent workflow. The test/eval and CI story is meaningful for the maturity level.

The biggest risk is that the public/private model-data boundary is documented but not yet hard enough to enforce. The most serious example is `scripts/flexo_mms_env.py backup`: by default it exports the live Fuseki dataset and refreshes `deploy/flexo-mms/mount/cluster.nq`, which is a tracked startup dataset. That creates a realistic path for private Flexo graph state to enter the public tooling repo unless users are very careful. The `.gitignore` protects backups, service data, env files, reports, runs, diagnostics, and `exports/`, but it does not protect the tracked Flexo startup dataset. The current `share-check` also does not appear to block tracked private exports or tracked changes to `cluster.nq`.

The highest-value improvement is to harden the artifact boundary: stop updating tracked `cluster.nq` by default, add a safe ignored runtime seed/state location, require or strongly prompt for `MBSE_MODEL_WORKSPACE` before model-generating commands, and expand `share-check` to catch tracked exports, tracked seed mutations, default credentials, and model-looking content.

Usability rating: **7/10**. The repo is understandable and likely usable by a technically capable user, but it has a few high-impact safety and onboarding gaps that matter specifically because it is public MBSE tooling.

---

## What works well

The repo’s core identity is clear. The README opens with the project title, explains that the repo is a reusable local lab kit, names Flexo MMS and SysON, and shows the file/text bridge path from Flexo REST JSON to `.sysml` to SysON GraphQL import. It also explicitly states that Flexo and SysON are separate stacks and that Flexo should be treated as the durable API-driven repository path while SysON is for graphical review/editing.

The “tooling repo, not model repo” boundary is visible early. The README includes a dedicated section, a recommended public/private directory layout, and the `MBSE_MODEL_WORKSPACE` convention. The private workspace docs repeat the boundary and list what belongs inside and outside the repo.

The CLI is a real onboarding asset, not just a thin afterthought. The `pyproject.toml` exposes `mbse-lab = "mbse_lab.cli:main"`, and the CLI docs cover installation, completion, `doctor`, `init`, `bootstrap`, `services`, `first-model`, private workspaces, diagnostics, reports, cleanup, Flexo/SysON commands, bridge commands, and deployment verification.

`bootstrap --dry-run` and `first-model --dry-run` are especially good developer-experience features. They make first use feel safer and provide a non-destructive way to understand what will happen. The CLI tests verify dry-run behavior for `bootstrap`, `init`, `first-model`, service commands, and bridge wrappers.

The Docker Compose organization is sensible. Flexo and SysON live under separate deployment directories, each with a README. Flexo exposes Layer1, SysML v2, auth, Fuseki, and MinIO ports; SysON has its own app/database compose stack and local Postgres bind mount.

Diagnostics, reporting, and cleanup are unusually mature for a local lab repo. `collect_diagnostics.py` gathers redacted command outputs, HTTP probes, selected config files, and deployment verification into `diagnostics/latest/`; `report` writes Markdown/HTML/JSON; `cleanup` removes generated reports, diagnostics, runs, and temp output while avoiding service data and exports.

The repo has a useful safety baseline. `.gitignore` excludes runtime env files, SysON Postgres data, MinIO data, backups, diagnostics, reports, runs, logs, temp output, MkDocs site output, and all generated exports except `exports/README.md`.

The bridge scope is documented honestly. The bridge docs and modeling conventions state that the renderer supports a limited set of SysML v2 element types, preserves unsupported elements in Flexo JSON, does not render unsupported types into `.sysml`, and does not round-trip diagram layout.

Tests are well aligned to the project’s maturity. There are deterministic bridge rendering tests, CLI tests, deployment contract tests, and live evals gated behind `MBSE_LIVE_EVAL=1`. CI runs pre-commit, strict docs build, env preparation, and `make check`.

---

## Major usability concerns

### 1. Tracked Flexo startup dataset can become a private model-data leak

**Issue**
`deploy/flexo-mms/mount/cluster.nq` is tracked, and `scripts/flexo_mms_env.py backup` updates it by default after exporting the live Fuseki dataset.

**Why it matters**
This is the sharpest mismatch with the repo boundary. Users are explicitly told to keep real models outside the public tooling repo, but the local Flexo graph state can be written into a tracked file. A user who creates real model data in Flexo and runs `backup` may unintentionally stage private graph data.

**Evidence from the repo**
The backup command writes an N-Quads backup and, unless `--no-update-init` is used, writes the same contents to `deploy/flexo-mms/mount/cluster.nq`.  The tracked `cluster.nq` already contains generated Flexo graph state with org/repo/commit/policy data.  `.gitignore` ignores backups and some service data, but not `deploy/flexo-mms/mount/cluster.nq`.

**Recommended improvement**
Make `backup` default to writing ignored backups only. Add a separate explicit command such as `mbse-lab flexo seed-update --org-only` or `scripts/flexo_mms_env.py backup --update-init --i-understand-this-updates-tracked-seed`. Move mutable startup data into an ignored path, or commit only a synthetic seed fixture. Add `share-check` detection for changes to `deploy/flexo-mms/mount/cluster.nq`.

**Priority:** High
**Effort:** Medium

---

### 2. Generated artifacts still default into the public repo when `MBSE_MODEL_WORKSPACE` is unset

**Issue**
The default output directory is `exports/` when `MBSE_MODEL_WORKSPACE` is not set.

**Why it matters**
The repo does ignore `exports/**`, but writing private JSON and `.sysml` snapshots into the public repo still increases the chance of accidental disclosure, confusion, or later force-add mistakes. For a public MBSE tooling repo, the safest default should be outside the repo or should require explicit consent.

**Evidence from the repo**
`workspace.default_output_dir()` returns `$MBSE_MODEL_WORKSPACE/exports` if set, otherwise `Path("exports")`.  The bridge script has the same default behavior.  The README documents that generated artifacts default to `exports/` without the workspace variable.

**Recommended improvement**
For commands that create real model artifacts, require one of: `MBSE_MODEL_WORKSPACE`, explicit `--output`/`--output-dir`, or `--allow-repo-exports`. At minimum, print a high-visibility warning before writing to repo-local `exports/`.

**Priority:** High
**Effort:** Small to Medium

---

### 3. `share-check` is valuable but incomplete for the repo’s highest-risk paths

**Issue**
`share-check` flags tracked runtime env/service paths, untracked `exports/flexo` and `exports/sysml` files, and a small set of hard-coded secret patterns. It does not appear to flag tracked private exports if force-added, tracked changes to `cluster.nq`, arbitrary `.sysml` files outside `exports/`, or high-entropy credentials.

**Why it matters**
The command is positioned as the safety gate before sharing. Users handling private model data will trust it. If it misses the most likely model-data leak paths, it can create a false sense of security.

**Evidence from the repo**
The forbidden tracked paths/prefixes do not include `exports/` or `deploy/flexo-mms/mount/cluster.nq`; the forbidden untracked prefixes include only `exports/flexo/` and `exports/sysml/`.  The scanner checks tracked files only against a limited list of regex patterns.  Tests cover untracked generated export detection, but not tracked export detection or tracked seed mutation detection.

**Recommended improvement**
Add policy modes: block tracked generated exports unless under an explicit curated allowlist; flag any tracked `.sysml`, `.nq`, `.trig`, `.json` model-like artifact outside fixtures/docs unless allowlisted; detect dirty `cluster.nq`; scan for common token/secret entropy patterns; flag default values such as `change-me` in runtime `.env`.

**Priority:** High
**Effort:** Medium

---

### 4. README is useful but too dense for first-use onboarding

**Issue**
The README contains purpose, boundary, layout, requirements, docs, CLI installation, bootstrap, credentials, services, initialization, health checks, data safety, common workflows, stop/restart, maintenance, bridge scope, and troubleshooting.

**Why it matters**
The README is accurate, but a new user looking for “clone → install → run first useful workflow” has to scan through many sections and two command styles. This slows first use.

**Evidence from the repo**
The README includes a large amount of detailed script-level operational content after the CLI quickstart, including direct `python3 scripts/...` commands and manual Docker Compose commands.

**Recommended improvement**
Reorganize README around a five-minute quickstart first, followed by “what this repo is/is not,” “first model workflow,” “common commands,” and links to detailed docs. Move most direct script-level workflows, service maintenance, credentials, and troubleshooting into task-specific docs.

**Priority:** High
**Effort:** Small

---

### 5. There are two overlapping command surfaces: modern CLI and legacy/direct scripts

**Issue**
The repo presents both `mbse-lab ...` commands and direct `python3 scripts/...` commands throughout README and docs.

**Why it matters**
Technically capable users can handle both, but first-time users will wonder which command style is canonical. This is especially confusing for MBSE users who are already learning Docker, Flexo, SysON, SysML v2 APIs, and the bridge.

**Evidence from the repo**
The README introduces the CLI, then later documents the same workflows through `scripts/flexo_mms_env.py` and `scripts/flexo_syson_bridge.py`.  The CLI itself wraps those scripts for service and bridge workflows.  The docs still include direct script commands as primary bridge instructions.

**Recommended improvement**
Make `mbse-lab` the primary user-facing interface everywhere. Move direct script usage into “Developer internals” or “Advanced/manual recovery.” Keep script commands only where the CLI does not yet cover the operation.

**Priority:** Medium
**Effort:** Small to Medium

---

### 6. Bridge renderer silently skips unsupported element types

**Issue**
Unsupported elements are omitted from `.sysml` output. The docs state this honestly, but the generated output does not appear to include a skipped-element summary or capability report.

**Why it matters**
Users may import a snapshot into SysON and think they imported the model, when only a subset was rendered. This is especially risky for technical leads evaluating workflow completeness.

**Evidence from the repo**
`render_element()` returns an empty list for unsupported element types, and `render_snapshot()` only emits a generic “No supported renderable SysML elements” comment if nothing renders.  The modeling conventions page lists supported types and says unsupported types remain in raw JSON but are not emitted.

**Recommended improvement**
Emit a bridge manifest beside every `.sysml` file with rendered count, skipped count, skipped type histogram, root IDs, source commit, and renderer version. Also add a comment block to the `.sysml` file such as `// Rendered 17 elements; skipped 42 unsupported elements: OwningMembership=30, ...`.

**Priority:** High
**Effort:** Medium

---

### 7. SysON `.env` handling starts from a default password

**Issue**
`deploy/syson/.env.example` contains `SYSON_POSTGRES_PASSWORD=change-me`, and `ensure_syson_env()` copies that template when missing.

**Why it matters**
For local-only use this may be acceptable, but `bootstrap` can create the file and start services. A user may never see the instruction to replace the password. It also creates password drift when a persisted database was initialized with a different password.

**Evidence from the repo**
The SysON compose file requires `SYSON_POSTGRES_PASSWORD`, but the example sets it to `change-me`.   The workspace/env helper copies the example unchanged.  The release-process doc explicitly calls out local SysON password drift as a live-smoke failure mode.

**Recommended improvement**
Generate a random SysON database password during `init`/`bootstrap`, similar to Flexo runtime secrets. Have `doctor` flag `change-me` and known default passwords.

**Priority:** Medium
**Effort:** Small to Medium

---

### 8. Service readiness is not consistently checked before dependent workflows

**Issue**
Flexo startup waits for containers to be running, but not necessarily API readiness. SysON startup is a plain `docker compose up -d`, and `bootstrap` status checks run `docker compose ps` for SysON rather than a readiness probe.

**Why it matters**
A first-time user may run `first-model` immediately after `bootstrap` and hit intermittent failures if SysON or Flexo APIs are still initializing.

**Evidence from the repo**
`services up` starts Flexo through `flexo_mms_env.py up --wait`, then starts SysON with Docker Compose.  The Flexo wait function checks container running state, not HTTP readiness.  `doctor` does HTTP checks for Flexo `/projects` and SysON `/`, showing that the repo already has a better readiness concept.

**Recommended improvement**
Add service readiness waits to `mbse-lab services up` and `bootstrap`: Flexo `/projects`, SysON `/`, and optionally SysON GraphQL. Have `first-model` run a preflight and print exact missing service/startup instructions.

**Priority:** Medium
**Effort:** Medium

---

### 9. Possible SysON roots inconsistency in the bridge script

**Issue**
The bridge script’s `cmd_syson_roots()` appears to call `/api/rest/projects/{project_id}/commits/{project_id}/roots`, using the project ID as the commit ID. Elsewhere, the code and live test first resolve the latest commit ID and then call `/commits/{commit_id}/roots`.

**Why it matters**
`syson-roots` is a key manual bridge step. If it fails or returns misleading results, users will get stuck finding the namespace ID needed for import.

**Evidence from the repo**
The bridge script shows `cmd_syson_roots()` using `commits/{project_id}/roots`.  The package-level `syson_root_package_id()` and live SysON import test use the latest commit ID before resolving roots.

**Recommended improvement**
Update `syson-roots` to resolve latest commit ID first, or accept `--commit-id` explicitly. Add a unit test for the URL construction.

**Priority:** High
**Effort:** Small

---

### 10. Code is modularizing, but the bridge script has become a mixed-responsibility module

**Issue**
`src/mbse_lab/` contains useful modules, but `scripts/flexo_syson_bridge.py` still includes HTTP helpers, Flexo operations, SysON operations, rendering, deployment contract extraction, Docker runtime verification, run logging, and CLI parsing.

**Why it matters**
This is manageable today, but it increases hidden coupling between docs, CLI wrappers, tests, bridge behavior, and deployment validation. It will get harder to extend the bridge safely.

**Evidence from the repo**
The script contains renderable type definitions, Flexo export, SysON GraphQL import, deployment contract/verification logic, and command parser code.  The package separately contains HTTP, health, model, workspace, report, share, and shell helpers.

**Recommended improvement**
Move bridge/render/import/deployment logic into package modules, leaving scripts as compatibility shims. Add typed data contracts for snapshots, render results, deployment contracts, and run logs.

**Priority:** Medium
**Effort:** Large

---

## New-user onboarding review

A technically capable new user would likely understand the repo’s intent quickly. The README title, opening description, diagrams, and “Tooling Repo, Not Model Repo” section are clear. The role split between Flexo and SysON is also explained early: Flexo is the durable API-driven path; SysON is the graphical review/editing path.

Where they may get slowed down is the path from “clone” to “first useful result.” The README has all the pieces, but the fastest path is mixed with documentation-site build instructions, layout, direct scripts, credentials, service tables, health checks, and maintenance commands. A first-time user may ask: Should I start with `make install-cli`, `mbse-lab bootstrap`, `make init`, or `python3 scripts/flexo_mms_env.py init --with-sysmlv2`?

`mbse-lab bootstrap` is discoverable, but it should be more prominent. It deserves to be the first command sequence after prerequisites. `mbse-lab first-model` is excellent conceptually: it creates a Flexo project, commits one root package, exports JSON, renders `.sysml`, creates a SysON project, imports the rendered text, and prints IDs and artifact paths.  The code also prints Flexo project/commit IDs, package ID, export path, SysML path, SysON project ID, namespace ID, and SysON URL.

Likely first-hour sticking points:

1. **Python/Hatch/CLI setup choice.** The repo says no packages are required for scripts, but the CLI requires `click` and installation. That is okay, but “scripts need only stdlib” and “CLI needs editable install” can be made clearer.

2. **Workspace variable persistence.** `init --model-workspace` prints `export MBSE_MODEL_WORKSPACE=...`, but it cannot set the parent shell. Users may think they configured a workspace permanently and later generate artifacts into repo-local `exports/`.

3. **SysON startup readiness.** The bootstrap flow starts SysON but does not visibly wait for SysON API readiness. A first `first-model` run could fail if the app is still starting.

4. **Password drift.** The repo already documents SysON persisted Postgres password drift as a real live-smoke issue. This is likely to recur for users experimenting with resets.

5. **Manual namespace ID discovery.** The bridge workflow requires a SysON namespace/root package ID. The docs explain this, but it remains an awkward concept for a new user. `first-model` avoids it; `bridge run` still requires it.

Can they reach a first useful result? Yes, probably, especially using:

```bash
make install-cli
mbse-lab bootstrap --model-workspace ~/work/my-private-models
mbse-lab first-model "My First Model"
```

But the README should present that path as the default, then put manual script workflows later.

The first onboarding improvement should be a short “Five-minute quickstart” near the top with expected outputs, service URLs, and the next command after each step.

---

## Repository structure review

The high-level directory layout is intuitive:

```text
deploy/flexo-mms/
deploy/syson/
docs/
exports/
scripts/
src/mbse_lab/
evals/
.github/workflows/
```

The README explains the major directories and distinguishes deployments, docs, scripts, and curated exports.  The structure supports the repo’s purpose well.

The strongest structural concern is the Flexo deployment directory. `deploy/flexo-mms/` contains both source-controlled deployment templates and local runtime/state-adjacent material. Runtime `.env` and backups are ignored, but `mount/cluster.nq` is tracked and mutable through `backup`. That makes the distinction between “source-controlled template” and “local runtime output” unsafe.

`exports/` is clearly marked as curated publishable examples only, and the README says new files under `exports/` are ignored by default.  That is good, but the repo currently has no explicit curated-example subdirectory or metadata convention. If force-added examples are allowed, there should be a clear `exports/examples/` or `fixtures/exports/` convention and `share-check` should block everything else.

`evals/` is useful but may be less discoverable than `tests/` for software developers. The name “evals” is acceptable for an AI/automation-oriented lab, but the README/docs should clearly say these are the deterministic and live test suites.

`docs/model-specs/` and `docs/plans/` are valuable, but they may distract new users. In MkDocs navigation, “Plans” and detailed model specs appear alongside user guide pages. That can make the docs feel like a project notebook rather than a task-oriented user guide.

Private model workspaces are sufficiently separated conceptually, but not fully enforceable yet. `MBSE_MODEL_WORKSPACE` is well documented, and workspace initialization creates `docs`, `source`, `exports/flexo`, `exports/sysml`, `evidence`, and `runs`.  The missing piece is making the private workspace the default for all model-generating commands after first setup.

---

## README review

The README is strong in content and weak in information hierarchy.

It is not too short. It is probably too dense for first use. It explains purpose, Flexo/SysON roles, the bridge, the tooling/model boundary, requirements, CLI, credentials, services, initialization, health checks, data safety, common workflows, stopping/restarting, maintenance, bridge scope, and troubleshooting.

It does provide a good quickstart in pieces, but not as a single top-level “do this first” path. The `bootstrap` and `first-model` commands appear after several sections. A user scanning quickly may miss the intended happy path.

It clearly explains Flexo, SysON, and the bridge. The bridge diagram is helpful. The “Flexo durable repository / SysON graphical review” distinction is one of the README’s strengths.

It clearly states “tooling repo, not model repo,” but the operational guardrails do not fully match the statement. The README should explicitly warn about `cluster.nq` and backup behavior until the implementation is changed.

The README should be reorganized into “quickstart first, details later.” Keep the following in README:

```text
What this repo is
What this repo is not
Five-minute quickstart
Prerequisites
First model workflow
Common commands
Private model workspace safety
Flexo vs SysON roles
Bridge scope and limitations
Documentation links
Troubleshooting starter
Contributing/maintainer links
```

Move these to docs pages:

```text
Detailed credential rotation
Manual script-level Flexo commands
Manual script-level SysON commands
Full bridge command reference
Backup/restore details
Diagnostics bundle anatomy
Release process
Detailed troubleshooting by symptom
Deployment contract details
```

---

## Documentation site review

The MkDocs setup is healthy: Material theme, search, Mermaid, strict build, and a navigation tree that includes user guide, local lab, methodology, model specs, and plans.  The docs build is wired into Hatch and CI.

The current docs are organized more by repository area than by user task. `docs/index.md` is mostly a list of pages, not a guided start page.

Recommended documentation structure:

```text
Getting Started
  - Start here
  - Five-minute quickstart
  - Prerequisites
  - First model workflow

Safety
  - Private model workspace safety
  - Safe to commit / do not commit
  - Backups, runtime data, and exports
  - Publishing checklist

Local Services
  - Flexo MMS local service
  - SysON local service
  - Ports and health checks
  - Backup and restore
  - Resetting safely

Workflows
  - Flexo workflows
  - SysON workflows
  - Bridge workflows
  - First-model walkthrough
  - Reports and diagnostics

Reference
  - CLI reference
  - Service URLs
  - Environment variables
  - Generated artifact locations
  - Bridge capability matrix

Troubleshooting
  - By symptom
  - Docker/Compose failures
  - Port conflicts
  - SysON Postgres password drift
  - Flexo org missing
  - Import succeeds but diagram looks empty

Developer / Maintainer
  - Architecture
  - Code organization
  - Testing and live evals
  - Release process
  - Workflow/agent guide
```

Missing or underdeveloped pages:

* `docs/getting-started/quickstart.md`
* `docs/getting-started/first-model.md`
* `docs/safety/safe-to-commit.md`
* `docs/safety/flexo-startup-dataset.md`
* `docs/services/flexo.md`
* `docs/services/syson.md`
* `docs/workflows/bridge-capability-matrix.md`
* `docs/troubleshooting/index.md`
* `docs/reference/cli.md` generated or validated from Click help
* `docs/developer/architecture.md`

The current `docs/lab/modeling-conventions.md` is good and should become the bridge capability matrix or link to it.

---

## CLI and workflow review

| Command/group                  | Review                                                                                                                                                                                                                                                                                             |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mbse-lab init`                | Good separation from `bootstrap`: it prepares env files and optional workspace without starting services. Dry-run behavior is tested. Improve by generating a random SysON password and writing a local config file or `.envrc` snippet so the workspace setting is less ephemeral.                |
| `mbse-lab doctor`              | Strong command. It checks Python, Docker, Compose, repo markers, env files, workspace, ports, HTTP reachability, and SysON DB credential drift. Improve output grouping into “required failures,” “warnings,” and “next commands.”                                                                 |
| `mbse-lab doctor --fix`        | Useful because it applies low-risk fixes only. It can create SysON `.env` and workspace layout, then prints next commands. Improve by refusing/default-warning on `change-me`, checking dirty `cluster.nq`, and explaining that it cannot persist shell env vars.                                |
| `mbse-lab bootstrap`           | Compelling first-use command. It initializes FleON envs, starts services, initializes Flexo org, backs up Flexo, runs status, and prints service URLs. Improve by waiting for SysON HTTP/GraphQL readiness and by making the final “Next” command `mbse-lab first-model "My First Model"`.   |
| `mbse-lab bootstrap --dry-run` | Excellent. It lowers anxiety and is covered by tests. Keep it prominent in README.                                                                                                                                                                                                             |
| `mbse-lab services up`         | Good naming and supports `--flexo/--no-flexo`, `--syson/--no-syson`, timeout, and dry-run. Add readiness probes and clearer failure messages for port conflicts.                                                                                                                                   |
| `mbse-lab services logs`       | Useful and simple. Consider allowing service-specific names and printing “most useful next cmand” after errors.                                                                                                                                                                                  |
| `mbse-lab services down`       | Safe default because it does not remove volumes. Good. Keep destructive volume removal out of the default CLI unless guarded.                                                                                                                                                                    |
| `mbse-lab first-model`         | One of the strongest features. It gives a meaningful end-to-end result. Improve by preflighting service readiness, requiring/strongly warning on missing workspace, and printing a short explanation of what was created.                                                                          |
| `mbse-lab flexo list`          | Intuitive. Output should be table-like with ID, name, default branch/commit if available, and next commands. Current wrapper delegates to the bridge script.                                                                                                                                       |
| `mbse-lab syson list`          | Intuitive. Output should include project ID, editing context ID, and how to get root namespace.                                                                                                                                                                                                    |
| `mbse-lab bridge run`          | Good name. It should produce a manifest and clearly state rendered/skipped elements. It should also support creating the SysON project and discovering namespace automatically when possible.                                                                                                      |
| `mbse-lab share-check`         | Essential command, but must be stronger. It should block tracked exports and tracked mutable seed data, not just untracked generated exports and known secret patterns.                                                                                                                            |
| `mbse-lab report`              | Useful for handoff and local status. The HTML currently renders escaped Markdown inside a `<pre>`, which is functional but not very polished.                                                                                                                                                      |
| `mbse-lab cleanup`             | Good safety posture: removes reports, diagnostics, runs, and tmp; leaves exports, env files, service data, backups, and `site/` unless explicitly requested.                                                                                                                                       |

---

## Flexo/SysON bridge review

The bridge architecture is understandable. The repo consistently describes:

```text
Flexo SysML v2 REST JSON -> SysML v2 textual .sysml -> SysON GraphQL import
```

That is a good, honest exchange path for a local lab.

The role split is also clear: Flexo is the API-driven model repository path; SysON is a graphical review/editing environment for imported textual content.

The file/text integration path is documented, but users could still overestimate it. The repo says unsupported elements are preserved in JSON but not rendered; diagram layout is not round-tripped.  The next step should be machine-readable capability reporting.

Current bridge strengths:

* Deterministic renderer.
* Supported-type table.
* Fixtures for a basic package, RF link budget, and container deployment.
* Live Flexo export and SysON import evals.
* Run log support in the bridge script.
* `first-model` provides a guided end-to-end flow.

Current bridge concerns:

* Unsupported elements are silently skipped from `.sysml`.
* No sidecar manifest documenting lossiness.
* Bridge and deployment verification logic live in the same large script.
* Manual `bridge run` still requires users to know the SysON project ID and namespace ID.
* The possible `syson-roots` commit-ID bug should be fixed before relying on manual bridge workflows.

Generated `.json` and `.sysml` artifacts are stored safely only when `MBSE_MODEL_WORKSPACE` is set or output paths are explicit. Without that, they go to repo-local `exports/`.

---

## Data safety and publishing review

The repo has a strong safety intent and several good mechanisms:

* Runtime `.env` files are ignored.
* Publishable `.example` files are committed.
* SysON Postgres data is ignored.
* Flexo MinIO data is ignored.
* Flexo backups are ignored.
* Diagnostics, reports, runs, temp output, logs, and MkDocs site output are ignored.
* `exports/**` is ignored except the README.
* `share-check` exists and is integrated into `make check`.

The main safety weaknesses are:

1. **Tracked `cluster.nq` can contain runtime graph state.** This is the biggest issue. The backup command refreshes it by default.

2. **`share-check` does not appear to block tracked private exports.** It catches untracked files under `exports/flexo/` and `exports/sysml/`, but force-added files are not blocked by the current forbidden tracked paths.

3. **Repo-local `exports/` remains the default fallback.** Ignoring the files helps, but it does not prevent local leakage or force-add accidents.

4. **SysON starts from a default example password.** Generate a random local password instead.

5. **Diagnostics are redacted, but model names/IDs may still be sensitive.** The redaction patterns focus on credentials. For private projects, diagnostics should have a “safe for public sharing?” mode that can omit project lists, names, and import logs.

6. **Cleanup is safe, but backup/restore/destructive paths need stronger guardrails.** `cleanup` avoids service data and exports, which is good. But `flexo_mms_env.py restore` and backup seed update are potentially destructive or publish-sensitive and should require clearer intent.

Recommended stronger guardrails:

```text
- Make MBSE_MODEL_WORKSPACE required for bridge/first-model unless explly overridden.
- Stop updating tracked cluster.nq by default.
- Add share-check detection for tracked exports, tracked .sysml/.nq/.trig, and dirty cluster.nq.
- Add allowlist metadata for curated public examples.
- Generate SysON password during init/bootstrap.
- Add doctor checks for default credentials.
- Add diagnostics mode: --public-safe, which strips project names/IDs and import details.
```

---

## Build, test, and CI review

The local build/test command surface is good. The Makefile exposes `install-cli`, `bootstrap`, `first-model`, `doctor`, `report`, `cleanup`, `share-check`, `up`, `down`, `status`, `logs`, `diagnostics`, `check`, `docs-check`, `docs-build`, `docs-serve`, `eval`, `live-eval`, `backup`, `rotate-secrets`, `deployment-contract`, and `deployment-verify`.

The Python/Hatch setup is clean. `pyproject.toml` defines build metadata, the CLI entry point, Ruff settings, Hatch lint/test/docs environments, and strict MkDocs build.

CI is meaningful for a local lab repo. It checks out code, installs Hatch/pre-commit, runs pre-commit, builds docs, prepares runtime env files, and runs `make check`.  The docs workflow builds and deploys GitHub Pages.

Tests are usefully categorized:

* Deterministic bridge rendering and deployment contract tests.
* CLI behavior and safety tests.
* Live Flexo export evals gated behind `MBSE_LIVE_EVAL=1`.
* Live SysON import evals gated behind `MBSE_LIVE_EVAL=1`.
* Live deployment runtime evals gated behind `MBSE_LIVE_EVAL=1`.

Gaps to address:

* Add tests for tracked export blocking.
* Add tests for dirty/tracked `cluster.nq` detection.
* Add tests for default SysON password warnings.
* Add tests for bridge render manifests and skipped-element summaries.
* Add a unit test for `syson-roots` resolving latest commit ID.
* Add CLI help snapshot tests or generated CLI reference docs.
* Add docs examples that validate `mbse-lab` commands, not only `make` and script subcommands.
* Consider a scheduled/manual CI workflow for full Docker smoke tests, separate from normal PR CI.

---

## Code maintainability review

The package layout under `src/mbse_lab/` is moving in the right direction:

```text
cli.py
constants.py
health.py
http.py
model.py
reports.py
share.py
shell.py
workspace.py
```

These modules have reasonable names and responsibilities. The `health`, `workspace`, `share`, `reports`, and `model` modules are especially useful separations.

The maintainability problem is that significant production logic still lives in scripts:

* `scripts/flexo_mms_env.py` generates env files, Compose files, secrets, service JWTs, starts/stops Flexo, checks status, fetches tokens, backs up/restores Fuseki.
* `scripts/flexo_syson_bridge.py` handles Flexo export, SysON GraphQL, textual rendering, deployment contracts, Docker verification, run logging, and CLI parsing.

This creates duplication:

* HTTP helpers exist in both package and script form.
* URL constants exist in both package and script form.
* Identifier sanitization exists in both package and script form.
* Flexo/SysON model operations exist in both package and bridge script form.
* Deployment verification lives in a bridge script even though it is broader than bridge behavior.

Error handling is generally clear but basic. `click.ClickException` in the package and `fail()` in scripts produce readable failures. Subprocess helpers show command and exit code, but they do not always include captured stderr/stdout.

Typed interfaces are limited. There are a few dataclasses, but snapshots, render results, deployment contracts, diagnostics manifests, and run logs are plain dictionaries. For a bridge that will grow, typed data models would improve confidence and testability.

Recommended refactor path:

```text
src/mbse_lab/flexo.py
src/mbse_lab/syson.py
src/mbse_lab/bridge/render.py
src/mbse_lab/bridge/contracts.py
src/mbse_lab/bridge/runlog.py
src/mbse_lab/deployment/contract.py
src/mbse_lab/deployment/verify.py
src/mbse_lab/env/flexo.py
src/mbse_lab/env/syson.py
```

Then make `scripts/*.py` compatibility shims that import package functions.

---

## Usability-oriented recommendations

### Quick wins

1. Add a five-minute quickstart at the top of README:

   ```bash
   make install-cli
   mbse-lab bootstrap --dry-run --model-workspace ~/work/my-private-models
   mbse-lab bootstrap --model-workspace ~/work/my-private-models
   export MBSE_MODEL_WORKSPACE=~/work/my-private-models
   mbse-lab first-model "My First Model"
   mbse-lab share-check
   ```

2. Add a “Which command should I run?” table:

   ```text
   First s        mbse-lab bootstrap
   Check environment  mbse-lab doctor
   Start services     mbse-lab services up
   Create demo model  mbse-lab first-model
   Bridge existing    mbse-lab bridge run
   Before sharing     mbse-lab share-check
   ```

3. Add a “safe to commit / do not commit” table in README and docs.

4. Add expected output snippets for `doctor`, `bootstrap`, and `first-model`.

5. Change `bootstrap` final next command to `mbse-lab first-model "My First Model"`.

6. Add a high-visibility warnihen writing generated artifacts to repo-local `exports/`.

7. Have `doctor` flag `deploy/syson/.env` if it contains `SYSON_POSTGRES_PASSWORD=change-me`.

8. Add `share-check` rules for tracked `exports/flexo/**`, tracked `exports/sysml/**`, tracked `.sysml`, tracked `.nq`, tracked `.trig`, and dirty `deploy/flexo-mms/mount/cluster.nq`.

9. Fix `syson-roots` to resolve the latest commit ID before fetching roots.

10. Add a bridge output comment and/or sidecar manifest showing skipped unsupported element types.

### Medium improvements

1. Split README into concise quickstart plus detailed docs pages.

2. Add task-oriented docs pages for getting started, local services, bridge workflow, private workspace safety, and troubleshooting by symptom.

3. Generate CLI reference docs from Click help and validate them in CI.

4. Add service readiness waits for Flexo and SysON in `bootstrap` and `services up`.

5. Generate random SysON database passwords during init/bootstrap.

6. Add a local ignored config file such as `.mbse-lab.local.json` or `.envrc.example` to remember the chosen model workspace.

7. Create an explicit curated-example convention, such as:

   ```text
   exports/examples/
   exports/examples/README.md
   exports/examples/*.public.json
   exports/examples/*.public.sysml
   ```

8. Add tests for tracked private artifact blocking.

9. Add a bridge capability matrix page with supported, partially supported, and unsupported SysML v2 elements.

10. Add a public-safe diagnostics mode that omits project names, IDs, and import details.

### Larger design improvements

1. Refactor scripts into package modules and keep scripts as shims.

2. Define explicit bridge data contracts for Flexo snapshots, render results, SysON import results, run logs, and deployment contracts.

3. Add plugin-like renderers/importers so the bridge can grow without one monolithic script.

4. Add a validated fixture suite for SysML v2 element coverage.

5. Add a guided first-run wizard or TUI that performs prerequisite checks, workspace setup, service startup, first-model creation, and report generation.

6. Separate public tooling seed data from local runtime Flexo graph state. This is the most important architectural safety improvement.

7. Add a manual/scheduled full Docker smoke workflow in GitHub Actions, separate from normal CI.

---

## Suggested README outline

```text
# SysML v2 Local Lab Kit

## What this repo is
- Local reusable tooling for Flexo MMS, SysON, bridge workflows, diagnostics, docs, and fixtures.

## What this repo is not
- Not the long-term home for real/private SysML v2 models.
- Not a live Flexo/SysON synchronization product.
- Not a full SysML v2 renderer.

## Five-minute quickstart
1. Clone
2. Install CLI
3. Bootstrap dry-run
4. Bootstrap
5. Set/confirm model workspace
6. Run first model
7. Open service URLs
8. Run share-check

## Prerequisites
- Docker + Compose plugin
- Python 3.10+
- Hatch
- Optional: curl, jq

## First model workflow
- What `mbse-lab first-model` creates
- Expected output
- Where generated artifacts go

## Common commands
- `doctor`
- `services up/down/logs`
- `first-model`
- `bridge run`
- `report`
- `cleanup`
- `share-check`

## Private model workspace safety
- Recommended public/private layout
- `MBSE_MODEL_WORKSPACE`
- Safe to commit / do not commit table
- Backup and startup dataset warning

## Flexo vs SysON roles
- Flexo: API-driven durable repository path
- SysON: graphical review/editing path
- No live sync

## Bridge scope and limitations
- JSON snapshot
- Textual `.sysml`
- SysON import
- Supported element types summary
- Unsupported/skipped behavior
- No diagram round-trip

## Documentation
- Getting started
- Local services
- Bridge workflow
- Troubleshooting
- Maintainer guide

## Troubleshooting starter
- Port conflicts
- Missing Flexo org
- SysON password drift
- Import succeeds but looks empty

## Contributing / maintainer notes
- `make check`
- `make docs-build`
- `make live-eval`
- Release process link
```

---

## Suggested GitHub issue list

### Onboarding

**Title:** Add five-minute quickstart to README
**Problem:** The fastest path is present but buried.
**Proposed change:** Add a top-level quickstart with `make install-cli`, `bootstrap --dry-run`, `bootstrap`, `first-model`, and `share-check`.
**Acceptance criteria:** A new user can follow one README section from clone to first SysML import; expected output snippets included.
**Suggested labels:** `docs`, `onboarding`, `quick-win`

**Title:** Add “Which command should I run?” table
**Problem:** Users see Make, CLI, and scriommands.
**Proposed change:** Add a command decision table near the top of README and docs index.
**Acceptance criteria:** Table covers setup, doctor, services, first model, bridge, diagnostics, cleanup, and share-check.
**Suggested labels:** `docs`, `developer-experience`

**Title:** Make `bootstrap` final next step point to `first-model`
**Problem:** Current next steps do not clearly drive users to a first useful model.
**Proposed change:** Print `mbse-lab first-model "My First Model"` after successful bootstrap.
**Acceptance criteria:** Bootstrap output includes service URLs and first-model command.
**Suggested labels:** `cli`, `onboarding`, `quick-win`

### Documentation

**Title:** Split README details into task-oriented docs pages
**Problem:** README is accurate but dense.
**Proposed change:** Keep quickstart and overview in README; move detailed service, credential, backup, and bridge operations into docs.
**Acceptance criteria:** README is shorter; docs pages exist for services, bridge, safety, and troubleshooting.
**Suggested labels:** `docs`, `information-architecture`

**Title:** Add troubleshooting-by-symptom page
**Problem:** Troubleshooting is scattered and short.
**Proposed change:** Add symptoms for port conflicts, Docker not running, Flexo org missing, SysON password drift, SysON slow startup, import appears empty.
**Acceptance criteria:** Each symptom has cause, commands to run, and safe recovery steps.
**Suggested labels:** `docs`, `supportability`

**Title:** Add bridge capability matrix
**Problem:** Supported types are listed, but users need a clearer capability view.
**Proposed change:** Create a matrix of supported, skipped, partially supported, and planned SysML v2 elements.
**Acceptance criteria:** Matrix links to fixtures/tests and is referenced from README and bridge docs.
**Suggested labels:** `docs`, `bridge`, `mbse`

### CLI usability

**Title:** Add readiness waits for SysON and Flexo APIs
**Problem:** Startup waits mostly check containers, not API readiness.
**Proposed change:** Add readiness probes to `bootstrap` and `services up`.
**Acceptance criteria:** Commands wait for Flexo `/projects` and SysON `/` or GraphQL before reporting ready.
**Suggested labels:** `cli`, `services`, `reliability`

**Title:** Require explicit output location for model-generating commands when workspace is unset
**Problem:** Artifacts default to repo-local `exports/`.
**Proposed change:** Require `MBSE_MODEL_WORKSPACE`, explicit output path, or `--allow-repo-exports`.
**Acceptance criteria:** `first-model`, `flexo export`, `bridge render`, and `bridge run` warn or fail safely when workspace is unset.
**Suggested labels:** `cli`, `data-safety`, `breaking-change`

**Title:** Fix `syson-roots` commit ID handling
**Problem:** Bridge script appears to use project ID as commit ID for roots lookup.
**Proposed change:** Resolve latest commit ID before fetching roots; optionally support `--commit-id`.
**Acceptance criteria:** Unit test verifies URL uses latest commit ID.
**Suggested labels:** `bug`, `bridge`, `cli`

### Data safety

**Title:** Stop updating tracked `cluster.nq` by default during backup
**Problem:** Backup can write live graph state into a tracked file.
**Proposed change:** Make backup write ignored backup files only unless an explicit seed-update flag is used.
**Acceptance criteria:** Default backup does not modify tracked files; seed update requires explicit flag and warning.
**Suggested labels:** `data-safety`, `flexo`, `high-priority`

**Title:** Expand `share-check` to block tracked model artifacts
**Problem:** Current share-check catches some untracked exports but not force-added tracked exports.
**Proposed change:** Block tracked generated exports, `.sysml`, `.nq`, `.trig`, and model-looking JSON outside allowlisted fixtures/examples.
**Acceptance criteria:** Tests cover tracked export, tracked `.sysml`, and dirty `cluster.nq`.
**Suggested labels:** `data-safety`, `testing`, `share-check`

**Title:** Generate random SysON database password on init/bootstrap
**Problem:** SysON `.env.example` uses `change-me`, and init copies it.
**Proposed change:** Generate a local random password when creating `deploy/syson/.env`.
**Acceptance criteria:** New `.env` does not contain `change-me`; doctor warns on default password.
**Suggested labels:** `security`, `cli`, `services`

**Title:** Add public-safe diagnostics mode
**Problem:** Diagnostics redact secrets but may include sensitive project names/IDs.
**Proposed change:** Add `mbse-lab diagnostics --public-safe` to omit or hash model/project details.
**Acceptance criteria:** Public-safe diagnostics excludes project names, project IDs, import logs, and generated artifact paths unless explicitly allowed.
**Suggested labels:** `data-safety`, `diagnostics`

### Testing/CI

**Title:** Add tests for share-check safety gaps
**Problem:** Tests do not cover tracked private exports or tracked seed mutation.
**Proposed change:** Add unit tests for tracked exports, tracked `.sysml`, tracked `.trig`, dirty `cluster.nq`, and default credentials.
**Acceptance criteria:** New tests fail before share-check fixes and pass after.
**Suggested labels:** `testing`, `data-safety`

**Title:** Generate and validate CLI reference docs
**Problem:** CLI docs can drift from Click command definitions.
**Proposed change:** Generate CLI reference from `mbse-lab --help` and subcommand help, or validate docs snippets.
**Acceptance criteria:** CI fails if documented commands/options drift.
**Suggested labels:** `docs`, `cli`, `ci`

**Title:** Add manual full-stack smoke workflow
**Problem:** Normal CI does not run Flexo/SysON live workflows.
**Proposed change:** Add `workflow_dispatch` CI that starts the Docker stack and runs `first-model`, deployment verify, and live evals.
**Acceptance criteria:** Manual workflow produces logs/artifacts and does not run on every PR by default.
**Suggested labels:** `ci`, `services`, `live-eval`

### Bridge workflow

**Title:** Add bridge render manifest with skipped-element summary
**Problem:** Unsupported SysML v2 elements are skipped without a clear output summary.
**Proposed change:** Write a JSON manifest and optional `.sysml` comment block with rendered/skipped counts and type histogram.
**Acceptance criteria:** Manifest includes source project, commit, renderer version, rendered types, skipped types, output paths.
**Suggested labels:** `bridge`, `usability`, `mbse`

**Title:** Add bridge auto-create SysON review project option
**Problem:** Manual bridge requires users to create a SysON project and namespace.
**Proposed change:** Add `mbse-lab bridge run --create-syson-project "Name"` that creates project and discovers root package.
**Acceptance criteria:** Existing `first-model` logic is reused; user can bridge with one command after Flexo project ID.
**Suggested labels:** `bridge`, `cli`, `onboarding`

**Title:** Add fixture coverage for more SysML v2 element types
**Problem:** Renderer subset is narrow and should grow with confidence.
**Proposed change:** Add fixture-driven tests for each planned element type.
**Acceptance criteria:** Capability matrix links each supported type to at least one fixture assertion.
**Suggested labels:** `bridge`, `testing`, `mbse`

### Maintainability

**Title:** Refactor bridge script into package modules
**Problem:** `flexo_syson_bridge.py` mixes bridge, rendering, SysON, Flexo, deployment, and Docker verification logic.
**Proposed change:** Move logic into `src/mbse_lab/bridge`, `src/mbse_lab/flexo.py`, `src/mbse_lab/syson.py`, and `src/mbse_lab/deployment`.
**Acceptance criteria:** Script remains as shim; tests import package modules; no duplicated HTTP/sanitize/default constants.
**Suggested labels:** `maintainability`, `refactor`, `bridge`

**Title:** Add typed data contracts for bridge and deployment reports
**Problem:** Snapshots, render results, deployment contracts, and run logs are plain dicts.
**Proposed change:** Introduce dataclasses or typed models with validation helpers.
**Acceptance criteria:** Renderer and deployment verification functions return typed results or validated dictionaries; tests cover malformed inputs.
**Suggested labels:** `maintainability`, `typing`, `architecture`

---

## Final assessment

**Usability rating: 7/10**

The repo earns a 7 because it already has a clear purpose, a meaningful CLI, a credible first-model workflow, useful Docker organization, real diagnostics/reporting/cleanup commands, strong documentation intent, deterministic tests, live eval hooks, and CI. A technically capable user can probably get to a first useful SysML v2 workflow.

It does not score higher because the public/private boundary is not yet enforceable enough. The tracked Flexo startup dataset and default backup behavior are the largest concern. The README is also too dense for first-time use, and the bridge needs better lossiness reporting.

What would raise it by one point:

* Add the five-minute quickstart.
* Make CLI-first docs the default.
* Fix `syson-roots`.
* Add readiness waits.
* Expand `share-check` to catch tracked exports and dirty `cluster.nq`.

What would raise it by three points:

* Redesign the artifact/runtime boundary so private Flexo graph state cannot easily enter tracked files.
* Require or persist private model workspace configuration for model-generating workflows.
* Add bridge manifests and a capability matrix.
* Refactor bridge/deployment logic into typed package modules.
* Add task-oriented docs and a full-stack manual smoke workflow.

The repo should prioritize **data-boundary hardening first**, then **README/onboarding simplification**, then **bridge transparency and maintainability**.
