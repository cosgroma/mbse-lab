# OpenMBEE View Editor Flexo Experiment

This page records redacted request evidence for the experimental OpenMBEE View
Editor deployment in `deploy/view-editor/`.

The experiment is not part of the supported SysML v2 graphical workflow. SysON
remains the documented graphical review path unless this experiment proves a
viable View Editor integration.

## Runtime Under Test

Evidence captured on 2026-05-01.

- View Editor image: `openmbee/view-editor:3.6.1-omg`
- View Editor URL: `http://localhost:18091/`
- Flexo Layer1 URL from host: `http://localhost:18080`
- Flexo SysML v2 URL from host: `http://localhost:18083`
- Flexo project used for path probes:
  `aceb2496-9cca-4e97-9b17-bcfd5b076a4b`

The published View Editor image uses the legacy Exec-era URL shape:

- Login: `/alfresco/service/api/login`
- Projects: `/alfresco/service/projects`
- Orgs: `/alfresco/service/orgs`
- Refs: `/alfresco/service/projects/<project-id>/refs`
- Documents:
  `/alfresco/service/projects/<project-id>/refs/<ref-id>/documents`

The image rewrites `angular-mms-grunt-servers.json` at startup from
`VE_HOST`, `VE_MMS_HOST`, and `VE_MMS_PORT`.

## Layer1 Target

View Editor was started with its default experiment target:

```text
VE_MMS_HOST=layer1-service
VE_MMS_PORT=8080
```

The generated container proxy config was:

```json
{
  "host": "localhost",
  "acs_host": "layer1-service",
  "acs_port": "8080"
}
```

Observed request summary:

| Request | Status | Response summary |
| --- | ---: | --- |
| `GET http://localhost:18091/` | 200 | View Editor HTML shell |
| `GET http://localhost:18091/alfresco/service/projects` | 200 | View Editor HTML shell, not backend JSON |
| `GET http://localhost:18091/alfresco/service/orgs` | 200 | View Editor HTML shell, not backend JSON |
| `GET http://localhost:18091/alfresco/service/projects/<project-id>/refs` | 200 | View Editor HTML shell, not backend JSON |
| `GET http://localhost:18091/alfresco/service/projects/<project-id>/refs/master/documents` | 200 | View Editor HTML shell, not backend JSON |
| `POST http://localhost:18091/alfresco/service/api/login` | 404 | View Editor local server response: `Cannot POST /alfresco/service/api/login` |
| `GET http://localhost:18080/alfresco/service/projects` | 404 | Direct Layer1 target has no legacy Alfresco service path |
| `GET http://localhost:18080/projects` | 404 | Direct Layer1 target has no top-level projects resource |
| `GET http://localhost:18080/orgs` | 401 | Direct Layer1 org endpoint requires authorization |
| `POST http://localhost:18080/alfresco/service/api/login` | 404 | Direct Layer1 target has no legacy Alfresco login path |

Layer1 result: the published View Editor image did not proxy the legacy GET
paths to Layer1 in this Docker mode; it served the single-page app shell
instead. The legacy login POST failed at the View Editor local server. Direct
Layer1 probing also showed no legacy Alfresco login or project paths.

## SysML v2 Target

View Editor was restarted against the Flexo SysML v2 service:

```text
VE_MMS_HOST=flexo-sysmlv2
VE_MMS_PORT=8080
```

The generated container proxy config was:

```json
{
  "host": "localhost",
  "acs_host": "flexo-sysmlv2",
  "acs_port": "8080"
}
```

Observed request summary:

| Request | Status | Response summary |
| --- | ---: | --- |
| `GET http://localhost:18091/` | 200 | View Editor HTML shell |
| `GET http://localhost:18091/alfresco/service/projects` | 200 | View Editor HTML shell, not backend JSON |
| `GET http://localhost:18091/alfresco/service/orgs` | 200 | View Editor HTML shell, not backend JSON |
| `GET http://localhost:18091/alfresco/service/projects/<project-id>/refs` | 200 | View Editor HTML shell, not backend JSON |
| `GET http://localhost:18091/alfresco/service/projects/<project-id>/refs/master/documents` | 200 | View Editor HTML shell, not backend JSON |
| `POST http://localhost:18091/alfresco/service/api/login` | 404 | View Editor local server response: `Cannot POST /alfresco/service/api/login` |
| `GET http://localhost:18083/alfresco/service/projects` | 404 | Direct SysML v2 target has no legacy Alfresco service path |
| `GET http://localhost:18083/projects` | 200 | Direct SysML v2 target returns OMG-style project JSON array |
| `GET http://localhost:18083/orgs` | 404 | Direct SysML v2 target has no org endpoint |
| `POST http://localhost:18083/alfresco/service/api/login` | 404 | Direct SysML v2 target has no legacy Alfresco login path |

