from comparison_functions import less_than, greater_than, less_or_equal, greater_or_equal, equal

def evaluate_condition(condition):
    operator, pair = condition
    if operator == "<":
        return less_than(pair)
    elif operator == ">":
        return greater_than(pair)
    elif operator == "<=":
        return less_or_equal(pair)
    elif operator == ">=":
        return greater_or_equal(pair)
    elif operator == "==":
        return equal(pair)
    else:
        raise ValueError(f"Неизвестный оператор: {operator}")

def cond(*conditions):
    for condition, value in conditions:
        if evaluate_condition(condition) == 1:
            return value
    return None

# # Пример использования:
# a = 5
# b = 3
#
# result = cond(
#     ((">", (a, (b, ()))), 1),
#     (("<", (a, (b, ()))), -1),
#     (("==", (a, (b, ()))), 0)
# )
#
# print(result)  # -> 1