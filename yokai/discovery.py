from types import ModuleType

from .plugin import PluginOverlapError
from .staticinspect import ROUTINE_TYPES, format_instance, format_signature, is_own


def object_list(namespace, hidden, plugins=()):
    """
    Renders one line per variable in `namespace` (a dict, in its order),
    skipping underscore-names, names in `hidden` and YokAI's own objects.
    Instances show the identification of the plugin covering them, if any.
    Reads no values from the objects.
    A variable whose handling raises is left out.
    An overlap of plugins is raised, as it is for the maintainer.
    """
    lines = []
    for variable_name, obj in namespace.items():
        try:
            if is_listed(variable_name, obj, hidden):
                lines.append(format_variable(variable_name, obj, plugins))
        except PluginOverlapError:
            raise
        except Exception:
            # anything may go wrong in arbitrary code -- never fail the question
            pass
    return "\n".join(lines)


def is_listed(variable_name, obj, hidden):
    if variable_name.startswith("_") or variable_name in hidden:
        return False
    return not is_own(obj)


def format_variable(variable_name, obj, plugins):
    # type(obj), never isinstance(obj, …), which may read obj.__class__
    cls = type(obj)
    if issubclass(cls, ModuleType):
        return f"{variable_name} = {obj.__name__}"
    if issubclass(cls, type):
        return "class " + variable_name + format_signature(obj)
    if issubclass(cls, ROUTINE_TYPES):
        return variable_name + format_signature(obj)
    return format_instance(variable_name, obj, plugins)


