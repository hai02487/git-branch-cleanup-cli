#!/usr/bin/env python3
"""git-branch-cleanup: delete stale local git branches, safely by default.

Default run is a dry run: it lists what WOULD be deleted and deletes
nothing. Pass --apply to actually delete, and only then.

Safety rules (non-negotiable):
- The current branch is never deleted.
- A branch is only auto-deleted if its upstream is gone, or it is fully
  merged into HEAD. Both are checked with git itself, not guessed.
- Unmerged branches are listed as "kept" and are never deleted unless the
  user passes BOTH --include-unmerged and --yes (which uses `git branch -D`).
- Nothing is fetched, pushed, or sent anywhere. This tool only reads the
  local repo and deletes local branches the user approved.

Usage:
    python3 src/git_branch_cleanup.py            # dry run, list only
    python3 src/git_branch_cleanup.py --apply    # delete gone + merged
    python3 src/git_branch_cleanup.py --apply --include-unmerged --yes

Exit codes: 0 = ok (dry run or deletions done), 1 = usage/git error,
2 = refused (e.g. not a git repo, or --include-unmerged without --yes).
Python standard library only. No third-party dependencies.
"""

import argparse
import subprocess
import sys


def run_git(repo, args):
    """Run git in repo; return (returncode, stdout). Raise on git missing."""
    result = subprocess.run(
        ["git", "-C", repo] + args,
        capture_output=True, text=True, check=False,
    )
    return result.returncode, result.stdout.strip()


def is_git_repo(repo):
    code, _ = run_git(repo, ["rev-parse", "--git-dir"])
    return code == 0


def current_branch(repo):
    code, out = run_git(repo, ["branch", "--show-current"])
    if code != 0:
        raise RuntimeError("could not determine the current branch")
    return out


def local_branches(repo):
    """All local branch names, in git's order."""
    code, out = run_git(repo, ["branch", "--format=%(refname:short)"])
    if code != 0:
        raise RuntimeError("could not list local branches")
    return [line.strip() for line in out.splitlines() if line.strip()]


def merged_branches(repo):
    """Branches fully merged into HEAD."""
    code, out = run_git(repo, ["branch", "--merged", "HEAD",
                               "--format=%(refname:short)"])
    if code != 0:
        raise RuntimeError("could not list merged branches")
    return set(line.strip() for line in out.splitlines() if line.strip())


def gone_branches(repo):
    """Branches whose upstream is gone.

    Parses `git branch -vv`, where a gone upstream shows as ': gone]'.
    Note: run `git fetch --prune` first if you want this list to reflect
    the remote's current state; this tool deliberately does not fetch.
    """
    code, out = run_git(repo, ["branch", "-vv"])
    if code != 0:
        raise RuntimeError("could not list branches with upstream info")
    gone = set()
    for line in out.splitlines():
        if ": gone]" in line:
            # Line form: "* name  abc1234 [origin/name: gone] message"
            # or: "  name  abc1234 [origin/name: gone] message"
            parts = line.replace("*", " ").split()
            if parts:
                gone.add(parts[0])
    return gone


def classify(branches, current, merged, gone):
    """Sort branches into (delete, keep) with a reason for each kept one.

    A branch is deletable only if it is not current AND (gone or merged).
    Everything else is kept, with the reason stated plainly.
    """
    delete = []
    keep = {}
    for branch in branches:
        if branch == current:
            keep[branch] = "current branch"
        elif branch in gone:
            delete.append(branch)
        elif branch in merged:
            delete.append(branch)
        else:
            keep[branch] = "not merged and upstream still exists"
    return delete, keep


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="List (default) or delete stale local git branches.")
    parser.add_argument("--repo", default=".",
                        help="path to the git repo (default: current dir)")
    parser.add_argument("--apply", action="store_true",
                        help="actually delete; without this, dry run only")
    parser.add_argument("--include-unmerged", action="store_true",
                        help="also delete unmerged branches (needs --yes)")
    parser.add_argument("--yes", action="store_true",
                        help="confirm unmerged deletion (needs --include-unmerged)")
    args = parser.parse_args(argv)

    if args.include_unmerged and not args.yes:
        print("Refused: --include-unmerged requires --yes. "
              "Unmerged branches are never deleted on a single flag.",
              file=sys.stderr)
        return 2
    if not is_git_repo(args.repo):
        print(f"Refused: {args.repo} is not a git repository.",
              file=sys.stderr)
        return 2

    try:
        current = current_branch(args.repo)
        branches = local_branches(args.repo)
        merged = merged_branches(args.repo)
        gone = gone_branches(args.repo)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    delete, keep = classify(branches, current, merged, gone)
    unmerged = [b for b in keep if keep[b].startswith("not merged")]
    if args.include_unmerged and args.yes:
        delete = delete + unmerged
        keep = {b: r for b, r in keep.items() if b not in unmerged}

    print(f"Current branch: {current}")
    print(f"Local branches: {len(branches)}")
    if delete:
        print("Would delete:" if not args.apply else "Deleting:")
        for branch in delete:
            reason = "upstream gone" if branch in gone else "merged"
            print(f"  - {branch} ({reason})")
    else:
        print("Nothing to delete.")
    if keep:
        print("Kept:")
        for branch, reason in keep.items():
            print(f"  - {branch} ({reason})")

    if not args.apply:
        print("Dry run: nothing deleted. Re-run with --apply to delete.")
        return 0

    force = args.include_unmerged and args.yes
    # Forced (-D) only for the explicitly confirmed unmerged set.
    failures = []
    for branch in delete:
        is_unmerged = branch in unmerged
        code, out = run_git(args.repo,
                            ["branch", "-D" if is_unmerged else "-d", branch])
        if code != 0:
            failures.append((branch, out))
    if failures:
        for branch, out in failures:
            print(f"Failed to delete {branch}: {out}", file=sys.stderr)
        return 1
    print(f"Deleted {len(delete)} branch(es).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
