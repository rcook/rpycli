from logging import DEBUG
from rpycli.context import Logger
from rpycli.sample.foo import Foo


def main() -> None:
    logger = Logger("sample-logger", DEBUG)
    logger.info("info")
    with logger.span("main span"):
        logger.info("in main span")
        foo = Foo()
        foo.run(logger)


if __name__ == "__main__":
    main()
