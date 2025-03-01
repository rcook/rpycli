from logging import DEBUG
from rpycli.context import Logger
from typing import Any, ContextManager


def test_basics() -> None:
    logger = Logger("test-logger", log_level=DEBUG)
    with logger.span("test-span") as span:
        assert span is None
