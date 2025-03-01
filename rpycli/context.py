from argparse import Namespace
from contextlib import contextmanager
from dataclasses import dataclass, make_dataclass
from rpycli.logger import Logger, LoggerProtocol
from typing import Any, Generator, Optional, Protocol, TypeVar, cast


SKIP_ARGS: list[str] = ["command", "func"]


class ContextBaseProtocol(Protocol):
    @property
    def logger(self) -> LoggerProtocol:
        raise NotImplementedError()


class ContextProtocol(Protocol):
    @property
    def log_level(self) -> int:
        raise NotImplementedError()

    def log_debug(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()

    def log_info(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()

    def log_warning(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()

    def log_error(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()

    def log_fatal(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()

    @contextmanager
    def log_span(self, *name: str) -> Generator[None, None, None]:
        raise NotImplementedError()


class ContextMixin:
    @property
    def log_level(self: ContextBaseProtocol) -> int:
        return self.logger.level

    def log_debug(self: ContextBaseProtocol, *args: Any, **kwargs: Any) -> None:
        self.logger.debug(*args, **kwargs)

    def log_info(self: ContextBaseProtocol, *args: Any, **kwargs: Any) -> None:
        self.logger.info(*args, **kwargs)

    def log_warning(self: ContextBaseProtocol, *args: Any, **kwargs: Any) -> None:
        self.logger.warning(*args, **kwargs)

    def log_error(self: ContextBaseProtocol, *args: Any, **kwargs: Any) -> None:
        self.logger.error(*args, **kwargs)

    def log_fatal(self: ContextBaseProtocol, *args: Any, **kwargs: Any) -> None:
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
            if isinstance(obj, list):
                return f"[{', '.join(encode_arg_value(item) for item in obj)}]"
            else:
                return str(obj)

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
            fields=[(k, cast(object, type(v))) for k, v in d.items()],
            bases=(cls,),
            frozen=True)

        logger = Logger(name=name, level=log_level)
        ctx = ctx_cls(logger=logger, **d)
        for k in sorted(args.__dict__.keys() - SKIP_ARGS):
            s = encode_arg_value(args.__dict__[k])
            ctx.log_info(f"{k} = {s}")

        return cast(_T3, ctx)
