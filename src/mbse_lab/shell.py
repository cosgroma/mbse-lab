"""Subprocess helpers for the MBSE lab CLI."""

from __future__ import annotations

import subprocess
from pathlib import Path

import click


def run_command(command: list[str], cwd: Path, dry_run: bool = False) -> None:
    if dry_run:
        click.echo(f"dry-run: {' '.join(command)}")
        return
    completed = subprocess.run(command, cwd=cwd)
    if completed.returncode != 0:
        raise click.ClickException(f"command failed with exit code {completed.returncode}: {' '.join(command)}")


def run_capture(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if completed.returncode != 0:
        raise click.ClickException(f"command failed with exit code {completed.returncode}: {' '.join(command)}")
    return completed.stdout


def run_capture_result(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True)
