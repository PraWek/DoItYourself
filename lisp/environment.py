from .errors import LispNameError
from .parser import Symbol


class Environment:
    def __init__(self, values=None, parent=None):
        self.values = dict(values or {})
        self.parent = parent

    def child(self, values=None):
        return Environment(values, self)

    def define(self, name, value):
        self.values[str(name)] = value
        return value

    def resolve(self, name):
        key = str(name)
        if key in self.values:
            return self
        if self.parent is not None:
            return self.parent.resolve(key)
        raise LispNameError(f"Неизвестный символ: {key}")

    def get(self, name: Symbol):
        return self.resolve(name).values[str(name)]

    def set(self, name, value, create=False):
        try:
            target = self.resolve(name)
        except LispNameError:
            if not create:
                raise
            target = self
        target.values[str(name)] = value
        return value
