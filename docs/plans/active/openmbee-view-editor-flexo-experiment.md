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
- <https://github.com/Open-MBEE/exec-ve>

## Relevant Files

- `deploy/flexo-mms/docker-compose.yml`
- `deploy/flexo-mms/README.md`
- `scripts/flexo_mms_env.py`
- `scripts/flexo_syson_bridge.py`
- `deploy/view-editor/docker-compose.yml`
- `deploy/view-editor/README.md`
- `deploy/view-editor-5/docker-compose.yml`
- `deploy/view-editor-5/README.md`
- `docs/lab/view-editor-flexo-experiment.md`

## View Editor Runtime Inventory

Inventory completed on 2026-05-01 against `Open-MBEE/exec-ve` `develop`
commit `25c66a3b06db8ce6278872d67bca260aaae98b94` and the public Docker Hub
repository metadata.

- Current source repository: <https://github.com/Open-MBEE/exec-ve>.
- Latest GitHub release visible from the repository page: `5.0.0`.
- Public Docker Hub repository: `openmbee/view-editor`.
- Only public Docker tag returned by the Docker Hub registry API:
  `3.6.1-omg`, last updated 2020-08-04.
- `openmbee/view-editor:5.0.0`, `openmbee/view-editor:5.0.0-alpha`,
  `openmbee/view-editor:develop`, and `openmbee/view-editor:latest` did not
  have Docker manifests when checked locally with `docker manifest inspect`.
- The source Dockerfile builds View Editor from source with Node and serves the
  static bundle from nginx.
- The `config/example.json` file configures `apiUrl`, `printUrl`, `basePath`,
  branding, and login warning text. The example points `apiUrl` at
  `http://localhost:8080`.
- View Editor configuration is effectively build-time for source builds via
  `VE_ENV=<env_name> yarn build`; the README also describes mounting a config
  file into the container under `/opt/mbee/ve/config/<env_file_name>.json` for
  the nginx image.
- Runtime container knobs documented by the source README are `VE_PORT`,
  `VE_PROTOCOL`, and `VE_ENV`.

Observed client API expectations from `src/ve-utils/mms-api-client`:

- Authentication: `POST <apiUrl>/authentication`, token stored in browser
  local storage, and `GET <apiUrl>/checkAuth` for login checks.
- Repository discovery: `/orgs`, `/projects`, `/projects?orgId=<orgId>`,
  `/projects/<projectId>`, `/projects/<projectId>/refs`, commits, and mounts.
- Document/view operations:
  `/projects/<projectId>/refs/<refId>/groups`,
  `/projects/<projectId>/refs/<refId>/documents`,
  `/projects/<projectId>/refs/<refId>/views`,
  `/projects/<projectId>/refs/<refId>/views/<elementId>`, and
  `/projects/<projectId>/refs/<refId>/search`.
- Element/artifact operations:
  `/projects/<projectId>/refs/<refId>/elements`,
  `/projects/<projectId>/refs/<refId>/elements/<elementId>`, and artifact
  subresources below an element.

Initial API-shape note: `GET http://localhost:18083/projects` returns the local
Flexo SysML v2 projects, but as an OMG-style JSON array with `@id`, `@type`,
`defaultBranch`, `description`, and `name`. View Editor source expects MMS
response envelopes such as `projects`, `orgs`, `elements`, and document/view
resources. `GET /authentication` returned 404 on both local Layer1 and SysML v2
ports, which is consistent with View Editor requiring a legacy MMS auth
endpoint or an adapter rather than only the Flexo SSO login endpoint.

Follow-up source-build note: the `Open-MBEE/exec-ve` tag `5.0.0` includes a
root Dockerfile, but no public `openmbee/exec-ve:5.0.0` image was found. The
tagged Dockerfile failed locally because the Docker context excluded lint and
format configuration files and then failed on existing lint/format errors once
those files were allowed through. A narrower temporary image that ran the
production webpack bundle directly did build and serve View Editor 5.0.0 on
`http://localhost:18092/`, with a mounted runtime `config/config.json` pointing
`apiUrl` at `http://localhost:18083`. Direct Flexo probes still showed the 5.x
client endpoints are absent: `/authentication`, `/checkAuth`, `/orgs`, and
`/projects/<project-id>/refs` returned 404, while `/projects` returned only the
OMG-style SysML v2 project array.

