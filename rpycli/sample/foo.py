from rpycli.logger import LoggerProtocol


class Foo:
    def run(self, logger: LoggerProtocol) -> None:
        logger.info("info")
        with logger.span("path", "to", "foo span"):
            logger.info("in foo span")
