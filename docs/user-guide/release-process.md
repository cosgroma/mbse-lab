# Release Process

`mbse-lab` uses a lightweight Git Flow policy:

```text
feature/*, bugfix/*, dependabot/* -> develop
release/*, hotfix/*               -> main
```

Use `develop` for normal integration work. Use `main` for the published,
stable branch that users install from by default.

## MVP Release Checklist

Before opening a release branch:

```bash
hatch run lint:all
make check
make docs-build
mbse-lab share-check
```

Run the live smoke pass when Docker is available:

```bash
export MBSE_MODEL_WORKSPACE=~/workspace/projects/mbse-mvp-smoke-models
mbse-lab init --model-workspace "$MBSE_MODEL_WORKSPACE"
mbse-lab doctor
mbse-lab services up
mbse-lab first-model "MVP Smoke Model"
mbse-lab deployment verify
make live-eval
mbse-lab share-check
```

The live smoke pass creates disposable Flexo and SysON projects and writes
generated artifacts under the private model workspace.

## Prepare A Release Branch

Start the release from `develop`:

```bash
git switch develop
git pull --ff-only origin develop
git switch -c release/v0.1.0
```

Update release-facing documentation or version metadata if needed, then run the
release checklist. Commit any release-only cleanup on the `release/*` branch.

Push the release branch and open a pull request into `main`:

```bash
git push -u origin release/v0.1.0
gh pr create --base main --head release/v0.1.0 --title "Release v0.1.0" --body "Release v0.1.0"
```

Squash or merge the release PR according to the repository setting, then tag
the resulting `main` commit:

```bash
git switch main
git pull --ff-only origin main
git tag -a v0.1.0 -m "v0.1.0"
git push origin v0.1.0
gh release create v0.1.0 --generate-notes
```

## Sync Back To Develop

After `main` is released, bring the release commit back to `develop`:

```bash
git switch develop
git pull --ff-only origin develop
git merge --ff-only main
git push origin develop
```

If `develop` has moved past the release branch, use a normal merge from `main`
instead of forcing history:

```bash
git merge main
git push origin develop
```

Do not rewrite `main` or release tags after a public release unless correcting a
serious publication problem.
