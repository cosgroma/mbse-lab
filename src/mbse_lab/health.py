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
