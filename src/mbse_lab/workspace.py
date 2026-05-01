"""Private model workspace helpers."""

from __future__ import annotations

import os
import re
import secrets
from pathlib import Path

import click

from mbse_lab.constants import WORKSPACE_DIRS
from mbse_lab.shell import run_command

SYSON_POSTGRES_PASSWORD_PLACEHOLDER = "change-me"


def default_output_dir() -> Path:
    model_workspace = os.environ.get("MBSE_MODEL_WORKSPACE")
    if model_workspace:
        return Path(model_workspace).expanduser() / "exports"
    return Path("exports")


def sanitize_identifier(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]", "_", value.strip())
    if not value:
        return "Unnamed"
    if value[0].isdigit():
        value = f"_{value}"
    return value


def _generate_syson_env_content(example_path: Path) -> str:
    """Read the example env file, replace the placeholder password with a random one, and return the modified content."""
    template = example_path.read_text(encoding="utf-8")
    random_password = secrets.token_urlsafe(24)
    return template.replace(
        f"SYSON_POSTGRES_PASSWORD={SYSON_POSTGRES_PASSWORD_PLACEHOLDER}",
        f"SYSON_POSTGRES_PASSWORD={random_password}",
    )


def ensure_syson_env(repo_root: Path, dry_run: bool = False) -> None:
    env_path = repo_root / "deploy/syson/.env"
    example_path = repo_root / "deploy/syson/.env.example"
    if env_path.exists():
        click.echo(f"SysON env already exists: {env_path.relative_to(repo_root)}")
        return
    if not example_path.exists():
        raise click.ClickException(f"missing SysON env template: {example_path}")
    if dry_run:
        click.echo(f"dry-run: copy {example_path.relative_to(repo_root)} to {env_path.relative_to(repo_root)}")
        return
    env_content = _generate_syson_env_content(example_path)
    env_path.write_text(env_content, encoding="utf-8")
    click.echo(f"Created SysON env with generated password: {env_path.relative_to(repo_root)}")


def initialize_model_workspace(root: Path, force: bool, git_init: bool, dry_run: bool = False) -> Path:
    root = root.expanduser().resolve()
    if dry_run:
        click.echo(f"dry-run: initialize model workspace {root}")
        return root

    root.mkdir(parents=True, exist_ok=True)
    for directory in WORKSPACE_DIRS:
        (root / directory).mkdir(parents=True, exist_ok=True)

    readme = root / "README.md"
    if force or not readme.exists():
        readme.write_text(
            "\n".join(
                [
                    "# SysML v2 Model Workspace",
                    "",
                    "Private workspace for SysML v2 model source, generated exports, run logs, and evidence.",
                    "",
                    "Use the shared lab kit CLI and set:",
                    "",
                    "```bash",
                    f"export MBSE_MODEL_WORKSPACE={root}",
                    "```",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    gitignore = root / ".gitignore"
    if force or not gitignore.exists():
        gitignore.write_text(
            "\n".join(
                [
                    "# Generated bridge artifacts and local run evidence.",
                    "exports/",
                    "runs/",
                    "diagnostics/",
                    "*.log",
                    "",
                    "# Local service or editor noise.",
                    ".DS_Store",
                    "Thumbs.db",
                    ".idea/",
                    ".vscode/",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    if git_init and not (root / ".git").exists():
        run_command(["git", "init", "-b", "main"], root)
    return root
