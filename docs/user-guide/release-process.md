# Release Process

`mbse-lab` uses a lightweight Git Flow policy:

```text
feature/*, bugfix/*, dependabot/*, copilot/* -> develop
release/*, hotfix/*                          -> main
```

Use `develop` for normal integration work. Use `main` for the published,
stable branch that users install from by default.
Copilot-authored branches using the `copilot/*` prefix are accepted only when
they target `develop`.

## Release Checklist

Before opening a release branch:

```bash
hatch run lint:all
make check
make docs-build
mbse-lab share-check
```

Run the live smoke pass when Docker is available:

```bash
export MBSE_MODEL_WORKSPACE=~/workspace/projects/mbse-release-smoke-models
mbse-lab init --model-workspace "$MBSE_MODEL_WORKSPACE"
mbse-lab doctor
python3 scripts/flexo_mms_env.py up --wait --timeout 180
sleep 20
for attempt in {1..12}; do
  if mbse-lab flexo init-org --timeout 60; then
    org_initialized=true
    break
  fi
  python3 scripts/flexo_mms_env.py status --with-sysmlv2 || true
  sleep 5
done
test "${org_initialized:-false}" = "true"
mbse-lab services up --no-flexo --syson --timeout 180
mbse-lab flexo list --timeout 60
mbse-lab first-model "Release Smoke Model"
mbse-lab deployment verify
make live-eval
mbse-lab share-check
```

The live smoke pass creates disposable Flexo and SysON projects and writes
generated artifacts under the private model workspace.

Before publishing a release, also run the manual GitHub Actions workflow
`Live smoke` from the Actions tab. It starts Flexo and SysON, runs the
first-use smoke workflow and live evals, and uploads a public-safe diagnostics
artifact if the workflow fails.

## Troubleshooting Live Smoke

If `syson-app` exits with a Postgres message such as:

```text
FATAL: password authentication failed for user "username"
```

then the ignored local `deploy/syson/.env` file probably does not match the
password stored in the existing `deploy/syson/data/postgres/` runtime data.
Align the ignored `.env` file with the existing local database password, or
back up and reset the SysON runtime data before starting SysON again.

Do not commit `deploy/syson/.env` or `deploy/syson/data/postgres/`.

## Prepare A Release Branch

Start the release from `develop`:

```bash
git switch develop
git pull --ff-only origin develop
git switch -c release/v0.2.0
```

Update release-facing documentation or version metadata if needed, then run the
release checklist. Commit any release-only cleanup on the `release/*` branch.

Push the release branch and open a pull request into `main`:

```bash
git push -u origin release/v0.2.0
gh pr create --base main --head release/v0.2.0 --title "Release v0.2.0" --body "Release v0.2.0"
```

Squash or merge the release PR according to the repository setting, then tag
the resulting `main` commit:

```bash
git switch main
git pull --ff-only origin main
git tag -a v0.2.0 -m "v0.2.0"
git push origin v0.2.0
gh release create v0.2.0 --generate-notes
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
