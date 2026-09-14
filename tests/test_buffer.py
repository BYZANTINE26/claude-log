import os

from claude_log import buffer
from claude_log.config import buffer_path


def test_start_turn_then_read_and_clear_round_trip(project_root):
    path = buffer_path(project_root, "sess1", "prompt1")
    buffer.start_turn(path, "add a function", "abc123", {"a.txt": "hash1"})

    result = buffer.read_and_clear(path)
    assert result["prompt"] == "add a function"
    assert result["commit_before"] == "abc123"
    assert result["dirty_before"] == {"a.txt": "hash1"}
    assert result["assistant_messages"] == []
    assert not os.path.exists(path)  # disposable: gone after read_and_clear
    assert not os.path.exists(f"{path}.tmp")


def test_read_and_clear_on_missing_buffer_returns_empty_shape(project_root):
    path = buffer_path(project_root, "sess1", "never-started")
    result = buffer.read_and_clear(path)
    assert result["prompt"] is None
    assert result["assistant_messages"] == []


def test_message_delta_accumulates_until_final(project_root):
    path = buffer_path(project_root, "sess1", "prompt1")
    buffer.start_turn(path, "prompt", None, {})

    buffer.append_message_delta(path, "msg-1", "Hello ", final=False)
    buffer.append_message_delta(path, "msg-1", "world.\n", final=True)

    result = buffer.read_and_clear(path)
    assert result["assistant_messages"] == ["Hello world.\n"]


def test_two_full_messages_stay_separate(project_root):
    path = buffer_path(project_root, "sess1", "prompt1")
    buffer.start_turn(path, "prompt", None, {})

    buffer.append_message_delta(path, "msg-1", "First message.", final=True)
    buffer.append_message_delta(path, "msg-2", "Second message.", final=True)

    result = buffer.read_and_clear(path)
    assert result["assistant_messages"] == ["First message.", "Second message."]


def test_non_interactive_single_call_message(project_root):
    """SDK/claude -p runs: one call, index 0, final true, full text."""
    path = buffer_path(project_root, "sess1", "prompt1")
    buffer.start_turn(path, "prompt", None, {})

    buffer.append_message_delta(path, "msg-1", "The whole message at once.", final=True)

    result = buffer.read_and_clear(path)
    assert result["assistant_messages"] == ["The whole message at once."]


def test_sweep_orphaned_finds_and_deletes_stale_buffers(project_root):
    stale_path = buffer_path(project_root, "sess1", "old-prompt")
    current_path = buffer_path(project_root, "sess1", "current-prompt")
    buffer.start_turn(stale_path, "old turn, never finished", None, {})
    buffer.start_turn(current_path, "current turn", None, {})

    markers = buffer.sweep_orphaned(project_root, "sess1", "current-prompt")

    assert len(markers) == 1
    assert markers[0]["turn_id"] == "old-prompt"
    assert markers[0]["turn_lost"] is True
    assert not os.path.exists(stale_path)
    assert os.path.exists(current_path)  # untouched


def test_sweep_orphaned_ignores_other_sessions(project_root):
    other_session_path = buffer_path(project_root, "sess-other", "prompt1")
    buffer.start_turn(other_session_path, "different session", None, {})

    markers = buffer.sweep_orphaned(project_root, "sess1", "current-prompt")

    assert markers == []
    assert os.path.exists(other_session_path)


def test_sweep_orphaned_on_missing_buffers_dir(project_root):
    assert buffer.sweep_orphaned(project_root, "sess1", "current-prompt") == []
