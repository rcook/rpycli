from argparse import Namespace
from contextlib import contextmanager
from dataclasses import dataclass, make_dataclass
from rpycli.logger import Logger, LoggerProtocol
from typing import Any, Generator, Optional, Protocol, TypeVar


SKIP_ARGS: list[str] = ["command", "func"]


class ContextBaseProtocol(Protocol):
    @property
    def logger(self) -> LoggerProtocol:
        raise NotImplementedError()


class ContextMixin:
    def log_debug(self: ContextBaseProtocol, *args: Any, **kwargs: Any):
        self.logger.debug(*args, **kwargs)

    def log_info(self: ContextBaseProtocol, *args: Any, **kwargs: Any):
        self.logger.info(*args, **kwargs)

    def log_warning(self: ContextBaseProtocol, *args: Any, **kwargs: Any):
        self.logger.warning(*args, **kwargs)

    def log_error(self: ContextBaseProtocol, *args: Any, **kwargs: Any):
        self.logger.error(*args, **kwargs)

    def log_fatal(self: ContextBaseProtocol, *args: Any, **kwargs: Any):
        self.logger.fatal(*args, **kwargs)

    @contextmanager
    def log_span(self: ContextBaseProtocol, *name: str) -> Generator[None, None, None]:
        with self.logger.span(*name) as span:
            yield span


_T3 = TypeVar("_T3", bound="Context")


@dataclass(frozen=True)
class Context(ContextMixin):
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
