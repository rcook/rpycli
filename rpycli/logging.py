from typing import Any, ContextManager, Protocol


class LoggerProtocol(Protocol):
    def info(self, *args: Any, **kwargs: Any):
        raise NotImplementedError()

    def span(self, name: str) -> ContextManager:
        raise NotImplementedError()
