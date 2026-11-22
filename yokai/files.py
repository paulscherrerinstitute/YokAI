from pathlib import Path


def read_markdown(path):
    """
    Reads a Markdown file.
    `path` may be str, pathlib.Path or Traversable (from importlib.resources.files(...))
    For str and Path, ~ is expanded.
    """
    if isinstance(path, str):
        path = Path(path)
    if isinstance(path, Path):
        path = path.expanduser()
    return path.read_text(encoding="utf-8")


