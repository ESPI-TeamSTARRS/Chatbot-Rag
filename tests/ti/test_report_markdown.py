import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from chatbot_rag.adapters.output.report_markdown import MarkdownReportWriter
from chatbot_rag.domain import Report, ReportError, ToolCall


def fixed_clock():
    return datetime(2026, 10, 19, 14, 30, 12, tzinfo=timezone.utc)


def make_report(title="Redis Timeout!"):
    call = ToolCall("search_docs", {"query": "redis timeout"}, "hit: redis.md")
    return Report(title, "Restart sentinel.", "ERROR redis timed out", (call,))


def test_file_naming(tmp_path):
    out = tmp_path / "actions-taken"
    path = MarkdownReportWriter(out, fixed_clock).write(make_report())
    assert path == str(out / "20261019-143012-redis-timeout.md")


def test_unusable_title_file_starts_with_incident(tmp_path):
    path = MarkdownReportWriter(tmp_path / "out", fixed_clock).write(make_report("!!!"))
    assert Path(path).name.endswith("-incident.md")


def test_file_content(tmp_path):
    path = MarkdownReportWriter(tmp_path / "out", fixed_clock).write(make_report())
    text = Path(path).read_text()
    assert "Restart sentinel." in text and "ERROR redis timed out" in text and "hit: redis.md" in text


def test_collision_leaves_existing_file(tmp_path):
    writer = MarkdownReportWriter(tmp_path / "out", fixed_clock)
    path = writer.write(make_report())
    original = Path(path).read_text()
    with pytest.raises(ReportError):
        writer.write(Report("Redis Timeout!", "other", "other", ()))
    assert Path(path).read_text() == original


def test_default_clock_gives_utc_timestamp_prefix(tmp_path):
    path = MarkdownReportWriter(tmp_path).write(make_report())
    assert re.match(r"^\d{8}-\d{6}-redis-timeout\.md$", Path(path).name)
