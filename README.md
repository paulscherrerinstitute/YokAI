# YokAI

An LLM assistant for IPython/Jupyter sessions.

## Setup

Store your token once per account:

```python
from yokai import store_token
store_token()
```

It is stored in `$XDG_CONFIG_HOME/yokai/token` (default: `~/.config/yokai/token`), readable only by you.

## Usage

In an IPython/Jupyter session:

```python
from yokai import YokAI
ai = YokAI()

ai.ask("How do I wiggle the electrons?")
ai.ask("now straighten them out") # the conversation continues
```

To start a fresh conversation, you may use `ai.reset()`.

### Magics

Creating a `YokAI` object registers the line magic `%yokai`:

```python
%yokai How do I wiggle the electrons?
```

... and the cell magic `%%yokai` (for a question over several lines, e.g. with a pasted traceback):

```python
%%yokai why does this fail?
Traceback (most recent call last):
...
```

## Plugins

A bare `ai = YokAI()` works in any IPython/Jupyter session. It knows the names, types and signatures of what's in your session, plus your recent code. It cannot look up values, so `x = 5` shows up as `x: int`, and a numpy array as `arr: ndarray` with no shape or contents.

For it to know about a specific library, a plugin is needed:
- [sfdata](https://github.com/paulscherrerinstitute/sf_datafiles/blob/master/sfdata/ai/plugin.py)
- [slic](https://github.com/paulscherrerinstitute/slic/blob/master/slic/ai/plugin.py)

