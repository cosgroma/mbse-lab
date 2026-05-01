# OpenMBEE View Editor Flexo Experiment

## Objective

Evaluate whether OpenMBEE View Editor can be used with the current local Flexo
MMS deployment, including `flexo-mms-sysmlv2`, and determine whether any
compatibility layer is needed before treating it as a supported graphical
frontend option.

The experiment should answer:

- Can View Editor authenticate against the local Flexo MMS auth service?
- Can View Editor discover or open content from the local Flexo Layer1 API?
- Can View Editor interact with SysML v2 projects exposed through
  `flexo-mms-sysmlv2`?
- If it fails, is the blocker configuration, authentication, CORS, or an API
  contract mismatch between legacy MMS document/view resources and the OMG
  SysML v2 API?

## Background

The current lab stack exposes:

- Flexo Layer1 API: `http://localhost:18080`
- Flexo auth login: `http://localhost:8082/login`
- Flexo SysML v2 API: `http://localhost:18083`

OpenMBEE's Flexo page describes `flexo-mms-sysmlv2` as an implementation of the
OMG SysML v2 API Services Specification built on Flexo MMS. The View Editor
documentation describes a client built around MMS REST API concepts such as
model elements, Documents, and Views. Those contracts may not match directly.

Primary references:

- <https://www.openmbee.org/flexo.html>
- <https://docs.openmbee.org/projects/ve/en/latest/index.html>
- <https://github.com/Open-MBEE/flexo-mms-sysmlv2>

## Relevant Files

- `deploy/flexo-mms/docker-compose.yml`
- `deploy/flexo-mms/README.md`
- `scripts/flexo_mms_env.py`
- `scripts/flexo_syson_bridge.py`
- Future candidate: `deploy/view-editor/docker-compose.yml`
- Future candidate: `docs/lab/view-editor-flexo-experiment.md`

## Experiment Scope

This is a contained spike. Do not add View Editor to the main supported workflow
until the request traces prove a viable integration path.

In scope:

- Inspect View Editor documentation, source, or container configuration.
- Run View Editor beside the current Flexo stack on the existing Docker network.
- Try both Layer1 and SysML v2 service URLs as backend targets.
- Capture browser/API request traces for login, project listing, content open,
  and document/view operations.
- Document the compatibility result.

Out of scope for the first spike:

- Building a production-grade adapter.
- Migrating private models into View Editor.
- Treating View Editor as a replacement for SysON.
- Committing runtime credentials, generated private exports, logs, or browser
  trace bundles.

## Planned Steps

1. Confirm the baseline Flexo deployment is healthy:

   ```bash
   python3 scripts/flexo_mms_env.py up --wait --timeout 60
   python3 scripts/flexo_mms_env.py status --with-sysmlv2 --strict
   python3 scripts/flexo_mms_env.py token
   python3 scripts/flexo_syson_bridge.py flexo-list-projects
   ```

2. Inventory View Editor runtime requirements:

   - Identify the current image or source repo to use.
   - Record required environment variables and backend URL configuration.
   - Determine whether configuration is build-time or runtime.
   - Identify expected authentication flow and API paths.

3. Create an isolated experimental compose file if needed:

   - Use a separate `deploy/view-editor/` directory.
   - Join the existing `flexo-mms-test-network`.
   - Avoid changing the supported Flexo compose file until compatibility is
     proven.

4. Probe backend targets in this order:

   - `http://layer1-service:8080` from inside Docker.
   - `http://flexo-sysmlv2:8080` from inside Docker.
   - `http://localhost:18080` from the browser.
   - `http://localhost:18083` from the browser.

5. Capture evidence:

   - Browser console errors.
   - Network request method, path, status, and response summary.
   - Container logs from View Editor and Flexo services.
   - Whether any operation reaches a useful model view.

6. If direct Flexo integration fails, run or inspect a known legacy MMS/View
   Editor baseline to separate View Editor setup issues from API mismatch.

7. Write a compatibility report with one of these outcomes:

   - Directly compatible.
   - Partially compatible with configuration constraints.
   - Not compatible without an adapter.
   - Inconclusive, with exact missing evidence.

## Expected Outcomes

Most likely outcome: View Editor will not work directly with
`flexo-mms-sysmlv2` because it expects legacy MMS document/view resources while
the SysML v2 service exposes the OMG SysML v2 API.

Useful partial outcome: authentication or basic Flexo Layer1 discovery works,
but document/view operations fail. That would define the adapter boundary.

Strong success outcome: View Editor can authenticate, discover content, and
open or edit useful model views using the current Flexo stack without custom
adapter code. If this happens, add a supported deployment path and user docs in
a follow-up chunk.

## Decisions And Tradeoffs

- Treat View Editor as experimental until proven against request traces.
- Keep SysON as the documented graphical SysML v2 review path for now.
- Prefer isolated compose and documentation over modifying the stable Flexo
  deployment during the spike.
- Preserve private model boundaries; use synthetic or disposable projects only.

## Validation Commands

For planning-only changes:

```bash
make check
```

If the future spike adds compose or docs navigation:

```bash
docker compose -f deploy/view-editor/docker-compose.yml config --quiet
make docs-build
make share-check
```

If live services are running during the future spike:

```bash
make deployment-verify
make live-eval
```

## Progress Log

- 2026-05-01: Created the experiment plan after reviewing OpenMBEE Flexo and
  View Editor references. The working hypothesis is that direct compatibility
  is unlikely without an adapter, but request tracing is needed before closing
  the question.

## Follow-Up Debt

- Identify the exact current View Editor image or source revision to test.
- Decide where to store redacted request-trace summaries.
- If an adapter is needed, define the minimal legacy MMS document/view facade
  required by View Editor.