Durable source-build note: `deploy/view-editor-5/` now provides a repeatable
source-build experiment for View Editor 5.0.0. It builds the production webpack
bundle directly and serves it through nginx with `apiUrl` set to
`http://localhost:18092/api`. nginx proxies `/api/` to
`http://flexo-sysmlv2:8080/` on the shared Docker network so browser traces are
not blocked first by CORS.

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

   Status: complete as of 2026-05-01. Flexo services started cleanly, strict
   status passed, token issuance succeeded, and the SysML v2 project list was
   reachable.

2. Inventory View Editor runtime requirements:

   - Identify the current image or source repo to use.
   - Record required environment variables and backend URL configuration.
   - Determine whether configuration is build-time or runtime.
   - Identify expected authentication flow and API paths.

   Status: complete as of 2026-05-01. Use the source repository for a current
   5.x experiment unless intentionally testing the older published
   `openmbee/view-editor:3.6.1-omg` image as a legacy baseline.

3. Create an isolated experimental compose file if needed:

   - Use a separate `deploy/view-editor/` directory.
   - Join the existing `flexo-mms-test-network`.
   - Avoid changing the supported Flexo compose file until compatibility is
     proven.

   Status: complete as of 2026-05-02. The legacy compose file runs
   `openmbee/view-editor:3.6.1-omg` on host port `18091`, joins the external
   `flexo-mms-test-network`, and defaults the View Editor proxy target to
   `layer1-service:8080`. The source-built 5.x compose file builds
   `Open-MBEE/exec-ve` tag `5.0.0`, serves it on host port `18092`, and proxies
   same-origin `/api/` requests to `flexo-sysmlv2:8080`.

4. Probe backend targets in this order:

   - `http://layer1-service:8080` from inside Docker.
   - `http://flexo-sysmlv2:8080` from inside Docker.
   - `http://localhost:18080` from the browser.
   - `http://localhost:18083` from the browser.

   Status: complete as of 2026-05-01 for HTTP-level proxy and backend shape
   probes. The published View Editor image served the HTML shell for legacy
   `GET /alfresco/service/...` paths and rejected legacy login POSTs locally.
   Direct Flexo probes confirmed that Layer1 and SysML v2 do not expose the
   legacy Alfresco MMS paths; SysML v2 does expose `/projects` as OMG-style
   project JSON.

5. Capture evidence:

   - Browser console errors.
   - Network request method, path, status, and response summary.
   - Container logs from View Editor and Flexo services.
   - Whether any operation reaches a useful model view.

   Status: complete for the direct-compatibility spike as of 2026-05-02. HTTP,
   container-log, and browser-level summaries are captured in
   `docs/lab/view-editor-flexo-experiment.md`. A Playwright login trace against
   the source-built 5.x deployment showed `POST /api/authentication` returning
   404. A synthetic-token trace showed `GET /api/checkAuth` returning 404.

6. If direct Flexo integration fails, run or inspect a known legacy MMS/View
   Editor baseline to separate View Editor setup issues from API mismatch.

   Status: complete enough for direct compatibility as of 2026-05-02. A durable
   source-built View Editor 5.0.0 deployment was added under
   `deploy/view-editor-5/`. This separated the older
   `openmbee/view-editor:3.6.1-omg` proxy behavior from the API contract
   mismatch: View Editor 5.x can be served, configured, and browser-tested
   against a same-origin Flexo SysML v2 proxy, but Flexo SysML v2 still does not
   expose the 5.x MMS authentication, auth-check, org, ref, document/view,
   element, artifact, and search endpoints.

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
docker compose -f deploy/view-editor-5/docker-compose.yml config --quiet
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
- 2026-05-01: Executed the Flexo baseline health chunk. `python3
  scripts/flexo_mms_env.py up --wait --timeout 60` started all expected Flexo
  MMS services, `python3 scripts/flexo_mms_env.py status --with-sysmlv2
  --strict` passed, `python3 scripts/flexo_mms_env.py token` returned a JWT,
  and `python3 scripts/flexo_syson_bridge.py flexo-list-projects` returned the
  local projects `MVP Smoke Model` and `Bridge Probe`. The token value was not
  recorded.
