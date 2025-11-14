#!/usr/bin/env python3
"""GitHub Settings の状態を検証するスクリプト"""

import argparse
import os
import sys
from typing import Any

import requests


def get_github_token() -> str:
    """環境変数から GitHub token を取得"""
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN or GH_TOKEN environment variable is required", file=sys.stderr)
        sys.exit(1)
    return token


def api_request(token: str, endpoint: str) -> dict[str, Any]:
    """GitHub API リクエストを実行"""
    url = f"https://api.github.com/repos/{endpoint}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def check_actions_permissions(token: str, repo: str) -> dict[str, Any]:
    """Actions permissions を確認"""
    try:
        data = api_request(token, f"{repo}/actions/permissions")
        return {
            "enabled": data.get("enabled", False),
            "allowed_actions": data.get("allowed_actions", "unknown"),
            "sha_pinning_required": data.get("sha_pinning_required", False),
        }
    except Exception as e:
        return {"error": str(e)}


def check_selected_actions(token: str, repo: str) -> dict[str, Any]:
    """Selected actions を確認"""
    try:
        data = api_request(token, f"{repo}/actions/permissions/selected-actions")
        return {
            "github_owned_allowed": data.get("github_owned_allowed", False),
            "verified_allowed": data.get("verified_allowed", False),
            "patterns_allowed": data.get("patterns_allowed", []),
        }
    except Exception as e:
        return {"error": str(e)}


def check_environments(token: str, repo: str) -> list[dict[str, Any]]:
    """Environments を確認"""
    try:
        data = api_request(token, f"{repo}/environments")
        return [
            {
                "name": env.get("name"),
                "protection_rules": len(env.get("protection_rules", [])),
                "can_admins_bypass": env.get("can_admins_bypass", False),
            }
            for env in data.get("environments", [])
        ]
    except Exception as e:
        return [{"error": str(e)}]


def check_vulnerability_alerts(token: str, repo: str) -> dict[str, Any]:
    """Vulnerability alerts を確認"""
    try:
        response = requests.get(
            f"https://api.github.com/repos/{repo}/vulnerability-alerts",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.dorian-preview+json",
            },
        )
        return {"enabled": response.status_code == 204}
    except Exception as e:
        return {"error": str(e)}


def check_automated_security_fixes(token: str, repo: str) -> dict[str, Any]:
    """Automated security fixes を確認"""
    try:
        response = requests.get(
            f"https://api.github.com/repos/{repo}/automated-security-fixes",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.london-preview+json",
            },
        )
        return {"enabled": response.status_code == 204}
    except Exception as e:
        return {"error": str(e)}


def check_branch_protection(token: str, repo: str, branch: str = "main") -> dict[str, Any]:
    """Branch protection を確認"""
    try:
        data = api_request(token, f"{repo}/branches/{branch}/protection")
        return {
            "required_status_checks": data.get("required_status_checks", {}),
            "enforce_admins": data.get("enforce_admins", {}),
            "required_pull_request_reviews": data.get("required_pull_request_reviews", {}),
        }
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"enabled": False, "message": "Branch protection not configured"}
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check GitHub repository settings"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository in format owner/repo"
    )
    args = parser.parse_args()

    token = get_github_token()

    print(f"Checking GitHub Settings for: {args.repo}\n")
    print("=" * 60)

    # Actions permissions
    print("\n[1] Actions Permissions:")
    actions_perms = check_actions_permissions(token, args.repo)
    if "error" in actions_perms:
        print(f"  ERROR: {actions_perms['error']}")
    else:
        print(f"  Enabled: {actions_perms['enabled']}")
        print(f"  Allowed actions: {actions_perms['allowed_actions']}")
        print(f"  SHA pinning required: {actions_perms['sha_pinning_required']}")

    # Selected actions
    print("\n[2] Selected Actions:")
    selected = check_selected_actions(token, args.repo)
    if "error" in selected:
        print(f"  ERROR: {selected['error']}")
    else:
        print(f"  GitHub owned allowed: {selected['github_owned_allowed']}")
        print(f"  Verified allowed: {selected['verified_allowed']}")
        print(f"  Patterns allowed: {len(selected.get('patterns_allowed', []))}")

    # Environments
    print("\n[3] Environments:")
    envs = check_environments(token, args.repo)
    if envs and "error" in envs[0]:
        print(f"  ERROR: {envs[0]['error']}")
    else:
        for env in envs:
            name = env['name']
            rules_count = env['protection_rules']
            admin_bypass = env['can_admins_bypass']
            print(
                f"  - {name}: {rules_count} protection rules, "
                f"admin bypass: {admin_bypass}"
            )

    # Vulnerability alerts
    print("\n[4] Vulnerability Alerts:")
    vuln_alerts = check_vulnerability_alerts(token, args.repo)
    if "error" in vuln_alerts:
        print(f"  ERROR: {vuln_alerts['error']}")
    else:
        print(f"  Enabled: {vuln_alerts['enabled']}")

    # Automated security fixes
    print("\n[5] Automated Security Fixes:")
    auto_fixes = check_automated_security_fixes(token, args.repo)
    if "error" in auto_fixes:
        print(f"  ERROR: {auto_fixes['error']}")
    else:
        print(f"  Enabled: {auto_fixes['enabled']}")

    # Branch protection
    print("\n[6] Branch Protection (main):")
    branch_prot = check_branch_protection(token, args.repo, "main")
    if "error" in branch_prot:
        print(f"  ERROR: {branch_prot['error']}")
    elif "enabled" in branch_prot and not branch_prot["enabled"]:
        print(f"  {branch_prot.get('message', 'Not configured')}")
    else:
        print(f"  Required status checks: {branch_prot.get('required_status_checks', {})}")
        print(f"  Required PR reviews: {branch_prot.get('required_pull_request_reviews', {})}")

    print("\n" + "=" * 60)
    print("Check completed!")


if __name__ == "__main__":
    main()

