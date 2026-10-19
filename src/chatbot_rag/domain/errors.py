class LlmError(Exception):
    """The LLM server could not produce a usable reply."""


class IterationLimitError(Exception):
    """The LLM kept requesting tools without ever giving a final answer."""


class ReportError(Exception):
    """The incident report could not be written."""
