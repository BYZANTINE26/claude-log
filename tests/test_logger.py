"""Tests for claude_log.logger: append-only JSONL log."""

import json
import os

from claude_log.logger import (
    append_entry,
    build_entry,
    count_entries,
    get_recent_entries,
    initialize_or_resume,
)


def test_initialize_or_resume_creates_empty_log(project_root, config):
    log_path = initialize_or_resume(project_root, "session-1", config)
    assert os.path.exists(log_path)
    assert get_recent_entries(log_path, 10) == []


def test_initialize_or_resume_does_not_truncate_existing_log(
    project_root, config
):
    log_path = initialize_or_resume(project_root, "session-1", config)
    append_entry(log_path, {"turn_id": "session-1:0", "summary": "first"})

    initialize_or_resume(project_root, "session-1", config)  # resume

    assert len(get_recent_entries(log_path, 10)) == 1


def test_append_entry_produces_valid_jsonl(tmp_path):
    log_path = str(tmp_path / "session.jsonl")
    append_entry(log_path, {"turn_id": "a:0", "summary": "one"})
    append_entry(log_path, {"turn_id": "a:1", "summary": "two"})

    with open(log_path, "r", encoding="utf-8") as log_file:
        lines = log_file.readlines()
    assert [json.loads(line)["summary"] for line in lines] == ["one", "two"]


def test_get_recent_entries_returns_correct_tail_slice(tmp_path):
    log_path = str(tmp_path / "session.jsonl")
    for index in range(5):
        append_entry(log_path, {"turn_id": f"a:{index}", "summary": str(index)})

    recent = get_recent_entries(log_path, 2)
    assert [entry["summary"] for entry in recent] == ["3", "4"]


def test_count_entries(tmp_path):
    log_path = str(tmp_path / "session.jsonl")
    assert count_entries(log_path) == 0

    append_entry(log_path, {"turn_id": "a:0", "summary": "one"})
    assert count_entries(log_path) == 1


def test_build_entry_slim_omits_context():
    entry = build_entry(
        "a:0", "2026-01-01T00:00:00Z", "did something", {"tools": []}, None, "slim"
    )
    assert "context" not in entry


def test_build_entry_rich_includes_context():
    context = {"prompt": "hi", "tool_calls": []}
    entry = build_entry(
        "a:0", "2026-01-01T00:00:00Z", "did something", {"tools": []},
        context, "rich",
    )
    assert entry["context"] == context
