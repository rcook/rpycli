from argparse import Namespace
from contextlib import AbstractContextManager
from dataclasses import dataclass, make_dataclass
from functools import partialmethod
from rpycli.log_level import LogLevel
from rpycli.logger import Logger, LoggerProtocol
from typing import Any, Optional, TypeVar


SKIP_ARGS: list[str] = ["command", "func"]


_T1 = TypeVar("_T1", bound="ContextMeta")


class ContextMeta(type):
    def __new__(cls: type[_T1], name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> _T1:
        def log(self, log_level: str, *args: Any, **kwargs: Any) -> None:
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
    def from_args(cls: type[_T3], args: Namespace, name: Optional[str] = None, **kwargs: Any) -> _T3:
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

    def span(self, *args: Any, **kwargs: Any) -> AbstractContextManager:
        return self.logger.span(*args, **kwargs)
