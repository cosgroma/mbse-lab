"""Command-line interface for the SysML v2 local lab."""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path

import click

from mbse_lab import __version__

DEFAULT_FLEXO_URL = "http://localhost:18083"
DEFAULT_SYSON_URL = "http://localhost:18090"

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


def run_command(command: list[str], cwd: Path, dry_run: bool = False) -> None:
    if dry_run:
        click.echo(f"dry-run: {' '.join(command)}")
        return
    completed = subprocess.run(command, cwd=cwd)
    if completed.returncode != 0:
        raise click.ClickException(f"command failed with exit code {completed.returncode}: {' '.join(command)}")


def trim_url(url: str) -> str:
    return url.rstrip("/")


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


def request_json(
    method: str,
    url: str,
    payload: object | None = None,
    timeout: int = 30,
    expected: set[int] | None = None,
) -> object:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, method=method)
    request.add_header("Accept", "application/json")
    if body is not None:
        request.add_header("Content-Type", "application/json")
    expected_status = expected or {200}
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            if response.status not in expected_status:
                raise click.ClickException(f"{method} {url} returned {response.status}: {raw}")
            if not raw.strip():
                return {}
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise click.ClickException(f"{method} {url} returned {exc.code}: {raw}") from exc
    except urllib.error.URLError as exc:
        raise click.ClickException(f"{method} {url} failed: {exc}") from exc


def graphql(
    syson_url: str, query: str, variables: dict[str, object] | None = None, timeout: int = 30
) -> dict[str, object]:
    response = request_json(
        "POST",
        f"{trim_url(syson_url)}/api/graphql",
        {"query": query, "variables": variables or {}},
        timeout=timeout,
    )
    if not isinstance(response, dict):
        raise click.ClickException("SysON GraphQL returned a non-object response")
    if response.get("errors"):
        raise click.ClickException(json.dumps(response["errors"], indent=2))
    return response


def create_flexo_project(flexo_url: str, name: str, timeout: int) -> dict[str, object]:
    project = request_json(
        "POST",
        f"{trim_url(flexo_url)}/projects",
        {
            "@type": "Project",
            "name": name,
            "description": "Created by mbse-lab first-model",
        },
        timeout=timeout,
        expected={200, 201},
    )
    if not isinstance(project, dict):
        raise click.ClickException("Flexo project creation returned a non-object response")
    return project


def commit_flexo_package(
    flexo_url: str, project_id: str, package_id: str, package_name: str, timeout: int
) -> dict[str, object]:
    commit = request_json(
        "POST",
        f"{trim_url(flexo_url)}/projects/{urllib.parse.quote(project_id)}/commits",
        {
            "@type": "Commit",
            "description": "Create first package from mbse-lab",
            "change": [
                {
                    "@type": "DataVersion",
                    "identity": None,
                    "payload": {
                        "@id": package_id,
                        "@type": "Package",
                        "declaredName": package_name,
                    },
                }
            ],
        },
        timeout=timeout,
        expected={200, 201},
    )
    if not isinstance(commit, dict):
        raise click.ClickException("Flexo commit returned a non-object response")
    return commit


def create_syson_project(syson_url: str, name: str, timeout: int) -> dict[str, object]:
    mutation = """
    mutation CreateProject($input: CreateProjectInput!) {
      createProject(input: $input) {
        __typename
        ... on CreateProjectSuccessPayload {
          project { id name currentEditingContext { id } }
        }
        ... on ErrorPayload { message }
      }
    }
    """
    response = graphql(
        syson_url,
        mutation,
        {
            "input": {
                "id": str(uuid.uuid4()),
                "name": name,
                "templateId": "sysmlv2-template",
                "libraryIds": [],
            }
        },
        timeout=timeout,
    )
    data = response["data"]
    if not isinstance(data, dict):
        raise click.ClickException("SysON GraphQL response missing data object")
    result = data["createProject"]
    if not isinstance(result, dict):
        raise click.ClickException("SysON createProject response was not an object")
    if result["__typename"] == "ErrorPayload":
        raise click.ClickException(str(result["message"]))
    project = result["project"]
    if not isinstance(project, dict):
        raise click.ClickException("SysON project response was not an object")
    return project


def syson_latest_commit_id(syson_url: str, project_id: str, timeout: int) -> str:
    commits = request_json(
        "GET",
        f"{trim_url(syson_url)}/api/rest/projects/{urllib.parse.quote(project_id)}/commits",
        timeout=timeout,
    )
    if not isinstance(commits, list) or not commits:
        raise click.ClickException(f"SysON project has no REST commits: {project_id}")
    latest_commit = commits[-1]
    if not isinstance(latest_commit, dict) or "@id" not in latest_commit:
        raise click.ClickException(f"SysON latest commit was malformed for project {project_id}")
    return str(latest_commit["@id"])


