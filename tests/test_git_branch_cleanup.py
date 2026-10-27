"""Tests for git-branch-cleanup.

Run: python3 tests/test_git_branch_cleanup.py
No third-party dependencies. The integration test builds a real throwaway
git repo in a temp dir and never touches the caller's repo.
"""

import os
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from git_branch_cleanup import classify, gone_branches, main  # noqa: E402


def test_classify_never_deletes_current():
    delete, keep = classify(["main", "done", "wip"], "main",
                            merged={"done"}, gone=set())
    assert delete == ["done"], delete
    assert keep["main"] == "current branch"
    assert keep["wip"] == "not merged and upstream still exists"


def test_classify_gone_beats_unmerged():
    delete, keep = classify(["old"], "main", merged=set(), gone={"old"})
    assert delete == ["old"]
    assert "old" not in keep


def test_gone_parsing():
    # gone_branches parses `git branch -vv` output; simulate by monkeypatch.
    import git_branch_cleanup as mod
    sample = ("* main  abc1234 [origin/main] first\n"
              "  old   abc1234 [origin/old: gone] last\n")
    orig = mod.run_git
    mod.run_git = lambda repo, args: (0, sample)
    try:
        assert gone_branches(".") == {"old"}
    finally:
        mod.run_git = orig


def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", repo] + list(args),
                          capture_output=True, text=True, check=check)


def test_integration_dry_run_then_apply():
    with tempfile.TemporaryDirectory() as tmp:
        git(tmp, "init", "-b", "main")
        git(tmp, "config", "user.email", "test@example.com")
        git(tmp, "config", "user.name", "Test")
        pathlib.Path(tmp, "a.txt").write_text("a\n")
        git(tmp, "add", ".")
        git(tmp, "commit", "-m", "base")
        git(tmp, "branch", "done")
        git(tmp, "checkout", "-b", "wip")
        pathlib.Path(tmp, "b.txt").write_text("b\n")
        git(tmp, "add", ".")
        git(tmp, "commit", "-m", "wip work")
        git(tmp, "checkout", "main")
        git(tmp, "merge", "done", "--no-ff", "-m", "merge done")
        # Dry run must not delete anything.
        assert main(["--repo", tmp]) == 0
        names = git(tmp, "branch", "--format=%(refname:short)").stdout.split()
        assert set(names) == {"main", "done", "wip"}, names
        # Apply deletes the merged branch only; wip survives.
        assert main(["--repo", tmp, "--apply"]) == 0
        names = git(tmp, "branch", "--format=%(refname:short)").stdout.split()
        assert set(names) == {"main", "wip"}, names
        # Unmerged needs both flags, otherwise refused.
        assert main(["--repo", tmp, "--apply", "--include-unmerged"]) == 2
        names = git(tmp, "branch", "--format=%(refname:short)").stdout.split()
        assert "wip" in names


def test_refuses_non_repo():
    with tempfile.TemporaryDirectory() as tmp:
        assert main(["--repo", tmp]) == 2


def main_test():
    tests = [test_classify_never_deletes_current,
             test_classify_gone_beats_unmerged,
             test_gone_parsing,
             test_integration_dry_run_then_apply,
             test_refuses_non_repo]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"All {len(tests)} tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main_test())
