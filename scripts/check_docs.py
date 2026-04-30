#!/usr/bin/env python3
"""Validate documentation discoverability and command snippets."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_FILES = [
    ROOT / "README.md",
    ROOT / "WORKFLOW.md",
    ROOT / "AGENTS.md",
    ROOT / "docs" / "harness-engineering.md",
]
WORKFLOW_FILE = ROOT / "WORKFLOW.md"
DOC_GLOBS = ["docs/**/*.md", "deploy/**/README.md"]
IGNORED_DOCS = {
    "docs/plans/active/.gitkeep",
    "docs/plans/completed/.gitkeep",
}
COMMAND_LINE = re.compile(r"^\s*(?:[A-Z0-9_./-]+=\\S+\s+)*(make|python3|docker|curl|git|cp|jq)\b(.+)?$")
PYTHON_SCRIPT = re.compile(r"python3\s+(scripts/[A-Za-z0-9_.\-/]+\.py)(?:\s+([A-Za-z0-9_-]+))?")
MAKE_TARGET = re.compile(r"\bmake\s+([A-Za-z0-9_.-]+)")


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def tracked_and_untracked_docs() -> list[Path]:
    docs: set[Path] = set()
    for pattern in DOC_GLOBS:
        docs.update(ROOT.glob(pattern))
    docs.update([ROOT / "AGENTS.md", ROOT / "README.md", WORKFLOW_FILE])
    return sorted(path for path in docs if path.is_file())


def visible_index_text() -> str:
    parts = []
    for path in INDEX_FILES:
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def make_targets() -> set[str]:
    result = run(["make", "-qp"])
    targets: set[str] = set()
    for line in result.stdout.splitlines():
        if not line or line.startswith("\t") or line.startswith("."):
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+)\s*:", line)
        if match:
            targets.add(match.group(1))
    return targets


def script_subcommands(script: Path) -> set[str]:
    result = run(["python3", str(script.relative_to(ROOT)), "--help"])
    text = result.stdout + result.stderr
    match = re.search(r"\{([^}]+)\}", text)
    if not match:
        return set()
    return {part.strip() for part in match.group(1).split(",") if part.strip()}


def command_blocks(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    commands: list[str] = []
    in_fence = False
    fence_language = ""
    for line in text.splitlines():
        if line.startswith("```"):
            if not in_fence:
                in_fence = True
                fence_language = line.removeprefix("```").strip()
            else:
                in_fence = False
                fence_language = ""
            continue
        if not in_fence or fence_language not in {"bash", "sh", "shell", ""}:
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.endswith("\\"):
            continue
        if COMMAND_LINE.match(stripped):
            commands.append(stripped)
    return commands


def check_discoverability(failures: list[str]) -> None:
    index = visible_index_text()
    for path in tracked_and_untracked_docs():
        relative = path.relative_to(ROOT).as_posix()
        if relative in {"README.md", "AGENTS.md"} or relative in IGNORED_DOCS:
            continue
        if relative.startswith("docs/plans/active/") or relative.startswith("docs/plans/completed/"):
            continue
        if relative not in index:
            fail(f"{relative} is not referenced by README.md, AGENTS.md, or docs/harness-engineering.md", failures)


def check_make_commands(failures: list[str]) -> None:
    targets = make_targets()
    for doc in tracked_and_untracked_docs():
        for command in command_blocks(doc):
            for target in MAKE_TARGET.findall(command):
                if target not in targets:
                    fail(f"{doc.relative_to(ROOT)} references missing make target `{target}`", failures)


def check_python_commands(failures: list[str]) -> None:
    subcommand_cache: dict[Path, set[str]] = {}
    for doc in tracked_and_untracked_docs():
        for command in command_blocks(doc):
            for script_name, subcommand in PYTHON_SCRIPT.findall(command):
                script = ROOT / script_name
                if not script.exists():
                    fail(f"{doc.relative_to(ROOT)} references missing script `{script_name}`", failures)
                    continue
                if not subcommand or subcommand.startswith("-"):
                    continue
                subcommands = subcommand_cache.setdefault(script, script_subcommands(script))
                if subcommands and subcommand not in subcommands:
                    fail(
                        f"{doc.relative_to(ROOT)} references `{script_name} {subcommand}`, "
                        "but that subcommand is not in --help",
                        failures,
                    )


def check_workflow_contract(failures: list[str]) -> None:
    if not WORKFLOW_FILE.exists():
        fail("WORKFLOW.md is missing", failures)
        return
    text = WORKFLOW_FILE.read_text(encoding="utf-8")
    required_fragments = [
        "commit_after_chunk: true",
        "trusted-local-lab",
        "make check",
        "make diagnostics",
        "make deployment-verify",
        "make live-eval",
        "explicit user intent",
        "recommended next chunk",
    ]
    for fragment in required_fragments:
        if fragment not in text:
            fail(f"WORKFLOW.md must mention `{fragment}`", failures)


def main() -> None:
    failures: list[str] = []
    check_discoverability(failures)
    check_make_commands(failures)
    check_python_commands(failures)
    check_workflow_contract(failures)
    if failures:
        print("docs-check failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        raise SystemExit(1)
    print("docs-check passed")


if __name__ == "__main__":
    main()
