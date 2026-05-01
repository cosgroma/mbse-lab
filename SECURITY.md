# Security Policy

## Supported Versions

Security fixes are handled on the active `main` and `develop` branches.

## Reporting a Vulnerability

Do not open a public issue for suspected vulnerabilities, leaked credentials,
or private model exposure.

Report security issues to `cosgroma@gmail.com`. Include:

- A short description of the issue.
- Steps to reproduce when safe to share.
- Affected files, commands, or deployment paths.
- Any logs or diagnostics with secrets and private model data removed.

The maintainer will review the report, ask for clarification if needed, and
coordinate a fix before public disclosure when the issue affects users.

## Sensitive Data

This repository must not contain runtime credentials, private SysML v2 models,
private exports, service databases, run logs, or diagnostics bundles. Run the
share check before publishing changes:

```bash
make share-check
```
