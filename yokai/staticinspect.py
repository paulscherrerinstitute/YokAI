import inspect
import json
from types import (
    BuiltinFunctionType, FunctionType, MethodType, ModuleType,
    ClassMethodDescriptorType, MethodDescriptorType
)

from .plugin import find_covering_plugin
from .utils import has_class_from, is_in_module, is_str, typename


FUNCTION_TYPES = (BuiltinFunctionType, FunctionType, MethodType)
# methods of builtin classes, e.g., list.append
METHOD_DESCRIPTOR_TYPES = (ClassMethodDescriptorType, MethodDescriptorType)
ROUTINE_TYPES = (*FUNCTION_TYPES, *METHOD_DESCRIPTOR_TYPES)

# exact types only: subclasses (e.g., IntEnum) may have any repr
SAFE_DEFAULT_TYPES = (type(None), bool, int, float, str)

ELIDED = "…"

# YokAI's own objects are those from its package, by module or by type.
# By type covers the plugins and presets as they subclass the core's Plugin and YokAI.
OWN_PACKAGE = __package__


def is_own(obj):
    return is_own_by_module(obj) or is_own_by_type(obj)


def is_own_by_module(obj):
    # not a str for, e.g., methods of builtin objects ([].append)
    return is_in_module(module_name(obj), OWN_PACKAGE)


def is_own_by_type(obj):
    """
    Any object is own if a class in its type's MRO comes from OWN_PACKAGE,
    a class also if a class in its own MRO does.
    """
    # type(obj), never obj.__class__, which may be any object (cf. plugin coverage)
    cls = type(obj)
    if has_class_from(cls, OWN_PACKAGE):
        return True
    return issubclass(cls, type) and has_class_from(obj, OWN_PACKAGE)


def module_name(obj):
    cls = type(obj)
    if issubclass(cls, ModuleType):
        return obj.__name__
    if issubclass(cls, MethodType):
        return module_name(obj.__func__)
    if issubclass(cls, (type, FunctionType, BuiltinFunctionType)):
        return obj.__module__
    return cls.__module__


def format_instance(variable_name, obj, plugins):
    """
    Renders the type of obj and the covering plugin's identification, if any.
    """
    parts = [f"{variable_name}: {typename(obj)}"]
    plugin = find_covering_plugin(obj, plugins)
    if plugin is not None:
        identification = plugin.identification(obj)
        parts.extend(format_identification(identification))
    return ", ".join(parts)


def format_identification(identification):
    """
    Renders each part as label "value", leaving out values that are not of type str.
    """
    return [
        f"{label} {quote(value)}"
        for label, value in identification.items()
        if is_str(value)
    ]


def quote(text):
    # wraps text in double quotes and escapes the quotes and newlines inside it,
    # so that each object keeps to one line in the object list and in describe
    return json.dumps(text, ensure_ascii=False)


def read_instance_dict(obj):
    # Like vars(obj), but never runs the class's attribute hooks.
    # For objects without __dict__, vars() calls custom __getattribute__ and __getattr__.
    # These can have side effects or return another object's __dict__ (proxies).
    try:
        return object.__getattribute__(obj, "__dict__")
    except AttributeError:  # no instance __dict__, e.g., int or __slots__
        return {}


def format_signature(obj):
    """
    Renders the signature of a function or class without annotations (rendering them may call any repr),
    showing only defaults of a safe type (see SAFE_DEFAULT_TYPES), and "…" for the others.
    """
    try:
        sig = read_signature(obj)
    except Exception: # anything may go wrong in arbitrary code; never fail the question
        return f"({ELIDED})"
    params = [sanitize_parameter(p) for p in sig.parameters.values()]
    sig = sig.replace(parameters=params, return_annotation=sig.empty)
    return str(sig)


def read_signature(obj):
    sig = inspect.signature(obj)
    if issubclass(type(obj), type):
        sig = drop_self(sig)
    return sig


def drop_self(sig):
    params = list(sig.parameters.values())
    if params and params[0].name == "self":
        sig = sig.replace(parameters=params[1:])
    return sig


def sanitize_parameter(param):
    param = param.replace(annotation=param.empty)
    default = param.default
    if default is param.empty:
        return param
    return param.replace(default=Verbatim(format_default(default)))


def format_default(value):
    if is_safe_default(value):
        return repr(value)
    return ELIDED


def is_safe_default(value):
    # by identity: `in` compares by ==, which runs the __eq__ of the type's metaclass
    cls = type(value)
    return any(cls is t for t in SAFE_DEFAULT_TYPES)



class Verbatim:
    """
    Stands in for a default value.
    Signature renders defaults via repr.
    """

    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return self.text


