import json
from dataclasses import dataclass

from .builtins import standard_values, truthy
from .environment import Environment
from .errors import LispError, LispSyntaxError, LispTypeError
from .parser import DictLiteral, Symbol, Vector, VectorLiteral, parse_many


@dataclass
class Procedure:
    interpreter: object
    parameters: tuple
    body: tuple
    environment: Environment
    rest_parameter: str | None = None

    def __call__(self, *arguments):
        if self.rest_parameter is None and len(arguments) != len(self.parameters):
            raise LispTypeError(
                f"lambda: ожидалось {len(self.parameters)} арг., получено {len(arguments)}"
            )
        if self.rest_parameter is not None and len(arguments) < len(self.parameters):
            raise LispTypeError(
                f"lambda: ожидалось не меньше {len(self.parameters)} арг., получено {len(arguments)}"
            )
        values = dict(zip(self.parameters, arguments))
        if self.rest_parameter is not None:
            values[self.rest_parameter] = list(arguments[len(self.parameters):])
        return self.interpreter.evaluate_sequence(self.body, self.environment.child(values))

    def __repr__(self):
        return "<lambda>"


class Interpreter:
    SPECIAL_FORMS = {
        "quote", "if", "cond", "define", "set", "set!", "lambda", "let", "let*",
        "begin", "progn", "and", "or", "try",
    }

    def __init__(self, values=None):
        self.global_environment = Environment(standard_values())
        if values:
            for name, value in values.items():
                self.define(name, value)

    def define(self, name, value):
        if not callable(value):
            self.global_environment.define(name, value)
            return value

        def checked(*arguments):
            try:
                return value(*arguments)
            except LispError:
                raise
            except TypeError as error:
                raise LispTypeError(f"{name}: неверные аргументы") from error

        checked.__name__ = str(name)
        self.global_environment.define(name, checked)
        return value

    def execute(self, source: str):
        expressions = parse_many(source)
        if not expressions:
            return []
        return self.evaluate_sequence(expressions, self.global_environment)

    def evaluate_sequence(self, expressions, environment):
        result = []
        for expression in expressions:
            result = self.evaluate(expression, environment)
        return result

    def evaluate(self, expression, environment=None):
        environment = environment or self.global_environment

        if isinstance(expression, Symbol):
            return environment.get(expression)
        if isinstance(expression, VectorLiteral):
            return Vector(self.evaluate(value, environment) for value in expression.values)
        if isinstance(expression, DictLiteral):
            try:
                return {
                    self.evaluate(key, environment): self.evaluate(value, environment)
                    for key, value in expression.pairs
                }
            except TypeError as error:
                raise LispTypeError("Ключ словаря должен быть неизменяемым") from error
        if not isinstance(expression, list):
            return expression
        if not expression:
            return []

        head = expression[0]
        if isinstance(head, Symbol) and head in self.SPECIAL_FORMS:
            return self._evaluate_special(str(head), expression[1:], environment)

        function = self.evaluate(head, environment)
        arguments = [self.evaluate(argument, environment) for argument in expression[1:]]
        return self.call(function, arguments)

    def call(self, function, arguments):
        if not callable(function):
            raise LispTypeError(f"Значение не является функцией: {self.format(function)}")
        try:
            return function(*arguments)
        except LispError:
            raise
        except TypeError as error:
            name = getattr(function, "__name__", "функция")
            raise LispTypeError(f"{name}: неверные аргументы") from error
        except Exception as error:
            name = getattr(function, "__name__", "функция")
            raise LispError(f"{name}: {error}") from error

    def _evaluate_special(self, name, arguments, environment):
        method = getattr(self, f"_special_{name.replace('!', '_bang').replace('*', '_star')}")
        return method(arguments, environment)

    def _special_quote(self, arguments, _environment):
        self._arity("quote", arguments, 1, 1)
        return self._quote(arguments[0])

    def _special_if(self, arguments, environment):
        self._arity("if", arguments, 2, 3)
        condition = self.evaluate(arguments[0], environment)
        branch = arguments[1] if truthy(condition) else (arguments[2] if len(arguments) == 3 else [])
        return self.evaluate(branch, environment)

    def _special_cond(self, clauses, environment):
        for clause in clauses:
            if not isinstance(clause, list) or len(clause) < 2:
                raise LispSyntaxError("cond: каждая ветвь должна содержать условие и результат")
            condition = clause[0]
            matches = isinstance(condition, Symbol) and condition in ("else", "t")
            if matches or truthy(self.evaluate(condition, environment)):
                return self.evaluate_sequence(clause[1:], environment)
        return []

    def _special_define(self, arguments, environment):
        self._at_least("define", arguments, 2)
        target = arguments[0]
        if isinstance(target, list) and target:
            name, *parameters = target
            self._require_symbol(name, "define")
            value = self._make_procedure(parameters, arguments[1:], environment)
        else:
            self._arity("define", arguments, 2, 2)
            self._require_symbol(target, "define")
            name = target
            value = self.evaluate(arguments[1], environment)
        return environment.define(name, value)

    def _special_set(self, arguments, environment):
        self._arity("set", arguments, 2, 2)
        self._require_symbol(arguments[0], "set")
        value = self.evaluate(arguments[1], environment)
        return environment.set(arguments[0], value, create=True)

    def _special_set_bang(self, arguments, environment):
        self._arity("set!", arguments, 2, 2)
        self._require_symbol(arguments[0], "set!")
        return environment.set(arguments[0], self.evaluate(arguments[1], environment))

    def _special_lambda(self, arguments, environment):
        self._at_least("lambda", arguments, 2)
        return self._make_procedure(arguments[0], arguments[1:], environment)

    def _make_procedure(self, parameters, body, environment):
        if not isinstance(parameters, list):
            raise LispSyntaxError("lambda: параметры должны быть списком")
        names = []
        rest = None
        index = 0
        while index < len(parameters):
            parameter = parameters[index]
            if isinstance(parameter, Symbol) and parameter == "&rest":
                if rest is not None or index + 2 != len(parameters):
                    raise LispSyntaxError("lambda: после &rest ожидается одно имя")
                rest = parameters[index + 1]
                self._require_symbol(rest, "lambda")
                break
            self._require_symbol(parameter, "lambda")
            names.append(str(parameter))
            index += 1
        if len(set(names + ([str(rest)] if rest else []))) != len(names) + (1 if rest else 0):
            raise LispSyntaxError("lambda: имена параметров не должны повторяться")
        return Procedure(self, tuple(names), tuple(body), environment, str(rest) if rest else None)

    def _special_let(self, arguments, environment):
        self._at_least("let", arguments, 2)
        bindings = self._bindings(arguments[0])
        values = {str(name): self.evaluate(value, environment) for name, value in bindings}
        return self.evaluate_sequence(arguments[1:], environment.child(values))

    def _special_let_star(self, arguments, environment):
        self._at_least("let*", arguments, 2)
        child = environment.child()
        for name, expression in self._bindings(arguments[0]):
            child.define(name, self.evaluate(expression, child))
        return self.evaluate_sequence(arguments[1:], child)

    def _special_begin(self, arguments, environment):
        return self.evaluate_sequence(arguments, environment)

    _special_progn = _special_begin

    def _special_and(self, arguments, environment):
        result = True
        for argument in arguments:
            result = self.evaluate(argument, environment)
            if not truthy(result):
                return []
        return result

    def _special_or(self, arguments, environment):
        for argument in arguments:
            result = self.evaluate(argument, environment)
            if truthy(result):
                return result
        return []

    def _special_try(self, arguments, environment):
        self._arity("try", arguments, 2, 2)
        try:
            return self.evaluate(arguments[0], environment)
        except Exception as error:
            local = environment.child({"error": str(error)})
            handler = self.evaluate(arguments[1], local)
            return self.call(handler, [str(error)]) if callable(handler) else handler

    def _bindings(self, expression):
        if not isinstance(expression, list):
            raise LispSyntaxError("let: привязки должны быть списком")
        bindings = []
        names = set()
        for binding in expression:
            if not isinstance(binding, list) or len(binding) != 2:
                raise LispSyntaxError("let: привязка должна иметь вид (имя значение)")
            self._require_symbol(binding[0], "let")
            if str(binding[0]) in names:
                raise LispSyntaxError(f"let: имя {binding[0]} повторяется")
            names.add(str(binding[0]))
            bindings.append(binding)
        return bindings

    def _quote(self, value):
        if isinstance(value, VectorLiteral):
            return Vector(self._quote(item) for item in value.values)
        if isinstance(value, DictLiteral):
            try:
                return {self._quote(key): self._quote(item) for key, item in value.pairs}
            except TypeError as error:
                raise LispTypeError("Ключ словаря должен быть неизменяемым") from error
        if isinstance(value, list):
            return [self._quote(item) for item in value]
        return value

    @staticmethod
    def _require_symbol(value, form):
        if not isinstance(value, Symbol):
            raise LispSyntaxError(f"{form}: ожидается имя")

    @staticmethod
    def _arity(name, arguments, minimum, maximum=None):
        maximum = minimum if maximum is None else maximum
        if len(arguments) < minimum or len(arguments) > maximum:
            expected = str(minimum) if minimum == maximum else f"от {minimum} до {maximum}"
            raise LispSyntaxError(f"{name}: ожидается {expected} арг.")

    @staticmethod
    def _at_least(name, arguments, minimum):
        if len(arguments) < minimum:
            raise LispSyntaxError(f"{name}: ожидается не меньше {minimum} арг.")

    def format(self, value):
        if value == [] or value is False or value is None:
            return "nil"
        if value is True:
            return "t"
        if isinstance(value, str) and not isinstance(value, Symbol):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, Symbol):
            return str(value)
        if isinstance(value, Vector):
            return "[" + " ".join(self.format(item) for item in value) + "]"
        if isinstance(value, list):
            return "(" + " ".join(self.format(item) for item in value) + ")"
        if isinstance(value, dict):
            contents = " ".join(f"{self.format(key)}: {self.format(item)}" for key, item in value.items())
            return "{" + contents + "}"
        return str(value)
