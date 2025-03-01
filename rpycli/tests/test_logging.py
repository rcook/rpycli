from logging import DEBUG
from rpycli.context import Logger


def test_basics() -> None:
    logger = Logger("test-logger", log_level=DEBUG)
    with logger.span("test-span") as span:
        assert span is None
