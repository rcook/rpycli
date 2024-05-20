from colorama import Style
from io import StringIO
import sys


def cprint(fore, *args, **kwargs):
    file = kwargs.pop("file", sys.stdout)
    with StringIO() as stream:
        print(*args, **kwargs, file=stream)
        print(fore + stream.getvalue() + Style.RESET_ALL, end="", file=file)
