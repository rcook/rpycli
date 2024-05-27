from enum import unique
from rpycli.arg_enum import ArgEnum
import logging


@unique
class LogLevel(ArgEnum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    FATAL = logging.FATAL
