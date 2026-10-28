# MAO packs

The official registry of [MAO](https://github.com/pub-struct) packs. A pack shares arrangements, roles and agents (for example "Codex with our reviewer role") that anyone can install from the Packs tab in MAO or with `mao pack add <publisher>/<name>`.

This repository is an index. `packs.toml` lists packs, each pinned to one commit of the author's own repository. MAO fetches that commit, checks it on the person's machine, and shows a review before anything is installed. A custom command in a pack still needs the approval of the person installing it, and a pack never runs scripts at install.

## Publish a pack

1. **Create and check it.** Start the pack with `mao pack init`, then run `mao pack check <folder>` until it passes.
2. **Make it public.** Commit and push the pack to a public GitHub repository.
3. **Open the pull request.** Run `mao pack publish <folder> --dry-run` to see the entry, then `mao pack publish <folder>`. It forks this repository, adds one `[[pack]]` entry to the end of `packs.toml`, and opens the pull request with your own `gh`, only after you confirm. Writing the entry by hand is just as good.
4. **Wait for the check and the review.** The check below runs on the pull request. A maintainer then reviews the pack the way a person installing it would: its custom commands, every role's prompt and its portal addresses.
5. **Merging is publishing.** MAO lists the pack under Available on its next refresh, and offers new versions as updates.

An entry looks like this:

```toml
[[pack]]
id = "acme/review-team"
repo = "https://github.com/acme/mao-review-team"
path = "."
version = "1.2.0"
commit = "0123456789abcdef0123456789abcdef01234567"
title = "Review team"
description = "A reviewer and a tester, wired for pull requests."
```

## Rules

- **A publisher is claimed once.** The `acme` in `acme/review-team` belongs to whoever opened the first accepted pull request for it. Later entries under that publisher come from the maintainers named in `CODEOWNERS`.
- **A listed version is never edited.** A fix is a new version with a new entry. An entry is removed only when a pack should no longer be offered, and people who installed it keep their copy.
- **Versions go up.** A new entry for an id has a higher semantic version than every entry before it.
- **The commit is the exact commit of that version.** It is a full 40-character id, never a branch or a tag.
- **One pack version per pull request.** The pull request adds that one entry and changes nothing else.

## The check

`.github/workflows/check.yml` runs on every pull request, on a runner with no secrets. For each entry the pull request adds or changes, it:

- checks that `packs.toml` parses, every commit is a full id, no id appears twice at one version, and versions go up;
- fetches the pinned commit of the entry's repository anonymously;
- checks that the pack's `mao-pack.toml` has the same `id` and `version` as the entry.

The full `mao pack check` step is added once a `mao` build is published for runners to download. Until then, maintainers run `mao pack check` locally during the review.

The registry does not sign packs, approve commands, or know who installs what. The default branch is protected, and every change is a reviewed pull request.

## Mirrors and company registries

A company can keep its own registry with the same layout, public or private, and its members add it in MAO under Settings, Pack sources. A mirror of this registry is used with `mao source set-url official <address>`.
