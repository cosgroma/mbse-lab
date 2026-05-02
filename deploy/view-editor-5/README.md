# OpenMBEE View Editor 5.x Experiment

This directory contains an isolated source-build experiment for OpenMBEE View
Editor 5.x. It exists to test the current View Editor source line against the
local Flexo SysML v2 service without relying on the older published
`openmbee/view-editor:3.6.1-omg` image.

This is not a supported graphical workflow. Use synthetic or disposable model
data only.

## Build Path

The Dockerfile clones `Open-MBEE/exec-ve` at tag `5.0.0`, installs the upstream
Yarn dependencies, and builds the production webpack bundle directly:

```text
VE_ENV=example yarn webpack --config webpack.config.ts --mode=production --bail
```

It intentionally bypasses the upstream `prebuild` lint/format gate because the
tagged source Dockerfile did not build cleanly during the experiment. The
runtime stage serves the static bundle from nginx.

## Runtime API Target

The bundled config points View Editor at a same-origin API prefix:

```text
http://localhost:18092/api
```

nginx proxies `/api/` to the Flexo SysML v2 service on the shared Docker
network:

```text
http://flexo-sysmlv2:8080/
```

This avoids browser CORS failures so request traces show Flexo API compatibility
failures directly. If you change `VIEW_EDITOR_5_HOST_PORT`, update
`config/flexo-sysmlv2.json` to keep `apiUrl` on the same host and port.

## Run

Start Flexo first so the shared Docker network exists:

```bash
python3 scripts/flexo_mms_env.py up --wait --timeout 60
```

Build and start View Editor 5.x:

```bash
docker compose -f deploy/view-editor-5/docker-compose.yml up -d --build
```

Open:

```text
http://localhost:18092/
```

Stop the experiment:

```bash
docker compose -f deploy/view-editor-5/docker-compose.yml down
```

## Expected Result

The View Editor 5.x app should load, but Flexo SysML v2 is not expected to
satisfy the MMS-style View Editor API contract. The key expected missing
resources are authentication, auth check, org, ref, document/view, element,
artifact, and search endpoints.
