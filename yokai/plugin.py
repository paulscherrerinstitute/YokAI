from .utils import has_class_from, qualified_name, typename


class Plugin:
    """
    Teaches YokAI about one library:
    - `paragraph` is the library's paragraph in the instructions.
      Read at import with read_markdown. If missing, YokAI fails early.
    - `faq_file` is the library's FAQ.
      Read when asked. If missing, YokAI warns once and works without it.
    - `module_prefix` decides which objects the plugin covers (cf. covers(...))
    With just the defaults, nothing is added.
    """

    paragraph = None
    faq_file = None
    module_prefix = None

    def identification(self, obj):
        """
        Returns the identification of obj as labels and their values.
        `obj` is an instance this plugin covers.
        Values other than str are left out.
        It must not read values from obj.
        """
        return {}



def find_covering_plugin(obj, plugins):
    """
    Returns the plugin covering obj, or None if no plugin does.
    Raises PluginOverlapError if several do.
    """
    covering = [p for p in plugins if covers(p, obj)]
    if len(covering) > 1:
        raise PluginOverlapError(describe_overlap(obj, covering))
    if not covering:
        return None
    return covering[0]


def covers(plugin, obj):
    """
    A plugin covers obj if a class in its type's MRO comes from the plugin's library.
    """
    prefix = plugin.module_prefix
    if prefix is None:
        return False
    # type(obj), never obj.__class__, which may be any object
    return has_class_from(type(obj), prefix)


def describe_overlap(obj, plugins):
    names = ", ".join(typename(p) for p in plugins)
    return f"{qualified_name(type(obj))} is covered by several plugins: {names}"



class PluginOverlapError(Exception):
    """
    No overlap between plugins is expected.
    A real case is to be solved once understood, not resolved silently.
    """


