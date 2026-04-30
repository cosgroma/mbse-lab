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
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
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


def collect_commands(output: Path, cwd: Path, timeout: int, log_tail: int) -> None:
    commands = [
        ["git", "status", "--short"],
        ["git", "log", "--oneline", "--decorate", "-5"],
        ["docker", "ps", "--format", "json"],
        ["docker", "compose", "-f", "deploy/flexo-mms/docker-compose.yml", "ps"],
        ["docker", "compose", "-f", "deploy/syson/docker-compose.yml", "ps"],
        ["python3", "scripts/flexo_mms_env.py", "status", "--with-sysmlv2"],
        ["python3", "scripts/flexo_syson_bridge.py", "flexo-list-projects"],
        ["python3", "scripts/flexo_syson_bridge.py", "syson-list-projects"],
        ["docker", "compose", "-f", "deploy/flexo-mms/docker-compose.yml", "logs", "--tail", str(log_tail)],
        ["docker", "compose", "-f", "deploy/syson/docker-compose.yml", "logs", "--tail", str(log_tail), "app"],
    ]
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


def collect_http(output: Path, timeout: int) -> None:
    endpoints = {
        "flexo-projects.json": "http://localhost:18083/projects",
        "syson-rest-projects.json": "http://localhost:18090/api/rest/projects",
        "syson-root.html.json": "http://localhost:18090/",
        "syson-openapi.json": "http://localhost:18090/v3/api-docs/rest-apis",
    }
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


def cmd_collect(args: argparse.Namespace) -> None:
    cwd = Path.cwd()
    output = args.output
    recreate_output_dir(output)
    metadata = {
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "cwd": str(cwd),
        "timeout": args.timeout,
        "log_tail": args.log_tail,
    }
    write_json(output / "metadata.json", metadata)
    collect_commands(output, cwd, args.timeout, args.log_tail)
    collect_deployment_verification(output, cwd, args.timeout)
    collect_http(output, args.timeout)
    collect_files(output, cwd)
    print(f"Wrote diagnostics bundle: {output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--log-tail", type=int, default=DEFAULT_LOG_TAIL)
    return parser


def main() -> None:
    cmd_collect(build_parser().parse_args())


if __name__ == "__main__":
    main()
