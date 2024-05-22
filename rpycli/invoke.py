from inspect import getfullargspec


def invoke_func(func, **kwargs):
    spec = getfullargspec(func)
    d = {name: kwargs.pop(name) for name in spec.args}
    kwargs = {} if spec.varkw is None else kwargs
    return func(**d, **kwargs)
