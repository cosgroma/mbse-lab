# Usability Remediation Plan

## Objective

Turn `docs/reviews/usability-review.md` into a sequence of focused, validated
changes that materially improve the lab kit's safety, onboarding, bridge
transparency, and maintainability.

The first priority is the public/private model-data boundary. The repo already
documents that private SysML v2 model data belongs outside this tooling repo,
but the review identifies several paths where local generated artifacts or
Flexo graph state can still become easy to stage or publish.

## Relevant Files

- `docs/reviews/usability-review.md`
- `README.md`
- `WORKFLOW.md`
- `docs/plans/README.md`
- `src/mbse_lab/share.py`
- `src/mbse_lab/constants.py`
- `src/mbse_lab/cli.py`
- `src/mbse_lab/workspace.py`
- `scripts/flexo_mms_env.py`
- `scripts/flexo_syson_bridge.py`
- `evals/test_bridge_cli.py`
- `evals/test_bridge_render.py`
- `deploy/flexo-mms/mount/cluster.nq`

## Planned Steps

1. Harden publish-safety checks.
   - Block force-added generated exports.
   - Flag tracked model-looking `.sysml`, `.nq`, and `.trig` artifacts outside
     curated allowlists.
   - Flag dirty `deploy/flexo-mms/mount/cluster.nq`.
   - Add focused deterministic tests.

2. Fix bounded bridge workflow bugs.
   - Update `syson-roots` so it resolves the latest SysON commit ID before
     listing roots.
   - Add a unit test for the REST URLs used by the command.

3. Reduce first-use friction.
   - Add a README five-minute quickstart.
   - Make `mbse-lab` the primary command surface in the top-level docs.
   - Point successful bootstrap output at
     `mbse-lab first-model "My First Model"`.

4. Make generated artifact placement safer.
   - Warn clearly when model-generating commands fall back to repo-local
     `exports/`.
   - Decide whether a later breaking change should require
     `MBSE_MODEL_WORKSPACE`, an explicit output path, or an explicit
     `--allow-repo-exports`.

5. Improve bridge transparency.
   - Emit a render manifest and skipped-element summary.
   - Link the manifest to a bridge capability matrix in docs.

6. Improve service readiness and local credentials.
   - Add readiness waits for Flexo and SysON in service startup/bootstrap.
   - Warn on default SysON database passwords.
   - Evaluate generating a random SysON password during init/bootstrap.

7. Defer broad maintainability work until user-facing risks are reduced.
   - Split bridge/deployment logic into package modules.
   - Add typed contracts for snapshots, render results, run logs, and
     deployment verification reports.

## Progress Log

- 2026-05-01: Created plan from usability review and selected the first chunk:
  publish-safety hardening plus the bounded `syson-roots` fix.
- 2026-05-01: Added an explicit `exports/examples/` convention, moved the
  tracked sample export there, expanded `share-check` coverage for tracked and
  ignored generated artifacts, and fixed `syson-roots` to resolve the latest
  SysON commit before fetching roots.
- 2026-05-01: Selected public-safe diagnostics as the next follow-up debt
  chunk. The approach is to omit sensitive project-list and recent-log evidence
  from public-safe bundles instead of attempting broad post-collection
  redaction.
- 2026-05-01: Added `mbse-lab diagnostics --public-safe` and
  `scripts/collect_diagnostics.py --public-safe` to collect reduced bundles that
  omit project-list probes and recent service logs.
- 2026-05-01: Moved the Flexo/SysON bridge implementation behind
  `mbse_lab.bridge` package modules, kept `scripts/flexo_syson_bridge.py` as a
  compatibility wrapper, and added typed validation for Flexo snapshots,
  deployment contracts, and deployment verification reports.
- 2026-05-01: Selected non-breaking repo-local export warnings for the generated
  artifact placement chunk. Commands still allow repo-local `exports/`, but
  warn when `MBSE_MODEL_WORKSPACE` is unset and no explicit output path was
  provided.
- 2026-05-01: Added `docs/reviews/recommended-features.md` to the published
  documentation review set and linked it from `docs/index.md` and MkDocs
  navigation.

## Validation Commands

Run focused checks during the first chunk:

```bash
hatch run test:eval
make share-check
```

Run the deterministic baseline before closing a broader remediation chunk:

```bash
make check
```

When README or MkDocs navigation changes:

```bash
make docs-build
```

When service startup, backup/restore, or import behavior changes and services
are running:

```bash
make live-eval
make deployment-verify
```

## Decisions And Tradeoffs

- Treat data-boundary hardening as the first priority because it affects trust
  in the public tooling repo.
- Keep the first implementation chunk narrow enough to validate quickly:
  `share-check` hardening and a small bridge URL bug.
- Do not refactor the bridge script before fixing user-visible safety and
  workflow defects; a refactor would make behavioral review harder.

## Follow-Up Debt

- Curated public export convention: decided and documented as
  `exports/examples/**/*.public.json` and `exports/examples/**/*.public.sysml`.
- Repo-local generated export policy: decided on non-breaking warnings for this
  branch. A future breaking change can still make repo-local exports an explicit
  opt-in after users have had a warning period.
- Public-safe diagnostics mode: implemented as `mbse-lab diagnostics
  --public-safe`; reduced bundles omit project-list probes and recent service
  logs.
- Move active plan to `docs/plans/completed/` when the review findings have been
  addressed or intentionally deferred with rationale.
