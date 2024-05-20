from colorama import Fore, Style
from contextlib import contextmanager
from dataclasses import dataclass, make_dataclass
from datetime import timedelta
from functools import cache, partialmethod
from time import perf_counter
import contextlib
import inspect
import logging
import sys


DEFAULT_LOG_LEVEL_NAME = logging.getLevelName(logging.INFO).lower()
LOG_LEVEL_NAMES = list(map(lambda p: p[0].lower(), sorted(
    filter(
        lambda p: p[0] not in {"NOTSET", "WARN"},
        logging.getLevelNamesMapping().items()),
    key=lambda p: p[1])))
SKIP_ARGS = ["command", "func"]


class ContextMeta(type):
    def __new__(cls, name, bases, dct):
        def get_calling_module(records):
            for record in records:
                frame = record[0]
                module = inspect.getmodule(frame)
                if module != this_module and module != contextlib:
                    return module
            raise RuntimeError()

        def log(self, log_level, *args, **kwargs):
            module = get_calling_module(inspect.stack())
            logger = self._logger(module.__name__)
            method = getattr(logger, log_level)
            return method(*args, **kwargs)

        this_module = sys.modules[__name__]
        t = super().__new__(cls, name, bases, dct)
        for n in LOG_LEVEL_NAMES:
            setattr(t, f"log_{n}", partialmethod(log, n))
        return t


@dataclass(frozen=True)
class Context(metaclass=ContextMeta):
    name: str | None
    log_level: int

    @classmethod
    def from_args(cls, args, name=None):
        d = args.__dict__.copy()
        log_level = logging.getLevelNamesMapping()[d.pop("log_level").upper()]
        for k in SKIP_ARGS:
            del d[k]

        ctx_cls = make_dataclass(
            cls_name="Context",
            fields=[(k, type(v)) for k, v in d.items()],
            bases=(cls,),
            frozen=True)

        ctx = ctx_cls(name=name, log_level=log_level, **d)
        for k in sorted(args.__dict__.keys() - SKIP_ARGS):
            ctx.log_info(f"{k} = {args.__dict__[k]}")

        return ctx

    @contextmanager
    def span(self, name):
        def report_end(log_level, disposition):
            duration = timedelta(seconds=perf_counter() - start_time)
            getattr(
                self,
                f"log_{log_level}")(f"[{name}] {disposition} after {duration}")

        start_time = perf_counter()
        self.log_info(f"[{name}] started")
        try:
            yield
            report_end(log_level="info", disposition="completed")
        except:
            report_end(log_level="error", disposition="failed")
            raise

    @cache
    def _logger(self, name):
        name = self.name \
            if name == "__main__" and self.name is not None \
            else name
        formatter = logging.Formatter(
            Fore.LIGHTMAGENTA_EX + "[%(asctime)s] " +
            Fore.LIGHTYELLOW_EX + "[%(name)s] " +
            Fore.LIGHTCYAN_EX + "[%(levelname)s] " +
            Fore.LIGHTGREEN_EX + "%(message)s" +
            Style.RESET_ALL)
        handler = logging.StreamHandler()
        handler.setLevel(self.log_level)
        handler.setFormatter(formatter)
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        logger.addHandler(handler)
        return logger
