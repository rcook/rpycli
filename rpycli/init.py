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

        from win32api import GetCommandLine

        command_line = GetCommandLine()
        new_argv = []
        for arg in argv:
            if arg.endswith("\""):
                s = arg.rstrip("\"")
                if command_line.find("\"" + s + "\\\"") != -1:
                    new_argv.append(s)
                    continue
            new_argv.append(arg)
        return new_argv

    func(cwd=Path(os.getcwd()).resolve(), argv=munge(sys.argv[1:]))
