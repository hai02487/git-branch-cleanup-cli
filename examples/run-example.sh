#!/bin/sh
# Walkthrough: merged branch deleted, unmerged branch kept.
# Creates a throwaway repo under /tmp, never touches your real repos.
# Usage: sh examples/run-example.sh
set -e
SCRIPT_DIR=$(cd "$(dirname "$0")/.." && pwd)
DIR=$(mktemp -d)
cd "$DIR"
git init -b main -q
git config user.email "test@example.com"
git config user.name "Test"
echo a > a.txt && git add . && git commit -qm "base"
git branch done
git checkout -qb wip
echo b > b.txt && git add . && git commit -qm "wip work"
git checkout -q main
git merge done --no-ff -qm "merge done"
echo "--- dry run (deletes nothing) ---"
python3 "$SCRIPT_DIR/src/git_branch_cleanup.py" --repo "$DIR" || true
echo "--- apply ---"
python3 "$SCRIPT_DIR/src/git_branch_cleanup.py" --repo "$DIR" --apply
echo "--- remaining branches (expect: main, wip) ---"
git branch --format='%(refname:short)'
cd /
rm -rf "$DIR"
