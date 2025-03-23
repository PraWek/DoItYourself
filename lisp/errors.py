class LispError(Exception):
    """Base error exposed by the interpreter."""


class LispSyntaxError(LispError):
    pass


class LispNameError(LispError):
    pass


class LispTypeError(LispError):
    pass
