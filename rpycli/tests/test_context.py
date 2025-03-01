from logging import DEBUG
from rpycli.context import Context, Logger
from rpycli.logging import LoggerProtocol
from typing import cast, no_type_check


def test_context() -> None:
    logger = Logger("test-logger", log_level=DEBUG)
    ctx = Context(cast(LoggerProtocol, logger))
    called = False
    with ctx.span("test-span") as span:
        called = True
        assert span is None
    assert called


@no_type_check
def test_logger() -> None:
    logger = Logger("test-logger", log_level=DEBUG)
    called = False
    with logger.span("test-span") as span:
        called = True
        assert span is None
    assert called
