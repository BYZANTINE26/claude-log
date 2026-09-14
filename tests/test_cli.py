from claude_log.cli import load_recent
from claude_log.logger import append_entry, build_entry, get_recent_entries, initialize_or_resume, mark_context_reset


def test_load_recent_prints_and_records_reingestion(project_root, capsys):
    for index in range(5):
        path = initialize_or_resume(project_root, "sess1")
        append_entry(path, build_entry(f"t{index}", "ts", f"summary {index}", {}))
    mark_context_reset(project_root, "sess1")

    recent = load_recent(project_root, 3)

    assert len(recent) == 3
    printed_lines = capsys.readouterr().out.strip().splitlines()
    # self-labeling header, then summaries only, numbered — no
    # turn_id/timestamp/refs metadata
    assert printed_lines == [
        "claude-log: recent session summaries (background context, no action needed):",
        "1. summary 2",
        "2. summary 3",
        "3. summary 4",
    ]

    # window formula now sees 3 reingested + new turns since reset
    another_path = initialize_or_resume(project_root, "sess1")
    append_entry(another_path, build_entry("t5", "ts", "summary 5", {}))
    assert len(get_recent_entries(project_root, "sess1", 10)) == 4


def test_load_recent_with_no_session_log(project_root, capsys):
    result = load_recent(project_root, 10)
    assert result == []
    assert "no session log found" in capsys.readouterr().out


def test_load_recent_skips_summary_failed_and_turn_lost_markers(project_root, capsys):
    path = initialize_or_resume(project_root, "sess1")
    append_entry(path, build_entry("t0", "ts", "did the first thing", {}))
    append_entry(path, build_entry("t1", "ts", None, {}, failure_flag="summary_failed"))
    append_entry(path, {"turn_id": "t2", "timestamp": "ts", "turn_lost": True})
    append_entry(path, build_entry("t3", "ts", "did the last thing", {}))

    recent = load_recent(project_root, 4)

    assert len(recent) == 4  # count still spans all 4 raw entries
    printed_lines = capsys.readouterr().out.strip().splitlines()
    # markers skipped entirely, remaining summaries renumbered from 1
    assert printed_lines == [
        "claude-log: recent session summaries (background context, no action needed):",
        "1. did the first thing",
        "2. did the last thing",
    ]


def test_load_recent_prints_nothing_when_every_entry_is_a_marker(project_root, capsys):
    path = initialize_or_resume(project_root, "sess1")
    append_entry(path, build_entry("t0", "ts", None, {}, failure_flag="summary_failed"))
    append_entry(path, {"turn_id": "t1", "timestamp": "ts", "turn_lost": True})

    load_recent(project_root, 2)

    # no summaries to show -> no header either, not an empty labeled block
    assert capsys.readouterr().out == ""
