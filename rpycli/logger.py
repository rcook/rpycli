from contextlib import contextmanager
from colorama import Fore, Style
from dataclasses import dataclass
from datetime import timedelta
from functools import cache
from inspect import FrameInfo
from time import perf_counter
from types import ModuleType
from typing import Any, Generator, Optional, Protocol, no_type_check
import contextlib
import inspect
import logging
import sys


THIS_MODULE: ModuleType = sys.modules[__name__]


SKIP_ARGS: list[str] = ["command", "func"]


class LoggerBaseProtocol(Protocol):
    def log(self, level_name: str, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()


class LoggerProtocol(Protocol):
    @property
    def level(self) -> int:
        raise NotImplementedError()

    def debug(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()

    def info(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()

    def warning(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()

    def error(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()

    def fatal(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()

    @contextmanager
    def span(self, *name: str) -> Generator[None, None, None]:
        raise NotImplementedError()


class LoggerMixin:
    def debug(self: LoggerBaseProtocol, *args: Any, **kwargs: Any) -> None:
        self.log("debug", *args, **kwargs)

    def info(self: LoggerBaseProtocol, *args: Any, **kwargs: Any) -> None:
        self.log("info", *args, **kwargs)

    def warning(self: LoggerBaseProtocol, *args: Any, **kwargs: Any) -> None:
        self.log("warning", *args, **kwargs)

    def error(self: LoggerBaseProtocol, *args: Any, **kwargs: Any) -> None:
        self.log("error", *args, **kwargs)

    def fatal(self: LoggerBaseProtocol, *args: Any, **kwargs: Any) -> None:
        self.log("fatal", *args, **kwargs)

    @contextmanager
    def span(self, *name: str) -> Generator[None, None, None]:
        if len(name) == 0:
            label = "span"
        else:
            label = "[" + "/".join(name) + "]"

        def report_end(level_name: str, disposition: str) -> None:
            duration = timedelta(seconds=perf_counter() - start_time)
            method = getattr(self, level_name)
            method(f"{label} {disposition} after {duration}")

        start_time = perf_counter()
        self.info(f"{label} started")  # type: ignore
        try:
            yield
            report_end(level_name="info", disposition="completed")
        except:
            report_end(level_name="error", disposition="failed")
            raise


@dataclass(frozen=True)
class Logger(LoggerMixin):
    name: Optional[str]
    level: int

    def log(self, level_name: str, *args: Any, **kwargs: Any) -> None:
        module = self.__class__._get_calling_module(inspect.stack())
        logger = self.__class__._get_logger(
            context_name=self.name,
            log_level=0,  # self.log_level,
            name=module.__name__)
        method = getattr(logger, level_name)
        method(*args, **kwargs)

    @staticmethod
    def _get_calling_module(records: list[FrameInfo]) -> ModuleType:
        @no_type_check
        def is_calling_module(module: ModuleType):
            return module != THIS_MODULE and module != contextlib

        for record in records:
            frame = record[0]
            module = inspect.getmodule(frame)
            assert module is not None
            if is_calling_module(module):
                return module

        raise RuntimeError("Could not find calling module")

    @cache
    @staticmethod
    def _get_logger(context_name: Optional[str], log_level: int, name: str) -> logging.Logger:
        name = context_name \
            if name == "__main__" and context_name is not None \
            else name
        formatter = ColouredLevelFormatter(
            Fore.LIGHTMAGENTA_EX + "[%(asctime)s] " +
            Fore.LIGHTYELLOW_EX + "[%(name)s] " +
            "%(level_colour)s[%(levelname)s] " +
            Fore.LIGHTGREEN_EX + "%(message)s" +
            Style.RESET_ALL)
        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        handler.setFormatter(formatter)
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        logger.addHandler(handler)
        return logger


class ColouredLevelFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        match record.levelno:
            case logging.DEBUG: level_colour = Fore.LIGHTMAGENTA_EX
            case logging.INFO: level_colour = Fore.LIGHTWHITE_EX
            case logging.WARNING: level_colour = Fore.LIGHTYELLOW_EX
            case logging.ERROR: level_colour = Fore.RED
            case logging.FATAL: level_colour = Fore.LIGHTRED_EX
            case _: raise NotImplementedError()
        record.level_colour = level_colour
        return super().format(record)
