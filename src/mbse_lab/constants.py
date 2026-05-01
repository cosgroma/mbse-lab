"""Shared constants for the MBSE lab CLI."""

from __future__ import annotations

from pathlib import Path

DEFAULT_FLEXO_URL = "http://localhost:18083"
DEFAULT_SYSON_URL = "http://localhost:18090"

FLEXO_CONTAINERS = (
    "openldap-server",
    "quad-server",
    "minio-server",
    "auth-service",
    "store-service",
    "layer1-service",
    "flexo-sysmlv2",
)
SYSON_CONTAINERS = (
    "syson-database",
    "syson-app",
)

REQUIRED_MARKERS = (
    Path("deploy/flexo-mms/docker-compose.yml"),
    Path("deploy/syson/docker-compose.yml"),
    Path("scripts/flexo_mms_env.py"),
    Path("scripts/flexo_syson_bridge.py"),
)

WORKSPACE_DIRS = (
    "docs",
    "source",
    "exports/flexo",
    "exports/sysml",
    "evidence",
    "runs",
)

CLEANUP_PATHS = (
    "reports",
    "diagnostics",
    "runs",
    "tmp",
)

OPTIONAL_CLEANUP_PATHS = ("site",)

FORBIDDEN_TRACKED_PATHS = (
    "deploy/flexo-mms/.env",
    "deploy/syson/.env",
    "diagnostics/",
    "reports/",
    "runs/",
    "tmp/",
    "site/",
)

FORBIDDEN_TRACKED_PREFIXES = (
    "deploy/flexo-mms/env/",
    "deploy/flexo-mms/data/",
    "deploy/syson/data/postgres/",
)

FORBIDDEN_UNTRACKED_PREFIXES = (
    "exports/flexo/",
    "exports/sysml/",
)
