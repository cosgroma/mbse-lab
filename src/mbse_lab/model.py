"""Service operations used by the first-model workflow."""

from __future__ import annotations

import urllib.parse
import uuid

import click

from mbse_lab.http import graphql, request_json, trim_url


def create_flexo_project(flexo_url: str, name: str, timeout: int) -> dict[str, object]:
    project = request_json(
        "POST",
        f"{trim_url(flexo_url)}/projects",
        {
            "@type": "Project",
            "name": name,
            "description": "Created by mbse-lab first-model",
        },
        timeout=timeout,
        expected={200, 201},
    )
    if not isinstance(project, dict):
        raise click.ClickException("Flexo project creation returned a non-object response")
    return project


def commit_flexo_package(
    flexo_url: str, project_id: str, package_id: str, package_name: str, timeout: int
) -> dict[str, object]:
    commit = request_json(
        "POST",
        f"{trim_url(flexo_url)}/projects/{urllib.parse.quote(project_id)}/commits",
        {
            "@type": "Commit",
            "description": "Create first package from mbse-lab",
            "change": [
                {
                    "@type": "DataVersion",
                    "identity": None,
                    "payload": {
                        "@id": package_id,
                        "@type": "Package",
                        "declaredName": package_name,
                    },
                }
            ],
        },
        timeout=timeout,
        expected={200, 201},
    )
    if not isinstance(commit, dict):
        raise click.ClickException("Flexo commit returned a non-object response")
    return commit


def create_syson_project(syson_url: str, name: str, timeout: int) -> dict[str, object]:
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
    response = graphql(
        syson_url,
        mutation,
        {
            "input": {
                "id": str(uuid.uuid4()),
                "name": name,
                "templateId": "sysmlv2-template",
                "libraryIds": [],
            }
        },
        timeout=timeout,
    )
    data = response["data"]
    if not isinstance(data, dict):
        raise click.ClickException("SysON GraphQL response missing data object")
    result = data["createProject"]
    if not isinstance(result, dict):
        raise click.ClickException("SysON createProject response was not an object")
    if result["__typename"] == "ErrorPayload":
        raise click.ClickException(str(result["message"]))
    project = result["project"]
    if not isinstance(project, dict):
        raise click.ClickException("SysON project response was not an object")
    return project


def syson_latest_commit_id(syson_url: str, project_id: str, timeout: int) -> str:
    commits = request_json(
        "GET",
        f"{trim_url(syson_url)}/api/rest/projects/{urllib.parse.quote(project_id)}/commits",
        timeout=timeout,
    )
    if not isinstance(commits, list) or not commits:
        raise click.ClickException(f"SysON project has no REST commits: {project_id}")
    latest_commit = commits[-1]
    if not isinstance(latest_commit, dict) or "@id" not in latest_commit:
        raise click.ClickException(f"SysON latest commit was malformed for project {project_id}")
    return str(latest_commit["@id"])


def syson_root_package_id(syson_url: str, project_id: str, commit_id: str, timeout: int) -> str:
    roots = request_json(
        "GET",
        (
            f"{trim_url(syson_url)}/api/rest/projects/{urllib.parse.quote(project_id)}"
            f"/commits/{urllib.parse.quote(commit_id)}/roots"
        ),
        timeout=timeout,
    )
    if not isinstance(roots, list):
        raise click.ClickException(f"SysON roots response was not a list for project {project_id}")
    for root in roots:
        if isinstance(root, dict) and root.get("@type") == "Package":
            return str(root["@id"])
    raise click.ClickException(f"no root Package found in SysON project {project_id}")


def import_sysml_text(
    syson_url: str,
    namespace_id: str,
    editing_context_id: str,
    textual_content: str,
    timeout: int,
) -> dict[str, object]:
    mutation = """
    mutation InsertTextualSysMLv2($input: InsertTextualSysMLv2Input!) {
      insertTextualSysMLv2(input: $input) {
        __typename
        ... on SuccessPayload { id }
        ... on ErrorPayload { message }
      }
    }
    """
    response = graphql(
        syson_url,
        mutation,
        {
            "input": {
                "id": str(uuid.uuid4()),
                "editingContextId": editing_context_id,
                "objectId": namespace_id,
                "textualContent": textual_content,
            }
        },
        timeout=timeout,
    )
    data = response["data"]
    if not isinstance(data, dict):
        raise click.ClickException("SysON GraphQL response missing data object")
    result = data["insertTextualSysMLv2"]
    if not isinstance(result, dict):
        raise click.ClickException("SysON import response was not an object")
    if result["__typename"] == "ErrorPayload":
        raise click.ClickException(str(result["message"]))
    return result
