from argparse import BooleanOptionalAction
from enum import StrEnum, Enum
from functools import cached_property
from pathlib import Path
from rpycli.context import DEFAULT_LOG_LEVEL_NAME, LOG_LEVEL_NAMES
import argparse
import rpycli.invoke
import sys


MISSING = object()


def path(cwd, s):
    return Path(cwd, Path(s).expanduser()).resolve()


class ArgumentParser(argparse.ArgumentParser):
    @staticmethod
    def invoke_func(args, **kwargs):
        d = args.__dict__.copy()
        func = d.pop("func")
        result = rpycli.invoke.invoke_func(func=func, **d, **kwargs)
        match result:
            case None: pass
            case bool() as b if not b: sys.exit(1)
            case bool() as b if b: pass
            case int() as exit_code if exit_code != 0: sys.exit(exit_code)
            case _: raise NotImplementedError(f"Unsupported result {result}")

    def add_command(self, *args, func, **kwargs):
        parser = self.add_command_group(*args, **kwargs)
        parser.set_defaults(func=func)
        return parser

    def add_command_group(self, *args, **kwargs):
        help = kwargs.get("help", MISSING)
        if help is not MISSING and len(help) > 0 and "description" not in kwargs:
            kwargs["description"] = help[0].upper() + help[1:]
        parser = self._commands.add_parser(*args, **kwargs)

        assert not hasattr(parser, "_RPYCLI_parent")
        parser._RPYCLI_parent = self

        return parser

    def add_argument(self, *args, redact=MISSING, **kwargs):
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

    def add_enum_argument(self, *args, type, default, converters=None, **kwargs):
        if converters is not None:
            from_str, to_str = converters
        elif issubclass(type, StrEnum):
            def from_str(s):
                try:
                    return type(s)
                except ValueError:
                    raise ArgumentTypeError(f"invalid value '{s}'")
            to_str = str
        elif issubclass(type, Enum):
            def from_str(s):
                for member in type:
                    if str(member) == s:
                        return member
                raise ArgumentTypeError(f"invalid value '{s}'")
            to_str = str
        else:
            raise NotImplementedError()

        help = kwargs.get("help", MISSING)
        if help is not MISSING:
            kwargs["help"] = \
                f"{help} (one of: " \
                f"{', '.join(to_str(m) for m in type)})"

        self.add_argument(
            *args,
            type=from_str,
            choices=list(type),
            default=to_str(default),
            **kwargs)

    def parse_args(self, args=None, namespace=None):
        if args is not None and len(args) == 0:
            self.print_usage()
            sys.exit(2)

        namespace = super().parse_args(args=args, namespace=namespace)

        command = []
        i = 0
        while True:
            k = f"_RPYCLI_command_{i}"
            c = getattr(namespace, k, None)
            if c is None:
                break
            delattr(namespace, k)
            command.append(c)
            i += 1

        setattr(namespace, "command", command)

        return namespace

    def run(self, argv, **kwargs):
        args = self.parse_args(argv)
        self.__class__.invoke_func(args, **kwargs)

    @cached_property
    def _commands(self):
        parent = getattr(self, "_RPYCLI_parent", None)
        if parent is not None:
            group_action = parent._subparsers._group_actions[0]
            depth = group_action._RPYCLI_depth + 1
        else:
            depth = 0

        subparsers = self.add_subparsers(
            required=True,
            dest=f"_RPYCLI_command_{depth}")

        assert not hasattr(subparsers, "_RPYCLI_depth")
        subparsers._RPYCLI_depth = depth

        return subparsers


class CommonArgumentsMixin:
    def add_log_level_argument(self):
        return self.add_argument(
            "--log",
            "-l",
            dest="log_level",
            type=str,
            choices=LOG_LEVEL_NAMES,
            required=False,
            default=DEFAULT_LOG_LEVEL_NAME,
            help=f"log level (one of: {', '.join(LOG_LEVEL_NAMES)})")

    def add_dry_run_argument(self):
        return self.add_argument(
            "--dry-run",
            dest="dry_run",
            action=BooleanOptionalAction,
            required=False,
            default=True,
            help="dry run")

    def add_force_argument(self):
        return self.add_argument(
            "--force",
            "-f",
            dest="force",
            action=BooleanOptionalAction,
            required=False,
            default=False,
            help="force overwrite")
