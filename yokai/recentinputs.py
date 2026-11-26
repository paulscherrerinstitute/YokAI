from weakref import WeakKeyDictionary

from .currentinput import without_asking_statements
from .magic import registered_magic_names


MAX_RECENT_INPUTS = 10

# per shell, the indices in In of the inputs any YokAI on it was asked from
asked_from_by_shell = WeakKeyDictionary()


def record_asked_from(shell, index):
    """
    Records on the shell that a question was asked from its input In[index],
    answered or not, so that every YokAI on the shell cuts the asking statements from it.
    """
    asked_from_by_shell.setdefault(shell, set()).add(index)


def read_recent_inputs(shell, previous_question_at, asked_at):
    """
    The newest of the inputs between the previous question and this one,
    at most MAX_RECENT_INPUTS, oldest first.
    A failed question asked again word for word is left out, so it is not sent twice.
    The inputs a question was asked from, by any YokAI on the shell,
    are cut as the current input is, and left out if nothing remains.
    Going from the newest backwards, the inputs older than the MAX_RECENT_INPUTS-th kept one
    are never parsed.
    """
    inputs = shell.user_ns["In"]
    question_input = inputs[asked_at]
    asked_from = asked_from_by_shell.get(shell, set())
    magic_names = registered_magic_names(shell)
    kept = []
    for index in reversed(range(previous_question_at + 1, asked_at)):
        if len(kept) == MAX_RECENT_INPUTS:
            break
        source = inputs[index]
        if source == question_input:
            continue
        if index in asked_from:
            source = without_asking_statements(source, magic_names)
        if source:
            kept.append(source)
    kept.reverse()
    return kept


