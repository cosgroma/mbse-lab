# OpenMBEE View Editor Experiment

This directory contains an isolated experiment for running the legacy published
OpenMBEE View Editor image beside the local Flexo MMS stack.

This is not a supported graphical workflow yet. Use it only to collect request
traces for the View Editor/Flexo compatibility experiment.

## Image

The only public Docker Hub tag found during the experiment inventory was:

```text
openmbee/view-editor:3.6.1-omg
```

That image serves View Editor on container port `9000` and proxies `/alfresco`
requests to the host and port configured by `VE_MMS_HOST` and `VE_MMS_PORT`.

## Run

Start Flexo first so the shared Docker network exists:

```bash
python3 scripts/flexo_mms_env.py up --wait --timeout 60
```

Start View Editor with the default Layer1 target:

```bash
docker compose -f deploy/view-editor/docker-compose.yml up -d
```

The published image rebuilds the bundled web assets when it starts, so the
first useful HTTP response can lag container startup by a few seconds.

Open:

```text
http://localhost:18091/
```

Stop the experiment:

```bash
docker compose -f deploy/view-editor/docker-compose.yml down
```

## Backend Targets

The compose file defaults to the Flexo Layer1 service from inside Docker:

```bash
VIEW_EDITOR_MMS_HOST=layer1-service VIEW_EDITOR_MMS_PORT=8080 \
  docker compose -f deploy/view-editor/docker-compose.yml up -d
```

To point the same image at the Flexo SysML v2 service:

```bash
VIEW_EDITOR_MMS_HOST=flexo-sysmlv2 VIEW_EDITOR_MMS_PORT=8080 \
  docker compose -f deploy/view-editor/docker-compose.yml up -d
```

Expected result for the first spike is request evidence, not a successful user
workflow. The View Editor image expects legacy MMS resources under `/alfresco`,
including authentication, document, view, element, and search APIs.
