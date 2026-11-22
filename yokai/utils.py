
def typename(obj):
    return type(obj).__name__


def qualified_name(obj):
    """
    Returns module.qualname of a class or function
    or the qualname alone if it has no module (e.g., list.append).
    """
    res = obj.__qualname__
    module = getattr(obj, "__module__", None)
    if is_str(module):
        res = f"{module}.{res}"
    return res


def has_class_from(cls, prefix):
    """
    Does a class in the MRO of `cls` come from the module prefix or one below it?
    """
    # a class made by type() has no __module__ if the caller's globals lack __name__
    modules = (getattr(c, "__module__", None) for c in cls.__mro__)
    return any(is_in_module(module, prefix) for module in modules)


def is_in_module(module_name, prefix):
    """
    Is `module_name` the module prefix or one below it?
    `module_name` may be any object (e.g., None, or a class's `__module__` set to anything).
    """
    if not is_str(module_name):
        return False
    return module_name == prefix or module_name.startswith(prefix + ".")


def is_str(value):
    # exact type check: a str subclass could run arbitrary code when formatted
    return type(value) is str


