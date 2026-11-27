import inspect
import json

from ..plugin import PluginOverlapError
from ..utils import typename

from .describe import describe
from .error import ToolError
from .get_source import get_source


TARGET_DESCRIPTION = "A reference, i.e., a variable name in the user's session followed by attributes (e.g., obj.x) or a qualified name in a loaded module (e.g., collections.OrderedDict)"

ARGUMENTS_FORMAT = '{"target": "…"}'


def run_tool(namespace, tool_name, arguments, plugins=()):
    """
    Runs a tool call of the model (arguments is the raw JSON string)
    and returns the result, errors included, as a string.
    An overlap of plugins is raised, as it is for the maintainer, not the model.
    """
    try:
        tool = look_up_tool(tool_name)
        target = read_target(arguments)
        return tool(namespace, target, plugins)
    except ToolError as exc:
        return f"Error: {exc}"
    except PluginOverlapError:
        raise
    except Exception as exc:
        # anything may go wrong in arbitrary code -- never fail the question
        return f"Error: {typename(exc)}: {exc}"


def format_tool_call(tool_name, arguments):
    """
    Renders a tool call for the user, e.g., `get_source(obj.x)`.
    """
    try:
        target = read_target(arguments)
    except ToolError:
        target = arguments
    return f"{tool_name}({target})"


def look_up_tool(tool_name):
    try:
        return TOOLS[tool_name]
    except KeyError:
        msg = f"unknown tool `{tool_name}`"
        names = ", ".join(TOOLS)
        hint = f"the tools are: {names}"
        raise ToolError(msg, hint=hint)


def read_target(arguments):
    try:
        target = json.loads(arguments)["target"]
    except (ValueError, TypeError, KeyError):
        target = None
    if not isinstance(target, str):
        msg = f"malformed arguments: {arguments}"
        hint = f"the arguments must be a JSON object {ARGUMENTS_FORMAT}"
        raise ToolError(msg, hint=hint)
    return target


def make_schema(tool_name, tool):
    target = {"type": "string", "description": TARGET_DESCRIPTION}
    properties = {"target": target}
    parameters = {"type": "object", "properties": properties, "required": ["target"]}
    description = inspect.getdoc(tool)
    function = {"name": tool_name, "description": description, "parameters": parameters}
    return {"type": "function", "function": function}


# each tool takes the namespace, the target and the plugins, whether it uses them or not
TOOLS = {
    "describe": describe,
    "get_source": get_source,
}

TOOL_SCHEMAS = [make_schema(name, tool) for name, tool in TOOLS.items()]


