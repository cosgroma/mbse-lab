#!/usr/bin/env python3
"""Manage a local OpenMBEE Flexo MMS Docker Compose environment."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import hmac
import json
import secrets
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_ENV_DIR = Path("deploy/flexo-mms")
CLUSTER_TRIG_URL = (
    "https://raw.githubusercontent.com/Open-MBEE/flexo-mms-deployment/"
    "develop/docker-compose/mount/cluster.trig"
)

CORE_CONTAINERS = [
    "openldap-server",
    "quad-server",
    "minio-server",
    "auth-service",
    "store-service",
    "layer1-service",
]
SYSMLV2_CONTAINER = "flexo-sysmlv2"

ENV_FILE_EXAMPLES = {
    ".env.example": """\
FLEXO_MMS_FUSEKI_HOST_PORT=3030
FLEXO_MMS_MINIO_HOST_PORT=9000
FLEXO_MMS_STORE_HOST_PORT=8081
FLEXO_MMS_AUTH_HOST_PORT=8082
FLEXO_MMS_LAYER1_HOST_PORT=18080
FLEXO_MMS_SYSMLV2_HOST_PORT=18083
FLEXO_MMS_LDAP_ADMIN_PASSWORD=change-me
FLEXO_MMS_LDAP_USER01_PASSWORD=change-me
FLEXO_MMS_LDAP_USER02_PASSWORD=change-me
FLEXO_MMS_MINIO_ROOT_USER=change-me
FLEXO_MMS_MINIO_ROOT_PASSWORD=change-me
""",
    "env/flexo-mms-auth.env.example": """\
LDAP_LOCATION=ldap://openldap-server:1389
LDAP_BASE=dc=example,dc=org
LDAP_USER_PATTERN=cn=%s,ou=users
LDAP_USER_NAMESPACE=ldap/user/
LDAP_GROUP_SEARCH_FILTER=(&(objectclass=group)(member=%s)(|(%s)))
LDAP_GROUP_ATTRIBUTE=cn
LDAP_GROUP_STORE_URI=http://quad-server:3030/ds/sparql
LDAP_GROUP_STORE_CONTEXT=http://layer1-service/
""",
    "env/flexo-mms-jwt.env.example": """\
JWT_DOMAIN=http://flexo-mms-services
JWT_AUDIENCE=flexo-mms-audience
JWT_REALM=flexo-mms
JWT_SECRET=change-me
""",
    "env/flexo-mms-layer1.env.example": """\
FLEXO_MMS_ROOT_CONTEXT=http://layer1-service
FLEXO_MMS_STORE_SERVICE_URL=http://store-service:8080/store
FLEXO_MMS_QUERY_URL=http://quad-server:3030/ds/sparql
FLEXO_MMS_UPDATE_URL=http://quad-server:3030/ds/update
FLEXO_MMS_GRAPH_STORE_PROTOCOL_URL=http://quad-server:3030/ds/data
FLEXO_MMS_ARTIFACT_USE_STORE=true
""",
    "env/flexo-mms-quad-store.env.example": """\
JAVA_OPTIONS="-Xmx4096m -Xms1024m"
""",
    "env/flexo-mms-store.env.example": """\
S3_ENDPOINT=http://minio-server:9000
S3_REGION=us-east-1
""",
    "env/flexo-sysmlv2.env.example": """\
