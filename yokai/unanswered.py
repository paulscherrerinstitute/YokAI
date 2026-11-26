
# at most this many unanswered questions are shown, the newest
MAX_SHOWN_UNANSWERED = 3

UNANSWERED_NOTE_HEADING = (
    "Background, to be used only if the question refers to it: "
    "earlier questions that went unanswered, grouped by reason, oldest first in each group."
)

FAILED_TEMPL = "The request failed, and the user was shown:\n\n```text\n{description}\n```"

# the reason for a question the user interrupted with ctrl-c
INTERRUPTED_REASON = "The user interrupted YokAI:"


def failed_reason(description):
    """
    The reason for a question whose request failed: the description shown to the user.
    """
    return FAILED_TEMPL.format(description=description)


def make_unanswered_note(unanswered, question):
    """
    The note on the questions left unanswered, each a (question, reason) pair, oldest first.
    The question being asked is left out, as a retry word for word needs no note.
    None if no others remain.
    The newest MAX_SHOWN_UNANSWERED are shown, grouped by reason,
    plus how many earlier ones there are.
    """
    listed = listed_once(unanswered, question)
    if not listed:
        return None
    shown = listed[-MAX_SHOWN_UNANSWERED:]
    n_earlier = len(listed) - len(shown)
    sections = [UNANSWERED_NOTE_HEADING]
    for reason, questions in group_by_reason(shown).items():
        sections.append(reason)
        sections.append("\n".join(f"- {q}" for q in questions))
    if n_earlier:
        sections.append(earlier_line(n_earlier))
    return "\n\n".join(sections)


def listed_once(unanswered, question):
    """
    The unanswered questions other than question, oldest first.
    A question asked several times is listed once, at its newest asking and with its reason.
    """
    newest = {}
    for q, reason in unanswered:
        if q == question:
            continue
        # popped first, so that a repeat moves to its newest asking
        newest.pop(q, None)
        newest[q] = reason
    return list(newest.items())


def group_by_reason(unanswered):
    """
    The questions of each reason, in the order of each group's oldest question.
    """
    groups = {}
    for q, reason in unanswered:
        groups.setdefault(reason, []).append(q)
    return groups


def earlier_line(n_earlier):
    noun = "question" if n_earlier == 1 else "questions"
    return f"And {n_earlier} earlier {noun}."


