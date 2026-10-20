from chatbot_rag.adapters.output.report_markdown import MarkdownReportRenderer, slugify
from chatbot_rag.domain import Report, ToolCall


def test_unusable_title_falls_back():
    assert slugify("!!! ???") == "incident"


def test_accents_and_spaces():
    assert slugify("Café  Crash") == "cafe-crash"


def test_slug_is_length_capped():
    assert len(slugify("a" * 200)) <= 60


def test_render_contains_factual_sections():
    report = Report("T", "S", "TRACE", (ToolCall("search_docs", {"query": "q"}, "RES"),))
    text = MarkdownReportRenderer().render(report)
    for expected in ("# T", "S", "TRACE", "`search_docs`", '"query": "q"', "RES"):
        assert expected in text


def test_render_without_tool_calls():
    assert "No tool calls were made." in MarkdownReportRenderer().render(Report("T", "S", "TRACE", ()))
