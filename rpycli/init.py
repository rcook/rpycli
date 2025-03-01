from colorama import Fore, just_fix_windows_console
from pathlib import Path
from platform import system
from rpycli.cprint import cprint
from rpycli.error import ReportableError, UserCancelledError
from types import TracebackType
from typing import Protocol, TypeVar, no_type_check
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
    @no_type_check
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


def cli_exception_hook(exctype: type[BaseException], value: BaseException, traceback: TracebackType | None) -> None:
    match value:
        case ReportableError() as e:
            m = str(e)
            m = f"(Unknown error with exit code {e.exit_code})" \
                if len(m) == 0 \
                else m
            cprint(Fore.LIGHTRED_EX, m, file=sys.stderr)
            sys.exit(e.exit_code)
        case KeyboardInterrupt() | UserCancelledError() as e:
            m = str(e)
            m = "Operation cancelled by user" \
                if len(m) == 0 \
                else f"Operation cancelled by user: {m}"
            cprint(Fore.LIGHTBLUE_EX, m)
            sys.exit(0)
        case _: sys.__excepthook__(exctype, value, traceback)
