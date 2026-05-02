# SysML JSON Rendering Reuse Spike

## Objective

Determine whether an existing open-source renderer or exporter can convert
Flexo SysML v2 REST JSON into valid textual SysML before expanding the local
Python renderer in `scripts/flexo_syson_bridge.py`.

The spike should answer:

- Is there a maintained tool that accepts SysML v2 API-shaped JSON and emits
  `.sysml` directly?
- Can SysON's textual exporter be reused by feeding Flexo JSON through an
  existing SysON import or data-version path?
- Can the OMG SysML v2 Pilot Implementation materialize API JSON into an EMF
  model that can be serialized through its Xtext stack?
- If no direct renderer exists, what is the smallest adapter boundary that
  avoids owning a broad hand-written textual renderer?

## Background

The current bridge path is:

```text
Flexo SysML v2 REST JSON -> conservative Python .sysml rendering -> SysON import
```

The Python renderer is intentionally narrow. It supports enough element shapes
for the current lab fixtures, but broad SysML v2 textual coverage would be a
large maintenance commitment. Before growing that renderer, inspect and test
the strongest reuse candidates:

- Eclipse SysON textual export, which serializes SysON EMF SysML elements to
  textual SysML.
- The OMG SysML v2 Pilot Implementation Xtext and API tooling.
- SysML v2 API clients or CLIs that might already provide JSON-to-text export.

## Relevant Files

- `scripts/flexo_syson_bridge.py`
- `docs/lab/flexo-syson-bridge.md`
- `docs/lab/modeling-conventions.md`
- `docs/plans/active/sysml-json-rendering-reuse-spike.md`
- `exports/examples/flexo/`
- `evals/fixtures/`

External source references to inspect:

- <https://github.com/eclipse-syson/syson>
- <https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation>
- <https://github.com/Systems-Modeling/SysML-v2-API-Python-Client>

## Planned Steps

1. Capture the current known reuse candidates and their adapter requirements.

   Status: started on 2026-05-02. Initial source inspection found no direct
   Flexo JSON to `.sysml` CLI, but identified SysON's textual exporter as the
   strongest reuse candidate.

2. Probe SysON's REST/data-version import surface with a small Flexo-style
   SysML v2 API JSON payload.

   Acceptance criteria:

   - Create or choose a disposable SysON project.
   - Submit a minimal package/root payload using any exposed SysON REST
     data-version or import endpoint that accepts API-shaped JSON.
   - Export the resulting SysON document as textual SysML using SysON's
     existing exporter.
   - Record whether the path works without custom Java code.

3. If the REST path is not viable, assess a Java harness around SysON's
   serializer.

   Acceptance criteria:

   - Identify the minimum SysON modules needed to instantiate a SysML model
     element and call `SysMLElementSerializer`.
   - Determine whether Flexo API JSON can be mapped mechanically into SysON's
     EMF model without depending on private SysON internals.
   - Record license and packaging implications.

4. Inspect the SysML v2 Pilot Implementation for API JSON to EMF to text
   support.

   Acceptance criteria:

   - Confirm whether a supported or testable API JSON load path exists.
   - If it exists, run a minimal package/root payload through it.
   - If it does not exist, document the missing boundary and avoid treating the
     Pilot stack as a near-term renderer.

5. Compare options and make a recommendation.

   Possible outcomes:

   - Use SysON as the renderer by routing Flexo JSON through a supported SysON
     import/export path.
   - Build a narrow adapter from Flexo API JSON into SysON's serializer model.
   - Keep the current Python renderer but constrain its scope and use SysON or
     Pilot tooling only as validation/reference.
   - Adopt a discovered direct JSON-to-text renderer if one exists and has
     acceptable licensing and operational fit.

## Progress Log

- 2026-05-02: Created this spike plan after broad source and web inspection.
  Initial findings:
  - SysON has an active textual export stack centered on
    `SysMLElementSerializer` and `SysMLv2DocumentExporter`, but it serializes
    SysON EMF model objects rather than raw Flexo JSON.
  - The SysML v2 Pilot Implementation includes Xtext serializers and
    `SysML2JSON`, but no obvious documented API JSON to textual SysML CLI was
    found in the first pass.
  - The public SysML v2 API Python client appears to be a generated REST client,
    not a textual renderer.

## Validation Commands

Run deterministic checks after changing tracked repo files:

```bash
make check
```

Use live service checks only when probing a running SysON or Flexo stack:

```bash
python3 scripts/flexo_mms_env.py status --with-sysmlv2 --strict
docker compose -f deploy/syson/docker-compose.yml ps
python3 scripts/flexo_syson_bridge.py flexo-list-projects
```

If the spike produces a reusable bridge path, add focused deterministic tests
before updating the supported workflow documentation.

## Decisions And Tradeoffs

- Prefer using SysON's exporter as a service or harness over copying serializer
  code into this repository.
- Do not expand the local Python renderer beyond narrow fixture needs until the
  SysON and Pilot reuse paths are tested.
- Treat licensing as part of the technical decision. SysON and the Pilot
  Implementation have different licenses, so vendoring code is a materially
  different choice from invoking an external tool or service.
- Keep real model exports and run evidence out of this repo; use synthetic
  payloads or private workspaces for live probes.

## Follow-Up Debt

- Update `docs/lab/modeling-conventions.md` if the recommended rendering path
  changes.
- Update `docs/lab/flexo-syson-bridge.md` if the bridge flow changes from local
  Python rendering to SysON-mediated rendering.
- Add fixture coverage for any adopted adapter path.
