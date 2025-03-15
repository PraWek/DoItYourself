from comparison_functions import less_than, greater_than, less_or_equal, greater_or_equal, equal
from evaluate import evaluate
from all_namespace import namespace


names = namespace()

def evaluate_condition(condition):
    try:
        if not isinstance(condition, tuple) or len(condition) != 2:
            raise ValueError("Некорректная структура условия")

        operator, pair = condition
        if not isinstance(operator, str):
            raise TypeError("Оператор должен быть строкой")

        if not isinstance(pair, tuple):
            raise TypeError("Операнды должны быть в кортеже")

        if operator not in names:
            raise ValueError(f"Неизвестный оператор сравнения: '{operator}'")

        return names[operator](pair)
    except Exception as e:
        if isinstance(e, (ValueError, TypeError)):
            raise
        raise ValueError(f"Ошибка при вычислении условия: {str(e)}")


def cond(*conditions):
    try:
        if not conditions:
            raise ValueError("Отсутствуют условия")

        for condition_pair in conditions:
            if not isinstance(condition_pair, tuple) or len(condition_pair) != 2:
                raise ValueError("Некорректная структура пары условие-значение")

            condition, value = condition_pair
            try:
                if evaluate_condition(condition) == 1:
                    return evaluate(value, names)
            except Exception as e:
                raise ValueError(f"Ошибка в условии {condition}: {str(e)}")

        return None
    except Exception as e:
        if isinstance(e, (ValueError, TypeError)):
            raise
        raise ValueError(f"Ошибка в операции cond: {str(e)}")
