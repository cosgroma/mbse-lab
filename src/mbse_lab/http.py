"""HTTP and GraphQL helpers for the MBSE lab CLI."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

import click


def trim_url(url: str) -> str:
    return url.rstrip("/")


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


def fetch_status(url: str, timeout: float = 2.0) -> int | None:
    request = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except (OSError, urllib.error.URLError):
        return None
