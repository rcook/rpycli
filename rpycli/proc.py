from contextlib import contextmanager
from rpycli.error import ReportableError
from rpycli.logging import LoggerProtocol
from subprocess import PIPE, Popen, STDOUT
from typing import Any, Iterator, Never, Tuple
import shlex


@contextmanager
def proc_stream(logger: LoggerProtocol, op: str, command: list[Any], dry_run: bool = True, text: bool = True, encoding: str = "utf-8", errors: str = "replace") -> Iterator[Tuple[Popen[bytes] | None, list[Never] | Iterator[bytes] | Iterator[str]]]:
    c = [str(x) for x in command]
    command_str = shlex.join(c)

    if dry_run:
        logger.info(f"dry run: skipping command: {command_str}")
        yield None, []
    else:
        logger.info(f"command: {command_str}")
        with logger.span(op):
            with Popen(c, stdout=PIPE, stderr=STDOUT, text=False) as proc:
                assert proc.stdout is not None
                stdout = iter(proc.stdout.readline, b"")
                if text:
                    yield proc, map(
                        lambda b: b.decode(encoding=encoding, errors=errors),
                        stdout)
                else:
                    yield proc, stdout

            proc.wait()
            if proc.returncode != 0:
                raise ReportableError(
                    f"{op} failed with exit code {proc.returncode}: pass \"--log debug\" to get more details")
