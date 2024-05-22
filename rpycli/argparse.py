from argparse import BooleanOptionalAction
from functools import cached_property
from pathlib import Path
from rpycli.context import DEFAULT_LOG_LEVEL_NAME, LOG_LEVEL_NAMES
import argparse
import inspect
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
        help = kwargs.get("help", MISSING)
        if help is not MISSING and len(help) > 0 and "description" not in kwargs:
            kwargs["description"] = help[0].upper() + help[1:]
        parser = self._commands.add_parser(*args, **kwargs)
        parser.set_defaults(func=func)
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

    def run(self, argv, **kwargs):
        args = self.parse_args(argv)
        self.__class__.invoke_func(args, **kwargs)

    @cached_property
    def _commands(self):
        return self.add_subparsers(required=True, dest="command")


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
