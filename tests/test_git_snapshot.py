import subprocess

import pytest

from claude_log.git_snapshot import files_touched, snapshot_git_state


def _git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def git_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git("init", "-q", cwd=repo)
    _git("config", "user.email", "test@example.com", cwd=repo)
    _git("config", "user.name", "Test", cwd=repo)
    return repo


def _commit_file(repo, name, content):
    (repo / name).write_text(content)
    _git("add", name, cwd=repo)
    _git("commit", "-q", "-m", f"add {name}", cwd=repo)


def test_snapshot_outside_git_repo(tmp_path):
    non_repo = tmp_path / "not-a-repo"
    non_repo.mkdir()
    snapshot = snapshot_git_state(str(non_repo))
    assert snapshot == {"commit": None, "dirty": {}}


def test_snapshot_no_commits_yet(git_repo):
    snapshot = snapshot_git_state(str(git_repo))
    assert snapshot["commit"] is None


def test_committed_change_shows_in_files_touched(git_repo):
    _commit_file(git_repo, "a.txt", "one")
    before = snapshot_git_state(str(git_repo))
    _commit_file(git_repo, "b.txt", "two")
    after = snapshot_git_state(str(git_repo))
    assert files_touched(before, after, str(git_repo)) == ["b.txt"]


def test_multiple_commits_collapse_to_one_diff(git_repo):
    _commit_file(git_repo, "a.txt", "one")
    before = snapshot_git_state(str(git_repo))
    _commit_file(git_repo, "b.txt", "two")
    _commit_file(git_repo, "c.txt", "three")
    after = snapshot_git_state(str(git_repo))
    assert files_touched(before, after, str(git_repo)) == ["b.txt", "c.txt"]


def test_pre_existing_dirty_file_untouched_is_excluded(git_repo):
    _commit_file(git_repo, "a.txt", "one")
    (git_repo / "a.txt").write_text("dirty before the turn started")
    before = snapshot_git_state(str(git_repo))
    after = snapshot_git_state(str(git_repo))  # untouched during the "turn"
    assert files_touched(before, after, str(git_repo)) == []


def test_pre_existing_dirty_file_further_modified_is_included(git_repo):
    _commit_file(git_repo, "a.txt", "one")
    (git_repo / "a.txt").write_text("dirty before the turn started")
    before = snapshot_git_state(str(git_repo))
    (git_repo / "a.txt").write_text("modified during the turn")
    after = snapshot_git_state(str(git_repo))
    assert files_touched(before, after, str(git_repo)) == ["a.txt"]


def test_new_untracked_file_is_included(git_repo):
    _commit_file(git_repo, "a.txt", "one")
    before = snapshot_git_state(str(git_repo))
    (git_repo / "new.txt").write_text("brand new")
    after = snapshot_git_state(str(git_repo))
    assert files_touched(before, after, str(git_repo)) == ["new.txt"]


def test_reverted_edit_shows_no_net_change(git_repo):
    _commit_file(git_repo, "a.txt", "one")
    before = snapshot_git_state(str(git_repo))
    (git_repo / "a.txt").write_text("temporarily changed")
    (git_repo / "a.txt").write_text("one")  # reverted back before Stop
    after = snapshot_git_state(str(git_repo))
    assert files_touched(before, after, str(git_repo)) == []


def test_deleted_file_is_included(git_repo):
    _commit_file(git_repo, "a.txt", "one")
    before = snapshot_git_state(str(git_repo))
    (git_repo / "a.txt").unlink()
    after = snapshot_git_state(str(git_repo))
    assert files_touched(before, after, str(git_repo)) == ["a.txt"]


def test_untracked_directory_does_not_blank_out_other_files(git_repo):
    """Regression test for a real bug found live: an entirely-untracked
    directory used to fold into one `git status --porcelain` line that
    `git hash-object` can't hash, silently emptying the *whole* dirty
    hash map (every other genuinely touched file included) rather than
    just that one directory's entry."""
    before = snapshot_git_state(str(git_repo))
    (git_repo / "regular.txt").write_text("a plain new file")
    nested_dir = git_repo / "somedir"
    nested_dir.mkdir()
    (nested_dir / "inner.txt").write_text("inside an untracked directory")
    after = snapshot_git_state(str(git_repo))
    assert files_touched(before, after, str(git_repo)) == [
        "regular.txt",
        "somedir/inner.txt",
    ]