def syson_root_package_id(syson_url: str, project_id: str, commit_id: str, timeout: int) -> str:
    roots = request_json(
        "GET",
        (
            f"{trim_url(syson_url)}/api/rest/projects/{urllib.parse.quote(project_id)}"
            f"/commits/{urllib.parse.quote(commit_id)}/roots"
        ),
        timeout=timeout,
    )
    if not isinstance(roots, list):
        raise click.ClickException(f"SysON roots response was not a list for project {project_id}")
    for root in roots:
        if isinstance(root, dict) and root.get("@type") == "Package":
            return str(root["@id"])
    raise click.ClickException(f"no root Package found in SysON project {project_id}")


def import_sysml_text(
    syson_url: str,
    namespace_id: str,
    editing_context_id: str,
    textual_content: str,
    timeout: int,
) -> dict[str, object]:
    mutation = """
    mutation InsertTextualSysMLv2($input: InsertTextualSysMLv2Input!) {
      insertTextualSysMLv2(input: $input) {
        __typename
        ... on SuccessPayload { id }
        ... on ErrorPayload { message }
      }
    }
    """
    response = graphql(
        syson_url,
        mutation,
        {
            "input": {
                "id": str(uuid.uuid4()),
                "editingContextId": editing_context_id,
                "objectId": namespace_id,
                "textualContent": textual_content,
            }
        },
        timeout=timeout,
    )
    data = response["data"]
    if not isinstance(data, dict):
        raise click.ClickException("SysON GraphQL response missing data object")
    result = data["insertTextualSysMLv2"]
    if not isinstance(result, dict):
        raise click.ClickException("SysON import response was not an object")
    if result["__typename"] == "ErrorPayload":
        raise click.ClickException(str(result["message"]))
    return result


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
    shutil.copyfile(example_path, env_path)
    click.echo(f"Created SysON env: {env_path.relative_to(repo_root)}")


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


def print_service_urls() -> None:
    click.echo("")
    click.echo("Service URLs:")
    click.echo("  Flexo Layer1 API:   http://localhost:18080")
    click.echo("  Flexo SysML v2 API: http://localhost:18083")
    click.echo("  SysON Web UI:       http://localhost:18090")
    click.echo("  SysON GraphQL API:  http://localhost:18090/api/graphql")


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
) -> None:
    """Create a tiny Flexo model and import it into a SysON review project."""
    repo_root = require_repo_root(ctx)
    resolved_package_name = package_name or name
    resolved_syson_project_name = syson_project_name or f"{name} Review"
    resolved_output_dir = (output_dir or default_output_dir()).expanduser()
    package_identifier = sanitize_identifier(resolved_package_name)

    if dry_run:
        click.echo(f"dry-run: create Flexo project `{name}` at {flexo_url}")
        click.echo(f"dry-run: commit Package `{resolved_package_name}`")
        click.echo(f"dry-run: export Flexo JSON to {resolved_output_dir / 'flexo' / '<flexo-project-id>.json'}")
        click.echo(f"dry-run: render SysML to {resolved_output_dir / 'sysml' / '<flexo-project-id>.sysml'}")
        click.echo(f"dry-run: create SysON project `{resolved_syson_project_name}` at {syson_url}")
        click.echo(f"dry-run: import package `{package_identifier}` into the SysON root package")
        return

    package_id = str(uuid.uuid4())
    flexo_project = create_flexo_project(flexo_url, name, timeout)
    flexo_project_id = str(flexo_project["@id"])
    flexo_commit = commit_flexo_package(flexo_url, flexo_project_id, package_id, resolved_package_name, timeout)
    flexo_commit_id = str(flexo_commit["@id"])

    export_path = resolved_output_dir / "flexo" / f"{flexo_project_id}.json"
    sysml_path = resolved_output_dir / "sysml" / f"{flexo_project_id}.sysml"
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

    syson_project = create_syson_project(syson_url, resolved_syson_project_name, timeout)
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

    summary = {
        "flexo_project_id": flexo_project_id,
        "flexo_commit_id": flexo_commit_id,
        "package_id": package_id,
        "package_name": resolved_package_name,
        "export_path": str(export_path),
        "sysml_path": str(sysml_path),
        "syson_project_id": syson_project_id,
        "syson_project_name": resolved_syson_project_name,
        "syson_commit_id": syson_commit_id,
        "namespace_id": namespace_id,
        "editing_context_id": editing_context_id,
        "import_result": import_result,
        "syson_url": syson_url,
    }
    if json_output:
        click.echo(json.dumps(summary, indent=2, sort_keys=True))
        return

    click.echo("Created first SysML v2 model.")
    click.echo(f"  Flexo project: {flexo_project_id}")
    click.echo(f"  Flexo commit:  {flexo_commit_id}")
    click.echo(f"  Package:       {resolved_package_name} ({package_id})")
    click.echo(f"  Flexo export:  {export_path}")
    click.echo(f"  SysML text:    {sysml_path}")
    click.echo(f"  SysON project: {syson_project_id}")
    click.echo(f"  SysON root:    {namespace_id}")
    click.echo(f"  Open SysON:    {trim_url(syson_url)}")


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
