from rpycli.error import ReportableError
from subprocess import PIPE, Popen, STDOUT
from contextlib import contextmanager
import shlex


@contextmanager
def proc_stream(ctx, operation, command):
    c = [str(x) for x in command]
    command_str = shlex.join(c)

    if ctx.dry_run:
        ctx.log_info(f"dry run: skipping command: {command_str}")
        yield None, []
    else:
        ctx.log_info(f"command: {command_str}")
        with ctx.span(operation):
            with Popen(c, stdout=PIPE, stderr=STDOUT, text=True) as proc:
                stdout = iter(proc.stdout.readline, "")
                yield proc, stdout

            proc.wait()
            if proc.returncode != 0:
                raise ReportableError(
                    f"{operation} failed with exit code {proc.returncode}: pass \"--log debug\" to get more details")
