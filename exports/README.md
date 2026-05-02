# Export Artifacts

This directory has two different roles:

- `exports/examples/` contains curated, publishable example snapshots.
- `exports/flexo/` and `exports/sysml/` are default generated-output locations
  when no private model workspace is configured.

Real Flexo exports and rendered SysML files should live outside this tooling
repo, usually in a private model workspace. Set `MBSE_MODEL_WORKSPACE` to make
bridge commands default to that private location:

```bash
export MBSE_MODEL_WORKSPACE=~/work/my-private-sysmlv2-models
```

With that variable set, generated bridge artifacts default to:

```text
$MBSE_MODEL_WORKSPACE/exports/flexo/
$MBSE_MODEL_WORKSPACE/exports/sysml/
```

New files under `exports/` are ignored by default to reduce the chance of
committing private model data by accident.

Before publishing or sharing this tooling repo, run:

```bash
mbse-lab share-check
```

That check blocks tracked generated exports under `exports/flexo/` and
`exports/sysml/`. Force-add only synthetic examples under `exports/examples/`
and use `.public.json` or `.public.sysml` suffixes for those curated artifacts.

## Curated Examples

The checked-in examples are synthetic and publishable. They are kept small so
they can serve as renderer fixtures and documentation examples.

```text
exports/examples/sysml/mbse-lab-tool-system.public.sysml
                                  Rendered textual snapshot of this repo's own
                                  MBSE lab tool-system fixture
```

Regenerate the MBSE lab tool-system snapshot with:

```bash
PYTHONPATH=src python3 -m mbse_lab.cli bridge render \
  evals/fixtures/mbse-lab-tool-system.json \
  --output exports/examples/sysml/mbse-lab-tool-system.public.sysml
```
