#!/usr/bin/env python3
"""Resolve the Together Optimized Modrinth project id (base62).

Prefers a direct slug lookup, then falls back to the authenticated user's
owned projects (needed for draft/unlisted projects that 404 publicly).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

SLUG = "together-optimized"
TITLE = "together optimized"
UA = "together-optimized-ci (github.com/College-Debt-SMP/together-optimized)"
API = "https://api.modrinth.com/v2"


def request(path: str, token: str) -> tuple[int, object]:
    req = urllib.request.Request(
        f"{API}{path}",
        headers={
            "Authorization": token,
            "User-Agent": UA,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = body
        return exc.code, payload


def main() -> int:
    token = os.environ.get("MODRINTH_TOKEN", "").strip()
    if not token:
        print("MODRINTH_TOKEN is not set", file=sys.stderr)
        return 1

    status, payload = request(f"/project/{SLUG}", token)
    if status == 200 and isinstance(payload, dict) and payload.get("id"):
        print(payload["id"])
        return 0

    print(f"Direct project lookup HTTP {status}; searching owned projects...", file=sys.stderr)
    status, user = request("/user", token)
    if status != 200 or not isinstance(user, dict):
        print(f"Failed to resolve Modrinth user (HTTP {status}): {payload}", file=sys.stderr)
        return 1

    user_id = user["id"]
    print(f"Authenticated Modrinth user id: {user_id}", file=sys.stderr)
    status, projects = request(f"/user/{user_id}/projects", token)
    if status != 200 or not isinstance(projects, list):
        print(f"Failed to list projects (HTTP {status}): {projects}", file=sys.stderr)
        return 1

    for project in projects:
        if project.get("slug") == SLUG or project.get("title", "").lower() == TITLE:
            print(project["id"])
            return 0

    print("Owned projects:", file=sys.stderr)
    for project in projects:
        print(
            "  {id} slug={slug} title={title} type={ptype} status={status}".format(
                id=project.get("id"),
                slug=project.get("slug"),
                title=project.get("title"),
                ptype=project.get("project_type"),
                status=project.get("status"),
            ),
            file=sys.stderr,
        )
    print(f"Could not find project slug={SLUG}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
