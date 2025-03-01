from argparse import Action, ArgumentTypeError, BooleanOptionalAction, Namespace, _SubParsersAction
from dataclasses import MISSING, _MISSING_TYPE
from enum import StrEnum, Enum
from functools import cached_property
from pathlib import Path
from rpycli.arg_enum import ArgEnum
from rpycli.log_level import LogLevel
from typing import Any, Protocol, Self, Sequence, Tuple, TypeVar, no_type_check, override
import argparse
import rpycli.invoke
import sys


class ArgumentParserProtocol(Protocol):
    def add_enum_argument(self, *args: Any, type, default, converters: Tuple[Any, Any] | _MISSING_TYPE = MISSING, **kwargs: Any) -> Action:
        raise NotImplementedError()

    def add_argument(self, *args: Any, redact: bool | _MISSING_TYPE = MISSING, **kwargs: Any) -> Action:
        raise NotImplementedError()


def path(cwd: Path, s: str) -> Path:
    return Path(cwd, Path(s).expanduser()).resolve()


T = TypeVar("T", covariant=True)


class CommandCallable(Protocol[T]):
    def __call__(self, *args: Any, **kwargs: Any) -> T:
        raise NotImplementedError()


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

    def add_command(self, *args: Any, func: CommandCallable, **kwargs: Any) -> Self:
        parser = self.add_command_group(*args, **kwargs)
        parser.set_defaults(func=func)
        return parser

    def add_command_group(self, *args: Any, **kwargs: Any) -> Self:
        help = kwargs.get("help", MISSING)
        if help is not MISSING and len(help) > 0 and "description" not in kwargs:
            kwargs["description"] = help[0].upper() + help[1:]
        parser = self._commands.add_parser(*args, **kwargs)

        assert not hasattr(parser, "_RPYCLI_parent")
        parser._RPYCLI_parent = self

        return parser

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

    def add_enum_argument(self, *args: Any, type, default, converters: Tuple[Any, Any] | _MISSING_TYPE = MISSING, **kwargs: Any) -> Action:
        if converters is not MISSING:
            from_str, to_str = converters
            to_str = to_str.fget if isinstance(to_str, property) else to_str
        elif issubclass(type, ArgEnum):
            from_str = type.from_arg
            to_str = type.arg.fget
        elif issubclass(type, StrEnum):
            from_str = type  # type: ignore[reportAssignmentType]
            to_str = str
        elif issubclass(type, Enum):
            def from_str(s):
                for member in type:
                    if str(member) == s:
                        return member
                raise ValueError(f"invalid value '{s}'")
            to_str = str
        else:
            raise NotImplementedError()

        assert from_str is not None and to_str is not None

        choices_str = ", ".join(
            to_str(m)  # type: ignore[reportCallIssue]
            for m in type)

        def from_str_wrapped(s: str):
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

    @override
    @no_type_check
    def parse_args(self, args: Any = None, namespace: Any = None) -> Any:
        namespace = super().parse_args(args=args, namespace=namespace)

        command = []
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

    def run(self, argv: Sequence[str] | None, **kwargs: Any):
        args = self.parse_args(argv)
        self.__class__.invoke_func(args, **kwargs)

    @cached_property
    @no_type_check
    def _commands(self) -> _SubParsersAction:
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
        subparsers._RPYCLI_depth = depth

        return subparsers


class CommonArgumentsMixin(ArgumentParserProtocol):
    def add_log_level_argument(self) -> Action:
        return self.add_enum_argument(
            "--log",
            "-l",
            dest="log_level",
            type=LogLevel,
            default=LogLevel.INFO,
            help="log level")

    def add_dry_run_argument(self) -> Action:
        return self.add_argument(
            "--dry-run",
            dest="dry_run",
            action=BooleanOptionalAction,
            required=False,
            default=True,
            help="dry run")

    def add_force_argument(self) -> Action:
        return self.add_argument(
            "--force",
            "-f",
            dest="force",
            action=BooleanOptionalAction,
            required=False,
            default=False,
            help="force overwrite")
