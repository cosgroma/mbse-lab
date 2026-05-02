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

   Status: complete as of 2026-05-02. The exposed SysON OpenAPI surface includes
   OMG-style project, branch, commit, change, root, and element REST endpoints,
   including `POST /api/rest/projects/{projectId}/commits`. A minimal
   Flexo/API-shaped `Package` payload submitted through that commit endpoint
   returned HTTP 201, but it did not create a new commit or add the submitted
   package to the SysON element list. The route is therefore not a viable
   no-code Flexo JSON to SysON model import path.

   Export note: SysON's existing document download endpoint can invoke the
   textual exporter for normal SysON documents. A disposable SysON template
   project exposed a `SysMLv2.sysml` document in the database, and
   `GET /api/editingcontexts/{editingContextId}/documents/{documentId}` with
   `Accept: text/html` returned textual SysML:

   ```sysml
   package Package1 {
   	view view1 : StandardViewDefinitions::GeneralView;
   }
   ```

   This confirms SysON's serializer is reachable through the running service,
   but only after content already exists as a SysON EMF document.

3. If the REST path is not viable, assess a Java harness around SysON's
   serializer.

   Acceptance criteria:

   - Identify the minimum SysON modules needed to instantiate a SysML model
     element and call `SysMLElementSerializer`.
   - Determine whether Flexo API JSON can be mapped mechanically into SysON's
     EMF model without depending on private SysON internals.
   - Record license and packaging implications.

   Status: complete as of 2026-05-02. SysON's serializer can be invoked without
   the full SysON Spring application once a SysON EMF model object exists. The
   minimum source module for a standalone harness is
   `backend/metamodel/syson-sysml-metamodel`, which contains both the generated
   SysML EMF model and `SysMLElementSerializer`. The
   `backend/application/syson-sysml-export` module wraps the same serializer for
   document downloads, but the wrapper is service-facing and adds document/media
   handling rather than solving JSON materialization.

   A disposable Java 21 probe against the local SysON source built the metamodel
   module and called:

   ```java
   new SysMLElementSerializer(options, statuses::add).doSwitch(pkg)
   ```

   for a `SysmlFactory.eINSTANCE.createPackage()` instance, producing:

   ```sysml
   package ProbePackage;
   ```

   The adapter boundary is therefore not serializer invocation. It is faithfully
   reconstructing SysON EMF containment and relationship structure from Flexo
   API JSON. SysON expects elements to be connected through typed relationship
   objects such as `OwningMembership`, `FeatureMembership`,
   `FeatureTyping`, `Subclassification`, and `Subsetting`; for example, a child
   package is not just appended to a parent field. The parent owns an
   `OwningMembership`, the membership owns or references the child through
   `ownedRelatedElement`, and membership references such as `memberElement` must
   be populated for namespace lookup and serialization. This is mechanical for a
   narrow subset, but it is still an adapter with SysML semantic knowledge.

   Packaging note: the local SysON source builds this module with Java 21. The
   host has a Java 21 runtime but `javac` 17 on `PATH`, so the successful probe
   used the `maven:3.9-eclipse-temurin-21` container. SysON source and the
   running image declare EPL-2.0 licensing; invoking an external harness is a
   lower-commitment path than copying SysON serializer code into this repo.

4. Inspect the SysML v2 Pilot Implementation for API JSON to EMF to text
   support.

   Acceptance criteria:

   - Confirm whether a supported or testable API JSON load path exists.
   - If it exists, run a minimal package/root payload through it.
   - If it does not exist, document the missing boundary and avoid treating the
     Pilot stack as a near-term renderer.

   Status: complete as of 2026-05-02. The Pilot Implementation has a real
   standard repository API to EMF path, but not a supported offline Flexo JSON
   file to textual SysML renderer. `SysMLRepositoryLoadUtil` and the
   interactive `load` flow download projects through `ProjectRepository`,
   build an in-memory `APIModel` from repository roots and elements, and then
   use `EMFModelRefresher` to materialize generated SysML EMF objects. That is
   the closest reusable boundary found.

   The missing piece is the file/import side. Source inspection found
   `SysML2JSON` and `JsonElementProcessingFacade` for text/EMF to API JSON,
   but no `JSON2SysML`, `fromJson`, or equivalent offline parser that accepts a
   Flexo export JSON file and returns an `APIModel` or textual `.sysml`.
   `APIModel` stores UUID-keyed roots/elements and can serialize itself back to
   JSON, but it does not parse API JSON. A Flexo-to-Pilot path would therefore
   still need an adapter that validates API-shaped JSON, normalizes ids when
   needed, populates `APIModel`, tracks library UUIDs through
   `EObjectUUIDTracker`, runs `EMFModelRefresher`, and saves/serializes the
   resulting EMF resources.

   Practical notes: the public example Flexo export uses UUID-shaped element
   ids and is closer to Pilot expectations than the synthetic fixture with
   ids such as `pkg-1`. The Pilot source is `LGPL-3.0-or-later`; invoking it as
   an external harness is lower risk than copying implementation code. A
   targeted Java 21 Docker build of the core, KerML Xtext, SysML Xtext, and
   target modules succeeded, so a harness is buildable, but it remains a
   heavyweight Java/Tycho dependency path.

