# ДЗ 5*: написать функцию cond

def evaluate(obj):
    if type(obj) == tuple:
        if not obj:
            return ()

        operator = obj[0]
        if operator == '+':
            return sum(evaluate(x) for x in obj[1:])
        elif operator == '*':
            result = 1
            for x in obj[1:]:
                result *= evaluate(x)
            return result
        elif operator == '>':
            return 1 if evaluate(obj[1]) > evaluate(obj[2]) else ()
        elif operator == '<':
            return 1 if evaluate(obj[1]) < evaluate(obj[2]) else ()
        elif operator == '==':
            return 1 if evaluate(obj[1]) == evaluate(obj[2]) else ()
        elif operator == '-':
            return evaluate(obj[1]) - evaluate(obj[2])
        elif operator == '/':
            return evaluate(obj[1]) / evaluate(obj[2])
        else:
            return obj
    else:
        return obj

# Проверка работоспособности evaluate
# print(evaluate(('+', 1, ('*', 2, 3))))  # -> 7
# print(evaluate(('>', 5, 3)))  # -> 1
# print(evaluate(('<', 5, 3)))  # -> ()

def cond(conditions):
    if not conditions:
        return ()

    first_condition, *rest_conditions = conditions
    condition, result = first_condition

    if evaluate(condition) != ():
        return evaluate(result)
    else:
        return cond(rest_conditions)

# Примеры
a = 10
b = 5
print(cond([
    (('>', a, b), 1),
    (('<', a, b), -1),
    ((1,), 0)
]))  # -> 1

a = 3
b = 5
print(cond([
    (('>', a, b), 1),
    (('<', a, b), -1),
    ((1,), 0)
]))  # -> -1

a = 5
b = 5
print(cond([
    (('>', a, b), 1),
    (('<', a, b), -1),
    ((1,), 0)
]))  # -> 0
