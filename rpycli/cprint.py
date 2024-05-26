from colorama import Style
from io import StringIO
from typing import Any
import sys


def cprint(fore: str, *args: Any, **kwargs: Any) -> None:
    file = kwargs.pop("file", sys.stdout)
    with StringIO() as stream:
        print(*args, **kwargs, file=stream)
        print(fore + stream.getvalue() + Style.RESET_ALL, end="", file=file)
