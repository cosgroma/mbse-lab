"""Static reporting and generated-file cleanup helpers."""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import shutil
from pathlib import Path

import click

from mbse_lab.constants import CLEANUP_PATHS, DEFAULT_FLEXO_URL, DEFAULT_SYSON_URL, OPTIONAL_CLEANUP_PATHS
from mbse_lab.health import doctor_report, service_report
from mbse_lab.share import scan_share_issues


def report_data(repo_root: Path) -> dict[str, object]:
    workspace = os.environ.get("MBSE_MODEL_WORKSPACE")
    diagnostics_index = repo_root / "diagnostics" / "latest" / "index.md"
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "model_workspace": workspace,
        "service_urls": {
            "flexo_layer1": "http://localhost:18080",
            "flexo_sysmlv2": DEFAULT_FLEXO_URL,
            "syson_web": DEFAULT_SYSON_URL,
            "syson_graphql": f"{DEFAULT_SYSON_URL}/api/graphql",
        },
        "doctor": doctor_report(repo_root),
        "status": service_report(repo_root),
        "share_issues": scan_share_issues(repo_root),
        "diagnostics": {
            "latest_index": str(diagnostics_index.relative_to(repo_root)),
            "latest_exists": diagnostics_index.exists(),
        },
    }


def markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


def render_report_markdown(data: dict[str, object]) -> str:
    status = data["status"] if isinstance(data.get("status"), dict) else {}
    doctor = data["doctor"] if isinstance(data.get("doctor"), dict) else {}
    diagnostics = data["diagnostics"] if isinstance(data.get("diagnostics"), dict) else {}
    service_urls = data["service_urls"] if isinstance(data.get("service_urls"), dict) else {}

    containers = status.get("containers", []) if isinstance(status, dict) else []
    container_rows = []
    for container in containers if isinstance(containers, list) else []:
        if not isinstance(container, dict):
            continue
        container_rows.append(
            [
                str(container.get("name", "")),
                str(container.get("status", "")),
                str(container.get("health", "")),
                "yes" if container.get("running") else "no",
            ]
        )

    share_issues = data.get("share_issues", [])
    lines = [
        "# MBSE Lab Report",
        "",
        f"Generated: `{data.get('generated_at')}`",
        f"Repo root: `{data.get('repo_root')}`",
        f"Model workspace: `{data.get('model_workspace') or 'unset'}`",
        "",
        "## Summary",
        "",
        f"- Doctor: `{doctor.get('status', 'unknown') if isinstance(doctor, dict) else 'unknown'}`",
        f"- Services: `{status.get('status', 'unknown') if isinstance(status, dict) else 'unknown'}`",
        f"- Share issues: `{len(share_issues) if isinstance(share_issues, list) else 'unknown'}`",
        "",
        "## Service URLs",
        "",
    ]
    if isinstance(service_urls, dict):
        for label, url in service_urls.items():
            lines.append(f"- {label}: {url}")
    lines.extend(["", "## Containers", ""])
    lines.extend(markdown_table(["Container", "Status", "Health", "Running"], container_rows))
    lines.extend(["", "## Diagnostics", ""])
    if diagnostics.get("latest_exists"):
        lines.append(f"- Latest diagnostics: `{diagnostics.get('latest_index')}`")
    else:
        lines.append("- Latest diagnostics: not found")
    lines.extend(["", "## Share Check", ""])
    if isinstance(share_issues, list) and share_issues:
        lines.extend(f"- {issue}" for issue in share_issues)
    else:
        lines.append("- No share-check issues found.")
    return "\n".join(lines) + "\n"


def render_report_html(data: dict[str, object]) -> str:
    markdown = render_report_markdown(data)
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            "  <title>MBSE Lab Report</title>",
            "  <style>",
            "    body { font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; color: #202124; }",
            "    pre { background: #f6f8fa; padding: 1rem; overflow: auto; border: 1px solid #d0d7de; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <h1>MBSE Lab Report</h1>",
            "  <pre>",
            html.escape(markdown),
            "  </pre>",
            "</body>",
            "</html>",
            "",
        ]
    )


def write_report(output_dir: Path, data: dict[str, object]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "doctor.json").write_text(
        json.dumps(data["doctor"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "status.json").write_text(
        json.dumps(data["status"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "report.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "index.md").write_text(render_report_markdown(data), encoding="utf-8")
    (output_dir / "index.html").write_text(render_report_html(data), encoding="utf-8")


def cleanup_generated(repo_root: Path, include_site: bool, dry_run: bool) -> list[Path]:
    names = [*CLEANUP_PATHS]
    if include_site:
        names.extend(OPTIONAL_CLEANUP_PATHS)
    removed: list[Path] = []
    for name in names:
        path = repo_root / name
        if not path.exists():
            continue
        resolved = path.resolve()
        if repo_root.resolve() not in (resolved, *resolved.parents):
            raise click.ClickException(f"refusing to clean path outside repo: {path}")
        if dry_run:
            click.echo(f"dry-run: remove {path.relative_to(repo_root)}")
        elif path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        removed.append(path)
    return removed
