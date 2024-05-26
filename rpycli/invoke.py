from inspect import getfullargspec
from typing import Any, Callable, TypeVar


T = TypeVar("T")


def invoke_func(func: Callable[..., T], **kwargs: Any) -> T:
    spec = getfullargspec(func)
    d = {name: kwargs.pop(name) for name in spec.args}
    kwargs = {} if spec.varkw is None else kwargs
    return func(**d, **kwargs)
