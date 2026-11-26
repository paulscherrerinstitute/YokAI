import inspect
import sys

from ..staticinspect import is_own
from ..utils import typename

from .error import ToolError
from .kinds import is_data_descriptor, kind_of, unwrap_method


def resolve(namespace, target):
    """
    Resolves target as a reference, else as a qualified name,
    without evaluating it, importing modules, or running properties or __getattr__.
    """
    parts = target.split(".")
    if not all(p.isidentifier() for p in parts):
        msg = f"`{target}` is neither a reference nor a qualified name"
        hint = "only dotted names are supported, no keys, no calls"
        raise ToolError(msg, hint=hint)

    try:
        return resolve_reference(namespace, parts)
    except ToolError as exc:
        reference_error = exc

    try:
        return resolve_qualified_name(parts)
    except ToolError as exc:
        qualified_name_error = exc

    as_reference = f"as a reference ({reference_error.message})"
    as_qualified_name = f"as a qualified name ({qualified_name_error.message})"
    msg = f"`{target}` resolves neither {as_reference} nor {as_qualified_name}"

    hints = [e.hint for e in (reference_error, qualified_name_error) if e.hint]
    hints.append("modules are never imported")
    hint = "; ".join(dict.fromkeys(hints))

    raise ToolError(msg, hint=hint)


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
            msg = f"`{prefix}` is a {typename(obj)} and its value is not read"
            hint = f"describe `{prefix}` instead"
            raise ToolError(msg, hint=hint)
        try:
            obj = inspect.getattr_static(obj, step)
        except AttributeError:
            msg = f"`{prefix}` has no attribute `{step}`"
            hint = make_missing_attribute_hint(obj, prefix, step)
            raise ToolError(msg, hint=hint)
        obj = unwrap_method(obj)
        prefix += "." + step
        check_not_own(obj, prefix)
    return obj


def make_missing_attribute_hint(obj, prefix, step):
    # a module's submodule is its attribute only once it is loaded
    if kind_of(obj) == "module":
        submodule = f"`{prefix}.{step}` may be a submodule that is not loaded"
        describe = f"describe `{prefix}` to list its names"
        return f"{submodule}; {describe}"
    return f"__getattr__ is never run, so describe `{prefix}` to list its attributes"


def check_not_own(obj, prefix):
    # so that the model looks at the user's session, not at YokAI itself
    if is_own(obj):
        raise ToolError(f"`{prefix}` is part of YokAI and thus out of reach of the tools")


