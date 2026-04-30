# Generated Exports

This directory is for curated, publishable example snapshots only.

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