FLEXO_HOST=layer1-service
FLEXO_PROTOCOL=http
FLEXO_PORT=8080
FLEXO_SYSMLV2_ORG=sysmlv2
FLEXO_AUTH="Bearer generated-at-init-time"
""",
}

COMPOSE_TEMPLATE = """\
services:
  openldap-server:
    image: bitnamilegacy/openldap:2.6.4
    hostname: openldap-server
    container_name: openldap-server
    environment:
      - LDAP_PORT_NUMBER=1389
      - LDAP_ROOT=dc=example,dc=org
      - LDAP_ADMIN_USERNAME=admin
      - LDAP_ADMIN_PASSWORD=${FLEXO_MMS_LDAP_ADMIN_PASSWORD}
      - LDAP_USERS=user01,user02
      - LDAP_USER_DC=users
      - LDAP_GROUP=group01
      - LDAP_PASSWORDS=${FLEXO_MMS_LDAP_USER01_PASSWORD},${FLEXO_MMS_LDAP_USER02_PASSWORD}

  quad-store-server:
    image: atomgraph/fuseki:4.6
    hostname: quad-server
    container_name: quad-server
    env_file:
      - ./env/flexo-mms-quad-store.env
    command: --file=/tmp/mount/cluster.trig --update /ds
    volumes:
      - ./mount:/tmp/mount
    ports:
      - "${FLEXO_MMS_FUSEKI_HOST_PORT:-3030}:3030"

  minio-server:
    image: quay.io/minio/minio
    hostname: minio-server
    container_name: minio-server
    environment:
      - MINIO_ROOT_USER=${FLEXO_MMS_MINIO_ROOT_USER}
      - MINIO_ROOT_PASSWORD=${FLEXO_MMS_MINIO_ROOT_PASSWORD}
    command: server /data
    volumes:
      - ./data/minio:/data
    ports:
      - "${FLEXO_MMS_MINIO_HOST_PORT:-9000}:9000"

  auth-service:
    image: openmbee/flexo-mms-auth-service:latest
    hostname: auth-service
    container_name: auth-service
    env_file:
      - ./env/flexo-mms-jwt.env
      - ./env/flexo-mms-auth.env
    depends_on:
      - openldap-server
      - quad-store-server
    ports:
      - "${FLEXO_MMS_AUTH_HOST_PORT:-8082}:8080"

  store-service:
    image: openmbee/flexo-mms-store-service:v0.2.0
    hostname: store-service
    container_name: store-service
    env_file:
      - ./env/flexo-mms-jwt.env
      - ./env/flexo-mms-store.env
    environment:
      - AWS_ACCESS_KEY_ID=${FLEXO_MMS_MINIO_ROOT_USER}
      - AWS_SECRET_ACCESS_KEY=${FLEXO_MMS_MINIO_ROOT_PASSWORD}
    depends_on:
      - minio-server
    ports:
      - "${FLEXO_MMS_STORE_HOST_PORT:-8081}:8080"

  layer1-service:
    image: openmbee/flexo-mms-layer1-service:v0.2.2
    hostname: layer1-service
    container_name: layer1-service
    env_file:
      - ./env/flexo-mms-jwt.env
      - ./env/flexo-mms-layer1.env
    depends_on:
      - store-service
      - auth-service
      - quad-store-server
    ports:
      - "${FLEXO_MMS_LAYER1_HOST_PORT:-18080}:8080"
{sysmlv2_service}

networks:
  default:
    name: flexo-mms-test-network
    driver: bridge
"""

SYSMLV2_SERVICE = """
  sysmlv2-service:
    image: openmbee/flexo-sysmlv2:v0.1.1
    hostname: flexo-sysmlv2
    container_name: flexo-sysmlv2
    env_file:
      - ./env/flexo-sysmlv2.env
    depends_on:
      - layer1-service
    ports:
      - "${FLEXO_MMS_SYSMLV2_HOST_PORT:-18083}:8080"
"""


def info(message: str) -> None:
    print(message)


def fail(message: str, exit_code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def run(command: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        fail(f"command failed with exit code {result.returncode}: {' '.join(command)}")
    return result


def docker_compose_command() -> list[str]:
    if shutil.which("docker"):
        result = subprocess.run(
            ["docker", "compose", "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode == 0:
            return ["docker", "compose"]
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    fail("Docker Compose was not found. Install Docker with the compose plugin or docker-compose.")


def compose_file(env_dir: Path) -> Path:
    return env_dir / "docker-compose.yml"


def compose_file_arg(env_dir: Path) -> str:
    return str(compose_file(env_dir).resolve())


def expected_containers(include_sysmlv2: bool) -> list[str]:
    containers = list(CORE_CONTAINERS)
    if include_sysmlv2:
        containers.append(SYSMLV2_CONTAINER)
    return containers


def has_sysmlv2(env_dir: Path) -> bool:
    path = compose_file(env_dir)
    return path.exists() and SYSMLV2_CONTAINER in path.read_text(encoding="utf-8")


def write_file(path: Path, contents: str, force: bool) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")
    return True


def random_secret(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def generate_service_jwt(secret: str, issuer: str, audience: str) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "aud": audience,
        "iss": issuer,
        "username": "user01",
        "groups": ["super_admins"],
        "iat": now,
        "exp": now + 10 * 365 * 24 * 60 * 60,
    }
    signing_input = ".".join(
        [
            b64url(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
    )
    signature = hmac.new(secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{b64url(signature)}"


def generated_env_files() -> dict[str, str]:
    jwt_domain = "http://flexo-mms-services"
    jwt_audience = "flexo-mms-audience"
    jwt_secret = random_secret(48)
    minio_user = "flexo-" + secrets.token_hex(8)
    minio_password = random_secret(32)
    user01_password = random_secret(18)
    service_token = generate_service_jwt(jwt_secret, jwt_domain, jwt_audience)
    return {
        ".env": f"""\