- 2026-05-01: Inventoried View Editor source and container options. The current
  source line is `Open-MBEE/exec-ve` 5.x, while Docker Hub only exposes the
  older `openmbee/view-editor:3.6.1-omg` tag. Source inspection shows View
  Editor is hard-wired to legacy MMS authentication, org/project/ref,
  document/view, element, artifact, and search endpoints. A quick local path
  check found `/authentication` is not present on the Flexo Layer1 or SysML v2
  ports.
- 2026-05-01: Added the isolated `deploy/view-editor/` experiment for the
  published `openmbee/view-editor:3.6.1-omg` image. Image inspection showed the
  container serves on port `9000` and rewrites its proxy config from `VE_HOST`,
  `VE_MMS_HOST`, and `VE_MMS_PORT`; the compose file exposes it on
  `http://localhost:18091/` and joins the existing Flexo Docker network without
  changing the supported Flexo deployment. A runtime smoke check started the
  container and `curl http://localhost:18091/` returned HTTP 200 after the image
  completed its Grunt asset build. Validation passed with `docker compose -f
  deploy/view-editor/docker-compose.yml config --quiet`, `make docs-build`, and
  `make check`.
- 2026-05-01: Captured request evidence for the published View Editor image
  against both `layer1-service:8080` and `flexo-sysmlv2:8080`. The image
  generated the expected proxy config for each target, but legacy
  `GET /alfresco/service/...` calls returned the View Editor HTML shell and the
  legacy login POST returned `Cannot POST /alfresco/service/api/login`,
  indicating the requests did not reach the configured backend. Direct backend
  probes confirmed the legacy Alfresco MMS paths are absent from both Flexo
  targets; SysML v2 only returned project data from `/projects` in OMG API
  shape. The redacted evidence summary is in
  `docs/lab/view-editor-flexo-experiment.md`. Validation passed with `docker
  compose -f deploy/view-editor/docker-compose.yml config --quiet`, `make
  docs-build`, and `make check`.
- 2026-05-01: Investigated the requested View Editor 5.0.0 image path before
  declaring adapter-only compatibility. No public `openmbee/exec-ve:5.0.0`
  image was found, but the `Open-MBEE/exec-ve` `5.0.0` tag contains a
  Dockerfile. The exact tagged build failed locally at the lint/format gate; a
  temporary webpack-only image built successfully as
  `mbse-view-editor:5.0.0-webpack-local` and served on
  `http://localhost:18092/` with `apiUrl=http://localhost:18083`. Direct probes
  against Flexo SysML v2 still returned 404 for View Editor 5.x
  `/authentication`, `/checkAuth`, `/orgs`, and
  `/projects/<project-id>/refs`; `/projects` remained reachable only as
  OMG-style SysML v2 JSON.
- 2026-05-02: Added the durable `deploy/view-editor-5/` source-build
  experiment. The compose path builds `Open-MBEE/exec-ve` tag `5.0.0`, runs the
  production webpack bundle directly, serves it from nginx on
  `http://localhost:18092/`, and proxies `http://localhost:18092/api/` to
  `flexo-sysmlv2:8080`. HTTP probes through the proxy returned 200 for
  `/api/projects` and 404 for `/api/authentication`, `/api/checkAuth`,
  `/api/orgs`, and `/api/projects/<project-id>/refs`. Playwright browser traces
  confirmed the login page renders, submitting synthetic credentials posts to
  `/api/authentication` and receives 404, and a synthetic preloaded token
  triggers `/api/checkAuth` and receives 404.

## Follow-Up Debt

- Write the compatibility report and close the direct-compatibility spike as
  not compatible without an adapter unless a new control run changes the
  evidence.
- Define the minimal legacy MMS document/view facade required by View Editor
  5.x.
