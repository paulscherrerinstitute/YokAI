import inspect
from types import FunctionType, MethodType

from ..staticinspect import METHOD_DESCRIPTOR_TYPES, format_instance, format_signature, read_instance_dict
from ..utils import is_str, qualified_name, typename

from .kinds import METHOD_WRAPPERS, is_data_descriptor, kind_of, unwrap_method
from .resolve import resolve


# what a class's vars() holds for its methods
METHOD_MEMBER_TYPES = (FunctionType, *METHOD_DESCRIPTOR_TYPES, *METHOD_WRAPPERS)

INDENT = "  "


def describe(namespace, target, plugins):
    """
    Describes a target without reading values:
    - An instance: its type and identification (e.g., a name),
      its class's constructor signature and docstring, public methods with
      signatures and properties, and its public attributes with their types.
    - A class: the same without the instance part.
    - A function: its signature and docstring.
    - A module: its public names with their kinds or types.
    Use it to look up real signatures and members instead of guessing.
    """
    obj = resolve(namespace, target)
    if is_data_descriptor(obj):
        return describe_property(target, obj)
    kind = kind_of(obj)
    if kind is None:
        return describe_instance(target, obj, plugins)
    return DESCRIBERS[kind](obj)


def describe_instance(target, obj, plugins):
    attributes = [
        f"{name}: {typename(value)}"
        for name, value in read_instance_dict(obj).items()
        if is_public(name)
    ]
    return join_sections(
        format_instance(target, obj, plugins),
        describe_class(type(obj)),
        format_section("attributes", attributes),
    )


def describe_class(cls):
    header = "class " + qualified_name(cls) + format_signature(cls)
    members = collect_members(cls)
    methods = [
        name + format_method_signature(cls, member)
        for name, member in members.items()
        if is_method(member)
    ]
    properties = [
        name
        for name, member in members.items()
        if is_data_descriptor(member)
    ]
    return join_sections(
        join_lines(header, read_docstring(cls)),
        format_section("methods", methods),
        format_section("properties", properties),
    )


def collect_members(cls):
    """
    Returns the public members of cls by name,
    from vars() of each class along the MRO (ignoring object),
    the first definition of a name wins.
    """
    members = {}
    for base in cls.__mro__:
        if base is object:
            continue
        for name, member in vars(base).items():
            if is_public(name):
                members.setdefault(name, member)
    return members


def is_method(member):
    return issubclass(type(member), METHOD_MEMBER_TYPES)


def format_method_signature(cls, member):
    function = unwrap_method(member)
    if issubclass(type(member), staticmethod):
        return format_signature(function)
    # bound only for the signature, which then leaves out self (or cls), as in a call
    return format_signature(MethodType(function, cls))


def describe_function(function):
    header = qualified_name(function) + format_signature(function)
    return join_lines(header, read_docstring(function))


def describe_property(target, prop):
    header = f"{target}: {typename(prop)}, its value is not read"
    # other data descriptors are instances of arbitrary classes: no reads from them
    if not issubclass(type(prop), property):
        return header
    return join_lines(header, read_docstring(prop))


def describe_module(module):
    names = [
        f"{name}: {kind_or_type(obj)}"
        for name, obj in vars(module).items()
        if is_public(name)
    ]
    return join_sections(
        "module " + module.__name__,
        format_section("names", names),
    )


def kind_or_type(obj):
    return kind_of(obj) or typename(obj)


def is_public(name):
    return not name.startswith("_")


def read_docstring(obj):
    """
    Returns the cleaned-up docstring of a class, function or property, or None.
    A class's own only; inspect.getdoc would inherit one from a base class.
    """
    doc = obj.__doc__
    if not is_str(doc):
        return None
    return inspect.cleandoc(doc)


def join_sections(*sections):
    return "\n\n".join(s for s in sections if s is not None)


def join_lines(*lines):
    return "\n".join(line for line in lines if line is not None)


def format_section(title, lines):
    if not lines:
        return None
    indented = (INDENT + line for line in lines)
    return join_lines(title + ":", *indented)


DESCRIBERS = {
    "module": describe_module,
    "class": describe_class,
    "function": describe_function,
}


