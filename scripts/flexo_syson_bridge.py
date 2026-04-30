#!/usr/bin/env python3
"""Move a conservative SysML v2 snapshot from Flexo into SysON.

The bridge intentionally starts with the lowest-risk exchange format:
Flexo SysML v2 REST JSON -> SysML v2 textual notation -> SysON GraphQL import.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any


DEFAULT_FLEXO_URL = "http://localhost:18083"
DEFAULT_LAYER1_URL = "http://localhost:18080"
DEFAULT_SYSON_URL = "http://localhost:18090"
DEFAULT_FLEXO_ENV_DIR = Path("deploy/flexo-mms")
DEFAULT_OUTPUT_DIR = Path("exports")
DEFAULT_RUN_DIR = Path("runs")
DEFAULT_DEPLOYMENT_FIXTURE = Path("evals/fixtures/container-deployment-basic.json")

RENDERABLE_TYPES = {
    "Package",
    "PartDefinition",
    "PartUsage",
    "AttributeUsage",
    "PortUsage",
    "RequirementDefinition",
    "RequirementUsage",
    "ConnectionDefinition",
    "ConnectionUsage",
    "InterfaceDefinition",
    "InterfaceUsage",
    "ActionDefinition",
    "ActionUsage",
    "ItemDefinition",
    "ItemUsage",
}


def fail(message: str, exit_code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def info(message: str) -> None:
    print(message)


def trim_url(url: str) -> str:
    return url.rstrip("/")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def run_log_path(run_dir: Path, workflow: str, run_id: str) -> Path:
    return run_dir / workflow / f"{run_id}.json"


def write_run_log(path: Path, record: dict[str, Any]) -> None:
    write_json(path, record)


def add_step(
    record: dict[str, Any],
    name: str,
    status: str,
    started_at: str,
    duration_seconds: float,
    details: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    step: dict[str, Any] = {
        "name": name,
        "status": status,
        "started_at": started_at,
        "duration_seconds": round(duration_seconds, 6),
    }
    if details:
        step["details"] = details
    if error:
        step["error"] = error
    record.setdefault("steps", []).append(step)


def request(
    method: str,
    url: str,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> tuple[int, bytes, dict[str, str]]:
    req = urllib.request.Request(url, data=body, method=method)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, response.read(), dict(response.headers)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), dict(exc.headers)
    except urllib.error.URLError as exc:
        fail(f"could not reach {url}: {exc}")


def request_json(
    method: str,
    url: str,
    payload: Any | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    expected: set[int] | None = None,
) -> Any:
    body = None
    merged_headers = dict(headers or {})
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        merged_headers.setdefault("Content-Type", "application/json")
    status, raw, _ = request(method, url, body=body, headers=merged_headers, timeout=timeout)
    if expected is None:
        expected = {200}
    if status not in expected:
        text = raw.decode("utf-8", errors="replace")
        fail(f"{method} {url} returned HTTP {status}: {text}")
    if not raw:
        return None
    return json.loads(raw.decode("utf-8"))


def graphql(url: str, query: str, variables: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    response = request_json(
        "POST",
        f"{trim_url(url)}/api/graphql",
        {"query": query, "variables": variables or {}},
        timeout=timeout,
    )
    if response.get("errors"):
        fail(json.dumps(response["errors"], indent=2))
    return response


def read_flexo_service_token(env_dir: Path) -> str | None:
    env_path = env_dir / "env" / "flexo-sysmlv2.env"
    if not env_path.exists():
        return None
    pattern = re.compile(r'^FLEXO_AUTH="?Bearer\s+(.+?)"?$')
    for line in env_path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if match:
            return match.group(1)
    return None


def cmd_init_flexo_org(args: argparse.Namespace) -> None:
    token = args.token or read_flexo_service_token(args.env_dir)
    if not token:
        fail("no token provided and no FLEXO_AUTH token found in deploy/flexo-mms/env/flexo-sysmlv2.env")

    body = (
        "@prefix dct: <http://purl.org/dc/terms/> .\n"
        f'<> dct:title "{args.title}" .\n'
    ).encode("utf-8")
    status, raw, _ = request(
        "PUT",
        f"{trim_url(args.layer1_url)}/orgs/{urllib.parse.quote(args.org_id)}",
        body=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "text/turtle",
        },
        timeout=args.timeout,
    )
    if status not in {200, 201, 204}:
        fail(raw.decode("utf-8", errors="replace"))
    info(f"Initialized Flexo org `{args.org_id}` via Layer1 ({status}).")


def cmd_flexo_list_projects(args: argparse.Namespace) -> None:
    projects = request_json("GET", f"{trim_url(args.flexo_url)}/projects", timeout=args.timeout)
    if args.json:
        print(json.dumps(projects, indent=2))
        return
    if not projects:
        info("No Flexo SysML v2 projects found.")
        return
    for project in projects:
        print(f"{project.get('@id')}  {project.get('name')}")


def cmd_flexo_create_project(args: argparse.Namespace) -> None:
    payload = {"@type": "Project", "name": args.name}
    if args.description:
        payload["description"] = args.description
    project = request_json(
        "POST",
        f"{trim_url(args.flexo_url)}/projects",
        payload,
        timeout=args.timeout,
        expected={200, 201},
    )
    print(json.dumps(project, indent=2))


def commit_id_from_branch(branch: dict[str, Any]) -> str | None:
    for key in ("head", "referencedCommit"):
        value = branch.get(key)
        if isinstance(value, dict) and value.get("@id"):
            return value["@id"]
    return None


def select_commit_id(flexo_url: str, project: dict[str, Any], explicit_commit_id: str | None, timeout: int) -> str:
    if explicit_commit_id:
        return explicit_commit_id

    project_id = project["@id"]
    branches = request_json("GET", f"{flexo_url}/projects/{project_id}/branches", timeout=timeout)
    default_branch_id = (project.get("defaultBranch") or {}).get("@id")
    for branch in branches:
        if branch.get("@id") == default_branch_id:
            commit_id = commit_id_from_branch(branch)
            if commit_id:
                return commit_id
    for branch in branches:
        commit_id = commit_id_from_branch(branch)
        if commit_id:
            return commit_id

    commits = request_json("GET", f"{flexo_url}/projects/{project_id}/commits", timeout=timeout)
    if commits:
        return commits[-1]["@id"]
    fail(f"could not determine a commit for Flexo project {project_id}")


def export_flexo_project(flexo_url: str, project_id: str, commit_id: str | None, timeout: int) -> dict[str, Any]:
    flexo_url = trim_url(flexo_url)
    project = request_json("GET", f"{flexo_url}/projects/{project_id}", timeout=timeout)
    branches = request_json("GET", f"{flexo_url}/projects/{project_id}/branches", timeout=timeout)
    selected_commit_id = select_commit_id(flexo_url, project, commit_id, timeout)
    commit = request_json("GET", f"{flexo_url}/projects/{project_id}/commits/{selected_commit_id}", timeout=timeout)
    roots = request_json(
        "GET",
        f"{flexo_url}/projects/{project_id}/commits/{selected_commit_id}/roots",
        timeout=timeout,
    )
    elements = request_json(
        "GET",
        f"{flexo_url}/projects/{project_id}/commits/{selected_commit_id}/elements",
        timeout=timeout,
    )
    return {
        "source": "flexo-sysmlv2",
        "project": project,
        "branches": branches,
        "commit": commit,
        "roots": roots,
        "elements": elements,
    }


def cmd_flexo_export(args: argparse.Namespace) -> None:
    snapshot = export_flexo_project(args.flexo_url, args.project_id, args.commit_id, args.timeout)
    output = args.output
    if output is None:
        output = DEFAULT_OUTPUT_DIR / "flexo" / f"{args.project_id}.json"
    write_json(output, snapshot)
    info(f"Wrote Flexo export: {output}")


def ref_id(value: Any) -> str | None:
    if isinstance(value, dict):
        return value.get("@id")
    return None


def ref_ids(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    ids: list[str] = []
    for value in values:
        item_id = ref_id(value)
        if item_id:
            ids.append(item_id)
    return ids


def element_name(element: dict[str, Any]) -> str:
    name = (
        element.get("declaredName")
        or element.get("name")
        or element.get("memberName")
        or element.get("@id")
        or "Unnamed"
    )
    return sanitize_identifier(str(name))


def sanitize_identifier(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]", "_", value.strip())
    if not value:
        return "Unnamed"
    if value[0].isdigit():
        value = f"_{value}"
    return value


def child_ids(element: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for key in (
        "ownedElement",
        "ownedMember",
        "ownedMemberElement",
        "ownedRelatedElement",
        "nestedPart",
        "nestedAttribute",
        "nestedPort",
        "nestedRequirement",
        "nestedConnection",
        "nestedUsage",
    ):
        value = element.get(key)
        if isinstance(value, dict):
            item_id = ref_id(value)
            if item_id:
                ids.append(item_id)
        else:
            ids.extend(ref_ids(value))
    return list(dict.fromkeys(ids))


def render_element(
    element: dict[str, Any],
    elements_by_id: dict[str, dict[str, Any]],
    depth: int = 0,
    seen: set[str] | None = None,
) -> list[str]:
    seen = set(seen or set())
    element_id = element.get("@id")
    if element_id:
        if element_id in seen:
            return []
        seen.add(element_id)

    element_type = element.get("@type", "Element")
    if element_type not in RENDERABLE_TYPES:
        return []

    indent = "  " * depth
    name = element_name(element)
    rendered_children: list[str] = []
    for child_id in child_ids(element):
        child = elements_by_id.get(child_id)
        if child:
            rendered_children.extend(render_element(child, elements_by_id, depth + 1, seen))

    keyword = {
        "Package": "package",
        "PartDefinition": "part def",
        "PartUsage": "part",
        "AttributeUsage": "attribute",
        "PortUsage": "port",
        "RequirementDefinition": "requirement def",
        "RequirementUsage": "requirement",
        "ConnectionDefinition": "connection def",
        "ConnectionUsage": "connection",
        "InterfaceDefinition": "interface def",
        "InterfaceUsage": "interface",
        "ActionDefinition": "action def",
        "ActionUsage": "action",
        "ItemDefinition": "item def",
        "ItemUsage": "item",
    }.get(element_type, "element")

    if rendered_children and element_type in {"Package", "PartDefinition", "RequirementDefinition"}:
        return [f"{indent}{keyword} {name} {{", *rendered_children, f"{indent}}}"]
    return [f"{indent}{keyword} {name};"]


def render_snapshot(snapshot: dict[str, Any]) -> str:
    elements = snapshot.get("elements") or []
    roots = snapshot.get("roots") or []
    elements_by_id = {
        element["@id"]: element
        for element in elements
        if isinstance(element, dict) and element.get("@id")
    }
    root_elements = [
        elements_by_id.get(root.get("@id"), root)
        for root in roots
        if isinstance(root, dict)
    ]
    if not root_elements:
        root_elements = [
            element
            for element in elements
            if isinstance(element, dict) and element.get("@type") in RENDERABLE_TYPES
        ]

    lines = [
        "// Generated from a Flexo SysML v2 REST export.",
        f"// Project: {snapshot.get('project', {}).get('name', 'unknown')}",
        f"// Commit: {snapshot.get('commit', {}).get('@id', 'unknown')}",
        "",
    ]
    rendered: list[str] = []
    for root in root_elements:
        rendered.extend(render_element(root, elements_by_id))
    if not rendered:
        rendered.append("// No supported renderable SysML elements were found in this snapshot.")
    return "\n".join(lines + rendered) + "\n"


def deployment_contract_from_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    elements = snapshot.get("elements") or []
    stack_by_child: dict[str, dict[str, Any]] = {}
    for element in elements:
        if not isinstance(element, dict) or not element.get("stackName"):
            continue
        for child_id in child_ids(element):
            stack_by_child[child_id] = element

    services: list[dict[str, Any]] = []
    for element in elements:
        if not isinstance(element, dict):
            continue
        container_name = element.get("containerName")
        if element.get("@type") != "PartUsage" or not container_name:
            continue
        service = {
            "id": element.get("@id"),
            "declaredName": element.get("declaredName"),
            "stackName": stack_by_child.get(element.get("@id"), {}).get("stackName"),
            "serviceName": element.get("serviceName"),
            "containerName": container_name,
            "ports": element.get("ports", []),
            "mounts": element.get("mounts", []),
        }
        services.append(service)

    services.sort(key=lambda service: str(service["containerName"]))
    return {
        "project": snapshot.get("project", {}),
        "commit": snapshot.get("commit", {}),
        "serviceCount": len(services),
        "services": services,
    }


def format_deployment_contract_table(contract: dict[str, Any]) -> str:
    rows = [
        [
            "CONTAINER",
            "SERVICE",
            "STACK",
            "PORTS",
            "MOUNTS",
        ]
    ]
    for service in contract["services"]:
        rows.append(
            [
                str(service.get("containerName") or ""),
                str(service.get("serviceName") or ""),
                str(service.get("stackName") or ""),
                format_contract_ports(service.get("ports", [])),
                format_contract_mounts(service.get("mounts", [])),
            ]
        )

    widths = [max(len(row[index]) for row in rows) for index in range(len(rows[0]))]
    lines = []
    for index, row in enumerate(rows):
        lines.append("  ".join(value.ljust(widths[column]) for column, value in enumerate(row)).rstrip())
        if index == 0:
            lines.append("  ".join("-" * width for width in widths).rstrip())
    return "\n".join(lines)


def format_contract_ports(ports: list[dict[str, Any]]) -> str:
    formatted = []
    for port in ports:
        protocol = port.get("protocol", "tcp")
        host = f"${{{port['hostPortEnv']}:-{port['defaultHostPort']}}}"
        formatted.append(f"{host}->{port['containerPort']}/{protocol}")
    return ", ".join(formatted)


def format_contract_mounts(mounts: list[dict[str, Any]]) -> str:
    return ", ".join(f"{mount['hostPath']}->{mount['containerPath']}" for mount in mounts)


def cmd_deployment_contract(args: argparse.Namespace) -> None:
    contract = deployment_contract_from_snapshot(read_json(args.fixture))
    if not contract["services"]:
        fail(f"no container services found in deployment fixture: {args.fixture}")
    if args.json:
        print(json.dumps(contract, indent=2, sort_keys=True))
        return
    print(format_deployment_contract_table(contract))


def read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def load_deployment_env(root: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    for path in (
        root / "deploy" / "flexo-mms" / ".env.example",
        root / "deploy" / "flexo-mms" / ".env",
        root / "deploy" / "syson" / ".env.example",
        root / "deploy" / "syson" / ".env",
    ):
        env.update(read_env_file(path))

    for key in (
        "FLEXO_MMS_FUSEKI_HOST_PORT",
        "FLEXO_MMS_MINIO_HOST_PORT",
        "FLEXO_MMS_AUTH_HOST_PORT",
        "FLEXO_MMS_STORE_HOST_PORT",
        "FLEXO_MMS_LAYER1_HOST_PORT",
        "FLEXO_MMS_SYSMLV2_HOST_PORT",
        "SYSON_HOST_PORT",
    ):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def inspect_docker_container(name: str, timeout: int) -> tuple[dict[str, Any] | None, str | None]:
    try:
        result = subprocess.run(
            ["docker", "inspect", name],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return None, "docker CLI is not available"
    except subprocess.TimeoutExpired:
        return None, f"docker inspect timed out after {timeout}s"

    if result.returncode != 0:
        return None, result.stderr.strip() or result.stdout.strip() or f"docker inspect exited {result.returncode}"

    inspected = json.loads(result.stdout)
    if len(inspected) != 1:
        return None, f"docker inspect returned {len(inspected)} objects"
    return inspected[0], None


def deployment_check(name: str, status: str, details: dict[str, Any], message: str | None = None) -> dict[str, Any]:
    check = {
        "name": name,
        "status": status,
        "details": details,
    }
    if message:
        check["message"] = message
    return check


def verify_deployment_contract(
    contract: dict[str, Any],
    env: dict[str, str],
    root: Path,
    timeout: int = 20,
) -> dict[str, Any]:
    services = []
    total_checks = 0
    failed_checks = 0

    for expected in contract["services"]:
        container_name = expected["containerName"]
        container, inspect_error = inspect_docker_container(container_name, timeout)
        checks: list[dict[str, Any]] = []
        if inspect_error:
            checks.append(
                deployment_check(
                    "container-inspect",
                    "failed",
                    {"containerName": container_name},
                    inspect_error,
                )
            )
        else:
            state = container.get("State", {})
            running = bool(state.get("Running"))
            checks.append(
                deployment_check(
                    "container-running",
                    "passed" if running else "failed",
                    {"status": state.get("Status"), "running": running},
                    None if running else f"{container_name} is not running: {state.get('Status')}",
                )
            )
            checks.extend(verify_deployment_ports(container, expected, env))
            checks.extend(verify_deployment_mounts(container, expected, root))

        service_failed_checks = sum(1 for check in checks if check["status"] != "passed")
        total_checks += len(checks)
        failed_checks += service_failed_checks
        services.append(
            {
                "id": expected.get("id"),
                "declaredName": expected.get("declaredName"),
                "stackName": expected.get("stackName"),
                "serviceName": expected.get("serviceName"),
                "containerName": container_name,
                "status": "failed" if service_failed_checks else "passed",
                "checks": checks,
            }
        )

    passed_services = sum(1 for service in services if service["status"] == "passed")
    report_status = "passed" if failed_checks == 0 else "failed"
    return {
        "status": report_status,
        "checkedAt": utc_now(),
        "project": contract.get("project", {}),
        "commit": contract.get("commit", {}),
        "summary": {
            "services": len(services),
            "passedServices": passed_services,
            "failedServices": len(services) - passed_services,
            "checks": total_checks,
            "passedChecks": total_checks - failed_checks,
            "failedChecks": failed_checks,
        },
        "services": services,
    }


def verify_deployment_ports(
    container: dict[str, Any],
    expected: dict[str, Any],
    env: dict[str, str],
) -> list[dict[str, Any]]:
    checks = []
    published_ports = container.get("NetworkSettings", {}).get("Ports") or {}
    for port in expected.get("ports", []):
        protocol = port.get("protocol", "tcp")
        container_port = f"{port['containerPort']}/{protocol}"
        bindings = published_ports.get(container_port) or []
        host_ports = sorted({binding.get("HostPort") for binding in bindings if binding.get("HostPort")})
        expected_host_port = env.get(port["hostPortEnv"], str(port["defaultHostPort"]))
        passed = expected_host_port in host_ports
        checks.append(
            deployment_check(
                "port-published",
                "passed" if passed else "failed",
                {
                    "containerPort": container_port,
                    "expectedHostPort": expected_host_port,
                    "hostPortEnv": port["hostPortEnv"],
                    "actualHostPorts": host_ports,
                },
                None
                if passed
                else (
                    f"{expected['containerName']} should publish {container_port} "
                    f"on host port {expected_host_port}"
                ),
            )
        )
    return checks


def verify_deployment_mounts(container: dict[str, Any], expected: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    checks = []
    mounts = container.get("Mounts") or []
    by_destination = {mount.get("Destination"): mount for mount in mounts}
    for mount in expected.get("mounts", []):
        actual = by_destination.get(mount["containerPath"])
        expected_source = os.path.abspath(root / mount["hostPath"])
        actual_source = actual.get("Source") if actual else None
        actual_type = actual.get("Type") if actual else None
        expected_type = mount.get("type", "bind")
        passed = bool(actual and actual_type == expected_type and actual_source == expected_source)
        checks.append(
            deployment_check(
                "mount-present",
                "passed" if passed else "failed",
                {
                    "containerPath": mount["containerPath"],
                    "expectedHostPath": expected_source,
                    "expectedType": expected_type,
                    "actualHostPath": actual_source,
                    "actualType": actual_type,
                },
                None
                if passed
                else f"{expected['containerName']} should mount {mount['containerPath']} from {expected_source}",
            )
        )
    return checks


def format_deployment_verification_report(report: dict[str, Any]) -> str:
    lines = [
        f"Deployment verification: {report['status']}",
        (
            "Services: "
            f"{report['summary']['passedServices']} passed, "
            f"{report['summary']['failedServices']} failed, "
            f"{report['summary']['services']} total"
        ),
        (
            "Checks: "
            f"{report['summary']['passedChecks']} passed, "
            f"{report['summary']['failedChecks']} failed, "
            f"{report['summary']['checks']} total"
        ),
        "",
    ]
    for service in report["services"]:
        lines.append(
            f"{service['status'].upper()} {service['containerName']} "
            f"({service.get('stackName') or 'unknown-stack'}/{service.get('serviceName') or 'unknown-service'})"
        )
        for check in service["checks"]:
            line = f"  - {check['status']} {check['name']}"
            if check.get("message"):
                line += f": {check['message']}"
            lines.append(line)
    return "\n".join(lines)


def cmd_deployment_verify(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    contract = deployment_contract_from_snapshot(read_json(args.fixture))
    if not contract["services"]:
        fail(f"no container services found in deployment fixture: {args.fixture}")
    report = verify_deployment_contract(
        contract,
        load_deployment_env(root),
        root,
        timeout=args.timeout,
    )
    report["fixture"] = str(args.fixture)

    if args.output:
        write_json(args.output, report)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_deployment_verification_report(report))
    if report["status"] != "passed":
        raise SystemExit(1)


def cmd_render_sysml(args: argparse.Namespace) -> None:
    snapshot = read_json(args.input)
    text = render_snapshot(snapshot)
    output = args.output
    if output is None:
        project_id = snapshot.get("project", {}).get("@id", "flexo-export")
        output = DEFAULT_OUTPUT_DIR / "sysml" / f"{project_id}.sysml"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    info(f"Wrote SysML textual export: {output}")


def cmd_syson_list_projects(args: argparse.Namespace) -> None:
    query = """
    query {
      viewer {
        projects {
          edges {
            node {
              id
              name
              currentEditingContext { id }
            }
          }
        }
      }
    }
    """
    response = graphql(args.syson_url, query, timeout=args.timeout)
    projects = response["data"]["viewer"]["projects"]["edges"]
    for edge in projects:
        node = edge["node"]
        editing_context = node.get("currentEditingContext") or {}
        print(f"{node['id']}  {node['name']}  editingContext={editing_context.get('id')}")


def cmd_syson_create_project(args: argparse.Namespace) -> None:
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
    variables = {
        "input": {
            "id": str(uuid.uuid4()),
            "name": args.name,
            "templateId": args.template_id,
            "libraryIds": args.library_ids,
        }
    }
    response = graphql(args.syson_url, mutation, variables, timeout=args.timeout)
    result = response["data"]["createProject"]
    if result["__typename"] == "ErrorPayload":
        fail(result["message"])
    print(json.dumps(result["project"], indent=2))


def cmd_syson_roots(args: argparse.Namespace) -> None:
    project_id = args.project_id
    roots = request_json(
        "GET",
        f"{trim_url(args.syson_url)}/api/rest/projects/{project_id}/commits/{project_id}/roots",
        timeout=args.timeout,
    )
    if args.json:
        print(json.dumps(roots, indent=2))
        return
    for root in roots:
        print(f"{root.get('@id')}  {root.get('@type')}  {root.get('declaredName') or root.get('name')}")


def syson_editing_context_id(syson_url: str, project_id: str, timeout: int) -> str:
    query = """
    query FetchEditingContext($projectId: ID!) {
      viewer {
        project(projectId: $projectId) {
          currentEditingContext { id }
        }
      }
    }
    """
    response = graphql(syson_url, query, {"projectId": project_id}, timeout=timeout)
    project = response["data"]["viewer"].get("project")
    if not project:
        fail(f"SysON project not found: {project_id}")
    editing_context = project.get("currentEditingContext")
    if not editing_context:
        fail(f"SysON project has no current editing context: {project_id}")
    return editing_context["id"]


def import_sysml_text(
    syson_url: str,
    project_id: str,
    namespace_id: str,
    textual_content: str,
    editing_context_id: str | None,
    timeout: int,
) -> dict[str, Any]:
    resolved_editing_context_id = editing_context_id or syson_editing_context_id(
        syson_url,
        project_id,
        timeout,
    )
    mutation = """
    mutation InsertTextualSysMLv2($input: InsertTextualSysMLv2Input!) {
      insertTextualSysMLv2(input: $input) {
        __typename
        ... on SuccessPayload { id }
        ... on ErrorPayload { message }
      }
    }
    """
    variables = {
        "input": {
            "id": str(uuid.uuid4()),
            "editingContextId": resolved_editing_context_id,
            "objectId": namespace_id,
            "textualContent": textual_content,
        }
    }
    response = graphql(syson_url, mutation, variables, timeout=timeout)
    result = response["data"]["insertTextualSysMLv2"]
    if result["__typename"] == "ErrorPayload":
        fail(result["message"])
    return {
        "editing_context_id": resolved_editing_context_id,
        "result": result,
    }


def cmd_syson_import_text(args: argparse.Namespace) -> None:
    import_sysml_text(
        args.syson_url,
        args.project_id,
        args.namespace_id,
        args.input.read_text(encoding="utf-8"),
        args.editing_context_id,
        args.timeout,
    )
    info(f"Imported {args.input} into SysON project {args.project_id}.")


def cmd_flexo_to_syson(args: argparse.Namespace) -> None:
    run_id = str(uuid.uuid4())
    workflow = "flexo-to-syson"
    log_path = args.run_log or run_log_path(args.run_log_dir, workflow, run_id)
    started_at = utc_now()
    started_perf = time.perf_counter()
    record: dict[str, Any] = {
        "run_id": run_id,
        "workflow": workflow,
        "status": "running",
        "started_at": started_at,
        "inputs": {
            "flexo_project_id": args.flexo_project_id,
            "commit_id": args.commit_id,
            "syson_project_id": args.syson_project_id,
            "namespace_id": args.namespace_id,
            "editing_context_id_provided": bool(args.editing_context_id),
            "output_dir": str(args.output_dir),
            "flexo_url": args.flexo_url,
            "syson_url": args.syson_url,
            "timeout": args.timeout,
        },
        "artifacts": {},
        "flexo": {},
        "syson": {
            "project_id": args.syson_project_id,
            "namespace_id": args.namespace_id,
        },
        "steps": [],
    }
    output_dir = args.output_dir
    export_path = output_dir / "flexo" / f"{args.flexo_project_id}.json"
    sysml_path = output_dir / "sysml" / f"{args.flexo_project_id}.sysml"
    try:
        step_start = utc_now()
        step_perf = time.perf_counter()
        snapshot = export_flexo_project(args.flexo_url, args.flexo_project_id, args.commit_id, args.timeout)
        add_step(
            record,
            "export-flexo",
            "succeeded",
            step_start,
            time.perf_counter() - step_perf,
            {
                "project_id": snapshot.get("project", {}).get("@id"),
                "commit_id": snapshot.get("commit", {}).get("@id"),
                "root_count": len(snapshot.get("roots") or []),
                "element_count": len(snapshot.get("elements") or []),
            },
        )
        record["flexo"] = {
            "project_id": snapshot.get("project", {}).get("@id"),
            "project_name": snapshot.get("project", {}).get("name"),
            "commit_id": snapshot.get("commit", {}).get("@id"),
            "root_count": len(snapshot.get("roots") or []),
            "element_count": len(snapshot.get("elements") or []),
        }

        step_start = utc_now()
        step_perf = time.perf_counter()
        write_json(export_path, snapshot)
        add_step(
            record,
            "write-flexo-export",
            "succeeded",
            step_start,
            time.perf_counter() - step_perf,
            {"path": str(export_path)},
        )
        record["artifacts"]["flexo_export"] = str(export_path)

        step_start = utc_now()
        step_perf = time.perf_counter()
        sysml_text = render_snapshot(snapshot)
        sysml_path.parent.mkdir(parents=True, exist_ok=True)
        sysml_path.write_text(sysml_text, encoding="utf-8")
        add_step(
            record,
            "render-sysml",
            "succeeded",
            step_start,
            time.perf_counter() - step_perf,
            {"path": str(sysml_path), "bytes": len(sysml_text.encode("utf-8"))},
        )
        record["artifacts"]["sysml_text"] = str(sysml_path)
        info(f"Wrote Flexo export: {export_path}")
        info(f"Wrote SysML textual export: {sysml_path}")

        step_start = utc_now()
        step_perf = time.perf_counter()
        import_result = import_sysml_text(
            args.syson_url,
            args.syson_project_id,
            args.namespace_id,
            sysml_text,
            args.editing_context_id,
            args.timeout,
        )
        add_step(
            record,
            "import-syson",
            "succeeded",
            step_start,
            time.perf_counter() - step_perf,
            import_result,
        )
        record["syson"]["editing_context_id"] = import_result["editing_context_id"]
        record["syson"]["import_result"] = import_result["result"]
        info(f"Imported {sysml_path} into SysON project {args.syson_project_id}.")
        record["status"] = "succeeded"
    except BaseException as exc:
        record["status"] = "failed"
        record["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
        raise
    finally:
        record["completed_at"] = utc_now()
        record["duration_seconds"] = round(time.perf_counter() - started_perf, 6)
        write_run_log(log_path, record)
        info(f"Wrote run log: {log_path}")


def add_common_url_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--timeout", type=int, default=30)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_org = subparsers.add_parser("init-flexo-org", help="Create the Flexo org used by the SysML v2 service")
    init_org.add_argument("--layer1-url", default=DEFAULT_LAYER1_URL)
    init_org.add_argument("--env-dir", type=Path, default=DEFAULT_FLEXO_ENV_DIR)
    init_org.add_argument("--org-id", default="sysmlv2")
    init_org.add_argument("--title", default="SysML v2")
    init_org.add_argument("--token")
    add_common_url_args(init_org)
    init_org.set_defaults(func=cmd_init_flexo_org)

    list_flexo = subparsers.add_parser("flexo-list-projects", help="List Flexo SysML v2 projects")
    list_flexo.add_argument("--flexo-url", default=DEFAULT_FLEXO_URL)
    list_flexo.add_argument("--json", action="store_true")
    add_common_url_args(list_flexo)
    list_flexo.set_defaults(func=cmd_flexo_list_projects)

    create_flexo = subparsers.add_parser("flexo-create-project", help="Create a Flexo SysML v2 project")
    create_flexo.add_argument("name")
    create_flexo.add_argument("--description")
    create_flexo.add_argument("--flexo-url", default=DEFAULT_FLEXO_URL)
    add_common_url_args(create_flexo)
    create_flexo.set_defaults(func=cmd_flexo_create_project)

    export_flexo = subparsers.add_parser("flexo-export", help="Export a Flexo project snapshot")
    export_flexo.add_argument("project_id")
    export_flexo.add_argument("--commit-id")
    export_flexo.add_argument("--output", type=Path)
    export_flexo.add_argument("--flexo-url", default=DEFAULT_FLEXO_URL)
    add_common_url_args(export_flexo)
    export_flexo.set_defaults(func=cmd_flexo_export)

    render = subparsers.add_parser("render-sysml", help="Render a Flexo export JSON file as SysML textual notation")
    render.add_argument("input", type=Path)
    render.add_argument("--output", type=Path)
    render.set_defaults(func=cmd_render_sysml)

    contract = subparsers.add_parser("deployment-contract", help="Print the fixture-derived deployment runtime contract")
    contract.add_argument("--fixture", type=Path, default=DEFAULT_DEPLOYMENT_FIXTURE)
    contract.add_argument("--json", action="store_true")
    contract.set_defaults(func=cmd_deployment_contract)

    verify = subparsers.add_parser(
        "deployment-verify",
        help="Verify Docker runtime state against the deployment contract",
    )
    verify.add_argument("--fixture", type=Path, default=DEFAULT_DEPLOYMENT_FIXTURE)
    verify.add_argument("--root", type=Path, default=Path("."))
    verify.add_argument("--timeout", type=int, default=20)
    verify.add_argument("--json", action="store_true")
    verify.add_argument("--output", type=Path, help="Write the structured verification report as JSON.")
    verify.set_defaults(func=cmd_deployment_verify)

    list_syson = subparsers.add_parser("syson-list-projects", help="List SysON projects")
    list_syson.add_argument("--syson-url", default=DEFAULT_SYSON_URL)
    add_common_url_args(list_syson)
    list_syson.set_defaults(func=cmd_syson_list_projects)

    create_syson = subparsers.add_parser("syson-create-project", help="Create a SysON project")
    create_syson.add_argument("name")
    create_syson.add_argument("--template-id", default="sysmlv2-template")
    create_syson.add_argument("--library-ids", nargs="*", default=[])
    create_syson.add_argument("--syson-url", default=DEFAULT_SYSON_URL)
    add_common_url_args(create_syson)
    create_syson.set_defaults(func=cmd_syson_create_project)

    roots = subparsers.add_parser("syson-roots", help="List root namespace elements for a SysON project")
    roots.add_argument("project_id")
    roots.add_argument("--syson-url", default=DEFAULT_SYSON_URL)
    roots.add_argument("--json", action="store_true")
    add_common_url_args(roots)
    roots.set_defaults(func=cmd_syson_roots)

    import_text = subparsers.add_parser("syson-import-text", help="Import a .sysml file into a SysON namespace")
    import_text.add_argument("input", type=Path)
    import_text.add_argument("--project-id", required=True)
    import_text.add_argument("--namespace-id", required=True)
    import_text.add_argument("--editing-context-id")
    import_text.add_argument("--syson-url", default=DEFAULT_SYSON_URL)
    add_common_url_args(import_text)
    import_text.set_defaults(func=cmd_syson_import_text)

    pipeline = subparsers.add_parser("flexo-to-syson", help="Export from Flexo, render .sysml, and import into SysON")
    pipeline.add_argument("flexo_project_id")
    pipeline.add_argument("--commit-id")
    pipeline.add_argument("--syson-project-id", required=True)
    pipeline.add_argument("--namespace-id", required=True)
    pipeline.add_argument("--editing-context-id")
    pipeline.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    pipeline.add_argument("--run-log", type=Path, help="Write the structured run log to this exact path.")
    pipeline.add_argument("--run-log-dir", type=Path, default=DEFAULT_RUN_DIR, help="Directory for generated run logs.")
    pipeline.add_argument("--flexo-url", default=DEFAULT_FLEXO_URL)
    pipeline.add_argument("--syson-url", default=DEFAULT_SYSON_URL)
    add_common_url_args(pipeline)
    pipeline.set_defaults(func=cmd_flexo_to_syson)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
