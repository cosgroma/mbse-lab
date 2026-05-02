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


def report_path_label(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def latest_bridge_run_report(repo_root: Path) -> dict[str, object]:
    run_dir = repo_root / "runs" / "flexo-to-syson"
    run_logs = sorted(run_dir.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not run_logs:
        return {
            "latest_exists": False,
            "run_log": None,
            "status": "not-found",
            "artifacts": {},
            "render_summary": None,
            "import_status": None,
        }

    run_log = run_logs[0]
    try:
        record = json.loads(run_log.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "latest_exists": True,
            "run_log": report_path_label(run_log, repo_root),
            "status": "unreadable",
            "artifacts": {},
            "render_summary": None,
            "import_status": None,
            "error": f"could not parse run log: {exc}",
        }

    artifacts = record.get("artifacts", {}) if isinstance(record, dict) else {}
    safe_artifacts: dict[str, str] = {}
    if isinstance(artifacts, dict):
        for name, raw_path in artifacts.items():
            if isinstance(raw_path, str):
                artifact_path = Path(raw_path)
                if not artifact_path.is_absolute():
                    artifact_path = repo_root / artifact_path
                safe_artifacts[str(name)] = report_path_label(artifact_path, repo_root)

    import_status = None
    steps = record.get("steps", []) if isinstance(record, dict) else []
    if isinstance(steps, list):
        for step in steps:
            if isinstance(step, dict) and step.get("name") == "import-syson":
                import_status = step.get("status")

    render_summary = None
    render_report_path = safe_artifacts.get("render_report")
    if render_report_path:
        raw_render_report_path = Path(str(artifacts.get("render_report"))) if isinstance(artifacts, dict) else None
        candidate = (
            raw_render_report_path
            if raw_render_report_path and raw_render_report_path.is_absolute()
            else repo_root / render_report_path
        )
        if candidate.exists():
            try:
                render_report = json.loads(candidate.read_text(encoding="utf-8"))
                if isinstance(render_report, dict) and isinstance(render_report.get("summary"), dict):
                    render_summary = render_report["summary"]
            except json.JSONDecodeError:
                render_summary = {"status": "unreadable"}

    return {
        "latest_exists": True,
        "run_log": report_path_label(run_log, repo_root),
        "status": record.get("status", "unknown") if isinstance(record, dict) else "unknown",
        "artifacts": safe_artifacts,
        "render_summary": render_summary,
        "import_status": import_status,
    }


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
        "bridge": latest_bridge_run_report(repo_root),
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
    bridge = data["bridge"] if isinstance(data.get("bridge"), dict) else {}
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
    lines.extend(["", "## Bridge Evidence", ""])
    if bridge.get("latest_exists"):
        lines.append(f"- Latest run log: `{bridge.get('run_log')}`")
        lines.append(f"- Workflow status: `{bridge.get('status', 'unknown')}`")
        if bridge.get("import_status") is not None:
            lines.append(f"- SysON import step: `{bridge.get('import_status')}`")
        artifacts = bridge.get("artifacts", {})
        if isinstance(artifacts, dict) and artifacts:
            for name, path in sorted(artifacts.items()):
                lines.append(f"- Artifact `{name}`: `{path}`")
        render_summary = bridge.get("render_summary")
        if isinstance(render_summary, dict):
            lines.append(
                "- Render coverage: "
                f"`{render_summary.get('rendered_elements', 'unknown')}` rendered, "
                f"`{render_summary.get('skipped_elements', 'unknown')}` skipped, "
                f"`{render_summary.get('unsupported_elements', 'unknown')}` unsupported"
            )
    else:
        lines.append("- Latest bridge run: not found")
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
