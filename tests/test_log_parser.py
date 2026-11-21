from incidentpilot.log_parser import parse_logs, summarize_logs, search_logs

SAMPLE = """2026-11-21 10:42:01 ERROR TypeError reading id request_id=req-1
2026-11-21 10:42:02 WARN retry request_id=req-1
2026-11-21 10:42:03 INFO health ok
"""

def test_parse_and_summary():
    rows = parse_logs(SAMPLE)
    summary = summarize_logs(rows)
    assert len(rows) == 3
    assert summary["error_count"] == 1
    assert summary["warning_count"] == 1
    assert "req-1" in summary["request_ids"]

def test_search_logs():
    rows = parse_logs(SAMPLE)
    found = search_logs(rows, "TypeError req-1")
    assert len(found) == 1
    assert found[0]["line"] == 1
