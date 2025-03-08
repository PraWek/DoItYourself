"""
задание*:
реализовать функции let и set. они обе макросы (т. е. принимают свои аргументы невычисленными) и должны иметь два аргумента: список лисповых аргументов и список мап, представляющий из себя пространство имён. let бдует использовать функции 1 и 2, set будет использовать функцию 2 из первой части дз.
синтаксис:
(set a 1)
(let ((a 1) (b 2)) (+ a b))
"""

def append_value(struct):
    struct.append({})
    return struct

def change_value(struct, changing_key, changing_val):
    struct[-1][changing_key] = changing_val
    return struct

def evaluate(expression, namespaces):
    if type(expression) == int or type(expression) == float:  # Число
        return expression
    elif type(expression) == str:  # Переменная
        for ns in reversed(namespaces):
            if expression in ns:
                return ns[expression]
    elif type(expression) == list:
        operator = expression[0]
        operands = expression[1:]
        if operator == '+':
            return sum(evaluate(op, namespaces) for op in operands)
        elif operator == '-':
            return evaluate(operands[0], namespaces) - sum(evaluate(op, namespaces) for op in operands[1:])
        elif operator == '*':
            result = 1
            for op in operands:
                result *= evaluate(op, namespaces)
            return result
        elif operator == '/':
            result = evaluate(operands[0], namespaces)
            for op in operands[1:]:
                divisor = evaluate(op, namespaces)
                result /= divisor
            return result

def my_set(expression, namespaces):
    variable_name = expression[1]
    value = expression[2]
    change_value(namespaces, variable_name, value)
    return value

def let(expression, namespaces):
    bindings = expression[1]
    body = expression[2]

    namespaces = append_value(namespaces)

    for var_name, val in bindings:
        change_value(namespaces, var_name, evaluate(val, namespaces))

    result = evaluate(body, namespaces)
    namespaces.pop()
    return result

# Пример
namespaces = [{}]

expression_set = ['set', 'x', 10]
my_set(expression_set, namespaces)
print(namespaces)  # [{'x': 10}]

expression_let = ['let', [('a', 1), ('b', 2)], ['+', 'a', 'b']]
result = let(expression_let, namespaces)
print(result)  # 3

# ================================================================
# Отладка
# namespaces = [{}]
#
# expression_let = ['let', [('a', 1), ('b', 2)], ['+', 'a', 'b']]
# result = let(expression_let, namespaces)
# print(result)  # -> 3
#
# expression_let = ['let', [('x', 10), ('y', 5)], ['-', 'x', 'y']]
# result = let(expression_let, namespaces)
# print(result)  # -> 5
#
# expression_let = ['let', [('x', 10), ('y', 5)], ['*', 'x', 'y']]
# result = let(expression_let, namespaces)
# print(result)  # -> 50
#
# expression_let = ['let', [('x', 10), ('y', 2)], ['/', 'x', 'y']]
# result = let(expression_let, namespaces)
# print(result)  # -> 5.0
#
# expression_let = ['let', [('a', 1), ('b', 2), ('c', 3)], ['+', 'a', ['*', 'b', 'c']]]
# result = let(expression_let, namespaces)
# print(result)  # -> 7
