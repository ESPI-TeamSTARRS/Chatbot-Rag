import json
import re
import unicodedata
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from chatbot_rag.domain import Report, ReportError
from chatbot_rag.ports import ReportWriterPort

MAX_SLUG_LENGTH = 60
FALLBACK_SLUG = "incident"
TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def slugify(title: str) -> str:
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")[:MAX_SLUG_LENGTH].strip("-")
    return slug or FALLBACK_SLUG


class MarkdownReportRenderer:
    """Turns a Report into a Markdown document."""

    def render(self, report: Report) -> str:
        lines = [
            f"# {report.title}",
            "",
            "## Summary",
            "",
            report.summary,
            "",
            "## Error trace",
            "",
            "```",
            report.error_trace,
            "```",
            "",
            "## Tool calls",
            "",
            *self._render_tool_calls(report),
            "## Remediation",
            "",
            "No remediation was executed.",
            "",
        ]
        return "\n".join(lines)

    def _render_tool_calls(self, report: Report) -> list[str]:
        if not report.tool_calls:
            return ["No tool calls were made.", ""]
        lines: list[str] = []
        for index, call in enumerate(report.tool_calls, start=1):
            lines += [
                f"### {index}. `{call.name}`",
                "",
                "Arguments:",
                "",
                "```json",
                json.dumps(call.arguments, indent=2, ensure_ascii=False),
                "```",
                "",
                "Result:",
                "",
                "```",
                call.result,
                "```",
                "",
            ]
        return lines


class MarkdownReportWriter(ReportWriterPort):
    """Writes each report as a new Markdown file named <timestamp>-<slug>.md."""

    def __init__(self, output_dir: Path, clock: Callable[[], datetime] = utc_now):
        self._output_dir = output_dir
        self._clock = clock
        self._renderer = MarkdownReportRenderer()

    def write(self, report: Report) -> str:
        path = self._output_dir / f"{self._clock().strftime(TIMESTAMP_FORMAT)}-{slugify(report.title)}.md"
        self._output_dir.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("x", encoding="utf-8") as file:
                file.write(self._renderer.render(report))
        except FileExistsError as error:
            raise ReportError(f"Report already exists: {path}") from error
        return str(path)