FLEXO_MMS_FUSEKI_HOST_PORT=3030
FLEXO_MMS_MINIO_HOST_PORT=9000
FLEXO_MMS_STORE_HOST_PORT=8081
FLEXO_MMS_AUTH_HOST_PORT=8082
FLEXO_MMS_LAYER1_HOST_PORT=18080
FLEXO_MMS_SYSMLV2_HOST_PORT=18083
FLEXO_MMS_LDAP_ADMIN_PASSWORD={random_secret(18)}
FLEXO_MMS_LDAP_USER01_PASSWORD={user01_password}
FLEXO_MMS_LDAP_USER02_PASSWORD={random_secret(18)}
FLEXO_MMS_MINIO_ROOT_USER={minio_user}
FLEXO_MMS_MINIO_ROOT_PASSWORD={minio_password}
""",
        "env/flexo-mms-auth.env": ENV_FILE_EXAMPLES["env/flexo-mms-auth.env.example"],
        "env/flexo-mms-jwt.env": f"""\
JWT_DOMAIN={jwt_domain}
JWT_AUDIENCE={jwt_audience}
JWT_REALM=flexo-mms
JWT_SECRET={jwt_secret}
""",
        "env/flexo-mms-layer1.env": ENV_FILE_EXAMPLES["env/flexo-mms-layer1.env.example"],
        "env/flexo-mms-quad-store.env": ENV_FILE_EXAMPLES["env/flexo-mms-quad-store.env.example"],
        "env/flexo-mms-store.env": ENV_FILE_EXAMPLES["env/flexo-mms-store.env.example"],
        "env/flexo-sysmlv2.env": f"""\
FLEXO_HOST=layer1-service
FLEXO_PROTOCOL=http
FLEXO_PORT=8080
FLEXO_SYSMLV2_ORG=sysmlv2
FLEXO_AUTH="Bearer {service_token}"
""",
    }


def download_cluster_trig(target: Path, force: bool) -> bool:
    if target.exists() and not force:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(CLUSTER_TRIG_URL, timeout=30) as response:
            target.write_bytes(response.read())
    except (urllib.error.URLError, TimeoutError) as exc:
        fail(
            "could not download cluster.trig from OpenMBEE. "
            f"Create {target} manually or rerun with network access. Details: {exc}"
        )
    return True


def cmd_init(args: argparse.Namespace) -> None:
    env_dir = args.env_dir
    env_dir.mkdir(parents=True, exist_ok=True)
    (env_dir / "backups").mkdir(parents=True, exist_ok=True)
    (env_dir / "data" / "minio").mkdir(parents=True, exist_ok=True)

    sysmlv2 = SYSMLV2_SERVICE if args.with_sysmlv2 else ""
    compose_contents = COMPOSE_TEMPLATE.format(sysmlv2_service=sysmlv2)

    changed: list[Path] = []
    for relative_path, contents in ENV_FILE_EXAMPLES.items():
        path = env_dir / relative_path
        if write_file(path, contents, args.force):
            changed.append(path)

    for relative_path, contents in generated_env_files().items():
        path = env_dir / relative_path
        if write_file(path, contents, args.force):
            changed.append(path)

    compose_path = compose_file(env_dir)
    if write_file(compose_path, compose_contents, args.force):
        changed.append(compose_path)

    cluster_path = env_dir / "mount" / "cluster.trig"
    if download_cluster_trig(cluster_path, args.force):
        changed.append(cluster_path)

    readme = env_dir / "README.md"
    layer1_port = read_env_value(env_dir / ".env", "FLEXO_MMS_LAYER1_HOST_PORT", "18080")
    auth_port = read_env_value(env_dir / ".env", "FLEXO_MMS_AUTH_HOST_PORT", "8082")
    fuseki_port = read_env_value(env_dir / ".env", "FLEXO_MMS_FUSEKI_HOST_PORT", "3030")
    minio_port = read_env_value(env_dir / ".env", "FLEXO_MMS_MINIO_HOST_PORT", "9000")
    sysmlv2_port = read_env_value(env_dir / ".env", "FLEXO_MMS_SYSMLV2_HOST_PORT", "18083")
    readme_contents = f"""\
