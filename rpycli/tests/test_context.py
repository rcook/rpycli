from argparse import Namespace
from logging import DEBUG
from rpycli.context import Context, ContextProtocol
from rpycli.log_level import LogLevel
from rpycli.logger import Logger


def test_context() -> None:
    def check_protocol(ctx: ContextProtocol) -> None:
        assert ctx.log_level == 123
        ctx.log_fatal("fatal")

    logger = Logger("test-logger", 123)
    ctx = Context(logger)
    called = False

    ctx.log_info("info")
    ctx.log_warning("warning")

    with ctx.log_span("test-span") as span:
        called = True
        assert span is None

    assert called

    check_protocol(ctx)


def test_context_from_args() -> None:
    args = Namespace()
    args.log_level = LogLevel.DEBUG
    ctx = Context.from_args(args, "context")
    assert ctx.log_level == DEBUG
