from logging import DEBUG
from rpycli.logger import Logger
from rpycli.sample.foo import Foo


def main() -> None:
    logger = Logger("logger", DEBUG)
    logger.info("info")

    with logger.span():
        pass

    with logger.span("path", "to", "main span"):
        logger.info("in main span")
        foo = Foo()
        foo.run(logger)

    logger.error("error")


if __name__ == "__main__":
    main()
