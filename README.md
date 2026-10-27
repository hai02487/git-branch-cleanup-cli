# git-branch-cleanup-cli

Delete stale local git branches — gone on the remote, or fully merged — with a dry run first, always.

[![CI](https://github.com/hai02487/git-branch-cleanup-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/hai02487/git-branch-cleanup-cli/actions/workflows/ci.yml) [![Licence: MIT](https://img.shields.io/badge/Licence-MIT-yellow.svg)](LICENSE)

## What it does

Over a project's life, local branches pile up: feature branches merged weeks ago, branches whose remote branch was deleted, experiment branches never finished. `git-branch-cleanup` lists them and, only when you say `--apply`, deletes the safe ones:

- **Upstream gone** — the remote branch no longer exists (shows as `: gone]` in `git branch -vv`).
- **Fully merged into HEAD** — `git branch --merged HEAD` says the work is already in your current branch.

## What it does NOT do

- It never deletes the current branch.
- It never deletes an unmerged branch unless you pass **both** `--include-unmerged` and `--yes` — a single flag is refused on purpose.
- It never fetches, pushes, or talks to a remote. If you want the "gone" list to reflect the remote's current state, run `git fetch --prune` first yourself.
- It never deletes remote branches, tags, or stashes.
- It sends nothing anywhere. Everything runs locally, Python standard library only.

## Install

No install step and no dependencies — Python 3.8+ and git are enough:

```sh
git clone https://github.com/hai02487/git-branch-cleanup-cli.git
cd git-branch-cleanup-cli
python3 src/git_branch_cleanup.py --help
```

## Usage

Dry run first — this is the default, and it deletes nothing:

```sh
python3 src/git_branch_cleanup.py
```

Real output on a sample repo (see `examples/`):

```
Current branch: main
Local branches: 3
Would delete:
  - done (merged)
Kept:
  - main (current branch)
  - wip (not merged and upstream still exists)
Dry run: nothing deleted. Re-run with --apply to delete.
```

Delete the safe branches:

```sh
python3 src/git_branch_cleanup.py --apply
```

Work on a different repo without changing directory:

```sh
python3 src/git_branch_cleanup.py --repo /path/to/your/repo --apply
```

Delete unmerged branches too — only with both flags, deliberately:

```sh
python3 src/git_branch_cleanup.py --apply --include-unmerged --yes
```

`--include-unmerged` alone is refused (exit code 2) and deletes nothing.

## Example

See `examples/` for a runnable walkthrough: it creates a throwaway repo with a merged branch and an unmerged branch, runs the dry run, then `--apply`, and shows that only the merged branch disappears. The same scenario is covered by the integration test, so the example and the tests cannot drift apart.

## How it is tested

```sh
python3 tests/test_git_branch_cleanup.py
```

Expected output: `All 5 tests passed.` The suite covers the classification rules (current branch never deleted, gone branches deletable, unmerged kept), the `: gone]` parsing, a real-repo dry-run-then-apply run, and refusal outside a git repo. Tests run on the exact files in this repo, with no network and no third-party packages.

## Contributing

Small, focused improvements are welcome. Open an issue first for anything larger than a typo, keep the safety rules above intact, and run the test suite before opening a pull request. See `CONTRIBUTING.md`.

## Licence

MIT — see `LICENSE`. Original work, written for this repo; it builds on git's own `--merged` and `-vv` output, not on any other cleanup tool's code.
