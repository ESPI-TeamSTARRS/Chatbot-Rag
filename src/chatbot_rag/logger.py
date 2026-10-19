from datetime import datetime


class Logger:
    """Prints "<timestamp> [DEBUG]: <message>" on stdout once debug mode has been enabled.

    A single instance, `logger`, is shared by the whole application: it is configured once at
    startup with `logger.configure(...)`, then used anywhere with `logger.debug(message=...)`.
    Until configured, nothing is printed.
    """

    def __init__(self):
        self._enabled: bool | None = None

    def configure(self, enabled: bool) -> None:
        if self._enabled is not None:
            raise RuntimeError("Logger is already configured")
        self._enabled = enabled

    def reset(self) -> None:
        """Forget the configuration (meant for tests)."""
        self._enabled = None

    def debug(self, message: str) -> None:
        if self._enabled:
            timestamp = datetime.now().isoformat(timespec="seconds")
            print(f"{timestamp} [DEBUG]: {message}", flush=True)


logger = Logger()