5. Compare options and make a recommendation.

   Possible outcomes:

   - Use SysON as the renderer by routing Flexo JSON through a supported SysON
     import/export path.
   - Build a narrow adapter from Flexo API JSON into SysON's serializer model.
   - Keep the current Python renderer but constrain its scope and use SysON or
     Pilot tooling only as validation/reference.
   - Adopt a discovered direct JSON-to-text renderer if one exists and has
     acceptable licensing and operational fit.

   Status: complete as of 2026-05-02. No discovered tool provides a supported
   offline Flexo/API JSON file to textual `.sysml` path. The recommended
   near-term path is to keep the existing Python renderer as the bridge's
   production renderer, constrain its supported subset in
   `docs/lab/modeling-conventions.md`, and expand it only through fixtures and
   SysON import validation.

   SysON remains useful as the graphical review/editing target and as a
   reference serializer for hand-built EMF probes, but its public REST
   data-version facade did not import the tested API-shaped payload into a
   usable SysON document. A SysON Java harness would still require a semantic
   Flexo JSON to SysON EMF adapter, which is likely more expensive than
   maintaining the current renderer for the narrow supported subset.

   The Pilot Implementation remains useful as a reference for standard SysML v2
   API semantics and possibly as a future validation harness. It does not
   remove the adapter boundary because it lacks a supported offline
   `APIModel.fromJson` or JSON-file-to-text command. A Pilot adapter would need
   to parse/validate Flexo JSON, populate `APIModel`, handle UUID/library
   tracking, run `EMFModelRefresher`, and then save or serialize EMF resources.

   Revisit a Java adapter only if the bridge needs broad semantic coverage such
   as typed relationships, memberships, specialization, connector ends, or
   library-aware references that would make the Python renderer drift into a
   broad SysML implementation. Until then, the adapter complexity and Java/Tycho
   packaging cost are not justified by the current bridge scope.

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
- 2026-05-02: Probed the running SysON `v2026.1.0` service. The OpenAPI
  document exposes `POST /api/rest/projects/{projectId}/commits`, but a minimal
  API-shaped `Package` `DataVersion` payload was not incorporated into either a
  REST-created project or a normal `sysmlv2-template` project. The same run
  confirmed that SysON document download can call the textual exporter for an
  existing SysON document when requested with `Accept: text/html`.
- 2026-05-02: Assessed the SysON Java harness path. The metamodel module builds
  standalone in a Java 21 Maven container and can directly serialize an
  in-memory SysON EMF package. The remaining work for this path is an API JSON
  to SysON EMF adapter, with the main complexity in reconstructing SysML
  relationship/membership objects rather than calling the serializer.
- 2026-05-02: Inspected the SysML v2 Pilot Implementation API repository and
  Xtext tooling. The strongest reusable component is
  `EMFModelRefresher`, reached from `SysMLRepositoryLoadUtil` after a live
  repository project has already been loaded into an `APIModel`. No supported
  offline API JSON file to `.sysml` command or `APIModel.fromJson` equivalent
  was found. A targeted Java 21 Docker build of the relevant Pilot modules
  completed successfully, confirming the harness route is buildable but still
  adapter-heavy.
- 2026-05-02: Completed the option comparison. The spike did not find a direct
  reusable renderer or supported import/export chain. The recommendation is to
  keep the local Python renderer as the production bridge path, keep its subset
  explicit and fixture-driven, and use SysON/Pilot only as reference or
  validation tooling unless the required SysML coverage grows beyond the
  current conservative declarations.

## Validation Commands

Run deterministic checks after changing tracked repo files:

```bash
make check
```

SysON serializer harness probe:

```bash
docker run --rm \
  -v /tmp/syson:/work \
  -v "$HOME/.m2":/root/.m2 \
  -w /work \
  maven:3.9-eclipse-temurin-21 \
  mvn -pl backend/metamodel/syson-sysml-metamodel -DskipTests package
```

The host Maven build is expected to fail until `javac` 21 is available on
`PATH`; this workspace currently has a Java 21 runtime but a Java 17 compiler.

Pilot API repository/Xtext build probe:

```bash
docker run --rm \
  -v /tmp/SysML-v2-Pilot-Implementation:/work \
  -v "$HOME/.m2":/root/.m2 \
  -w /work \
  maven:3.9-eclipse-temurin-21 \
  mvn -pl org.omg.sysml,org.omg.kerml.expressions.xtext,org.omg.kerml.xtext,org.omg.sysml.xtext -am -DskipTests package
```

This completed successfully against local commit
`96a0212 Merge pull request #751 from Systems-Modeling/ST6RI-898`.

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
- SysON's public REST data-version endpoint is not sufficient by itself for
  Flexo API JSON to SysON model import. Continue with a Java harness or internal
  SysON model-adapter assessment rather than trying to force the REST commit
  facade.
- A SysON Java harness is technically viable but not automatically cheaper than
  the current Python renderer for the supported subset. It becomes attractive
  only if the adapter can stay narrow and fixture-driven, or if another tool
  already materializes SysML v2 API JSON into an EMF model.
- Before implementing a SysON adapter, inspect the SysML v2 Pilot
  Implementation for an API JSON to EMF/text path. If that path exists, it could
  avoid rebuilding the same semantic relationship reconstruction against SysON's
  generated model.
- The Pilot Implementation does not remove the adapter need. It changes the
  possible adapter target from SysON EMF objects to Pilot `APIModel` plus
  `EMFModelRefresher`, and may be useful as a validation/reference harness for
  standard API semantics.
- Final spike recommendation: keep the current Python renderer as the supported
  bridge renderer for now. Maintain the subset contract, add fixture coverage
  before each new mapping, and validate generated text through SysON import
  behavior rather than adopting a Java adapter prematurely.
- Revisit SysON or Pilot adapters only when one of these conditions is met:
  a supported upstream JSON import path appears, a narrow adapter can be proven
  with fixture coverage, or bridge requirements expand into semantic
  relationship coverage that would make the Python renderer too broad to own.
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
- Add a short reuse-spike summary to the bridge documentation if this plan is
  archived or referenced from a PR description.
