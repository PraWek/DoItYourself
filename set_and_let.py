from evaluate import evaluate

def append_value(struct):
    struct.append({})
    return struct

def change_value(struct, changing_key, changing_val):
    struct[-1][changing_key] = changing_val
    return struct

def my_set(expression, namespaces):
    variable_name, (value, _) = expression
    evaluated_value = evaluate(value, namespaces)
    change_value(namespaces, variable_name, evaluated_value)
    return namespaces  # Возвращаем изменённый namespaces

def let(expression, namespaces):
    bindings, body = expression
    namespaces = append_value(namespaces)

    for binding in bindings:
        var_name, (value, _) = binding
        evaluated_value = evaluate(value, namespaces)
        change_value(namespaces, var_name, evaluated_value)

    result = evaluate(body, namespaces)
    namespaces.pop()
    return result

# from calculation_functions import add, subtract, multiply, divide
#
# # Пространство имён с функциями
# names = [{
#     "+": {"function": add},
#     "-": {"function": subtract},
#     "*": {"function": multiply},
#     "/": {"function": divide},
# }]
#
# # Пример set
# set_expr = ('a', (1, ()))
# result = my_set(set_expr, names)
# print(result)  # [{'a': 1}]
#
# # Пример let
# let_expr = (
#     (('a', (1, ())), ('b', (2, ()))),
#     ('+', ('a', ('b', ())))
# )
# result = let(let_expr, names)
# print(result)  # 3