from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class EvidenceError(RuntimeError):
    """Sonar evidence is incomplete, contradictory, or materially negative."""


def classify_sonar_evidence(
    *,
    check: dict[str, object],
    quality: dict[str, object],
    issues: dict[str, object],
) -> str:
    """Classify exact-head Sonar evidence without converting absence into PASS."""

    status = check.get("status")
    conclusion = check.get("conclusion")
    annotations = _exact_non_negative_int(
        check.get("annotations_count"), "check.annotations_count"
    )
    if status != "completed":
        raise EvidenceError(f"Sonar check status is {status!r}, expected 'completed'")
    if annotations != 0:
        raise EvidenceError(f"Sonar check reports {annotations} material annotations")

    quality_http = _exact_http_status(quality.get("http_status"), "quality.http_status")
    quality_status = quality.get("status")
    if quality_status is not None and type(quality_status) is not str:
        raise EvidenceError("quality.status must be a string or null")

    issues_http = _exact_http_status(issues.get("http_status"), "issues.http_status")
    issue_total = issues.get("total")
    if issues_http == 200:
        issue_total = _exact_non_negative_int(issue_total, "issues.total")
        if issue_total != 0:
            raise EvidenceError(f"Sonar reports {issue_total} unresolved pull-request issues")
    elif issues_http == 404:
        if issue_total is not None:
            raise EvidenceError("issues.total must be null when the issues API returns 404")
    else:
        raise EvidenceError(f"Sonar issues API returned unexpected HTTP {issues_http}")

    if conclusion == "success":
        if quality_http != 200 or quality_status != "OK":
            raise EvidenceError(
                "successful Sonar check lacks an explicit OK quality-gate result"
            )
        if issues_http != 200 or issue_total != 0:
            raise EvidenceError(
                "successful Sonar check lacks an explicit zero-issue result"
            )
        return "PASS"

    if conclusion == "cancelled":
        if quality_http == 404 and issues_http in (200, 404):
            return "NOT_COMPUTED_EXTERNAL"
        raise EvidenceError(
            "cancelled Sonar check is accepted only when the quality-gate object is absent"
        )

    raise EvidenceError(f"Sonar check conclusion is {conclusion!r}, expected success or cancelled")


def main() -> int:
    repository = _required_env("REPOSITORY")
    head = _required_env("EXACT_HEAD")
    pull_request = _required_env("PR_NUMBER")
    project = _required_env("SONAR_PROJECT")
    token = _required_env("GH_TOKEN")
    allow_not_computed = os.environ.get("ALLOW_NOT_COMPUTED_EXTERNAL") == "true"

    check = _wait_for_exact_head_check(repository, head, token)
    quality_url = "https://sonarcloud.io/api/qualitygates/project_status?" + urllib.parse.urlencode(
        {"projectKey": project, "pullRequest": pull_request}
    )
    issues_url = "https://sonarcloud.io/api/issues/search?" + urllib.parse.urlencode(
        {
            "componentKeys": project,
            "pullRequest": pull_request,
            "resolved": "false",
            "ps": "100",
        }
    )

    quality_http, quality_payload = _try_get_json(quality_url)
    issues_http, issues_payload = _try_get_json(issues_url)
    quality = {
        "http_status": quality_http,
        "status": _quality_status(quality_payload),
    }
    issues = {
        "http_status": issues_http,
        "total": _issue_total(issues_payload),
        "keys": _issue_keys(issues_payload),
    }

    state = classify_sonar_evidence(check=check, quality=quality, issues=issues)
    evidence = {
        "state": state,
        "check": check,
        "quality": quality,
        "issues": issues,
    }
    print("SONAR_EVIDENCE=" + json.dumps(evidence, sort_keys=True))
    _append_step_summary(evidence)

    if state == "NOT_COMPUTED_EXTERNAL" and not allow_not_computed:
        raise EvidenceError(
            "Sonar evidence is NOT_COMPUTED_EXTERNAL and no explicit waiver was provided"
        )
    return 0


def _wait_for_exact_head_check(
    repository: str,
    head: str,
    token: str,
) -> dict[str, object]:
    url = (
        f"https://api.github.com/repos/{repository}/commits/{head}/check-runs"
        "?check_name=SonarCloud%20Code%20Analysis&per_page=100"
    )
    for _ in range(30):
        payload = _get_json(url, github_token=token)
        candidates = [
            item
            for item in payload.get("check_runs", [])
            if item.get("name") == "SonarCloud Code Analysis"
            and item.get("head_sha") == head
        ]
        if candidates:
            candidate = candidates[-1]
            if candidate.get("status") == "completed":
                output = candidate.get("output")
                if type(output) is not dict:
                    raise EvidenceError("Sonar check output is not an object")
                return {
                    "id": candidate.get("id"),
                    "head_sha": candidate.get("head_sha"),
                    "status": candidate.get("status"),
                    "conclusion": candidate.get("conclusion"),
                    "annotations_count": output.get("annotations_count"),
                }
        time.sleep(10)
    raise EvidenceError("SonarCloud did not complete an exact-head check")


def _get_json(url: str, *, github_token: str | None = None) -> dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json" if github_token else "application/json",
        "User-Agent": "gitspace-task-011-evidence",
    }
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if type(payload) is not dict:
        raise EvidenceError(f"JSON response from {url} is not an object")
    return payload


def _try_get_json(url: str) -> tuple[int, dict[str, Any] | None]:
    try:
        return 200, _get_json(url)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return 404, None
        raise EvidenceError(f"Sonar API returned HTTP {error.code} for {url}") from error


def _quality_status(payload: dict[str, Any] | None) -> str | None:
    if payload is None:
        return None
    project_status = payload.get("projectStatus")
    if type(project_status) is not dict:
        raise EvidenceError("Sonar quality-gate payload lacks projectStatus")
    status = project_status.get("status")
    if type(status) is not str:
        raise EvidenceError("Sonar quality-gate payload lacks string status")
    return status


def _issue_total(payload: dict[str, Any] | None) -> int | None:
    if payload is None:
        return None
    return _exact_non_negative_int(payload.get("total"), "issues.total")


def _issue_keys(payload: dict[str, Any] | None) -> list[str]:
    if payload is None:
        return []
    issues = payload.get("issues")
    if type(issues) is not list:
        raise EvidenceError("Sonar issues payload lacks an issues array")
    keys: list[str] = []
    for item in issues:
        if type(item) is not dict or type(item.get("key")) is not str:
            raise EvidenceError("Sonar issue entry lacks a string key")
        keys.append(item["key"])
    return keys


def _exact_non_negative_int(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise EvidenceError(f"{label} must be an exact non-negative integer")
    return value


def _exact_http_status(value: object, label: str) -> int:
    status = _exact_non_negative_int(value, label)
    if status < 100 or status > 599:
        raise EvidenceError(f"{label} is outside the HTTP status range")
    return status


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise EvidenceError(f"missing required environment variable {name}")
    return value


def _append_step_summary(evidence: dict[str, object]) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    state = evidence["state"]
    check = evidence["check"]
    quality = evidence["quality"]
    issues = evidence["issues"]
    with open(path, "a", encoding="utf-8") as summary:
        summary.write("## Sonar evidence\n\n")
        summary.write(f"- State: `{state}`\n")
        summary.write(f"- Check: `{json.dumps(check, sort_keys=True)}`\n")
        summary.write(f"- Quality API: `{json.dumps(quality, sort_keys=True)}`\n")
        summary.write(f"- Issues API: `{json.dumps(issues, sort_keys=True)}`\n")


if __name__ == "__main__":
    raise SystemExit(main())
