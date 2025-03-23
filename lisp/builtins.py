import math
import operator
import random
from functools import reduce

from .errors import LispTypeError
from .parser import Symbol, Vector


def _numbers(arguments, name, minimum=0):
    if len(arguments) < minimum:
        raise LispTypeError(f"{name}: недостаточно аргументов")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in arguments):
        raise LispTypeError(f"{name}: ожидаются числа")
    return arguments


def add(*arguments):
    return sum(_numbers(arguments, "+"))


def subtract(*arguments):
    values = _numbers(arguments, "-", 1)
    if len(values) == 1:
        return -values[0]
    return values[0] - sum(values[1:])


def multiply(*arguments):
    return math.prod(_numbers(arguments, "*"))


def divide(*arguments):
    values = _numbers(arguments, "/", 1)
    divisors = values if len(values) == 1 else values[1:]
    if any(value == 0 for value in divisors):
        raise LispTypeError("/: деление на ноль")
    if len(values) == 1:
        return 1 / values[0]
    return reduce(operator.truediv, values)


def compare(arguments, operation, name):
    if len(arguments) < 2:
        raise LispTypeError(f"{name}: ожидаются хотя бы два аргумента")
    return all(operation(left, right) for left, right in zip(arguments, arguments[1:]))


def cons(value, sequence):
    if not isinstance(sequence, list):
        raise LispTypeError("cons: второй аргумент должен быть списком")
    return [value, *sequence]


def car(sequence):
    if not isinstance(sequence, list) or not sequence:
        raise LispTypeError("car: ожидается непустой список")
    return sequence[0]


def cdr(sequence):
    if not isinstance(sequence, list) or not sequence:
        raise LispTypeError("cdr: ожидается непустой список")
    return sequence[1:]


def append(*sequences):
    result = []
    for sequence in sequences:
        if not isinstance(sequence, list):
            raise LispTypeError("append: ожидаются списки")
        result.extend(sequence)
    return result


def make_dict(*arguments):
    if len(arguments) % 2:
        raise LispTypeError("dict: ожидается чётное число аргументов")
    return dict(zip(arguments[::2], arguments[1::2]))


def apply_function(function, arguments):
    if not callable(function) or not isinstance(arguments, list):
        raise LispTypeError("apply: ожидаются функция и список")
    return function(*arguments)


def map_function(function, sequence):
    if not callable(function) or not isinstance(sequence, list):
        raise LispTypeError("map: ожидаются функция и список")
    return [function(value) for value in sequence]


def filter_function(function, sequence):
    if not callable(function) or not isinstance(sequence, list):
        raise LispTypeError("filter: ожидаются функция и список")
    return [value for value in sequence if truthy(function(value))]


def reduce_function(function, sequence, *initial):
    if not callable(function) or not isinstance(sequence, list):
        raise LispTypeError("reduce: ожидаются функция и список")
    if len(initial) > 1:
        raise LispTypeError("reduce: лишний аргумент")
    if not sequence and not initial:
        raise LispTypeError("reduce: пустому списку нужно начальное значение")
    return reduce(function, sequence, *initial)


def random_number(*arguments):
    _numbers(arguments, "random")
    if not arguments:
        return random.random()
    if len(arguments) == 1:
        if arguments[0] <= 0:
            raise LispTypeError("random: граница должна быть положительной")
        return random.randrange(int(arguments[0]))
    if len(arguments) == 2:
        return random.randint(int(arguments[0]), int(arguments[1]))
    raise LispTypeError("random: ожидается не более двух аргументов")


def standard_values():
    return {
        "nil": [],
        "t": True,
        "+": add,
        "-": subtract,
        "*": multiply,
        "/": divide,
        "<": lambda *args: compare(args, operator.lt, "<"),
        ">": lambda *args: compare(args, operator.gt, ">"),
        "<=": lambda *args: compare(args, operator.le, "<="),
        ">=": lambda *args: compare(args, operator.ge, ">="),
        "=": lambda *args: compare(args, operator.eq, "="),
        "==": lambda *args: compare(args, operator.eq, "=="),
        "not": lambda value: not truthy(value),
        "number?": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
        "string?": lambda value: isinstance(value, str) and not isinstance(value, Symbol),
        "symbol?": lambda value: isinstance(value, Symbol),
        "list?": lambda value: isinstance(value, list) and not isinstance(value, Vector),
        "vector?": lambda value: isinstance(value, Vector),
        "dict?": lambda value: isinstance(value, dict),
        "null?": lambda value: value == [],
        "list": lambda *args: list(args),
        "vector": lambda *args: Vector(args),
        "dict": make_dict,
        "cons": cons,
        "car": car,
        "cdr": cdr,
        "append": append,
        "length": lambda value: len(value),
        "get": lambda container, key: container[key],
        "apply": apply_function,
        "map": map_function,
        "filter": filter_function,
        "reduce": reduce_function,
        "abs": abs,
        "min": min,
        "max": max,
        "sqrt": math.sqrt,
        "mod": operator.mod,
        "random": random_number,
    }


def truthy(value):
    return value is not False and value != [] and value is not None
