"""HTTP and GraphQL helpers for the MBSE lab CLI."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

import click


def trim_url(url: str) -> str:
    return url.rstrip("/")


def request_bytes(
    method: str,
    url: str,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> tuple[int, bytes, dict[str, str]]:
    request = urllib.request.Request(url, data=body, method=method)
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read(), dict(response.headers)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), dict(exc.headers)


def request_json(
    method: str,
    url: str,
    payload: object | None = None,
    timeout: int = 30,
    expected: set[int] | None = None,
) -> object:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    expected_status = expected or {200}
    try:
        status, raw_bytes, _headers = request_bytes(method, url, body=body, headers=headers, timeout=timeout)
    except urllib.error.URLError as exc:
        raise click.ClickException(f"{method} {url} failed: {exc}") from exc
    raw = raw_bytes.decode("utf-8", errors="replace")
    if status not in expected_status:
        raise click.ClickException(f"{method} {url} returned {status}: {raw}")
    if not raw.strip():
        return {}
    return json.loads(raw)


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


def fetch_status(url: str, timeout: float = 2.0) -> int | None:
    request = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except (OSError, urllib.error.URLError):
        return None
