# Feature: Environment Profiles

Status: Proposed

Release Target: `v0.6.0` candidate

## Problem

The documented path is local Docker, but advanced users may need alternate
ports, private workspaces, or experimental remote endpoints. Today those values
are passed through environment variables and command options without a named,
reviewable profile concept.

## Rationale

Profiles can reduce repeated configuration and make advanced workflows easier
to reproduce. They should come later because the local Docker path must remain
the stable default, and profile support should not weaken credential or private
workspace boundaries.

## Target Users

- Advanced users switching between local and experimental endpoints.
- Maintainers testing alternate port or workspace configurations.
- Developers automating repeatable lab workflows.
- Users with multiple private model workspaces.

## Non-Goals

- Do not make remote endpoint support part of the MVP promise.
- Do not store secrets in profile files.
- Do not replace existing environment variables or explicit CLI options.
- Do not add hosted-service or production deployment semantics.

## Current Behavior And Evidence

- Local Docker is the documented default.
- Commands accept explicit URLs and workspace paths in several places.
- Runtime credentials live in ignored env files.
- `MBSE_MODEL_WORKSPACE` controls private artifact placement.

## Proposed Behavior

Add named profiles for non-secret configuration such as service URLs, selected
ports, workspace path, and output policy.

Target-state command examples:

```text
mbse-lab profile list
mbse-lab profile show local
mbse-lab profile use local
mbse-lab profile create remote-probe --flexo-url <url> --syson-url <url>
```

Profile files should store only non-secret settings. Credentials remain in
ignored env files, environment variables, or explicit secret-management paths.

## CLI, Docs, And API Impact

- Add a future `mbse-lab profile` command group.
- Document precedence among CLI flags, environment variables, active profile,
  and defaults.
- Update doctor/report output to show active profile and config source.
- Add schema validation for profile files.

## Data And Credential Safety

Profiles must not store tokens, passwords, cookies, or private model content.
Profile paths may reveal local workspace names, so docs should recommend
private profile storage if path names are sensitive. Share-check should flag
tracked profile files containing secret-like values.

## Validation Plan

- Add deterministic profile parsing and precedence tests.
- Add share-check tests for secret-like profile content.
- Add docs-check coverage for profile docs once commands exist.
- Run `make check`.

## Acceptance Criteria

- Profiles can represent local Docker config without secrets.
- CLI flags override environment variables and profiles predictably.
- Doctor/report output identifies the active profile.
- Secret-like values in tracked profile files fail share-check.
- Existing env-var-only workflows remain compatible.

## Rollout And Compatibility Notes

This is additive and should wait until local Docker workflows are stable.
Profiles should start as an advanced feature, not a new first-use requirement.

## Open Decisions

- Where should profiles live by default: repo-local ignored path, user config
  directory, or private workspace?
- Should profile activation be persistent or command-scoped?
- How should profiles interact with generated `.env` files?
