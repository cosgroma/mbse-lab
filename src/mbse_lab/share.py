"""Share-safety checks for the tooling repository."""

from __future__ import annotations

import re
from pathlib import Path

from mbse_lab.constants import FORBIDDEN_TRACKED_PATHS, FORBIDDEN_TRACKED_PREFIXES, FORBIDDEN_UNTRACKED_PREFIXES
from mbse_lab.shell import run_capture

SECRET_PATTERNS = (
    re.compile("thisissomethingreally" "long"),
    re.compile("admin" "test"),
    re.compile("admin" "password"),
    re.compile("password" "1"),
    re.compile("password" "2"),
    re.compile("eyJhb" "Gci"),
    re.compile("SYSON_POSTGRES_PASSWORD=pass" "word"),
    re.compile("JWT_SECRET=thi" "s"),
)

FLEXO_STARTUP_DATASET = "deploy/flexo-mms/mount/cluster.nq"
MODEL_ARTIFACT_SUFFIXES = (".sysml", ".nq", ".trig")


def tracked_files(repo_root: Path) -> list[str]:
    output = run_capture(["git", "ls-files"], repo_root)
    return [line for line in output.splitlines() if line]


def untracked_files(repo_root: Path) -> list[str]:
    visible = run_capture(["git", "ls-files", "--others", "--exclude-standard"], repo_root)
    ignored = run_capture(["git", "ls-files", "--others", "--ignored", "--exclude-standard"], repo_root)
    return sorted({line for output in (visible, ignored) for line in output.splitlines() if line})


def dirty_paths(repo_root: Path, path: str) -> list[str]:
    output = run_capture(["git", "status", "--short", "--", path], repo_root)
    return [line for line in output.splitlines() if line]


def path_matches(path: str, exact_or_prefix: tuple[str, ...]) -> bool:
    return any(path == pattern.rstrip("/") or path.startswith(pattern) for pattern in exact_or_prefix)


def is_allowed_tracked_model_artifact(path: str) -> bool:
    if path == FLEXO_STARTUP_DATASET:
        return True
    return path.startswith("exports/examples/") and ".public." in Path(path).name


def scan_share_issues(repo_root: Path) -> list[str]:
    issues: list[str] = []
    tracked = tracked_files(repo_root)
    untracked = untracked_files(repo_root)

    for path in tracked:
        if path_matches(path, FORBIDDEN_TRACKED_PATHS) or path.startswith(FORBIDDEN_TRACKED_PREFIXES):
            if path.endswith(".example") or path.endswith(".gitkeep"):
                continue
            issues.append(f"tracked publish-blocked path: {path}")
        if path.endswith(MODEL_ARTIFACT_SUFFIXES) and not is_allowed_tracked_model_artifact(path):
            issues.append(f"tracked model artifact outside curated allowlist: {path}")

    for path in untracked:
        if path.startswith(FORBIDDEN_UNTRACKED_PREFIXES):
            issues.append(f"untracked generated export: {path}")

    for status_line in dirty_paths(repo_root, FLEXO_STARTUP_DATASET):
        issues.append(f"dirty Flexo startup dataset: {status_line[3:]}")

    for path in tracked:
        full_path = repo_root / path
        if not full_path.is_file() or full_path.stat().st_size > 1_000_000:
            continue
        try:
            text = full_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                issues.append(f"tracked secret-like pattern `{pattern.pattern}` in {path}")
                break

    return issues
