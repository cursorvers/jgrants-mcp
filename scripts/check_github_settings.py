#!/usr/bin/env python3
"""Verify that the repository-level GitHub settings match the documented guardrails."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Iterable

import requests

API_BASE = "https://api.github.com"

REQUIRED_ACTIONS = [
    "actions/checkout@08eba0b27e820071cde6df949e0beb9ba4906955",
    "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
    "actions/cache@6f8efc29b200d32929f49075959781ed54ec270c",
    "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    "actions/download-artifact@9bc31d5ccc31df68ecc42ccf4149144866c47d8a",
    "docker/login-action@465a07811f14bebb1938fbed4728c6a1ff8901fc",
    "docker/setup-buildx-action@885d1462b80bc1c1c7f0b00334ad271f09369c55",
    "docker/build-push-action@ca052bb54ab0790a636c9b5f226502c73d547a25",
    "sigstore/cosign-installer@c85d0e205a72a294fe064f618a87dbac13084086",
    "github/codeql-action/init@8dca8a82e2fa1a2c8908956f711300f9c4a4f4f6",
    "github/codeql-action/analyze@8dca8a82e2fa1a2c8908956f711300f9c4a4f4f6",
    "actions/dependency-review-action@93809e13f07c0db8c2db3c320885d98f2d235acc",
]

REQUIRED_ENVIRONMENTS = ["dev", "stg", "prod"]
REQUIRED_STATUS_CHECKS = ["CI (unit)", "Security / CodeQL", "Dependency Review"]


def _request(session: requests.Session, path: str) -> dict | list:
    resp = session.get(f"{API_BASE}{path}")
    if resp.status_code == 404:
        raise RuntimeError(f"Resource not found: {path}")
    resp.raise_for_status()
    return resp.json()


def _print_check(title: str, ok: bool, details: str | None = None) -> None:
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {title}")
    if details:
        print(f"      {details}")


def check_actions_permissions(session: requests.Session, repo: str) -> bool:
    data = _request(session, f"/repos/{repo}/actions/permissions")
    allowed = data.get("allowed_actions")
    selected = set(data.get("selected_actions") or [])
    ok = allowed == "selected" and selected.issuperset(REQUIRED_ACTIONS)
    missing = [x for x in REQUIRED_ACTIONS if x not in selected]
    details = (
        "missing: " + ", ".join(missing)
        if missing
        else "selected-actions allowlist is complete"
    )
    _print_check("Actions permissions (allowlist + read-only default)", ok, details)
    return ok


def check_environments(session: requests.Session, repo: str) -> bool:
    data = _request(session, f"/repos/{repo}/environments")
    names = {env["name"] for env in data.get("environments", [])}
    missing = [env for env in REQUIRED_ENVIRONMENTS if env not in names]
    ok = not missing
    details = (
        "missing: " + ", ".join(missing)
        if missing
        else "all expected environments exist"
    )
    _print_check("Environments existence", ok, details)
    return ok


def check_branch_protection(session: requests.Session, repo: str) -> bool:
    data = _request(session, f"/repos/{repo}/branches/main/protection")
    status_checks = data.get("required_status_checks", {}).get("contexts", [])
    missing_checks = [c for c in REQUIRED_STATUS_CHECKS if c not in status_checks]
    reviews = data.get("required_pull_request_reviews", {})
    reviews_ok = reviews.get("required_approving_review_count", 0) >= 1
    up_to_date = data.get("required_status_checks", {}).get("strict", False)
    ok = not missing_checks and reviews_ok and up_to_date
    details_parts = []
    if missing_checks:
        details_parts.append("missing checks: " + ", ".join(missing_checks))
    if not reviews_ok:
        details_parts.append("require at least 1 approving review")
    if not up_to_date:
        details_parts.append("branch must be up to date before merging")
    details = "; ".join(details_parts) if details_parts else "all branch protection safeguards applied"
    _print_check("Branch protection (main)", ok, details)
    return ok


def check_secret_scanning(session: requests.Session, repo: str) -> bool:
    data = _request(session, f"/repos/{repo}/secret-scanning" )
    status = data.get("status")
    ok = status == "enabled"
    details = "enabled" if ok else "secret scanning push protection not enabled"
    _print_check("Secret scanning push protection", ok, details)
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPOSITORY", "cursorvers/jgrants-mcp"),
        help="Repository in OWNER/NAME format",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"),
        help="GitHub token with repo scope (defaults to GITHUB_TOKEN)",
    )
    args = parser.parse_args()

    if not args.token:
        print("ERROR: provide a GitHub token via --token or GITHUB_TOKEN", file=sys.stderr)
        sys.exit(1)

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {args.token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "jgrants-mcp-settings-check/1.0",
    })

    print("Checking GitHub repository settings for", args.repo)
    results: list[bool] = []
    for check in (
        check_actions_permissions,
        check_environments,
        check_branch_protection,
        check_secret_scanning,
    ):
        try:
            results.append(check(session, args.repo))
        except RuntimeError as err:
            print(f"[FAIL] {check.__name__}: {err}")
            results.append(False)
    overall = all(results)
    print(f"Summary: {'PASS' if overall else 'FAIL'}")
    if not overall:
        sys.exit(2)


if __name__ == "__main__":
    main()
