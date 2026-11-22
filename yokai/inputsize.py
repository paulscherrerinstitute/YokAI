
MAX_RECENT_INPUTS = 10
MAX_CHARACTERS = 8000


def limit_recent_inputs(inputs):
    """
    The newest of the inputs, at most MAX_RECENT_INPUTS,
    as many whole inputs as fit into MAX_CHARACTERS in total.
    If not even the newest fits, it is cut and sent alone.
    """
    inputs = inputs[-MAX_RECENT_INPUTS:]
    kept = newest_that_fit(inputs)
    if inputs and not kept:
        return [cut_from_top(inputs[-1])]
    return kept


def cut_from_top(source):
    """
    The source's newest whole lines that fit into MAX_CHARACTERS,
    after a marker line saying how many lines were cut.
    """
    lines = source.split("\n")
    # the last line is kept even if it alone is longer, so that a cut is at a line break
    kept = newest_that_fit(lines, separator="\n") or lines[-1:]
    n_cut_lines = len(lines) - len(kept)
    if n_cut_lines == 0:
        return source
    return "\n".join([cut_marker(n_cut_lines), *kept])


def cut_marker(n_cut_lines):
    noun = "line" if n_cut_lines == 1 else "lines"
    return f"# … {n_cut_lines} {noun} cut"


def newest_that_fit(items, separator=""):
    """
    The newest of the items that fit into MAX_CHARACTERS when joined with the separator.
    """
    kept = []
    length = -len(separator) # n items need only n-1 separators, so start one short
    for item in reversed(items):
        length += len(separator) + len(item)
        if length > MAX_CHARACTERS:
            break
        kept.append(item)
    kept.reverse()
    return kept


