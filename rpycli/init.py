from colorama import just_fix_windows_console
from pathlib import Path
from platform import system
from typing import Protocol, TypeVar
import sys


def init_rpycli() -> None:
    just_fix_windows_console()


T = TypeVar("T", covariant=True)


class MainCallable(Protocol[T]):
    def __call__(
            self,
            cwd: Path,
            argv: list[str]) -> T:
        raise NotImplementedError()


def call_main(func: MainCallable[T], init: bool = True) -> T:
    def munge(argv: list[str]) -> list[str]:
        if system() != "Windows":
            return argv

        import win32api
        command_line = win32api.GetCommandLine()

        new_argv = []
        for arg in argv:
            quote_index = arg.find("\"")
            if quote_index != -1:
                prefix = arg[:quote_index]
                prefix_index = command_line.find("\"" + prefix + "\\\"")
                if prefix_index != -1:
                    new_argv.append(prefix)
                    suffix = arg[quote_index + 1:].lstrip(" ")
                    if len(suffix) > 0:
                        new_argv.append(suffix)
                    continue
            new_argv.append(arg)
        return new_argv

    if init:
        init_rpycli()

    return func(cwd=Path.cwd(), argv=munge(sys.argv[1:]))
