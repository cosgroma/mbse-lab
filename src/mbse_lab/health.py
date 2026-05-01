"""Health and prerequisite checks for the MBSE lab CLI."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import click

from mbse_lab.constants import (
    DEFAULT_FLEXO_URL,
    DEFAULT_SYSON_URL,
    FLEXO_CONTAINERS,
    REQUIRED_MARKERS,
    SYSON_CONTAINERS,
)
from mbse_lab.http import fetch_status
from mbse_lab.shell import run_capture_result


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


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def has_persisted_data(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        return any(path.iterdir())
    except PermissionError:
        return True


def docker_container_report(name: str, repo_root: Path) -> dict[str, object]:
    result = run_capture_result(["docker", "inspect", name], repo_root)
    if result.returncode != 0:
        return {
            "name": name,
            "exists": False,
            "running": False,
            "status": "missing",
            "health": "none",
            "ports": {},
        }
    data = json.loads(result.stdout)
    container = data[0] if data else {}
    state = container.get("State", {})
    ports: dict[str, list[str]] = {}
    for container_port, bindings in sorted((container.get("NetworkSettings", {}).get("Ports") or {}).items()):
        ports[container_port] = [
            f"{binding.get('HostIp', '')}:{binding.get('HostPort', '')}".strip(":") for binding in (bindings or [])
        ]
    return {
        "name": name,
        "exists": True,
        "running": bool(state.get("Running")),
        "status": state.get("Status", "unknown"),
        "health": state.get("Health", {}).get("Status", "none"),
        "ports": ports,
    }


def syson_database_credential_report(repo_root: Path) -> dict[str, object]:
    env_path = repo_root / "deploy/syson/.env"
    data_path = repo_root / "deploy/syson/data/postgres"
    env_values = read_env_file(env_path)
    database = env_values.get("SYSON_POSTGRES_DB", "postgres")
    username = env_values.get("SYSON_POSTGRES_USER", "username")
    password = env_values.get("SYSON_POSTGRES_PASSWORD")
    image = env_values.get("SYSON_POSTGRES_IMAGE", "postgres:15")
    data_exists = has_persisted_data(data_path)

    report: dict[str, object] = {
        "ok": True,
        "status": "skipped",
        "env_path": "deploy/syson/.env",
        "data_path": "deploy/syson/data/postgres",
        "env_exists": env_path.exists(),
        "data_exists": data_exists,
        "database_container_running": False,
        "detail": "SysON database credential check skipped.",
    }

    if not env_path.exists():
        report.update({"status": "missing-env", "detail": "deploy/syson/.env does not exist."})
        return report
    if not data_exists:
        report.update({"status": "no-data", "detail": "No persisted SysON Postgres data found."})
        return report
    if not password:
        report.update(
            {
                "ok": False,
                "status": "missing-password",
                "detail": "SYSON_POSTGRES_PASSWORD is missing from deploy/syson/.env.",
            }
        )
        return report

    database_container = docker_container_report("syson-database", repo_root)
    container_running = bool(database_container.get("running"))
    report["database_container_running"] = container_running
    if not container_running:
        report.update({"status": "database-stopped", "detail": "syson-database is not running."})
        return report

    result = run_capture_result(
        [
            "docker",
            "run",
            "--rm",
            "--pull=never",
            "--network",
            "syson-test-network",
            "-e",
            f"PGPASSWORD={password}",
            image,
            "psql",
            "-h",
            "database",
            "-U",
            username,
            "-d",
            database,
            "-c",
            "select 1;",
        ],
        repo_root,
    )
    if result.returncode == 0:
        report.update(
            {
                "ok": True,
                "status": "passed",
                "detail": "deploy/syson/.env password works with the running persisted SysON database.",
            }
        )
        return report

    stderr = result.stderr.strip()
    if "password authentication failed" in stderr:
        detail = "deploy/syson/.env password does not match the running persisted SysON database."
    elif "No such image" in stderr or "pull access denied" in stderr:
        detail = f"Could not run postgres client image without pulling: {image}."
    else:
        detail = "Could not verify SysON database credentials."
    report.update({"ok": False, "status": "failed", "detail": detail})
    return report


def service_report(repo_root: Path) -> dict[str, object]:
    containers = [docker_container_report(name, repo_root) for name in (*FLEXO_CONTAINERS, *SYSON_CONTAINERS)]
    http_checks = {
        "flexo_projects": {
            "url": f"{DEFAULT_FLEXO_URL}/projects",
            "status": fetch_status(f"{DEFAULT_FLEXO_URL}/projects"),
        },
        "syson_web": {
            "url": f"{DEFAULT_SYSON_URL}/",
            "status": fetch_status(f"{DEFAULT_SYSON_URL}/"),
        },
    }
    all_containers_running = all(bool(container["running"]) for container in containers)
    unhealthy = [container for container in containers if container["health"] == "unhealthy"]
    return {
        "status": "passed" if all_containers_running and not unhealthy else "warning",
        "containers": containers,
        "http": http_checks,
    }


def doctor_report(repo_root: Path | None) -> dict[str, object]:
    docker_ok = command_exists("docker")
    compose_ok = bool(
        docker_ok and subprocess.run(["docker", "compose", "version"], capture_output=True, text=True).returncode == 0
    )
    markers = []
    if repo_root:
        markers = [
            {
                "path": marker.as_posix(),
                "exists": (repo_root / marker).exists(),
            }
            for marker in REQUIRED_MARKERS
        ]
    workspace = os.environ.get("MBSE_MODEL_WORKSPACE")
    workspace_path = Path(workspace).expanduser() if workspace else None
    checks = {
        "python": {"ok": command_exists("python3"), "version": sys.version.split()[0]},
        "docker": {"ok": docker_ok},
        "docker_compose": {"ok": compose_ok},
        "repo_root": {"ok": repo_root is not None, "path": str(repo_root) if repo_root else None},
        "markers": markers,
        "flexo_env": {"ok": bool(repo_root and (repo_root / "deploy/flexo-mms/.env").exists())},
        "syson_env": {"ok": bool(repo_root and (repo_root / "deploy/syson/.env").exists())},
        "model_workspace": {
            "ok": bool(workspace_path and workspace_path.exists()),
            "path": str(workspace_path) if workspace_path else None,
        },
        "ports": {
            "flexo_sysmlv2": {"ok": tcp_connects("localhost", 18083), "host": "localhost", "port": 18083},
            "syson_web": {"ok": tcp_connects("localhost", 18090), "host": "localhost", "port": 18090},
        },
        "http": {
            "flexo_projects": {"status": fetch_status(f"{DEFAULT_FLEXO_URL}/projects")},
            "syson_web": {"status": fetch_status(f"{DEFAULT_SYSON_URL}/")},
        },
    }
    if repo_root:
        checks["syson_database_credentials"] = syson_database_credential_report(repo_root)
    required_ok = (
        checks["python"]["ok"]
        and checks["docker"]["ok"]
        and checks["docker_compose"]["ok"]
        and checks["repo_root"]["ok"]
        and all(marker["exists"] for marker in markers)
    )
    return {
        "status": "passed" if required_ok else "failed",
        "checks": checks,
    }
