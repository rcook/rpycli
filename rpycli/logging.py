from typing import Any, ContextManager, Protocol


class LoggerProtocol(Protocol):
    @property
    def level(self) -> int:
        raise NotImplementedError()

    def debug(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()

    def info(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()

    def warning(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()

    def error(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()

    def fatal(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()

    def span(self, name: str) -> ContextManager[None]:
        raise NotImplementedError()
