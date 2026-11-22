import inspect

from ..utils import typename

from .error import ToolError
from .kinds import kind_of
from .resolve import resolve


def get_source(namespace, target, plugins):
    """
    Returns the source code of a function, class or module; for an instance, of its class.
    Read it to understand how something works instead of guessing.
    """
    obj = resolve(namespace, target)
    if kind_of(obj) is not None:
        return read_source(obj, f"`{target}`")
    return read_source(type(obj), f"`{target}`, an instance of {typename(obj)}")


def read_source(obj, description):
    try:
        return inspect.getsource(obj)
    except (OSError, TypeError): # e.g., builtins, or classes defined interactively
        raise ToolError(f"no source available for {description}")


