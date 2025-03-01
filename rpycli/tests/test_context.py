from logging import DEBUG
from rpycli.context import Context, Logger


def test_context() -> None:
    logger = Logger("test-logger", log_level=DEBUG)
    ctx = Context(logger)
    called = False

    with ctx.span("test-span") as span:
        called = True
        assert span is None

    assert called
