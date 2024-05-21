from colorama import just_fix_windows_console
from pathlib import Path
from platform import system
import os
import sys


def init_rpycli():
    just_fix_windows_console()


def invoke_main(func):
    def munge(argv):
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

    func(cwd=Path(os.getcwd()).resolve(), argv=munge(sys.argv[1:]))