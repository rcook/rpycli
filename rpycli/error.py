from typing import Any


class ReportableError(RuntimeError):
    def __init__(self, *args: Any, exit_code: int | None = None, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._exit_code = 1 if exit_code is None else exit_code

    @property
    def exit_code(self) -> int: return self._exit_code


class UserCancelledError(RuntimeError):
    pass
