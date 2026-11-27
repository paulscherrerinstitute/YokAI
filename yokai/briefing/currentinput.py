from ..magic import registered_magic_names

from .askingstatements import without_asking_statements


def read_current_input(shell, asked_at):
    """
    The input the question was asked in, In[asked_at], without its asking statements.
    None if nothing remains.
    """
    source = shell.user_ns["In"][asked_at]
    magic_names = registered_magic_names(shell)
    return without_asking_statements(source, magic_names)


