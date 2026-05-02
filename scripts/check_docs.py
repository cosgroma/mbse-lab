#!/usr/bin/env python3
"""Validate documentation discoverability, command snippets, and workflow policy."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
INDEX_FILES = [
    ROOT / "README.md",
    ROOT / "WORKFLOW.md",
    ROOT / "AGENTS.md",
    ROOT / "docs" / "index.md",
    ROOT / "docs" / "lab" / "harness-engineering.md",
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
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
MBSE_LAB_COMMAND = re.compile(r"(?:^|\s)mbse-lab\s+([A-Za-z0-9_-]+(?:\s+[A-Za-z0-9_-]+)?)")


def run(command: list[str], extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = None
    if extra_env:
        env = {**os.environ, **extra_env}
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, env=env)


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def tracked_and_untracked_docs() -> list[Path]:
    docs: set[Path] = set()
    for pattern in DOC_GLOBS:
        docs.update(ROOT.glob(pattern))
    docs.update([ROOT / "AGENTS.md", ROOT / "README.md", WORKFLOW_FILE])
    return sorted(path for path in docs if path.is_file())


def linked_index_paths() -> set[str]:
    linked: set[str] = set()
    for source in INDEX_FILES:
        if not source.exists():
            continue
        text = source.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK.findall(text):
            target = raw_target.strip().split()[0]
            if not target or target.startswith("#") or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
                continue
            target = unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not target:
                continue
            resolved = (source.parent / target).resolve()
            try:
                relative = resolved.relative_to(ROOT)
            except ValueError:
                continue
            linked.add(relative.as_posix())
    return linked


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
        # Process bash, sh, shell, and unfenced (empty language tag) code blocks.
        if not in_fence or fence_language not in {"bash", "sh", "shell", ""}:
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.endswith("\\"):
            continue
        if COMMAND_LINE.match(stripped):
            commands.append(stripped)
    return commands


def code_block_lines(path: Path) -> list[str]:
    """Return all non-empty, non-comment lines from bash code blocks."""
    text = path.read_text(encoding="utf-8")
    lines: list[str] = []
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
        # Process bash, sh, shell, and unfenced (empty language tag) code blocks.
        if not in_fence or fence_language not in {"bash", "sh", "shell", ""}:
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.endswith("\\"):
            continue
        lines.append(stripped)
    return lines


def check_discoverability(failures: list[str]) -> None:
    linked_paths = linked_index_paths()
    for path in tracked_and_untracked_docs():
        relative = path.relative_to(ROOT).as_posix()
        if relative in {"README.md", "AGENTS.md"} or relative in IGNORED_DOCS:
            continue
        if relative.startswith("docs/plans/active/") or relative.startswith("docs/plans/completed/"):
            continue
        if relative not in linked_paths:
            fail(
                f"{relative} is not linked from README.md, WORKFLOW.md, AGENTS.md, docs/index.md, or harness guidance",
                failures,
            )


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


def mbse_lab_top_level_commands() -> set[str]:
    """Return the set of top-level mbse-lab command/group names from --help."""
    python_path = str(ROOT / "src")
    existing_python_path = os.environ.get("PYTHONPATH")
    if existing_python_path:
        python_path = f"{python_path}{os.pathsep}{existing_python_path}"
    result = run([sys.executable, "-m", "mbse_lab.cli", "--help"], {"PYTHONPATH": python_path})
    text = result.stdout + result.stderr
    commands: set[str] = set()
    in_commands = False
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^Commands:$", stripped, re.IGNORECASE):
            in_commands = True
            continue
        if in_commands:
            if not stripped:
                break
            match = re.match(r"^([A-Za-z0-9_-]+)", stripped)
            if match:
                commands.add(match.group(1))
    return commands


def check_mbse_lab_commands(failures: list[str]) -> None:
    top_level = mbse_lab_top_level_commands()
    if not top_level:
        return
    for doc in tracked_and_untracked_docs():
        for line in code_block_lines(doc):
            for match in MBSE_LAB_COMMAND.finditer(line):
                tokens = match.group(1).split()
                first_token = tokens[0]
                if first_token.startswith("-"):
                    continue
                if first_token not in top_level:
                    fail(
                        f"{doc.relative_to(ROOT)} references `mbse-lab {first_token}`, "
                        "but that command is not in `mbse-lab --help`",
                        failures,
                    )


def check_cli_reference(failures: list[str]) -> None:
    result = run(["python3", "scripts/generate_cli_reference.py", "--check"])
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        fail(detail or "generated CLI reference is out of date", failures)


def check_workflow_contract(failures: list[str]) -> None:
    if not WORKFLOW_FILE.exists():
        fail("WORKFLOW.md is missing", failures)
        return
    text = WORKFLOW_FILE.read_text(encoding="utf-8")
    required_fragments = [
        "commit_after_chunk: true",
        "trusted-local-lab",
        "make check",
        "make docs-build",
        "make diagnostics",
        "make deployment-verify",
        "make live-eval",
        "hatch run lint:all",
        "docs/plans/active/",
        "docs/plans/completed/",
        "GitHub CI workflow runs pre-commit",
        "MkDocs",
        "explicit user intent",
        "recommended next chunk",
    ]
    for fragment in required_fragments:
        if fragment not in text:
            fail(f"WORKFLOW.md must mention `{fragment}`", failures)


def validate_workflow() -> list[str]:
    failures: list[str] = []
    check_workflow_contract(failures)
    return failures


def validate_docs() -> list[str]:
    failures: list[str] = []
    check_discoverability(failures)
    check_cli_reference(failures)
    check_make_commands(failures)
    check_python_commands(failures)
    check_mbse_lab_commands(failures)
    failures.extend(validate_workflow())
    return failures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow-only", action="store_true", help="Validate only WORKFLOW.md policy requirements.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    failures = validate_workflow() if args.workflow_only else validate_docs()
    if failures:
        label = "workflow-check" if args.workflow_only else "docs-check"
        print(f"{label} failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        raise SystemExit(1)
    print("workflow-check passed" if args.workflow_only else "docs-check passed")


if __name__ == "__main__":
    main()
