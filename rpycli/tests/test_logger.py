from logging import DEBUG
from dataclasses import dataclass
from rpycli.logger import Logger, LoggerMixin, LoggerProtocol
from typing import Any


def test_logger_mixin() -> None:
    @dataclass(frozen=False)
    class MyLogger(LoggerMixin):
        level: int
        log_call_count: int = 0

        def log(self, level_name: str, *args: Any, **kwargs: Any) -> None:
            self.log_call_count += 1

    def check_protocol(logger: LoggerProtocol) -> None:
        assert logger.level == 123
        logger.fatal("fatal")

    logger = MyLogger(level=123)
    assert logger.log_call_count == 0
    logger.info("info")
    assert logger.log_call_count == 1
    logger.debug("debug")
    assert logger.log_call_count == 2

    check_protocol(logger)
    assert logger.log_call_count == 3

    span_entered = False

    with logger.span("span"):
        assert logger.log_call_count == 4
        span_entered = True

    assert span_entered

    assert logger.log_call_count == 5


def test_logger() -> None:
    logger = Logger("logger", DEBUG)
    logger.info("info")

    called = False

    with logger.span("test-span") as span:
        called = True
        assert span is None

    assert called
