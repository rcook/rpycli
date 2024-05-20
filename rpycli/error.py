class ReportableError(RuntimeError):
    def __init__(self, *args, exit_code=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._exit_code = 1 if exit_code is None else exit_code

    @property
    def exit_code(self): return self._exit_code


class UserCancelledError(RuntimeError):
    pass
