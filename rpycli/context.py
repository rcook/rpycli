from argparse import Namespace
from colorama import Fore, Style
from contextlib import contextmanager
from dataclasses import dataclass, make_dataclass
from datetime import timedelta
from functools import cache, partialmethod
from inspect import FrameInfo
from rpycli.log_level import LogLevel
from rpycli.logging import LoggerProtocol
from time import perf_counter
from types import ModuleType
from typing import Any, Generator, Optional, TypeVar, no_type_check
import contextlib
import inspect
import logging
import sys


SKIP_ARGS: list[str] = ["command", "func"]


_T0 = TypeVar("_T0", bound="LoggerMeta")


class LoggerMeta(type):
    def __new__(cls: type[_T0], name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> _T0:
        @no_type_check
        def get_calling_module(records: list[FrameInfo]) -> ModuleType:
            for record in records:
                frame = record[0]
                module = inspect.getmodule(frame)
                assert module is not None
                if module != this_module and module != contextlib:
                    return module
            raise RuntimeError()

        def log(self: Any, log_level: str, *args: Any, **kwargs: Any) -> None:
            module = get_calling_module(inspect.stack())
            logger = self.__class__._get_logger(
                context_name=self.name,
                log_level=self.log_level,
                name=module.__name__)
            method = getattr(logger, log_level)
            method(*args, **kwargs)

        this_module = sys.modules[__name__]
        t = super().__new__(cls, name, bases, namespace)
        for l in LogLevel:
            name = l.name.lower()
            setattr(t, name, partialmethod(log, name))
        return t


@dataclass(frozen=True)
class Logger(metaclass=LoggerMeta):
    name: Optional[str]
    log_level: int

    @contextmanager
    @no_type_check
    def span(self, name: str) -> Generator[None, None, None]:
        def report_end(log_level: str, disposition: str) -> None:
            duration = timedelta(seconds=perf_counter() - start_time)
            method = getattr(self, log_level)
            method(f"[{name}] {disposition} after {duration}")

        start_time = perf_counter()
        self.info(f"[{name}] started")  # type: ignore
        try:
            yield
            report_end(log_level="info", disposition="completed")
        except:
            report_end(log_level="error", disposition="failed")
            raise

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


_T1 = TypeVar("_T1", bound="ContextMeta")


class ContextMeta(type):
    def __new__(cls: type[_T1], name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> _T1:
        def log(self: Any, log_level: str, *args: Any, **kwargs: Any) -> None:
            method = getattr(self.logger, log_level)
            method(*args, **kwargs)

        t = super().__new__(cls, name, bases, namespace)
        for l in LogLevel:
            name = l.name.lower()
            setattr(t, f"log_{name}", partialmethod(log, name))
        return t


_T3 = TypeVar("_T3", bound="Context")


@dataclass(frozen=True)
class Context(metaclass=ContextMeta):
    logger: LoggerProtocol

    @classmethod
    @no_type_check
    def from_args(cls: type[_T3], args: Namespace, name: Optional[str] = None, **kwargs: Any) -> _T3:
        @no_type_check
        def encode_arg_value(obj: Any) -> str:
            match obj:
                case list() as items:
                    return f"[{', '.join(encode_arg_value(item) for item in items)}]"
                case _: return str(obj)

        d: dict[str, Any] = {}
        d.update(args.__dict__)
        d.update(kwargs)

        log_level = d.pop("log_level").value
        for k in SKIP_ARGS:
            try:
                del d[k]
            except KeyError:
                pass

        ctx_cls = make_dataclass(
            cls_name=f"{cls.__name__}_WRAPPED",
            fields=[(k, type(v)) for k, v in d.items()],
            bases=(cls,),
            frozen=True)

        logger = Logger(name=name, log_level=log_level)
        ctx = ctx_cls(logger=logger, **d)
        for k in sorted(args.__dict__.keys() - SKIP_ARGS):
            s = encode_arg_value(args.__dict__[k])
            ctx.log_info(f"{k} = {s}")

        return ctx

    @contextmanager
    def span(self, name: str) -> Generator[None, None, None]:
        with self.logger.span(name=name):
            yield


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
