
MAX_MOOD_LENGTH = 50

MOOD_TEMPL = """\
Your mood or persona is "{mood}".
Let it set the tone of your prose around the code. It never changes the code or its comments, nor anything the instructions above ask of you, such as when to ask a clarifying question.
"""


def format_mood(mood):
    """
    None without a mood (None, empty or blank), so that nothing is added.
    Raises ValueError for a mood too long or holding a line break.
    """
    if mood is None:
        return None
    mood = mood.strip()
    if not mood:
        return None
    length = len(mood)
    if length > MAX_MOOD_LENGTH:
        raise ValueError(f"mood must be at most {MAX_MOOD_LENGTH} characters long (got {length})")
    if "\n" in mood:
        raise ValueError(f"mood cannot contain line breaks (got {mood!r})")
    return MOOD_TEMPL.format(mood=mood)


