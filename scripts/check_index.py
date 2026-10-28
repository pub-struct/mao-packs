#!/usr/bin/env python3
"""Check packs.toml, and the entries a pull request adds or changes.

Usage: check_index.py <packs.toml> [<base packs.toml>] [--fetch]

Without a base, every entry is checked as new. With --fetch, each new or changed
entry's pinned commit is fetched anonymously and its mao-pack.toml must name the
same id and version as the entry.
"""

import os
import re
import subprocess
import sys
import tempfile
import tomllib

COMMIT = re.compile(r"^[0-9a-f]{40}$")
ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}/[a-z0-9][a-z0-9_-]{0,63}$")
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$")
KEYS = {"id", "repo", "path", "version", "commit", "title", "description"}
REQUIRED = {"id", "version", "commit"}


def version_key(text):
    match = SEMVER.match(text)
    major, minor, patch, pre = match.groups()
    # A pre-release sorts before its release.
    pre_key = (0, [(0, int(p)) if p.isdigit() else (1, p) for p in pre.split(".")]) if pre else (1, [])
    return (int(major), int(minor), int(patch), pre_key)


def load(path):
    with open(path, "rb") as file:
        table = tomllib.load(file)
    version = table.get("schema_version", 1)
    if not isinstance(version, int) or version < 1 or version > 1:
        raise SystemExit(f"{path}: schema_version must be 1")
    packs = table.get("pack", [])
    if not isinstance(packs, list):
        raise SystemExit(f"{path}: [[pack]] must be an array of tables")
    return packs


def check_entry(entry, errors):
    where = entry.get("id", "<no id>")
    unknown = set(entry) - KEYS
    if unknown:
        errors.append(f"{where}: unknown keys {sorted(unknown)}")
    missing = REQUIRED - set(entry)
    if missing:
        errors.append(f"{where}: missing {sorted(missing)}")
        return False
    ok = True
    if not ID.match(str(entry["id"])):
        errors.append(f"{where}: id must look like publisher/name, lowercase")
        ok = False
    if not SEMVER.match(str(entry["version"])):
        errors.append(f"{where}: version {entry['version']!r} is not semantic")
        ok = False
    if not COMMIT.match(str(entry["commit"])):
        errors.append(f"{where}: commit must be 40 lowercase hex digits")
        ok = False
    repo = entry.get("repo", ".")
    if repo != "." and not str(repo).startswith("https://github.com/"):
        errors.append(f"{where}: repo must be https://github.com/... or \".\"")
        ok = False
    path = str(entry.get("path", "."))
    if path.startswith("/") or ".." in path.split("/"):
        errors.append(f"{where}: path must stay inside the repository")
        ok = False
    return ok


def fetch_manifest(entry):
    repo = entry.get("repo", ".")
    url = os.environ.get("GITHUB_SERVER_URL", "https://github.com") + "/" + os.environ.get(
        "GITHUB_REPOSITORY", "pub-struct/mao-packs") if repo == "." else repo
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null")
    with tempfile.TemporaryDirectory() as scratch:
        run = lambda *args: subprocess.run(["git", "-C", scratch, *args], env=env, check=True,
                                           capture_output=True, text=True, timeout=300)
        run("init", "-q", "--bare")
        run("-c", "credential.helper=", "fetch", "-q", "--depth=1", url, entry["commit"])
        manifest = os.path.join(entry.get("path", "."), "mao-pack.toml").removeprefix("./")
        text = run("show", f"{entry['commit']}:{manifest}").stdout
    return tomllib.loads(text)


def main(argv):
    fetch = "--fetch" in argv
    args = [a for a in argv if a != "--fetch"]
    if not args:
        raise SystemExit(__doc__)
    head = load(args[0])
    base = load(args[1]) if len(args) > 1 and os.path.exists(args[1]) else []

    errors = []
    seen = set()
    for entry in head:
        check_entry(entry, errors)
        key = (entry.get("id"), entry.get("version"))
        if key in seen:
            errors.append(f"{key[0]}: version {key[1]} is listed twice")
        seen.add(key)

    base_by_key = {(e.get("id"), e.get("version")): e for e in base}
    head_by_key = {(e.get("id"), e.get("version")): e for e in head}
    for key, old in base_by_key.items():
        new = head_by_key.get(key)
        if new is not None and new != old:
            errors.append(f"{key[0]}: version {key[1]} is already listed and is never edited; raise the version")

    added = [e for k, e in head_by_key.items() if k not in base_by_key]
    for entry in added:
        if not SEMVER.match(str(entry.get("version", ""))):
            continue
        earlier = [e["version"] for e in base if e.get("id") == entry.get("id") and SEMVER.match(str(e.get("version", "")))]
        if earlier and version_key(entry["version"]) <= max(version_key(v) for v in earlier):
            errors.append(f"{entry['id']}: version {entry['version']} must be higher than {max(earlier, key=version_key)}")

    if fetch and not errors:
        for entry in added:
            try:
                manifest = fetch_manifest(entry)
            except subprocess.CalledProcessError as error:
                errors.append(f"{entry['id']}: could not fetch {entry['commit']} anonymously "
                              f"(the repository must be public): {error.stderr.strip()[:300]}")
                continue
            except (KeyError, tomllib.TOMLDecodeError) as error:
                errors.append(f"{entry['id']}: mao-pack.toml could not be read: {error}")
                continue
            pack = manifest
            for field in ("id", "version"):
                if str(pack.get(field)) != str(entry[field]):
                    errors.append(f"{entry['id']}: mao-pack.toml says {field} = {pack.get(field)!r}, the entry says {entry[field]!r}")
            print(f"ok: {entry['id']} {entry['version']} at {entry['commit'][:12]}")

    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"packs.toml: {len(head)} entries, {len(added)} new, all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
