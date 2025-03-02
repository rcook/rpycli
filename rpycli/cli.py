from argparse import \
    Action, \
    ArgumentTypeError, \
    BooleanOptionalAction, \
    Namespace
from dataclasses import \
    MISSING, \
    _MISSING_TYPE  # type: ignore[reportPrivateUsage]
from enum import StrEnum, Enum
from functools import cached_property
from pathlib import Path
from rpycli.arg_enum import ArgEnum
from rpycli.log_level import LogLevel
from typing import Any, Optional, Protocol, Self, Sequence, Tuple, TypeVar, cast, overload
import argparse
import rpycli.invoke
import sys


class ArgumentParserProtocol(Protocol):
    def add_enum_argument(self, *args: Any, type: Any, default: Any, converters: Tuple[Any, Any] | _MISSING_TYPE = MISSING, **kwargs: Any) -> Action:
        raise NotImplementedError()

    def add_argument(self, *args: Any, redact: bool | _MISSING_TYPE = MISSING, **kwargs: Any) -> Action:
        raise NotImplementedError()


def path(cwd: Path, s: str) -> Path:
    return Path(cwd, Path(s).expanduser()).resolve()


_T0 = TypeVar("_T0", covariant=True)


class CommandCallable(Protocol[_T0]):
    def __call__(self, *args: Any, **kwargs: Any) -> _T0:
        raise NotImplementedError()


_N = TypeVar("_N")


class ArgumentParser(argparse.ArgumentParser):
    @staticmethod
    def invoke_func(args: Namespace, **kwargs: Any) -> None:
        d = args.__dict__.copy()
        func = d.pop("func")
        result = rpycli.invoke.invoke_func(func=func, **d, **kwargs)
        match result:
            case None: pass
            case bool() as b if not b: sys.exit(1)
            case bool() as b if b: pass
            case int() as exit_code if exit_code != 0: sys.exit(exit_code)
            case _: raise NotImplementedError(f"Unsupported result {result}")

    def add_command(self, *args: Any, func: CommandCallable[_T0], **kwargs: Any) -> Self:
        parser = self.add_command_group(*args, **kwargs)
        parser.set_defaults(func=func)
        return parser

    def add_command_group(self, *args: Any, **kwargs: Any) -> Self:
        help = kwargs.get("help", MISSING)
        if help is not MISSING and len(help) > 0 and "description" not in kwargs:
            kwargs["description"] = help[0].upper() + help[1:]

        parser = self._commands.add_parser(*args, **kwargs)

        assert not hasattr(parser, "_RPYCLI_parent")
        setattr(parser, "_RPYCLI_parent", self)

        return cast(Self, parser)

    def add_argument(self, *args: Any, redact: bool | _MISSING_TYPE = MISSING, **kwargs: Any) -> Action:
        help = kwargs.get("help", MISSING)
        if help is not MISSING:
            default = kwargs.get("default", MISSING)
            if default is not MISSING and default != "==SUPPRESS==":
                if redact is not MISSING and redact:
                    default_str = "(redacted)"
                else:
                    match default:
                        case bool() as b: default_str = "(true)" if b else "(false)"
                        case _: default_str = str(default)
                kwargs["help"] = f"{help} (default: {default_str})"

        dest = kwargs.get("dest", MISSING)
        if dest is not MISSING and "metavar" not in kwargs:
            kwargs["metavar"] = dest.upper()

        return super().add_argument(*args, **kwargs)

    def add_enum_argument(self, *args: Any, type: Any, default: Any, converters: Tuple[Any, Any] | _MISSING_TYPE = MISSING, **kwargs: Any) -> Action:
        from_str: Any
        if converters is not MISSING:
            from_str, to_str = converters
            to_str = to_str.fget if isinstance(to_str, property) else to_str
        elif issubclass(type, ArgEnum):
            from_str = type.from_arg
            to_str = type.arg.fget
        elif issubclass(type, StrEnum):
            from_str = type
            to_str = str
        elif issubclass(type, Enum):
            def temp(s: str) -> Any:
                for member in type:
                    if str(member) == s:
                        return member
                raise ValueError(f"invalid value '{s}'")
            from_str = temp
            to_str = str
        else:
            raise NotImplementedError()

        assert to_str is not None
        choices_str = ", ".join(to_str(m) for m in type)

        def from_str_wrapped(s: str) -> Any:
            try:
                return from_str(s)
            except ValueError:
                one_of = f"(choose one of: {choices_str})"
                raise ArgumentTypeError(f"invalid choice '{s}' {one_of}")

        help = kwargs.get("help", MISSING)
        if help is not MISSING:
            kwargs["help"] = f"{help} (one of: {choices_str})"

        return self.add_argument(
            *args,
            type=from_str_wrapped,
            choices=list(type),
            default=to_str(default),
            **kwargs)

    @overload
    def parse_args(self, args: Sequence[str] | None = None, namespace: None = None) -> Namespace:
        raise NotImplementedError()

    @overload
    def parse_args(self, args: Sequence[str] | None, namespace: _N) -> _N:
        raise NotImplementedError()

    @overload
    def parse_args(self, *, namespace: _N) -> _N:
        raise NotImplementedError()

    def parse_args(self, args: Optional[Sequence[str]] = None, namespace: Any = None) -> Any:
        namespace = super().parse_args(args=args, namespace=namespace)

        command: list[Any] = []
        i = 1
        while True:
            k = f"command{i}"
            c = getattr(namespace, k, None)
            if c is None:
                break
            delattr(namespace, k)
            command.append(c)
            i += 1

        setattr(namespace, "command", command)

        return namespace

    def run(self, argv: Optional[Sequence[str]], **kwargs: Any) -> None:
        args = self.parse_args(argv)
        self.__class__.invoke_func(args, **kwargs)

    @cached_property
    def _commands(self) -> Any:
        parent = getattr(self, "_RPYCLI_parent", None)
        if parent is not None:
            group_action = parent._subparsers._group_actions[0]
            depth = group_action._RPYCLI_depth + 1
        else:
            depth = 1

        subparsers = self.add_subparsers(
            required=True,
            dest=f"command{depth}")

        assert not hasattr(subparsers, "_RPYCLI_depth")
        setattr(subparsers, "_RPYCLI_depth", depth)

        return subparsers


class CommonArgumentsMixin:
    def add_log_level_argument(self: ArgumentParserProtocol) -> Action:
        return self.add_enum_argument(
            "--log",
            "-l",
            dest="log_level",
            type=LogLevel,
            default=LogLevel.INFO,
            help="log level")

    def add_dry_run_argument(self: ArgumentParserProtocol) -> Action:
        return self.add_argument(
            "--dry-run",
            dest="dry_run",
            action=BooleanOptionalAction,
            required=False,
            default=True,
            help="dry run")

    def add_force_argument(self: ArgumentParserProtocol) -> Action:
        return self.add_argument(
            "--force",
            "-f",
            dest="force",
            action=BooleanOptionalAction,
            required=False,
            default=False,
            help="force overwrite")
