def find_value_by_key(list_of_dicts, key):
    for dictionary in reversed(list_of_dicts):
        if key in dictionary:
            return dictionary[key]
    return None

def evaluate_elems(elems, names):
    if not elems:
        return ()
    head, tail = elems
    head = evaluate(head, names)
    tail = evaluate_elems(tail, names)
    return (head, tail)

def evaluate(value, names):
    if isinstance(value, (int, float)):
        return value

    elif isinstance(value, str):
        res = find_value_by_key(names, value)
        if res:
            return res
        else:
            raise NameError(value)

    elif isinstance(value, dict):
        return value

    elif isinstance(value, tuple):
        if not value:
            return value
        head, tail = value
        head = evaluate(head, names)
        if not isinstance(head, dict):
            raise TypeError(f'`{value}` не вызывается')
        if "macro" in head:
            macro = head["macro"]
            return macro(tail)
        elif "function" in head:
            func = head["function"]
            tail = evaluate_elems(tail, names)
            return func(tail)
        raise SystemError(f'неожиданный словарь: `{value}`')

    raise TypeError(f'неподдерживаемый тип: `{type(value)}`')

# from calculation_functions import multiply
#
# # Пространство имён
# names = [{
#     "*": {"function": multiply},
#     "x": 10,
#     "y": 20,
# }]
#
# # Примеры вызовов
# print(evaluate(42, names))
# print(evaluate("x", names))
# # ["*", "x", "y"]
# print(evaluate(("*", ("x", ("y", ()))), names))
