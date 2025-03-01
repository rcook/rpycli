from logging import DEBUG
from rpycli.context import Context
from rpycli.logger import Logger


def test_context() -> None:
    logger = Logger("test-logger", log_level=DEBUG)
    ctx = Context(logger)
    called = False

    ctx.log_info("info")
    ctx.log_warning("warning")

    with ctx.log_span("test-span") as span:
        called = True
        assert span is None

    assert called
