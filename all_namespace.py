from calculation_functions import add, subtract, multiply, divide
from comparison_functions import less_than, greater_than, less_or_equal, greater_or_equal, equal
from evaluate import evaluate


def try_function(args):
    names = namespace()

    if not args or len(args) < 2:
        raise ValueError("try требует как минимум два аргумента: выражение и обработчик")

    expr, handler = args[0], args[1]
    try:
        return evaluate(expr, names)
    except Exception as e:
        return evaluate((handler, (str(e), ())), names)


def namespace():
    names = [{
        "+": {"function": add},
        "-": {"function": subtract},
        "*": {"function": multiply},
        "/": {"function": divide},
        "<": less_than,
        ">": greater_than,
        "<=": less_or_equal,
        ">=": greater_or_equal,
        "==": equal,
        "try": {"function": try_function}
    }]
    return names