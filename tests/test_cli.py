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
    assert len(printed_lines) == 3

    # window formula now sees 3 reingested + new turns since reset
    another_path = initialize_or_resume(project_root, "sess1")
    append_entry(another_path, build_entry("t5", "ts", "summary 5", {}))
    assert len(get_recent_entries(project_root, "sess1", 10)) == 4


def test_load_recent_with_no_session_log(project_root, capsys):
    result = load_recent(project_root, 10)
    assert result == []
    assert "no session log found" in capsys.readouterr().out