# Flexo MMS Local Environment

Generated by `scripts/flexo_mms_env.py`.

## Commands

```bash
python3 scripts/flexo_mms_env.py up
python3 scripts/flexo_mms_env.py status
python3 scripts/flexo_mms_env.py token
python3 scripts/flexo_mms_env.py backup
python3 scripts/flexo_mms_env.py down
```

Core services:

- Layer1 API: http://localhost:{layer1_port}
- Auth login: http://localhost:{auth_port}/login
- Fuseki: http://localhost:{fuseki_port}
- MinIO: http://localhost:{minio_port}
{"- SysML v2 API: http://localhost:" + sysmlv2_port if args.with_sysmlv2 else ""}
"""
    if write_file(readme, readme_contents, args.force):
        changed.append(readme)

    if changed:
        info("Initialized Flexo MMS files:")
        for path in changed:
            info(f"  {path}")
    else:
        info(f"Flexo MMS environment already exists at {env_dir}. Use --force to overwrite generated files.")


def cmd_rotate_secrets(args: argparse.Namespace) -> None:
    env_dir = args.env_dir
    env_dir.mkdir(parents=True, exist_ok=True)
    changed: list[Path] = []
    for relative_path, contents in generated_env_files().items():
        path = env_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
        changed.append(path)
    info("Rotated local Flexo runtime env files:")
    for path in changed:
        info(f"  {path}")
    info("Restart the Flexo stack for containers to use the new credentials.")


def read_env_value(path: Path, key: str, default: str) -> str:
    if not path.exists():
        return default
    prefix = f"{key}="
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith(prefix):
            return line[len(prefix) :].strip().strip('"').strip("'")
    return default


def ensure_initialized(env_dir: Path) -> None:
    if not compose_file(env_dir).exists():
        fail(f"{compose_file(env_dir)} does not exist. Run `init` first.")
    if not (env_dir / "mount" / "cluster.trig").exists():
        fail(f"{env_dir / 'mount' / 'cluster.trig'} does not exist. Run `init --force` to download it.")


def cmd_up(args: argparse.Namespace) -> None:
    ensure_initialized(args.env_dir)
    compose = docker_compose_command()
    command = compose + ["-f", compose_file_arg(args.env_dir), "up", "-d"]
    info("Starting Flexo MMS services...")
    result = run(command)
    if result.stdout:
        print(result.stdout, end="")
    if args.wait:
        wait_for_containers(expected_containers(has_sysmlv2(args.env_dir)), args.timeout)
    info("Flexo MMS startup command completed.")


def cmd_down(args: argparse.Namespace) -> None:
    ensure_initialized(args.env_dir)
    compose = docker_compose_command()
    command = compose + ["-f", compose_file_arg(args.env_dir), "down"]
    if args.volumes:
        command.append("--volumes")
    result = run(command)
    if result.stdout:
        print(result.stdout, end="")


def container_state(name: str) -> tuple[str, str, str]:
    result = run(["docker", "inspect", name], check=False)
    if result.returncode != 0:
        return ("missing", "none", "")
    data = json.loads(result.stdout)
    if not data:
        return ("missing", "none", "")
    container = data[0]
    state = container.get("State", {})
    status = state.get("Status", "unknown")
    health = state.get("Health", {}).get("Status", "none")
    ports_data = container.get("NetworkSettings", {}).get("Ports") or {}
    ports = []
    for container_port, bindings in sorted(ports_data.items()):
        if not bindings:
            continue
        for binding in bindings:
            host_ip = binding.get("HostIp", "")
            host_port = binding.get("HostPort", "")
            host = f"{host_ip}:{host_port}" if host_ip else host_port
            ports.append(f"{container_port}={host}")
    return (status, health, " ".join(ports))


def print_status(containers: list[str], strict: bool) -> None:
    rows = []
    failures = 0
    for name in containers:
        status, health, ports = container_state(name)
        ok = status == "running" and health not in {"unhealthy"}
        if not ok:
            failures += 1
        rows.append((name, status, health, ports, ok))

    print(f"{'container':<22} {'status':<10} {'health':<10} ports")
    print("-" * 80)
    for name, status, health, ports, ok in rows:
        marker = "OK" if ok else "FAIL"
        print(f"{name:<22} {status:<10} {health:<10} {ports} {marker}")

    if strict and failures:
        raise SystemExit(1)


def cmd_status(args: argparse.Namespace) -> None:
    include_sysmlv2 = args.with_sysmlv2 or has_sysmlv2(args.env_dir)
    print_status(expected_containers(include_sysmlv2), args.strict)


def wait_for_containers(containers: list[str], timeout: int) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        states = [container_state(name)[0] for name in containers]
        if all(state == "running" for state in states):
            print_status(containers, strict=False)
            return
        time.sleep(3)
    print_status(containers, strict=False)
    fail(f"timed out waiting for containers to run after {timeout}s")


def cmd_logs(args: argparse.Namespace) -> None:
    ensure_initialized(args.env_dir)
    compose = docker_compose_command()
    command = compose + ["-f", compose_file_arg(args.env_dir), "logs"]
    if args.follow:
        command.append("--follow")
    if args.tail:
        command += ["--tail", str(args.tail)]
    command += args.services
    subprocess.run(command, check=False)


def cmd_token(args: argparse.Namespace) -> None:
    if args.url:
        url = args.url
    else:
        auth_port = read_env_value(args.env_dir / ".env", "FLEXO_MMS_AUTH_HOST_PORT", "8082")
        url = f"http://localhost:{auth_port}/login"
    password = args.password or read_env_value(args.env_dir / ".env", "FLEXO_MMS_LDAP_USER01_PASSWORD", "")
    if not password:
        fail("no password provided and FLEXO_MMS_LDAP_USER01_PASSWORD was not found in the generated .env")
    credentials = f"{args.username}:{password}".encode("utf-8")
    request = urllib.request.Request(url)
    request.add_header("Authorization", "Basic " + base64.b64encode(credentials).decode("ascii"))
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        fail(f"auth service returned HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')}")
    except urllib.error.URLError as exc:
        fail(f"could not reach auth service at {url}: {exc}")

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        print(body)
        return

    if isinstance(parsed, str):
        print(parsed)
    elif isinstance(parsed, dict):
        for key in ("token", "access_token", "jwt"):
            if key in parsed:
                print(parsed[key])
                return
        print(json.dumps(parsed, indent=2))
    else:
        print(json.dumps(parsed, indent=2))


def cmd_backup(args: argparse.Namespace) -> None:
    env_dir = args.env_dir
    fuseki_port = read_env_value(env_dir / ".env", "FLEXO_MMS_FUSEKI_HOST_PORT", "3030")
    url = args.url or f"http://localhost:{fuseki_port}/ds"
    output = args.output
    if output is None:
        timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output = env_dir / "backups" / f"flexo-mms-{timestamp}.nq"

    request = urllib.request.Request(url)
    request.add_header("Accept", "application/n-quads")
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            contents = response.read()
    except urllib.error.URLError as exc:
        fail(f"could not export Fuseki dataset from {url}: {exc}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(contents)
    info(f"Wrote dataset backup: {output}")

    if args.update_init:
        init_path = env_dir / "mount" / "cluster.trig"
        init_path.parent.mkdir(parents=True, exist_ok=True)
        init_path.write_bytes(contents)
        info(f"Updated startup dataset file: {init_path}")


def cmd_restore(args: argparse.Namespace) -> None:
    backup = args.backup
    if not backup.exists():
        fail(f"backup file does not exist: {backup}")
    init_path = args.env_dir / "mount" / "cluster.trig"
    init_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(backup, init_path)
    info(f"Restored startup dataset file from {backup} to {init_path}")
    info("Restart the stack with `down` then `up --wait` for this local Fuseki setup to reload it.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--env-dir",
        type=Path,
        default=DEFAULT_ENV_DIR,
        help=f"Flexo MMS environment directory. Default: {DEFAULT_ENV_DIR}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create local Compose, env, and initialization files.")
    init_parser.add_argument("--force", action="store_true", help="Overwrite generated files.")
    init_parser.add_argument("--with-sysmlv2", action="store_true", help="Include the Flexo SysML v2 API service.")
    init_parser.set_defaults(func=cmd_init)

    rotate_parser = subparsers.add_parser("rotate-secrets", help="Regenerate ignored local runtime env files.")
    rotate_parser.set_defaults(func=cmd_rotate_secrets)

    up_parser = subparsers.add_parser("up", help="Start the Flexo MMS Docker Compose environment.")
    up_parser.add_argument("--wait", action="store_true", help="Wait until expected containers are running.")
    up_parser.add_argument("--timeout", type=int, default=180, help="Wait timeout in seconds.")
    up_parser.set_defaults(func=cmd_up)

    down_parser = subparsers.add_parser("down", help="Stop the Flexo MMS Docker Compose environment.")
    down_parser.add_argument("--volumes", action="store_true", help="Also remove compose-managed volumes.")
    down_parser.set_defaults(func=cmd_down)

    status_parser = subparsers.add_parser("status", help="Check expected Docker container status.")
    status_parser.add_argument("--strict", action="store_true", help="Exit non-zero if any expected container is not running.")
    status_parser.add_argument("--with-sysmlv2", action="store_true", help="Also check the SysML v2 container.")
    status_parser.set_defaults(func=cmd_status)

    logs_parser = subparsers.add_parser("logs", help="Show Docker Compose logs.")
    logs_parser.add_argument("services", nargs="*", help="Optional compose service names.")
    logs_parser.add_argument("--follow", "-f", action="store_true", help="Follow logs.")
    logs_parser.add_argument("--tail", type=int, default=100, help="Number of log lines to show.")
    logs_parser.set_defaults(func=cmd_logs)

    token_parser = subparsers.add_parser("token", help="Request a local JWT from the auth service.")
    token_parser.add_argument("--url", help="Auth service login URL. Defaults to the generated auth host port.")
    token_parser.add_argument("--username", default="user01", help="LDAP username.")
    token_parser.add_argument("--password", help="LDAP password. Defaults to FLEXO_MMS_LDAP_USER01_PASSWORD in .env.")
    token_parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds.")
    token_parser.set_defaults(func=cmd_token)

    backup_parser = subparsers.add_parser("backup", help="Export the live Fuseki dataset to a durable N-Quads file.")
    backup_parser.add_argument("--url", help="Fuseki dataset URL. Defaults to the generated Fuseki host port.")
    backup_parser.add_argument("--output", type=Path, help="Backup file path. Defaults to deploy/flexo-mms/backups/*.nq.")
    backup_parser.add_argument("--timeout", type=int, default=60, help="HTTP timeout in seconds.")
    backup_parser.add_argument(
        "--no-update-init",
        dest="update_init",
        action="store_false",
        help="Do not refresh mount/cluster.trig after exporting the backup.",
    )
    backup_parser.set_defaults(func=cmd_backup, update_init=True)

    restore_parser = subparsers.add_parser("restore", help="Restore mount/cluster.trig from a backup file.")
    restore_parser.add_argument("backup", type=Path, help="Backup file to copy into mount/cluster.trig.")
    restore_parser.set_defaults(func=cmd_restore)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