SysML v2 result: direct Flexo SysML v2 project discovery works at `/projects`,
but the response shape is the OMG API shape, not the legacy MMS envelope that
View Editor expects. The legacy View Editor paths are absent.

## View Editor 5.0.0 Source Build Probe

Evidence captured on 2026-05-01.

Public image lookup found no usable `openmbee/exec-ve:5.0.0` image. Docker Hub
lists `openmbee/view-editor`, but the public OpenMBEE namespace only exposed
the older `openmbee/view-editor:3.6.1-omg` View Editor image during this
probe. The `Open-MBEE/exec-ve` source repository does contain a `5.0.0` tag
with a root `Dockerfile`.

The source-tag Dockerfile path was tested from `Open-MBEE/exec-ve` tag
`5.0.0`:

```bash
docker build -t mbse-view-editor:5.0.0-local /tmp/exec-ve-5.0.0
```

That exact build did not complete. The tag's `.dockerignore` excludes dotfiles
needed by the build's lint/format precheck, so ESLint first failed because it
could not find its configuration. After copying the source tree to a temporary
context and allowing the lint/format config files through `.dockerignore`, the
build reached the lint step but failed on existing lint and formatting errors.

As a narrower source-build proof, the same tag was built with a temporary
Dockerfile that keeps the upstream dependency install and production webpack
bundle, but bypasses the `prebuild` lint/format gate:

```bash
docker build \
  -f /tmp/exec-ve-5.0.0-build/Dockerfile.webpack \
  -t mbse-view-editor:5.0.0-webpack-local \
  /tmp/exec-ve-5.0.0-build
```

That image built successfully and served the View Editor 5.0.0 static bundle
from nginx. It also confirmed the 5.x runtime config file can be replaced after
image build by mounting over:

```text
/usr/share/nginx/html/config/config.json
```

The local proof container was started on host port `18092` with `apiUrl`
pointing at the Flexo SysML v2 service:

```text
View Editor 5.0.0 proof URL: http://localhost:18092/
apiUrl: http://localhost:18083
```

Observed request summary:

| Request | Status | Response summary |
| --- | ---: | --- |
| `GET http://localhost:18092/` | 200 | View Editor 5.0.0 HTML shell |
| `GET http://localhost:18092/config/config.json` | 200 | Runtime config with `apiUrl` set to `http://localhost:18083` |
| `GET http://localhost:18083/projects` | 200 | OMG-style project JSON array |
| `GET http://localhost:18083/authentication` | 404 | Flexo SysML v2 has no View Editor 5.x authentication endpoint |
| `GET http://localhost:18083/checkAuth` | 404 | Flexo SysML v2 has no View Editor 5.x auth-check endpoint |
| `GET http://localhost:18083/orgs` | 404 | Flexo SysML v2 has no View Editor 5.x org endpoint |
| `GET http://localhost:18083/projects/<project-id>/refs` | 404 | Flexo SysML v2 has no View Editor 5.x refs endpoint |
| `OPTIONS http://localhost:18083/projects` from `http://localhost:18092` | 405 | Browser CORS preflight would not succeed for this direct static-app target |

View Editor 5.0.0 result: the newer source line gives us a buildable local
test path if we bypass the source tag's lint/format gate, and its runtime
configuration can point directly at the Flexo SysML v2 host port. That removes
the legacy `openmbee/view-editor:3.6.1-omg` proxy behavior as the only
explanation for failure. However, the 5.x client still expects MMS-style
authentication, org, ref, document/view, element, artifact, and search
resources that are not exposed by Flexo SysML v2.

## Interim Compatibility Finding

The published `openmbee/view-editor:3.6.1-omg` image is not directly compatible
with the current local Flexo stack.

There are two separate blockers:

- Runtime/proxy blocker: in this image mode, legacy GET paths under
  `/alfresco/service/...` are handled by the View Editor single-page-app
  fallback instead of being proxied to the configured backend.
- API contract blocker: neither Flexo Layer1 nor Flexo SysML v2 exposes the
  legacy Alfresco MMS login, document, view, and project resources expected by
  this View Editor generation. Flexo SysML v2 exposes OMG SysML v2 resources
  instead.

The next useful probe is either to run a known legacy MMS/View Editor baseline
to prove the image behavior against its intended backend, or to build the
current View Editor 5.x source with explicit Flexo-facing configuration to see
whether its newer container path proxies requests differently. Neither path is
expected to remove the need for a legacy MMS document/view facade if View Editor
is to work with Flexo SysML v2.
