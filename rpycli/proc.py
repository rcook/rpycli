from rpycli.error import ReportableError
from subprocess import PIPE, Popen, STDOUT
from contextlib import contextmanager
import shlex


@contextmanager
def proc_stream(ctx, op, command, text=True, encoding="utf-8", errors="replace"):
    c = [str(x) for x in command]
    command_str = shlex.join(c)

    if ctx.dry_run:
        ctx.log_info(f"dry run: skipping command: {command_str}")
        yield None, []
    else:
        ctx.log_info(f"command: {command_str}")
        with ctx.span(op):
            with Popen(c, stdout=PIPE, stderr=STDOUT, text=False) as proc:
                stdout = iter(proc.stdout.readline, b"")
                if text:
                    stdout=map(lambda b: b.decode(encoding=encoding, errors=errors), stdout)
                yield proc, stdout

            proc.wait()
            if proc.returncode != 0:
                raise ReportableError(
                    f"{op} failed with exit code {proc.returncode}: pass \"--log debug\" to get more details")
