#!/usr/bin/env python3
"""Collect a redacted diagnostics bundle for the local MBSE lab."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_OUTPUT = Path("diagnostics/latest")
DEFAULT_TIMEOUT = 10
DEFAULT_LOG_TAIL = 120
FLEXO_CONTAINERS = [
    "openldap-server",
    "quad-server",
    "minio-server",
    "auth-service",
    "store-service",
    "layer1-service",
]

REDACTION_PATTERNS = [
    re.compile(r"(?i)(password\s*[:=]\s*)([^\s\"']+)"),
    re.compile(r"(?i)(secret\s*[:=]\s*)([^\s\"']+)"),
    re.compile(r"(?i)(token\s*[:=]\s*)([^\s\"']+)"),
    re.compile(r"(?i)(authorization:\s*bearer\s+)([A-Za-z0-9._~+/=-]+)"),
    re.compile(r"(Bearer\s+)([A-Za-z0-9._~+/=-]+)"),
    re.compile(r"(JWT_SECRET=)(.+)"),
    re.compile(r"(AWS_SECRET_ACCESS_KEY=)(.+)"),
    re.compile(r"(FLEXO_MMS_LDAP_[A-Z0-9_]*PASSWORD=)(.+)"),
    re.compile(r"(FLEXO_MMS_MINIO_ROOT_PASSWORD=)(.+)"),
    re.compile(r"(SYSON_POSTGRES_PASSWORD=)(.+)"),
]


def redact(text: str) -> str:
    redacted = text
    for pattern in REDACTION_PATTERNS:
        redacted = pattern.sub(r"\1<redacted>", redacted)
    return redacted


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact(text), encoding="utf-8")


def write_json(path: Path, data: object) -> None:
    write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def run(command: list[str], cwd: Path, timeout: int) -> dict[str, object]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except FileNotFoundError as exc:
        return {"command": command, "returncode": None, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": f"timed out after {timeout}s\n{exc.stderr or ''}",
        }


def fetch(url: str, timeout: int) -> dict[str, object]:
    request = urllib.request.Request(url)
    request.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            parsed: object
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = body
            return {"url": url, "status": response.status, "body": parsed}
    except urllib.error.HTTPError as exc:
        return {
            "url": url,
            "status": exc.code,
            "body": exc.read().decode("utf-8", errors="replace"),
        }
    except urllib.error.URLError as exc:
        return {"url": url, "status": None, "body": str(exc)}


def recreate_output_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def command_to_filename(command: list[str]) -> str:
    normalized = "-".join(part.strip("-").replace("/", "_") for part in command)
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "-", normalized)
    return normalized[:140] + ".txt"


def diagnostic_commands(log_tail: int, public_safe: bool) -> list[list[str]]:
    common_commands = [
        ["git", "log", "--oneline", "--decorate", "-5"],
        ["docker", "ps", "--format", "json"],
        [
            "docker",
            "inspect",
            "--format",
            "{{.Name}} status={{.State.Status}} exit={{.State.ExitCode}} oom={{.State.OOMKilled}} "
            "error={{.State.Error}} started={{.State.StartedAt}} finished={{.State.FinishedAt}}",
            *FLEXO_CONTAINERS,
        ],
        ["docker", "compose", "-f", "deploy/flexo-mms/docker-compose.yml", "ps"],
        ["docker", "compose", "-f", "deploy/syson/docker-compose.yml", "ps"],
        ["python3", "scripts/flexo_mms_env.py", "status", "--with-sysmlv2"],
    ]
    if public_safe:
        return common_commands
    return [
        ["git", "status", "--short"],
        *common_commands,
        ["python3", "scripts/flexo_syson_bridge.py", "flexo-list-projects"],
        ["python3", "scripts/flexo_syson_bridge.py", "syson-list-projects"],
        ["docker", "compose", "-f", "deploy/flexo-mms/docker-compose.yml", "logs", "--tail", str(log_tail)],
        ["docker", "compose", "-f", "deploy/syson/docker-compose.yml", "logs", "--tail", str(log_tail), "app"],
    ]


def collect_commands(output: Path, cwd: Path, timeout: int, log_tail: int, public_safe: bool) -> None:
    commands = diagnostic_commands(log_tail, public_safe)
    summary = []
    for command in commands:
        result = run(command, cwd, timeout)
        summary.append(
            {
                "command": command,
                "returncode": result["returncode"],
                "file": f"commands/{command_to_filename(command)}",
            }
        )
        content = (
            f"$ {' '.join(command)}\n"
            f"returncode: {result['returncode']}\n\n"
            "## stdout\n"
            f"{result['stdout']}\n\n"
            "## stderr\n"
            f"{result['stderr']}\n"
        )
        write_text(output / "commands" / command_to_filename(command), content)
    if public_safe:
        summary.append(
            {
                "omitted": "public-safe mode omits git status, project lists, and service logs",
            }
        )
    write_json(output / "commands" / "index.json", summary)


def collect_deployment_verification(output: Path, cwd: Path, timeout: int) -> None:
    report_path = output / "deployment-verification.json"
    command = [
        "python3",
        "scripts/flexo_syson_bridge.py",
        "deployment-verify",
        "--json",
        "--output",
        str(report_path),
        "--timeout",
        str(timeout),
    ]
    result = run(command, cwd, timeout)
    command_file = f"commands/{command_to_filename(command)}"
    content = (
        f"$ {' '.join(command)}\n"
        f"returncode: {result['returncode']}\n\n"
        "## stdout\n"
        f"{result['stdout']}\n\n"
        "## stderr\n"
        f"{result['stderr']}\n"
    )
    write_text(output / command_file, content)
    command_index = output / "commands" / "index.json"
    if command_index.exists():
        summary = json.loads(command_index.read_text(encoding="utf-8"))
        summary.append(
            {
                "command": command,
                "returncode": result["returncode"],
                "file": command_file,
            }
        )
        write_json(command_index, summary)
    if not report_path.exists():
        write_json(
            report_path,
            {
                "status": "failed",
                "error": "deployment-verify did not write a report",
                "returncode": result["returncode"],
            },
        )


def diagnostic_http_endpoints(public_safe: bool) -> dict[str, str]:
    endpoints = {
        "syson-root.html.json": "http://localhost:18090/",
        "syson-openapi.json": "http://localhost:18090/v3/api-docs/rest-apis",
    }
    if public_safe:
        return endpoints
    return {
        "flexo-projects.json": "http://localhost:18083/projects",
        "syson-rest-projects.json": "http://localhost:18090/api/rest/projects",
        **endpoints,
    }


def collect_http(output: Path, timeout: int, public_safe: bool) -> None:
    endpoints = diagnostic_http_endpoints(public_safe)
    summary = {}
    for filename, url in endpoints.items():
        result = fetch(url, timeout)
        summary[filename] = {"url": url, "status": result["status"]}
        write_json(output / "http" / filename, result)
    write_json(output / "http" / "index.json", summary)


def collect_files(output: Path, cwd: Path) -> None:
    files = [
        ".gitignore",
        "Makefile",
        "deploy/flexo-mms/docker-compose.yml",
        "deploy/flexo-mms/.env.example",
        "deploy/syson/docker-compose.yml",
        "deploy/syson/.env.example",
    ]
    for relative in files:
        path = cwd / relative
        if path.exists():
            write_text(output / "files" / relative, path.read_text(encoding="utf-8"))


def read_json_if_exists(path: Path) -> object:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_manifest(output: Path) -> dict[str, object]:
    metadata = read_json_if_exists(output / "metadata.json") or {}
    command_index = read_json_if_exists(output / "commands" / "index.json") or []
    http_index = read_json_if_exists(output / "http" / "index.json") or {}
    deployment = read_json_if_exists(output / "deployment-verification.json") or {}
    deployment_summary = deployment.get("summary", {}) if isinstance(deployment, dict) else {}

    return {
        "metadata": metadata,
        "artifacts": {
            "metadata": "metadata.json",
            "humanIndex": "index.md",
            "commandIndex": "commands/index.json",
            "httpIndex": "http/index.json",
            "deploymentVerification": "deployment-verification.json",
            "files": "files/",
        },
        "commands": {
            "total": len(command_index),
            "failed": [
                item for item in command_index if isinstance(item, dict) and item.get("returncode") not in (0, None)
            ],
            "timedOutOrMissing": [
                item for item in command_index if isinstance(item, dict) and item.get("returncode") is None
            ],
        },
        "http": http_index,
        "deploymentVerification": {
            "status": deployment.get("status") if isinstance(deployment, dict) else None,
            "checkedAt": deployment.get("checkedAt") if isinstance(deployment, dict) else None,
            "summary": deployment_summary,
        },
    }


def render_manifest_markdown(manifest: dict[str, object]) -> str:
    metadata = manifest.get("metadata", {})
    commands = manifest.get("commands", {})
    deployment = manifest.get("deploymentVerification", {})
    deployment_summary = deployment.get("summary", {}) if isinstance(deployment, dict) else {}
    http = manifest.get("http", {})
    artifacts = manifest.get("artifacts", {})

    lines = [
        "# Diagnostics Bundle",
        "",
        f"- Created: {metadata.get('created_at', 'unknown') if isinstance(metadata, dict) else 'unknown'}",
        f"- Working directory: `{metadata.get('cwd', 'unknown') if isinstance(metadata, dict) else 'unknown'}`",
        ("- Public-safe mode: " f"`{metadata.get('public_safe', False) if isinstance(metadata, dict) else False}`"),
        f"- Deployment verification: `{deployment.get('status', 'unknown') if isinstance(deployment, dict) else 'unknown'}`",
        (
            "- Deployment checks: "
            f"{deployment_summary.get('passedChecks', 0)} passed, "
            f"{deployment_summary.get('failedChecks', 0)} failed, "
            f"{deployment_summary.get('checks', 0)} total"
        ),
        (
            "- Deployment services: "
            f"{deployment_summary.get('passedServices', 0)} passed, "
            f"{deployment_summary.get('failedServices', 0)} failed, "
            f"{deployment_summary.get('services', 0)} total"
        ),
        (
            "- Commands captured: "
            f"{commands.get('total', 0) if isinstance(commands, dict) else 0} total, "
            f"{len(commands.get('failed', [])) if isinstance(commands, dict) else 0} failed, "
            f"{len(commands.get('timedOutOrMissing', [])) if isinstance(commands, dict) else 0} timed out or missing"
        ),
        "",
        "## Start Here",
        "",
    ]
    if isinstance(artifacts, dict):
        lines.extend(
            [
                f"- Deployment evidence: `{artifacts.get('deploymentVerification')}`",
                f"- Command transcript index: `{artifacts.get('commandIndex')}`",
                f"- HTTP probe index: `{artifacts.get('httpIndex')}`",
                f"- Captured config files: `{artifacts.get('files')}`",
            ]
        )
    lines.extend(["", "## HTTP Probes", ""])
    if isinstance(http, dict):
        for filename, result in sorted(http.items()):
            status = result.get("status") if isinstance(result, dict) else "unknown"
            url = result.get("url") if isinstance(result, dict) else ""
            lines.append(f"- `{filename}`: status `{status}` from {url}")
    lines.append("")
    return "\n".join(lines)


def collect_manifest(output: Path) -> None:
    manifest = build_manifest(output)
    write_json(output / "manifest.json", manifest)
    write_text(output / "index.md", render_manifest_markdown(manifest))


def cmd_collect(args: argparse.Namespace) -> None:
    cwd = Path.cwd()
    output = args.output
    recreate_output_dir(output)
    metadata = {
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "cwd": str(cwd),
        "timeout": args.timeout,
        "log_tail": args.log_tail,
        "public_safe": args.public_safe,
    }
    write_json(output / "metadata.json", metadata)
    collect_commands(output, cwd, args.timeout, args.log_tail, args.public_safe)
    collect_deployment_verification(output, cwd, args.timeout)
    collect_http(output, args.timeout, args.public_safe)
    collect_files(output, cwd)
    collect_manifest(output)
    suffix = " (public-safe)" if args.public_safe else ""
    print(f"Wrote diagnostics bundle{suffix}: {output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--log-tail", type=int, default=DEFAULT_LOG_TAIL)
    parser.add_argument(
        "--public-safe",
        action="store_true",
        help="Omit project lists and recent service logs from the diagnostics bundle.",
    )
    return parser


def main() -> None:
    cmd_collect(build_parser().parse_args())


if __name__ == "__main__":
    main()
