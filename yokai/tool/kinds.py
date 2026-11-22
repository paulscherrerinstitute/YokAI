import inspect
from types import ModuleType

from ..staticinspect import ROUTINE_TYPES


METHOD_WRAPPERS = (staticmethod, classmethod)


def kind_of(obj):
    """
    Returns "module", "class" or "function", or None for an instance (of anything else).
    """
    # type(obj), never isinstance(obj, …), which may read obj.__class__
    cls = type(obj)
    if issubclass(cls, ModuleType):
        return "module"
    if issubclass(cls, type):
        return "class"
    if issubclass(cls, ROUTINE_TYPES):
        return "function"
    return None


def is_data_descriptor(obj):
    # like inspect.isdatadescriptor, but static:
    # isinstance may read obj.__class__ and
    # hasattr on the class may run its metaclass's __getattr__
    cls = type(obj)
    return has_static(cls, "__set__") or has_static(cls, "__delete__")


def has_static(obj, name):
    missing = object()
    return inspect.getattr_static(obj, name, missing) is not missing


def unwrap_method(obj):
    if issubclass(type(obj), METHOD_WRAPPERS):
        return obj.__func__
    return obj


