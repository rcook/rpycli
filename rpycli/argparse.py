from functools import cached_property
from pathlib import Path
import argparse
import inspect
import sys


MISSING = object()


def path(cwd, s):
    return Path(cwd, Path(s).expanduser()).resolve()


class ArgumentParser(argparse.ArgumentParser):
    @staticmethod
    def invoke_func(args, **kwargs):
        def get_value(name):
            value = kwargs.pop(name, MISSING)
            if value is not MISSING:
                return value
            return getattr(args, name)

        func = args.func
        spec = inspect.getfullargspec(func)
        d = {name: get_value(name) for name in spec.args}
        result = func(**d, **kwargs)
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

    def add_argument(self, *args, **kwargs):
        help = kwargs.get("help", MISSING)
        if help is not MISSING:
            default = kwargs.get("default", MISSING)
            if default is not MISSING and default != "==SUPPRESS==":
                kwargs["help"] = f"{help} (default: {default})"

        return super().add_argument(*args, **kwargs)

    def run(self, argv, **kwargs):
        args = self.parse_args(argv)
        self.__class__.invoke_func(args, **kwargs)

    @cached_property
    def _commands(self):
        return self.add_subparsers(required=True, dest="command")
