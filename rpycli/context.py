from argparse import Namespace
from colorama import Fore, Style
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, make_dataclass
from datetime import timedelta
from functools import cache, partialmethod
from inspect import FrameInfo
from rpycli.logging import LogLevel, LoggerProtocol
from time import perf_counter
from types import ModuleType
from typing import Any, Generator, Tuple
import contextlib
import inspect
import logging
import sys


SKIP_ARGS: list[str] = ["command", "func"]


class LoggerMeta(type):
    def __new__(cls, name: str, bases: Tuple[type, ...], namespace: dict[str, Any]) -> "LoggerMeta":
        def get_calling_module(records: list[FrameInfo]) -> ModuleType:
            for record in records:
                frame = record[0]
                module = inspect.getmodule(frame)
                assert module is not None
                if module != this_module and module != contextlib:
                    return module
            raise RuntimeError()

        def log(self, log_level: str, *args: Any, **kwargs: Any) -> None:
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
    name: str | None
    log_level: int

    @contextmanager
    def span(self, name: list | str | None) -> Generator:
        match name:
            case list() | tuple() as names: name = "/".join(str(x) for x in names)
            case _: name = str(name)

        def report_end(log_level, disposition):
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
    def _get_logger(context_name: str | None, log_level: int, name: str) -> logging.Logger:
        name = context_name \
            if name == "__main__" and context_name is not None \
            else name
        formatter = logging.Formatter(
            Fore.LIGHTMAGENTA_EX + "[%(asctime)s] " +
            Fore.LIGHTYELLOW_EX + "[%(name)s] " +
            Fore.LIGHTCYAN_EX + "[%(levelname)s] " +
            Fore.LIGHTGREEN_EX + "%(message)s" +
            Style.RESET_ALL)
        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        handler.setFormatter(formatter)
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        logger.addHandler(handler)
        return logger


class ContextMeta(type):
    def __new__(cls, name: str, bases: Tuple[type, ...], namespace: dict[str, Any]) -> "ContextMeta":
        def log(self, log_level: str, *args: Any, **kwargs: Any) -> None:
            method = getattr(self.logger, log_level)
            method(*args, **kwargs)

        t = super().__new__(cls, name, bases, namespace)
        for l in LogLevel:
            name = l.name.lower()
            setattr(t, f"log_{name}", partialmethod(log, name))
        return t


@dataclass(frozen=True)
class Context(metaclass=ContextMeta):
    logger: LoggerProtocol

    @classmethod
    def from_args(cls, args: Namespace, name: str | None = None) -> "Context":
        def encode_arg_value(obj: Any) -> str:
            match obj:
                case list() as items:
                    return f"[{', '.join(encode_arg_value(item) for item in items)}]"
                case _: return str(obj)

        d = args.__dict__.copy()
        log_level = d.pop("log_level").value
        for k in SKIP_ARGS:
            del d[k]

        ctx_cls = make_dataclass(
            cls_name="Context",
            fields=[(k, type(v)) for k, v in d.items()],
            bases=(cls,),
            frozen=True)

        logger = Logger(name=name, log_level=log_level)
        ctx = ctx_cls(logger=logger, **d)
        for k in sorted(args.__dict__.keys() - SKIP_ARGS):
            s = encode_arg_value(args.__dict__[k])
            ctx.log_info(f"{k} = {s}")

        return ctx

    def span(self, *args: Any, **kwargs: Any) -> AbstractContextManager:
        return self.logger.span(*args, **kwargs)
