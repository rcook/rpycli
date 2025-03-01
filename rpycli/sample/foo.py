from rpycli.logging import LoggerProtocol


class Foo:
    def run(self, logger: LoggerProtocol) -> None:
        logger.info("info")
        with logger.span("foo span"):
            logger.info("in foo span")
