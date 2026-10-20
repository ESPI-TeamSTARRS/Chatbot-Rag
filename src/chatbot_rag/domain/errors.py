class LlmError(Exception):
    """The LLM server could not produce a usable reply."""


class IterationLimitError(Exception):
    """The LLM kept requesting tools without ever giving a final answer."""


class SearchError(Exception):
    """The documentation search server could not answer."""


class ReportError(Exception):
    """The incident report could not be written."""


class HistoryError(Exception):
    """The request history database could not be reached or written."""
