"""Tests for claude_log.metadata: commit hash and touched-files extraction."""

from claude_log.metadata import current_commit_hash, files_touched


def test_current_commit_hash_in_this_git_repo():
    project_root = "/Volumes/GBC/projects/claude-log"
    commit_hash = current_commit_hash(project_root)
    assert commit_hash is None or len(commit_hash) == 40


def test_current_commit_hash_outside_a_git_repo(tmp_path):
    assert current_commit_hash(str(tmp_path)) is None


def test_files_touched_dedups_and_preserves_order():
    tool_calls = [
        {"tool_name": "Edit", "tool_input": {"file_path": "a.py"}},
        {"tool_name": "Bash", "tool_input": {"command": "ls"}},
        {"tool_name": "Write", "tool_input": {"file_path": "b.py"}},
        {"tool_name": "Edit", "tool_input": {"file_path": "a.py"}},
    ]
    assert files_touched(tool_calls) == ["a.py", "b.py"]


def test_files_touched_ignores_calls_without_file_path():
    tool_calls = [{"tool_name": "Edit", "tool_input": {}}]
    assert files_touched(tool_calls) == []
