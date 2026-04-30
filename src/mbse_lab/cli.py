"""Command-line interface for the SysML v2 local lab."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import click

from mbse_lab import __version__

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


@dataclass(frozen=True)
class CliContext:
    repo_root: Path | None


def find_repo_root(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if all((candidate / marker).exists() for marker in REQUIRED_MARKERS):
            return candidate
    return None


def require_repo_root(ctx: click.Context) -> Path:
    obj = ctx.find_object(CliContext)
    if obj and obj.repo_root:
        return obj.repo_root
    raise click.ClickException("Could not find the mbse lab repo root. Run from the repo or pass --repo-root.")


def run_command(command: list[str], repo_root: Path) -> None:
    completed = subprocess.run(command, cwd=repo_root)
    if completed.returncode != 0:
        raise click.ClickException(f"command failed with exit code {completed.returncode}: {' '.join(command)}")


def check_mark(label: str, ok: bool, detail: str = "") -> None:
    status = "ok" if ok else "fail"
    message = f"{status:4} {label}"
    if detail:
        message = f"{message} - {detail}"
    click.echo(message)


def warn_mark(label: str, ok: bool, detail: str = "") -> None:
    status = "ok" if ok else "warn"
    message = f"{status:4} {label}"
    if detail:
        message = f"{message} - {detail}"
    click.echo(message)


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def tcp_connects(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def fetch_status(url: str, timeout: float = 2.0) -> int | None:
    request = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except (OSError, urllib.error.URLError):
        return None


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="mbse-lab")
@click.option(
    "--repo-root",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    help="Path to the shared mbse lab repo. Defaults to searching from the current directory.",
)
@click.pass_context
def main(ctx: click.Context, repo_root: Path | None) -> None:
    """Operate the local SysML v2 lab and private model workspaces."""
    resolved_root = repo_root.resolve() if repo_root else find_repo_root()
    ctx.obj = CliContext(repo_root=resolved_root)


@main.command()
@click.pass_context
def doctor(ctx: click.Context) -> None:
    """Check local prerequisites, repo layout, workspace settings, and service reachability."""
    repo_root = ctx.find_object(CliContext).repo_root
    failures = 0

    check_mark("python", command_exists("python3"), sys.version.split()[0])
    if not command_exists("python3"):
        failures += 1

    docker_ok = command_exists("docker")
    check_mark("docker", docker_ok)
    if not docker_ok:
        failures += 1
    elif subprocess.run(["docker", "compose", "version"], capture_output=True, text=True).returncode == 0:
        check_mark("docker compose", True)
    else:
        check_mark("docker compose", False)
        failures += 1

    if repo_root:
        check_mark("repo root", True, str(repo_root))
        for marker in REQUIRED_MARKERS:
            exists = (repo_root / marker).exists()
            check_mark(str(marker), exists)
            if not exists:
                failures += 1
        warn_mark("Flexo env", (repo_root / "deploy/flexo-mms/.env").exists(), "run `make init` if missing")
        warn_mark("SysON env", (repo_root / "deploy/syson/.env").exists(), "copy deploy/syson/.env.example if missing")
    else:
        check_mark("repo root", False, "run from the repo or pass --repo-root")
        failures += 1

    workspace = os.environ.get("MBSE_MODEL_WORKSPACE")
    if workspace:
        workspace_path = Path(workspace).expanduser()
        warn_mark("MBSE_MODEL_WORKSPACE", workspace_path.exists(), str(workspace_path))
    else:
        warn_mark("MBSE_MODEL_WORKSPACE", False, "unset; generated artifacts default to exports/")

    for label, port in (
        ("Flexo SysML v2 port", 18083),
        ("SysON web port", 18090),
    ):
        warn_mark(label, tcp_connects("localhost", port), f"localhost:{port}")

    for label, url in (
        ("Flexo projects API", "http://localhost:18083/projects"),
        ("SysON web", "http://localhost:18090/"),
    ):
        status = fetch_status(url)
        warn_mark(label, status is not None and status < 500, f"status={status}" if status else url)

    if failures:
        raise click.ClickException(f"doctor found {failures} required failure(s)")


@main.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Run the existing Flexo and SysON status checks."""
    repo_root = require_repo_root(ctx)
    run_command(["python3", "scripts/flexo_mms_env.py", "status", "--with-sysmlv2", "--strict"], repo_root)
    run_command(["docker", "compose", "-f", "deploy/syson/docker-compose.yml", "ps"], repo_root)


@main.command()
@click.pass_context
def diagnostics(ctx: click.Context) -> None:
    """Collect a redacted diagnostics bundle."""
    repo_root = require_repo_root(ctx)
    run_command(["python3", "scripts/collect_diagnostics.py"], repo_root)


@main.group()
def workspace() -> None:
    """Create and inspect private model workspaces."""


@workspace.command("init")
@click.argument("path", type=click.Path(path_type=Path))
@click.option("--force", is_flag=True, help="Overwrite generated README.md and .gitignore files.")
@click.option("--git/--no-git", "git_init", default=True, help="Initialize a git repository if one is not present.")
def workspace_init(path: Path, force: bool, git_init: bool) -> None:
    """Initialize a private model workspace."""
    root = path.expanduser().resolve()
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

    click.echo(f"Initialized model workspace: {root}")
    click.echo(f"Set it for bridge defaults with: export MBSE_MODEL_WORKSPACE={root}")


@workspace.command("check")
@click.argument("path", type=click.Path(path_type=Path), required=False)
def workspace_check(path: Path | None) -> None:
    """Check a private model workspace layout."""
    workspace_value = path or os.environ.get("MBSE_MODEL_WORKSPACE")
    if not workspace_value:
        raise click.ClickException("Provide PATH or set MBSE_MODEL_WORKSPACE.")
    root = Path(workspace_value).expanduser()
    root = root.resolve()
    failures = 0
    check_mark("workspace root", root.exists(), str(root))
    if not root.exists():
        raise click.ClickException(f"workspace does not exist: {root}")
    for directory in WORKSPACE_DIRS:
        exists = (root / directory).is_dir()
        check_mark(directory, exists)
        if not exists:
            failures += 1
    warn_mark("git repo", (root / ".git").exists())
    if failures:
        raise click.ClickException(f"workspace is missing {failures} expected directorie(s)")


@workspace.command("env")
@click.argument("path", type=click.Path(path_type=Path), required=False)
def workspace_env(path: Path | None) -> None:
    """Print the shell command for setting MBSE_MODEL_WORKSPACE."""
    workspace_value = path or os.environ.get("MBSE_MODEL_WORKSPACE")
    if not workspace_value:
        raise click.ClickException("Provide PATH or set MBSE_MODEL_WORKSPACE.")
    root = Path(workspace_value).expanduser().resolve()
    click.echo(f"export MBSE_MODEL_WORKSPACE={root}")


@main.group()
def deployment() -> None:
    """Inspect or verify the container deployment contract."""


@deployment.command("contract")
@click.pass_context
def deployment_contract(ctx: click.Context) -> None:
    """Print the fixture-derived deployment runtime contract."""
    repo_root = require_repo_root(ctx)
    run_command(["python3", "scripts/flexo_syson_bridge.py", "deployment-contract"], repo_root)


@deployment.command("verify")
@click.pass_context
def deployment_verify(ctx: click.Context) -> None:
    """Verify Docker runtime state against the deployment contract."""
    repo_root = require_repo_root(ctx)
    run_command(["python3", "scripts/flexo_syson_bridge.py", "deployment-verify"], repo_root)


if __name__ == "__main__":
    main()
