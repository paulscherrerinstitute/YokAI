import inspect
import sys

from ..staticinspect import is_own
from ..utils import typename

from .error import ToolError
from .kinds import is_data_descriptor, unwrap_method


def resolve(namespace, target):
    """
    Resolves target as a reference, else as a qualified name,
    without evaluating it, importing modules, or running properties or __getattr__.
    """
    parts = target.split(".")
    if not all(p.isidentifier() for p in parts):
        raise ToolError(
            f"`{target}` is neither a reference nor a qualified name "
            "-- only dotted names are supported, no keys, no calls"
        )

    try:
        return resolve_reference(namespace, parts)
    except ToolError as exc:
        reference_error = exc

    try:
        return resolve_qualified_name(parts)
    except ToolError as exc:
        qualified_name_error = exc
    raise ToolError(
        f"`{target}` resolves neither as a reference ({reference_error}) "
        f"nor as a qualified name ({qualified_name_error}) "
        "-- modules are never imported"
    )


def resolve_reference(namespace, parts):
    variable_name, *steps = parts
    try:
        obj = namespace[variable_name]
    except KeyError:
        raise ToolError(f"`{variable_name}` is not a variable in the session")
    return step_into(obj, variable_name, steps)


def resolve_qualified_name(parts):
    # longest first: a package's attribute may hide its submodule of the same name
    for count in range(len(parts), 0, -1):
        module_name = ".".join(parts[:count])
        module = sys.modules.get(module_name)
        if module is not None:
            return step_into(module, module_name, parts[count:])
    raise ToolError(f"no module `{parts[0]}` is loaded")


def step_into(obj, prefix, steps):
    """
    Steps along the attributes without running properties or __getattr__,
    stopping at data descriptors (e.g., properties), whose values are not read,
    and at YokAI's own objects.
    `prefix` is the dotted name of `obj`, for the error messages.
    """
    check_not_own(obj, prefix)
    for step in steps:
        if is_data_descriptor(obj):
            raise ToolError(f"`{prefix}` is a {typename(obj)} and its value is not read")
        try:
            obj = inspect.getattr_static(obj, step)
        except AttributeError:
            raise ToolError(f"`{prefix}` has no attribute `{step}`")
        obj = unwrap_method(obj)
        prefix += "." + step
        check_not_own(obj, prefix)
    return obj


def check_not_own(obj, prefix):
    # so that the model looks at the user's session, not at YokAI itself
    if is_own(obj):
        raise ToolError(f"`{prefix}` is part of YokAI and thus out of reach of the tools")


