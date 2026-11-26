
class ToolError(Exception):
    """
    Goes back to the model as the tool result, so that it can correct itself.
    The hint, if any, tells the model what it needs to know to correct itself.
    """

    def __init__(self, message, hint=None):
        super().__init__(message)
        self.message = message
        self.hint = hint

    def __str__(self):
        if not self.hint:
            return self.message
        return f"{self.message} -- {self.hint}"


