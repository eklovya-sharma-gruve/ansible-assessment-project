#!/usr/bin/env python3
"""
Git/SCM content inspector for the Gruve AAP assessment.

Given a list of project SCM URLs, shallow-clones each repo (read-only) into a
workspace and inspects it for:
  - Content quality: roles, collections, standalone playbooks, meta/ presence
  - Reuse signal: duplicate role names across repos
  - Standards: presence of naming/structure conventions (ansible.cfg, meta/main.yml)
  - Plaintext-secret scan: regex hits for unvaulted secrets / private keys
  - CI & testing evidence: ansible-lint, yamllint, molecule, pipeline files
  - Config-as-code: controller config files (e.g. infra.aap_configuration vars)

Outputs a single JSON object to stdout. Designed to run inside an execution
environment. Uses only the Python stdlib plus the `git` binary.

Security notes:
  - Clones are shallow (depth 1) and never executed.
  - Secret matches report file + line + pattern name only — NEVER the secret value.
  - The workspace is removed at the end.
"""
from __future__ import annotations
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter


def clone(url: str, dest: str, depth: int, username: str = "", token: str = "") -> tuple[bool, str]:
    auth_url = url
    if token and url.startswith("https://"):
        # inject read-only creds without logging them
        cred = token if not username else f"{username}:{token}"
        auth_url = url.replace("https://", f"https://{cred}@", 1)
    try:
        subprocess.run(
            ["git", "clone", "--depth", str(depth), "--quiet", auth_url, dest],
            check=True, capture_output=True, timeout=120,
        )
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, "clone failed"
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:80]


def inspect_repo(path: str, secret_patterns: list[str]) -> dict:
    roles, collections, playbooks = set(), set(), []
    has_meta = has_molecule = has_lint = has_yamllint = has_ci = has_cac = False
    role_names = set()
    secret_hits = []
    file_count = 0

    compiled = [(p, re.compile(p)) for p in secret_patterns]

    for root, dirs, files in os.walk(path):
        # skip .git
        if ".git" in dirs:
            dirs.remove(".git")
        rel_root = os.path.relpath(root, path)
        parts = rel_root.split(os.sep)

        if "roles" in parts:
            # the dir directly under roles/ is a role name
            idx = parts.index("roles")
            if len(parts) > idx + 1:
                role_names.add(parts[idx + 1])
                roles.add(parts[idx + 1])
        if "molecule" in parts:
            has_molecule = True
        if "collections" in parts or "ansible_collections" in parts:
            collections.add(rel_root)

        for fn in files:
            file_count += 1
            low = fn.lower()
            fpath = os.path.join(root, fn)
            if fn == "meta" or fn == "main.yml" and "meta" in parts:
                has_meta = True
            if low in (".ansible-lint", "ansible-lint.yml"):
                has_lint = True
            if low in (".yamllint", ".yamllint.yml", ".yamllint.yaml"):
                has_yamllint = True
            if low in (".gitlab-ci.yml",) or ".github" in parts or low.endswith("azure-pipelines.yml") \
               or "workflows" in parts or fn == "Jenkinsfile":
                has_ci = True
            if low.endswith((".yml", ".yaml")) and ("controller" in low or "aap_config" in low or "configuration" in low):
                has_cac = True
            if low.endswith((".yml", ".yaml")) and "playbook" in low:
                playbooks.append(fn)

            # secret scan — text files only, cap size
            if low.endswith((".yml", ".yaml", ".json", ".ini", ".cfg", ".env", ".sh", ".txt", ".pem", ".key")):
                try:
                    if os.path.getsize(fpath) > 512 * 1024:
                        continue
                    with open(fpath, "r", errors="ignore") as fh:
                        for lineno, line in enumerate(fh, 1):
                            # skip lines already vaulted
                            if "!vault" in line or line.strip().startswith("#"):
                                continue
                            for pname, rx in compiled:
                                if rx.search(line):
                                    secret_hits.append({
                                        "file": os.path.relpath(fpath, path),
                                        "line": lineno,
                                        "pattern": pname[:40],
                                    })
                                    break
                except Exception:  # noqa: BLE001
                    pass

    return {
        "file_count": file_count,
        "role_count": len(roles),
        "role_names": sorted(role_names),
        "collection_dirs": len(collections),
        "standalone_playbooks": len(playbooks),
        "has_meta": has_meta,
        "has_molecule": has_molecule,
        "has_ansible_lint": has_lint,
        "has_yamllint": has_yamllint,
        "has_ci_pipeline": has_ci,
        "has_config_as_code": has_cac,
        "secret_hit_count": len(secret_hits),
        "secret_hits": secret_hits[:50],  # cap
    }


def main():
    cfg = json.load(sys.stdin)
    projects = cfg.get("projects", [])
    workspace = cfg.get("workspace", tempfile.mkdtemp(prefix="gruve_lld_"))
    depth = int(cfg.get("depth", 1))
    username = cfg.get("username", "")
    token = cfg.get("token", "")
    max_repos = int(cfg.get("max_repos", 25))
    patterns = cfg.get("secret_patterns", [])

    os.makedirs(workspace, exist_ok=True)
    repo_results = []
    all_role_names = Counter()
    totals = {"repos_cloned": 0, "repos_failed": 0, "secret_hits": 0,
              "repos_with_molecule": 0, "repos_with_lint": 0, "repos_with_ci": 0,
              "repos_with_roles": 0, "repos_with_cac": 0}

    for p in projects[:max_repos]:
        url = p.get("scm_url", "")
        name = p.get("name", "repo")
        if not url or not url.startswith(("http", "git@", "ssh://", "file://")):
            continue
        dest = os.path.join(workspace, re.sub(r"[^A-Za-z0-9_.-]", "_", name))
        ok, err = clone(url, dest, depth, username, token)
        if not ok:
            totals["repos_failed"] += 1
            repo_results.append({"name": name, "clone_ok": False, "error": err})
            continue
        totals["repos_cloned"] += 1
        info = inspect_repo(dest, patterns)
        info["name"] = name
        info["clone_ok"] = True
        repo_results.append(info)
        for rn in info["role_names"]:
            all_role_names[rn] += 1
        totals["secret_hits"] += info["secret_hit_count"]
        totals["repos_with_molecule"] += 1 if info["has_molecule"] else 0
        totals["repos_with_lint"] += 1 if (info["has_ansible_lint"] or info["has_yamllint"]) else 0
        totals["repos_with_ci"] += 1 if info["has_ci_pipeline"] else 0
        totals["repos_with_roles"] += 1 if info["role_count"] > 0 else 0
        totals["repos_with_cac"] += 1 if info["has_config_as_code"] else 0

    # reuse signal: role names appearing in >1 repo (duplication / copy-paste)
    duplicated_roles = {n: c for n, c in all_role_names.items() if c > 1}

    out = {
        "totals": totals,
        "duplicated_role_count": len(duplicated_roles),
        "duplicated_roles": dict(sorted(duplicated_roles.items(), key=lambda x: -x[1])[:20]),
        "repos": repo_results,
    }
    print(json.dumps(out))

    # cleanup
    try:
        shutil.rmtree(workspace, ignore_errors=True)
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    main()
