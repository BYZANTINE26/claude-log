import concurrent.futures
import json
import os
import time

from claude_log import logger
from claude_log.config import log_file_path


def _append(project_root, session_id, summary):
    path = logger.initialize_or_resume(project_root, session_id)
    entry = logger.build_entry(f"turn-{summary}", "2026-09-13T00:00:00Z", summary, {})
    logger.append_entry(path, entry)


def test_initialize_or_resume_does_not_create_file(project_root):
    path = logger.initialize_or_resume(project_root, "sess1")
    assert path == log_file_path(project_root, "sess1")
    assert not os.path.exists(path)  # no entries yet -> no file on disk
    assert os.path.isdir(os.path.dirname(path))


def test_append_entry_creates_valid_jsonl(project_root):
    _append(project_root, "sess1", "did a thing")
    _append(project_root, "sess1", "did another thing")

    path = log_file_path(project_root, "sess1")
    with open(path) as log_file:
        lines = [json.loads(line) for line in log_file]
    assert [entry["summary"] for entry in lines] == ["did a thing", "did another thing"]


def test_initialize_or_resume_never_truncates_existing_log(project_root):
    _append(project_root, "sess1", "first")
    logger.initialize_or_resume(project_root, "sess1")  # simulate a resume
    _append(project_root, "sess1", "second")

    path = log_file_path(project_root, "sess1")
    with open(path) as log_file:
        entries = [json.loads(line) for line in log_file]
    assert [entry["summary"] for entry in entries] == ["first", "second"]


def test_build_entry_success_shape():
    entry = logger.build_entry("t1", "ts", "a summary", {"files": ["a.py"]})
    assert entry == {
        "turn_id": "t1",
        "timestamp": "ts",
        "summary": "a summary",
        "refs": {"files": ["a.py"]},
    }


def test_build_entry_summary_failed_has_no_fabricated_text():
    entry = logger.build_entry("t1", "ts", None, {"files": []}, failure_flag="summary_failed")
    assert entry["summary_failed"] is True
    assert "summary" not in entry


def test_get_recent_entries_with_no_reset_returns_full_window(project_root):
    for index in range(15):
        _append(project_root, "sess1", f"turn {index}")

    recent = logger.get_recent_entries(project_root, "sess1", configured_window=10)
    assert [entry["summary"] for entry in recent] == [f"turn {index}" for index in range(5, 15)]


def test_get_recent_entries_resumed_session_gets_full_window(project_root):
    """A resumed session never gets a reset marker written for it."""
    for index in range(3):
        _append(project_root, "sess1", f"turn {index}")
    logger.initialize_or_resume(project_root, "sess1")  # simulate SessionStart(resume)

    recent = logger.get_recent_entries(project_root, "sess1", configured_window=10)
    assert len(recent) == 3


def test_get_recent_entries_after_reset_with_no_reingestion_is_empty(project_root):
    for index in range(5):
        _append(project_root, "sess1", f"before clear {index}")
    logger.mark_context_reset(project_root, "sess1")

    recent = logger.get_recent_entries(project_root, "sess1", configured_window=10)
    assert recent == []


def test_get_recent_entries_grows_as_turns_accumulate_after_reset(project_root):
    for index in range(5):
        _append(project_root, "sess1", f"before clear {index}")
    logger.mark_context_reset(project_root, "sess1")

    _append(project_root, "sess1", "after clear 1")
    assert len(logger.get_recent_entries(project_root, "sess1", 10)) == 1

    _append(project_root, "sess1", "after clear 2")
    assert len(logger.get_recent_entries(project_root, "sess1", 10)) == 2


def test_get_recent_entries_with_reingestion_starts_from_k(project_root):
    for index in range(5):
        _append(project_root, "sess1", f"before clear {index}")
    logger.mark_context_reset(project_root, "sess1")
    logger.record_reingestion(project_root, "sess1", 3)

    _append(project_root, "sess1", "after clear 1")
    recent = logger.get_recent_entries(project_root, "sess1", configured_window=10)
    assert len(recent) == 4  # 3 reingested + 1 new since reset


def test_get_recent_entries_reads_correctly_across_a_chunk_boundary(project_root):
    """`_tail_lines` seeks backward in 8192-byte chunks — write enough
    entries to cross that boundary and confirm the seek-backward read
    still lands on the exact right lines, not an off-by-one from a line
    split across two chunks."""
    for index in range(500):  # each entry line is small, but 500 of them
        _append(project_root, "sess1", f"turn {index}")  # crosses 8192 bytes

    recent = logger.get_recent_entries(project_root, "sess1", configured_window=3)
    assert [entry["summary"] for entry in recent] == ["turn 497", "turn 498", "turn 499"]


def test_get_recent_entries_window_caps_at_configured_max(project_root):
    for index in range(5):
        _append(project_root, "sess1", f"before clear {index}")
    logger.mark_context_reset(project_root, "sess1")
    logger.record_reingestion(project_root, "sess1", 8)

    for index in range(5):
        _append(project_root, "sess1", f"after clear {index}")
    recent = logger.get_recent_entries(project_root, "sess1", configured_window=10)
    assert len(recent) == 10  # 8 + 5 = 13, capped at configured_window


def test_append_entry_is_safe_under_concurrent_writers(project_root):
    """BACKLOG.md #16: two Claude Code sessions sharing a session_id must
    not corrupt or drop each other's entry. Entries are made large enough
    (bigger than a typical single write-syscall buffer) that an unlocked
    writer would be likely to interleave and produce a torn line."""
    path = logger.initialize_or_resume(project_root, "sess1")
    writer_count = 20
    large_text = "x" * 100_000

    def write_one(index):
        entry = logger.build_entry(f"turn-{index}", "ts", large_text, {"index": index})
        logger.append_entry(path, entry)

    with concurrent.futures.ThreadPoolExecutor(max_workers=writer_count) as pool:
        list(pool.map(write_one, range(writer_count)))

    with open(path, encoding="utf-8") as log_file:
        entries = [json.loads(line) for line in log_file]  # raises if any line is torn
    assert len(entries) == writer_count
    assert {entry["refs"]["index"] for entry in entries} == set(range(writer_count))


def test_locked_serializes_concurrent_critical_sections(tmp_path):
    """Direct test of the lock primitive `mark_context_reset` and
    `record_reingestion` both rely on: a classic read-then-write race
    (read counter, sleep, write counter+1) must lose no increments when
    every critical section goes through the same lock file."""
    target_path = str(tmp_path / "target.txt")
    counter = {"value": 0}

    def increment(_index):
        with logger._locked(target_path):
            current = counter["value"]
            time.sleep(0.001)  # widen the race window
            counter["value"] = current + 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        list(pool.map(increment, range(50)))

    assert counter["value"] == 50
