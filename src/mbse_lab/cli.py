"""Command-line interface for the SysML v2 local lab."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import click

from mbse_lab import __version__
from mbse_lab.constants import (
    DEFAULT_FLEXO_URL,
    DEFAULT_SYSON_URL,
    FLEXO_CONTAINERS,
    REQUIRED_MARKERS,
    SYSON_CONTAINERS,
    WORKSPACE_DIRS,
)
from mbse_lab.health import (
    check_mark,
    command_exists,
    docker_container_report,
    doctor_report,
    service_report,
    tcp_connects,
    warn_mark,
)
from mbse_lab.http import fetch_status, trim_url
from mbse_lab.model import (
    commit_flexo_package,
    create_flexo_project,
    create_syson_project,
    import_sysml_text,
    syson_latest_commit_id,
    syson_root_package_id,
)
from mbse_lab.reports import cleanup_generated, report_data, write_report
from mbse_lab.share import scan_share_issues
from mbse_lab.shell import run_capture, run_capture_result, run_command
from mbse_lab.workspace import default_output_dir, ensure_syson_env, initialize_model_workspace, sanitize_identifier

MODEL_WORKSPACE_ENV = "MBSE_MODEL_WORKSPACE"

__all__ = (
    "DEFAULT_FLEXO_URL",
    "DEFAULT_SYSON_URL",
    "FLEXO_CONTAINERS",
    "SYSON_CONTAINERS",
    "WORKSPACE_DIRS",
    "docker_container_report",
    "fetch_status",
    "main",
    "run_capture",
    "run_capture_result",
    "scan_share_issues",
)


def should_warn_repo_local_exports(explicit_output: Path | None, allow_repo_exports: bool = False) -> bool:
    return not allow_repo_exports and explicit_output is None and not os.environ.get(MODEL_WORKSPACE_ENV)


def warn_repo_local_exports(output_dir: Path) -> None:
    click.echo(
        (
            f"warning: {MODEL_WORKSPACE_ENV} is unset; generated model artifacts "
            f"will be written under repo-local `{output_dir}`. Set {MODEL_WORKSPACE_ENV} "
            "or pass an explicit output path for private model data. "
            "Pass --allow-repo-exports to suppress this warning."
        ),
        err=True,
    )


def first_model_dry_run_summary(
    name: str,
    package_name: str,
    syson_project_name: str,
    output_dir: Path,
    flexo_url: str,
    syson_url: str,
) -> dict[str, object]:
    package_identifier = sanitize_identifier(package_name)
    return {
        "status": "dry-run",
        "model_name": name,
        "package_name": package_name,
        "package_identifier": package_identifier,
        "syson_project_name": syson_project_name,
        "export_path": str(output_dir / "flexo" / "<flexo-project-id>.json"),
        "sysml_path": str(output_dir / "sysml" / "<flexo-project-id>.sysml"),
        "flexo_url": flexo_url,
        "syson_url": syson_url,
        "planned_steps": [
            f"create Flexo project `{name}` at {flexo_url}",
            f"commit Package `{package_name}`",
            f"export Flexo JSON to {output_dir / 'flexo' / '<flexo-project-id>.json'}",
            f"render SysML to {output_dir / 'sysml' / '<flexo-project-id>.sysml'}",
            f"create SysON project `{syson_project_name}` at {syson_url}",
            f"import package `{package_identifier}` into the SysON root package",
        ],
    }


def echo_first_model_dry_run(summary: dict[str, object]) -> None:
    for step in summary["planned_steps"] if isinstance(summary.get("planned_steps"), list) else []:
        click.echo(f"dry-run: {step}")


def create_first_model_summary(
    repo_root: Path,
    name: str,
    package_name: str,
    syson_project_name: str,
    output_dir: Path,
    flexo_url: str,
    syson_url: str,
    timeout: int,
    preflight: bool = True,
) -> dict[str, object]:
    if preflight:
        wait_for_readiness(readiness_probes(flexo_url=flexo_url, syson_url=syson_url), timeout)

    package_id = str(uuid.uuid4())
    flexo_project = create_flexo_project(flexo_url, name, timeout)
    flexo_project_id = str(flexo_project["@id"])
    flexo_commit = commit_flexo_package(flexo_url, flexo_project_id, package_id, package_name, timeout)
    flexo_commit_id = str(flexo_commit["@id"])

    export_path = output_dir / "flexo" / f"{flexo_project_id}.json"
    sysml_path = output_dir / "sysml" / f"{flexo_project_id}.sysml"
    run_command(
        [
            "python3",
            "scripts/flexo_syson_bridge.py",
            "flexo-export",
            flexo_project_id,
            "--commit-id",
            flexo_commit_id,
            "--output",
            str(export_path),
            "--flexo-url",
            flexo_url,
            "--timeout",
            str(timeout),
        ],
        repo_root,
    )
    run_command(
        ["python3", "scripts/flexo_syson_bridge.py", "render-sysml", str(export_path), "--output", str(sysml_path)],
        repo_root,
    )

    syson_project = create_syson_project(syson_url, syson_project_name, timeout)
    syson_project_id = str(syson_project["id"])
    editing_context = syson_project.get("currentEditingContext") or {}
    if not isinstance(editing_context, dict) or not editing_context.get("id"):
        raise click.ClickException(f"SysON project has no editing context: {syson_project_id}")
    editing_context_id = str(editing_context["id"])
    syson_commit_id = syson_latest_commit_id(syson_url, syson_project_id, timeout)
    namespace_id = syson_root_package_id(syson_url, syson_project_id, syson_commit_id, timeout)
    import_result = import_sysml_text(
        syson_url,
        namespace_id,
        editing_context_id,
        sysml_path.read_text(encoding="utf-8"),
        timeout,
    )

    return {
        "flexo_project_id": flexo_project_id,
        "flexo_commit_id": flexo_commit_id,
        "package_id": package_id,
        "package_name": package_name,
        "export_path": str(export_path),
        "sysml_path": str(sysml_path),
        "syson_project_id": syson_project_id,
        "syson_project_name": syson_project_name,
        "syson_commit_id": syson_commit_id,
        "namespace_id": namespace_id,
        "editing_context_id": editing_context_id,
        "import_result": import_result,
        "syson_url": syson_url,
    }


COMPLETION_ENVVAR = "_MBSE_LAB_COMPLETE"


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


def run_bridge(ctx: click.Context, args: list[str], dry_run: bool = False) -> None:
    repo_root = require_repo_root(ctx)
    run_command(["python3", "scripts/flexo_syson_bridge.py", *args], repo_root, dry_run)


def run_syson_compose(ctx: click.Context, args: list[str], dry_run: bool = False) -> None:
    repo_root = require_repo_root(ctx)
    run_command(["docker", "compose", "-f", "deploy/syson/docker-compose.yml", *args], repo_root, dry_run)


def run_flexo_env(ctx: click.Context, args: list[str], dry_run: bool = False) -> None:
    repo_root = require_repo_root(ctx)
    run_command(["python3", "scripts/flexo_mms_env.py", *args], repo_root, dry_run)


def print_service_urls() -> None:
    click.echo("")
    click.echo("Service URLs:")
    click.echo("  Flexo Layer1 API:   http://localhost:18080")
    click.echo("  Flexo SysML v2 API: http://localhost:18083")
    click.echo("  SysON Web UI:       http://localhost:18090")
    click.echo("  SysON GraphQL API:  http://localhost:18090/api/graphql")


@dataclass(frozen=True)
class ReadinessProbe:
    label: str
    url: str
    next_step: str


def readiness_probes(
    flexo: bool = True,
    syson: bool = True,
    flexo_url: str = DEFAULT_FLEXO_URL,
    syson_url: str = DEFAULT_SYSON_URL,
) -> list[ReadinessProbe]:
    probes: list[ReadinessProbe] = []
    if flexo:
        probes.append(
            ReadinessProbe(
                label="Flexo SysML v2 API",
                url=f"{trim_url(flexo_url)}/projects",
                next_step="mbse-lab services up --flexo --timeout 60",
            )
        )
    if syson:
        probes.append(
            ReadinessProbe(
                label="SysON Web UI",
                url=f"{trim_url(syson_url)}/",
                next_step="mbse-lab services up --syson --timeout 60",
            )
        )
    return probes


def wait_for_readiness(probes: list[ReadinessProbe], timeout: int, interval: float = 2.0) -> None:
    if not probes:
        return
    deadline = time.monotonic() + max(timeout, 0)
    pending = {probe.label: probe for probe in probes}
    last_status: dict[str, int | None] = {probe.label: None for probe in probes}

    while pending:
        for label, probe in list(pending.items()):
            status = fetch_status(probe.url)
            last_status[label] = status
            if status is not None and status < 500:
                del pending[label]
        if not pending:
            click.echo("Service readiness checks passed.")
            return
        if time.monotonic() >= deadline:
            details = []
            for label, probe in pending.items():
                status = last_status[label]
                status_detail = f"last status {status}" if status is not None else "no HTTP response"
                details.append(f"{label} at {probe.url} ({status_detail}; next: `{probe.next_step}`)")
            raise click.ClickException(f"Service readiness failed after {timeout}s: " + "; ".join(details))
        time.sleep(min(interval, max(deadline - time.monotonic(), 0)))


def unique_lines(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    unique = []
    for line in lines:
        if line in seen:
            continue
        seen.add(line)
        unique.append(line)
    return unique


def apply_doctor_fixes(repo_root: Path | None) -> tuple[list[str], list[str]]:
    fixed: list[str] = []
    next_steps: list[str] = []

    if not repo_root:
        next_steps.append("mbse-lab --repo-root <path-to-mbse-repo> doctor --fix")
    else:
        if not (repo_root / "deploy/flexo-mms/.env").exists():
            next_steps.append("mbse-lab init")

        syson_env = repo_root / "deploy/syson/.env"
        if not syson_env.exists():
            ensure_syson_env(repo_root)
            fixed.append("created deploy/syson/.env from deploy/syson/.env.example")

    workspace = os.environ.get("MBSE_MODEL_WORKSPACE")
    if workspace:
        workspace_root = Path(workspace).expanduser()
        missing_layout = not workspace_root.exists() or any(
            not (workspace_root / directory).is_dir() for directory in WORKSPACE_DIRS
        )
        missing_layout = missing_layout or not (workspace_root / "README.md").exists()
        missing_layout = missing_layout or not (workspace_root / ".gitignore").exists()
        if missing_layout:
            initialized = initialize_model_workspace(workspace_root, force=False, git_init=False)
            fixed.append(f"initialized model workspace layout at {initialized}")
    else:
        next_steps.append("mbse-lab workspace init <private-model-workspace>")
        next_steps.append("export MBSE_MODEL_WORKSPACE=<private-model-workspace>")

    if not command_exists("docker"):
        next_steps.append("Install Docker and make the `docker` command available.")
    elif subprocess.run(["docker", "compose", "version"], capture_output=True, text=True).returncode != 0:
        next_steps.append("Install the Docker Compose plugin so `docker compose version` succeeds.")

    if repo_root:
        flexo_reachable = tcp_connects("localhost", 18083)
        syson_reachable = tcp_connects("localhost", 18090)
        if not flexo_reachable:
            next_steps.append("mbse-lab services up --flexo --timeout 60")
        if not syson_reachable:
            next_steps.append("mbse-lab services up --syson --timeout 60")
        if not flexo_reachable:
            next_steps.append("mbse-lab flexo init-org")
            next_steps.append("mbse-lab flexo backup")

    return fixed, unique_lines(next_steps)


def completion_snippet(shell: str) -> str:
    snippets = {
        "bash": f'eval "$({COMPLETION_ENVVAR}=bash_source mbse-lab)"',
        "zsh": f"source <({COMPLETION_ENVVAR}=zsh_source mbse-lab)",
        "fish": f"{COMPLETION_ENVVAR}=fish_source mbse-lab | source",
    }
    return snippets[shell]


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
@click.argument("shell", type=click.Choice(("bash", "zsh", "fish")))
def completion(shell: str) -> None:
    """Print shell completion setup for Bash, Zsh, or Fish."""
    click.echo(completion_snippet(shell))


@main.command()
@click.option(
    "--model-workspace",
    type=click.Path(path_type=Path),
    help="Initialize a private model workspace and print the export command.",
)
@click.option("--force-workspace", is_flag=True, help="Overwrite generated workspace README.md and .gitignore files.")
@click.option(
    "--workspace-git/--no-workspace-git",
    default=True,
    help="Initialize git in --model-workspace when needed.",
)
@click.option("--dry-run", is_flag=True, help="Print the planned setup without changing files.")
@click.pass_context
def init(
    ctx: click.Context,
    model_workspace: Path | None,
    force_workspace: bool,
    workspace_git: bool,
    dry_run: bool,
) -> None:
    """Create local runtime env files and optional private workspace layout."""
    repo_root = require_repo_root(ctx)
    click.echo(f"Initializing SysML v2 lab files at {repo_root}")

    run_flexo_env(ctx, ["init", "--with-sysmlv2"], dry_run)
    ensure_syson_env(repo_root, dry_run)

    if model_workspace:
        workspace_root = initialize_model_workspace(model_workspace, force_workspace, workspace_git, dry_run)
        click.echo(f"Model workspace: {workspace_root}")
        click.echo(f"Set it for bridge defaults with: export MBSE_MODEL_WORKSPACE={workspace_root}")
    elif not os.environ.get("MBSE_MODEL_WORKSPACE"):
        click.echo("No model workspace configured. Set MBSE_MODEL_WORKSPACE or pass --model-workspace.")

    click.echo("")
    click.echo("Next:")
    click.echo("  mbse-lab doctor")
    click.echo("  mbse-lab services up")


@main.command()
@click.option(
    "--model-workspace",
    type=click.Path(path_type=Path),
    help="Initialize a private model workspace and print the export command.",
)
@click.option("--force-workspace", is_flag=True, help="Overwrite generated workspace README.md and .gitignore files.")
@click.option(
    "--workspace-git/--no-workspace-git",
    default=True,
    help="Initialize git in --model-workspace when needed.",
)
@click.option("--skip-start", is_flag=True, help="Prepare files but do not start Flexo or SysON containers.")
@click.option("--skip-flexo-org", is_flag=True, help="Do not initialize the Flexo SysML v2 org.")
@click.option("--skip-backup", is_flag=True, help="Do not back up Flexo after org initialization.")
@click.option("--skip-status", is_flag=True, help="Do not run final service status checks.")
@click.option("--timeout", type=int, default=60, show_default=True, help="Container startup/status timeout in seconds.")
@click.option("--dry-run", is_flag=True, help="Print the planned commands without changing files or containers.")
@click.pass_context
def bootstrap(
    ctx: click.Context,
    model_workspace: Path | None,
    force_workspace: bool,
    workspace_git: bool,
    skip_start: bool,
    skip_flexo_org: bool,
    skip_backup: bool,
    skip_status: bool,
    timeout: int,
    dry_run: bool,
) -> None:
    """Prepare the local lab for first use."""
    repo_root = require_repo_root(ctx)
    click.echo(f"Bootstrapping SysML v2 lab at {repo_root}")

    run_command(["python3", "scripts/flexo_mms_env.py", "init", "--with-sysmlv2"], repo_root, dry_run)
    ensure_syson_env(repo_root, dry_run)

    if model_workspace:
        workspace_root = initialize_model_workspace(model_workspace, force_workspace, workspace_git, dry_run)
        click.echo(f"Model workspace: {workspace_root}")
        click.echo(f"Set it for bridge defaults with: export MBSE_MODEL_WORKSPACE={workspace_root}")
    elif not os.environ.get("MBSE_MODEL_WORKSPACE"):
        click.echo("No model workspace configured. Set MBSE_MODEL_WORKSPACE or pass --model-workspace.")

    if not skip_start:
        run_command(
            ["python3", "scripts/flexo_mms_env.py", "up", "--wait", "--timeout", str(timeout)],
            repo_root,
            dry_run,
        )
        run_command(["docker", "compose", "-f", "deploy/syson/docker-compose.yml", "up", "-d"], repo_root, dry_run)
        if not dry_run:
            wait_for_readiness(readiness_probes(), timeout)

    if not skip_flexo_org:
        run_command(["python3", "scripts/flexo_syson_bridge.py", "init-flexo-org"], repo_root, dry_run)
        if not skip_backup:
            run_command(["python3", "scripts/flexo_mms_env.py", "backup"], repo_root, dry_run)

    if not skip_status:
        run_command(
            ["python3", "scripts/flexo_mms_env.py", "status", "--with-sysmlv2", "--strict"],
            repo_root,
            dry_run,
        )
        run_command(["docker", "compose", "-f", "deploy/syson/docker-compose.yml", "ps"], repo_root, dry_run)

    print_service_urls()
    click.echo("")
    click.echo("Next:")
    click.echo("  mbse-lab doctor")
    click.echo("  mbse-lab workspace env <private-workspace>")
    click.echo('  mbse-lab first-model "My First Model"')


@main.command("first-model")
@click.argument("name", default="First Model", required=False)
@click.option("--package-name", help="Name of the first SysML package. Defaults to NAME.")
@click.option("--syson-project-name", help="Name of the SysON review project. Defaults to '<NAME> Review'.")
@click.option("--output-dir", type=click.Path(path_type=Path), help="Directory for generated export artifacts.")
@click.option("--flexo-url", default=DEFAULT_FLEXO_URL, show_default=True)
@click.option("--syson-url", default=DEFAULT_SYSON_URL, show_default=True)
@click.option("--timeout", type=int, default=30, show_default=True)
@click.option("--json-output", is_flag=True, help="Print a machine-readable JSON summary.")
@click.option("--dry-run", is_flag=True, help="Print the planned workflow without creating projects.")
@click.option(
    "--allow-repo-exports",
    is_flag=True,
    help="Suppress the warning when MBSE_MODEL_WORKSPACE is unset and writing to repo-local exports/.",
)
@click.pass_context
def first_model(
    ctx: click.Context,
    name: str,
    package_name: str | None,
    syson_project_name: str | None,
    output_dir: Path | None,
    flexo_url: str,
    syson_url: str,
    timeout: int,
    json_output: bool,
    dry_run: bool,
    allow_repo_exports: bool,
) -> None:
    """Create a tiny Flexo model and import it into a SysON review project."""
    repo_root = require_repo_root(ctx)
    resolved_package_name = package_name or name
    resolved_syson_project_name = syson_project_name or f"{name} Review"
    resolved_output_dir = (output_dir or default_output_dir()).expanduser()
    if should_warn_repo_local_exports(output_dir, allow_repo_exports):
        warn_repo_local_exports(resolved_output_dir)

    if dry_run:
        echo_first_model_dry_run(
            first_model_dry_run_summary(
                name,
                resolved_package_name,
                resolved_syson_project_name,
                resolved_output_dir,
                flexo_url,
                syson_url,
            )
        )
        return

    summary = create_first_model_summary(
        repo_root,
        name,
        resolved_package_name,
        resolved_syson_project_name,
        resolved_output_dir,
        flexo_url,
        syson_url,
        timeout,
    )
    if json_output:
        click.echo(json.dumps(summary, indent=2, sort_keys=True))
        return

    click.echo("Created first SysML v2 model.")
    click.echo(f"  Flexo project: {summary['flexo_project_id']}")
    click.echo(f"  Flexo commit:  {summary['flexo_commit_id']}")
    click.echo(f"  Package:       {summary['package_name']} ({summary['package_id']})")
    click.echo(f"  Flexo export:  {summary['export_path']}")
    click.echo(f"  SysML text:    {summary['sysml_path']}")
    click.echo(f"  SysON project: {summary['syson_project_id']}")
    click.echo(f"  SysON root:    {summary['namespace_id']}")
    click.echo(f"  Open SysON:    {trim_url(syson_url)}")


@main.group()
def smoke() -> None:
    """Run proof workflows for the local lab."""


@smoke.command("first-use")
@click.argument("name", default="First Use Smoke Model", required=False)
@click.option("--package-name", help="Name of the first SysML package. Defaults to NAME.")
@click.option("--syson-project-name", help="Name of the SysON review project. Defaults to '<NAME> Review'.")
@click.option("--output-dir", type=click.Path(path_type=Path), help="Directory for generated export artifacts.")
@click.option(
    "--report-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=Path("reports/latest"),
    show_default=True,
    help="Directory for the generated lab report.",
)
@click.option("--flexo-url", default=DEFAULT_FLEXO_URL, show_default=True)
@click.option("--syson-url", default=DEFAULT_SYSON_URL, show_default=True)
@click.option("--timeout", type=int, default=60, show_default=True)
@click.option("--json-output", is_flag=True, help="Print a machine-readable JSON summary.")
@click.option(
    "--dry-run", is_flag=True, help="Print the planned workflow without starting services or creating projects."
)
@click.option(
    "--allow-repo-exports",
    is_flag=True,
    help="Suppress the warning when MBSE_MODEL_WORKSPACE is unset and writing to repo-local exports/.",
)
@click.pass_context
def smoke_first_use(
    ctx: click.Context,
    name: str,
    package_name: str | None,
    syson_project_name: str | None,
    output_dir: Path | None,
    report_dir: Path,
    flexo_url: str,
    syson_url: str,
    timeout: int,
    json_output: bool,
    dry_run: bool,
    allow_repo_exports: bool,
) -> None:
    """Validate first-use setup by creating and importing a disposable model."""
    repo_root = require_repo_root(ctx)
    resolved_package_name = package_name or name
    resolved_syson_project_name = syson_project_name or f"{name} Review"
    resolved_output_dir = (output_dir or default_output_dir()).expanduser()
    resolved_report_dir = report_dir.expanduser()
    if not resolved_report_dir.is_absolute():
        resolved_report_dir = repo_root / resolved_report_dir
    report_path = resolved_report_dir / "index.md"

    if should_warn_repo_local_exports(output_dir, allow_repo_exports):
        warn_repo_local_exports(resolved_output_dir)

    model_plan = first_model_dry_run_summary(
        name,
        resolved_package_name,
        resolved_syson_project_name,
        resolved_output_dir,
        flexo_url,
        syson_url,
    )
    dry_run_summary = {
        "status": "dry-run",
        "model": model_plan,
        "report_path": str(report_path),
        "planned_steps": [
            f"start Flexo services with timeout {timeout}s",
            "start SysON services",
            f"wait for Flexo and SysON readiness for up to {timeout}s",
            "initialize Flexo SysML v2 org",
            *[str(step) for step in model_plan.get("planned_steps", [])],
            f"write lab report to {report_path}",
        ],
    }

    if dry_run:
        if json_output:
            click.echo(json.dumps(dry_run_summary, indent=2, sort_keys=True))
            return
        for step in dry_run_summary["planned_steps"] if isinstance(dry_run_summary["planned_steps"], list) else []:
            click.echo(f"dry-run: {step}")
        return

    run_command(["python3", "scripts/flexo_mms_env.py", "up", "--wait", "--timeout", str(timeout)], repo_root)
    run_command(["docker", "compose", "-f", "deploy/syson/docker-compose.yml", "up", "-d"], repo_root)
    wait_for_readiness(readiness_probes(flexo_url=flexo_url, syson_url=syson_url), timeout)
    run_command(["python3", "scripts/flexo_syson_bridge.py", "init-flexo-org"], repo_root)
    model_summary = create_first_model_summary(
        repo_root,
        name,
        resolved_package_name,
        resolved_syson_project_name,
        resolved_output_dir,
        flexo_url,
        syson_url,
        timeout,
        preflight=False,
    )
    write_report(resolved_report_dir, report_data(repo_root))

    summary = {
        "status": "passed",
        "model": model_summary,
        "report_path": str(report_path),
        "service_urls": {
            "flexo_sysmlv2": flexo_url,
            "syson_web": syson_url,
            "syson_graphql": f"{trim_url(syson_url)}/api/graphql",
        },
    }
    if json_output:
        click.echo(json.dumps(summary, indent=2, sort_keys=True))
        return

    click.echo("First-use smoke workflow passed.")
    click.echo(f"  Flexo project: {model_summary['flexo_project_id']}")
    click.echo(f"  SysON project: {model_summary['syson_project_id']}")
    click.echo(f"  Flexo export:  {model_summary['export_path']}")
    click.echo(f"  SysML text:    {model_summary['sysml_path']}")
    click.echo(f"  Report:        {report_path}")
    click.echo(f"  Open SysON:    {trim_url(syson_url)}")


@main.command()
@click.option("--json-output", is_flag=True, help="Print a machine-readable JSON report.")
@click.option("--fix", is_flag=True, help="Apply low-risk local setup fixes and print remaining next commands.")
@click.pass_context
def doctor(ctx: click.Context, json_output: bool, fix: bool) -> None:
    """Check local prerequisites, repo layout, workspace settings, and service reachability."""
    repo_root = ctx.find_object(CliContext).repo_root
    if fix and json_output:
        raise click.ClickException("--fix cannot be combined with --json-output")
    if fix:
        fixed, next_steps = apply_doctor_fixes(repo_root)
        if fixed:
            click.echo("Applied fixes:")
            for item in fixed:
                click.echo(f"  - {item}")
        else:
            click.echo("No automatic fixes were needed.")
        if next_steps:
            click.echo("")
            click.echo("Next commands:")
            for step in next_steps:
                click.echo(f"  {step}")
        click.echo("")

    report = doctor_report(repo_root)
    if json_output:
        click.echo(json.dumps(report, indent=2, sort_keys=True))
        if report["status"] == "failed":
            raise click.ClickException("doctor found required failure(s)")
        return

    failures = 0

    click.echo("--- Prerequisites ---")
    python_ok = command_exists("python3")
    check_mark("python", python_ok, sys.version.split()[0])
    if not python_ok:
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

    click.echo("")
    click.echo("--- Repo Setup ---")
    if repo_root:
        check_mark("repo root", True, str(repo_root))
        for marker in REQUIRED_MARKERS:
            exists = (repo_root / marker).exists()
            check_mark(str(marker), exists)
            if not exists:
                failures += 1
        warn_mark("Flexo env", (repo_root / "deploy/flexo-mms/.env").exists(), "run `make init` if missing")
        warn_mark("SysON env", (repo_root / "deploy/syson/.env").exists(), "run `mbse-lab init` if missing")
    else:
        check_mark("repo root", False, "run from the repo or pass --repo-root")
        failures += 1

    click.echo("")
    click.echo("--- Workspace ---")
    workspace = os.environ.get("MBSE_MODEL_WORKSPACE")
    if workspace:
        workspace_path = Path(workspace).expanduser()
        warn_mark("MBSE_MODEL_WORKSPACE", workspace_path.exists(), str(workspace_path))
    else:
        warn_mark("MBSE_MODEL_WORKSPACE", False, "unset; generated artifacts default to exports/")

    click.echo("")
    click.echo("--- Services ---")
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

    syson_database_credentials = report["checks"].get("syson_database_credentials")
    if isinstance(syson_database_credentials, dict):
        warn_mark(
            "SysON database credentials",
            bool(syson_database_credentials.get("ok")),
            str(syson_database_credentials.get("detail", "")),
        )

    remediation_codes = report.get("remediation_codes", [])
    if remediation_codes:
        click.echo("")
        click.echo("--- Remediation Codes ---")
        for code in remediation_codes:
            click.echo(f"  {code}")

    if failures:
        raise click.ClickException(f"doctor found {failures} required failure(s)")


@main.command()
@click.option("--json-output", is_flag=True, help="Print a machine-readable JSON report.")
@click.pass_context
def status(ctx: click.Context, json_output: bool) -> None:
    """Run the existing Flexo and SysON status checks."""
    repo_root = require_repo_root(ctx)
    if json_output:
        click.echo(json.dumps(service_report(repo_root), indent=2, sort_keys=True))
        return
    run_command(["python3", "scripts/flexo_mms_env.py", "status", "--with-sysmlv2", "--strict"], repo_root)
    run_command(["docker", "compose", "-f", "deploy/syson/docker-compose.yml", "ps"], repo_root)


@main.group()
def services() -> None:
    """Start, stop, restart, and inspect local lab services."""


@services.command("up")
@click.option("--flexo/--no-flexo", default=True, help="Start Flexo services.")
@click.option("--syson/--no-syson", default=True, help="Start SysON services.")
@click.option("--wait/--no-wait", default=True, help="Wait for selected service APIs during startup.")
@click.option("--timeout", type=int, default=60, show_default=True, help="Startup readiness timeout in seconds.")
@click.option("--dry-run", is_flag=True, help="Print commands without changing containers.")
@click.pass_context
def services_up(ctx: click.Context, flexo: bool, syson: bool, wait: bool, timeout: int, dry_run: bool) -> None:
    """Start Flexo and SysON services."""
    if not flexo and not syson:
        raise click.ClickException("Select at least one service family.")
    if flexo:
        args = ["up"]
        if wait:
            args.extend(["--wait", "--timeout", str(timeout)])
        run_flexo_env(ctx, args, dry_run)
    if syson:
        run_syson_compose(ctx, ["up", "-d"], dry_run)
    if wait and not dry_run:
        wait_for_readiness(readiness_probes(flexo=flexo, syson=syson), timeout)
    if not dry_run:
        print_service_urls()


@services.command("down")
@click.option("--flexo/--no-flexo", default=True, help="Stop Flexo services.")
@click.option("--syson/--no-syson", default=True, help="Stop SysON services.")
@click.option("--volumes", is_flag=True, help="Also remove Flexo compose-managed volumes.")
@click.option("--dry-run", is_flag=True, help="Print commands without changing containers.")
@click.pass_context
def services_down(ctx: click.Context, flexo: bool, syson: bool, volumes: bool, dry_run: bool) -> None:
    """Stop Flexo and SysON services without deleting runtime data."""
    if not flexo and not syson:
        raise click.ClickException("Select at least one service family.")
    if syson:
        run_syson_compose(ctx, ["down"], dry_run)
    if flexo:
        args = ["down"]
        if volumes:
            args.append("--volumes")
        run_flexo_env(ctx, args, dry_run)


@services.command("restart")
@click.option("--flexo/--no-flexo", default=True, help="Restart Flexo services.")
@click.option("--syson/--no-syson", default=True, help="Restart SysON services.")
@click.option("--wait/--no-wait", default=True, help="Wait for Flexo health during startup.")
@click.option("--timeout", type=int, default=60, show_default=True, help="Flexo startup wait timeout in seconds.")
@click.option("--dry-run", is_flag=True, help="Print commands without changing containers.")
@click.pass_context
def services_restart(ctx: click.Context, flexo: bool, syson: bool, wait: bool, timeout: int, dry_run: bool) -> None:
    """Restart Flexo and SysON services."""
    if not flexo and not syson:
        raise click.ClickException("Select at least one service family.")
    if syson:
        run_syson_compose(ctx, ["down"], dry_run)
    if flexo:
        run_flexo_env(ctx, ["down"], dry_run)
        args = ["up"]
        if wait:
            args.extend(["--wait", "--timeout", str(timeout)])
        run_flexo_env(ctx, args, dry_run)
    if syson:
        run_syson_compose(ctx, ["up", "-d"], dry_run)
    if not dry_run:
        print_service_urls()


@services.command("logs")
@click.option("--flexo/--no-flexo", default=True, help="Show Flexo logs.")
@click.option("--syson/--no-syson", default=True, help="Show SysON app logs.")
@click.option("--flexo-service", "flexo_services", multiple=True, help="Flexo compose service to include.")
@click.option("--syson-service", "syson_services", multiple=True, help="SysON compose service to include.")
@click.option("--follow", "-f", is_flag=True, help="Follow logs.")
@click.option("--tail", type=int, default=100, show_default=True, help="Number of log lines to show.")
@click.option("--dry-run", is_flag=True, help="Print commands without reading logs.")
@click.pass_context
def services_logs(
    ctx: click.Context,
    flexo: bool,
    syson: bool,
    flexo_services: tuple[str, ...],
    syson_services: tuple[str, ...],
    follow: bool,
    tail: int,
    dry_run: bool,
) -> None:
    """Show recent Flexo and SysON service logs."""
    if not flexo and not syson:
        raise click.ClickException("Select at least one service family.")
    if flexo:
        args = ["logs", "--tail", str(tail)]
        if follow:
            args.append("--follow")
        args.extend(flexo_services)
        run_flexo_env(ctx, args, dry_run)
    if syson:
        args = ["logs", "--tail", str(tail)]
        if follow:
            args.append("--follow")
        args.extend(syson_services or ("app",))
        run_syson_compose(ctx, args, dry_run)


@main.command()
@click.option(
    "--public-safe",
    is_flag=True,
    help="Omit project lists and recent service logs from the diagnostics bundle.",
)
@click.option("--output", type=click.Path(path_type=Path), help="Diagnostics bundle output directory.")
@click.option("--timeout", type=int, default=20, show_default=True, help="Command and HTTP timeout in seconds.")
@click.option("--log-tail", type=int, default=80, show_default=True, help="Number of service log lines to collect.")
@click.pass_context
def diagnostics(ctx: click.Context, public_safe: bool, output: Path | None, timeout: int, log_tail: int) -> None:
    """Collect a redacted diagnostics bundle."""
    repo_root = require_repo_root(ctx)
    args = ["python3", "scripts/collect_diagnostics.py"]
    if public_safe:
        args.append("--public-safe")
    if output:
        args.extend(["--output", str(output)])
    args.extend(["--timeout", str(timeout), "--log-tail", str(log_tail)])
    run_command(args, repo_root)


@main.command()
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=Path("reports/latest"),
    show_default=True,
    help="Directory for generated report files.",
)
@click.pass_context
def report(ctx: click.Context, output_dir: Path) -> None:
    """Generate a static Markdown/HTML local lab report."""
    repo_root = require_repo_root(ctx)
    resolved_output_dir = output_dir if output_dir.is_absolute() else repo_root / output_dir
    data = report_data(repo_root)
    write_report(resolved_output_dir, data)
    click.echo(f"Wrote report: {resolved_output_dir / 'index.md'}")
    click.echo(f"Wrote report: {resolved_output_dir / 'index.html'}")


@main.command()
@click.option("--include-site", is_flag=True, help="Also remove MkDocs build output under site/.")
@click.option("--dry-run", is_flag=True, help="Print cleanup targets without removing files.")
@click.pass_context
def cleanup(ctx: click.Context, include_site: bool, dry_run: bool) -> None:
    """Remove generated local reports, diagnostics, run logs, and temporary output."""
    repo_root = require_repo_root(ctx)
    removed = cleanup_generated(repo_root, include_site, dry_run)
    if not removed:
        click.echo("No generated cleanup targets found.")
        return
    verb = "Would remove" if dry_run else "Removed"
    click.echo(f"{verb} {len(removed)} generated cleanup target(s).")


@main.command("share-check")
@click.pass_context
def share_check(ctx: click.Context) -> None:
    """Check for accidental private data before sharing the tooling repo."""
    repo_root = require_repo_root(ctx)
    issues = scan_share_issues(repo_root)
    if issues:
        click.echo("share-check failed:")
        for issue in issues:
            click.echo(f"  - {issue}")
        raise click.ClickException(f"found {len(issues)} sharing issue(s)")
    click.echo("share-check passed")


@main.group()
def flexo() -> None:
    """Work with Flexo SysML v2 projects."""


@flexo.command("init-org")
@click.option("--layer1-url", default="http://localhost:18080", show_default=True)
@click.option("--env-dir", type=click.Path(path_type=Path), default=Path("deploy/flexo-mms"), show_default=True)
@click.option("--org-id", default="sysmlv2", show_default=True)
@click.option("--title", default="SysML v2", show_default=True)
@click.option("--token")
@click.option("--timeout", type=int, default=30, show_default=True)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def flexo_init_org(
    ctx: click.Context,
    layer1_url: str,
    env_dir: Path,
    org_id: str,
    title: str,
    token: str | None,
    timeout: int,
    dry_run: bool,
) -> None:
    """Create the Flexo org used by the SysML v2 service."""
    args = [
        "init-flexo-org",
        "--layer1-url",
        layer1_url,
        "--env-dir",
        str(env_dir),
        "--org-id",
        org_id,
        "--title",
        title,
        "--timeout",
        str(timeout),
    ]
    if token:
        args.extend(["--token", token])
    run_bridge(ctx, args, dry_run)


@flexo.command("token")
@click.option("--url", help="Auth service login URL. Defaults to the generated auth host port.")
@click.option("--username", default="user01", show_default=True)
@click.option("--password", help="LDAP password. Defaults to FLEXO_MMS_LDAP_USER01_PASSWORD in .env.")
@click.option("--timeout", type=int, default=30, show_default=True)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def flexo_token(
    ctx: click.Context, url: str | None, username: str, password: str | None, timeout: int, dry_run: bool
) -> None:
    """Request a local Flexo JWT from the auth service."""
    args = ["token", "--username", username, "--timeout", str(timeout)]
    if url:
        args.extend(["--url", url])
    if password:
        args.extend(["--password", password])
    run_flexo_env(ctx, args, dry_run)


@flexo.command("backup")
@click.option("--url", help="Fuseki dataset URL. Defaults to the generated Fuseki host port.")
@click.option("--output", type=click.Path(path_type=Path), help="Backup file path.")
@click.option("--timeout", type=int, default=60, show_default=True)
@click.option(
    "--update-init/--no-update-init",
    default=False,
    help="Also refresh tracked mount/cluster.trig after export.",
)
@click.option(
    "--i-understand-this-updates-tracked-seed",
    is_flag=True,
    help="Required with --update-init to acknowledge that tracked seed data must be publishable.",
)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def flexo_backup(
    ctx: click.Context,
    url: str | None,
    output: Path | None,
    timeout: int,
    update_init: bool,
    i_understand_this_updates_tracked_seed: bool,
    dry_run: bool,
) -> None:
    """Export the live Flexo Fuseki dataset to a durable backup."""
    if update_init and not i_understand_this_updates_tracked_seed:
        raise click.ClickException(
            "Updating deploy/flexo-mms/mount/cluster.trig requires " "--i-understand-this-updates-tracked-seed."
        )
    if i_understand_this_updates_tracked_seed and not update_init:
        raise click.ClickException("--i-understand-this-updates-tracked-seed requires --update-init.")

    args = ["backup", "--timeout", str(timeout)]
    if url:
        args.extend(["--url", url])
    if output:
        args.extend(["--output", str(output)])
    if update_init:
        args.extend(["--update-init", "--i-understand-this-updates-tracked-seed"])
    run_flexo_env(ctx, args, dry_run)


@flexo.command("restore")
@click.argument("backup", type=click.Path(path_type=Path))
@click.option("--dry-run", is_flag=True)
@click.pass_context
def flexo_restore(ctx: click.Context, backup: Path, dry_run: bool) -> None:
    """Restore Flexo mount/cluster.trig from a backup file."""
    run_flexo_env(ctx, ["restore", str(backup)], dry_run)


@flexo.command("rotate-secrets")
@click.option("--dry-run", is_flag=True)
@click.pass_context
def flexo_rotate_secrets(ctx: click.Context, dry_run: bool) -> None:
    """Regenerate ignored local Flexo runtime secrets."""
    run_flexo_env(ctx, ["rotate-secrets"], dry_run)


@flexo.command("list")
@click.option("--json-output", is_flag=True, help="Print raw JSON from Flexo.")
@click.option("--flexo-url", default=DEFAULT_FLEXO_URL, show_default=True)
@click.option("--timeout", type=int, default=30, show_default=True)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def flexo_list(ctx: click.Context, json_output: bool, flexo_url: str, timeout: int, dry_run: bool) -> None:
    """List Flexo SysML v2 projects."""
    args = ["flexo-list-projects", "--flexo-url", flexo_url, "--timeout", str(timeout)]
    if json_output:
        args.append("--json")
    run_bridge(ctx, args, dry_run)


@flexo.command("create")
@click.argument("name")
@click.option("--description")
@click.option("--flexo-url", default=DEFAULT_FLEXO_URL, show_default=True)
@click.option("--timeout", type=int, default=30, show_default=True)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def flexo_create(
    ctx: click.Context, name: str, description: str | None, flexo_url: str, timeout: int, dry_run: bool
) -> None:
    """Create a Flexo SysML v2 project."""
    args = ["flexo-create-project", name, "--flexo-url", flexo_url, "--timeout", str(timeout)]
    if description:
        args.extend(["--description", description])
    run_bridge(ctx, args, dry_run)


@flexo.command("export")
@click.argument("project_id")
@click.option("--commit-id")
@click.option("--output", type=click.Path(path_type=Path))
@click.option("--flexo-url", default=DEFAULT_FLEXO_URL, show_default=True)
@click.option("--timeout", type=int, default=30, show_default=True)
@click.option("--dry-run", is_flag=True)
@click.option(
    "--allow-repo-exports",
    is_flag=True,
    help="Suppress the warning when MBSE_MODEL_WORKSPACE is unset and writing to repo-local exports/.",
)
@click.pass_context
def flexo_export(
    ctx: click.Context,
    project_id: str,
    commit_id: str | None,
    output: Path | None,
    flexo_url: str,
    timeout: int,
    dry_run: bool,
    allow_repo_exports: bool,
) -> None:
    """Export a Flexo project snapshot."""
    args = ["flexo-export", project_id, "--flexo-url", flexo_url, "--timeout", str(timeout)]
    if should_warn_repo_local_exports(output, allow_repo_exports):
        warn_repo_local_exports(default_output_dir())
    if commit_id:
        args.extend(["--commit-id", commit_id])
    if output:
        args.extend(["--output", str(output)])
    run_bridge(ctx, args, dry_run)


@main.group()
def syson() -> None:
    """Work with SysON projects and import namespaces."""


@syson.command("list")
@click.option("--syson-url", default=DEFAULT_SYSON_URL, show_default=True)
@click.option("--timeout", type=int, default=30, show_default=True)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def syson_list(ctx: click.Context, syson_url: str, timeout: int, dry_run: bool) -> None:
    """List SysON projects."""
    run_bridge(ctx, ["syson-list-projects", "--syson-url", syson_url, "--timeout", str(timeout)], dry_run)


@syson.command("create")
@click.argument("name")
@click.option("--template-id", default="sysmlv2-template", show_default=True)
@click.option("--library-id", "library_ids", multiple=True, help="SysON library ID to include. Repeatable.")
@click.option("--syson-url", default=DEFAULT_SYSON_URL, show_default=True)
@click.option("--timeout", type=int, default=30, show_default=True)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def syson_create(
    ctx: click.Context,
    name: str,
    template_id: str,
    library_ids: tuple[str, ...],
    syson_url: str,
    timeout: int,
    dry_run: bool,
) -> None:
    """Create a SysON project."""
    args = [
        "syson-create-project",
        name,
        "--template-id",
        template_id,
        "--syson-url",
        syson_url,
        "--timeout",
        str(timeout),
    ]
    if library_ids:
        args.append("--library-ids")
        args.extend(library_ids)
    run_bridge(ctx, args, dry_run)


@syson.command("roots")
@click.argument("project_id")
@click.option("--json-output", is_flag=True, help="Print raw JSON roots.")
@click.option("--syson-url", default=DEFAULT_SYSON_URL, show_default=True)
@click.option("--timeout", type=int, default=30, show_default=True)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def syson_roots(
    ctx: click.Context, project_id: str, json_output: bool, syson_url: str, timeout: int, dry_run: bool
) -> None:
    """List root namespace elements for a SysON project."""
    args = ["syson-roots", project_id, "--syson-url", syson_url, "--timeout", str(timeout)]
    if json_output:
        args.append("--json")
    run_bridge(ctx, args, dry_run)


@main.group()
def bridge() -> None:
    """Render and move snapshots between Flexo and SysON."""


@bridge.command("render")
@click.argument("input", type=click.Path(path_type=Path, exists=False))
@click.option("--output", type=click.Path(path_type=Path))
@click.option("--dry-run", is_flag=True)
@click.option(
    "--allow-repo-exports",
    is_flag=True,
    help="Suppress the warning when MBSE_MODEL_WORKSPACE is unset and writing to repo-local exports/.",
)
@click.pass_context
def bridge_render(
    ctx: click.Context, input: Path, output: Path | None, dry_run: bool, allow_repo_exports: bool
) -> None:
    """Render a Flexo export JSON file as SysML textual notation."""
    args = ["render-sysml", str(input)]
    if should_warn_repo_local_exports(output, allow_repo_exports):
        warn_repo_local_exports(default_output_dir())
    if output:
        args.extend(["--output", str(output)])
    run_bridge(ctx, args, dry_run)


@bridge.command("import")
@click.argument("input", type=click.Path(path_type=Path, exists=False))
@click.option("--project-id", required=True)
@click.option("--namespace-id", required=True)
@click.option("--editing-context-id")
@click.option("--syson-url", default=DEFAULT_SYSON_URL, show_default=True)
@click.option("--timeout", type=int, default=30, show_default=True)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def bridge_import(
    ctx: click.Context,
    input: Path,
    project_id: str,
    namespace_id: str,
    editing_context_id: str | None,
    syson_url: str,
    timeout: int,
    dry_run: bool,
) -> None:
    """Import a .sysml file into a SysON namespace."""
    args = [
        "syson-import-text",
        str(input),
        "--project-id",
        project_id,
        "--namespace-id",
        namespace_id,
        "--syson-url",
        syson_url,
        "--timeout",
        str(timeout),
    ]
    if editing_context_id:
        args.extend(["--editing-context-id", editing_context_id])
    run_bridge(ctx, args, dry_run)


@bridge.command("run")
@click.argument("flexo_project_id")
@click.option("--commit-id")
@click.option("--syson-project-id", required=True)
@click.option("--namespace-id", required=True)
@click.option("--editing-context-id")
@click.option("--output-dir", type=click.Path(path_type=Path))
@click.option("--run-log", type=click.Path(path_type=Path))
@click.option("--run-log-dir", type=click.Path(path_type=Path))
@click.option("--flexo-url", default=DEFAULT_FLEXO_URL, show_default=True)
@click.option("--syson-url", default=DEFAULT_SYSON_URL, show_default=True)
@click.option("--timeout", type=int, default=30, show_default=True)
@click.option("--dry-run", is_flag=True)
@click.option(
    "--allow-repo-exports",
    is_flag=True,
    help="Suppress the warning when MBSE_MODEL_WORKSPACE is unset and writing to repo-local exports/.",
)
@click.pass_context
def bridge_run(
    ctx: click.Context,
    flexo_project_id: str,
    commit_id: str | None,
    syson_project_id: str,
    namespace_id: str,
    editing_context_id: str | None,
    output_dir: Path | None,
    run_log: Path | None,
    run_log_dir: Path | None,
    flexo_url: str,
    syson_url: str,
    timeout: int,
    dry_run: bool,
    allow_repo_exports: bool,
) -> None:
    """Export from Flexo, render SysML text, and import into SysON."""
    if should_warn_repo_local_exports(output_dir, allow_repo_exports):
        warn_repo_local_exports(default_output_dir())
    args = [
        "flexo-to-syson",
        flexo_project_id,
        "--syson-project-id",
        syson_project_id,
        "--namespace-id",
        namespace_id,
        "--flexo-url",
        flexo_url,
        "--syson-url",
        syson_url,
        "--timeout",
        str(timeout),
    ]
    for option, value in (
        ("--commit-id", commit_id),
        ("--editing-context-id", editing_context_id),
        ("--output-dir", output_dir),
        ("--run-log", run_log),
        ("--run-log-dir", run_log_dir),
    ):
        if value:
            args.extend([option, str(value)])
    run_bridge(ctx, args, dry_run)


@main.group()
def workspace() -> None:
    """Create and inspect private model workspaces."""


@workspace.command("init")
@click.argument("path", type=click.Path(path_type=Path))
@click.option("--force", is_flag=True, help="Overwrite generated README.md and .gitignore files.")
@click.option("--git/--no-git", "git_init", default=True, help="Initialize a git repository if one is not present.")
def workspace_init(path: Path, force: bool, git_init: bool) -> None:
    """Initialize a private model workspace."""
    root = initialize_model_workspace(path, force, git_init)
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
@click.option("--fixture", type=click.Path(path_type=Path), help="Deployment fixture path.")
@click.option("--json-output", is_flag=True, help="Print a machine-readable JSON contract.")
@click.pass_context
def deployment_contract(ctx: click.Context, fixture: Path | None, json_output: bool) -> None:
    """Print the fixture-derived deployment runtime contract."""
    repo_root = require_repo_root(ctx)
    args = ["python3", "scripts/flexo_syson_bridge.py", "deployment-contract"]
    if fixture:
        args.extend(["--fixture", str(fixture)])
    if json_output:
        args.append("--json")
    run_command(args, repo_root)


@deployment.command("verify")
@click.option("--fixture", type=click.Path(path_type=Path), help="Deployment fixture path.")
@click.option(
    "--project-name",
    help="Inspect containers by Compose project and service labels instead of fixed container names.",
)
@click.option("--timeout", type=int, default=20, show_default=True)
@click.option("--json-output", is_flag=True, help="Print a machine-readable JSON report.")
@click.option("--output", type=click.Path(path_type=Path), help="Write the structured verification report as JSON.")
@click.pass_context
def deployment_verify(
    ctx: click.Context,
    fixture: Path | None,
    project_name: str | None,
    timeout: int,
    json_output: bool,
    output: Path | None,
) -> None:
    """Verify Docker runtime state against the deployment contract."""
    repo_root = require_repo_root(ctx)
    args = ["python3", "scripts/flexo_syson_bridge.py", "deployment-verify", "--timeout", str(timeout)]
    if fixture:
        args.extend(["--fixture", str(fixture)])
    if project_name:
        args.extend(["--project-name", project_name])
    if json_output:
        args.append("--json")
    if output:
        args.extend(["--output", str(output)])
    run_command(args, repo_root)


@deployment.command("isolated-smoke")
@click.option("--fixture", type=click.Path(path_type=Path), help="Deployment fixture path.")
@click.option("--project-name", help="Compose project name. Defaults to a generated unique name.")
@click.option(
    "--runtime-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    help="Directory for disposable bind-mounted data. Defaults under tmp/isolated-deployments/.",
)
@click.option("--timeout", type=int, default=120, show_default=True)
@click.option("--output", type=click.Path(path_type=Path), help="Write the structured verification report as JSON.")
@click.option("--keep", is_flag=True, help="Leave the isolated deployment running after verification.")
@click.option("--dry-run", is_flag=True, help="Print commands without starting containers.")
@click.pass_context
def deployment_isolated_smoke(
    ctx: click.Context,
    fixture: Path | None,
    project_name: str | None,
    runtime_dir: Path | None,
    timeout: int,
    output: Path | None,
    keep: bool,
    dry_run: bool,
) -> None:
    """Start and verify a disposable isolated deployment."""
    repo_root = require_repo_root(ctx)
    args = ["python3", "scripts/flexo_syson_bridge.py", "deployment-isolated-smoke", "--timeout", str(timeout)]
    if fixture:
        args.extend(["--fixture", str(fixture)])
    if project_name:
        args.extend(["--project-name", project_name])
    if runtime_dir:
        args.extend(["--runtime-dir", str(runtime_dir)])
    if output:
        args.extend(["--output", str(output)])
    if keep:
        args.append("--keep")
    if dry_run:
        args.append("--dry-run")
    run_command(args, repo_root)


if __name__ == "__main__":
    main()
