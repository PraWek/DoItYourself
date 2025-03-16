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
    try:
        if isinstance(value, (int, float)):
            return value

        elif isinstance(value, dict) and "type" in value:
            if value["type"] == "string":
                return value
            elif value["type"] == "array":
                return {"type": "array", "value": [evaluate(x, names) for x in value["value"]]}
            elif value["type"] == "dict":
                return {"type": "dict", "value": {evaluate(k, names): evaluate(v, names)
                                                  for k, v in value["value"].items()}}

        elif isinstance(value, str):
            if not names:
                raise ValueError("Пустое пространство имён")
            res = find_value_by_key(names, value)
            if res is not None:
                return res
            raise NameError(f"Неопределённая переменная: '{value}'")

        elif isinstance(value, dict):
            if not value:
                raise ValueError("Пустой словарь")
            return value

        elif isinstance(value, tuple):
            if not value and value != ():
                raise ValueError("Некорректный кортеж")
            if not value:
                return value

            if len(value) < 2:
                raise ValueError("Некорректная структура кортежа")

            head, tail = value
            try:
                head = evaluate(head, names)
            except Exception as e:
                raise ValueError(f"Ошибка при вычислении головы выражения: {str(e)}")

            if not isinstance(head, dict):
                raise TypeError(f"Выражение '{value}' не является вызовом функции")

            if "macro" in head:
                try:
                    macro = head["macro"]
                    return macro(tail)
                except Exception as e:
                    raise ValueError(f"Ошибка при выполнении макроса: {str(e)}")
            elif "function" in head:
                try:
                    func = head["function"]
                    tail = evaluate_elems(tail, names)
                    return func(tail)
                except Exception as e:
                    raise ValueError(f"Ошибка при выполнении функции: {str(e)}")
            raise SystemError(f"Неожиданный тип словаря: '{value}'")

        raise TypeError(f"Неподдерживаемый тип данных: '{type(value)}'")
    except Exception as e:
        if isinstance(e, (ValueError, TypeError, NameError, SystemError)):
            raise
        raise ValueError(f"Ошибка при вычислении выражения: {str(e)}")

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
